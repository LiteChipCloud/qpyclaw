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
    if bool(snapshot.get("has_runtime")) and bool(snapshot.get("has_extension")):
        return node
    return None


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


def main(open_audio=False, step_delay_ms=20, enable_voice=False, voice_auto_start=False):
    qpyclaw_node = _load_qpyclaw_node()
    existing = _existing_board_runtime(qpyclaw_node)
    if existing is not None:
        return _configure_existing_runtime(
            existing,
            enable_voice=enable_voice,
            voice_auto_start=voice_auto_start,
        )

    extension = create_qpyclaw_extension(
        enable_charge=True,
        enable_display=True,
        open_audio=open_audio,
        enable_voice=enable_voice,
        voice_auto_start=voice_auto_start,
    )
    runtime = qpyclaw_node.create_runtime(extension=extension)

    while True:
        runtime.step()
        try:
            _utime.sleep_ms(step_delay_ms)
        except Exception:
            pass


if __name__ == "__main__":
    main()
