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
    state = snapshot.get("state") or {}
    if (
        bool(snapshot.get("has_runtime"))
        and bool(snapshot.get("has_extension"))
        and int(state.get("last_tick_ms") or 0) > 0
    ):
        return node
    return None


def main():
    qpyclaw_node = _load_qpyclaw_node()
    existing = _existing_board_runtime(qpyclaw_node)
    if existing is not None:
        return existing

    cfg = getattr(qpyclaw_node, "config", None)
    voice_enabled = _cfg_bool(cfg, "BOARD_VOICE_ENABLED", _cfg_bool(cfg, "VOICE_ENABLED", False))
    open_audio = _cfg_bool(cfg, "BOARD_OPEN_AUDIO", voice_enabled)
    voice_auto_start = _cfg_bool(cfg, "BOARD_VOICE_AUTO_START", voice_enabled)

    extension = create_qpyclaw_extension(
        enable_charge=True,
        enable_display=True,
        open_audio=open_audio,
        enable_voice=voice_enabled,
        voice_auto_start=voice_auto_start,
    )
    runtime = qpyclaw_node.create_runtime(extension=extension)

    while True:
        runtime.step()
        try:
            _utime.sleep_ms(20)
        except Exception:
            pass


if __name__ == "__main__":
    main()
