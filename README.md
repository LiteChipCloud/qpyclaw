# qpyclaw

**qpyclaw** is the QuecPython-native OpenClaw Node initiative. It keeps the gateway topology `qpyclaw-node -> Official OpenClaw Gateway` but rewrites the device runtime to fit resource-constrained QuecPython boards while still exposing the OpenClaw toolset.

## Overview

- The shared runtime lives under `embed/qpyclaw-node/code/`: `qpyclaw_node.py`, `config.py`, `transport.py`, `tools.py`, `voice.py`, `dispatch.py`, and `node_main.py` are the pieces that drive the node process running in `/usr`.  
- Reusable helpers (`ws_client.py`, `cellular.py`) ship from `embed/components/` and get copied to `/usr` along with the runtime.  
- Board-specific extensions live under `embed/boards/ec800mcnle-audio-board/code/` as `board_*.py`. They run from `/usr/board` and control the screen, speakers, and capture while feeding a `VoiceSessionController` back into the runtime.  
- Media assets for `board_ui` now canonicalize on `U:/media/`, with `/usr/media/` used as a fallback. The board UI tries every prefix automatically.
- The deployment target for every artifact remains `/usr`. Boards keep their own `/usr/board` and `U:/media` slices, and `config_local.py` is the only file that carries secrets.

## Architecture

```
embed/
├── qpyclaw-node/
│   ├── code/            <- runtime modules copied to /usr
│   ├── deploy/          <- manifests that drive qpy_usr_mirror_sync
│   └── examples/        <- board-specific examples and configs
├── components/          <- shared ws_client.py & cellular.py also deployed to /usr
└── boards/
    └── ec800mcnle-audio-board/
        ├── code/        <- board_bootstrap.py, board_audio.py, etc.
        └── resource/    <- `U:/media` emoji assets and schematics
```

## Deployment

1. Use `embed/qpyclaw-node/deploy/runtime-manifest.json` to drive `qpy_usr_mirror_sync.py`. That manifest now points at the `code/` directory and includes the components (`ws_client`, `cellular`).
2. Run `qpy_board_code_sync.py` / `qpy_board_media_sync.py` when flashing the EC800MCNLE board; these tools rely on the updated board manifest that now lists `board_audio.py`, `board_bootstrap.py`, etc.
3. Bootstrapping a device still relies on `tools/host/qpy_post_flash_recover.py`. It syncs `/usr`, `/usr/board`, and `U:/media` per the manifests and then pushes `config_local.py` via `config-local-profiles.json`.
4. Voice diagnostics and GUI rely on the board UI assets in `U:/media`. If `U:/media` is missing, `board_ui` falls back to `/usr/media`, keeping the runtime resilient.

## Getting Started

See the public Quickstart (`docs/public/00-quickstart.md`) for the bring-up workflow and the config samples (`docs/public/01-config-sample.md`) for the placeholders you should override on-device. Host tooling lives under `tools/host/` and contains the recovery, smoke, and probe scripts you use on Windows.

## Recommended Hardware

The target board for this runtime — the EC800MCNLE audio board — is available off the shelf as the **EC800X Audio Core Board** from the Quectel Tmall flagship store. It carries an onboard mic + speaker interface, antenna / UART / LCD / USB / battery headers, a function key with tri-color status LED, and supports QuecPython/AT development out of the box.

<p align="center">
  <img src="docs/images/quectel-ec800x-audio-board.jpg" alt="EC800X Audio Core Board — Quectel Tmall flagship store" width="380" />
</p>

---

## Related Project: LiteGate CLI

[LiteGate](https://github.com/LiteChipCloud/litegate) is an all-in-one LLM API gateway: one key for Claude, GLM, DeepSeek, MiniMax, Qwen and 14 models in total — OpenAI & Claude dual-protocol compatible, permanently-free models, 1M context across the lineup. The official CLI wires Claude Code / Codex / ZCode / MiniMax Code and more to LiteGate in one command:

```bash
# zero-install
npx @litechipcloud/litegate init
```

See [LiteChipCloud/litegate](https://github.com/LiteChipCloud/litegate) for details.
