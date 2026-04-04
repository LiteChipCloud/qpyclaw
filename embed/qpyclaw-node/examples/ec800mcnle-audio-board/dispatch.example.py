try:
    import usys as _sys
except Exception:
    import sys as _sys

import _thread


def _ensure_path(path):
    try:
        if path not in _sys.path:
            _sys.path.append(path)
    except Exception:
        pass


def _run_board_main():
    try:
        mods = getattr(_sys, "modules", None)
        if mods is not None and "node_main" in mods:
            mods.pop("node_main")
    except Exception:
        pass
    import node_main

    node_main.main()


def main():
    _ensure_path("/usr")
    _ensure_path("usr")
    _ensure_path("/usr/board")
    _ensure_path("board")
    _thread.start_new_thread(_run_board_main, ())
    return True


if __name__ == "__main__":
    main()
