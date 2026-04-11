try:
    import usys as _sys
except Exception:
    import sys as _sys


names = (
    "board_airi_frame_player",
    "board_airi_scene",
    "board_ui",
    "board_bootstrap",
    "qpyclaw_node",
    "node_main",
    "dispatch",
)

mods = getattr(_sys, "modules", None)
if mods is not None:
    index = 0
    while index < len(names):
        try:
            if names[index] in mods:
                mods.pop(names[index])
        except Exception:
            pass
        index += 1

exec(open("/usr/device_force_airi_boot.py").read(), globals(), globals())
print("RELOAD_BOOT_OK")
