# qpyclaw_node.py — Slim orchestrator for qpyclaw-node.
# Imports config, transport, tools, voice, cellular from extracted modules.
# Contains RuntimeState, QpyClawNode, reboot helpers, and public API.

from config import config
import utime

from ws_client import WsClosed
from transport import build_transport, apply_extension_cfg
from tools import ToolRunner, CommandWorker, build_runtime_telemetry, set_runtime_provider
from voice import VoiceDialogClient
from cellular import CellularNetworkManager, safe_import, safe_call, quick_network_status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# RuntimeState
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Reboot helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Global runtime singleton
# ---------------------------------------------------------------------------

_LAST_NODE = None
_LAST_EXCEPTION = ""


# ---------------------------------------------------------------------------
# QpyClawNode — main orchestrator
# ---------------------------------------------------------------------------

class QpyClawNode(object):

    def __init__(self, cfg=None, extension=None):
        if cfg is None:
            cfg = config
        self.extension = extension
        apply_extension_cfg(cfg, extension)
        self.cfg = cfg
        self.state = RuntimeState(cfg)
        self.transport = build_transport(cfg, self.state)
        self.transport.set_telemetry_provider(lambda: build_runtime_telemetry(cfg, self.state))
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _remember_runtime(node):
    global _LAST_NODE
    global _LAST_EXCEPTION
    _LAST_NODE = node
    _LAST_EXCEPTION = ""
    set_runtime_provider(get_runtime)
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
