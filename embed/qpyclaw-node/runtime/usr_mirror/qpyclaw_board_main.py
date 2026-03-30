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


def main():
    qpyclaw_node = _load_qpyclaw_node()
    existing = _existing_board_runtime(qpyclaw_node)
    if existing is not None:
        return existing

    extension = create_qpyclaw_extension(
        enable_charge=True,
        enable_display=True,
        open_audio=False,
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
