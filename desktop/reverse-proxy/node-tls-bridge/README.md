# Node TLS Bridge

This is the simplest Windows-native path when:

- OpenClaw Gateway already runs locally on `127.0.0.1:18789`
- you want `qpyclaw-node` to use `wss://`
- you do not want to install `stunnel` or `Caddy`

## Topology

```text
qpyclaw-node
  -> wss://your-public-bridge.example.com:10503
  -> PeanutShell TCP 10503
  -> 127.0.0.1:18443
  -> node openclaw_tls_bridge.mjs
  -> 127.0.0.1:18789
  -> OpenClaw Gateway
```

## 1. Generate A PFX

PowerShell:

```powershell
Set-Location C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\desktop\reverse-proxy\node-tls-bridge
.\generate-self-signed-pfx.ps1 -DnsName your-public-bridge.example.com -OutDir .\certs -Password "replace_with_dev_passphrase"
```

## 2. Start The TLS Bridge

PowerShell:

```powershell
$env:TLS_BRIDGE_LISTEN_HOST = "127.0.0.1"
$env:TLS_BRIDGE_LISTEN_PORT = "18443"
$env:TLS_BRIDGE_UPSTREAM_HOST = "127.0.0.1"
$env:TLS_BRIDGE_UPSTREAM_PORT = "18789"
$env:TLS_BRIDGE_PFX_FILE = "C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\desktop\reverse-proxy\node-tls-bridge\certs\openclaw-tls-bridge.pfx"
$env:TLS_BRIDGE_PFX_PASSPHRASE = "replace_with_dev_passphrase"
node .\openclaw_tls_bridge.mjs
```

Expected log:

```text
[tls-bridge] listening on 127.0.0.1:18443, forwarding to 127.0.0.1:18789
```

## 3. Change PeanutShell TCP Mapping

Change the current TCP mapping target:

```text
from: 127.0.0.1:18789
to:   127.0.0.1:18443
```

Public address remains:

```text
your-public-bridge.example.com:10503
```

## 4. Device URL

Set device local override to:

```python
OPENCLAW_WS_URL = "wss://your-public-bridge.example.com:10503"
```

## Notes

- For current QuecPython probe purposes, a self-signed cert is acceptable if the
  module-side TLS stack does not enforce CA validation.
- For browser/UI and production deployment, replace the self-signed cert with a
  trusted certificate strategy.
