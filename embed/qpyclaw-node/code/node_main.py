try:
    import usys as _sys
except Exception:
    import sys as _sys

import utime as _utime


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


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _normalize_bool(value, default=False):
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    text = _string(value).strip().lower()
    if text in ("1", "true", "yes", "on", "enable", "enabled"):
        return True
    if text in ("0", "false", "no", "off", "disable", "disabled"):
        return False
    return bool(default)


def _cfg_bool(cfg, name, default=False):
    if cfg is None:
        return bool(default)
    try:
        value = getattr(cfg, name)
    except Exception:
        return bool(default)
    return _normalize_bool(value, default)


def _purge_runtime_modules():
    names = (
        "qpyclaw_node",
        "config",
        "ws_client",
        "transport",
        "qpy_tools_runtime",
        "voice",
        "cellular",
    )
    try:
        mods = getattr(_sys, "modules", None)
    except Exception:
        mods = None
    if mods is None:
        return False
    removed = False
    index = 0
    while index < len(names):
        name = names[index]
        try:
            if name in mods:
                mods.pop(name)
                removed = True
        except Exception:
            pass
        index += 1
    return removed


def _load_qpyclaw_node():
    module = None
    try:
        module = __import__("qpyclaw_node")
    except Exception:
        module = None

    if module is not None and hasattr(module, "create_runtime"):
        return module

    _purge_runtime_modules()
    return __import__("qpyclaw_node")


def _existing_board_runtime(module):
    try:
        node = getattr(module, "_LAST_NODE", None)
    except Exception:
        node = None
    if node is None:
        return None
    if not hasattr(node, "debug_snapshot"):
        return None
    try:
        snapshot = node.debug_snapshot()
    except Exception:
        return None
    if not _runtime_snapshot_alive(snapshot):
        return None
    return node


def _configure_existing_runtime(runtime, enable_voice=False, voice_auto_start=False):
    if runtime is None:
        return None
    extension = getattr(runtime, "extension", None)
    if extension is None or not hasattr(extension, "board"):
        return runtime
    board = extension.board
    if board is None or not hasattr(board, "voice") or board.voice is None:
        return runtime
    if enable_voice:
        board.voice.configure(enabled=True, auto_start=voice_auto_start)
        if voice_auto_start:
            board.voice.start()
    return runtime


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


def _runtime_snapshot_alive(snapshot, max_idle_ms=6000):
    if not isinstance(snapshot, dict):
        return False
    state = snapshot.get("state") or {}
    if not bool(snapshot.get("has_runtime")):
        return False
    if not bool(snapshot.get("has_extension")):
        return False
    last_tick_ms = int(state.get("last_tick_ms") or 0)
    if last_tick_ms <= 0:
        return False
    return _ticks_diff(_ticks_ms(), last_tick_ms) <= int(max_idle_ms or 6000)


def _sleep_ms(delay_ms):
    try:
        if int(delay_ms or 0) >= 1000:
            _utime.sleep(int(int(delay_ms) / 1000))
        else:
            _utime.sleep_ms(int(delay_ms or 0))
    except Exception:
        pass


_MAX_CONSECUTIVE_STEP_ERRORS = 10


def _run_runtime_loop(runtime):
    consecutive_errors = 0
    while True:
        try:
            ok = runtime.step()
            consecutive_errors = 0
        except Exception as e:
            consecutive_errors += 1
            try:
                if hasattr(runtime, "state") and hasattr(runtime.state, "note_error"):
                    runtime.state.note_error("MAIN_LOOP_ERROR", _string(e))
            except Exception:
                pass
            if consecutive_errors >= _MAX_CONSECUTIVE_STEP_ERRORS:
                try:
                    import qpyclaw_node as _qn
                    if hasattr(_qn, "execute_reboot"):
                        _qn.execute_reboot("soft")
                except Exception:
                    pass
            _sleep_ms(3000)
            continue
        if ok:
            _sleep_ms(20)
        else:
            _sleep_ms(1000)


def main():
    qpyclaw_node = _load_qpyclaw_node()
    cfg = getattr(qpyclaw_node, "config", None)
    voice_enabled = _cfg_bool(cfg, "BOARD_VOICE_ENABLED", _cfg_bool(cfg, "VOICE_ENABLED", False))
    open_audio = _cfg_bool(cfg, "BOARD_OPEN_AUDIO", voice_enabled)
    voice_auto_start = _cfg_bool(cfg, "BOARD_VOICE_AUTO_START", voice_enabled)
    existing = _existing_board_runtime(qpyclaw_node)
    if existing is not None:
        return _configure_existing_runtime(
            existing,
            enable_voice=voice_enabled,
            voice_auto_start=voice_auto_start,
        )

    extension = create_qpyclaw_extension(
        enable_charge=True,
        enable_display=True,
        open_audio=open_audio,
        enable_voice=voice_enabled,
        voice_auto_start=voice_auto_start,
    )
    runtime = qpyclaw_node.create_runtime(extension=extension)
    _run_runtime_loop(runtime)


if __name__ == "__main__":
    main()
