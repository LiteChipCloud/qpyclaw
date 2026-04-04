## qpyclaw-node runtime (code)

This directory contains the production runtime modules that are synced to `/usr` during deployment.

- `qpyclaw_node.py`: the slim orchestrator that loads configuration, transport, tools, and voice hooks.
- `config.py`: configuration defaults plus helpers that load `/usr/config_local.py` (and legacy `/usr/app/config_local.py`).
- `transport.py`: WebSocket transport implementation used by the Official OpenClaw Gateway client.
- `tools.py`: command toolkit, tool catalog, and the `ToolRunner` used by host smoke scripts.
- `voice.py`: voice dialog client, ASR/TTS adapters, and operators.
- `node_main.py` & `dispatch.py`: board-aware loops that import `board_bootstrap` and the EC800MCNLE board extension.
- `_main.py`: development helper that bootstraps dispatch for manual smoke runs.

Host tooling relies on this directory, but all synchronization is driven by manifests in `../deploy/`. The manifest lists these files in the exact order they should appear under `/usr`, so the host sync scripts no longer point at the legacy `usr_mirror` tree.

If you need to extend runtime functionality, add modules here and update `deploy/runtime-manifest.json`. Keep `ws_client.py` and `cellular.py` in `embed/components/` and list them in the manifest so they copy alongside the runtime.
