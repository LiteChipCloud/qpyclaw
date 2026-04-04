# embed/qpyclaw-node

`embed/qpyclaw-node` holds the shared node runtime that runs on QuecPython devices and connects to the Official OpenClaw Gateway.

## Runtime Layout

- All production runtime modules live in `embed/qpyclaw-node/code/`. These include `qpyclaw_node.py`, `config.py`, `transport.py`, `tools.py`, `voice.py`, `dispatch.py`, `node_main.py`, and `_main.py`.
- Shared support helpers (`ws_client.py`, `cellular.py`) live in `embed/components/` and are copied into `/usr` along with the runtime during recovery.
- Board-specific code lives under `embed/boards/ec800mcnle-audio-board/code/` and uses `board_bootstrap.py`, `board_audio.py`, `board_display.py`, `board_power.py`, `board_ui.py`, `board_voice_controller.py`, `board_remote_asr.py`, and `board_remote_tts.py`. Those modules load via `dispatch.py`/`node_main.py`.
- Media assets (emojis, UI skins) reside in `embed/boards/ec800mcnle-audio-board/resource/ui/emoji/` which are synced to `U:/media/` on the device. `board_ui` tries `U:/media` first and falls back to `/usr/media`.

## Deploy Flow

1. Use `embed/qpyclaw-node/deploy/runtime-manifest.json` to declare files that may be pushed to `/usr`. It now points at `code/` instead of the legacy `usr_mirror` tree.
2. Run `tools/host/qpy_post_flash_recover.py` to orchestrate recovery, board code sync, and board media sync according to the manifests.
3. For board-level bring-up, use `embed/qpyclaw-node/examples/ec800mcnle-audio-board/` for reference configs and smoke scripts (`voice_text_smoke.example.py`, `voice_session_main.example.py`).

## Getting Started

- General runtime: `import qpyclaw_node; qpyclaw_node.run()`  
- EC800MCNLE board: `import dispatch; dispatch.main()` or `import node_main; node_main.main(open_audio=True)` to exercise the full board UI and voice controller.
- Read `docs/public/00-quickstart.md` for the bring-up flow and `docs/public/01-config-sample.md` for configuration guidance.
