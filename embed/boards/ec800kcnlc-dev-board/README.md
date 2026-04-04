# EC800KCNLC Dev Board

This profile represents the minimal bring-up platform for `qpyclaw-node`. Because the EC800KCNLC dev board lacks display/audio peripherals, it is ideal for bootstrapping the gateway connection and verifying the runtime basics before adding the EC800MCNLE board extension.

## What lives here

- The runtime remains under `embed/qpyclaw-node/code/`. Nothing new sits inside the `boards/ec800kcnlc-dev-board/` directory besides this documentation and a reference config in `examples/ec800kcnlc-dev-board/`.
- When flashing an EC800K board, point `qpy_post_flash_recover.py --profile ec800kcnlc-dev-board` at `/usr` so that `qpyclaw_node.py`, `config.py`, `tools.py`, `dispatch.py`, etc. end up under `/usr`.
- For networking validation, use the host smoke scripts listed in `tools/host/README.md`.

## Bring-up flow

1. Recover runtime to `/usr` using the manifest in `embed/qpyclaw-node/deploy/runtime-manifest.json`.
2. Push `config_local.py` via `tools/host/qpy_config_local_bootstrap.py --profile ec800kcnlc-dev-board`.
3. Start the runtime on-device:

```python
import qpyclaw_node
qpyclaw_node.run()
```

4. Use `tools/host/qpy_runtime_smoke.py --port <COM>` to verify `qpy.runtime.status`, `qpy.tools.catalog`, and filesystem commands.

This dev board remains the canonical starting point because it isolates the networking/runtime stack before layering in the EC800MCNLE display/audio features.
