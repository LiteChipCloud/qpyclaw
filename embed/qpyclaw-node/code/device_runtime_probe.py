try:
    import usys as _sys
except Exception:
    import sys as _sys

try:
    import ujson as _json
except Exception:
    _json = None


def _ensure_path(path):
    try:
        if path not in _sys.path:
            _sys.path.append(path)
    except Exception:
        pass


def _dump(value):
    if _json is not None:
        try:
            return _json.dumps(value)
        except Exception:
            pass
    try:
        return str(value)
    except Exception:
        return "<dump-error>"


_ensure_path("/usr")
_ensure_path("usr")
_ensure_path("/usr/board")
_ensure_path("board")

print("RUNTIME_PROBE_START")
print("RUNTIME_PROBE_IMPORT_BOOTSTRAP")
from board_bootstrap import create_qpyclaw_extension
print("RUNTIME_PROBE_IMPORT_NODE")
import qpyclaw_node
print("RUNTIME_PROBE_BEFORE_EXTENSION")
extension = create_qpyclaw_extension(
    enable_charge=True,
    enable_display=True,
    open_audio=False,
    enable_voice=False,
    voice_auto_start=False,
)
print("RUNTIME_PROBE_AFTER_EXTENSION")
print("RUNTIME_PROBE_BEFORE_RUNTIME")
runtime = qpyclaw_node.create_runtime(extension=extension)
print("RUNTIME_PROBE_AFTER_RUNTIME")
print("RUNTIME_PROBE_SNAPSHOT=%s" % _dump(runtime.debug_snapshot()))
print("RUNTIME_PROBE_END")
