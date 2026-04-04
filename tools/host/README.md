# Host Tools

This directory hosts the Windows-side helpers used to provision, recover, and exercise `qpyclaw-node` devices. Every tool assumes that the runtime modules under `embed/qpyclaw-node/code/` have been synchronized to `/usr`.

Only `qpy_*.py` files are part of the formal host toolchain. `_*.py`, `_*.ps1`, and `_*.json` files are treated as local scratch diagnostics and are ignored by the repository.

## Primary Recovery Flow

`qpy_post_flash_recover.py` is the canonical entry point after flashing. It performs the following steps:

1. Syncs the runtime manifest (`embed/qpyclaw-node/deploy/runtime-manifest.json`) to `/usr`.
2. Optionally syncs board code via `qpy_board_code_sync.py`.
3. Optionally syncs board media (emojis) via `qpy_board_media_sync.py` to `U:/media`.
4. Bootstraps `/usr/config_local.py` from `config-local-profiles.json`.

Default command:

```powershell
python tools/host/qpy_post_flash_recover.py --profile ec800kcnlc-dev-board --port COM14 --json
```

Add `--profile ec800mcnle-audio-board` and `--skip-board-media-sync` for the EC800MCNLE audio kit.

## Runtime Smoke

`qpy_runtime_smoke.py` verifies that `/usr/qpyclaw_node.py` imports, initializes `RuntimeState`, and executes common tools (`qpy.runtime.status`, `qpy.tools.catalog`, `qpy.fs.read`). When `--board-smoke` is supplied, it also loads the board extension (`dispatch.py`), reads board status, audio, power, and UI, and optionally exercises write-path APIs (`qpy.audio.volume`, `qpy.power.charge`, `qpy.ui.emotion`).

```powershell
python tools/host/qpy_runtime_smoke.py --port COM14 --json
python tools/host/qpy_runtime_smoke.py --port COM19 --board-smoke --json
```

## Board Runtime Probe

Use this when you need to start the board extension and capture a runtime snapshot.

1. Dispatch `/usr/dispatch.py` (the onboard entry that assembles the EC800MCNLE board extension).
2. Wait for the runtime to report `online`.
3. Execute a short list of `qpy.*` commands via the embedded `ToolRunner`.

```powershell
python tools/host/qpy_board_runtime_probe.py --port COM19 --json
```

Add `--skip-dispatch` if the board is already running.

## Board Voice Smoke

This script runs `examples/ec800mcnle-audio-board/voice_text_smoke.example.py` or `voice_session_main.example.py` through the REPL.

- **text** mode (default) calls `qpyclaw_node.voice_chat()` while the board UI is active.
- **session** mode waits for a full session lifecycle via `voice_session_smoke`.
- **asr** mode executes `_main.py`, waits for the board to capture audio, and verifies the remote ASR results.

```powershell
python tools/host/qpy_board_voice_smoke.py --port COM6 --json
python tools/host/qpy_board_voice_smoke.py --port COM6 --mode asr --json
```

## Utility Sync Scripts

- `qpy_usr_mirror_sync.py` copies the manifest-listed files to `/usr`.
- `qpy_board_code_sync.py --profile ec800mcnle-audio-board` syncs `/usr/board`.
- `qpy_board_media_sync.py --profile ec800mcnle-audio-board` syncs `U:/media`.
 - `qpy_config_local_bootstrap.py` renders board-profile-based `config_local.py` without overwriting existing configs.

## Voice Sidecar Support

`qpy_voice_sidecar_configure.py` patches `/usr/config_local.py` to point at the DashScope voice sidecar (`http://124.70.221.88:8788/api/asr` + `/api/tts`/`/ws/tts`). `qpy_voice_sidecar_health.py` keeps the DASHScope service healthy via SSH or HTTP checks.
