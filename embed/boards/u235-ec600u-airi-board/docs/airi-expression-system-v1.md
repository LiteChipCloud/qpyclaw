# AIRI Expression System V1

## Goal

Keep AIRI asset creation friendly for design while keeping board runtime stable.

Source of truth for design:

- GIF
- PNG sequence

Runtime format on board:

- RGB565 frame sequence
- Manifest-driven playback
- LVGL animation for halo, motion, and UI timing

## Runtime Decision

Do not use GIF as the final runtime format on the board.

Reasons:

- GIF decode cost is harder to control on QuecPython.
- Frame timing, state switching, and fallback behavior are easier with a manifest-driven player.
- The current AIRI scene is already stable on `rgb565 -> lv.canvas -> lv.img`.

## Resource Layout

Board runtime path:

- `/usr/media/airi/expressions/manifest.json`
- `/usr/media/airi/expressions/<expression-key>/<frame>.rgb565`

Manifest example:

```json
{
  "version": 1,
  "default": "idle_blink",
  "expressions": {
    "idle_blink": {
      "width": 176,
      "height": 176,
      "zoom": 320,
      "tick_step": 3,
      "loop": true,
      "frames": [
        "idle_blink/frame-000.rgb565",
        "idle_blink/frame-001.rgb565"
      ]
    }
  }
}
```

## Core Expression Set

- `idle_blink`
- `listen_focus`
- `talk_smile`
- `talk_open`
- `happy_pop`
- `sad_soft`
- `angry_fire`
- `sleep_breath`
- `shock_hold`
- `wink_ping`

## Recommended Visual Split

Do not animate the full body for every frame unless it is truly needed.

Recommended split:

- Base AIRI body stays mostly static.
- Face layers carry the expression changes.
- LVGL animation adds breathing, halo pulse, and stage rhythm.

This keeps storage and I/O lower while making the board feel more alive.

## Asset Workflow

1. Design exports a GIF or PNG sequence per expression.
2. Host tool converts frames into `rgb565` files and updates `manifest.json`.
3. Assets are pushed to `/usr/media/airi/expressions`.
4. `board_airi_frame_player.py` picks the expression by key.
5. `board_airi_scene.py` falls back to static AIRI when expression assets are missing.

## First Delivery Target

V1 target should be:

- `idle_blink`
- `listen_focus`
- one speaking loop: `talk_open`

That is enough to prove the full pipeline before building the full pack.
