import utime

from board_display import BoardDisplay
from board_ui import BoardAiriUi


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _recent_ms(now_ms, source_ms, window_ms):
    try:
        source = int(source_ms or 0)
        window = int(window_ms or 0)
    except Exception:
        return False
    if source <= 0 or window <= 0:
        return False
    try:
        return utime.ticks_diff(now_ms, source) <= window
    except Exception:
        return False


def _limit_text(value, limit):
    text = _string(value).replace("\r", "\n")
    rows = []
    for row in text.split("\n"):
        item = row.strip()
        if item:
            rows.append(item)
    text = " ".join(rows).strip()
    if limit and len(text) > limit:
        text = text[: max(0, int(limit) - 3)].rstrip() + "..."
    return text


def _safe_int(value, default_value=0):
    try:
        if value in (None, ""):
            return int(default_value)
        return int(value)
    except Exception:
        return int(default_value)


def _is_ui_control_tool(tool_name):
    text = _string(tool_name).strip().lower()
    if not text:
        return False
    rows = (
        "qpy.ui.",
        "qpy.display.",
        "qpy.board.",
        "ui.",
        "display.",
        "board.",
    )
    index = 0
    while index < len(rows):
        if text.startswith(rows[index]):
            return True
        index += 1
    return False


def _build_ui_state(phase, mode_key, mood, status, message, footer):
    mode_text = _string(mode_key).strip().lower() or "idle"
    mood_text = _string(mood).strip() or "neutral"
    status_text = _limit_text(status, 96) or "AIRI is holding the screen."
    message_text = _limit_text(message, 140) or "AIRI is visible on the board."
    footer_text = _limit_text(footer, 128) or "The board state is being held on screen."
    return {
        "phase": _string(phase).strip().lower() or "boot",
        "mode_key": mode_text,
        "mood": mood_text,
        "status": status_text,
        "message": message_text,
        "footer": footer_text,
        "signature": "|".join((mode_text, mood_text, status_text, message_text, footer_text)),
    }


def _boot_ui_state(node_id):
    node_name = _string(node_id).strip() or "qpyclaw-node"
    return _build_ui_state(
        "boot",
        "idle",
        "wake",
        "AIRI is preparing the runtime.",
        "qpyclaw-node is starting on the board now.",
        "The display and %s runtime are settling before network checks begin." % node_name,
    )


class U235EC600UAiriBoard(object):

    def __init__(self, display=None, ui=None):
        if display is None:
            display = BoardDisplay()
        if ui is None:
            ui = BoardAiriUi(display)
        self.display = display
        self.ui = ui
        self.runtime = None

    def boot_minimal(self, enable_display=True):
        if enable_display and self.display.supported:
            self.display.ensure_ready()
            self.ui.ensure_ready()
            self.display.start_auto_pump(16)
            boot_state = _boot_ui_state("qpyclaw-node")
            self.ui.render_runtime_state(
                boot_state.get("mode_key"),
                boot_state.get("status"),
                boot_state.get("message"),
                boot_state.get("footer"),
                mood=boot_state.get("mood"),
            )
        return self.snapshot()

    def attach_runtime(self, runtime):
        self.runtime = runtime
        return True

    def tick(self):
        return self.ui.tick()

    def snapshot(self):
        return {
            "display": self.display.snapshot(),
            "ui": self.ui.snapshot(),
            "runtime_attached": bool(self.runtime is not None),
        }


def create_default_board():
    display = BoardDisplay()
    ui = BoardAiriUi(display)
    return U235EC600UAiriBoard(display=display, ui=ui)


class U235EC600UAiriBoardExtension(object):

    def __init__(
        self,
        board=None,
        enable_display=True,
        enable_charge=False,
        open_audio=False,
        enable_voice=False,
        voice_auto_start=False,
        **kwargs
    ):
        if board is None:
            board = create_default_board()
        self.board = board
        self.enable_display = bool(enable_display)
        self.enable_charge = bool(enable_charge)
        self.open_audio = bool(open_audio)
        self.enable_voice = bool(enable_voice)
        self.voice_auto_start = bool(voice_auto_start)
        self.extra_options = kwargs or {}
        self._bootstrapped = False
        self._last_render_signature = ""
        self._last_ui_state = {}
        self._last_ui_phase = ""
        self._last_ui_reason = ""

    def get_caps(self):
        return ["display", "board-ui", "airi-ui"]

    def get_tool_specs(self):
        return [
            {
                "name": "qpy.board.status",
                "summary": "Return U235 EC600U AIRI board capability snapshot.",
                "aliases": ["board.status"],
                "category": "board",
                "read_only": True,
                "executor": self.execute_board_status,
            },
            {
                "name": "qpy.display.status",
                "summary": "Return local display-driver state for the AIRI board.",
                "aliases": ["display.status"],
                "category": "display",
                "read_only": True,
                "executor": self.execute_display_status,
            },
            {
                "name": "qpy.display.clear",
                "summary": "Fill the full panel with black and pause AIRI scene rendering.",
                "aliases": ["display.clear"],
                "category": "display",
                "read_only": False,
                "executor": self.execute_display_clear,
            },
            {
                "name": "qpy.display.fill",
                "summary": "Fill the full panel with a solid RGB565 color and pause AIRI scene rendering.",
                "aliases": ["display.fill"],
                "category": "display",
                "read_only": False,
                "executor": self.execute_display_fill,
            },
            {
                "name": "qpy.ui.status",
                "summary": "Return AIRI UI state and current mode.",
                "aliases": ["ui.status"],
                "category": "display",
                "read_only": True,
                "executor": self.execute_ui_status,
            },
            {
                "name": "qpy.ui.mode.catalog",
                "summary": "Return supported AIRI modes and emotion aliases.",
                "aliases": ["ui.mode.catalog", "ui.emotion.catalog"],
                "category": "display",
                "read_only": True,
                "executor": self.execute_ui_catalog,
            },
            {
                "name": "qpy.ui.mode.show",
                "summary": "Show an AIRI mode on the board screen.",
                "aliases": ["ui.mode.show", "ui.emotion.show"],
                "category": "display",
                "read_only": False,
                "executor": self.execute_ui_mode_show,
            },
            {
                "name": "qpy.ui.overlay.set",
                "summary": "Override AIRI status, message, and footer text on the board UI.",
                "aliases": ["ui.overlay.set", "ui.message.set"],
                "category": "display",
                "read_only": False,
                "executor": self.execute_ui_overlay_set,
            },
        ]

    def on_runtime_created(self, runtime):
        self.board.attach_runtime(runtime)
        if not self._bootstrapped:
            self.board.boot_minimal(enable_display=self.enable_display)
            boot_state = self._boot_ui_state_from_runtime(runtime)
            self._remember_ui_state(boot_state, "boot_minimal", True)
            self._bootstrapped = True
        return True

    def on_online_changed(self, runtime, online):
        _ = runtime
        _ = online
        return True

    def after_step(self, runtime):
        self._render_runtime_state(runtime)
        self.board.tick()
        return True

    def on_runtime_error(self, runtime, message):
        _ = runtime
        _ = message
        return True

    def _runtime_node_id(self, runtime):
        if runtime is None:
            return "qpyclaw-node"
        try:
            state = getattr(runtime, "state", None)
            if state is not None:
                node_id = _string(getattr(state, "node_id", "")).strip()
                if node_id:
                    return node_id
                node_id = _string(getattr(state, "logical_device_id", "")).strip()
                if node_id:
                    return node_id
        except Exception:
            pass
        return "qpyclaw-node"

    def _boot_ui_state_from_runtime(self, runtime):
        return _boot_ui_state(self._runtime_node_id(runtime))

    def _remember_ui_state(self, ui_state, reason, rendered=False):
        if not isinstance(ui_state, dict):
            ui_state = {}
        copied = {}
        for key in ui_state:
            copied[key] = ui_state[key]
        self._last_ui_state = copied
        self._last_ui_phase = _string(copied.get("phase")).strip().lower()
        self._last_ui_reason = _string(reason).strip()
        if rendered:
            self._last_render_signature = _string(copied.get("signature")).strip()

    def _command_active_state(self, state, now_ms):
        inflight_tool = _string(state.get("inflight_cmd_tool")).strip()
        last_tool = _string(state.get("last_business_cmd_tool")).strip()
        if not last_tool:
            last_tool = _string(state.get("last_cmd_tool")).strip()
        recent_cmd_ms = state.get("last_business_cmd_ms")
        if recent_cmd_ms in (None, "", 0):
            recent_cmd_ms = state.get("last_cmd_ms")
            if _is_ui_control_tool(last_tool):
                recent_cmd_ms = 0

        busy = bool(state.get("worker_busy")) or bool(state.get("inflight_cmd_id"))
        if busy:
            if not inflight_tool or (not _is_ui_control_tool(inflight_tool)):
                return True, inflight_tool or "runtime", "command_active:inflight"

        if _recent_ms(now_ms, recent_cmd_ms, 5000):
            if not last_tool or (not _is_ui_control_tool(last_tool)):
                return True, last_tool or "runtime", "command_active:recent"

        return False, "", ""

    def _network_wait_state(self, network):
        stage = _safe_int(network.get("last_stage"), -1)
        state = _safe_int(network.get("last_state"), -1)
        if stage == 1:
            return (
                _build_ui_state(
                    "network_wait",
                    "listen",
                    "confused",
                    "The module is still getting ready.",
                    "Waiting for SIM or modem readiness before the node can go online.",
                    "AIRI stays visible while the cellular stack finishes bootstrapping.",
                ),
                "network_wait:stage1",
            )
        if stage == 2:
            return (
                _build_ui_state(
                    "network_wait",
                    "listen",
                    "listen",
                    "The board is joining the cellular network.",
                    "The modem is registering on the carrier right now.",
                    "Gateway connection will start after cellular registration succeeds.",
                ),
                "network_wait:stage2",
            )
        if stage == 3 and state != 1:
            return (
                _build_ui_state(
                    "network_wait",
                    "listen",
                    "confused",
                    "The data link is not ready yet.",
                    "Cellular registration is up, but PDP or data context is still inactive.",
                    "AIRI holds the panel while the board recovers its data session.",
                ),
                "network_wait:stage3",
            )
        return (
            _build_ui_state(
                "network_wait",
                "listen",
                "confused",
                "The network stack is still settling.",
                "The board is waiting for the next usable network state.",
                "AIRI remains visible while connectivity is being recovered.",
            ),
            "network_wait:unknown",
        )

    def _normalize_runtime_ui_state(self, snapshot):
        state = snapshot.get("state") or {}
        network = snapshot.get("network") or {}
        voice = snapshot.get("voice") or {}
        online = bool(snapshot.get("online"))
        now_ms = utime.ticks_ms()
        error_text = _limit_text(state.get("last_error"), 110)
        error_code = _string(state.get("last_error_code")).strip()
        connect_attempts = _safe_int(state.get("connect_attempts"), 0)
        failures = _safe_int(state.get("consecutive_failures"), 0)
        node_id = _string(state.get("node_id")).strip() or _string(state.get("logical_device_id")).strip() or "qpyclaw-node"
        network_known = (
            _safe_int(network.get("last_check_ms"), 0) > 0
            or _safe_int(network.get("last_stage"), -1) >= 0
            or bool(_string(network.get("last_reason")).strip())
        )

        if error_text and _recent_ms(now_ms, state.get("last_error_ms"), 12000):
            footer = "AIRI stays on screen while the node recovers."
            if error_code:
                footer = "AIRI stays on screen while the node recovers from %s." % error_code
            return (
                _build_ui_state(
                    "runtime_error",
                    "listen",
                    "shocked",
                    "The runtime hit a recent error.",
                    error_text,
                    footer,
                ),
                "runtime_error",
            )

        if network_known and (not bool(network.get("last_ready"))):
            return self._network_wait_state(network)

        if bool(network.get("last_ready")) and (not online) and connect_attempts > 0:
            return (
                _build_ui_state(
                    "gateway_reconnect",
                    "listen",
                    "listen",
                    "The gateway connection is retrying.",
                    "Transport connect attempt %d is in progress with %d recent failures." % (connect_attempts, failures),
                    "Cellular data is ready, but the node is still handshaking with the gateway.",
                ),
                "gateway_reconnect",
            )

        active, tool_name, active_reason = self._command_active_state(state, now_ms)
        if active:
            return (
                _build_ui_state(
                    "command_active",
                    "talk",
                    "happy",
                    "AIRI is actively handling a runtime task.",
                    "Executing %s on the qpyclaw node." % (tool_name or "runtime"),
                    "The board will return to standby when the current task settles.",
                ),
                active_reason,
            )

        if online and bool(voice.get("enabled")) and bool(voice.get("online")):
            return (
                _build_ui_state(
                    "voice_ready",
                    "listen",
                    "listen",
                    "The voice channel is ready.",
                    "Voice operator link is online and waiting for the next turn.",
                    "AIRI stays alert for the next dialog input.",
                ),
                "voice_ready",
            )

        if online:
            return (
                _build_ui_state(
                    "online_idle",
                    "idle",
                    "neutral",
                    "The node is online and idle.",
                    "qpyclaw-node is connected and waiting for work.",
                    "AIRI remains stable until the next command or voice turn.",
                ),
                "online_idle",
            )

        return (_boot_ui_state(node_id), "boot")

    def _render_runtime_state(self, runtime):
        snapshot = runtime.debug_snapshot()
        ui_state, reason = self._normalize_runtime_ui_state(snapshot)
        signature = _string(ui_state.get("signature")).strip()
        if signature == self._last_render_signature:
            self._remember_ui_state(ui_state, reason, False)
            return True
        self.board.ui.render_runtime_state(
            ui_state.get("mode_key"),
            ui_state.get("status"),
            ui_state.get("message"),
            ui_state.get("footer"),
            mood=ui_state.get("mood"),
        )
        self._remember_ui_state(ui_state, reason, True)
        return True

    def execute_board_status(self, args):
        _ = args
        return self.snapshot()

    def execute_display_status(self, args):
        _ = args
        return self.board.display.snapshot()

    def _coerce_color(self, value, default_color):
        if value is None:
            return int(default_color) & 0xFFFF
        if isinstance(value, int):
            return int(value) & 0xFFFF
        text = _string(value).strip().lower()
        named = {
            "black": 0x0000,
            "white": 0xFFFF,
            "red": 0xF800,
            "green": 0x07E0,
            "blue": 0x001F,
            "yellow": 0xFFE0,
            "cyan": 0x07FF,
            "magenta": 0xF81F,
        }
        if text in named:
            return named[text]
        if text[:1] == "#":
            text = text[1:]
        if text[:2] == "0x":
            return int(text, 16) & 0xFFFF
        return int(text) & 0xFFFF

    def execute_display_clear(self, args):
        _ = args
        result = self.board.ui.show_fill(0x0000)
        return {
            "result": result,
            "color": 0x0000,
            "color_hex": "0x0000",
            "ui": self.board.ui.snapshot(),
            "display": self.board.display.snapshot(),
        }

    def execute_display_fill(self, args):
        args = args or {}
        color = self._coerce_color(args.get("color"), 0xFFFF)
        result = self.board.ui.show_fill(color)
        return {
            "result": result,
            "color": color,
            "color_hex": "0x%04X" % color,
            "ui": self.board.ui.snapshot(),
            "display": self.board.display.snapshot(),
        }

    def execute_ui_status(self, args):
        _ = args
        return self.board.ui.snapshot()

    def execute_ui_catalog(self, args):
        _ = args
        return self.board.ui.catalog()

    def execute_ui_mode_show(self, args):
        args = args or {}
        mode = _string(args.get("mode")).strip().lower()
        emotion = _string(args.get("emotion")).strip().lower()
        if not mode and emotion:
            result = self.board.ui.show_emotion(emotion)
        else:
            if not mode:
                mode = "idle"
            result = self.board.ui.show_mode(
                mode,
                status=args.get("status"),
                message=args.get("message"),
                footer=args.get("footer"),
                mood=args.get("mood"),
            )
        return {
            "result": result,
            "ui": self.board.ui.snapshot(),
            "display": self.board.display.snapshot(),
        }

    def execute_ui_overlay_set(self, args):
        args = args or {}
        result = self.board.ui.show_overlay(
            status=args.get("status"),
            message=args.get("message"),
            footer=args.get("footer"),
            mood=args.get("mood"),
        )
        return {
            "result": result,
            "ui": self.board.ui.snapshot(),
            "display": self.board.display.snapshot(),
        }

    def snapshot(self):
        return {
            "name": "U235EC600UAiriBoardExtension",
            "enable_display": bool(self.enable_display),
            "enable_charge": bool(self.enable_charge),
            "open_audio": bool(self.open_audio),
            "enable_voice": bool(self.enable_voice),
            "voice_auto_start": bool(self.voice_auto_start),
            "bootstrapped": bool(self._bootstrapped),
            "last_ui_phase": self._last_ui_phase,
            "last_ui_reason": self._last_ui_reason,
            "last_ui_state": self._last_ui_state,
            "board": self.board.snapshot(),
        }


def create_qpyclaw_extension(
    board=None,
    enable_display=True,
    enable_charge=False,
    open_audio=False,
    enable_voice=False,
    voice_auto_start=False,
    **kwargs
):
    return U235EC600UAiriBoardExtension(
        board=board,
        enable_display=enable_display,
        enable_charge=enable_charge,
        open_audio=open_audio,
        enable_voice=enable_voice,
        voice_auto_start=voice_auto_start,
        **kwargs
    )
