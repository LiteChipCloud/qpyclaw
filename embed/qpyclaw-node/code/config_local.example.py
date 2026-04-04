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

# Optional: text voice dialog over the Official OpenClaw Gateway.
# Verified minimum path:
# 1. `OPENCLAW_DEVICE_AUTH_MODE = "remote_signer_http"`
# 2. `VOICE_OPERATOR_CLIENT_ID = "cli"`
# 3. `VOICE_OPERATOR_CLIENT_MODE = "cli"`
# 4. `VOICE_OPERATOR_REUSE_NODE_TOKEN = True`
# 5. first operator(cli) repair pairing may require one gateway approval
#
# VOICE_ENABLED = True
# BOARD_OPEN_AUDIO = True
# BOARD_VOICE_ENABLED = True
# BOARD_VOICE_AUTO_START = True
# VOICE_MAIN_SESSION_KEY = "main"
# VOICE_OPERATOR_WS_URL = OPENCLAW_WS_URL
# VOICE_OPERATOR_REUSE_NODE_TOKEN = True
# VOICE_OPERATOR_DEVICE_AUTH_MODE = "none"
# VOICE_OPERATOR_CLIENT_ID = "cli"
# VOICE_OPERATOR_CLIENT_MODE = "cli"
# VOICE_OPERATOR_CLIENT_DISPLAY_NAME = "qpyclaw voice cli"
# VOICE_CHAT_SUBSCRIBE = False
#
# Optional: board-local audio -> qpyclaw voice sidecar -> transcript -> Official OpenClaw.
# Recommended first deployment path:
# 1. run `tools/runtime_local/voice_sidecar/app.py` on your public server
# 2. point the device to `/api/asr`
# 3. keep OpenClaw itself on the text path
# 4. after ASR is stable, add `/api/tts` for local speaker playback
#
# HTTP ASR mode expects JSON with `text`, `transcript`, `result.text`, or
# `data.text`.
#
# VOICE_TRANSCRIPT_PROVIDER = "remote_asr_http"
# VOICE_ASR_HTTP_URL = "https://your-voice-sidecar.example.com:8788/api/asr"
# VOICE_ASR_HTTP_AUTH_TOKEN = "replace_with_real_proxy_token"
# VOICE_ASR_HTTP_HEADERS = {"X-Device-Class": "qpyclaw-node"}
# VOICE_ASR_HTTP_AUDIO_FORMAT = "opus"
# VOICE_ASR_HTTP_SAMPLE_RATE = 16000
#
# Optional: cloud TTS -> local speaker playback.
# If `VOICE_TTS_HTTP_URL` is omitted, the board extension can derive it from
# `VOICE_ASR_HTTP_URL` when the sidecar exposes `/api/tts`.
#
# VOICE_TTS_HTTP_ENABLED = True
# VOICE_TTS_HTTP_URL = "https://your-voice-sidecar.example.com:8788/api/tts"
# VOICE_TTS_HTTP_AUTH_TOKEN = "replace_with_real_proxy_token"
# VOICE_TTS_HTTP_HEADERS = {"X-Device-Class": "qpyclaw-node"}
# VOICE_TTS_HTTP_AUDIO_FORMAT = "mp3"
# VOICE_TTS_HTTP_SAMPLE_RATE = 16000
# VOICE_TTS_HTTP_VOICE = "Cherry"
# VOICE_TTS_HTTP_CACHE_PATH = "/usr/qpyclaw/voice_reply.mp3"
# VOICE_TTS_HTTP_PLAY_TIMEOUT_MS = 20000
#
# Recommended when `/usr` space is tight:
# stream PCM chunks directly from the sidecar without local file caching.
#
# VOICE_TTS_STREAM_ENABLED = True
# VOICE_TTS_STREAM_URL = "ws://your-voice-sidecar.example.com:8788/ws/tts"
# VOICE_TTS_STREAM_AUTH_TOKEN = "replace_with_real_proxy_token"
# VOICE_TTS_STREAM_HEADERS = {"X-Device-Class": "qpyclaw-node"}
# VOICE_TTS_STREAM_AUDIO_FORMAT = "pcm"
# VOICE_TTS_STREAM_SAMPLE_RATE = 16000
# VOICE_TTS_STREAM_TIMEOUT_MS = 45000
# VOICE_TTS_STREAM_DRAIN_MS = 400
#
# Smoke-only shortcut without a real ASR service:
# VOICE_TRANSCRIPT_PROVIDER = "fixed"
# VOICE_ASR_FIXED_TRANSCRIPT = "Who are you?"

# Recommended to keep auto-recover enabled on cellular devices.
NETWORK_AUTO_RECOVER = True
RECONNECT_BACKOFF_SEC = 5
NETWORK_READY_TIMEOUT_SEC = 30
NETWORK_FORCE_RECOVER_AFTER_CONNECT_FAILURES = 3
