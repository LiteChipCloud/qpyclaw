# EC800MCNLE Screen Emoji Bring-Up

## Current State

- Board UI driver exists in `boards/ec800mcnle-audio-board/code/board_ui.py`
- Board extension already exposes `qpy.ui.status` and `qpy.ui.emotion.show`
- This change adds:
  - bundled emoji PNG assets under `boards/ec800mcnle-audio-board/resource/ui/emoji`
  - host-side `qpy_board_media_sync.py`
  - recovery support for board media sync
  - `qpy.ui.emotion.catalog` for device-side visibility of available assets
  - runtime fallback from `U:/media` to `/usr/media`

## Asset Source

- Local upstream source:
  - `opensource/AIChatbot-Xiaozhi-Mqtt/src(UI)/media`
- Device target path:
  - `/usr/media`

## Deploy

Only sync media assets:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_media_sync.py --profile ec800mcnle-audio-board --port COM19 --json
```

Full recovery including board code and board media:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800mcnle-audio-board --port COM19 --board-probe --json
```

## Validate

Runtime smoke:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_runtime_smoke.py --port COM19 --board-write-smoke --json
```

Manual checks from node tooling or gateway:

- `qpy.ui.status`
- `qpy.ui.emotion.catalog`
- `qpy.ui.emotion.show {"emotion":"happy"}`
- `qpy.ui.emotion.show {"emotion":"thinking"}`

## Expected Behavior

- `qpy.ui.emotion.catalog` returns the supported emoji list from board code
- `qpy.ui.status` now reports:
  - `current_path`
  - `current_asset_exists`
  - `resolved_media_prefix`
  - `supported_emojis`
  - `available_emojis`
- Once `/usr/media` is populated, `qpy.ui.emotion.show` should drive real PNG swaps on screen instead of only changing runtime state
