# Host Tools

## Standard Post-Flash Recovery

Use this as the canonical host entrypoint after firmware flashing or after
device `/usr` has been reset.

It chains:

1. `qpy_usr_mirror_sync.py`
2. optional board code sync
3. optional board media sync
4. `qpy_config_local_bootstrap.py`

Default behavior:

1. restore runtime files to `/usr`
2. if a matching board manifest exists, restore board-specific code to `/usr/board`
3. if a matching board media manifest exists, restore board-specific media to `/usr/media`
4. bootstrap board-profile-based `config_local.py`
5. protect an existing legacy `/usr/app/config_local.py` unless explicitly forced
6. optionally run runtime smoke with `--smoke`

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800kcnlc-dev-board --port COM14 --json
```

For `EC800MCNLE` audio-board bring-up, the same wrapper will now auto-pick the
matching board manifest and sync `/usr/board`:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800mcnle-audio-board --port COM19 --json
```

Skip board media sync:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800mcnle-audio-board --port COM19 --skip-board-media-sync --json
```

Dry run:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800kcnlc-dev-board --port COM14 --dry-run --json
```

Recovery plus smoke:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800kcnlc-dev-board --port COM14 --smoke --json
```

Recovery plus board probe:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800mcnle-audio-board --port COM19 --board-probe --json
```

## qpyclaw Runtime Smoke

Use this after recovery or after runtime refactors to confirm the device can
still:

1. import `/usr/config_local.py`
2. initialize `RuntimeState` and `ToolRunner`
3. execute `qpy.runtime.status`
4. execute `qpy.tools.catalog`
5. execute `qpy.fs.read`

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_runtime_smoke.py --port COM14 --json
```

For the `EC800MCNLE` audio board, use board smoke or board write smoke:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_runtime_smoke.py --port COM19 --board-smoke --json
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_runtime_smoke.py --port COM19 --board-write-smoke --json
```

`--board-write-smoke` currently checks and restores:

1. `qpy.audio.volume.set`
2. `qpy.audio.stream.open` / `qpy.audio.stream.close`
3. `qpy.power.charge.enable` / `qpy.power.charge.disable`
4. `qpy.ui.emotion.show`

## qpyclaw Board Runtime Probe

Use this during active `EC800MCNLE` board development when you want the
host to:

1. dispatch `/usr/qpyclaw_board_dispatch.py`
2. wait for board-thread bring-up
3. read `qpyclaw_node.debug_snapshot()`
4. run a small set of local board/runtime commands

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_runtime_probe.py --port COM19 --json
```

Keep raw REPL transcript:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_runtime_probe.py --port COM19 --include-raw --json
```

Probe current runtime without re-running dispatch:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_runtime_probe.py --port COM19 --skip-dispatch --json
```

## qpyclaw Voice ASR Smoke

Use this to verify end-to-end ASR on an EC800MCNLE device with the DashScope
voice sidecar.

Modes:

1. **natural** (default) — exec `_main.py`, let runtime auto-enter `listening`,
   user speaks into mic during the hands-off window, then query final state.
2. **manual** — exec `_main.py`, manually set up audio capture pipeline, record
   for N seconds, base64-encode, POST to sidecar `/api/asr`, print transcript.

Natural mode (user speaks during 60s hands-off window):

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_voice_asr_smoke.py --port COM6 --json
```

Manual mode (5s recording window):

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_voice_asr_smoke.py --port COM6 --mode manual --record-seconds 5 --json
```

## qpyclaw Voice Sidecar Health

Use this to health-check, deploy, or restart the DashScope voice sidecar on
the remote server via SSH.

Checks: HTTP reachability, systemd service status, recent journal logs, and
optionally a DashScope ASR probe with a known audio file.

Quick status:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_voice_sidecar_health.py --json
```

Full check with ASR probe:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_voice_sidecar_health.py --asr-probe --json
```

Deploy updated app.py and restart:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_voice_sidecar_health.py --deploy --restart --json
```

## OpenClaw Gateway Probe

Use this before changing device-side runtime config. It probes candidate
`ws://` and `wss://` endpoints from the host machine, then reports:

- plain HTTP/HTTPS response status on the same entrypoint
- websocket open success
- whether `connect.challenge` was received
- whether an OpenClaw `connect` request succeeded

Command:

```powershell
node C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\openclaw_gateway_probe.mjs --json
```

Optional:

```powershell
node C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\openclaw_gateway_probe.mjs --url ws://127.0.0.1:18789 --url wss://your-public-bridge.example.com --insecure
```

Notes:

- The script reads `~/.openclaw/openclaw.json` by default.
- Token output is masked.
- `--insecure` disables TLS certificate verification for quick `wss://` bridge tests.

## qpyclaw Server Ops

Use this when:

1. the official server-local `openclaw nodes ...` CLI is regressing
2. the desktop cannot stably complete direct raw RPC to the public gateway
3. you still need a practical operator path for `qpyclaw-node`

This script works by:

1. SSH into the OpenClaw server
2. run a server-local raw websocket RPC against `ws://127.0.0.1:18789`
3. execute `node.list` or `node.invoke`

It also auto-loads the gateway token from the remote:

`/home/openclaw/.openclaw/openclaw.json`

Node list:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_openclaw_server_ops.py --ssh-host your-openclaw-gateway.example.com --ssh-user root --ssh-password-env OPENCLAW_SSH_PASSWORD node-list --connected-only --json
```

Invoke board status:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_openclaw_server_ops.py --ssh-host your-openclaw-gateway.example.com --ssh-user root --ssh-password-env OPENCLAW_SSH_PASSWORD node-invoke --node your-node-id --command qpy.board.status --json
```

Invoke with params:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_openclaw_server_ops.py --ssh-host your-openclaw-gateway.example.com --ssh-user root --ssh-password-env OPENCLAW_SSH_PASSWORD node-invoke --node your-node-id --command qpy.audio.volume.set --param volume=6 --json
```

Direct public websocket mode:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_openclaw_server_ops.py --transport direct --ssh-host your-openclaw-gateway.example.com --gateway-token replace_with_real_gateway_token node-list --connected-only --json
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_openclaw_server_ops.py --transport direct --ssh-host your-openclaw-gateway.example.com --gateway-token replace_with_real_gateway_token node-invoke --node your-node-id --command qpy.runtime.status --json
```

Notes:

1. The script adds repo-root `.vendor` to `sys.path` so vendored `paramiko` can be used.
2. It is currently `ws://` only because it intentionally runs from the gateway host against local loopback.
3. It is a pragmatic operations bridge, not a replacement for upstream OpenClaw CLI.
4. `--param key=value` is the recommended way to pass simple invoke parameters from PowerShell.

## QuecPython TLS Matrix Probe

Use this to isolate whether an EC800K board is failing at:

- raw TCP
- `ussl.wrap_socket`
- HTTPS over TLS
- WebSocket Upgrade over TLS

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_tls_matrix_probe.py --port COM14 --json
```

## QuecPython Plain WS Probe

Use this when the board cannot complete TLS, but you still want to test whether
a public `ws://host:port` entrypoint is reachable over raw TCP.

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_plain_ws_probe.py --port COM14 --host your-public-bridge.example.com --port-num 10503 --path / --http --json
```

## QuecPython High-Level Network Probe

Use this when you need to verify whether official QuecPython-facing APIs fail
for the same reason as low-level `ussl`.

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_highlevel_net_probe.py --port COM14 --https-url https://your-openclaw-gateway.example.com:18790/ --json
```

## QuecPython usr_mirror Sync

Use this after firmware flashing when `/usr` has been reset and the
`qpyclaw-node` runtime must be restored from the local mirror.

The script now defaults to:

1. `embed/qpyclaw-node/deploy/runtime-manifest.json`
2. manifest allowlist push only
3. cleanup of manifest-declared stale runtime files
4. preservation of device-local `config_local.py` paths during transition

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_usr_mirror_sync.py --port COM14 --json
```

Dry run:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_usr_mirror_sync.py --port COM14 --dry-run --json
```

## qpyclaw Board Code Sync

Use this when you only want to update board-specific code under `/usr/board`
without touching the generic runtime.

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_code_sync.py --profile ec800mcnle-audio-board --port COM19 --json
```

Dry run:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_code_sync.py --profile ec800mcnle-audio-board --port COM19 --dry-run --json
```

## qpyclaw Board Media Sync

Use this when you want to sync board-local UI resources such as emoji PNGs to
the EC800MCNLE file-system media path:

`U:/media`

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_media_sync.py --profile ec800mcnle-audio-board --port COM19 --json
```

Dry run:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_media_sync.py --profile ec800mcnle-audio-board --port COM19 --dry-run --json
```

Notes:

1. This uses a manifest-driven sync, just like runtime and board-code sync.
2. This dedicated media sync exists because the generic `/usr` sync flow is not the right place to manage `U:/media`.
3. The current `EC800MCNLE` board UI code looks up emoji assets from `U:/media/<emotion>.png`.

## qpyclaw config_local Bootstrap

Use this to generate and optionally push a board-profile-based
`/usr/config_local.py` without overwriting an existing device config by
default. If legacy `/usr/app/config_local.py` still exists, bootstrap now
skips creating a new canonical file unless explicitly forced.

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_config_local_bootstrap.py --profile ec800kcnlc-dev-board --port COM14 --push --json
```

Non-destructive preview:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_config_local_bootstrap.py --profile ec800kcnlc-dev-board --show-content --json
```

## qpyclaw config_local Migrate

Use this to copy a legacy device config from `/usr/app/config_local.py` to the
canonical `/usr/config_local.py` without changing its content.

Command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_config_local_migrate.py --port COM19 --json
```
