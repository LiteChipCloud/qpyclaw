import utime

from board_audio import BoardAudio
from board_display import BoardDisplay
from board_power import BoardPower
from board_ui import BoardEmojiUi
from board_voice_controller import BoardVoiceSessionController

try:
    from machine import Pin as _Pin
except Exception:
    _Pin = None


def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _boolish(value, default=False):
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    text = _string(value).strip().lower()
    if text in ("1", "true", "yes", "on", "enable", "enabled"):
        return True
    if text in ("0", "false", "no", "off", "disable", "disabled"):
        return False
    return bool(default)


def _transcript_provider_name(provider):
    if provider is None:
        return ""
    try:
        return provider.__class__.__name__
    except Exception:
        return _string(provider)


def _speaker_name(speaker):
    if speaker is None:
        return ""
    try:
        return speaker.__class__.__name__
    except Exception:
        return _string(speaker)


class EC800MCNLEAudioBoard(object):

    def __init__(self, audio=None, power=None, display=None, ui=None, voice=None):
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
        if voice is None:
            voice = BoardVoiceSessionController(self)
        self.voice = voice
        self._init_user_button(voice)

    def _init_user_button(self, voice):
        if _Pin is None:
            return
        try:
            btn = _Pin(getattr(_Pin, "GPIO27", 27), _Pin.IN, _Pin.PULL_PU)
            voice._button_pin = btn
        except Exception:
            pass

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
        if self.voice is not None:
            self.voice.bind_runtime(runtime)
        return True

    def show_online(self):
        if self.voice is not None:
            voice_state = _string(getattr(self.voice, "state", "")).strip()
            voice_active = bool(getattr(self.voice, "active", False))
            if voice_active and voice_state and voice_state not in ("idle", "stopped"):
                try:
                    self.voice._show_state(voice_state)
                    self.voice._show_status_text(voice_state)
                    return True
                except Exception:
                    pass
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
        if self.voice is not None:
            try:
                self.voice.handle_button()
            except Exception:
                pass
            try:
                self.voice.step()
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
            "voice": self.voice.snapshot() if self.voice is not None else None,
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

    def __init__(
        self,
        board=None,
        enable_charge=True,
        enable_display=True,
        open_audio=False,
        enable_voice=False,
        voice_auto_start=False,
        transcript_provider=None,
        reply_handler=None,
        speaker=None,
    ):
        if board is None:
            board = create_default_board()
        self.board = board
        self.enable_charge = bool(enable_charge)
        self.enable_display = bool(enable_display)
        self.open_audio = bool(open_audio)
        self.enable_voice = bool(enable_voice)
        self.voice_auto_start = bool(voice_auto_start)
        self.transcript_provider = transcript_provider
        self.reply_handler = reply_handler
        self.speaker = speaker
        self._bootstrapped = False
        self._resolved_transcript_provider = transcript_provider
        self._resolved_speaker = speaker
        self.debug_force_listen_on_boot = False
        self._debug_force_listen_pending = False
        self._debug_force_listen_attempts = 0
        self._debug_force_listen_last_result = ""
        self._debug_force_listen_last_error = ""
        self._debug_force_listen_last_runtime_online = False
        self._debug_force_listen_last_voice_state = ""
        self._debug_force_listen_last_ms = 0
        if self.board.voice is not None:
            self.board.voice.configure(
                enabled=self.enable_voice,
                auto_start=self.voice_auto_start,
                transcript_provider=self.transcript_provider,
                reply_handler=self.reply_handler,
                speaker=self.speaker,
            )

    def _resolve_transcript_provider(self, runtime):
        provider = self.transcript_provider
        if provider is not None:
            self._resolved_transcript_provider = provider
            return provider
        cfg = getattr(runtime, "cfg", None)
        if cfg is None:
            self._resolved_transcript_provider = None
            return None
        mode = _string(getattr(cfg, "VOICE_TRANSCRIPT_PROVIDER", "")).strip().lower()
        url = _string(getattr(cfg, "VOICE_ASR_HTTP_URL", "")).strip()
        fixed_text = _string(getattr(cfg, "VOICE_ASR_FIXED_TRANSCRIPT", "")).strip()
        if (not mode) and (not url) and (not fixed_text):
            self._resolved_transcript_provider = None
            return None
        if mode not in ("", "http", "remote_asr_http", "asr_http", "fixed", "mock", "smoke") and (not url) and (not fixed_text):
            self._resolved_transcript_provider = None
            return None
        module = _safe_import("board_remote_asr")
        if module is None or (not hasattr(module, "RemoteAsrTranscriptProvider")):
            self._resolved_transcript_provider = None
            return None
        provider = module.RemoteAsrTranscriptProvider(cfg)
        self._resolved_transcript_provider = provider
        return provider

    def _resolve_speaker(self, runtime):
        speaker = self.speaker
        if speaker is not None:
            self._resolved_speaker = speaker
            return speaker
        cfg = getattr(runtime, "cfg", None)
        if cfg is None:
            self._resolved_speaker = None
            return None
        stream_enabled = _boolish(getattr(cfg, "VOICE_TTS_STREAM_ENABLED", None), False)
        stream_url = _string(getattr(cfg, "VOICE_TTS_STREAM_URL", "")).strip()
        if stream_enabled or stream_url:
            module = _safe_import("board_remote_tts")
            if module is not None and hasattr(module, "RemoteTtsSpeaker"):
                speaker = module.RemoteTtsSpeaker(cfg)
                self._resolved_speaker = speaker
                return speaker
        enabled_value = getattr(cfg, "VOICE_TTS_HTTP_ENABLED", None)
        if enabled_value is not None:
            enabled_text = _string(enabled_value).strip().lower()
            if enabled_text in ("0", "false", "no", "off", "disable", "disabled"):
                self._resolved_speaker = None
                return None
        tts_url = _string(getattr(cfg, "VOICE_TTS_HTTP_URL", "")).strip()
        asr_url = _string(getattr(cfg, "VOICE_ASR_HTTP_URL", "")).strip()
        if (not tts_url) and (not asr_url):
            self._resolved_speaker = None
            return None
        module = _safe_import("board_remote_tts")
        if module is None or (not hasattr(module, "RemoteTtsSpeaker")):
            self._resolved_speaker = None
            return None
        speaker = module.RemoteTtsSpeaker(cfg)
        self._resolved_speaker = speaker
        return speaker

    def get_caps(self):
        caps = ["audio", "display", "board-ui", "power"]
        if self.board.voice is not None:
            caps.append("voice-local")
        return caps

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
                "name": "qpy.board.voice.status",
                "summary": "Return board-local voice session controller state.",
                "aliases": ["board.voice.status", "voice.session.status"],
                "category": "voice",
                "read_only": True,
                "executor": self.execute_board_voice_status,
            },
            {
                "name": "qpy.board.voice.start",
                "summary": "Start board-local voice session control.",
                "aliases": ["board.voice.start", "voice.session.start"],
                "category": "voice",
                "read_only": False,
                "executor": self.execute_board_voice_start,
            },
            {
                "name": "qpy.board.voice.listen",
                "summary": "Force the board-local voice controller into listening state.",
                "aliases": ["board.voice.listen", "voice.session.listen", "voice.session.wake"],
                "category": "voice",
                "read_only": False,
                "executor": self.execute_board_voice_listen,
            },
            {
                "name": "qpy.board.voice.stop",
                "summary": "Stop board-local voice session control.",
                "aliases": ["board.voice.stop", "voice.session.stop"],
                "category": "voice",
                "read_only": False,
                "executor": self.execute_board_voice_stop,
            },
            {
                "name": "qpy.board.voice.abort",
                "summary": "Abort the current board-local voice turn.",
                "aliases": ["board.voice.abort", "voice.session.abort"],
                "category": "voice",
                "read_only": False,
                "executor": self.execute_board_voice_abort,
            },
            {
                "name": "qpy.board.voice.inject",
                "summary": "Inject a transcript into the board-local voice controller.",
                "aliases": ["board.voice.inject", "voice.session.submit", "voice.session.inject"],
                "category": "voice",
                "read_only": False,
                "executor": self.execute_board_voice_inject,
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
            try:
                self.board.boot_minimal(
                    enable_charge=self.enable_charge,
                    enable_display=self.enable_display,
                    open_audio=self.open_audio,
                )
            except Exception:
                if not self.enable_display:
                    raise
                self.enable_display = False
                self.board.boot_minimal(
                    enable_charge=self.enable_charge,
                    enable_display=False,
                    open_audio=self.open_audio,
                )
            self._bootstrapped = True
        self.board.attach_runtime(runtime)
        cfg = getattr(runtime, "cfg", None)
        self.debug_force_listen_on_boot = _boolish(
            getattr(cfg, "BOARD_DEBUG_FORCE_LISTEN_ON_BOOT", False),
            False,
        )
        self._debug_force_listen_pending = bool(self.debug_force_listen_on_boot)
        if self.debug_force_listen_on_boot and self.board.voice is not None:
            try:
                timeout_ms = int(getattr(self.board.voice, "listen_timeout_ms", 0) or 0)
            except Exception:
                timeout_ms = 0
            try:
                debug_timeout_ms = int(
                    getattr(cfg, "BOARD_DEBUG_FORCE_LISTEN_TIMEOUT_MS", 10000) or 10000
                )
            except Exception:
                debug_timeout_ms = 10000
            if debug_timeout_ms < 3000:
                debug_timeout_ms = 3000
            if timeout_ms < debug_timeout_ms:
                self.board.voice.listen_timeout_ms = debug_timeout_ms
        provider = self._resolve_transcript_provider(runtime)
        speaker = self._resolve_speaker(runtime)
        if self.board.voice is not None:
            self.board.voice.configure(
                enabled=self.enable_voice,
                auto_start=self.voice_auto_start,
                transcript_provider=provider,
                reply_handler=self.reply_handler,
                speaker=speaker,
            )
            if self.enable_voice and self.voice_auto_start:
                try:
                    self.board.voice.start()
                except Exception:
                    pass
        return True

    def on_online_changed(self, runtime, online):
        _ = runtime
        if online:
            self.board.show_online()
        else:
            self.board.show_offline()
        return True

    def _runtime_online(self, runtime):
        if runtime is None:
            return False
        transport = getattr(runtime, "transport", None)
        if transport is not None:
            try:
                if bool(getattr(transport, "online", False)):
                    return True
            except Exception:
                pass
        state = getattr(runtime, "state", None)
        if state is not None:
            try:
                return bool(getattr(state, "online", False))
            except Exception:
                return False
        return False

    def after_step(self, runtime):
        if self.debug_force_listen_on_boot and self.board.voice is not None:
            self._debug_force_listen_attempts = self._debug_force_listen_attempts + 1
            self._debug_force_listen_last_ms = utime.ticks_ms()
            self._debug_force_listen_last_error = ""
            runtime_online = self._runtime_online(runtime)
            self._debug_force_listen_last_runtime_online = bool(runtime_online)
            voice_state = _string(getattr(self.board.voice, "state", "")).strip()
            self._debug_force_listen_last_voice_state = voice_state
            active = bool(getattr(self.board.voice, "active", False))
            worker_busy = bool(getattr(self.board.voice, "worker_busy", False))
            vad_running = bool(getattr(self.board.voice, "vad_running", False))
            if (
                runtime_online
                and active
                and (not worker_busy)
                and (not vad_running)
                and voice_state in ("idle", "error")
            ):
                try:
                    if self.board.voice.begin_listening("boot-debug"):
                        self.debug_force_listen_on_boot = False
                        self._debug_force_listen_pending = False
                        self._debug_force_listen_last_result = "started"
                    else:
                        self._debug_force_listen_last_result = "begin_listening_false"
                except Exception as e:
                    self._debug_force_listen_last_error = _string(e)
                    self._debug_force_listen_last_result = "exception"
            else:
                reasons = []
                if not runtime_online:
                    reasons.append("runtime_offline")
                if not active:
                    reasons.append("voice_inactive")
                if worker_busy:
                    reasons.append("worker_busy")
                if vad_running:
                    reasons.append("vad_running")
                if voice_state not in ("idle", "error"):
                    reasons.append("voice_state=" + voice_state)
                self._debug_force_listen_last_result = ",".join(reasons) or "conditions_not_met"
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

    def _board_voice(self):
        if self.board.voice is None:
            raise Exception("board voice unavailable")
        return self.board.voice

    def execute_board_voice_status(self, args):
        _ = args
        return self._board_voice().snapshot()

    def execute_board_voice_start(self, args):
        args = args or {}
        controller = self._board_voice()
        if "auto_start" in args:
            controller.configure(auto_start=bool(args.get("auto_start")))
        if "enabled" in args:
            controller.configure(enabled=bool(args.get("enabled")))
        result = controller.start()
        return {
            "result": True,
            "voice": result,
        }

    def execute_board_voice_listen(self, args):
        args = args or {}
        controller = self._board_voice()
        reason = _string(args.get("reason")).strip() or "manual"
        result = controller.begin_listening(reason)
        return {
            "result": bool(result),
            "voice": controller.snapshot(),
        }

    def execute_board_voice_stop(self, args):
        args = args or {}
        controller = self._board_voice()
        result = controller.stop()
        if bool(args.get("disable")):
            controller.configure(enabled=False, auto_start=False)
            result = controller.snapshot()
        return {
            "result": True,
            "voice": result,
        }

    def execute_board_voice_abort(self, args):
        args = args or {}
        controller = self._board_voice()
        reason = str(args.get("reason") or "tool.abort")
        result = controller.abort(reason)
        return {
            "result": True,
            "voice": result,
        }

    def execute_board_voice_inject(self, args):
        args = args or {}
        text = str(args.get("text") or "").strip()
        if not text:
            raise Exception("text required")
        source = str(args.get("source") or "tool.inject")
        result = self._board_voice().inject_transcript(text, source=source)
        return {
            "result": True,
            "voice": result,
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
            "enable_voice": self.enable_voice,
            "voice_auto_start": self.voice_auto_start,
            "debug_force_listen_on_boot": self.debug_force_listen_on_boot,
            "debug_force_listen_pending": self._debug_force_listen_pending,
            "debug_force_listen_attempts": self._debug_force_listen_attempts,
            "debug_force_listen_last_result": self._debug_force_listen_last_result,
            "debug_force_listen_last_error": self._debug_force_listen_last_error,
            "debug_force_listen_last_runtime_online": self._debug_force_listen_last_runtime_online,
            "debug_force_listen_last_voice_state": self._debug_force_listen_last_voice_state,
            "debug_force_listen_last_ms": self._debug_force_listen_last_ms,
            "transcript_provider": _transcript_provider_name(self._resolved_transcript_provider),
            "speaker": _speaker_name(self._resolved_speaker),
            "bootstrapped": self._bootstrapped,
            "board": self.board.snapshot(),
        }

def create_qpyclaw_extension(
    board=None,
    enable_charge=True,
    enable_display=True,
    open_audio=False,
    enable_voice=False,
    voice_auto_start=False,
    transcript_provider=None,
    reply_handler=None,
    speaker=None,
):
    return EC800MCNLEBoardExtension(
        board,
        enable_charge=enable_charge,
        enable_display=enable_display,
        open_audio=open_audio,
        enable_voice=enable_voice,
        voice_auto_start=voice_auto_start,
        transcript_provider=transcript_provider,
        reply_handler=reply_handler,
        speaker=speaker,
    )
