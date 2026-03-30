# Copy this file to `config_local.py` only on the target device or in an
# untracked local workspace. Do not commit real tokens.
#
# This example belongs to:
# `embed/qpyclaw-node/examples/ec800mcnle-audio-board/`
#
# Prefer using `tools/host/qpy_config_local_bootstrap.py` for first-flash
# bring-up so board-profile defaults and non-overwrite behavior stay
# standardized.

DEVICE_ID = "qpyclaw_ec800m_audio_001"
DEVICE_NAME = "qpyclaw EC800M Audio Node"
BOARD_PROFILE = "ec800mcnle-audio-board"

OPENCLAW_WS_URL = "wss://your-public-openclaw-gateway.example.com:10503"
OPENCLAW_AUTH_TOKEN = "replace_with_real_gateway_token"

# Official cloud / strict gateway note:
# If the gateway returns `NOT_PAIRED: device identity required`, switch from the
# token-only path to the official signed-device path below.
# OPENCLAW_CLIENT_ID = "node-host"
# OPENCLAW_CLIENT_DISPLAY_NAME = "qpyclaw EC800M Audio Node"
# OPENCLAW_DEVICE_AUTH_MODE = "remote_signer_http"
# REMOTE_SIGNER_HTTP_URL = "http://your-signer.example.com:8787/sign"
# REMOTE_SIGNER_HTTP_AUTH_TOKEN = "replace_me"
# TENANT_ID = "tenant_demo"
