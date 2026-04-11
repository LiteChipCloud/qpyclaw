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


def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def snapshot():
    board = _find_board()
    if board is None:
        return {
            "ok": False,
            "error": "_AIRI_ONLY_BOARD missing",
        }
    try:
        raw = board.snapshot()
    except Exception as e:
        return {
            "ok": False,
            "error": _string(e),
        }
    raw = _safe_dict(raw)
    ui = _safe_dict(raw.get("ui"))
    scene = _safe_dict(ui.get("scene"))
    return {
        "ok": True,
        "display": _safe_dict(raw.get("display")),
        "ui_ready": bool(ui.get("ready")),
        "scene": scene,
        "runtime_attached": bool(raw.get("runtime_attached")),
    }


def _dump(data):
    if _json is None:
        return _string(data)
    try:
        return _json.dumps(data)
    except Exception:
        return _string(data)


def _print_probe():
    data = snapshot()
    display = _safe_dict(data.get("display"))
    scene = _safe_dict(data.get("scene"))
    expression = _safe_dict(scene.get("expression_player"))
    animimg = _safe_dict(scene.get("expression_animimg"))
    print("AIRI_PROBE_START")
    print("display.ready=%s" % bool(display.get("ready")))
    print("scene.ready=%s" % bool(scene.get("ready")))
    print("expression_engine=%s" % _string(scene.get("expression_engine")))
    print("avatar_render_mode=%s" % _string(scene.get("avatar_render_mode")))
    print("avatar_src=%s" % _string(scene.get("avatar_src")))
    print("avatar_stage=%s" % _dump(scene.get("avatar_stage")))
    print("avatar_image=%s" % _dump(scene.get("avatar_image")))
    print("avatar_panel=%s" % _dump(scene.get("avatar_panel")))
    print("expression.ready=%s" % bool(expression.get("ready")))
    print("expression.current_src=%s" % _string(expression.get("current_src")))
    print("expression.frame_format=%s" % _string(expression.get("frame_format")))
    print("animimg.ready=%s" % bool(animimg.get("ready")))
    print("animimg.current_src=%s" % _string(animimg.get("current_src")))
    print("AIRI_PROBE_END")
    return data


_print_probe()
