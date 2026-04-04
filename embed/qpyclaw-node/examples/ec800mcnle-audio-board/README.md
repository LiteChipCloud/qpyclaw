# EC800MCNLE Audio Board Example

This folder demonstrates how the EC800MCNLE board extension works with the runtime.

## Contents

- `config_local.example.py`: board-specific configuration that overrides gateway/auth settings.
- `main.example.py`: launches `qpyclaw_node.create_runtime()` with an EC800MCNLE extension (`create_qpyclaw_extension`) and calls `runtime.step()` in a loop.
- `dispatch.example.py`: spawns the board dispatch thread by calling `node_main.main()`/`dispatch.main()`.
- `voice_text_smoke.example.py`, `voice_session_main.example.py`: helper scripts that run board voice smoke scenarios using the installed extension.
- `deploy-image/assemble.py`: assembles `/usr` and `/usr/board` from `embed/qpyclaw-node/code/`, `embed/components/`, and `embed/boards/ec800mcnle-audio-board/code/`.

## Runtime layout illustrated

```
/usr/
├── _main.py
├── config.py
├── config_local.py
├── qpyclaw_node.py
├── transport.py
├── tools.py
├── voice.py
├── node_main.py
└── dispatch.py
board/
├── board_bootstrap.py
├── board_audio.py
├── board_display.py
├── board_power.py
├── board_ui.py
├── board_remote_asr.py
├── board_remote_tts.py
└── board_voice_controller.py
```

Board UI assets are copied to `U:/media/` (with `/usr/media/` as a fallback), so `BoardEmojiUi` can always find `neutral.png`, `happy.png`, etc.

## Bringing up examples

1. Recover runtime & board manifest with `tools/host/qpy_post_flash_recover.py --profile ec800mcnle-audio-board`.
2. Run `dispatch` on the target: `import dispatch; dispatch.main()`.
3. Use `voice_text_smoke.example.py` or `voice_session_main.example.py` via `tools/host/qpy_board_voice_smoke.py` to exercise chat/ASR.
4. Configure board media using `tools/host/qpy_board_media_sync.py --profile ec800mcnle-audio-board`.

For reference, the board voice controller implements the full KWS/VAD/ASR/TTS pipeline, and the host scripts expect `dispatch.py` to have injected that controller into `qpyclaw_node`.
