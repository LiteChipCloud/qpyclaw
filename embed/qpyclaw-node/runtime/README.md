## qpyclaw-node runtime

This runtime targets QuecPython devices and currently focuses on the
non-peripheral feature set that can be brought up on an `EC800KCNLC`
board without extra hardware.

`runtime/` is the deployable runtime slice only. Board-specific examples
and sample configs should live under `../examples/<board>/`, not inside
`runtime/`.

Recommended deployment path:

1. Keep runtime source files under `usr_mirror/`
2. Use `../deploy/runtime-manifest.json` as the allowlist
3. Use host script `tools/host/qpy_post_flash_recover.py` as the canonical
   post-flash recovery entrypoint
4. Use `tools/host/qpy_usr_mirror_sync.py` directly only when lower-level
   runtime-only sync is needed

Manual fallback is still possible, but the manifest-driven sync flow is the
canonical deployment path.

For real gateway credentials, keep the repository defaults unchanged and
use host bootstrap script
`tools/host/qpy_config_local_bootstrap.py` to generate or push a
device-local `/usr/config_local.py`.
Single-file runtime compatibility still accepts legacy `/usr/app/config_local.py`
during transition, but `/usr/config_local.py` is the canonical target.
Reference templates now live under:

- `usr_mirror/config_local.example.py`
- `../examples/ec800kcnlc-dev-board/config_local.example.py`
- `../examples/ec800mcnle-audio-board/config_local.example.py`

Bootstrap is still the canonical first-flash flow because it keeps board
profiles and non-overwrite behavior standardized.

Recommended public gateway deployment flow:
- Keep `config.py` on demo-safe defaults only.
- Set `OPENCLAW_WS_URL` and `OPENCLAW_AUTH_TOKEN` in `config_local.py`.
- Use a public websocket endpoint such as a PeanutHull TCP mapping.
- Prefer the public mapped address over `127.0.0.1` for SIM-based nodes.

Current scope:
- Official OpenClaw Gateway websocket mode
- Device, SIM, network, cell, runtime, and filesystem tools
- OpenClaw-compatible aliases for `qpy.help`, `qpy.fs.ls`,
  `qpy.fs.tree`, `qpy.repl.run`, and `qpy.push`
- Reconnect, dedupe, and basic outbox handling
- Scheduled reboot after result acknowledgement

Out of scope in this runtime slice:
- Audio capture/playback
- Screen UI
- Camera
- External bus and sensor peripherals
