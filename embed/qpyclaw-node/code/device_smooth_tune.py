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

import qpyclaw_node

node = qpyclaw_node._LAST_NODE
if node is None:
    exec(open("/usr/device_force_airi_boot.py").read(), globals(), globals())
    import qpyclaw_node
    node = qpyclaw_node._LAST_NODE

if node is not None:
    display = node.extension.board.display
    scene = node.extension.board.ui.scene
    player = scene.expression_player
    display.tick_ms = 16
    display.set_pump_hook(scene._advance_anim_locked)
    think_seq = [
        "thinking/frame-000.rgb565",
        "thinking/frame-000.rgb565",
        "thinking/frame-000.rgb565",
        "thinking/frame-000.rgb565",
        "thinking/frame-000.rgb565",
        "thinking/frame-004.rgb565",
        "thinking/frame-005.rgb565",
        "thinking/frame-007.rgb565",
        "thinking/frame-005.rgb565",
        "thinking/frame-004.rgb565",
        "thinking/frame-002.rgb565",
        "thinking/frame-000.rgb565",
        "thinking/frame-000.rgb565",
    ]
    natural_blink_seq = [
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-008.rgb565",
        "neutral/frame-009.rgb565",
        "neutral/frame-008.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
        "neutral/frame-000.rgb565",
    ]
    player.expressions["neutral"]["frames"] = natural_blink_seq
    player.expressions["neutral"]["tick_step"] = 1
    player.expressions["idle_blink"]["frames"] = natural_blink_seq
    player.expressions["idle_blink"]["tick_step"] = 1
    player.expressions["thinking"]["frames"] = think_seq
    player.expressions["thinking"]["tick_step"] = 1
    player.expressions["listen_focus"]["frames"] = think_seq
    player.expressions["listen_focus"]["tick_step"] = 1
    player.expressions["confused"]["frames"] = think_seq
    player.expressions["confused"]["tick_step"] = 1
    player.current_entry = player._entry_for_key(scene.current_expression)
    player.current_tick_step = int((player.current_entry or {}).get("tick_step") or 1)
    player.frame_index = 0
    player.frame_hold = 0
    scene.set_mode(scene.mode_key)
    print("SMOOTH_TUNED")
else:
    print("SMOOTH_TUNE_NODE_MISSING")
