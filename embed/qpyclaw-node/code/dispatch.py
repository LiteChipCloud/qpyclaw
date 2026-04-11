try:
    import usys as _sys
except Exception:
    import sys as _sys

import _thread

_DISPATCH_LOCK = None
try:
    _DISPATCH_LOCK = _thread.allocate_lock()
except Exception:
    pass

import utime as _utime


def _set_dispatch_state(active, error, ready_ms=None):
    global _DISPATCH_THREAD_ACTIVE, _DISPATCH_LAST_ERROR, _DISPATCH_LAST_READY_MS
    if _DISPATCH_LOCK is not None:
        _DISPATCH_LOCK.acquire()
    try:
        _DISPATCH_THREAD_ACTIVE = bool(active)
        _DISPATCH_LAST_ERROR = _string(error)
        if ready_ms is not None:
            _DISPATCH_LAST_READY_MS = int(ready_ms or 0)
    finally:
        if _DISPATCH_LOCK is not None:
            try:
                _DISPATCH_LOCK.release()
            except Exception:
                pass


def _get_dispatch_state():
    if _DISPATCH_LOCK is not None:
        _DISPATCH_LOCK.acquire()
    try:
        return bool(_DISPATCH_THREAD_ACTIVE), _string(_DISPATCH_LAST_ERROR)
    finally:
        if _DISPATCH_LOCK is not None:
            try:
                _DISPATCH_LOCK.release()
            except Exception:
                pass

_DISPATCH_THREAD_ACTIVE = False
_DISPATCH_LAST_ERROR = ""
_DISPATCH_LAST_START_MS = 0
_DISPATCH_LAST_READY_MS = 0


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _ensure_path(path):
    try:
        if path not in _sys.path:
            _sys.path.append(path)
    except Exception:
        pass


def _ticks_ms():
    try:
        return _utime.ticks_ms()
    except Exception:
        return 0


def _ticks_diff(newer, older):
    try:
        return _utime.ticks_diff(int(newer or 0), int(older or 0))
    except Exception:
        return int(newer or 0) - int(older or 0)


def _sleep_ms(delay_ms):
    try:
        if int(delay_ms or 0) >= 1000:
            _utime.sleep(int(int(delay_ms) / 1000))
        else:
            _utime.sleep_ms(int(delay_ms or 0))
    except Exception:
        pass


def _qpyclaw_snapshot():
    try:
        import qpyclaw_node
    except Exception:
        return {}
    try:
        return qpyclaw_node.debug_snapshot()
    except Exception:
        return {}


def _runtime_ready(snapshot=None, max_idle_ms=6000):
    if snapshot is None:
        snapshot = _qpyclaw_snapshot()
    if not isinstance(snapshot, dict):
        return False
    if not bool(snapshot.get("has_runtime")):
        return False
    if not bool(snapshot.get("has_extension")):
        return False
    extension = snapshot.get("extension") or {}
    if isinstance(extension, dict):
        board = extension.get("board") or {}
        if isinstance(board, dict):
            display = board.get("display") or {}
            ui = board.get("ui") or {}
            if isinstance(display, dict) and isinstance(ui, dict):
                if bool(display.get("ready")) and bool(ui.get("ready")):
                    return True
    state = snapshot.get("state") or {}
    last_tick_ms = int(state.get("last_tick_ms") or 0)
    if last_tick_ms <= 0:
        return False
    return _ticks_diff(_ticks_ms(), last_tick_ms) <= int(max_idle_ms or 6000)


def _run_board_main():
    _set_dispatch_state(True, "")
    try:
        mods = getattr(_sys, "modules", None)
        if mods is not None and "node_main" in mods:
            mods.pop("node_main")
        import node_main
        node_main.main()
    except Exception as e:
        _set_dispatch_state(True, _string(e))
    finally:
        ready_ms_value = None
        if _runtime_ready():
            ready_ms_value = _ticks_ms()
        current_error = _get_dispatch_state()[1]
        _set_dispatch_state(False, current_error, ready_ms_value)


def debug_snapshot():
    snapshot = _qpyclaw_snapshot()
    active, last_error = _get_dispatch_state()
    if _DISPATCH_LOCK is not None:
        _DISPATCH_LOCK.acquire()
    try:
        last_start_ms = int(_DISPATCH_LAST_START_MS or 0)
        last_ready_ms = int(_DISPATCH_LAST_READY_MS or 0)
    finally:
        if _DISPATCH_LOCK is not None:
            try:
                _DISPATCH_LOCK.release()
            except Exception:
                pass
    return {
        "thread_active": bool(active),
        "last_error": last_error,
        "last_start_ms": last_start_ms,
        "last_ready_ms": last_ready_ms,
        "runtime_ready": bool(_runtime_ready(snapshot)),
        "runtime": snapshot,
    }


def main(wait_ready_ms=5000, poll_ms=120):
    _ensure_path("/usr")
    _ensure_path("usr")
    _ensure_path("/usr/board")
    _ensure_path("board")
    snapshot = _qpyclaw_snapshot()
    if _runtime_ready(snapshot):
        if _DISPATCH_LOCK is not None:
            _DISPATCH_LOCK.acquire()
        try:
            _DISPATCH_LAST_READY_MS = _ticks_ms()
        finally:
            if _DISPATCH_LOCK is not None:
                try:
                    _DISPATCH_LOCK.release()
                except Exception:
                    pass
        return True
    if not bool(_get_dispatch_state()[0]):
        if _DISPATCH_LOCK is not None:
            _DISPATCH_LOCK.acquire()
        try:
            _DISPATCH_LAST_START_MS = _ticks_ms()
        finally:
            if _DISPATCH_LOCK is not None:
                try:
                    _DISPATCH_LOCK.release()
                except Exception:
                    pass
        _thread.start_new_thread(_run_board_main, ())
    deadline = _ticks_ms() + max(0, int(wait_ready_ms or 0))
    while _ticks_diff(deadline, _ticks_ms()) >= 0:
        snapshot = _qpyclaw_snapshot()
        if _runtime_ready(snapshot):
            if _DISPATCH_LOCK is not None:
                _DISPATCH_LOCK.acquire()
            try:
                _DISPATCH_LAST_READY_MS = _ticks_ms()
            finally:
                if _DISPATCH_LOCK is not None:
                    try:
                        _DISPATCH_LOCK.release()
                    except Exception:
                        pass
            return True
        if _get_dispatch_state()[1]:
            return False
        _sleep_ms(poll_ms)
    return False


if __name__ == "__main__":
    main()
