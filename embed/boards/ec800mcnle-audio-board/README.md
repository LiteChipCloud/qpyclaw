# EC800MCNLE Audio Board

Board-specific extensions for the EC800MCNLE audio kit live under `embed/boards/ec800mcnle-audio-board/code/`. These Python modules run on top of the common runtime (`qpyclaw-node`) and expose the LVGL screen, speaker, microphone, and board buttons to the voice controller.

## Code Layout

- `board_bootstrap.py` constructs `EC800MCNLEBoardExtension` and attaches it to `dispatch.py`/`node_main.py`.
- `board_audio.py`, `board_remote_asr.py`, and `board_remote_tts.py` implement audio capture/playback plus remote ASR/TTS adapters.
- `board_display.py`, `board_ui.py`, and `board_voice_controller.py` manage the LVGL screen, emoji catalog, and voice session state machine (KWS, VAD, voice dialog).
- All board code expects to run from `/usr/board` after `dispatch.py` loads the extension.

## Media & UI

Emoji assets are stored in `resource/ui/emoji/` and synced to `U:/media/` via `tools/host/qpy_board_media_sync.py`. `BoardEmojiUi` resolves `U:/media` first and then `/usr/media` as a fallback to keep the UI resilient.

## Deployment Notes

1. `tools/host/qpy_board_code_sync.py --profile ec800mcnle-audio-board` pushes the board modules to `/usr/board` per `embed/qpyclaw-node/deploy/board-manifests/ec800mcnle-audio-board.json`.
2. The board extension is loaded through `dispatch.py`, so host probes and smoke scripts should import `dispatch` or `node_main` rather than legacy `qpyclaw_board_*` modules.
3. The board voice flow is exercised via `examples/ec800mcnle-audio-board/voice_text_smoke.example.py` and `voice_session_main.example.py`.
