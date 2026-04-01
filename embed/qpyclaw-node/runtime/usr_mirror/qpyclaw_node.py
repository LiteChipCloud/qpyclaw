# Generic qpyclaw-node runtime configuration.
# Keep real credentials out of source control.

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

import utime


def _wall_time_ms():
    try:
        return int(utime.time() * 1000)
    except Exception:
        return 0


def _sleep_ms(delay_ms):
    value = int(delay_ms or 0)
    if value <= 0:
        return
    if hasattr(utime, "sleep_ms"):
        utime.sleep_ms(value)
        return
    utime.sleep(value / 1000.0)


class RuntimeState(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.boot_ms = utime.ticks_ms()
        self.boot_wall_ms = _wall_time_ms()
        self.online = False
        self.node_id = cfg.DEVICE_ID
        self.logical_device_id = cfg.DEVICE_ID
        self.protocol = 0
        self.device_token = ""
        self.connect_attempts = 0
        self.connect_successes = 0
        self.consecutive_failures = 0
        self.safe_mode = False
        self.last_connect_ms = 0
        self.last_disconnect_ms = 0
        self.last_error = ""
        self.last_error_code = ""
        self.last_error_ms = 0
        self.last_event = ""
        self.last_event_ms = 0
        self.last_cmd_id = ""
        self.last_cmd_tool = ""
        self.last_cmd_ms = 0
        self.last_ack_ms = 0
        self.reconnect_count = 0
        self.sent_frames = 0
        self.received_frames = 0
        self.pending_cmds = 0
        self.outbox_depth = 0
        self.result_cache_depth = 0
        self.last_hello = None
        self.last_signer = None
        self.last_tick_ms = 0
        self.last_close_reason = ""
        self.last_close_ms = 0
        self.last_outbox_error = ""
        self.last_outbox_error_ms = 0
        self.inflight_cmd_id = ""
        self.inflight_cmd_tool = ""
        self.tool_exec_started_ms = 0
        self.tool_exec_finished_ms = 0
        self.last_exec_status = ""
        self.last_exec_result_code = ""
        self.worker_available = False
        self.worker_busy = False
        self.last_probe_tool = ""
        self.last_probe_duration_ms = 0
        self.last_probe_timings = {}
        self.last_probe_ts_ms = 0
        self.pending_reboot_mode = ""
        self.pending_reboot_due_ms = 0
        self.pending_reboot_requested_ms = 0
        self.last_reboot_mode = ""
        self.last_reboot_request_ms = 0

    def note_connecting(self):
        self.connect_attempts += 1

    def note_connect(self, node_id, protocol, hello_payload):
        self.online = True
        self.node_id = node_id or self.cfg.DEVICE_ID
        self.protocol = protocol or 0
        self.connect_successes += 1
        self.consecutive_failures = 0
        self.safe_mode = False
        self.last_connect_ms = utime.ticks_ms()
        self.last_hello = hello_payload

    def note_connect_failure(self, code, message):
        self.online = False
        self.consecutive_failures += 1
        self.note_error(code, message)
        threshold = int(getattr(self.cfg, "SAFE_MODE_FAILURE_THRESHOLD", 6))
        if getattr(self.cfg, "SAFE_MODE", False) and self.consecutive_failures >= threshold:
            self.safe_mode = True

    def note_disconnect(self):
        if self.online:
            self.reconnect_count += 1
        self.online = False
        self.last_disconnect_ms = utime.ticks_ms()

    def note_close(self, reason):
        self.last_close_reason = reason or ""
        self.last_close_ms = utime.ticks_ms()

    def note_error(self, code, message):
        self.last_error_code = code or ""
        self.last_error = message or ""
        self.last_error_ms = utime.ticks_ms()

    def note_outbox_error(self, message):
        self.last_outbox_error = message or ""
        self.last_outbox_error_ms = utime.ticks_ms()

    def note_event(self, event_name):
        self.last_event = event_name or ""
        self.last_event_ms = utime.ticks_ms()

    def note_command(self, cmd_id, tool):
        self.last_cmd_id = cmd_id or ""
        self.last_cmd_tool = tool or ""
        self.last_cmd_ms = utime.ticks_ms()

    def note_sent(self):
        self.sent_frames += 1

    def note_received(self):
        self.received_frames += 1

    def note_ack(self):
        self.last_ack_ms = utime.ticks_ms()

    def note_tick(self):
        self.last_tick_ms = utime.ticks_ms()

    def note_inflight_start(self, cmd_id, tool):
        self.inflight_cmd_id = cmd_id or ""
        self.inflight_cmd_tool = tool or ""
        self.tool_exec_started_ms = utime.ticks_ms()
        self.tool_exec_finished_ms = 0

    def note_inflight_finish(self, status, result_code):
        self.tool_exec_finished_ms = utime.ticks_ms()
        self.last_exec_status = status or ""
        self.last_exec_result_code = result_code or ""
        self.inflight_cmd_id = ""
        self.inflight_cmd_tool = ""

    def note_worker_status(self, available, busy):
        self.worker_available = bool(available)
        self.worker_busy = bool(busy)

    def note_probe_metrics(self, tool, duration_ms, timings):
        self.last_probe_tool = tool or ""
        self.last_probe_duration_ms = int(duration_ms or 0)
        if isinstance(timings, dict):
            self.last_probe_timings = timings
        else:
            self.last_probe_timings = {}
        self.last_probe_ts_ms = utime.ticks_ms()

    def update_queue_depths(self, pending_cmds, outbox_depth, result_cache_depth):
        self.pending_cmds = int(pending_cmds)
        self.outbox_depth = int(outbox_depth)
        self.result_cache_depth = int(result_cache_depth)

    def request_reboot(self, mode, delay_ms):
        if delay_ms is None:
            delay_ms = 0
        if delay_ms < 0:
            delay_ms = 0
        now = utime.ticks_ms()
        self.pending_reboot_mode = mode or "soft"
        self.pending_reboot_requested_ms = now
        self.pending_reboot_due_ms = utime.ticks_add(now, int(delay_ms))
        self.last_reboot_mode = self.pending_reboot_mode
        self.last_reboot_request_ms = now

    def pending_reboot_due(self):
        if not self.pending_reboot_mode:
            return None
        if utime.ticks_diff(utime.ticks_ms(), self.pending_reboot_due_ms) >= 0:
            return {
                "mode": self.pending_reboot_mode,
                "requested_ms": self.pending_reboot_requested_ms,
            }
        return None

    def clear_pending_reboot(self):
        self.pending_reboot_mode = ""
        self.pending_reboot_due_ms = 0
        self.pending_reboot_requested_ms = 0

    def snapshot(self):
        return {
            "online": self.online,
            "node_id": self.node_id,
            "logical_device_id": self.logical_device_id,
            "protocol": self.protocol,
            "boot_ms": self.boot_ms,
            "boot_wall_ms": self.boot_wall_ms,
            "last_connect_ms": self.last_connect_ms,
            "last_disconnect_ms": self.last_disconnect_ms,
            "last_error_code": self.last_error_code,
            "last_error": self.last_error,
            "last_error_ms": self.last_error_ms,
            "last_event": self.last_event,
            "last_event_ms": self.last_event_ms,
            "last_cmd_id": self.last_cmd_id,
            "last_cmd_tool": self.last_cmd_tool,
            "last_cmd_ms": self.last_cmd_ms,
            "last_ack_ms": self.last_ack_ms,
            "connect_attempts": self.connect_attempts,
            "connect_successes": self.connect_successes,
            "consecutive_failures": self.consecutive_failures,
            "reconnect_count": self.reconnect_count,
            "safe_mode": self.safe_mode,
            "sent_frames": self.sent_frames,
            "received_frames": self.received_frames,
            "pending_cmds": self.pending_cmds,
            "outbox_depth": self.outbox_depth,
            "result_cache_depth": self.result_cache_depth,
            "device_token_cached": bool(self.device_token),
            "last_signer": self.last_signer,
            "last_tick_ms": self.last_tick_ms,
            "last_close_reason": self.last_close_reason,
            "last_close_ms": self.last_close_ms,
            "last_outbox_error": self.last_outbox_error,
            "last_outbox_error_ms": self.last_outbox_error_ms,
            "inflight_cmd_id": self.inflight_cmd_id,
            "inflight_cmd_tool": self.inflight_cmd_tool,
            "tool_exec_started_ms": self.tool_exec_started_ms,
            "tool_exec_finished_ms": self.tool_exec_finished_ms,
            "last_exec_status": self.last_exec_status,
            "last_exec_result_code": self.last_exec_result_code,
            "worker_available": self.worker_available,
            "worker_busy": self.worker_busy,
            "last_probe_tool": self.last_probe_tool,
            "last_probe_duration_ms": self.last_probe_duration_ms,
            "last_probe_timings": self.last_probe_timings,
            "last_probe_ts_ms": self.last_probe_ts_ms,
            "pending_reboot": bool(self.pending_reboot_mode),
            "pending_reboot_mode": self.pending_reboot_mode,
            "pending_reboot_requested_ms": self.pending_reboot_requested_ms,
            "last_reboot_mode": self.last_reboot_mode,
            "last_reboot_request_ms": self.last_reboot_request_ms,
        }

import utime

try:
    import ubinascii
except Exception:
    ubinascii = None


def safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def safe_call(func, *args):
    if not func:
        return None
    try:
        return func(*args)
    except Exception:
        return None


def ok_value(value):
    return value not in (None, -1, "")


def mask_value(value, enabled):
    if (not enabled) or (not ok_value(value)):
        return value
    text = str(value)
    if len(text) <= 8:
        return text
    return text[:4] + ("*" * (len(text) - 8)) + text[-4:]


def wall_time_ms():
    try:
        return int(utime.time() * 1000)
    except Exception:
        return 0


def measure_step(step_name, timings, func, *args):
    started = utime.ticks_ms()
    result = func(*args)
    if isinstance(timings, dict):
        timings[step_name] = utime.ticks_diff(utime.ticks_ms(), started)
    return result


def safe_attr_call(module, names, *args):
    if not module:
        return None, ""
    for name in names:
        if hasattr(module, name):
            return safe_call(getattr(module, name), *args), name
    return None, ""


def parse_reg_entry(entry):
    if (not isinstance(entry, (list, tuple))) or len(entry) < 6:
        return None
    return {
        "state": entry[0],
        "lac": entry[1],
        "cid": entry[2],
        "rat": entry[3],
        "reject_cause": entry[4],
        "psc": entry[5],
    }


def parse_operator_info(raw):
    if (not isinstance(raw, (list, tuple))) or len(raw) < 4:
        return None
    return {
        "long_name": raw[0],
        "short_name": raw[1],
        "mcc": raw[2],
        "mnc": raw[3],
    }


def parse_pdp_context(raw, ip_type):
    if (not isinstance(raw, (list, tuple))) or len(raw) < 5:
        return None
    return {
        "ip_type": ip_type,
        "state": raw[0],
        "reconnect": raw[1],
        "ip_address": raw[2],
        "dns_primary": raw[3],
        "dns_secondary": raw[4],
    }


def parse_data_context(raw):
    if (not isinstance(raw, (list, tuple))) or len(raw) < 3:
        return None
    ctx = {
        "profile_id": raw[0],
        "ip_type_code": raw[1],
        "contexts": [],
    }
    if raw[1] == 2 and len(raw) >= 4:
        ipv4 = parse_pdp_context(raw[2], "IP")
        ipv6 = parse_pdp_context(raw[3], "IPV6")
        if ipv4:
            ctx["contexts"].append(ipv4)
        if ipv6:
            ctx["contexts"].append(ipv6)
    else:
        ip_type = "IPV6" if raw[1] == 1 else "IP"
        parsed = parse_pdp_context(raw[2], ip_type)
        if parsed:
            ctx["contexts"].append(parsed)

    preferred = None
    for item in ctx["contexts"]:
        if item.get("state") == 1:
            preferred = item
            break
    if preferred is None and ctx["contexts"]:
        preferred = ctx["contexts"][0]

    if preferred:
        ctx["cid_preferred"] = ctx["profile_id"]
        ctx["ip_type"] = preferred.get("ip_type")
        ctx["ip_address"] = preferred.get("ip_address")
        ctx["cid"] = ctx["profile_id"]
        ctx["state"] = preferred.get("state")
        ctx["source"] = "dataCall.getInfo"
    return ctx


def _signal_quality(csq):
    if not isinstance(csq, int) or csq < 0:
        return "unknown"
    if csq >= 20:
        return "good"
    if csq >= 10:
        return "fair"
    return "weak"


def _normalize_segments(path):
    parts = []
    for part in (path or "").replace("\\", "/").split("/"):
        if (not part) or part == ".":
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return parts


def normalize_fs_path(path, cfg):
    text = path or getattr(cfg, "FS_DEFAULT_ROOT", "/usr")
    parts = _normalize_segments(text)
    normalized = "/" + "/".join(parts)
    if normalized == "/":
        normalized = "/"
    if (not getattr(cfg, "FS_ALLOW_ANY_PATH", False)) and not (normalized == "/usr" or normalized.startswith("/usr/")):
        raise Exception("path outside /usr is disabled: " + normalized)
    return normalized


def _path_parent(path):
    if path in ("", "/"):
        return "/"
    parts = _normalize_segments(path)
    if not parts:
        return "/"
    return "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"


def _path_basename(path):
    parts = _normalize_segments(path)
    if not parts:
        return "/"
    return parts[-1]


def _stat_is_dir(mode):
    try:
        return bool(int(mode) & 0x4000)
    except Exception:
        return False


def fs_stat(path):
    uos = safe_import("uos")
    if not uos:
        raise Exception("uos unavailable")
    try:
        info = uos.stat(path)
    except Exception:
        return None
    if not isinstance(info, (list, tuple)) or len(info) < 7:
        return None
    mode = info[0]
    size = info[6]
    return {
        "path": path,
        "name": _path_basename(path),
        "mode": mode,
        "size": size,
        "is_dir": _stat_is_dir(mode),
    }


def _listdir_sorted(path):
    uos = safe_import("uos")
    if not uos:
        raise Exception("uos unavailable")
    rows = []
    for item in uos.ilistdir(path):
        rows.append(item)
    rows.sort(key=lambda x: str(x[0]))
    return rows


def _entry_from_ilistdir(base_path, item):
    name = item[0]
    mode = item[1] if len(item) > 1 else 0
    size = item[3] if len(item) > 3 else None
    child_path = base_path.rstrip("/")
    if child_path:
        child_path += "/" + str(name)
    else:
        child_path = "/" + str(name)
    entry = {
        "name": name,
        "path": child_path,
        "is_dir": _stat_is_dir(mode),
        "mode": mode,
    }
    if ok_value(size) or size == 0:
        entry["size"] = size
    return entry


def _list_tree(path, depth, max_depth):
    stat = fs_stat(path)
    if stat is None:
        raise Exception("path not found: " + path)
    node = {
        "name": stat.get("name"),
        "path": path,
        "is_dir": stat.get("is_dir"),
        "size": stat.get("size"),
        "mode": stat.get("mode"),
    }
    if not stat.get("is_dir"):
        return node
    node["children"] = []
    rows = _listdir_sorted(path)
    for item in rows:
        child = _entry_from_ilistdir(path, item)
        if child.get("is_dir") and depth < max_depth:
            child = _list_tree(child["path"], depth + 1, max_depth)
        node["children"].append(child)
    return node


def fs_list(path, recursive, max_depth):
    depth_limit = int(max_depth or 0)
    if depth_limit < 0:
        depth_limit = 0
    if not recursive:
        depth_limit = 0
    return _list_tree(path, 0, depth_limit)


def _decode_file_data(data):
    if data is None:
        return None
    try:
        return data.decode("utf-8")
    except Exception:
        pass
    if ubinascii is not None:
        try:
            return "hex:" + ubinascii.hexlify(data).decode("ascii")
        except Exception:
            pass
    return str(data)


def fs_read_text(path, max_bytes):
    if max_bytes <= 0:
        raise Exception("max_bytes must be positive")
    info = fs_stat(path)
    if info is None:
        raise Exception("path not found: " + path)
    if info.get("is_dir"):
        raise Exception("cannot read directory: " + path)
    fp = None
    try:
        fp = open(path, "rb")
        data = fp.read(max_bytes + 1)
    finally:
        if fp is not None:
            try:
                fp.close()
            except Exception:
                pass
    truncated = False
    if data is None:
        data = b""
    if len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
    return {
        "path": path,
        "size": info.get("size"),
        "bytes_read": len(data),
        "truncated": truncated,
        "content": _decode_file_data(data),
    }


def fs_make_dirs(path):
    ql_fs = safe_import("ql_fs")
    if ql_fs and hasattr(ql_fs, "mkdirs"):
        ql_fs.mkdirs(path)
        return path

    uos = safe_import("uos")
    if not uos:
        raise Exception("uos unavailable")
    current = ""
    for part in _normalize_segments(path):
        current = current + "/" + part
        try:
            uos.mkdir(current)
        except Exception:
            pass
    return path


def fs_write_text(path, content, append, makedirs):
    parent = _path_parent(path)
    if makedirs and parent not in ("", "/"):
        fs_make_dirs(parent)
    mode = "a" if append else "w"
    fp = None
    try:
        fp = open(path, mode)
        fp.write(content)
    finally:
        if fp is not None:
            try:
                fp.close()
            except Exception:
                pass
    info = fs_stat(path)
    return info or {"path": path}


def fs_remove(path, recursive):
    uos = safe_import("uos")
    if not uos:
        raise Exception("uos unavailable")
    info = fs_stat(path)
    if info is None:
        raise Exception("path not found: " + path)
    if info.get("is_dir"):
        if recursive:
            rows = _listdir_sorted(path)
            for item in rows:
                child = _entry_from_ilistdir(path, item)
                fs_remove(child["path"], True)
        uos.rmdir(path)
        return {"path": path, "removed": "dir"}
    uos.remove(path)
    return {"path": path, "removed": "file"}


def gather_storage_info(root_path):
    uos = safe_import("uos")
    data = {
        "available": bool(uos),
        "root": root_path,
    }
    if not uos or not hasattr(uos, "statvfs"):
        return data
    try:
        st = uos.statvfs(root_path)
        if isinstance(st, (list, tuple)) and len(st) >= 4:
            block_size = st[0]
            total_blocks = st[2]
            free_blocks = st[3]
            total_bytes = int(block_size) * int(total_blocks)
            free_bytes = int(block_size) * int(free_blocks)
            data["block_size"] = block_size
            data["total_bytes"] = total_bytes
            data["free_bytes"] = free_bytes
            data["used_bytes"] = total_bytes - free_bytes
    except Exception as e:
        data["error"] = str(e)
    return data


def gather_modem_info(cfg, mask_sensitive):
    modem = safe_import("modem")
    info = {
        "device_id": cfg.DEVICE_ID,
        "device_name": getattr(cfg, "DEVICE_NAME", ""),
        "device_model_hint": getattr(cfg, "DEVICE_MODEL_HINT", ""),
        "board_profile": getattr(cfg, "BOARD_PROFILE", ""),
        "tenant_id": cfg.TENANT_ID,
        "access_mode": cfg.ACCESS_MODE,
        "fw_version_config": cfg.FW_VERSION,
        "ts": wall_time_ms(),
    }
    if modem:
        model = safe_call(getattr(modem, "getDevModel", None))
        imei = safe_call(getattr(modem, "getDevImei", None))
        fw_version = safe_call(getattr(modem, "getDevFwVersion", None))
        sn = safe_call(getattr(modem, "getDevSN", None))
        product_id = safe_call(getattr(modem, "getDevProductId", None))
        mac = safe_call(getattr(modem, "getDevMAC", None))
        if ok_value(model):
            info["module_model"] = model
        if ok_value(imei):
            info["imei"] = mask_value(imei, mask_sensitive)
        if ok_value(fw_version):
            info["firmware_version"] = fw_version
        if ok_value(sn):
            info["serial_number"] = mask_value(sn, mask_sensitive)
        if ok_value(product_id):
            info["product_id"] = product_id
        if ok_value(mac):
            info["mac_address"] = mask_value(mac, mask_sensitive)
    return info


def gather_sim_info(mask_sensitive):
    sim = safe_import("sim")
    data = {
        "available": bool(sim),
        "ready": False,
    }
    if not sim:
        return data

    status = safe_call(getattr(sim, "getStatus", None))
    data["status"] = status
    data["ready"] = status == 1
    data["inserted"] = status not in (None, 0, -1)

    iccid = safe_call(getattr(sim, "getIccid", None))
    imsi = safe_call(getattr(sim, "getImsi", None))
    phone_number = safe_call(getattr(sim, "getPhoneNumber", None))
    cur_simid = safe_call(getattr(sim, "getCurSimid", None)) if hasattr(sim, "getCurSimid") else None

    if ok_value(iccid):
        data["iccid"] = mask_value(iccid, mask_sensitive)
    if ok_value(imsi):
        data["imsi"] = mask_value(imsi, mask_sensitive)
    if ok_value(phone_number):
        data["phone_number"] = mask_value(phone_number, mask_sensitive)
    if ok_value(cur_simid) or cur_simid == 0:
        data["current_sim_id"] = cur_simid
    return data


def gather_network_info():
    net = safe_import("net")
    check_net = safe_import("checkNet")
    data = {
        "available": bool(net),
    }
    if not net:
        return data

    reg_raw, reg_source = safe_attr_call(net, ["getState"])
    voice = None
    data_reg = None
    if isinstance(reg_raw, (list, tuple)) and len(reg_raw) >= 2:
        voice = parse_reg_entry(reg_raw[0])
        data_reg = parse_reg_entry(reg_raw[1])
        data["registration_raw"] = reg_raw
        data["registration_source"] = reg_source

    operator_raw, operator_source = safe_attr_call(net, ["getOperatorName", "operatorName"])
    operator_info = parse_operator_info(operator_raw)
    serving_ci, _ = safe_attr_call(net, ["getServingCi"])
    serving_lac, _ = safe_attr_call(net, ["getServingLac"])
    serving_mcc, _ = safe_attr_call(net, ["getServingMcc"])
    serving_mnc, _ = safe_attr_call(net, ["getServingMnc"])
    csq, _ = safe_attr_call(net, ["csqQueryPoll"])
    signal_detail, signal_source = safe_attr_call(net, ["getSignal"], 1)
    nitz, nitz_source = safe_attr_call(net, ["nitzTime"])
    cells, cells_source = safe_attr_call(net, ["getCellInfo", "currentCellInfo"])

    if voice:
        data["voice_registration"] = voice
    if data_reg:
        data["data_registration"] = data_reg
        state = data_reg.get("state")
        data["registered"] = state in (1, 5, 8)
        data["registration"] = {
            "registered": data["registered"],
            "source": "net.getState",
            "stat": state,
        }
    if operator_info:
        operator_info["source"] = operator_source
        data["operator"] = operator_info

    signal = {}
    if ok_value(serving_ci):
        signal["serving_ci"] = serving_ci
    if ok_value(serving_lac):
        signal["serving_lac"] = serving_lac
    if ok_value(serving_mcc):
        signal["serving_mcc"] = serving_mcc
    if ok_value(serving_mnc):
        signal["serving_mnc"] = serving_mnc
    if ok_value(csq):
        signal["csq"] = csq
        signal["quality"] = _signal_quality(csq)
    if ok_value(signal_detail):
        signal["detail"] = signal_detail
        signal["detail_source"] = signal_source
    if signal:
        data["signal"] = signal

    if ok_value(nitz):
        data["nitz_time"] = {
            "raw": nitz,
            "source": nitz_source,
        }
    if ok_value(cells):
        data["cell_scan"] = {
            "raw": cells,
            "source": cells_source,
        }

    if check_net and hasattr(check_net, "waitNetworkReady"):
        ready = safe_call(check_net.waitNetworkReady, 1)
        if isinstance(ready, (list, tuple)) and len(ready) >= 2:
            data["network_ready"] = {
                "stage": ready[0],
                "state": ready[1],
            }
    return data


def gather_data_context():
    data_call = safe_import("dataCall")
    data = {
        "available": bool(data_call),
    }
    if not data_call:
        return data

    raw = safe_call(getattr(data_call, "getInfo", None), 1, 2)
    if raw in (None, -1):
        raw = safe_call(getattr(data_call, "getInfo", None), 1, 0)
    parsed = parse_data_context(raw)
    if parsed:
        data.update(parsed)
        data["raw"] = raw
    return data


def quick_network_status(cfg):
    network_info = gather_network_info()
    data_context = gather_data_context()
    sim_info = gather_sim_info(False)
    registration = network_info.get("registration") or {}
    registered = bool(registration.get("registered"))
    sim_ready = bool(sim_info.get("ready"))
    ip_address = data_context.get("ip_address")
    pdp_active = bool(
        data_context.get("available")
        and data_context.get("state") == 1
        and ok_value(ip_address)
        and str(ip_address) not in ("0.0.0.0", "::", "0:0:0:0:0:0:0:0")
    )
    stage = 3
    state = 1 if pdp_active else 0
    if not sim_ready:
        stage = 1
        state = sim_info.get("status")
        if state in (None, ""):
            state = 0
    elif not registered:
        stage = 2
        state = registration.get("stat")
        if state in (None, ""):
            state = 0
    return {
        "ready": bool(sim_ready and registered and pdp_active),
        "stage": stage,
        "state": state,
        "sim_ready": sim_ready,
        "registered": registered,
        "pdp_active": pdp_active,
        "ip_address": ip_address or "",
        "cid": data_context.get("cid"),
        "sim": sim_info,
        "registration": registration,
        "data_context": data_context,
        "target_gateway": getattr(cfg, "OPENCLAW_WS_URL", ""),
        "ts": wall_time_ms(),
    }


def wait_network_ready_status(cfg, timeout_sec):
    seconds = int(timeout_sec or 0)
    if seconds <= 0:
        seconds = 1
    check_net = safe_import("checkNet")
    if check_net and hasattr(check_net, "waitNetworkReady"):
        ready = safe_call(getattr(check_net, "waitNetworkReady"), seconds)
        if isinstance(ready, (list, tuple)) and len(ready) >= 2:
            try:
                return {
                    "stage": int(ready[0]),
                    "state": int(ready[1]),
                    "source": "checkNet.waitNetworkReady",
                    "ready": int(ready[0]) == 3 and int(ready[1]) == 1,
                }
            except Exception:
                return {
                    "stage": ready[0],
                    "state": ready[1],
                    "source": "checkNet.waitNetworkReady",
                    "ready": ready[0] == 3 and ready[1] == 1,
                }
    quick = quick_network_status(cfg)
    return {
        "stage": quick.get("stage"),
        "state": quick.get("state"),
        "source": "quick_network_status",
        "ready": bool(quick.get("ready")),
    }


class CellularNetworkManager(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self.runtime = None
        self.bootstrapped = False
        self.callback_registered = False
        self.last_ready = False
        self.last_stage = -1
        self.last_state = -1
        self.last_reason = ""
        self.last_check_ms = 0
        self.last_recover_ms = 0
        self.last_cfun_ms = 0
        self.last_event_ms = 0
        self.last_event_profile = -1
        self.last_event_state = -1
        self.last_recovery_action = ""
        self.last_recovery_result = ""
        self.last_ip_address = ""
        self.pending_transport_close_reason = ""

    def attach_runtime(self, runtime):
        self.runtime = runtime
        return True

    def snapshot(self):
        return {
            "bootstrapped": self.bootstrapped,
            "callback_registered": self.callback_registered,
            "last_ready": self.last_ready,
            "last_stage": self.last_stage,
            "last_state": self.last_state,
            "last_reason": self.last_reason,
            "last_check_ms": self.last_check_ms,
            "last_recover_ms": self.last_recover_ms,
            "last_cfun_ms": self.last_cfun_ms,
            "last_event_ms": self.last_event_ms,
            "last_event_profile": self.last_event_profile,
            "last_event_state": self.last_event_state,
            "last_recovery_action": self.last_recovery_action,
            "last_recovery_result": self.last_recovery_result,
            "last_ip_address": self.last_ip_address,
            "pending_transport_close_reason": self.pending_transport_close_reason,
        }

    def bootstrap(self):
        if self.bootstrapped:
            return True
        data_call = safe_import("dataCall")
        profile_id = int(getattr(self.cfg, "NETWORK_PROFILE_ID", 1))
        ip_type = int(getattr(self.cfg, "NETWORK_IPTYPE", 2))
        if data_call:
            apn = str(getattr(self.cfg, "NETWORK_APN", "") or "")
            username = str(getattr(self.cfg, "NETWORK_APN_USERNAME", "") or "")
            password = str(getattr(self.cfg, "NETWORK_APN_PASSWORD", "") or "")
            auth_type = int(getattr(self.cfg, "NETWORK_APN_AUTH_TYPE", 0))
            if apn and hasattr(data_call, "setPDPContext"):
                safe_call(
                    getattr(data_call, "setPDPContext"),
                    profile_id,
                    ip_type,
                    apn,
                    username,
                    password,
                    auth_type,
                )
            if bool(getattr(self.cfg, "NETWORK_ENFORCE_AUTO_ACTIVATE", True)) and hasattr(data_call, "setAutoActivate"):
                safe_call(getattr(data_call, "setAutoActivate"), profile_id, 1)
            if bool(getattr(self.cfg, "NETWORK_ENFORCE_AUTO_CONNECT", True)) and hasattr(data_call, "setAutoConnect"):
                safe_call(getattr(data_call, "setAutoConnect"), profile_id, 1)
            if hasattr(data_call, "setCallback"):
                safe_call(getattr(data_call, "setCallback"), self._on_data_call_event)
                self.callback_registered = True
        self.bootstrapped = True
        return True

    def poll(self):
        reason = self.pending_transport_close_reason
        if not reason:
            return False
        self.pending_transport_close_reason = ""
        runtime = self.runtime
        if runtime is None or runtime.transport is None:
            return False
        if not getattr(runtime.transport, "online", False):
            return False
        runtime.transport.close(reason)
        return True

    def ensure_ready(self, reason):
        self.bootstrap()
        if not bool(getattr(self.cfg, "NETWORK_AUTO_RECOVER", True)):
            self._remember_quick(quick_network_status(self.cfg), reason or "disabled")
            return True

        quick = quick_network_status(self.cfg)
        force_recover = self._should_force_recover(quick)
        if self._remember_quick(quick, reason or "quick") and (not force_recover):
            return True

        now = utime.ticks_ms()
        min_interval_ms = int(getattr(self.cfg, "NETWORK_RECOVER_RETRY_INTERVAL_SEC", 15) * 1000)
        if self.last_recover_ms and utime.ticks_diff(now, self.last_recover_ms) < min_interval_ms:
            return False
        self.last_recover_ms = now

        quick_wait = wait_network_ready_status(
            self.cfg, int(getattr(self.cfg, "NETWORK_READY_QUICK_TIMEOUT_SEC", 1))
        )
        if self._remember_stage(quick_wait, "checknet.quick") and (not force_recover):
            return True

        stage = quick_wait.get("stage")
        state = quick_wait.get("state")
        if stage == 3 and state != 1 and bool(getattr(self.cfg, "NETWORK_ACTIVATE_ON_STAGE3", True)):
            if self._activate_pdp():
                activate_wait = wait_network_ready_status(self.cfg, 3)
                if self._remember_stage(activate_wait, "pdp.activate"):
                    return True
                stage = activate_wait.get("stage")
                state = activate_wait.get("state")

        allow_cfun = False
        if force_recover:
            allow_cfun = True
        elif stage == 2 and bool(getattr(self.cfg, "NETWORK_CFUN_ON_STAGE2", True)):
            allow_cfun = True
        elif stage == 3 and bool(getattr(self.cfg, "NETWORK_CFUN_ON_STAGE3", True)):
            allow_cfun = True

        if allow_cfun and self._cfun_recover():
            return True

        return self._remember_quick(quick_network_status(self.cfg), "quick.final")

    def _on_data_call_event(self, args):
        self.last_event_ms = utime.ticks_ms()
        try:
            self.last_event_profile = int(args[0])
        except Exception:
            self.last_event_profile = -1
        try:
            self.last_event_state = int(args[1])
        except Exception:
            self.last_event_state = -1

        if self.last_event_state == 1:
            self.last_ready = True
            self.last_stage = 3
            self.last_state = 1
            self.last_reason = "pdp.connected"
            self.pending_transport_close_reason = ""
            return

        if self.last_event_state == 0:
            self.last_ready = False
            self.last_stage = 3
            self.last_state = 0
            self.last_reason = "pdp.disconnected"
            self.state.note_error("NETWORK_LINK_DOWN", "dataCall callback: disconnected")
            if bool(getattr(self.cfg, "NETWORK_CLOSE_TRANSPORT_ON_PDP_DOWN", True)):
                self.pending_transport_close_reason = "network-disconnected"

    def _should_force_recover(self, quick):
        threshold = int(getattr(self.cfg, "NETWORK_FORCE_RECOVER_AFTER_CONNECT_FAILURES", 0))
        if threshold <= 0:
            return False
        if not bool(quick.get("ready")):
            return False
        return int(getattr(self.state, "consecutive_failures", 0)) >= threshold

    def _remember_quick(self, quick, reason):
        self.last_check_ms = utime.ticks_ms()
        self.last_ready = bool(quick.get("ready"))
        self.last_stage = quick.get("stage")
        self.last_state = quick.get("state")
        self.last_reason = str(reason or "")
        self.last_ip_address = str(quick.get("ip_address") or "")
        return self.last_ready

    def _remember_stage(self, status, reason):
        self.last_check_ms = utime.ticks_ms()
        self.last_stage = status.get("stage")
        self.last_state = status.get("state")
        self.last_reason = str(reason or "")
        self.last_ready = bool(status.get("ready"))
        return self.last_ready

    def _activate_pdp(self):
        data_call = safe_import("dataCall")
        if not data_call:
            self.last_recovery_action = "pdp.activate"
            self.last_recovery_result = "dataCall unavailable"
            return False

        profile_id = int(getattr(self.cfg, "NETWORK_PROFILE_ID", 1))
        ip_type = int(getattr(self.cfg, "NETWORK_IPTYPE", 2))
        apn = str(getattr(self.cfg, "NETWORK_APN", "") or "")
        username = str(getattr(self.cfg, "NETWORK_APN_USERNAME", "") or "")
        password = str(getattr(self.cfg, "NETWORK_APN_PASSWORD", "") or "")
        auth_type = int(getattr(self.cfg, "NETWORK_APN_AUTH_TYPE", 0))
        result = None
        if apn and hasattr(data_call, "setPDPContext"):
            safe_call(
                getattr(data_call, "setPDPContext"),
                profile_id,
                ip_type,
                apn,
                username,
                password,
                auth_type,
            )
        if hasattr(data_call, "activate"):
            result = safe_call(getattr(data_call, "activate"), profile_id)
        if result not in (0, True, None) and hasattr(data_call, "start"):
            result = safe_call(
                getattr(data_call, "start"),
                profile_id,
                ip_type,
                apn,
                username,
                password,
                auth_type,
            )
        self.last_recovery_action = "pdp.activate"
        self.last_recovery_result = str(result)
        return result in (0, True, None)

    def _cfun_recover(self):
        net = safe_import("net")
        if not net or (not hasattr(net, "setModemFun")):
            self.last_recovery_action = "cfun"
            self.last_recovery_result = "net.setModemFun unavailable"
            return False

        now = utime.ticks_ms()
        cooldown_ms = int(getattr(self.cfg, "NETWORK_CFUN_COOLDOWN_SEC", 90) * 1000)
        if self.last_cfun_ms and utime.ticks_diff(now, self.last_cfun_ms) < cooldown_ms:
            self.last_recovery_action = "cfun"
            self.last_recovery_result = "cooldown"
            return False

        off_result = safe_call(getattr(net, "setModemFun"), 0, 0)
        _sleep_ms(int(getattr(self.cfg, "NETWORK_CFUN_OFF_MS", 1200)))
        on_result = safe_call(getattr(net, "setModemFun"), 1, 0)
        self.last_cfun_ms = utime.ticks_ms()
        self.last_recovery_action = "cfun"
        self.last_recovery_result = str((off_result, on_result))
        wait_status = wait_network_ready_status(
            self.cfg, int(getattr(self.cfg, "NETWORK_POST_CFUN_WAIT_SEC", 15))
        )
        return self._remember_stage(wait_status, "cfun.wait")


def _fill_cell_serving_from_signal(data, signal):
    if not isinstance(signal, dict):
        return
    for source_key, target_key in (
        ("serving_ci", "ci"),
        ("serving_lac", "lac"),
        ("serving_mcc", "mcc"),
        ("serving_mnc", "mnc"),
    ):
        value = signal.get(source_key)
        if ok_value(value):
            data["serving"][target_key] = value


def _fill_cell_serving_from_raw(data):
    raw = data.get("raw")
    if not (isinstance(raw, (list, tuple)) and len(raw) >= 3):
        return
    rows = raw[2]
    if not (isinstance(rows, (list, tuple)) and rows):
        return
    row = rows[0]
    if not isinstance(row, (list, tuple)):
        return
    mapping = (
        (1, "ci"),
        (2, "mcc"),
        (3, "mnc"),
        (5, "lac"),
    )
    for index, key in mapping:
        if len(row) > index and ok_value(row[index]):
            data["serving"][key] = row[index]


def _fill_cell_neighbors_from_raw(data):
    raw = data.get("raw")
    if not (isinstance(raw, (list, tuple)) and len(raw) >= 3):
        return
    rows = raw[2]
    if not isinstance(rows, (list, tuple)):
        return
    collected = {
        "ci": [],
        "mcc": [],
        "mnc": [],
        "lac": [],
    }
    mapping = (
        (1, "ci"),
        (2, "mcc"),
        (3, "mnc"),
        (5, "lac"),
    )
    for row in rows:
        if not isinstance(row, (list, tuple)):
            continue
        for index, key in mapping:
            if len(row) > index and ok_value(row[index]):
                collected[key].append(row[index])
    for key in ("ci", "mcc", "mnc", "lac"):
        if collected[key] and key not in data["neighbors"]:
            data["neighbors"][key] = collected[key]


def gather_cell_info(network_info=None):
    net = safe_import("net")
    if not net and not isinstance(network_info, dict):
        return {"available": False}

    data = {
        "available": True,
        "serving": {},
        "neighbors": {},
    }

    if isinstance(network_info, dict):
        _fill_cell_serving_from_signal(data, network_info.get("signal"))
        cell_scan = network_info.get("cell_scan")
        if isinstance(cell_scan, dict):
            raw = cell_scan.get("raw")
            if ok_value(raw):
                data["raw"] = raw
                data["raw_source"] = cell_scan.get("source") or "reused.cell_scan"
                _fill_cell_serving_from_raw(data)
                _fill_cell_neighbors_from_raw(data)

    if net:
        if not data["serving"]:
            for method_name, key in (
                ("getServingCi", "ci"),
                ("getServingLac", "lac"),
                ("getServingMcc", "mcc"),
                ("getServingMnc", "mnc"),
            ):
                if hasattr(net, method_name):
                    value = safe_call(getattr(net, method_name))
                    if ok_value(value):
                        data["serving"][key] = value

        if "raw" not in data:
            cells, source = safe_attr_call(net, ["getCellInfo", "currentCellInfo"])
            if ok_value(cells):
                data["raw"] = cells
                data["raw_source"] = source
                _fill_cell_serving_from_raw(data)
                _fill_cell_neighbors_from_raw(data)
    return data


def gather_runtime_info(cfg, state):
    runtime = state.snapshot()
    runtime["gateway"] = {
        "url": getattr(cfg, "OPENCLAW_WS_URL", ""),
        "role": getattr(cfg, "OPENCLAW_ROLE", "node"),
        "device_auth_mode": getattr(cfg, "OPENCLAW_DEVICE_AUTH_MODE", "none"),
        "heartbeat_interval_sec": getattr(cfg, "HEARTBEAT_INTERVAL_SEC", 15),
        "telemetry_interval_sec": getattr(cfg, "TELEMETRY_INTERVAL_SEC", 60),
    }
    runtime["board_profile"] = getattr(cfg, "BOARD_PROFILE", "")
    runtime["runtime_version"] = getattr(cfg, "RUNTIME_VERSION", "")
    runtime["config_local"] = {
        "loaded": bool(getattr(cfg, "CONFIG_LOCAL_LOADED", False)),
        "source": str(getattr(cfg, "CONFIG_LOCAL_SOURCE", "") or ""),
        "error": str(getattr(cfg, "CONFIG_LOCAL_ERROR", "") or ""),
    }
    runtime["voice"] = {
        "enabled": bool(getattr(cfg, "VOICE_ENABLED", False)),
        "main_session_key": _string(getattr(cfg, "VOICE_MAIN_SESSION_KEY", "main")).strip() or "main",
        "operator_ws_url": _string(getattr(cfg, "VOICE_OPERATOR_WS_URL", "")).strip() or _string(getattr(cfg, "OPENCLAW_WS_URL", "")).strip(),
        "operator_device_auth_mode": _string(getattr(cfg, "VOICE_OPERATOR_DEVICE_AUTH_MODE", "")).strip() or _string(getattr(cfg, "OPENCLAW_DEVICE_AUTH_MODE", "none")).strip() or "none",
        "operator_role": _string(getattr(cfg, "VOICE_OPERATOR_ROLE", "operator")).strip() or "operator",
        "operator_scopes": _normalize_scopes(getattr(cfg, "VOICE_OPERATOR_SCOPES", [])),
        "chat_subscribe": bool(getattr(cfg, "VOICE_CHAT_SUBSCRIBE", True)),
    }
    runtime["command_count"] = len(getattr(cfg, "OPENCLAW_COMMANDS", []))
    return runtime


def build_runtime_telemetry(cfg, state):
    runtime = gather_runtime_info(cfg, state)
    return {
        "device_id": cfg.DEVICE_ID,
        "node_id": state.node_id,
        "runtime": runtime,
        "ts": wall_time_ms(),
    }


def build_recommendations(sim_info, network_info, data_context):
    tips = []
    status = sim_info.get("status")
    if status not in (None, 1):
        tips.append("SIM is not ready. Check card state, PIN, and contact quality.")
    registration = network_info.get("registration") or {}
    if registration and not registration.get("registered"):
        tips.append("Module is not registered on the cellular network yet.")
    if data_context.get("available") and data_context.get("state") != 1:
        tips.append("PDP context is not active. Check APN and activate data.")
    if not tips:
        tips.append("No obvious cellular fault was detected from the current probes.")
    return tips


def build_device_status(cfg, state, mask_sensitive):
    timings = {}
    started = utime.ticks_ms()
    modem_info = measure_step("gather_modem_info", timings, gather_modem_info, cfg, mask_sensitive)
    sim_info = measure_step("gather_sim_info", timings, gather_sim_info, mask_sensitive)
    network_info = measure_step("gather_network_info", timings, gather_network_info)
    data_context = measure_step("gather_data_context", timings, gather_data_context)
    runtime = measure_step("gather_runtime_info", timings, gather_runtime_info, cfg, state)
    cell = measure_step("gather_cell_info", timings, gather_cell_info, network_info)
    storage = measure_step("gather_storage_info", timings, gather_storage_info, getattr(cfg, "FS_DEFAULT_ROOT", "/usr"))
    recommendations = measure_step(
        "build_recommendations",
        timings,
        build_recommendations,
        sim_info,
        network_info,
        data_context,
    )
    total_ms = utime.ticks_diff(utime.ticks_ms(), started)
    return {
        "device_id": cfg.DEVICE_ID,
        "node_id": state.node_id,
        "module_model": modem_info.get("module_model"),
        "firmware_version": modem_info.get("firmware_version") or modem_info.get("fw_version_config"),
        "imei": modem_info.get("imei"),
        "sim_inserted": sim_info.get("inserted"),
        "sim_ready": sim_info.get("ready"),
        "registration": network_info.get("registration"),
        "data_context": data_context,
        "signal": network_info.get("signal"),
        "operator": network_info.get("operator"),
        "storage": storage,
        "runtime": runtime,
        "modem": modem_info,
        "sim": sim_info,
        "network": network_info,
        "cell": cell,
        "recommendations": recommendations,
        "probe_timings_ms": timings,
        "probe_duration_ms": total_ms,
        "ts": wall_time_ms(),
    }


def build_tool_catalog(entries):
    out = []
    for entry in entries:
        out.append({
            "tool": entry.get("name"),
            "aliases": entry.get("aliases") or [],
            "category": entry.get("category") or "misc",
            "summary": entry.get("summary") or "",
            "read_only": bool(entry.get("read_only", True)),
            "source": "core",
        })
    return out

class ToolDeviceInfo(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        mask_sensitive = bool(args.get("mask_sensitive", getattr(self.cfg, "SENSITIVE_MASK", True))) if args else bool(getattr(self.cfg, "SENSITIVE_MASK", True))
        data = gather_modem_info(self.cfg, mask_sensitive)
        data["sim"] = gather_sim_info(mask_sensitive)
        data["storage"] = gather_storage_info(getattr(self.cfg, "FS_DEFAULT_ROOT", "/usr"))
        data["node_id"] = self.state.node_id
        return data


class ToolDeviceStatus(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        mask_sensitive = bool(args.get("mask_sensitive", getattr(self.cfg, "SENSITIVE_MASK", True))) if args else bool(getattr(self.cfg, "SENSITIVE_MASK", True))
        return build_device_status(self.cfg, self.state, mask_sensitive)


class ToolDeviceReboot(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        mode = "soft"
        delay_ms = int(getattr(self.cfg, "REBOOT_RESULT_DELAY_MS", 1500))
        if args:
            mode = str(args.get("mode", mode) or mode)
            if "delay_ms" in args:
                delay_ms = int(args.get("delay_ms"))
        self.state.request_reboot(mode, delay_ms)
        return {
            "node_id": self.state.node_id,
            "scheduled": True,
            "mode": mode,
            "delay_ms": delay_ms,
        }

class ToolFsList(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        path = normalize_fs_path(args.get("path"), self.cfg)
        recursive = bool(args.get("recursive", False))
        max_depth = int(args.get("max_depth", getattr(self.cfg, "FS_LIST_MAX_DEPTH", 4)))
        return {
            "node_id": self.state.node_id,
            "path": path,
            "tree": fs_list(path, recursive, max_depth),
            "ts": wall_time_ms(),
        }


class ToolFsRead(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        path = normalize_fs_path(args.get("path"), self.cfg)
        max_bytes = int(args.get("max_bytes", getattr(self.cfg, "FS_READ_MAX_BYTES", 4096)))
        result = fs_read_text(path, max_bytes)
        result["node_id"] = self.state.node_id
        result["ts"] = wall_time_ms()
        return result


class ToolFsWrite(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        path = normalize_fs_path(args.get("path"), self.cfg)
        content = args.get("content", "")
        if content is None:
            content = ""
        content = str(content)
        max_bytes = int(getattr(self.cfg, "FS_WRITE_MAX_BYTES", 8192))
        if len(content) > max_bytes:
            raise Exception("content too large for single write")
        append = bool(args.get("append", False))
        makedirs = bool(args.get("makedirs", True))
        info = fs_write_text(path, content, append, makedirs)
        return {
            "node_id": self.state.node_id,
            "path": path,
            "append": append,
            "file": info,
            "ts": wall_time_ms(),
        }


class ToolFsMkdir(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        path = normalize_fs_path(args.get("path"), self.cfg)
        fs_make_dirs(path)
        return {
            "node_id": self.state.node_id,
            "path": path,
            "created": True,
            "ts": wall_time_ms(),
        }


class ToolFsRemove(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        path = normalize_fs_path(args.get("path"), self.cfg)
        recursive = bool(args.get("recursive", False))
        removed = fs_remove(path, recursive)
        removed["node_id"] = self.state.node_id
        removed["recursive"] = recursive
        removed["ts"] = wall_time_ms()
        return removed

class ToolNetDiag(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        mask_sensitive = bool(args.get("mask_sensitive", getattr(self.cfg, "SENSITIVE_MASK", True))) if args else bool(getattr(self.cfg, "SENSITIVE_MASK", True))
        sim_info = gather_sim_info(mask_sensitive)
        network_info = gather_network_info()
        data_context = gather_data_context()
        cell = gather_cell_info(network_info)
        return {
            "target_gateway": self.cfg.OPENCLAW_WS_URL,
            "registered": bool((network_info.get("registration") or {}).get("registered")),
            "network": network_info,
            "data_context": data_context,
            "cell": cell,
            "sim": sim_info,
            "runtime": gather_runtime_info(self.cfg, self.state),
            "recommendations": build_recommendations(sim_info, network_info, data_context),
            "ts": wall_time_ms(),
        }


class ToolNetIfconfig(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        _ = args
        network = gather_network_info()
        data_context = gather_data_context()
        return {
            "node_id": self.state.node_id,
            "registered": bool((network.get("registration") or {}).get("registered")),
            "ip_address": data_context.get("ip_address"),
            "ip_type": data_context.get("ip_type"),
            "cid": data_context.get("cid"),
            "data_context": data_context,
            "signal": network.get("signal"),
            "operator": network.get("operator"),
            "ts": wall_time_ms(),
        }


class ToolSimInfo(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        mask_sensitive = bool(args.get("mask_sensitive", getattr(self.cfg, "SENSITIVE_MASK", True))) if args else bool(getattr(self.cfg, "SENSITIVE_MASK", True))
        return {
            "node_id": self.state.node_id,
            "sim": gather_sim_info(mask_sensitive),
            "ts": wall_time_ms(),
        }


class ToolCellInfo(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        _ = args
        network = gather_network_info()
        return {
            "node_id": self.state.node_id,
            "cell": gather_cell_info(network),
            "operator": network.get("operator"),
            "signal": network.get("signal"),
            "ts": wall_time_ms(),
        }

def _stringify(value):
    if value is None:
        return ""
    return str(value)


def _resolve_builtins():
    try:
        import builtins as _builtins

        return _builtins
    except Exception:
        pass

    try:
        import __builtin__ as _builtins

        return _builtins
    except Exception:
        pass

    try:
        return __builtins__
    except Exception:
        return {}


class ToolRuntimeStatus(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        _ = args
        runtime = gather_runtime_info(self.cfg, self.state)
        runtime["ts"] = wall_time_ms()
        return runtime


class ToolToolsCatalog(object):

    def __init__(self, cfg, state, catalog_provider):
        self.cfg = cfg
        self.state = state
        self.catalog_provider = catalog_provider

    def execute(self, args):
        _ = args
        catalog = build_tool_catalog(self.catalog_provider())
        return {
            "node_id": self.state.node_id,
            "tool_count": len(catalog),
            "tools": catalog,
            "ts": wall_time_ms(),
        }


class ToolReplRun(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        expression = args.get("expression")
        code = args.get("code")
        mode = _stringify(args.get("mode") or "").strip().lower()
        namespace = {
            "cfg": self.cfg,
            "state": self.state,
            "__builtins__": _resolve_builtins(),
        }

        if expression not in (None, ""):
            result = eval(_stringify(expression), namespace, namespace)
            return {
                "node_id": self.state.node_id,
                "mode": "eval",
                "result_repr": repr(result),
                "result_type": _stringify(type(result)),
                "ts": wall_time_ms(),
            }

        if code in (None, ""):
            raise Exception("code or expression required")

        exec(_stringify(code), namespace, namespace)
        result_name = _stringify(args.get("result_var") or "result").strip()
        result = namespace.get(result_name)
        return {
            "node_id": self.state.node_id,
            "mode": mode or "exec",
            "result_var": result_name,
            "result_repr": repr(result),
            "result_type": _stringify(type(result)) if result is not None else "",
            "globals": sorted([name for name in namespace.keys() if name[:1] != "_"]),
            "ts": wall_time_ms(),
        }


class ToolVoiceStatus(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        _ = args
        runtime = get_runtime()
        if runtime is None or not hasattr(runtime, "voice") or runtime.voice is None:
            return {
                "node_id": self.state.node_id,
                "enabled": bool(getattr(self.cfg, "VOICE_ENABLED", False)),
                "available": False,
                "ts": wall_time_ms(),
            }
        data = runtime.voice.snapshot()
        data["node_id"] = self.state.node_id
        data["ts"] = wall_time_ms()
        return data


class ToolVoiceChat(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        runtime = get_runtime()
        if runtime is None or not hasattr(runtime, "voice") or runtime.voice is None:
            raise Exception("voice runtime unavailable")
        message = _stringify(args.get("message") or args.get("text") or "").strip()
        if not message:
            raise Exception("message required")
        session_key = _stringify(args.get("session_key") or args.get("sessionKey") or "").strip()
        idempotency_key = _stringify(args.get("idempotency_key") or args.get("idempotencyKey") or "").strip()
        timeout_ms = args.get("timeout_ms")
        if timeout_ms in (None, ""):
            timeout_ms = args.get("timeoutMs")
        subscribe = args.get("subscribe")
        history_limit = args.get("history_limit")
        if history_limit in (None, ""):
            history_limit = args.get("historyLimit")
        data = runtime.voice.chat(
            message,
            session_key=session_key,
            timeout_ms=timeout_ms,
            idempotency_key=idempotency_key,
            subscribe=subscribe,
            history_limit=history_limit,
        )
        data["node_id"] = self.state.node_id
        return data


class ToolVoiceAbort(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state

    def execute(self, args):
        args = args or {}
        runtime = get_runtime()
        if runtime is None or not hasattr(runtime, "voice") or runtime.voice is None:
            raise Exception("voice runtime unavailable")
        session_key = _stringify(args.get("session_key") or args.get("sessionKey") or "").strip()
        data = runtime.voice.abort(session_key=session_key)
        data["node_id"] = self.state.node_id
        data["ts"] = wall_time_ms()
        return data

import utime

import ujson as _json

try:
    import request
except Exception:
    request = None


def dumps(value):
    return _json.dumps(value)


def loads(value):
    return _json.loads(value)


def _string(value):
    if value is None:
        return ""
    return str(value)


def _normalize_scopes(value):
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            text = str(item)
            if text:
                out.append(text)
        return out
    return []


def _epoch_ms_fallback():
    try:
        return int(utime.time() * 1000)
    except Exception:
        return 0


def _auth_block(cfg, state):
    explicit_token = _string(getattr(cfg, "OPENCLAW_AUTH_TOKEN", "")).strip()
    cached_device_token = _string(getattr(state, "device_token", "")).strip()
    auth = {}
    if explicit_token:
        auth["token"] = explicit_token
        if cached_device_token:
            auth["deviceToken"] = cached_device_token
    elif cached_device_token:
        auth["token"] = cached_device_token
        auth["deviceToken"] = cached_device_token
    if auth:
        return auth, explicit_token or cached_device_token
    return None, ""


def _remote_signer_headers(cfg):
    headers = {
        "Content-Type": "application/json",
    }
    token = _string(getattr(cfg, "REMOTE_SIGNER_HTTP_AUTH_TOKEN", "")).strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    extra = getattr(cfg, "REMOTE_SIGNER_HTTP_HEADERS", None)
    if isinstance(extra, dict):
        for key in extra:
            headers[str(key)] = str(extra[key])
    return headers


def _response_json(resp):
    json_fn = getattr(resp, "json", None)
    if json_fn:
        try:
            data = json_fn()
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    text = getattr(resp, "text", "")
    if isinstance(text, (list, tuple)):
        text = "".join([str(item) for item in text])
    elif not isinstance(text, str):
        try:
            chunks = []
            for item in text:
                chunks.append(str(item))
            text = "".join(chunks)
        except Exception:
            text = str(text)
    return loads(text)


def _remote_signer_request_payload(
    cfg,
    state,
    auth_token,
    nonce,
    client_id=None,
    client_mode=None,
    role=None,
    scopes=None,
    logical_device_id=None,
    device_name=None,
):
    client_id_text = _string(client_id).strip()
    if not client_id_text:
        client_id_text = _string(getattr(cfg, "OPENCLAW_CLIENT_ID", "qpyclaw-node")).strip()
    client_mode_text = _string(client_mode).strip()
    if not client_mode_text:
        client_mode_text = _string(getattr(cfg, "OPENCLAW_CLIENT_MODE", "node")).strip()
    role_text = _string(role).strip()
    if not role_text:
        role_text = _string(getattr(cfg, "OPENCLAW_ROLE", "node")).strip()
    logical_id_text = _string(logical_device_id).strip()
    if not logical_id_text:
        logical_id_text = _string(getattr(cfg, "DEVICE_ID", "")).strip()
    device_name_text = _string(device_name).strip()
    if not device_name_text:
        device_name_text = _string(getattr(cfg, "DEVICE_NAME", "")).strip()
    normalized_scopes = _normalize_scopes(scopes)
    if not normalized_scopes:
        normalized_scopes = _normalize_scopes(getattr(cfg, "OPENCLAW_SCOPES", []))
    return {
        "logicalDeviceId": logical_id_text,
        "deviceName": device_name_text,
        "clientId": client_id_text,
        "clientMode": client_mode_text,
        "role": role_text,
        "scopes": normalized_scopes,
        "token": auth_token,
        "nonce": nonce,
        "platform": _string(getattr(cfg, "OPENCLAW_CLIENT_PLATFORM", "quectel")).strip(),
        "deviceFamily": _string(getattr(cfg, "OPENCLAW_CLIENT_DEVICE_FAMILY", "quecpython")).strip(),
        "requestedAtMs": _epoch_ms_fallback(),
    }


def _request_remote_signature(
    cfg,
    state,
    auth_token,
    nonce,
    client_id=None,
    client_mode=None,
    role=None,
    scopes=None,
    logical_device_id=None,
    device_name=None,
):
    if request is None:
        raise Exception("request module unavailable")

    url = _string(getattr(cfg, "REMOTE_SIGNER_HTTP_URL", "")).strip()
    if not url:
        raise Exception("remote signer url missing")

    payload = _remote_signer_request_payload(
        cfg,
        state,
        auth_token,
        nonce,
        client_id=client_id,
        client_mode=client_mode,
        role=role,
        scopes=scopes,
        logical_device_id=logical_device_id,
        device_name=device_name,
    )
    resp = None
    try:
        body_text = dumps(payload)
        headers = _remote_signer_headers(cfg)
        try:
            resp = request.post(url, data=body_text, headers=headers)
        except TypeError as e:
            if "buffer protocol" not in str(e):
                raise
            resp = request.post(url, data=body_text.encode("utf-8"), headers=headers)
        status_code = getattr(resp, "status_code", 0)
        if status_code != 200:
            raise Exception("remote signer http " + str(status_code))
        body = _response_json(resp)
        device = body.get("device") if isinstance(body, dict) else None
        if not isinstance(device, dict):
            raise Exception("remote signer invalid payload")
        if not device.get("nonce"):
            device["nonce"] = nonce
        state.last_signer = {
            "url": url,
            "signed_at": device.get("signedAt"),
            "logical_device_id": payload["logicalDeviceId"],
        }
        return device
    finally:
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass


def resolve_connect_security(cfg, state, nonce):
    auth, auth_token = _auth_block(cfg, state)
    device = None
    device_auth_mode = _string(getattr(cfg, "OPENCLAW_DEVICE_AUTH_MODE", "none")).strip() or "none"
    if device_auth_mode == "remote_signer_http":
        device = _request_remote_signature(cfg, state, auth_token, nonce)
    elif device_auth_mode != "none":
        raise Exception("unsupported device auth mode: " + device_auth_mode)
    return auth, device, device_auth_mode

import ubinascii
import uhashlib
import uos
import usocket
import ustruct

try:
    import ussl
except Exception:
    ussl = None


GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_TEXT = 0x1
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA


class WsError(Exception):
    pass


class WsClosed(WsError):
    pass


class WsTimeout(WsError):
    pass


class WsClient(object):

    def __init__(self):
        self.sock = None
        self.url = ""
        self.host = ""
        self.port = 0
        self.path = "/"
        self.secure = False
        self.open = False

    def _parse_url(self, url):
        raw = (url or "").strip()
        secure = False
        if raw.startswith("ws://"):
            raw = raw[5:]
        elif raw.startswith("wss://"):
            raw = raw[6:]
            secure = True
        else:
            raise ValueError("unsupported websocket scheme")

        slash = raw.find("/")
        if slash >= 0:
            host_part = raw[:slash]
            path = raw[slash:] or "/"
        else:
            host_part = raw
            path = "/"

        if ":" in host_part:
            host, port_text = host_part.split(":", 1)
            port = int(port_text)
        else:
            host = host_part
            port = 443 if secure else 80

        return secure, host, port, path

    def connect(self, url, timeout_sec, headers=None, server_hostname=None):
        self.secure, self.host, self.port, self.path = self._parse_url(url)
        self.url = url

        if headers is None:
            headers = {}

        sock = usocket.socket()
        sock.settimeout(timeout_sec)
        try:
            addr = usocket.getaddrinfo(self.host, self.port)[0][-1]
            sock.connect(addr)
            if self.secure:
                if ussl is None:
                    raise WsError("ussl unavailable")
                tls_host = server_hostname or self.host
                sock = ussl.wrap_socket(sock, server_hostname=tls_host)
                sock.settimeout(timeout_sec)

            sec_key = self._random_key()
            request_lines = [
                "GET " + self.path + " HTTP/1.1",
                "Host: " + self.host + ":" + str(self.port),
                "Connection: Upgrade",
                "Upgrade: websocket",
                "Sec-WebSocket-Key: " + sec_key,
                "Sec-WebSocket-Version: 13",
            ]
            for key in headers:
                request_lines.append(str(key) + ": " + str(headers[key]))
            request_lines.append("")
            request_lines.append("")
            request_bytes = "\r\n".join(request_lines).encode("utf-8")
            if hasattr(sock, "write"):
                sock.write(request_bytes)
            else:
                self._write_all(sock, request_bytes)

            status_line = self._read_line(sock)
            if (not status_line) or (not status_line.startswith("HTTP/1.1 101 ")):
                raise WsError("handshake failed: " + str(status_line or "no status"))

            response_headers = {}
            while True:
                line = self._read_line(sock)
                if line is None:
                    raise WsError("handshake header timeout")
                if line == "":
                    break
                pos = line.find(":")
                if pos > 0:
                    key = line[:pos].strip().lower()
                    value = line[pos + 1:].strip()
                    response_headers[key] = value

            expected_accept = self._expected_accept(sec_key)
            actual_accept = response_headers.get("sec-websocket-accept", "")
            if expected_accept and actual_accept and expected_accept != actual_accept:
                raise WsError("invalid websocket accept")

            self.sock = sock
            self.open = True
        except Exception:
            try:
                sock.close()
            except Exception:
                pass
            raise

    def settimeout_ms(self, timeout_ms):
        if self.sock:
            if timeout_ms is None:
                self.sock.settimeout(None)
            else:
                seconds = float(timeout_ms) / 1000.0
                if seconds <= 0:
                    seconds = 0.001
                self.sock.settimeout(seconds)

    def send_text(self, text):
        if not self.open or self.sock is None:
            raise WsClosed("websocket closed")
        if isinstance(text, bytes):
            payload = text
        else:
            payload = str(text).encode("utf-8")
        self._write_frame(OP_TEXT, payload)

    def recv_text(self, timeout_ms):
        if not self.open or self.sock is None:
            raise WsClosed("websocket closed")
        self.settimeout_ms(timeout_ms)

        while self.open:
            fin, opcode, payload = self._read_frame()
            if not fin:
                raise WsError("fragmented frame unsupported")
            if opcode == OP_TEXT:
                return payload.decode("utf-8")
            if opcode == OP_CLOSE:
                self._close_internal()
                raise WsClosed("server closed websocket")
            if opcode == OP_PING:
                self._write_frame(OP_PONG, payload)
                continue
            if opcode == OP_PONG:
                continue
            raise WsError("unsupported opcode")

        raise WsClosed("websocket closed")

    def close(self):
        if not self.open:
            return
        try:
            self._write_frame(OP_CLOSE, ustruct.pack("!H", 1000))
        except Exception:
            pass
        self._close_internal()

    def _close_internal(self):
        self.open = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None

    def _random_key(self):
        return self._b64(uos.urandom(16))

    def _expected_accept(self, sec_key):
        digest = self._sha1_bytes((sec_key + GUID).encode("utf-8"))
        return self._b64(digest)

    def _sha1_bytes(self, data):
        ctor = getattr(uhashlib, "SHA1", None)
        if ctor:
            return ctor(data).digest()

        ctor = getattr(uhashlib, "sha1", None)
        if ctor:
            try:
                return ctor(data).digest()
            except TypeError:
                hasher = ctor()
                hasher.update(data)
                return hasher.digest()

        new_fn = getattr(uhashlib, "new", None)
        if new_fn:
            hasher = new_fn("sha1")
            hasher.update(data)
            return hasher.digest()

        raise WsError("sha1 unavailable")

    def _b64(self, raw):
        return ubinascii.b2a_base64(raw).decode("utf-8").strip()

    def _read_line(self, sock):
        data = bytearray()
        while True:
            chunk = self._read_exact(sock, 1)
            if chunk is None:
                return None
            if chunk == b"\n":
                break
            if chunk != b"\r":
                data.extend(chunk)
        return bytes(data).decode("utf-8")

    def _read_frame(self):
        header = self._read_exact(self.sock, 2)
        if header is None:
            raise WsClosed("socket closed")
        byte1, byte2 = ustruct.unpack("!BB", header)
        fin = bool(byte1 & 0x80)
        opcode = byte1 & 0x0F
        masked = bool(byte2 & 0x80)
        length = byte2 & 0x7F

        if length == 126:
            raw_length = self._read_exact(self.sock, 2)
            if raw_length is None:
                raise WsClosed("socket closed")
            length = ustruct.unpack("!H", raw_length)[0]
        elif length == 127:
            raw_length = self._read_exact(self.sock, 8)
            if raw_length is None:
                raise WsClosed("socket closed")
            length = ustruct.unpack("!Q", raw_length)[0]

        mask_key = None
        if masked:
            mask_key = self._read_exact(self.sock, 4)
            if mask_key is None:
                raise WsClosed("socket closed")

        payload = self._read_exact(self.sock, length)
        if payload is None:
            raise WsClosed("socket closed")

        if masked:
            payload = self._mask_bytes(payload, mask_key)

        return fin, opcode, payload

    def _write_frame(self, opcode, payload):
        if payload is None:
            payload = b""
        fin = 0x80
        first = fin | opcode
        mask_bit = 0x80
        length = len(payload)

        header = bytearray()
        header.append(first)
        if length < 126:
            header.append(mask_bit | length)
        elif length < 65536:
            header.append(mask_bit | 126)
            header.extend(ustruct.pack("!H", length))
        else:
            header.append(mask_bit | 127)
            header.extend(ustruct.pack("!Q", length))

        mask_key = uos.urandom(4)
        header.extend(mask_key)
        masked_payload = self._mask_bytes(payload, mask_key)
        self._write_all(self.sock, bytes(header))
        self._write_all(self.sock, masked_payload)

    def _mask_bytes(self, payload, mask_key):
        out = bytearray(len(payload))
        for i in range(len(payload)):
            out[i] = payload[i] ^ mask_key[i % 4]
        return bytes(out)

    def _read_exact(self, sock, size):
        if size == 0:
            return b""
        chunks = bytearray()
        while len(chunks) < size:
            try:
                chunk = self._sock_read(sock, size - len(chunks))
            except Exception as e:
                if self._is_timeout_error(e):
                    raise WsTimeout("socket timeout")
                if self._is_socket_closed_error(e):
                    raise WsClosed("socket closed")
                raise
            if not chunk:
                if len(chunks) == 0:
                    return None
                return None
            chunks.extend(chunk)
        return bytes(chunks)

    def _sock_read(self, sock, size):
        if hasattr(sock, "recv"):
            return sock.recv(size)
        if hasattr(sock, "read"):
            return sock.read(size)
        raise WsClosed("socket read unavailable")

    def _write_all(self, sock, data):
        sent = 0
        total = len(data)
        while sent < total:
            try:
                if hasattr(sock, "write"):
                    count = sock.write(data[sent:])
                elif hasattr(sock, "send"):
                    count = sock.send(data[sent:])
                else:
                    raise WsClosed("socket write unavailable")
            except Exception as e:
                if self._is_timeout_error(e):
                    raise WsTimeout("socket timeout")
                if self._is_socket_closed_error(e):
                    raise WsClosed("socket write failed")
                raise
            if count is None:
                count = 0
            if count <= 0:
                raise WsClosed("socket write failed")
            sent += count

    def _is_timeout_error(self, exc):
        text = str(exc)
        if "timed out" in text.lower():
            return True
        args = getattr(exc, "args", None)
        if not args:
            return False
        code = args[0]
        return code in (11, 110, 115, 116)

    def _is_socket_closed_error(self, exc):
        text = str(exc).lower()
        if "econnaborted" in text or "econnreset" in text:
            return True
        if "socket closed" in text or "socket write failed" in text:
            return True
        if "network is unreachable" in text or "connection reset" in text:
            return True
        args = getattr(exc, "args", None)
        if not args:
            return False
        code = args[0]
        return code in (32, 54, 103, 104, 107, 113, 128, 129, 130, 131)

import utime


class _ExternalTool(object):

    def __init__(self, executor):
        self.executor = executor

    def execute(self, args):
        return self.executor(args)


class ToolRunner(object):

    def __init__(self, cfg, state, extension=None):
        self.cfg = cfg
        self.state = state
        self.extension = extension
        self._entries = []
        self._name_to_entry = {}
        self._loaded_domains = {}
        self._impl_cache = {}
        self._register(
            "qpy.help",
            "Enumerate the currently declared qpyclaw node tools.",
            ["help", "qpy.tools.help"],
            "runtime",
            True,
            "runtime",
            "ToolToolsCatalog",
            "catalog_provider",
        )
        self._register(
            "qpy.device.info",
            "Read modem identity, firmware, and SIM basics.",
            ["device.info", "tool_device_info"],
            "device",
            True,
            "device",
            "ToolDeviceInfo",
        )
        self._register(
            "qpy.device.status",
            "Read merged device, network, SIM, storage, and runtime status.",
            ["device.status"],
            "device",
            True,
            "device",
            "ToolDeviceStatus",
        )
        self._register(
            "qpy.device.reboot",
            "Schedule a local module reboot after result acknowledgement.",
            ["device.reboot"],
            "device",
            False,
            "device",
            "ToolDeviceReboot",
        )
        self._register(
            "qpy.net.diag",
            "Run cellular registration and data-context diagnostics.",
            ["net.diag", "tool_net_diag"],
            "network",
            True,
            "network",
            "ToolNetDiag",
        )
        self._register(
            "qpy.net.ifconfig",
            "Return current PDP context and preferred IP address.",
            ["net.ifconfig"],
            "network",
            True,
            "network",
            "ToolNetIfconfig",
        )
        self._register(
            "qpy.sim.info",
            "Return SIM presence, readiness, ICCID, and IMSI.",
            ["sim.info"],
            "network",
            True,
            "network",
            "ToolSimInfo",
        )
        self._register(
            "qpy.cell.info",
            "Return serving-cell and neighbor-cell data.",
            ["cell.info"],
            "network",
            True,
            "network",
            "ToolCellInfo",
        )
        self._register(
            "qpy.runtime.status",
            "Return runtime session, reconnect, and queue state.",
            ["runtime.status"],
            "runtime",
            True,
            "runtime",
            "ToolRuntimeStatus",
        )
        self._register(
            "qpy.tools.catalog",
            "Enumerate all declared node tools and aliases.",
            ["tools.catalog"],
            "runtime",
            True,
            "runtime",
            "ToolToolsCatalog",
            "catalog_provider",
        )
        self._register(
            "qpy.fs.list",
            "List a filesystem path and optionally recurse.",
            ["fs.list", "qpy.fs.ls", "fs.ls", "qpy.fs.tree", "fs.tree"],
            "filesystem",
            True,
            "filesystem",
            "ToolFsList",
        )
        self._register(
            "qpy.fs.read",
            "Read a local file from the module filesystem.",
            ["fs.read"],
            "filesystem",
            True,
            "filesystem",
            "ToolFsRead",
        )
        self._register(
            "qpy.fs.write",
            "Write text content into a local file.",
            ["fs.write", "qpy.push", "push"],
            "filesystem",
            False,
            "filesystem",
            "ToolFsWrite",
        )
        self._register(
            "qpy.fs.mkdir",
            "Create a directory path on the module filesystem.",
            ["fs.mkdir"],
            "filesystem",
            False,
            "filesystem",
            "ToolFsMkdir",
        )
        self._register(
            "qpy.fs.remove",
            "Remove a file or directory from the module filesystem.",
            ["fs.remove", "fs.rm", "fs.rmdir"],
            "filesystem",
            False,
            "filesystem",
            "ToolFsRemove",
        )
        self._register(
            "qpy.repl.run",
            "Execute ad-hoc Python on the device and return a summarized result.",
            ["repl.run"],
            "runtime",
            False,
            "runtime",
            "ToolReplRun",
        )
        self._register(
            "qpy.voice.status",
            "Return the operator-session and voice-dialog P0 status snapshot.",
            ["voice.status"],
            "voice",
            True,
            "runtime",
            "ToolVoiceStatus",
        )
        self._register(
            "qpy.voice.chat",
            "Send a text transcript into the OpenClaw main session via operator role.",
            ["voice.chat"],
            "voice",
            False,
            "runtime",
            "ToolVoiceChat",
        )
        self._register(
            "qpy.voice.abort",
            "Abort the active voice chat run for the configured session.",
            ["voice.abort"],
            "voice",
            False,
            "runtime",
            "ToolVoiceAbort",
        )
        self._register_extension_tools()

    def _register(self, name, summary, aliases, category, read_only, domain, class_name, factory_kind=None):
        entry = {
            "name": name,
            "impl": None,
            "summary": summary,
            "aliases": aliases or [],
            "category": category,
            "read_only": bool(read_only),
            "domain": domain,
            "class_name": class_name,
            "factory_kind": factory_kind or "default",
        }
        self._entries.append(entry)
        self._name_to_entry[name] = entry
        for alias in entry["aliases"]:
            self._name_to_entry[alias] = entry

    def _register_external(self, name, summary, aliases, category, read_only, executor):
        if name in self._name_to_entry:
            raise Exception("duplicate tool: " + name)
        impl = executor
        if not hasattr(impl, "execute"):
            impl = _ExternalTool(executor)
        entry = {
            "name": name,
            "impl": impl,
            "summary": summary,
            "aliases": aliases or [],
            "category": category,
            "read_only": bool(read_only),
            "domain": "external",
            "class_name": "",
            "factory_kind": "external",
        }
        self._entries.append(entry)
        self._name_to_entry[name] = entry
        for alias in entry["aliases"]:
            if alias in self._name_to_entry:
                raise Exception("duplicate tool alias: " + alias)
            self._name_to_entry[alias] = entry

    def _register_extension_tools(self):
        if self.extension is None or not hasattr(self.extension, "get_tool_specs"):
            return
        specs = self.extension.get_tool_specs()
        if not isinstance(specs, list):
            return
        for spec in specs:
            if not isinstance(spec, dict):
                continue
            name = str(spec.get("name") or "").strip()
            executor = spec.get("executor")
            if not name or executor is None:
                continue
            aliases = spec.get("aliases") or []
            summary = str(spec.get("summary") or "").strip()
            category = str(spec.get("category") or "board").strip() or "board"
            read_only = bool(spec.get("read_only", True))
            self._register_external(
                name,
                summary,
                aliases,
                category,
                read_only,
                executor,
            )

    def _cache_key(self, entry):
        return entry["domain"] + ":" + entry["class_name"] + ":" + entry["factory_kind"]

    def _build_impl(self, module, entry):
        cache_key = self._cache_key(entry)
        impl = self._impl_cache.get(cache_key)
        if impl is not None:
            return impl
        tool_cls = globals()[entry["class_name"]]
        if entry["factory_kind"] == "catalog_provider":
            impl = tool_cls(self.cfg, self.state, self.catalog_entries)
        else:
            impl = tool_cls(self.cfg, self.state)
        self._impl_cache[cache_key] = impl
        return impl

    def _load_domain(self, domain):
        if domain in self._loaded_domains:
            return
        known = False
        for entry in self._entries:
            if entry["domain"] != domain:
                continue
            known = True
            if entry["impl"] is None:
                entry["impl"] = self._build_impl(None, entry)
        if not known:
            raise Exception("unknown tool domain")
        self._loaded_domains[domain] = True

    def catalog_entries(self):
        return self._entries

    def _allowed(self, entry, requested_tool):
        allow_tools = getattr(self.cfg, "ALLOW_TOOLS", []) or []
        if "*" in allow_tools:
            return True
        if requested_tool in allow_tools:
            return True
        if entry["name"] in allow_tools:
            return True
        for alias in entry["aliases"]:
            if alias in allow_tools:
                return True
        return False

    def execute(self, cmd):
        started = utime.ticks_ms()
        request_id = cmd.get("request_id", "")
        tool = cmd.get("tool", "")
        args = self._normalize_args(tool, cmd.get("args") or {})

        entry = self._name_to_entry.get(tool)
        if not entry:
            return self._error(request_id, tool, tool, "UNSUPPORTED_TOOL", "tool not found", started)
        if not self._allowed(entry, tool):
            return self._error(request_id, tool, entry["name"], "UNSUPPORTED_TOOL", "tool not allowed", started)
        if entry["impl"] is None:
            self._load_domain(entry["domain"])

        self.state.note_command(request_id, entry["name"])
        try:
            data = entry["impl"].execute(args)
            duration_ms = utime.ticks_diff(utime.ticks_ms(), started)
            probe_timings = {}
            if isinstance(data, dict):
                timings = data.get("probe_timings_ms")
                if isinstance(timings, dict):
                    probe_timings = timings
            self.state.note_probe_metrics(entry["name"], duration_ms, probe_timings)
            return {
                "cmd_id": request_id,
                "requested_tool": tool,
                "tool": entry["name"],
                "status": "succeeded",
                "result_code": "OK",
                "data": data,
                "error": None,
                "duration_ms": duration_ms,
            }
        except Exception as e:
            return self._error(request_id, tool, entry["name"], "EXEC_RUNTIME_ERROR", str(e), started)

    def _normalize_args(self, requested_tool, args):
        if not isinstance(args, dict):
            return {"value": args}
        data = {}
        for key in args:
            data[key] = args[key]
        if requested_tool in ["qpy.fs.tree", "fs.tree"] and "recursive" not in data:
            data["recursive"] = True
        if requested_tool in ["qpy.push", "push"]:
            if "path" not in data and "remote_path" in data:
                data["path"] = data.get("remote_path")
            if "content" not in data and "text" in data:
                data["content"] = data.get("text")
        return data

    def _error(self, request_id, requested_tool, tool, code, message, started):
        return {
            "cmd_id": request_id,
            "requested_tool": requested_tool,
            "tool": tool,
            "status": "failed",
            "result_code": code,
            "data": None,
            "error": message,
            "duration_ms": utime.ticks_diff(utime.ticks_ms(), started),
        }

import utime

try:
    import _thread
except Exception:
    _thread = None


def _sleep_ms(delay_ms):
    if delay_ms <= 0:
        delay_ms = 1
    if hasattr(utime, "sleep_ms"):
        utime.sleep_ms(delay_ms)
        return
    utime.sleep(float(delay_ms) / 1000.0)


class CommandWorker(object):

    def __init__(self, runner, state):
        self.runner = runner
        self.state = state
        self.available = bool(_thread) and hasattr(_thread, "start_new_thread")
        self._lock = _thread.allocate_lock() if bool(_thread) and hasattr(_thread, "allocate_lock") else None
        self._pending_cmd = None
        self._result = None
        self._executing = False
        self._started = False
        self.state.note_worker_status(self.available, False)
        if self.available:
            self._start()

    def _acquire(self):
        if self._lock is not None:
            self._lock.acquire()

    def _release(self):
        if self._lock is not None:
            self._lock.release()

    def _start(self):
        if self._started:
            return
        _thread.start_new_thread(self._run_forever, ())
        self._started = True

    def can_accept(self):
        self._acquire()
        try:
            return self._pending_cmd is None and self._result is None and (not self._executing)
        finally:
            self._release()

    def submit(self, cmd):
        if (not self.available) or (not cmd):
            return False
        accepted = False
        self._acquire()
        try:
            if self._pending_cmd is None and self._result is None and (not self._executing):
                self._pending_cmd = cmd
                accepted = True
        finally:
            self._release()
        if accepted:
            self.state.note_inflight_start(cmd.get("request_id"), cmd.get("tool"))
            self.state.note_worker_status(self.available, True)
        return accepted

    def poll_result(self):
        self._acquire()
        try:
            item = self._result
            self._result = None
            busy = self._pending_cmd is not None or self._executing or self._result is not None
        finally:
            self._release()
        self.state.note_worker_status(self.available, busy)
        return item

    def _build_worker_error(self, cmd, message):
        return {
            "cmd_id": cmd.get("request_id", ""),
            "requested_tool": cmd.get("tool", ""),
            "tool": cmd.get("tool", ""),
            "status": "failed",
            "result_code": "EXEC_RUNTIME_ERROR",
            "data": None,
            "error": message,
            "duration_ms": 0,
        }

    def _run_forever(self):
        while True:
            cmd = None
            self._acquire()
            try:
                if self._pending_cmd is not None and self._result is None and (not self._executing):
                    cmd = self._pending_cmd
                    self._pending_cmd = None
                    self._executing = True
            finally:
                self._release()

            if cmd is None:
                if hasattr(utime, "sleep_ms"):
                    utime.sleep_ms(20)
                else:
                    utime.sleep(0.02)
                continue

            try:
                result = self.runner.execute(cmd)
            except Exception as e:
                self.state.note_error("WORKER_EXEC_FAILED", str(e))
                result = self._build_worker_error(cmd, str(e))

            self._acquire()
            try:
                self._result = {
                    "cmd": cmd,
                    "result": result,
                }
                self._executing = False
                busy = self._pending_cmd is not None or self._result is not None
            finally:
                self._release()

            self.state.note_inflight_finish(result.get("status"), result.get("result_code"))
            self.state.note_worker_status(self.available, busy)

import utime
import ujson as _json

try:
    import _thread
except Exception:
    _thread = None



def dumps(value):
    return _json.dumps(value)


def loads(value):
    return _json.loads(value)


class WsNativeTransport(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self.ws = None
        self.online = False
        self._seq = 0
        self._last_hb_ms = 0
        self._last_telemetry_ms = 0
        self._pending_cmds = []
        self._outbox = []
        self._result_cache = {}
        self._result_cache_keys = []
        self._queue_lock = _thread.allocate_lock() if bool(_thread) and hasattr(_thread, "allocate_lock") else None
        self._update_depths()

    def connect(self):
        self.close("reconnect")
        self.state.note_connecting()
        ws = WsClient()
        try:
            ws.connect(self.cfg.OPENCLAW_WS_URL, int(getattr(self.cfg, "CONNECT_TIMEOUT_SEC", 8)))
            self.ws = ws
            challenge = self._wait_connect_challenge()
            nonce = challenge.get("nonce") if isinstance(challenge, dict) else None
            if not nonce:
                raise Exception("connect challenge missing nonce")

            auth, device, device_auth_mode = resolve_connect_security(self.cfg, self.state, nonce)
            params = self._build_connect_params(auth, device)
            response = self._request("connect", params, int(getattr(self.cfg, "ACK_TIMEOUT_MS", 5000)))
            if not response.get("ok"):
                error = response.get("error") or {}
                code = error.get("code") if isinstance(error, dict) else "CONNECT_FAILED"
                message = error.get("message") if isinstance(error, dict) else str(error)
                raise Exception(str(code or "CONNECT_FAILED") + ":" + str(message or "connect failed"))

            payload = response.get("payload") or {}
            auth_info = payload.get("auth") or {}
            device_token = auth_info.get("deviceToken")
            if device_token:
                self.state.device_token = device_token
            protocol = payload.get("protocol") or 0
            node_id = self.cfg.DEVICE_ID
            if isinstance(device, dict) and device.get("id"):
                node_id = device.get("id")
            self.online = True
            self.state.note_connect(node_id, protocol, payload)
            self._last_hb_ms = 0
            self._last_telemetry_ms = utime.ticks_ms()
            if self._generic_node_events_enabled():
                self._queue_event("lifecycle", {
                    "phase": "online",
                    "device_auth_mode": device_auth_mode,
                    "protocol": protocol,
                }, "info")
                self.flush_outbox(1)
            return True
        except Exception as e:
            self.state.note_connect_failure("CONNECT_FAILED", str(e))
            self.close("connect-failed")
            return False

    def close(self, reason="close"):
        if self.online and self._generic_node_events_enabled():
            self._queue_event("lifecycle", {"phase": "offline", "reason": reason}, "warning")
        self.state.note_close(reason)
        self.online = False
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None
        self.state.note_disconnect()
        self._update_depths()

    def tick(self):
        self.state.note_tick()
        now = utime.ticks_ms()
        hb_ms = int(getattr(self.cfg, "HEARTBEAT_INTERVAL_SEC", 15) * 1000)
        tel_ms = int(getattr(self.cfg, "TELEMETRY_INTERVAL_SEC", 60) * 1000)
        if self._generic_node_events_enabled():
            if utime.ticks_diff(now, self._last_hb_ms) >= hb_ms:
                self._last_hb_ms = now
                self._queue_event("heartbeat", self._heartbeat_payload(), "info")
            if tel_ms > 0 and utime.ticks_diff(now, self._last_telemetry_ms) >= tel_ms:
                self._last_telemetry_ms = now
                self._queue_event("telemetry", build_runtime_telemetry(self.cfg, self.state), "info")
        self.flush_outbox(1)

    def recv_cmd(self, timeout_ms, can_consume=True):
        if can_consume:
            cmd = self._pop_pending_cmd()
            if cmd:
                return cmd
        if not self.online or self.ws is None:
            return None

        deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            remaining = utime.ticks_diff(deadline, utime.ticks_ms())
            try:
                frame = self._recv_frame(remaining)
            except WsTimeout:
                return None
            if frame is None:
                return None
            self._handle_incoming_frame(frame)
            if can_consume:
                cmd = self._pop_pending_cmd()
                if cmd:
                    return cmd
        return None

    def send_result(self, cmd, result_payload):
        params = self._build_result_params(cmd, result_payload)
        cache_key = cmd.get("dedupe_key") or cmd.get("request_id")
        if cache_key:
            self._cache_result(cache_key, params)
        self._enqueue_request("node.invoke.result", params, True)
        return self.flush_outbox(1)

    def flush_outbox(self, limit):
        if not self.online or self.ws is None:
            self._update_depths()
            return False
        sent_any = False
        processed = 0
        while processed < limit:
            item = self._claim_outbox_item()
            if item is None:
                break
            try:
                response = self._request(item["method"], item["params"], int(getattr(self.cfg, "ACK_TIMEOUT_MS", 5000)))
                if not response.get("ok"):
                    error = response.get("error") or {}
                    code = error.get("code") if isinstance(error, dict) else "ACK_FAILED"
                    message = error.get("message") if isinstance(error, dict) else str(error)
                    raise Exception(str(code or "ACK_FAILED") + ":" + str(message or "ack failed"))
                self._finish_outbox_success(item)
                self.state.note_ack()
                processed += 1
                sent_any = True
            except Exception as e:
                self.state.note_error("OUTBOX_SEND_FAILED", str(e))
                self.state.note_outbox_error(str(e))
                if self._finish_outbox_failure(item):
                    processed += 1
                    continue
                if self._is_fatal_outbox_error(e):
                    self.close("outbox-failed")
                break
        return sent_any

    def queue_boot_event(self):
        if not self._generic_node_events_enabled():
            return False
        return self._queue_event("lifecycle", {
            "phase": "boot",
            "firmware": getattr(self.cfg, "FW_VERSION", ""),
            "device_name": getattr(self.cfg, "DEVICE_NAME", ""),
        }, "info")

    def _wait_connect_challenge(self):
        deadline = utime.ticks_add(utime.ticks_ms(), int(getattr(self.cfg, "CONNECT_TIMEOUT_SEC", 8) * 1000))
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            remaining = utime.ticks_diff(deadline, utime.ticks_ms())
            frame = self._recv_frame(remaining)
            if not isinstance(frame, dict):
                continue
            if frame.get("type") == "event" and frame.get("event") == "connect.challenge":
                self.state.note_event("connect.challenge")
                return frame.get("payload") or {}
        raise Exception("connect challenge timeout")

    def _build_connect_params(self, auth, device):
        params = {
            "minProtocol": int(getattr(self.cfg, "OPENCLAW_MIN_PROTOCOL", 3)),
            "maxProtocol": int(getattr(self.cfg, "OPENCLAW_MAX_PROTOCOL", 3)),
            "client": {
                "id": getattr(self.cfg, "OPENCLAW_CLIENT_ID", "qpyclaw-node"),
                "displayName": getattr(self.cfg, "OPENCLAW_CLIENT_DISPLAY_NAME", "qpyclaw QuecPython Node"),
                "version": getattr(self.cfg, "FW_VERSION", "0.1.0"),
                "platform": getattr(self.cfg, "OPENCLAW_CLIENT_PLATFORM", "quectel"),
                "deviceFamily": getattr(self.cfg, "OPENCLAW_CLIENT_DEVICE_FAMILY", "quecpython"),
                "mode": getattr(self.cfg, "OPENCLAW_CLIENT_MODE", "node"),
            },
            "role": getattr(self.cfg, "OPENCLAW_ROLE", "node"),
            "scopes": list(getattr(self.cfg, "OPENCLAW_SCOPES", [])),
            "caps": list(getattr(self.cfg, "OPENCLAW_CAPS", [])),
            "commands": list(getattr(self.cfg, "OPENCLAW_COMMANDS", [])),
            "permissions": getattr(self.cfg, "OPENCLAW_PERMISSIONS", {}),
            "userAgent": getattr(self.cfg, "OPENCLAW_USER_AGENT", "qpyclaw-node/0.1.0"),
        }
        if auth:
            params["auth"] = auth
        if device:
            params["device"] = device
        return params

    def _request(self, method, params, timeout_ms):
        request_id = self._next_id(method)
        frame = {
            "type": "req",
            "id": request_id,
            "method": method,
            "params": params,
        }
        self._send_frame(frame)
        return self._await_response(request_id, timeout_ms)

    def _await_response(self, request_id, timeout_ms):
        deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            remaining = utime.ticks_diff(deadline, utime.ticks_ms())
            frame = self._recv_frame(remaining)
            if not isinstance(frame, dict):
                continue
            if frame.get("type") == "res" and frame.get("id") == request_id:
                return frame
            self._handle_incoming_frame(frame)
        raise Exception("ack timeout")

    def _recv_frame(self, timeout_ms):
        if self.ws is None:
            raise WsClosed("websocket closed")
        text = self.ws.recv_text(timeout_ms)
        frame = loads(text)
        self.state.note_received()
        return frame

    def _send_frame(self, frame):
        if self.ws is None:
            raise WsClosed("websocket closed")
        self.ws.send_text(dumps(frame))
        self.state.note_sent()

    def _handle_incoming_frame(self, frame):
        frame_type = frame.get("type")
        if frame_type == "event":
            event_name = frame.get("event")
            self.state.note_event(event_name)
            if event_name == "node.invoke.request":
                self._consume_invoke_request(frame.get("payload") or {})
        return None

    def _consume_invoke_request(self, payload):
        request_id = payload.get("id")
        node_id = payload.get("nodeId") or self.state.node_id
        command = payload.get("command") or ""
        params = {}
        raw_json = payload.get("paramsJSON")
        if raw_json not in (None, ""):
            try:
                params = loads(raw_json)
            except Exception:
                self._enqueue_request("node.invoke.result", {
                    "id": request_id,
                    "nodeId": node_id,
                    "ok": False,
                    "error": {
                        "code": "INVALID_PARAMS",
                        "message": "paramsJSON parse failed",
                    },
                }, True)
                return None
        dedupe_key = payload.get("idempotencyKey") or request_id
        if dedupe_key:
            cached = self._get_cached_result(dedupe_key)
            if cached:
                self._enqueue_request("node.invoke.result", cached, True)
                return None
        cmd = {
            "request_id": request_id,
            "node_id": node_id,
            "tool": command,
            "args": params if isinstance(params, dict) else {"value": params},
            "timeout_ms": payload.get("timeoutMs") or int(getattr(self.cfg, "MAX_CMD_EXEC_SEC", 10) * 1000),
            "idempotency_key": payload.get("idempotencyKey"),
            "dedupe_key": dedupe_key,
        }
        self._acquire_queue()
        try:
            self._pending_cmds.append(cmd)
            self._update_depths_locked()
        finally:
            self._release_queue()
        return None

    def _build_result_params(self, cmd, result_payload):
        params = {
            "id": cmd.get("request_id"),
            "nodeId": cmd.get("node_id") or self.state.node_id,
            "ok": result_payload.get("status") == "succeeded",
        }
        if params["ok"]:
            params["payload"] = result_payload
        else:
            params["error"] = {
                "code": result_payload.get("result_code") or "EXEC_RUNTIME_ERROR",
                "message": result_payload.get("error") or "command failed",
            }
        return params

    def _heartbeat_payload(self):
        runtime = self.state.snapshot()
        return {
            "event_id": self._next_id("heartbeat"),
            "logical_device_id": self.cfg.DEVICE_ID,
            "node_id": self.state.node_id,
            "severity": "info",
            "ts": wall_time_ms(),
            "payload": {
                "online": runtime.get("online"),
                "reconnect_count": runtime.get("reconnect_count"),
                "last_error_code": runtime.get("last_error_code"),
                "last_cmd_tool": runtime.get("last_cmd_tool"),
            },
        }

    def _generic_node_events_enabled(self):
        return bool(getattr(self.cfg, "OPENCLAW_GENERIC_NODE_EVENTS", False))

    def _queue_event(self, event_name, payload, severity):
        envelope = {
            "event_id": self._next_id(event_name),
            "logical_device_id": self.cfg.DEVICE_ID,
            "node_id": self.state.node_id,
            "severity": severity,
            "ts": wall_time_ms(),
            "payload": payload,
        }
        return self._enqueue_request("node.event", {
            "event": event_name,
            "payload": envelope,
        }, False)

    def _enqueue_request(self, method, params, critical):
        max_size = int(getattr(self.cfg, "OUTBOX_MAX", 64))
        dropped = False
        self._acquire_queue()
        try:
            if len(self._outbox) >= max_size:
                index = self._find_droppable_outbox_index_locked(True)
                if index < 0:
                    index = self._find_droppable_outbox_index_locked(False)
                if index >= 0:
                    self._outbox.pop(index)
                    dropped = True
                elif not critical:
                    self._update_depths_locked()
                    return False
            self._outbox.append({
                "method": method,
                "params": params,
                "critical": bool(critical),
                "attempts": 0,
                "next_attempt_ms": 0,
                "sending": False,
            })
            self._update_depths_locked()
        finally:
            self._release_queue()
        if dropped:
            self.state.note_outbox_error("OUTBOX_DROP_OLDEST")
        return True

    def _cache_result(self, key, params):
        self._acquire_queue()
        try:
            self._result_cache[key] = params
            self._result_cache_keys.append(key)
            max_size = int(getattr(self.cfg, "DEDUPE_WINDOW", 64))
            while len(self._result_cache_keys) > max_size:
                old_key = self._result_cache_keys.pop(0)
                if old_key in self._result_cache:
                    del self._result_cache[old_key]
            self._update_depths_locked()
        finally:
            self._release_queue()

    def _next_id(self, prefix):
        self._seq += 1
        return str(prefix) + "_" + str(utime.ticks_ms()) + "_" + str(self._seq)

    def _update_depths(self):
        self._acquire_queue()
        try:
            self._update_depths_locked()
        finally:
            self._release_queue()

    def _update_depths_locked(self):
        self.state.update_queue_depths(len(self._pending_cmds), len(self._outbox), len(self._result_cache_keys))

    def _acquire_queue(self):
        if self._queue_lock is not None:
            self._queue_lock.acquire()

    def _release_queue(self):
        if self._queue_lock is not None:
            self._queue_lock.release()

    def _pop_pending_cmd(self):
        cmd = None
        self._acquire_queue()
        try:
            if self._pending_cmds:
                cmd = self._pending_cmds.pop(0)
            self._update_depths_locked()
        finally:
            self._release_queue()
        return cmd

    def _get_cached_result(self, key):
        cached = None
        self._acquire_queue()
        try:
            cached = self._result_cache.get(key)
        finally:
            self._release_queue()
        return cached

    def _claim_outbox_item(self):
        item = None
        self._acquire_queue()
        try:
            if self._outbox:
                head = self._outbox[0]
                if (not head.get("sending")) and self._outbox_retry_ready(head):
                    head["sending"] = True
                    item = head
            self._update_depths_locked()
        finally:
            self._release_queue()
        return item

    def _finish_outbox_success(self, item):
        self._acquire_queue()
        try:
            self._remove_outbox_item_locked(item)
            self._update_depths_locked()
        finally:
            self._release_queue()

    def _finish_outbox_failure(self, item):
        removed = False
        self._acquire_queue()
        try:
            current = self._find_outbox_item_locked(item)
            if current is None:
                self._update_depths_locked()
                return False
            current["sending"] = False
            current["attempts"] = int(current.get("attempts") or 0) + 1
            if current["attempts"] > int(getattr(self.cfg, "MAX_RETRY", 3)):
                self._remove_outbox_item_locked(current)
                removed = True
            else:
                current["next_attempt_ms"] = utime.ticks_add(
                    utime.ticks_ms(),
                    int(getattr(self.cfg, "OUTBOX_RETRY_BACKOFF_MS", 1000)) * current["attempts"],
                )
            self._update_depths_locked()
        finally:
            self._release_queue()
        return removed

    def _find_outbox_item_locked(self, item):
        index = 0
        while index < len(self._outbox):
            if self._outbox[index] is item:
                return self._outbox[index]
            index += 1
        return None

    def _remove_outbox_item_locked(self, item):
        index = 0
        while index < len(self._outbox):
            if self._outbox[index] is item:
                self._outbox.pop(index)
                return True
            index += 1
        return False

    def _find_droppable_outbox_index_locked(self, prefer_non_critical):
        index = 0
        while index < len(self._outbox):
            item = self._outbox[index]
            if item.get("sending"):
                index += 1
                continue
            if prefer_non_critical and item.get("critical"):
                index += 1
                continue
            return index
        return -1

    def _outbox_retry_ready(self, item):
        next_attempt_ms = item.get("next_attempt_ms") or 0
        if not next_attempt_ms:
            return True
        return utime.ticks_diff(utime.ticks_ms(), next_attempt_ms) >= 0

    def _is_fatal_outbox_error(self, err):
        if isinstance(err, WsClosed):
            return True
        if isinstance(err, WsTimeout):
            return False
        if isinstance(err, WsError):
            return True
        text = str(err).lower()
        if "ack timeout" in text:
            return False
        if "ack failed" in text:
            return False
        if "websocket closed" in text or "server closed websocket" in text or "socket write failed" in text:
            return True
        return False

import utime


_LAST_NODE = None
_LAST_EXCEPTION = ""


def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def _safe_call(func, *args):
    if not func:
        return None
    return func(*args)


def _call_power_restart():
    misc = _safe_import("misc")
    if misc and hasattr(misc, "Power"):
        power = getattr(misc, "Power")
        for attr in ("powerRestart", "restart"):
            if hasattr(power, attr):
                _safe_call(getattr(power, attr))
                return "misc.Power." + attr

    power_mod = _safe_import("Power")
    if power_mod:
        for attr in ("powerRestart", "restart"):
            if hasattr(power_mod, attr):
                _safe_call(getattr(power_mod, attr))
                return "Power." + attr
    return ""


def _call_machine_reset():
    machine = _safe_import("machine")
    if machine and hasattr(machine, "reset"):
        _safe_call(getattr(machine, "reset"))
        return "machine.reset"
    return ""


def _call_pm_reboot():
    pm = _safe_import("pm")
    if pm:
        for attr in ("reboot", "reset"):
            if hasattr(pm, attr):
                _safe_call(getattr(pm, attr))
                return "pm." + attr
    return ""


def execute_reboot(mode):
    _ = mode
    method = _call_power_restart()
    if method:
        return method
    method = _call_machine_reset()
    if method:
        return method
    method = _call_pm_reboot()
    if method:
        return method
    raise Exception("no supported reboot method found")


def perform_pending_reboot(state):
    spec = state.pending_reboot_due()
    if not spec:
        return False
    mode = spec.get("mode") or "soft"
    state.clear_pending_reboot()
    execute_reboot(mode)
    return True


def _build_transport(cfg, state):
    if cfg.ACCESS_MODE != "ws_native":
        raise Exception("unsupported access mode: " + str(cfg.ACCESS_MODE))
    return WsNativeTransport(cfg, state)


def _append_unique(items, value):
    if value in items:
        return items
    items.append(value)
    return items


def _extension_tool_specs(extension):
    if extension is None or not hasattr(extension, "get_tool_specs"):
        return []
    specs = extension.get_tool_specs()
    if isinstance(specs, list):
        return specs
    return []


def _apply_extension_cfg(cfg, extension):
    specs = _extension_tool_specs(extension)
    if specs:
        commands = list(getattr(cfg, "OPENCLAW_COMMANDS", []) or [])
        allow_tools = list(getattr(cfg, "ALLOW_TOOLS", []) or [])
        allow_all = "*" in allow_tools
        for spec in specs:
            if not isinstance(spec, dict):
                continue
            name = str(spec.get("name") or "").strip()
            if not name:
                continue
            _append_unique(commands, name)
            if not allow_all:
                _append_unique(allow_tools, name)
            aliases = spec.get("aliases") or []
            for alias in aliases:
                alias_text = str(alias or "").strip()
                if not alias_text:
                    continue
                _append_unique(commands, alias_text)
                if not allow_all:
                    _append_unique(allow_tools, alias_text)
        cfg.OPENCLAW_COMMANDS = commands
        if not allow_all:
            cfg.ALLOW_TOOLS = allow_tools

    if extension is None or not hasattr(extension, "get_caps"):
        return
    caps = extension.get_caps()
    if not isinstance(caps, list):
        return
    current_caps = list(getattr(cfg, "OPENCLAW_CAPS", []) or [])
    for cap in caps:
        cap_text = str(cap or "").strip()
        if not cap_text:
            continue
        _append_unique(current_caps, cap_text)
    cfg.OPENCLAW_CAPS = current_caps


class VoiceDialogClient(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self.ws = None
        self.online = False
        self._seq = 0
        self._lock = _thread.allocate_lock() if bool(_thread) and hasattr(_thread, "allocate_lock") else None
        self.connected_at_ms = 0
        self.last_connect_ms = 0
        self.last_disconnect_ms = 0
        self.last_close_reason = ""
        self.last_close_ms = 0
        self.last_error = ""
        self.last_error_code = ""
        self.last_error_ms = 0
        self.last_event = ""
        self.last_event_ms = 0
        self.last_run_id = ""
        self.last_turn_id = ""
        self.last_sent_message = ""
        self.last_sent_session_key = ""
        self.last_reply_text = ""
        self.last_reply_message_id = ""
        self.last_voice_directive = {}
        self.last_history_count = 0
        self.last_chat_status = ""
        self.last_history_poll_ms = 0
        self.last_subscribe_error = ""
        self.last_chat_duration_ms = 0
        self.last_chat_event_count = 0
        self.last_chat_history_polls = 0
        self.last_server_hello = None
        self.server_methods = []
        self.subscriptions = {}

    def _acquire(self):
        if self._lock is not None:
            self._lock.acquire()

    def _release(self):
        if self._lock is not None:
            self._lock.release()

    def _fail_locked(self, code, message, close=False):
        self.last_error_code = code or ""
        self.last_error = message or ""
        self.last_error_ms = utime.ticks_ms()
        if close:
            self._close_locked(code or "error")
        raise Exception((code or "VOICE_ERROR") + ": " + (message or "voice dialog failed"))

    def _bool_value(self, value, default):
        if value is None:
            return bool(default)
        if isinstance(value, bool):
            return value
        text = _string(value).strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off"):
            return False
        return bool(default)

    def _ws_url(self):
        text = _string(getattr(self.cfg, "VOICE_OPERATOR_WS_URL", "")).strip()
        if text:
            return text
        return _string(getattr(self.cfg, "OPENCLAW_WS_URL", "")).strip()

    def _session_key(self, session_key):
        text = _string(session_key).strip()
        if text:
            return text
        text = _string(getattr(self.cfg, "VOICE_MAIN_SESSION_KEY", "main")).strip()
        if text:
            return text
        return "main"

    def _connect_timeout_sec(self):
        value = getattr(self.cfg, "VOICE_OPERATOR_CONNECT_TIMEOUT_SEC", getattr(self.cfg, "CONNECT_TIMEOUT_SEC", 12))
        try:
            value = int(value)
        except Exception:
            value = 12
        if value <= 0:
            value = 12
        return value

    def _ack_timeout_ms(self):
        value = getattr(self.cfg, "ACK_TIMEOUT_MS", 10000)
        try:
            value = int(value)
        except Exception:
            value = 10000
        if value <= 0:
            value = 10000
        return value

    def _chat_timeout_ms(self, timeout_ms):
        value = timeout_ms
        if value in (None, ""):
            value = getattr(self.cfg, "VOICE_CHAT_TIMEOUT_MS", 45000)
        try:
            value = int(value)
        except Exception:
            value = 45000
        if value <= 0:
            value = 45000
        return value

    def _chat_poll_ms(self):
        value = getattr(self.cfg, "VOICE_CHAT_POLL_MS", 800)
        try:
            value = int(value)
        except Exception:
            value = 800
        if value <= 0:
            value = 800
        return value

    def _history_limit(self, history_limit):
        value = history_limit
        if value in (None, ""):
            value = getattr(self.cfg, "VOICE_CHAT_HISTORY_LIMIT", 12)
        try:
            value = int(value)
        except Exception:
            value = 12
        if value <= 0:
            value = 12
        return value

    def _operator_auth_token(self):
        token = _string(getattr(self.cfg, "VOICE_OPERATOR_AUTH_TOKEN", "")).strip()
        if token:
            return token
        if self._bool_value(getattr(self.cfg, "VOICE_OPERATOR_REUSE_NODE_TOKEN", False), False):
            return _string(getattr(self.cfg, "OPENCLAW_AUTH_TOKEN", "")).strip()
        return ""

    def _operator_client_id(self):
        return _string(getattr(self.cfg, "VOICE_OPERATOR_CLIENT_ID", "cli")).strip() or "cli"

    def _operator_client_mode(self):
        return _string(getattr(self.cfg, "VOICE_OPERATOR_CLIENT_MODE", "cli")).strip() or "cli"

    def _operator_role(self):
        return _string(getattr(self.cfg, "VOICE_OPERATOR_ROLE", "operator")).strip() or "operator"

    def _operator_scopes(self):
        return _normalize_scopes(getattr(self.cfg, "VOICE_OPERATOR_SCOPES", []))

    def _operator_logical_device_id(self):
        return _string(getattr(self.state, "logical_device_id", "")).strip() or _string(getattr(self.cfg, "DEVICE_ID", "")).strip()

    def _operator_device_id(self):
        return _string(self.state.node_id or getattr(self.cfg, "DEVICE_ID", "")).strip() or _string(getattr(self.cfg, "DEVICE_ID", "")).strip()

    def _resolve_connect_security_locked(self, token, nonce):
        auth = {"token": token}
        device = None
        device_auth_mode = _string(getattr(self.cfg, "VOICE_OPERATOR_DEVICE_AUTH_MODE", "")).strip()
        if not device_auth_mode:
            device_auth_mode = _string(getattr(self.cfg, "OPENCLAW_DEVICE_AUTH_MODE", "none")).strip() or "none"
        if device_auth_mode == "remote_signer_http":
            device = _request_remote_signature(
                self.cfg,
                self.state,
                token,
                nonce,
                client_id=self._operator_client_id(),
                client_mode=self._operator_client_mode(),
                role=self._operator_role(),
                scopes=self._operator_scopes(),
                logical_device_id=self._operator_logical_device_id(),
                device_name=_string(getattr(self.cfg, "DEVICE_NAME", "")).strip(),
            )
        elif device_auth_mode != "none":
            self._fail_locked("VOICE_CONFIG_ERROR", "unsupported voice device auth mode: " + device_auth_mode, False)
        return auth, device

    def _build_connect_params_locked(self, auth, device):
        client_id = self._operator_client_id()
        display_name = _string(getattr(self.cfg, "VOICE_OPERATOR_CLIENT_DISPLAY_NAME", "qpyclaw Voice Operator")).strip() or "qpyclaw Voice Operator"
        client_mode = self._operator_client_mode()
        role = self._operator_role()
        params = {
            "minProtocol": int(getattr(self.cfg, "OPENCLAW_MIN_PROTOCOL", 3)),
            "maxProtocol": int(getattr(self.cfg, "OPENCLAW_MAX_PROTOCOL", 3)),
            "client": {
                "id": client_id,
                "displayName": display_name,
                "version": _string(getattr(self.cfg, "FW_VERSION", "0.1.0")).strip() or "0.1.0",
                "platform": _string(getattr(self.cfg, "OPENCLAW_CLIENT_PLATFORM", "quectel")).strip() or "quectel",
                "deviceFamily": _string(getattr(self.cfg, "OPENCLAW_CLIENT_DEVICE_FAMILY", "quecpython")).strip() or "quecpython",
                "mode": client_mode,
            },
            "role": role,
            "scopes": self._operator_scopes(),
            "caps": list(getattr(self.cfg, "VOICE_OPERATOR_CAPS", []) or []),
            "commands": list(getattr(self.cfg, "VOICE_OPERATOR_COMMANDS", []) or []),
            "permissions": getattr(self.cfg, "VOICE_OPERATOR_PERMISSIONS", {}),
            "userAgent": _string(getattr(self.cfg, "VOICE_OPERATOR_USER_AGENT", "qpyclaw-node/0.1.0 voice")).strip() or "qpyclaw-node/0.1.0 voice",
            "device": device or {
                "id": self._operator_device_id(),
            },
        }
        if auth:
            params["auth"] = auth
        return params

    def _next_id_locked(self, prefix):
        self._seq += 1
        return str(prefix) + "_" + str(utime.ticks_ms()) + "_" + str(self._seq)

    def _close_locked(self, reason):
        self.last_close_reason = _string(reason).strip()
        self.last_close_ms = utime.ticks_ms()
        if self.online:
            self.last_disconnect_ms = self.last_close_ms
        self.online = False
        self.connected_at_ms = 0
        self.server_methods = []
        self.subscriptions = {}
        self.last_server_hello = None
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None

    def close(self, reason="manual-close"):
        self._acquire()
        try:
            self._close_locked(reason)
            return True
        finally:
            self._release()

    def _recv_frame_locked(self, timeout_ms):
        if self.ws is None:
            raise WsClosed("voice websocket closed")
        text = self.ws.recv_text(timeout_ms)
        return loads(text)

    def _send_frame_locked(self, frame):
        if self.ws is None:
            raise WsClosed("voice websocket closed")
        self.ws.send_text(dumps(frame))

    def _await_response_locked(self, request_id, timeout_ms):
        deadline = utime.ticks_add(utime.ticks_ms(), int(timeout_ms))
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            remaining = utime.ticks_diff(deadline, utime.ticks_ms())
            frame = self._recv_frame_locked(remaining)
            if not isinstance(frame, dict):
                continue
            if frame.get("type") == "res" and frame.get("id") == request_id:
                return frame
            self._handle_async_frame_locked(frame, "", "")
        raise Exception("voice ack timeout")

    def _request_locked(self, method, params, timeout_ms):
        request_id = self._next_id_locked(method)
        frame = {
            "type": "req",
            "id": request_id,
            "method": method,
            "params": params,
        }
        self._send_frame_locked(frame)
        return self._await_response_locked(request_id, timeout_ms)

    def _wait_connect_challenge_locked(self):
        deadline = utime.ticks_add(utime.ticks_ms(), int(self._connect_timeout_sec() * 1000))
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            remaining = utime.ticks_diff(deadline, utime.ticks_ms())
            frame = self._recv_frame_locked(remaining)
            if not isinstance(frame, dict):
                continue
            if frame.get("type") == "event" and frame.get("event") == "connect.challenge":
                self.last_event = "connect.challenge"
                self.last_event_ms = utime.ticks_ms()
                return frame.get("payload") or {}
        raise Exception("voice connect challenge timeout")

    def _method_supported_locked(self, method):
        methods = self.server_methods
        if not isinstance(methods, list) or not methods:
            return True
        return method in methods

    def _ensure_connected_locked(self):
        if not self._bool_value(getattr(self.cfg, "VOICE_ENABLED", False), False):
            self._fail_locked("VOICE_DISABLED", "voice dialog is disabled", False)
        if self.online and self.ws is not None:
            return True
        url = self._ws_url()
        if not url:
            self._fail_locked("VOICE_CONFIG_ERROR", "voice operator websocket url missing", False)
        token = self._operator_auth_token()
        if not token:
            self._fail_locked("VOICE_CONFIG_ERROR", "voice operator token missing", False)

        self._close_locked("reconnect")
        ws = WsClient()
        try:
            ws.connect(url, self._connect_timeout_sec())
            self.ws = ws
            challenge = self._wait_connect_challenge_locked()
            nonce = challenge.get("nonce") if isinstance(challenge, dict) else None
            if not nonce:
                self._fail_locked("VOICE_CONNECT_FAILED", "connect challenge missing nonce", True)
            auth, device = self._resolve_connect_security_locked(token, nonce)
            response = self._request_locked(
                "connect",
                self._build_connect_params_locked(auth, device),
                self._ack_timeout_ms(),
            )
            if not response.get("ok"):
                error = response.get("error") or {}
                code = error.get("code") if isinstance(error, dict) else "VOICE_CONNECT_FAILED"
                message = error.get("message") if isinstance(error, dict) else str(error)
                self._fail_locked(_string(code).strip() or "VOICE_CONNECT_FAILED", _string(message).strip() or "voice connect failed", True)
            payload = response.get("payload") or {}
            self.online = True
            self.connected_at_ms = utime.ticks_ms()
            self.last_connect_ms = self.connected_at_ms
            self.last_error = ""
            self.last_error_code = ""
            self.last_server_hello = payload
            features = payload.get("features") or {}
            methods = features.get("methods") if isinstance(features, dict) else None
            if isinstance(methods, list):
                self.server_methods = methods
            else:
                self.server_methods = []
            return True
        except Exception as e:
            if self.last_error_code == "":
                self.last_error_code = "VOICE_CONNECT_FAILED"
                self.last_error = str(e)
                self.last_error_ms = utime.ticks_ms()
            self._close_locked("connect-failed")
            raise

    def _subscribe_locked(self, session_key):
        if session_key in self.subscriptions:
            return {
                "ok": True,
                "session_key": session_key,
                "status": "cached",
            }
        if not self._method_supported_locked("chat.subscribe"):
            return {
                "ok": False,
                "session_key": session_key,
                "status": "unsupported",
            }
        try:
            response = self._request_locked(
                "chat.subscribe",
                {"sessionKey": session_key},
                self._ack_timeout_ms(),
            )
            if bool(response.get("ok")):
                self.subscriptions[session_key] = utime.ticks_ms()
                self.last_subscribe_error = ""
                return {
                    "ok": True,
                    "session_key": session_key,
                    "status": "subscribed",
                    "payload": response.get("payload") or {},
                }
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_SUBSCRIBE_FAILED"
            message = error.get("message") if isinstance(error, dict) else str(error)
            self.last_subscribe_error = (_string(code).strip() or "CHAT_SUBSCRIBE_FAILED") + ": " + (_string(message).strip() or "subscribe failed")
            return {
                "ok": False,
                "session_key": session_key,
                "status": "failed",
                "error": self.last_subscribe_error,
            }
        except Exception as e:
            self.last_subscribe_error = str(e)
            return {
                "ok": False,
                "session_key": session_key,
                "status": "failed",
                "error": str(e),
            }

    def _history_locked(self, session_key, history_limit):
        if not self._method_supported_locked("chat.history"):
            self._fail_locked("VOICE_UNSUPPORTED", "chat.history not supported by gateway", False)
        params = {
            "sessionKey": session_key,
            "limit": int(history_limit),
        }
        response = self._request_locked("chat.history", params, self._ack_timeout_ms())
        if not response.get("ok"):
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_HISTORY_FAILED"
            message = error.get("message") if isinstance(error, dict) else str(error)
            self._fail_locked(_string(code).strip() or "CHAT_HISTORY_FAILED", _string(message).strip() or "chat history failed", False)
        payload = response.get("payload") or {}
        self.last_history_count = len(self._extract_history_messages_locked(payload))
        self.last_history_poll_ms = utime.ticks_ms()
        return payload

    def _send_chat_locked(self, message, session_key, idempotency_key):
        if not self._method_supported_locked("chat.send"):
            self._fail_locked("VOICE_UNSUPPORTED", "chat.send not supported by gateway", False)
        params = {
            "sessionKey": session_key,
            "message": message,
        }
        if idempotency_key:
            params["idempotencyKey"] = idempotency_key
        response = self._request_locked("chat.send", params, self._ack_timeout_ms())
        if not response.get("ok"):
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_SEND_FAILED"
            message_text = error.get("message") if isinstance(error, dict) else str(error)
            self._fail_locked(_string(code).strip() or "CHAT_SEND_FAILED", _string(message_text).strip() or "chat send failed", False)
        payload = response.get("payload") or {}
        self.last_run_id = _string(payload.get("runId")).strip()
        self.last_chat_status = _string(payload.get("status")).strip()
        self.last_sent_message = message
        self.last_sent_session_key = session_key
        self.last_turn_id = idempotency_key
        return payload

    def _abort_locked(self, session_key):
        if not self._method_supported_locked("chat.abort"):
            self._fail_locked("VOICE_UNSUPPORTED", "chat.abort not supported by gateway", False)
        response = self._request_locked(
            "chat.abort",
            {"sessionKey": session_key},
            self._ack_timeout_ms(),
        )
        if not response.get("ok"):
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_ABORT_FAILED"
            message = error.get("message") if isinstance(error, dict) else str(error)
            self._fail_locked(_string(code).strip() or "CHAT_ABORT_FAILED", _string(message).strip() or "chat abort failed", False)
        self.last_chat_status = "aborted"
        return response.get("payload") or {}

    def _event_matches_locked(self, payload, session_key, run_id):
        if not isinstance(payload, dict):
            return True
        session_value = payload.get("sessionKey")
        if session_value in (None, ""):
            session_value = payload.get("session_key")
        if session_value not in (None, "") and session_key and _string(session_value).strip() != session_key:
            return False
        run_value = payload.get("runId")
        if run_value in (None, ""):
            run_value = payload.get("run_id")
        if run_value not in (None, "") and run_id and _string(run_value).strip() != run_id:
            return False
        nested = payload.get("message")
        if nested is None:
            nested = payload.get("data")
        if nested is None:
            nested = payload.get("chat")
        if isinstance(nested, dict):
            return self._event_matches_locked(nested, session_key, run_id)
        return True

    def _handle_async_frame_locked(self, frame, session_key, run_id):
        if not isinstance(frame, dict):
            return False
        frame_type = frame.get("type")
        if frame_type == "event":
            event_name = _string(frame.get("event")).strip()
            self.last_event = event_name
            self.last_event_ms = utime.ticks_ms()
            if event_name == "chat":
                payload = frame.get("payload") or {}
                return self._event_matches_locked(payload, session_key, run_id)
        return False

    def _extract_history_messages_locked(self, payload):
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ("messages", "items", "history", "entries", "rows", "timeline"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for key in ("data", "session", "chat", "result", "payload"):
            value = payload.get(key)
            if isinstance(value, dict):
                items = self._extract_history_messages_locked(value)
                if items:
                    return items
        return []

    def _collect_text_locked(self, value, depth):
        if depth > 3 or value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, list):
            parts = []
            for item in value:
                text = self._collect_text_locked(item, depth + 1)
                text = _string(text).strip()
                if text:
                    parts.append(text)
            return "\n".join(parts)
        if isinstance(value, dict):
            for key in ("text", "message", "markdown", "body", "value", "contentText", "outputText"):
                if key in value:
                    text = self._collect_text_locked(value.get(key), depth + 1)
                    if _string(text).strip():
                        return text
            for key in ("content", "parts", "segments", "items"):
                if key in value:
                    text = self._collect_text_locked(value.get(key), depth + 1)
                    if _string(text).strip():
                        return text
        return ""

    def _message_role_locked(self, item):
        if not isinstance(item, dict):
            return ""
        for key in ("role", "authorRole", "senderRole", "messageRole"):
            value = item.get(key)
            if value not in (None, ""):
                return _string(value).strip().lower()
        for key in ("author", "sender", "meta"):
            value = item.get(key)
            if isinstance(value, dict):
                role = self._message_role_locked(value)
                if role:
                    return role
        return ""

    def _message_text_locked(self, item):
        if not isinstance(item, dict):
            return _string(item).strip()
        for key in ("text", "message", "content", "body", "value", "outputText"):
            if key in item:
                text = self._collect_text_locked(item.get(key), 0)
                if _string(text).strip():
                    return _string(text).strip()
        return ""

    def _message_id_locked(self, item):
        if not isinstance(item, dict):
            return ""
        for key in ("id", "messageId", "cid", "uuid"):
            value = item.get(key)
            if value not in (None, ""):
                return _string(value).strip()
        return ""

    def _message_fingerprint_locked(self, item):
        message_id = self._message_id_locked(item)
        text = self._message_text_locked(item)
        if len(text) > 160:
            text = text[:160]
        if message_id:
            return message_id + "|" + text
        role = self._message_role_locked(item)
        timestamp = ""
        if isinstance(item, dict):
            for key in ("ts", "createdAt", "createdAtMs", "timestamp", "time"):
                value = item.get(key)
                if value not in (None, ""):
                    timestamp = _string(value).strip()
                    break
        return role + "|" + timestamp + "|" + text

    def _assistant_role_locked(self, role):
        role_text = _string(role).strip().lower()
        return role_text in ("assistant", "agent", "model")

    def _text_lines_locked(self, text):
        raw = _string(text)
        if not raw:
            return []
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.split("\n")

    def _strip_voice_directive_locked(self, text):
        reply_text = _string(text)
        directive = {}
        lines = self._text_lines_locked(reply_text)
        first_index = -1
        index = 0
        while index < len(lines):
            if _string(lines[index]).strip():
                first_index = index
                break
            index += 1
        if first_index >= 0:
            first_line = _string(lines[first_index]).strip()
            if first_line[:1] == "{" and first_line[-1:] == "}":
                try:
                    maybe = loads(first_line)
                    if isinstance(maybe, dict):
                        directive = maybe
                        lines.pop(first_index)
                        reply_text = "\n".join(lines).strip()
                except Exception:
                    pass
        return reply_text, directive

    def _find_reply_locked(self, payload, seen):
        messages = self._extract_history_messages_locked(payload)
        self.last_history_count = len(messages)
        candidate = None
        for item in messages:
            fingerprint = self._message_fingerprint_locked(item)
            if fingerprint in seen:
                continue
            seen[fingerprint] = True
            text = self._message_text_locked(item)
            role = self._message_role_locked(item)
            if text and self._assistant_role_locked(role):
                candidate = {
                    "fingerprint": fingerprint,
                    "message_id": self._message_id_locked(item),
                    "role": role,
                    "text": text,
                    "raw": item,
                }
        return candidate

    def snapshot(self):
        self._acquire()
        try:
            return {
                "enabled": bool(getattr(self.cfg, "VOICE_ENABLED", False)),
                "online": self.online,
                "connected_at_ms": self.connected_at_ms,
                "last_connect_ms": self.last_connect_ms,
                "last_disconnect_ms": self.last_disconnect_ms,
                "last_close_reason": self.last_close_reason,
                "last_close_ms": self.last_close_ms,
                "last_error_code": self.last_error_code,
                "last_error": self.last_error,
                "last_error_ms": self.last_error_ms,
                "last_event": self.last_event,
                "last_event_ms": self.last_event_ms,
                "last_run_id": self.last_run_id,
                "last_turn_id": self.last_turn_id,
                "last_sent_session_key": self.last_sent_session_key,
                "last_reply_text": self.last_reply_text,
                "last_reply_message_id": self.last_reply_message_id,
                "last_voice_directive": self.last_voice_directive,
                "last_history_count": self.last_history_count,
                "last_chat_status": self.last_chat_status,
                "last_history_poll_ms": self.last_history_poll_ms,
                "last_subscribe_error": self.last_subscribe_error,
                "last_chat_duration_ms": self.last_chat_duration_ms,
                "last_chat_event_count": self.last_chat_event_count,
                "last_chat_history_polls": self.last_chat_history_polls,
                "main_session_key": self._session_key(""),
                "operator_ws_url": self._ws_url(),
                "operator_role": _string(getattr(self.cfg, "VOICE_OPERATOR_ROLE", "operator")).strip() or "operator",
                "operator_scopes": _normalize_scopes(getattr(self.cfg, "VOICE_OPERATOR_SCOPES", [])),
                "subscriptions": [name for name in self.subscriptions.keys()],
                "server_methods": self.server_methods,
            }
        finally:
            self._release()

    def chat(self, message, session_key="", timeout_ms=None, idempotency_key="", subscribe=None, history_limit=None):
        self._acquire()
        try:
            message_text = _string(message).strip()
            if not message_text:
                self._fail_locked("CHAT_SEND_FAILED", "message required", False)
            session_key_text = self._session_key(session_key)
            timeout_value = self._chat_timeout_ms(timeout_ms)
            poll_ms = self._chat_poll_ms()
            history_limit_value = self._history_limit(history_limit)
            subscribe_enabled = self._bool_value(subscribe, getattr(self.cfg, "VOICE_CHAT_SUBSCRIBE", True))
            turn_id = _string(idempotency_key).strip()
            if not turn_id:
                turn_id = self._next_id_locked("voice_turn")
            started = utime.ticks_ms()

            self._ensure_connected_locked()
            baseline = {}
            baseline_payload = self._history_locked(session_key_text, history_limit_value)
            baseline_messages = self._extract_history_messages_locked(baseline_payload)
            index = 0
            while index < len(baseline_messages):
                baseline[self._message_fingerprint_locked(baseline_messages[index])] = True
                index += 1

            subscribe_result = None
            if subscribe_enabled:
                subscribe_result = self._subscribe_locked(session_key_text)

            send_payload = self._send_chat_locked(message_text, session_key_text, turn_id)
            run_id = _string(send_payload.get("runId")).strip()
            history_polls = 0
            chat_events = 0
            deadline = utime.ticks_add(utime.ticks_ms(), timeout_value)

            while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
                remaining = utime.ticks_diff(deadline, utime.ticks_ms())
                wait_ms = remaining
                if wait_ms > poll_ms:
                    wait_ms = poll_ms
                if wait_ms <= 0:
                    wait_ms = 1
                try:
                    frame = self._recv_frame_locked(wait_ms)
                    if self._handle_async_frame_locked(frame, session_key_text, run_id):
                        chat_events += 1
                except WsTimeout:
                    pass
                payload = self._history_locked(session_key_text, history_limit_value)
                history_polls += 1
                candidate = self._find_reply_locked(payload, baseline)
                if candidate is not None:
                    reply_text, directive = self._strip_voice_directive_locked(candidate.get("text"))
                    self.last_reply_text = reply_text
                    self.last_reply_message_id = candidate.get("message_id") or ""
                    self.last_voice_directive = directive
                    self.last_chat_status = "ok"
                    self.last_chat_duration_ms = utime.ticks_diff(utime.ticks_ms(), started)
                    self.last_chat_event_count = chat_events
                    self.last_chat_history_polls = history_polls
                    return {
                        "ok": True,
                        "status": "ok",
                        "session_key": session_key_text,
                        "turn_id": turn_id,
                        "run_id": run_id,
                        "reply_text": reply_text,
                        "voice_directive": directive,
                        "assistant_message_id": self.last_reply_message_id,
                        "chat_events": chat_events,
                        "history_polls": history_polls,
                        "duration_ms": self.last_chat_duration_ms,
                        "subscribe": subscribe_result,
                    }

            self.last_chat_status = "timeout"
            self.last_chat_duration_ms = utime.ticks_diff(utime.ticks_ms(), started)
            self.last_chat_event_count = chat_events
            self.last_chat_history_polls = history_polls
            self._fail_locked("CHAT_TIMEOUT", "chat reply not received before timeout", False)
        finally:
            self._release()

    def abort(self, session_key=""):
        self._acquire()
        try:
            session_key_text = self._session_key(session_key)
            self._ensure_connected_locked()
            payload = self._abort_locked(session_key_text)
            return {
                "ok": True,
                "status": "aborted",
                "session_key": session_key_text,
                "run_id": self.last_run_id,
                "payload": payload,
            }
        finally:
            self._release()


class QpyClawNode(object):

    def __init__(self, cfg=None, extension=None):
        if cfg is None:
            cfg = config
        self.extension = extension
        _apply_extension_cfg(cfg, extension)
        self.cfg = cfg
        self.state = RuntimeState(cfg)
        self.transport = _build_transport(cfg, self.state)
        self.runner = ToolRunner(cfg, self.state, extension)
        self.worker = CommandWorker(self.runner, self.state)
        self.network = CellularNetworkManager(cfg, self.state)
        self.voice = VoiceDialogClient(cfg, self.state)
        self.network.attach_runtime(self)
        self.boot_event_queued = False
        self._last_online = None
        self._extension_call("on_runtime_created", self)

    def _extension_call(self, method, *args):
        if self.extension is None or not hasattr(self.extension, method):
            return None
        try:
            return getattr(self.extension, method)(*args)
        except Exception as e:
            global _LAST_EXCEPTION
            _LAST_EXCEPTION = str(e)
            self.state.note_error("BOARD_EXTENSION_ERROR", method + ": " + str(e))
            return None

    def _after_step(self):
        online = bool(getattr(self.transport, "online", False))
        if self._last_online is None or online != self._last_online:
            self._last_online = online
            self._extension_call("on_online_changed", self, online)
        self._extension_call("after_step", self)

    def queue_boot_event(self):
        if not self.boot_event_queued:
            self.transport.queue_boot_event()
            self.boot_event_queued = True

    def execute_local(self, tool, args=None, request_id=""):
        if args is None:
            args = {}
        if not request_id:
            request_id = "local-" + str(utime.ticks_ms())
        self.state.note_inflight_start(request_id, tool)
        result = self.runner.execute({
            "request_id": request_id,
            "tool": tool,
            "args": args,
        })
        self.state.note_inflight_finish(result.get("status"), result.get("result_code"))
        return result

    def schedule_reboot(self, mode, delay_ms=None):
        if not mode:
            mode = "soft"
        if delay_ms is None:
            delay_ms = int(getattr(self.cfg, "REBOOT_RESULT_DELAY_MS", 1500))
        self.state.request_reboot(mode, int(delay_ms))
        return {
            "scheduled": True,
            "mode": mode,
            "delay_ms": int(delay_ms),
            "pending": bool(self.state.pending_reboot_mode),
        }

    def close(self, reason):
        if self.voice is not None:
            try:
                self.voice.close(reason or "manual-close")
            except Exception:
                pass
        self.transport.close(reason or "manual-close")

    def debug_snapshot(self):
        state_snapshot = None
        extension_snapshot = None
        try:
            state_snapshot = self.state.snapshot()
        except Exception:
            state_snapshot = None
        if self.extension is not None and hasattr(self.extension, "snapshot"):
            try:
                extension_snapshot = self.extension.snapshot()
            except Exception:
                extension_snapshot = None
        return {
            "has_runtime": True,
            "has_state": self.state is not None,
            "has_transport": self.transport is not None,
            "has_runner": self.runner is not None,
            "has_worker": self.worker is not None,
            "has_network_manager": self.network is not None,
            "has_voice": self.voice is not None,
            "boot_event_queued": bool(self.boot_event_queued),
            "online": bool(getattr(self.transport, "online", False)),
            "has_extension": self.extension is not None,
            "extension_name": self.extension.__class__.__name__ if self.extension is not None else "",
            "extension": extension_snapshot,
            "network": self.network.snapshot() if self.network is not None else None,
            "voice": self.voice.snapshot() if self.voice is not None else None,
            "last_exception": _LAST_EXCEPTION,
            "state": state_snapshot,
        }

    def step(self):
        self.queue_boot_event()
        try:
            if self.network is not None:
                self.network.poll()
            if not self.transport.online:
                if self.network is not None:
                    ready = self.network.ensure_ready("transport.connect")
                    if not ready:
                        self._after_step()
                        cooldown = self.cfg.RECONNECT_BACKOFF_SEC
                        if self.state.safe_mode:
                            cooldown = int(getattr(self.cfg, "SAFE_MODE_COOLDOWN_SEC", cooldown))
                        utime.sleep(cooldown)
                        return False
                ok = self.transport.connect()
                if not ok:
                    self._after_step()
                    cooldown = self.cfg.RECONNECT_BACKOFF_SEC
                    if self.state.safe_mode:
                        cooldown = int(getattr(self.cfg, "SAFE_MODE_COOLDOWN_SEC", cooldown))
                    utime.sleep(cooldown)
                    return False

            self.transport.tick()

            if self.worker.available:
                done = self.worker.poll_result()
                if done:
                    self.transport.send_result(done.get("cmd") or {}, done.get("result") or {})

                if self.worker.can_accept():
                    cmd = self.transport.recv_cmd(int(getattr(self.cfg, "READ_POLL_MS", 200)), True)
                    if cmd:
                        if not self.worker.submit(cmd):
                            self.state.note_inflight_start(cmd.get("request_id"), cmd.get("tool"))
                            result = self.runner.execute(cmd)
                            self.state.note_inflight_finish(result.get("status"), result.get("result_code"))
                            self.transport.send_result(cmd, result)
                else:
                    self.transport.recv_cmd(int(getattr(self.cfg, "READ_POLL_MS", 200)), False)
            else:
                cmd = self.transport.recv_cmd(int(getattr(self.cfg, "READ_POLL_MS", 200)), True)
                if cmd:
                    self.state.note_inflight_start(cmd.get("request_id"), cmd.get("tool"))
                    result = self.runner.execute(cmd)
                    self.state.note_inflight_finish(result.get("status"), result.get("result_code"))
                    self.transport.send_result(cmd, result)

            if self.network is not None:
                self.network.poll()
            perform_pending_reboot(self.state)
            self._after_step()
            return True

        except WsClosed as e:
            global _LAST_EXCEPTION
            _LAST_EXCEPTION = str(e)
            self.state.note_error("TRANSPORT_DISCONNECTED", str(e))
            self.transport.close("reconnect")
            self._after_step()
            utime.sleep(self.cfg.RECONNECT_BACKOFF_SEC)
            return False

        except Exception as e:
            _LAST_EXCEPTION = str(e)
            self.state.note_error("RUNTIME_LOOP_ERROR", str(e))
            self._extension_call("on_runtime_error", self, str(e))
            self.transport.close("loop-error")
            self._after_step()
            utime.sleep(self.cfg.RECONNECT_BACKOFF_SEC)
            return False

    def run_forever(self):
        while True:
            self.step()


def _remember_runtime(node):
    global _LAST_NODE
    global _LAST_EXCEPTION
    _LAST_NODE = node
    _LAST_EXCEPTION = ""
    return node


def get_runtime():
    return _LAST_NODE


def create_runtime(cfg=None, extension=None):
    return _remember_runtime(QpyClawNode(cfg, extension))


def queue_boot_event(runtime=None):
    node = runtime or _LAST_NODE
    if node is None:
        node = create_runtime()
    node.queue_boot_event()
    return True


def execute_local(tool, args=None, request_id="", runtime=None):
    node = runtime or _LAST_NODE
    if node is None:
        node = create_runtime()
    return node.execute_local(tool, args, request_id)


def voice_status(runtime=None):
    node = runtime or _LAST_NODE
    if node is None:
        node = create_runtime()
    if not hasattr(node, "voice") or node.voice is None:
        return {"available": False}
    return node.voice.snapshot()


def voice_chat(message, session_key="", timeout_ms=None, idempotency_key="", subscribe=None, history_limit=None, runtime=None):
    node = runtime or _LAST_NODE
    if node is None:
        node = create_runtime()
    if not hasattr(node, "voice") or node.voice is None:
        raise Exception("voice runtime unavailable")
    return node.voice.chat(
        message,
        session_key=session_key,
        timeout_ms=timeout_ms,
        idempotency_key=idempotency_key,
        subscribe=subscribe,
        history_limit=history_limit,
    )


def voice_abort(session_key="", runtime=None):
    node = runtime or _LAST_NODE
    if node is None:
        node = create_runtime()
    if not hasattr(node, "voice") or node.voice is None:
        raise Exception("voice runtime unavailable")
    return node.voice.abort(session_key=session_key)


def schedule_reboot(mode="soft", delay_ms=None, runtime=None):
    node = runtime or _LAST_NODE
    if node is None:
        node = create_runtime()
    return node.schedule_reboot(mode, delay_ms)


def debug_snapshot():
    node = _LAST_NODE
    if node is None:
        return {
            "has_runtime": False,
            "has_state": False,
            "has_transport": False,
            "has_runner": False,
            "has_worker": False,
            "boot_event_queued": False,
            "online": False,
            "last_exception": _LAST_EXCEPTION,
            "state": None,
        }
    return node.debug_snapshot()


def run(cfg=None, extension=None):
    node = create_runtime(cfg, extension)
    node.run_forever()
