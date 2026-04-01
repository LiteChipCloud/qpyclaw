try:
    import usys as _sys
except Exception:
    import sys as _sys

import utime as _utime

try:
    import _thread as _thread
except Exception:
    _thread = None


def _ensure_path(path):
    try:
        if path not in _sys.path:
            _sys.path.append(path)
    except Exception:
        pass


_ensure_path("/usr")
_ensure_path("usr")
_ensure_path("/usr/board")
_ensure_path("board")

from board_bootstrap import create_qpyclaw_extension


_LOOP_RUNNING = False
_LOOP_THREAD_STARTED = False


def _load_qpyclaw_node():
    module = None
    try:
        module = __import__("qpyclaw_node")
    except Exception:
        module = None

    if module is not None and hasattr(module, "create_runtime"):
        return module

    try:
        mods = getattr(_sys, "modules", None)
        if mods is not None and "qpyclaw_node" in mods:
            mods.pop("qpyclaw_node")
    except Exception:
        pass

    return __import__("qpyclaw_node")


def _existing_runtime(module):
    try:
        node = getattr(module, "_LAST_NODE", None)
    except Exception:
        node = None
    if node is None or not hasattr(node, "debug_snapshot"):
        return None
    try:
        snapshot = node.debug_snapshot()
    except Exception:
        return None
    if bool(snapshot.get("has_runtime")) and bool(snapshot.get("has_extension")):
        return node
    return None


def _controller_from_runtime(runtime):
    extension = getattr(runtime, "extension", None)
    if extension is None or not hasattr(extension, "board"):
        return None
    board = extension.board
    if board is None or not hasattr(board, "voice"):
        return None
    return board.voice


def _loop_running():
    global _LOOP_RUNNING
    return bool(_LOOP_RUNNING)


def _set_loop_running(value):
    global _LOOP_RUNNING
    _LOOP_RUNNING = bool(value)
    return _LOOP_RUNNING


def _ticks_ms():
    try:
        return _utime.ticks_ms()
    except Exception:
        try:
            return int(_utime.time() * 1000)
        except Exception:
            return 0


def _ticks_add(base_ms, delta_ms):
    try:
        return _utime.ticks_add(base_ms, int(delta_ms))
    except Exception:
        return int(base_ms or 0) + int(delta_ms or 0)


def _ticks_diff(left_ms, right_ms):
    try:
        return _utime.ticks_diff(left_ms, right_ms)
    except Exception:
        return int(left_ms or 0) - int(right_ms or 0)


def ensure_runtime(open_audio=True):
    qpyclaw_node = _load_qpyclaw_node()
    runtime = _existing_runtime(qpyclaw_node)
    if runtime is None:
        extension = create_qpyclaw_extension(
            enable_charge=True,
            enable_display=True,
            open_audio=open_audio,
            enable_voice=True,
            voice_auto_start=True,
        )
        runtime = qpyclaw_node.create_runtime(extension=extension)
    controller = _controller_from_runtime(runtime)
    if controller is None:
        raise Exception("board voice controller unavailable")
    controller.configure(enabled=True, auto_start=True, audio_enabled=bool(open_audio))
    return qpyclaw_node, runtime, controller


def _controller_loop_running(open_audio=True):
    try:
        _qpyclaw_node, _runtime, controller = ensure_runtime(open_audio=open_audio)
    except Exception:
        return False
    if controller is None or not hasattr(controller, "snapshot"):
        return False
    try:
        snapshot = controller.snapshot()
    except Exception:
        return False
    return bool(snapshot.get("active")) and bool(snapshot.get("runtime_online"))


def _loop_main(step_delay_ms=20, open_audio=True):
    _set_loop_running(True)
    try:
        _qpyclaw_node, runtime, controller = ensure_runtime(open_audio=open_audio)
        controller.start()
        while True:
            runtime.step()
            try:
                _utime.sleep_ms(step_delay_ms)
            except Exception:
                pass
    finally:
        _set_loop_running(False)


def spawn_background(step_delay_ms=20, open_audio=True):
    global _LOOP_THREAD_STARTED
    if _loop_running() or _controller_loop_running(open_audio=open_audio):
        return {"started": False, "reason": "loop_running"}
    if _thread is None or not hasattr(_thread, "start_new_thread"):
        raise Exception("thread unsupported")
    _thread.start_new_thread(_loop_main, (step_delay_ms, open_audio))
    _LOOP_THREAD_STARTED = True
    return {
        "started": True,
        "reason": "background_started",
        "step_delay_ms": int(step_delay_ms),
        "open_audio": bool(open_audio),
    }


def ensure_loop_running(step_delay_ms=20, open_audio=True):
    if _loop_running() or _controller_loop_running(open_audio=open_audio):
        return {"started": False, "reason": "loop_running"}
    return spawn_background(step_delay_ms=step_delay_ms, open_audio=open_audio)


def _sleep_ms(delay_ms):
    try:
        _utime.sleep_ms(int(delay_ms))
    except Exception:
        pass


def _pump_runtime_until(runtime, controller, timeout_ms=12000, step_delay_ms=20, baseline_turn_count=None):
    deadline = _ticks_add(_ticks_ms(), int(timeout_ms))
    snapshot = controller.snapshot()
    if baseline_turn_count is None:
        baseline_turn_count = int(snapshot.get("turn_count") or 0)
    while True:
        runtime.step()
        snapshot = controller.snapshot()
        if int(snapshot.get("turn_count") or 0) > int(baseline_turn_count or 0):
            if (not snapshot.get("worker_busy")) and int(snapshot.get("pending_transcripts") or 0) <= 0:
                return snapshot
        if snapshot.get("last_result_ok") is not None and (not snapshot.get("worker_busy")) and int(snapshot.get("pending_transcripts") or 0) <= 0:
            return snapshot
        if _ticks_diff(deadline, _ticks_ms()) <= 0:
            return snapshot
        _sleep_ms(step_delay_ms)


def _result_snapshot(controller, open_audio=True):
    data = controller.snapshot()
    data["loop_running"] = bool(_loop_running() or _controller_loop_running(open_audio=open_audio))
    data["loop_thread_started"] = bool(_LOOP_THREAD_STARTED)
    return data


def voice_session_spawn(open_audio=True, step_delay_ms=20):
    result = ensure_loop_running(step_delay_ms=step_delay_ms, open_audio=open_audio)
    try:
        _qpyclaw_node, runtime, controller = ensure_runtime(open_audio=open_audio)
    except Exception:
        return result
    if not result.get("started"):
        return _result_snapshot(controller, open_audio=open_audio)
    _pump_runtime_until(runtime, controller, timeout_ms=1200, step_delay_ms=step_delay_ms)
    return _result_snapshot(controller, open_audio=open_audio)


def voice_session_status(open_audio=True):
    _qpyclaw_node, _runtime, controller = ensure_runtime(open_audio=open_audio)
    return _result_snapshot(controller, open_audio=open_audio)


def voice_session_start(open_audio=True, ensure_loop=False, step_delay_ms=20):
    _qpyclaw_node, runtime, controller = ensure_runtime(open_audio=open_audio)
    controller.start()
    if ensure_loop:
        ensure_loop_running(step_delay_ms=step_delay_ms, open_audio=open_audio)
    else:
        _pump_runtime_until(runtime, controller, timeout_ms=600, step_delay_ms=step_delay_ms)
    return _result_snapshot(controller, open_audio=open_audio)


def voice_session_stop(open_audio=True):
    _qpyclaw_node, _runtime, controller = ensure_runtime(open_audio=open_audio)
    controller.stop()
    return _result_snapshot(controller, open_audio=open_audio)


def voice_session_abort(reason="manual", open_audio=True):
    _qpyclaw_node, _runtime, controller = ensure_runtime(open_audio=open_audio)
    controller.abort(reason)
    return _result_snapshot(controller, open_audio=open_audio)


def voice_session_inject(text, source="manual", open_audio=True, ensure_loop=False, step_delay_ms=20, wait_result_ms=12000):
    _qpyclaw_node, runtime, controller = ensure_runtime(open_audio=open_audio)
    baseline = controller.snapshot()
    baseline_turn_count = int(baseline.get("turn_count") or 0)
    controller.start()
    if ensure_loop:
        ensure_loop_running(step_delay_ms=step_delay_ms, open_audio=open_audio)
        _sleep_ms(300)
    controller.inject_transcript(text, source=source)
    data = _pump_runtime_until(
        runtime,
        controller,
        timeout_ms=wait_result_ms,
        step_delay_ms=step_delay_ms,
        baseline_turn_count=baseline_turn_count,
    )
    return _result_snapshot(controller, open_audio=open_audio)


def voice_session_smoke(
    message="Please reply in one short English sentence: who are you?",
    open_audio=True,
):
    return voice_session_inject(message, source="smoke", open_audio=open_audio, ensure_loop=False)


def main(step_delay_ms=20, open_audio=True):
    _loop_main(step_delay_ms=step_delay_ms, open_audio=open_audio)


if __name__ == "__main__":
    main()
