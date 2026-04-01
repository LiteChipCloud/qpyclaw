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


def main(reason="manual-host"):
    import qpyclaw_node

    node = getattr(qpyclaw_node, "_LAST_NODE", None)
    if node is None:
        return {
            "status": "failed",
            "error": "runtime not started",
        }
    return node.execute_local(
        "qpy.board.voice.listen",
        {
            "reason": reason,
        },
        "manual-listen-existing",
    )
