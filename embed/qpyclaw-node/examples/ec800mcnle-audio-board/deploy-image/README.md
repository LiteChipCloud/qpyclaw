# EC800MCNLE Audio Board — Deploy Image Template

This directory is a ready-to-assemble mirror of the device `/usr/` filesystem.

`output/` is generated locally by `assemble.py` and should not be committed.

## How to use

1. Copy `config_local.example.py` → `usr/config_local.py` and fill in real credentials.
2. Run the assemble script (or manually copy files per layout below).
3. Use host sync tools to push `usr/` contents to device `/usr/`.

## Device filesystem layout

```text
/usr/
├── _main.py              ← entry point (exec'd from REPL or main.py)
├── config.py             ← default config + local override loader
├── config_local.py       ← device-local credentials (NOT in repo)
├── qpyclaw_node.py       ← slim orchestrator
├── transport.py           ← WebSocket transport layer
├── tools.py               ← tool system + command worker
├── voice.py               ← voice dialog client
├── ws_client.py           ← portable WebSocket client (component)
├── cellular.py            ← cellular network manager (component)
├── dispatch.py            ← thread dispatch for board main
├── node_main.py           ← board-aware main loop
└── board/
    ├── board_bootstrap.py       ← board extension + factory
    ├── board_audio.py           ← audio driver
    ├── board_display.py         ← SPI display driver
    ├── board_power.py           ← charge/power pin control
    ├── board_ui.py              ← emoji UI layer
    ├── board_voice_controller.py ← KWS/VAD/ASR/TTS state machine
    ├── board_remote_asr.py      ← HTTP ASR transcript provider
    └── board_remote_tts.py      ← WS/HTTP TTS speaker
```

## Source file mapping

| Device path | Repo source |
|---|---|
| `/usr/_main.py` | `embed/qpyclaw-node/code/_main.py` |
| `/usr/config.py` | `embed/qpyclaw-node/code/config.py` |
| `/usr/qpyclaw_node.py` | `embed/qpyclaw-node/code/qpyclaw_node.py` |
| `/usr/transport.py` | `embed/qpyclaw-node/code/transport.py` |
| `/usr/tools.py` | `embed/qpyclaw-node/code/tools.py` |
| `/usr/voice.py` | `embed/qpyclaw-node/code/voice.py` |
| `/usr/ws_client.py` | `embed/components/ws_client.py` |
| `/usr/cellular.py` | `embed/components/cellular.py` |
| `/usr/dispatch.py` | `embed/qpyclaw-node/code/dispatch.py` |
| `/usr/node_main.py` | `embed/qpyclaw-node/code/node_main.py` |
| `/usr/board/board_*.py` | `embed/boards/ec800mcnle-audio-board/code/board_*.py` |

## Quick deploy

### 1. Assemble image (gather files from multiple repo dirs)

```powershell
python assemble.py --clean
```

### 2. Push to device via quecpython-dev-skill

Use `qpy_device_fs_cli.py` from the skill to push assembled files:

```powershell
# Push runtime files to /usr/
python scripts/qpy_device_fs_cli.py --json --port COM6 push --local output/usr/qpyclaw_node.py --remote-dir /usr --push-via repl
python scripts/qpy_device_fs_cli.py --json --port COM6 push --local output/usr/config.py --remote-dir /usr --push-via repl
# ... repeat for each file, or use host sync tool:

python tools/host/qpy_post_flash_recover.py --profile ec800mcnle-audio-board --port COM6 --json
```

### 3. Verify

```powershell
python scripts/qpy_device_fs_cli.py --json --port COM6 ls --path /usr --ls-via repl
python scripts/qpy_device_fs_cli.py --json --port COM6 run --path /usr/_main.py
```
