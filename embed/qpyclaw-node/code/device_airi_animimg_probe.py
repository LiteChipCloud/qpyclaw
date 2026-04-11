try:
    import ujson as _json
except Exception:
    _json = None


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _find_board():
    board = globals().get("_AIRI_ONLY_BOARD")
    if board is not None:
        return board
    try:
        import _main as _main_mod
        return getattr(_main_mod, "_AIRI_ONLY_BOARD", None)
    except Exception:
        return None


def _dump(data):
    if _json is None:
        return _string(data)
    try:
        return _json.dumps(data)
    except Exception:
        return _string(data)


board = _find_board()
print("AIRI_ANIMIMG_PROBE_START")
if board is None:
    print("error=board missing")
else:
    scene = board.ui.scene
    result = scene.set_expression_engine("animimg")
    scene.set_mode("listen")
    snap = board.snapshot()
    scene_data = ((snap.get("ui") or {}).get("scene") or {})
    animimg = scene_data.get("expression_animimg") or {}
    print("switch=%s" % _dump(result))
    print("avatar_render_mode=%s" % _string(scene_data.get("avatar_render_mode")))
    print("expression_engine=%s" % _string(scene_data.get("expression_engine")))
    print("animimg.ready=%s" % bool(animimg.get("ready")))
    print("animimg.frame_count=%s" % _string(animimg.get("frame_count")))
    print("animimg.memory_bytes=%s" % _string(animimg.get("memory_bytes")))
    print("animimg.current_src=%s" % _string(animimg.get("current_src")))
print("AIRI_ANIMIMG_PROBE_END")
