try:
    import usys as _sys
except Exception:
    import sys as _sys


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


def start_listen(reason="manual-host", open_audio=True, listen_timeout_ms=0):
    import qpyclaw_node
    from board_bootstrap import create_qpyclaw_extension

    _runtime = getattr(qpyclaw_node, "_LAST_NODE", None)
    _controller = None
    if _runtime is not None:
        try:
            _snapshot = _runtime.debug_snapshot()
        except Exception:
            _snapshot = {}
        _extension = getattr(_runtime, "extension", None)
        _board = getattr(_extension, "board", None)
        _controller = getattr(_board, "voice", None)
        if (not bool(_snapshot.get("has_extension"))) or _controller is None:
            _runtime = None
            _controller = None
    if _runtime is None:
        _extension = create_qpyclaw_extension(
            enable_charge=True,
            enable_display=True,
            open_audio=open_audio,
            enable_voice=True,
            voice_auto_start=True,
        )
        _runtime = qpyclaw_node.create_runtime(extension=_extension)
        _board = getattr(getattr(_runtime, "extension", None), "board", None)
        _controller = getattr(_board, "voice", None)
    if _controller is None:
        raise Exception("board voice controller unavailable")
    _controller.configure(enabled=True, auto_start=True, audio_enabled=bool(open_audio))
    _controller.start()
    if int(listen_timeout_ms or 0) > 0:
        try:
            _controller.listen_timeout_ms = int(listen_timeout_ms)
        except Exception:
            pass
    _controller.begin_listening(reason)
    return _controller.snapshot()


def status(open_audio=True):
    import qpyclaw_node

    _runtime = getattr(qpyclaw_node, "_LAST_NODE", None)
    if _runtime is None:
        return {"available": False, "error": "runtime not started"}
    _extension = getattr(_runtime, "extension", None)
    _board = getattr(_extension, "board", None)
    _controller = getattr(_board, "voice", None)
    if _controller is None:
        return {"available": False, "error": "board voice controller unavailable"}
    try:
        _controller.configure(audio_enabled=bool(open_audio))
    except Exception:
        pass
    return _controller.snapshot()
