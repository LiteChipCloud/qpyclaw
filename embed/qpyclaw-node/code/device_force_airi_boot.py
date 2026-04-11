try:
    import usys as _sys
except Exception:
    import sys as _sys

try:
    import utime as _utime
except Exception:
    import time as _utime


def _ensure_path(path):
    try:
        if path not in _sys.path:
            _sys.path.append(path)
    except Exception:
        pass


def _sleep_ms(delay_ms):
    try:
        _utime.sleep_ms(int(delay_ms or 0))
    except Exception:
        _utime.sleep(float(int(delay_ms or 0)) / 1000.0)


LOG_PATH = "/usr/force_airi_boot.log"


def _log(text):
    fp = open(LOG_PATH, "a")
    try:
        fp.write(str(text) + "\n")
    finally:
        fp.close()


_ensure_path("/usr")
_ensure_path("usr")
_ensure_path("/usr/board")
_ensure_path("board")


def main():
    open(LOG_PATH, "w").close()
    _log("force:start")
    from board_bootstrap import create_qpyclaw_extension
    _log("force:bootstrap")
    import qpyclaw_node
    _log("force:qpyclaw_node")
    ext = create_qpyclaw_extension(
        enable_charge=True,
        enable_display=True,
        open_audio=False,
        enable_voice=False,
        voice_auto_start=False,
    )
    _log("force:extension")
    node = qpyclaw_node.create_runtime(extension=ext)
    _log("force:runtime")
    try:
        node.extension.board.ui.scene.set_expression_engine("frame")
        _log("force:engine=frame")
    except Exception as e:
        _log("force:engine_error=%s" % str(e))
    _sleep_ms(600)
    try:
        _log("force:snapshot=%s" % str(node.debug_snapshot()))
    except Exception as e:
        _log("force:snapshot_error=%s" % str(e))
    return True


try:
    main()
except Exception as e:
    _log("force:error=%s" % str(e))
