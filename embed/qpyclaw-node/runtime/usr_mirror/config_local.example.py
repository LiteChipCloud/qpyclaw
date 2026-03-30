# Generic qpyclaw-node local config example.
# Copy to /usr/config_local.py on the device or keep an untracked local copy.
# Do not commit real tokens or real gateway endpoints.

DEVICE_ID = "qpyclaw_demo_node_001"
DEVICE_NAME = "qpyclaw Demo Node"
DEVICE_MODEL_HINT = "EC800KCNLC"
BOARD_PROFILE = "ec800kcnlc-sim-only"

OPENCLAW_WS_URL = "ws://your-openclaw-gateway.example.com:18789"
OPENCLAW_AUTH_TOKEN = "replace_with_real_gateway_token"
OPENCLAW_CLIENT_ID = "node-host"
OPENCLAW_CLIENT_DISPLAY_NAME = "qpyclaw Demo Node"
TENANT_ID = "tenant_demo"

# Start with token-only mode first.
OPENCLAW_DEVICE_AUTH_MODE = "none"

# If the official gateway requires signed device identity, switch to:
# OPENCLAW_DEVICE_AUTH_MODE = "remote_signer_http"
# REMOTE_SIGNER_HTTP_URL = "http://your-signer.example.com:8787/sign"
# REMOTE_SIGNER_HTTP_AUTH_TOKEN = "replace_with_real_signer_token"

# Recommended to keep auto-recover enabled on cellular devices.
NETWORK_AUTO_RECOVER = True
RECONNECT_BACKOFF_SEC = 5
NETWORK_READY_TIMEOUT_SEC = 30
NETWORK_FORCE_RECOVER_AFTER_CONNECT_FAILURES = 3
