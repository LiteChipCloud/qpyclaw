# Host Gateway Probe

## Purpose

Before changing `qpyclaw-node` runtime again, probe the candidate gateway
entrypoints from the host machine and separate:

1. transport reachability
2. websocket handshake reachability
3. OpenClaw `connect` reachability
4. node pairing / device-identity policy

## Probe Script

```text
tools/host/openclaw_gateway_probe.mjs
```

## Result Matrix

| URL | Role | Result |
| --- | --- | --- |
| `ws://127.0.0.1:18789` | `operator` | fully connected |
| `wss://282r41l383.oicp.vip` | `operator` | fully connected |
| `ws://282r41l383.oicp.vip:10503` | `operator` | timed out before websocket open |
| `wss://282r41l383.oicp.vip:10503` | `operator` | timed out before websocket open |
| `ws://127.0.0.1:18789` | `node` | transport OK, blocked by `NOT_PAIRED` |
| `wss://282r41l383.oicp.vip` | `node` | transport OK, blocked by `NOT_PAIRED` |

## Key Conclusion

The currently correct public host-side websocket entrypoint is:

```text
wss://282r41l383.oicp.vip
```

The currently wrong path for `qpyclaw-node` is:

```text
ws://282r41l383.oicp.vip:10503
```

and also:

```text
wss://282r41l383.oicp.vip:10503
```

## Meaning For qpyclaw-node

The next blocker is no longer “which public entrypoint works on the host”.
That has been narrowed down.

The remaining blockers are:

1. `EC800K` device-side TLS/WebSocket compatibility with `wss://282r41l383.oicp.vip`
2. OpenClaw `role=node` device identity / pairing requirement

## Evidence

```text
docs/bringup/evidence/2026-03-27-host-gateway-probe-summary.json
```
