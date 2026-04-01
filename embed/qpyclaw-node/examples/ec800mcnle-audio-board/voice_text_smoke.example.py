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


def _existing_runtime(module):
    try:
        node = getattr(module, "_LAST_NODE", None)
    except Exception:
        node = None
    if node is None:
        return None
    if not hasattr(node, "voice") or not hasattr(node, "debug_snapshot"):
        return None
    try:
        snapshot = node.debug_snapshot()
    except Exception:
        return None
    if not bool(snapshot.get("has_extension")):
        return None
    return node


def ensure_runtime(open_audio=False):
    qpyclaw_node = _load_qpyclaw_node()
    runtime = _existing_runtime(qpyclaw_node)
    if runtime is not None:
        return qpyclaw_node, runtime
    extension = create_qpyclaw_extension(
        enable_charge=True,
        enable_display=True,
        open_audio=open_audio,
    )
    runtime = qpyclaw_node.create_runtime(extension=extension)
    return qpyclaw_node, runtime


def _board_from_runtime(runtime):
    extension = getattr(runtime, "extension", None)
    if extension is None or not hasattr(extension, "board"):
        return None
    return extension.board


def voice_status(open_audio=False):
    qpyclaw_node, runtime = ensure_runtime(open_audio=open_audio)
    return qpyclaw_node.voice_status(runtime=runtime)


def voice_abort(session_key="main", open_audio=False):
    qpyclaw_node, runtime = ensure_runtime(open_audio=open_audio)
    return qpyclaw_node.voice_abort(session_key=session_key, runtime=runtime)


def voice_text_smoke(
    message="Please reply in one short English sentence: who are you?",
    timeout_ms=45000,
    subscribe=False,
    open_audio=False,
):
    qpyclaw_node, runtime = ensure_runtime(open_audio=open_audio)
    board = _board_from_runtime(runtime)
    if board is not None:
        try:
            board.ui.show_booting()
        except Exception:
            pass
    try:
        result = qpyclaw_node.voice_chat(
            message,
            timeout_ms=timeout_ms,
            subscribe=subscribe,
            runtime=runtime,
        )
    except Exception:
        if board is not None:
            try:
                board.ui.show_error()
            except Exception:
                pass
        raise
    if board is not None:
        try:
            if bool(result.get("ok")):
                board.ui.show_ready()
                reply_text = str(result.get("reply_text") or "").strip()
                if reply_text:
                    board.ui.show_message(reply_text)
            else:
                board.ui.show_error()
        except Exception:
            pass
    return result


def main():
    return voice_text_smoke()


if __name__ == "__main__":
    main()
