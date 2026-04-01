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
    import qpyclaw_board_voice_session as _helper

    _helper.ensure_loop_running(open_audio=open_audio)
    _qpyclaw_node, _runtime, _controller = _helper.ensure_runtime(open_audio=open_audio)
    if int(listen_timeout_ms or 0) > 0:
        try:
            _controller.listen_timeout_ms = int(listen_timeout_ms)
        except Exception:
            pass
    _controller.begin_listening(reason)
    return _controller.snapshot()


def status(open_audio=True):
    import qpyclaw_board_voice_session as _helper

    return _helper.voice_session_status(open_audio=open_audio)
