# Reverse Proxy

This directory holds host-side gateway exposure templates for `qpyclaw-node`
public access.

Current preferred path for cellular devices:

```text
EC800K qpyclaw-node
  -> wss://public-host:public-port
  -> PeanutShell TCP mapping
  -> local TLS terminator
  -> OpenClaw Gateway (plain ws/http)
```

Why:

- `ws://` over a custom public port may be intercepted by the carrier HTTP path.
- `wss://` keeps the outer transport opaque to that HTTP interception layer.
- The local OpenClaw Gateway at `127.0.0.1:18789` is plain websocket/http, so it
  needs a TLS terminator in front of it before being exposed as `wss://`.

Templates:

- `stunnel/openclaw-wss-stunnel.conf.example`
- `caddy/Caddyfile.example`
- `node-tls-bridge/openclaw_tls_bridge.mjs`
