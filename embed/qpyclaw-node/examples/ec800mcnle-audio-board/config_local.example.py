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

# Optional: text voice dialog over the Official OpenClaw Gateway.
# Current verified path:
# 1. keep the node side on `remote_signer_http`
# 2. enable voice with the same gateway URL
# 3. reuse the node token first
# 4. the first operator(cli) connect may return `NOT_PAIRED: pairing required`
# 5. approve the latest pending device once on the gateway, then retry
#
# VOICE_ENABLED = True
# BOARD_OPEN_AUDIO = True
# BOARD_VOICE_ENABLED = True
# BOARD_VOICE_AUTO_START = True
# VOICE_MAIN_SESSION_KEY = "main"
# VOICE_OPERATOR_WS_URL = OPENCLAW_WS_URL
# VOICE_OPERATOR_REUSE_NODE_TOKEN = True
# VOICE_OPERATOR_CLIENT_ID = "cli"
# VOICE_OPERATOR_CLIENT_MODE = "cli"
# VOICE_OPERATOR_CLIENT_DISPLAY_NAME = "qpyclaw voice cli"
# VOICE_CHAT_SUBSCRIBE = False

# Optional: board-local audio -> qpyclaw voice sidecar -> transcript -> Official OpenClaw.
# Recommended first deployment path:
# 1. run `tools/runtime_local/voice_sidecar/app.py` on your public server
# 2. point the device to `/api/asr`
# 3. keep OpenClaw itself on the text path
# 4. after ASR is stable, add `/api/tts` for local speaker playback
#
# If configured, `voice_session_main.example.py` can reuse the board-local
# KWS/VAD pipeline and inject the returned transcript into the existing
# OpenClaw voice text chain.
#
# VOICE_TRANSCRIPT_PROVIDER = "remote_asr_http"
# VOICE_ASR_HTTP_URL = "https://your-voice-sidecar.example.com:8788/api/asr"
# VOICE_ASR_HTTP_AUTH_TOKEN = "replace_with_real_proxy_token"
# VOICE_ASR_HTTP_HEADERS = {"X-Device-Class": "qpyclaw-node"}
# VOICE_ASR_HTTP_AUDIO_FORMAT = "opus"
# VOICE_ASR_HTTP_SAMPLE_RATE = 16000
#
# Optional: cloud TTS -> local speaker playback.
# If `VOICE_TTS_HTTP_URL` is omitted, the board extension will try to derive
# it from `VOICE_ASR_HTTP_URL` by replacing `/api/asr` with `/api/tts`.
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
# Recommended once the board speaker path is stable:
# bypass `/usr` file writes and stream PCM chunks directly from the sidecar.
#
# VOICE_TTS_STREAM_ENABLED = True
# VOICE_TTS_STREAM_URL = "ws://your-voice-sidecar.example.com:8788/ws/tts"
# VOICE_TTS_STREAM_AUTH_TOKEN = "replace_with_real_proxy_token"
# VOICE_TTS_STREAM_HEADERS = {"X-Device-Class": "qpyclaw-node"}
# VOICE_TTS_STREAM_AUDIO_FORMAT = "pcm"
# VOICE_TTS_STREAM_SAMPLE_RATE = 16000
# VOICE_TTS_STREAM_TIMEOUT_MS = 45000
# VOICE_TTS_STREAM_DRAIN_MS = 400

# Quickest device-side smoke for the new transcript provider skeleton.
# This path does not call a real ASR service. It lets the board-local voice
# controller turn captured audio into a fixed transcript first, so the local
# capture/provider/session chain can be verified before real cloud ASR access.
#
# VOICE_TRANSCRIPT_PROVIDER = "mock"
# VOICE_ASR_FIXED_TRANSCRIPT = "This is fixed transcript smoke."
#
# Smoke-only shortcut without a real ASR service:
# VOICE_TRANSCRIPT_PROVIDER = "fixed"
# VOICE_ASR_FIXED_TRANSCRIPT = "Please tell me who you are."
