# tools.py — Tool system for qpyclaw-node.
# Contains tool classes, ToolRunner (lazy-loading), CommandWorker, and FS utils.

import utime

try:
    import _thread
except Exception:
    _thread = None

try:
    import ubinascii
except Exception:
    ubinascii = None

from cellular import (
    safe_import, safe_call, ok_value, mask_value, wall_time_ms,
    measure_step, safe_attr_call,
    gather_modem_info, gather_sim_info, gather_network_info,
    gather_data_context, gather_cell_info,
)


# ---------------------------------------------------------------------------
# Module-level runtime provider (set by orchestrator to break circular dep)
# ---------------------------------------------------------------------------

_runtime_provider = None


def set_runtime_provider(fn):
    global _runtime_provider
    _runtime_provider = fn


def get_runtime():
    if _runtime_provider is not None:
        return _runtime_provider()
    return None


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _string(value):
    if value is None:
        return ""
    return str(value)


def _stringify(value):
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


def _sleep_ms(delay_ms):
    if delay_ms <= 0:
        delay_ms = 1
    if hasattr(utime, "sleep_ms"):
        utime.sleep_ms(delay_ms)
        return
    utime.sleep(float(delay_ms) / 1000.0)


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Runtime/telemetry info builders
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# REPL builtins resolver
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tool classes
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# _ExternalTool wrapper
# ---------------------------------------------------------------------------

class _ExternalTool(object):

    def __init__(self, executor):
        self.executor = executor

    def execute(self, args):
        return self.executor(args)


# ---------------------------------------------------------------------------
# ToolRunner — lazy-loading tool registry
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# CommandWorker — async tool execution on a background thread
# ---------------------------------------------------------------------------

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

            exec_started = utime.ticks_ms()
            try:
                result = self.runner.execute(cmd)
            except Exception as e:
                self.state.note_error("WORKER_EXEC_FAILED", str(e))
                result = self._build_worker_error(cmd, str(e))

            elapsed_ms = utime.ticks_diff(utime.ticks_ms(), exec_started)
            max_ms = int(getattr(self.runner.cfg, "MAX_CMD_EXEC_SEC", 30)) * 1000
            if elapsed_ms > max_ms:
                self.state.note_error(
                    "WORKER_EXEC_TIMEOUT",
                    str(cmd.get("tool") or "unknown") + " took " + str(elapsed_ms) + "ms",
                )

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
