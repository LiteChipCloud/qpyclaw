# qpyclaw-node Deploy

This directory holds deployment control files for `qpyclaw-node`.

## Runtime Manifest

`runtime-manifest.json` is the explicit allowlist for files that may be
deployed from `embed/qpyclaw-node/code/` to device `/usr`.

It defines:

1. `local_root_rel`: the source code root (now pointing at `../code`)
2. `remote_root`: the device-side target root
3. `files`: files allowed to be pushed
4. `preserve_remote_files`: device-local files that should not be managed
5. `remove_remote_files`: known stale runtime files that should be cleaned

## Board Manifests

`board-manifests/*.json` are explicit allowlists for board-specific code that
should be deployed separately from the generic runtime.

Current example:

1. `board-manifests/ec800mcnle-audio-board.json`
2. `board-manifests/ec800mcnle-audio-board-media.json`

This keeps the split explicit and ensures the board media manifest points at `U:/media` (the path checked by `BoardEmojiUi`).

1. generic runtime -> `/usr`
2. board-specific code -> `/usr/board`
3. board-specific media -> `U:/media`

Current standard runtime payload (the files the manifest copies to `/usr`):

1. `/usr/_main.py` — entry point
2. `/usr/config.py` — default config + local override loader
3. `/usr/qpyclaw_node.py` — slim orchestrator
4. `/usr/transport.py` — WebSocket transport layer
5. `/usr/tools.py` — tool system + command worker
6. `/usr/voice.py` — voice dialog client
7. `/usr/dispatch.py` — thread dispatch for board main
8. `/usr/node_main.py` — board-aware main loop
9. optional `/usr/config_local.py` — device-local credentials

Component files are still pulled from `embed/components/` and deployed to `/usr/`:

1. `/usr/ws_client.py` — portable WebSocket client
2. `/usr/cellular.py` — cellular network manager

Legacy compatibility note:

1. `config.py` loads `config_local.py` overrides automatically.
2. `/usr/config_local.py` is the canonical credentials file.
3. `/usr/app/config_local.py` is still accepted during transition but should not be relied on for new flows.

## config_local Profiles

`config-local-profiles.json` is the board-profile registry used to bootstrap
device-local `/usr/config_local.py` without overwriting an existing device
config by default.

Recommended standard recovery command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800kcnlc-dev-board --port COM11 --json
```

Recommended bootstrap command:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_config_local_bootstrap.py --profile ec800kcnlc-dev-board --port COM11 --push --json
```

## Recommended Command

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_usr_mirror_sync.py --port COM11 --json
```

Board-only sync:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_code_sync.py --profile ec800mcnle-audio-board --port COM19 --json
```

Board media-only sync:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_media_sync.py --profile ec800mcnle-audio-board --port COM19 --json
```

Recovery with board sync:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800mcnle-audio-board --port COM19 --json
```

Recovery without board media sync:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_post_flash_recover.py --profile ec800mcnle-audio-board --port COM19 --skip-board-media-sync --json
```

## Dry Run

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_usr_mirror_sync.py --port COM11 --dry-run --json
```
