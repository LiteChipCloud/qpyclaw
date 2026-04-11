try:
    import usys as _sys
except Exception:
    import sys as _sys


def _drop_module(name):
    try:
        if name in _sys.modules:
            del _sys.modules[name]
    except Exception:
        pass


def _reset_boot_state():
    try:
        globals()["_AIRI_ONLY_BOARD"] = None
    except Exception:
        pass
    names = (
        "_main",
        "board_bootstrap",
        "board_ui",
        "board_airi_scene",
        "board_airi_animimg_player",
        "board_airi_frame_player",
        "board_miaoban_player",
    )
    index = 0
    while index < len(names):
        _drop_module(names[index])
        index += 1


_reset_boot_state()
print("AIRI_BOOT_PROBE_START")
print("AIRI_BOOT_PROBE_BEFORE_MAIN")
try:
    exec(open("/usr/_main.py").read(), globals(), globals())
    print("AIRI_BOOT_PROBE_AFTER_MAIN")
except Exception as e:
    print("AIRI_BOOT_PROBE_MAIN_ERROR=%s" % str(e))
    raise
print("AIRI_BOOT_PROBE_BEFORE_SCENE")
try:
    exec(open("/usr/device_airi_probe.py").read(), globals(), globals())
    print("AIRI_BOOT_PROBE_AFTER_SCENE")
except Exception as e:
    print("AIRI_BOOT_PROBE_SCENE_ERROR=%s" % str(e))
    raise
print("AIRI_BOOT_PROBE_END")
