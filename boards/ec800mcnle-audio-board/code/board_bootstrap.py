import utime

from board_audio import BoardAudio
from board_display import BoardDisplay
from board_power import BoardPower
from board_ui import BoardEmojiUi


class EC800MCNLEAudioBoard(object):

    def __init__(self, audio=None, power=None, display=None, ui=None):
        if audio is None:
            audio = BoardAudio()
        if power is None:
            power = BoardPower()
        if display is None:
            display = BoardDisplay()
        if ui is None:
            ui = BoardEmojiUi(display)

        self.audio = audio
        self.power = power
        self.display = display
        self.ui = ui
        self.runtime = None
        self.last_online = None

    def boot_minimal(self, enable_charge=True, enable_display=True, open_audio=False):
        if self.power.supported:
            self.power.prepare_boot_pins()
            if enable_charge:
                self.power.enable_charge()

        if enable_display and self.display.supported:
            self.display.ensure_ready()
            self.ui.ensure_ready()
            self.ui.show_booting()

        if open_audio and self.audio.supported:
            self.audio.open_stream()

        if enable_display and self.display.supported:
            self.ui.show_waiting()

        return self.snapshot()

    def attach_runtime(self, runtime):
        self.runtime = runtime
        return True

    def show_online(self):
        if self.ui is not None:
            self.ui.show_ready()
        return True

    def show_offline(self):
        if self.ui is not None:
            self.ui.show_waiting()
        return True

    def show_error(self):
        if self.ui is not None:
            self.ui.show_error()
        return True

    def update_from_runtime(self):
        if self.runtime is None:
            return None
        snapshot = self.runtime.debug_snapshot()
        online = bool(snapshot.get("online"))
        if self.last_online is None or online != self.last_online:
            self.last_online = online
            if online:
                self.show_online()
            else:
                self.show_offline()
        return online

    def tick(self):
        try:
            self.update_from_runtime()
        except Exception:
            self.show_error()
        if self.ui is not None:
            self.ui.tick()
        return True

    def snapshot(self):
        return {
            "audio": self.audio.snapshot(),
            "power": self.power.snapshot(),
            "display": self.display.snapshot(),
            "ui": self.ui.snapshot(),
            "runtime_attached": self.runtime is not None,
        }

    def run_qpyclaw_node_forever(self, runtime=None, open_audio=False, step_delay_ms=20):
        if runtime is None:
            import qpyclaw_node

            runtime = qpyclaw_node.create_runtime()

        self.boot_minimal(enable_charge=True, enable_display=True, open_audio=open_audio)
        self.attach_runtime(runtime)

        while True:
            try:
                runtime.step()
                self.tick()
            except Exception:
                self.show_error()
            utime.sleep_ms(step_delay_ms)


def create_default_board(media_prefix="U:/media"):
    display = BoardDisplay()
    ui = BoardEmojiUi(display, media_prefix=media_prefix)
    return EC800MCNLEAudioBoard(display=display, ui=ui)


class EC800MCNLEBoardExtension(object):

    def __init__(self, board=None, enable_charge=True, enable_display=True, open_audio=False):
        if board is None:
            board = create_default_board()
        self.board = board
        self.enable_charge = bool(enable_charge)
        self.enable_display = bool(enable_display)
        self.open_audio = bool(open_audio)
        self._bootstrapped = False

    def get_caps(self):
        return ["audio", "display", "board-ui", "power"]

    def get_tool_specs(self):
        return [
            {
                "name": "qpy.board.status",
                "summary": "Return EC800MCNLE audio-board capability snapshot.",
                "aliases": ["board.status"],
                "category": "board",
                "read_only": True,
                "executor": self.execute_board_status,
            },
            {
                "name": "qpy.audio.status",
                "summary": "Return local audio capability and stream state.",
                "aliases": ["audio.status"],
                "category": "audio",
                "read_only": True,
                "executor": self.execute_audio_status,
            },
            {
                "name": "qpy.audio.volume.get",
                "summary": "Read current speaker volume on the EC800MCNLE audio board.",
                "aliases": ["audio.volume.get"],
                "category": "audio",
                "read_only": True,
                "executor": self.execute_audio_volume_get,
            },
            {
                "name": "qpy.audio.volume.set",
                "summary": "Set speaker volume on the EC800MCNLE audio board.",
                "aliases": ["audio.volume.set"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_volume_set,
            },
            {
                "name": "qpy.audio.play",
                "summary": "Play a local audio file on the EC800MCNLE audio board.",
                "aliases": ["audio.play"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_play,
            },
            {
                "name": "qpy.audio.stop",
                "summary": "Stop local audio playback on the EC800MCNLE audio board.",
                "aliases": ["audio.stop"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_stop,
            },
            {
                "name": "qpy.audio.stream.open",
                "summary": "Open the board-local Opus audio stream pipeline.",
                "aliases": ["audio.stream.open"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_stream_open,
            },
            {
                "name": "qpy.audio.stream.close",
                "summary": "Close the board-local Opus audio stream pipeline.",
                "aliases": ["audio.stream.close"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_stream_close,
            },
            {
                "name": "qpy.audio.kws.start",
                "summary": "Start local keyword spotting on the EC800MCNLE audio board.",
                "aliases": ["audio.kws.start"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_kws_start,
            },
            {
                "name": "qpy.audio.kws.stop",
                "summary": "Stop local keyword spotting on the EC800MCNLE audio board.",
                "aliases": ["audio.kws.stop"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_kws_stop,
            },
            {
                "name": "qpy.audio.vad.start",
                "summary": "Start local VAD on the EC800MCNLE audio board.",
                "aliases": ["audio.vad.start"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_vad_start,
            },
            {
                "name": "qpy.audio.vad.stop",
                "summary": "Stop local VAD on the EC800MCNLE audio board.",
                "aliases": ["audio.vad.stop"],
                "category": "audio",
                "read_only": False,
                "executor": self.execute_audio_vad_stop,
            },
            {
                "name": "qpy.power.status",
                "summary": "Return EC800MCNLE power and charge-pin state.",
                "aliases": ["power.status"],
                "category": "power",
                "read_only": True,
                "executor": self.execute_power_status,
            },
            {
                "name": "qpy.power.charge.enable",
                "summary": "Enable board charging control pin.",
                "aliases": ["power.charge.enable"],
                "category": "power",
                "read_only": False,
                "executor": self.execute_power_charge_enable,
            },
            {
                "name": "qpy.power.charge.disable",
                "summary": "Disable board charging control pin.",
                "aliases": ["power.charge.disable"],
                "category": "power",
                "read_only": False,
                "executor": self.execute_power_charge_disable,
            },
            {
                "name": "qpy.display.status",
                "summary": "Return local display-driver state.",
                "aliases": ["display.status"],
                "category": "display",
                "read_only": True,
                "executor": self.execute_display_status,
            },
            {
                "name": "qpy.display.clear",
                "summary": "Fill the full panel with black and pause UI repainting.",
                "aliases": ["display.clear"],
                "category": "display",
                "read_only": False,
                "executor": self.execute_display_clear,
            },
            {
                "name": "qpy.display.fill",
                "summary": "Fill the full panel with a solid RGB565 color and pause UI repainting.",
                "aliases": ["display.fill"],
                "category": "display",
                "read_only": False,
                "executor": self.execute_display_fill,
            },
            {
                "name": "qpy.ui.status",
                "summary": "Return board UI state and current emoji.",
                "aliases": ["ui.status"],
                "category": "display",
                "read_only": True,
                "executor": self.execute_ui_status,
            },
            {
                "name": "qpy.ui.emotion.catalog",
                "summary": "Return supported and available emoji assets for the board UI.",
                "aliases": ["ui.emotion.catalog"],
                "category": "display",
                "read_only": True,
                "executor": self.execute_ui_emotion_catalog,
            },
            {
                "name": "qpy.ui.emotion.show",
                "summary": "Show a named emoji on the board screen UI.",
                "aliases": ["ui.emotion.show"],
                "category": "display",
                "read_only": False,
                "executor": self.execute_ui_emotion_show,
            },
        ]

    def on_runtime_created(self, runtime):
        if not self._bootstrapped:
            self.board.boot_minimal(
                enable_charge=self.enable_charge,
                enable_display=self.enable_display,
                open_audio=self.open_audio,
            )
            self._bootstrapped = True
        self.board.attach_runtime(runtime)
        return True

    def on_online_changed(self, runtime, online):
        _ = runtime
        if online:
            self.board.show_online()
        else:
            self.board.show_offline()
        return True

    def after_step(self, runtime):
        _ = runtime
        self.board.tick()
        return True

    def on_runtime_error(self, runtime, message):
        _ = runtime
        _ = message
        self.board.show_error()
        self.board.tick()
        return True

    def execute_board_status(self, args):
        _ = args
        return self.board.snapshot()

    def execute_audio_status(self, args):
        _ = args
        return self.board.audio.snapshot()

    def execute_audio_volume_get(self, args):
        _ = args
        return {
            "volume": self.board.audio.get_volume(),
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_volume_set(self, args):
        args = args or {}
        if "volume" not in args:
            raise Exception("volume required")
        volume = int(args.get("volume"))
        self.board.audio.set_volume(volume)
        return {
            "volume": self.board.audio.get_volume(),
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_play(self, args):
        args = args or {}
        path = str(args.get("path") or "").strip()
        if not path:
            raise Exception("path required")
        result = self.board.audio.play(path)
        return {
            "path": path,
            "result": result,
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_stop(self, args):
        _ = args
        result = self.board.audio.stop()
        return {
            "result": result,
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_stream_open(self, args):
        _ = args
        result = self.board.audio.open_stream()
        return {
            "result": result,
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_stream_close(self, args):
        _ = args
        result = self.board.audio.close_stream()
        return {
            "result": result,
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_kws_start(self, args):
        args = args or {}
        wakeword = str(args.get("wakeword") or "_xiao_zhi_xiao_zhi")
        threshold = float(args.get("threshold") if "threshold" in args else 0.7)
        result = self.board.audio.start_kws(wakeword, threshold)
        return {
            "result": result,
            "wakeword": wakeword,
            "threshold": threshold,
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_kws_stop(self, args):
        _ = args
        result = self.board.audio.stop_kws()
        return {
            "result": result,
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_vad_start(self, args):
        _ = args
        result = self.board.audio.start_vad()
        return {
            "result": result,
            "audio": self.board.audio.snapshot(),
        }

    def execute_audio_vad_stop(self, args):
        _ = args
        result = self.board.audio.stop_vad()
        return {
            "result": result,
            "audio": self.board.audio.snapshot(),
        }

    def execute_power_status(self, args):
        _ = args
        return self.board.power.snapshot()

    def execute_power_charge_enable(self, args):
        _ = args
        result = self.board.power.enable_charge()
        return {
            "result": result,
            "power": self.board.power.snapshot(),
        }

    def execute_power_charge_disable(self, args):
        _ = args
        result = self.board.power.disable_charge()
        return {
            "result": result,
            "power": self.board.power.snapshot(),
        }

    def execute_display_status(self, args):
        _ = args
        return self.board.display.snapshot()

    def _coerce_display_color(self, value, default_color):
        if value is None:
            return int(default_color) & 0xFFFF
        if isinstance(value, int):
            return int(value) & 0xFFFF
        text = str(value).strip().lower()
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
        if text.startswith("#"):
            text = text[1:]
        if text.startswith("0x"):
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
        color = self._coerce_display_color(args.get("color"), 0xFFFF)
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
        return {
            "ui": self.board.ui.snapshot(),
            "display": self.board.display.snapshot(),
        }

    def execute_ui_emotion_catalog(self, args):
        _ = args
        return self.board.ui.catalog()

    def execute_ui_emotion_show(self, args):
        args = args or {}
        emotion = str(args.get("emotion") or "").strip()
        if not emotion:
            raise Exception("emotion required")
        result = self.board.ui.show_emotion(emotion)
        return {
            "result": result,
            "ui": self.board.ui.snapshot(),
            "display": self.board.display.snapshot(),
        }

    def snapshot(self):
        return {
            "name": "EC800MCNLEBoardExtension",
            "enable_charge": self.enable_charge,
            "enable_display": self.enable_display,
            "open_audio": self.open_audio,
            "bootstrapped": self._bootstrapped,
            "board": self.board.snapshot(),
        }

def create_qpyclaw_extension(board=None, enable_charge=True, enable_display=True, open_audio=False):
    return EC800MCNLEBoardExtension(
        board,
        enable_charge=enable_charge,
        enable_display=enable_display,
        open_audio=open_audio,
    )
