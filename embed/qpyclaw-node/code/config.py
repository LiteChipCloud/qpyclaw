# config.py — Default runtime configuration for qpyclaw-node.
# Keep real credentials out of source control; use config_local.py overrides.

try:
    import usys as _sys
except Exception:
    import sys as _sys


def _ensure_import_path(path):
    try:
        if path and path not in _sys.path:
            _sys.path.append(path)
    except Exception:
        pass


class _Config(object):
    pass


config = _Config()
config.DEVICE_ID = "qpyclaw_demo_001"
config.DEVICE_NAME = "qpyclaw EC800K Node"
config.DEVICE_MODEL_HINT = "EC800KCNLC"
config.BOARD_PROFILE = "ec800kcnlc-no-peripheral"
config.TENANT_ID = "tenant_demo"
config.RUNTIME_VERSION = "0.1.0"

config.ACCESS_MODE = "ws_native"

config.OPENCLAW_WS_URL = "ws://127.0.0.1:18789"
config.OPENCLAW_ROLE = "node"
config.OPENCLAW_MIN_PROTOCOL = 3
config.OPENCLAW_MAX_PROTOCOL = 3
config.OPENCLAW_CLIENT_ID = "node-host"
config.OPENCLAW_CLIENT_MODE = "node"
config.OPENCLAW_CLIENT_PLATFORM = "quectel"
config.OPENCLAW_CLIENT_DEVICE_FAMILY = "quecpython"
config.OPENCLAW_CLIENT_DISPLAY_NAME = "qpyclaw QuecPython Node"
config.OPENCLAW_USER_AGENT = "qpyclaw-node/0.1.0"

config.OPENCLAW_AUTH_TOKEN = "replace_with_real_token"
config.OPENCLAW_DEVICE_AUTH_MODE = "none"
config.REMOTE_SIGNER_HTTP_URL = ""
config.REMOTE_SIGNER_HTTP_AUTH_TOKEN = ""
config.REMOTE_SIGNER_HTTP_TIMEOUT_SEC = 5
config.REMOTE_SIGNER_HTTP_HEADERS = {}
config.VOICE_ENABLED = False
config.VOICE_TRANSCRIPT_PROVIDER = ""
config.VOICE_ASR_HTTP_URL = ""
config.VOICE_ASR_HTTP_AUTH_TOKEN = ""
config.VOICE_ASR_HTTP_HEADERS = {}
config.VOICE_ASR_HTTP_TIMEOUT_SEC = 15
config.VOICE_ASR_FIXED_TRANSCRIPT = ""
config.VOICE_ASR_HTTP_AUDIO_FORMAT = "oggopus"
config.VOICE_ASR_HTTP_SAMPLE_RATE = 16000
config.VOICE_MAIN_SESSION_KEY = "main"
config.VOICE_OPERATOR_WS_URL = ""
config.VOICE_OPERATOR_AUTH_TOKEN = ""
config.VOICE_OPERATOR_REUSE_NODE_TOKEN = False
config.VOICE_OPERATOR_DEVICE_AUTH_MODE = ""
config.VOICE_OPERATOR_CLIENT_ID = "cli"
config.VOICE_OPERATOR_CLIENT_DISPLAY_NAME = "qpyclaw Voice Operator"
config.VOICE_OPERATOR_CLIENT_MODE = "cli"
config.VOICE_OPERATOR_ROLE = "operator"
config.VOICE_OPERATOR_SCOPES = ["operator.read", "operator.write"]
config.VOICE_OPERATOR_CAPS = []
config.VOICE_OPERATOR_COMMANDS = []
config.VOICE_OPERATOR_PERMISSIONS = {}
config.VOICE_OPERATOR_USER_AGENT = "qpyclaw-node/0.1.0 voice"
config.VOICE_OPERATOR_CONNECT_TIMEOUT_SEC = 12
config.VOICE_CHAT_TIMEOUT_MS = 45000
config.VOICE_CHAT_POLL_MS = 800
config.VOICE_CHAT_HISTORY_LIMIT = 12
config.VOICE_CHAT_SUBSCRIBE = True
config.VOICE_TTS_STREAM_ENABLED = False
config.VOICE_TTS_STREAM_URL = ""
config.VOICE_TTS_STREAM_AUTH_TOKEN = ""
config.VOICE_TTS_STREAM_HEADERS = {}
config.VOICE_TTS_STREAM_AUDIO_FORMAT = "pcm"
config.VOICE_TTS_STREAM_FORMAT = config.VOICE_TTS_STREAM_AUDIO_FORMAT
config.VOICE_TTS_STREAM_SAMPLE_RATE = 16000
config.VOICE_TTS_STREAM_CONNECT_TIMEOUT_SEC = 12
config.VOICE_TTS_STREAM_TIMEOUT_MS = 45000
config.VOICE_TTS_STREAM_RECV_TIMEOUT_MS = config.VOICE_TTS_STREAM_TIMEOUT_MS
config.VOICE_TTS_STREAM_END_GRACE_MS = 300
config.VOICE_TTS_STREAM_CLOSE_AFTER_PLAY = True
config.VOICE_TTS_STREAM_DRAIN_MS = 400

config.OPENCLAW_GENERIC_NODE_EVENTS = False
config.OPENCLAW_ALERT_UPLINK_MODE = "agent_request"
config.OPENCLAW_AGENT_REQUEST_SESSION_KEY = ""
config.OPENCLAW_AGENT_REQUEST_DELIVER = False
config.OPENCLAW_AGENT_REQUEST_CHANNEL = ""
config.OPENCLAW_AGENT_REQUEST_TO = ""
config.OPENCLAW_AGENT_REQUEST_RECEIPT = False
config.OPENCLAW_AGENT_REQUEST_RECEIPT_TEXT = "Device alert received."
config.OPENCLAW_AGENT_REQUEST_THINKING = "low"
config.OPENCLAW_AGENT_REQUEST_TIMEOUT_SECONDS = 0

config.HEARTBEAT_INTERVAL_SEC = 15
config.TELEMETRY_INTERVAL_SEC = 60
config.RECONNECT_BACKOFF_SEC = 5
config.CONNECT_TIMEOUT_SEC = 12
config.NETWORK_AUTO_RECOVER = True
config.NETWORK_READY_QUICK_TIMEOUT_SEC = 1
config.NETWORK_READY_TIMEOUT_SEC = 30
config.NETWORK_RECOVER_RETRY_INTERVAL_SEC = 15
config.NETWORK_FORCE_RECOVER_AFTER_CONNECT_FAILURES = 3
config.NETWORK_CFUN_COOLDOWN_SEC = 90
config.NETWORK_CFUN_OFF_MS = 1200
config.NETWORK_POST_CFUN_WAIT_SEC = 15
config.NETWORK_PROFILE_ID = 1
config.NETWORK_IPTYPE = 2
config.NETWORK_APN = ""
config.NETWORK_APN_USERNAME = ""
config.NETWORK_APN_PASSWORD = ""
config.NETWORK_APN_AUTH_TYPE = 0
config.NETWORK_ENFORCE_AUTO_ACTIVATE = True
config.NETWORK_ENFORCE_AUTO_CONNECT = True
config.NETWORK_ACTIVATE_ON_STAGE3 = True
config.NETWORK_CFUN_ON_STAGE2 = True
config.NETWORK_CFUN_ON_STAGE3 = True
config.NETWORK_CLOSE_TRANSPORT_ON_PDP_DOWN = True
config.ACK_TIMEOUT_MS = 10000
config.READ_POLL_MS = 200
config.MAX_CMD_EXEC_SEC = 30
config.OUTBOX_MAX = 64
config.DEDUPE_WINDOW = 64
config.MAX_RETRY = 3
config.OUTBOX_RETRY_BACKOFF_MS = 1000
config.SENSITIVE_MASK = True

config.FS_DEFAULT_ROOT = "/usr"
config.FS_ALLOW_ANY_PATH = True
config.FS_READ_MAX_BYTES = 4096
config.FS_WRITE_MAX_BYTES = 8192
config.FS_LIST_MAX_DEPTH = 4
config.REBOOT_RESULT_DELAY_MS = 1500

config.OPENCLAW_CAPS = [
    "cellular",
    "diagnostics",
    "filesystem",
    "network",
    "runtime",
]

config.OPENCLAW_COMMANDS = [
    "qpy.help",
    "qpy.device.info",
    "device.info",
    "qpy.device.status",
    "device.status",
    "qpy.device.reboot",
    "device.reboot",
    "qpy.net.diag",
    "net.diag",
    "qpy.net.ifconfig",
    "net.ifconfig",
    "qpy.sim.info",
    "sim.info",
    "qpy.cell.info",
    "cell.info",
    "qpy.runtime.status",
    "runtime.status",
    "qpy.tools.catalog",
    "tools.catalog",
    "qpy.fs.list",
    "qpy.fs.ls",
    "fs.list",
    "fs.ls",
    "qpy.fs.tree",
    "fs.tree",
    "qpy.fs.read",
    "fs.read",
    "qpy.fs.write",
    "fs.write",
    "qpy.fs.mkdir",
    "fs.mkdir",
    "qpy.fs.remove",
    "fs.remove",
    "qpy.repl.run",
    "repl.run",
    "qpy.push",
    "push",
    "qpy.voice.status",
    "voice.status",
    "qpy.voice.chat",
    "voice.chat",
    "qpy.voice.abort",
    "voice.abort",
]

config.ALLOW_TOOLS = ["*"]
config.OPENCLAW_SCOPES = []
config.OPENCLAW_PERMISSIONS = {}

config.SAFE_MODE = False
config.SAFE_MODE_FAILURE_THRESHOLD = 6
config.SAFE_MODE_COOLDOWN_SEC = 30
config.FW_VERSION = config.RUNTIME_VERSION
config.CONFIG_LOCAL_LOADED = False
config.CONFIG_LOCAL_ERROR = ""
config.CONFIG_LOCAL_SOURCE = ""




def _apply_local_override(module_obj):
    for name in dir(module_obj):
        if not name:
            continue
        if name[:1] == "_":
            continue
        setattr(config, name, getattr(module_obj, name))


def _record_config_local_source(module_obj):
    try:
        config.CONFIG_LOCAL_SOURCE = str(getattr(module_obj, "__file__", "") or "")
    except Exception:
        config.CONFIG_LOCAL_SOURCE = ""


for _path in ("/usr", "usr"):
    _ensure_import_path(_path)

try:
    _config_local = __import__("config_local", globals(), locals(), ["config_local"])
    _apply_local_override(_config_local)
    _record_config_local_source(_config_local)
    config.CONFIG_LOCAL_LOADED = True
    config.CONFIG_LOCAL_ERROR = ""
except Exception as e:
    config.CONFIG_LOCAL_ERROR = str(e)
    for _path in ("/usr/app", "app"):
        _ensure_import_path(_path)
    try:
        _config_local = __import__("config_local", globals(), locals(), ["config_local"])
        _apply_local_override(_config_local)
        _record_config_local_source(_config_local)
        config.CONFIG_LOCAL_LOADED = True
        config.CONFIG_LOCAL_ERROR = ""
    except Exception:
        pass
