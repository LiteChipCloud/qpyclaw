def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def _ticks_ms(utime_mod):
    if utime_mod is None:
        return 0
    try:
        return utime_mod.ticks_ms()
    except Exception:
        try:
            return int(utime_mod.time() * 1000)
        except Exception:
            return 0


def _sleep_ms(utime_mod, delay_ms):
    if utime_mod is None:
        return
    try:
        utime_mod.sleep_ms(int(delay_ms))
    except Exception:
        pass


class BoardAudio(object):

    def __init__(self, channel=0, volume=5, pa_gpio=29, opus_bitrate=6000):
        self.channel = channel
        self.volume = volume
        self.pa_gpio = pa_gpio
        self.opus_bitrate = opus_bitrate
        self.utime = _safe_import("utime")
        self._thread = _safe_import("_thread")
        self.audio_mod = _safe_import("audio")
        self.opus_mod = _safe_import("Opus")
        self.supported = bool(self.audio_mod)
        self.opus_supported = bool(self.opus_mod)
        self.init_error = ""
        self.aud = None
        self.rec = None
        self.pcm = None
        self.opus = None
        self.stream_mode = ""
        self.stream_open_error = ""
        self.play_pcm = None
        self.play_opus = None
        self.play_stream_mode = ""
        self.play_stream_error = ""
        self.play_stream_sample_rate = 0
        self.play_stream_written_bytes = 0
        self.play_stream_written_frames = 0
        self.vad_skip = 0
        self.kws_callback = None
        self.vad_callback = None
        self.frame_callback = None
        self.kws_running = False
        self.vad_running = False
        self.thread_supported = bool(self._thread and hasattr(self._thread, "start_new_thread"))
        self.capture_pump_enabled = False
        self.capture_pump_running = False
        self.capture_pump_frame_ms = 60
        self.capture_pump_started_ms = 0
        self.capture_pump_last_frame_ms = 0
        self.capture_pump_last_error = ""
        self.capture_pump_frame_count = 0
        self.playback_busy = False
        self.playback_last_event = None
        self.playback_started_ms = 0
        self.playback_finished_ms = 0
        self.playback_last_path = ""
        self.playback_last_result = None
        self.playback_wait_timeout_count = 0

        if not self.supported:
            self.init_error = "audio module unavailable"
            return

        try:
            self.aud = self.audio_mod.Audio(channel)
            self.aud.set_pa(pa_gpio)
            self.aud.setVolume(volume)
            self.aud.setCallback(self._audio_cb)
            self.rec = self.audio_mod.Record(channel)
            self.rec.gain_set(4, 10)
        except Exception as e:
            self.init_error = str(e)
            self.supported = False
            self.aud = None
            self.rec = None

    def _audio_cb(self, event):
        self.playback_last_event = event
        if int(event or -1) == 0:
            self.playback_busy = True
            self.playback_started_ms = _ticks_ms(self.utime)
        elif int(event or -1) == 7:
            self.playback_busy = False
            self.playback_finished_ms = _ticks_ms(self.utime)
        return None

    def _require_supported(self):
        if not self.supported:
            raise Exception(self.init_error or "board audio unsupported")

    def play(self, path):
        self._require_supported()
        self.playback_busy = True
        self.playback_last_event = None
        self.playback_started_ms = _ticks_ms(self.utime)
        self.playback_finished_ms = 0
        self.playback_last_path = str(path or "")
        self.playback_last_result = self.aud.play(0, 1, path)
        return self.playback_last_result

    def stop(self):
        self._require_supported()
        try:
            result = self.aud.stopAll()
            self.playback_busy = False
            self.playback_finished_ms = _ticks_ms(self.utime)
            self.playback_last_result = result
            return result
        finally:
            self.close_playback_stream()
            if (not self.kws_running) and (not self.vad_running):
                self.stop_capture_pump(close_stream=False)

    def _close_pcm_like(self, obj):
        if obj is None:
            return
        try:
            obj.close()
        except Exception:
            pass

    def _open_pcm(self, sample_rate, frame_count):
        # Playback stream must be opened in write mode. Capture still uses the
        # original read/write path in `open_stream()` for the Opus encoder.
        return self.audio_mod.Audio.PCM(0, 1, int(sample_rate), 1, 1, int(frame_count))

    def open_stream(self):
        self._require_supported()
        if self.stream_mode:
            return True
        last_error = ""
        # Prefer record_stream (Ogg/Opus container) over raw Opus frames.
        # DashScope and other ASR services expect a proper audio container;
        # the raw Opus module produces bare encoded frames without an Ogg
        # header, which remote ASR endpoints cannot parse.
        stream_start = getattr(self.rec, "stream_start", None)
        stream_format = getattr(self.rec, "OGGOPUS", None)
        if callable(stream_start) and stream_format is not None:
            try:
                ret = stream_start(stream_format, 16000, 0)
                if int(ret) == 0:
                    self.stream_mode = "record_stream"
                    self.stream_open_error = ""
                    return True
                last_error = "record_stream_start=" + str(ret)
            except Exception as e:
                last_error = "record_stream: " + str(e)
        if self.opus_supported:
            try:
                self.pcm = self.audio_mod.Audio.PCM(0, 1, 16000, 2, 1, 15)
                self.opus = self.opus_mod(self.pcm, 0, self.opus_bitrate)
                self.stream_mode = "opus"
                if last_error:
                    self.stream_open_error = "record_stream_failed: " + last_error
                else:
                    self.stream_open_error = ""
                return True
            except Exception as e:
                last_error = last_error + "; opus: " + str(e) if last_error else str(e)
                self.stream_open_error = last_error
                if self.opus is not None:
                    try:
                        self.opus.close()
                    except Exception:
                        pass
                if self.pcm is not None:
                    try:
                        self.pcm.close()
                    except Exception:
                        pass
                self.opus = None
                self.pcm = None
        self.stream_open_error = last_error or "stream open failed"
        raise Exception(self.stream_open_error)

    def close_stream(self):
        self.stop_capture_pump(close_stream=False)
        if self.stream_mode == "record_stream":
            try:
                self.rec.stream_stop()
            except Exception:
                pass
        if self.opus is not None:
            try:
                self.opus.close()
            except Exception:
                pass
        if self.pcm is not None:
            try:
                self.pcm.close()
            except Exception:
                pass
        self.opus = None
        self.pcm = None
        self.stream_mode = ""
        return True

    def read_frame(self, frame_ms=60):
        self._require_supported()
        if not self.stream_mode:
            self.open_stream()
        if self.stream_mode == "opus":
            return self.opus.read(frame_ms)
        deadline = _ticks_ms(self.utime) + max(120, int(frame_ms or 60) + 60)
        used = 0
        while _ticks_ms(self.utime) < deadline:
            try:
                used = int(self.rec.ring_buf_used())
            except Exception:
                used = 0
            if used > 0:
                break
            _sleep_ms(self.utime, 10)
        if used <= 0:
            return b""
        if used > 1024:
            used = 1024
        buf = bytearray(used)
        read_len = self.rec.stream_read(buf, used)
        if int(read_len or 0) <= 0:
            return b""
        return bytes(buf[:read_len])

    def write_frame(self, data):
        self._require_supported()
        if not self.stream_mode:
            self.open_stream()
        if self.stream_mode != "opus":
            raise Exception("write_frame unsupported for " + str(self.stream_mode))
        return self.opus.write(data)

    def open_playback_stream(self, format_name="pcm", sample_rate=16000, frame_count=15):
        self._require_supported()
        requested = str(format_name or "pcm").strip().lower()
        if requested not in ("pcm", "opus"):
            raise Exception("unsupported playback format: " + requested)
        if self.play_stream_mode == requested and self.play_pcm is not None:
            return True
        self.close_playback_stream()
        if self.capture_pump_running or self.capture_pump_enabled:
            self.stop_capture_pump(close_stream=False)
        if self.stream_mode:
            try:
                self.close_stream()
            except Exception:
                pass
            _sleep_ms(self.utime, 180)
        self.play_stream_error = ""
        self.play_stream_sample_rate = int(sample_rate or 16000)
        try:
            self.play_pcm = self._open_pcm(self.play_stream_sample_rate, frame_count)
            if requested == "opus":
                if not self.opus_supported:
                    raise Exception("Opus module unavailable")
                self.play_opus = self.opus_mod(self.play_pcm, 0, self.opus_bitrate)
            self.play_stream_mode = requested
            self.play_stream_written_bytes = 0
            self.play_stream_written_frames = 0
            self.playback_busy = True
            self.playback_started_ms = _ticks_ms(self.utime)
            self.playback_finished_ms = 0
            return True
        except Exception as e:
            self.play_stream_error = str(e)
            self._close_pcm_like(self.play_opus)
            self._close_pcm_like(self.play_pcm)
            self.play_opus = None
            self.play_pcm = None
            self.play_stream_mode = ""
            raise

    def close_playback_stream(self, drain_ms=0):
        if int(drain_ms or 0) > 0:
            _sleep_ms(self.utime, int(drain_ms or 0))
        if self.play_pcm is not None:
            reset = getattr(self.play_pcm, "resetWriteBuffer", None)
            if callable(reset):
                try:
                    reset()
                except Exception:
                    pass
        self._close_pcm_like(self.play_opus)
        self._close_pcm_like(self.play_pcm)
        self.play_opus = None
        self.play_pcm = None
        self.play_stream_mode = ""
        if self.playback_busy:
            self.playback_busy = False
            self.playback_finished_ms = _ticks_ms(self.utime)
        return True

    def write_playback_frame(self, data):
        self._require_supported()
        if not data:
            return 0
        if not self.play_stream_mode:
            self.open_playback_stream("pcm", 16000)
        if self.play_stream_mode == "opus":
            written = self.play_opus.write(data)
        elif self.play_stream_mode == "pcm":
            if self.play_pcm is None:
                raise Exception("pcm playback unavailable")
            write = getattr(self.play_pcm, "write", None)
            if not callable(write):
                raise Exception("pcm write unavailable")
            try:
                written = write(data)
            except TypeError:
                written = write(data, len(data))
        else:
            raise Exception("unsupported playback mode: " + str(self.play_stream_mode))
        try:
            written_len = int(written or 0)
        except Exception:
            written_len = len(data)
        if written_len <= 0:
            written_len = len(data)
        self.play_stream_written_bytes = self.play_stream_written_bytes + int(written_len)
        self.play_stream_written_frames = self.play_stream_written_frames + 1
        self.playback_busy = True
        return written

    def set_kws_callback(self, callback):
        self._require_supported()
        self.kws_callback = callback
        self.rec.ovkws_set_callback(callback)
        return True

    def set_vad_callback(self, callback):
        self._require_supported()
        self.vad_callback = callback

        def _wrapper(state):
            if self.vad_skip != 2:
                self.vad_skip = self.vad_skip + 1
                return None
            return callback(state)

        self.rec.vad_set_callback(_wrapper)
        return True

    def set_frame_callback(self, callback):
        self.frame_callback = callback
        return True

    def _dispatch_frame(self, data):
        callback = self.frame_callback
        if callback is None:
            return False
        try:
            callback(data)
            return True
        except Exception as e:
            self.capture_pump_last_error = "frame_callback: " + str(e)
            return False

    def _capture_pump_main(self):
        self.capture_pump_running = True
        self.capture_pump_started_ms = _ticks_ms(self.utime)
        try:
            while self.capture_pump_enabled:
                try:
                    data = self.read_frame(self.capture_pump_frame_ms)
                    self.capture_pump_last_frame_ms = _ticks_ms(self.utime)
                    self.capture_pump_frame_count = self.capture_pump_frame_count + 1
                    self.capture_pump_last_error = ""
                    if data:
                        self._dispatch_frame(data)
                except Exception as e:
                    self.capture_pump_last_error = str(e)
                    _sleep_ms(self.utime, 120)
        finally:
            self.capture_pump_running = False

    def ensure_capture_pump(self, frame_ms=60):
        self._require_supported()
        self.open_stream()
        self.capture_pump_frame_ms = int(frame_ms or 60)
        self.capture_pump_enabled = True
        if self.capture_pump_running:
            return {
                "started": False,
                "reason": "already_running",
                "frame_ms": self.capture_pump_frame_ms,
            }
        if not self.thread_supported:
            raise Exception("audio capture pump requires _thread")
        self._thread.start_new_thread(self._capture_pump_main, ())
        return {
            "started": True,
            "reason": "started",
            "frame_ms": self.capture_pump_frame_ms,
        }

    def stop_capture_pump(self, close_stream=False, wait_ms=1200):
        self.capture_pump_enabled = False
        deadline = _ticks_ms(self.utime) + int(wait_ms or 0)
        while self.capture_pump_running and (_ticks_ms(self.utime) < deadline):
            _sleep_ms(self.utime, 40)
        if close_stream:
            self.close_stream()
        return {
            "running": bool(self.capture_pump_running),
            "enabled": bool(self.capture_pump_enabled),
            "frame_count": self.capture_pump_frame_count,
        }

    def _stop_capture_if_idle(self):
        if self.kws_running or self.vad_running:
            return False
        self.stop_capture_pump(close_stream=False)
        return True

    def start_kws(self, wakeword="_xiao_zhi_xiao_zhi", threshold=0.7):
        self._require_supported()
        self.rec.ovkws_start(wakeword, threshold)
        self.kws_running = True
        return True

    def stop_kws(self):
        self._require_supported()
        self.rec.ovkws_stop()
        self.kws_running = False
        self._stop_capture_if_idle()
        return True

    def start_vad(self):
        self._require_supported()
        self.vad_skip = 0
        self.ensure_capture_pump()
        self.rec.vad_start()
        self.vad_running = True
        return True

    def stop_vad(self):
        self._require_supported()
        self.rec.vad_stop()
        self.vad_running = False
        self._stop_capture_if_idle()
        return True

    def get_volume(self):
        self._require_supported()
        return self.aud.getVolume()

    def set_volume(self, volume):
        self._require_supported()
        self.aud.setVolume(volume)
        self.volume = volume
        return volume

    def is_playing(self):
        return bool(self.playback_busy)

    def wait_playback(self, timeout_ms=12000, poll_ms=60):
        deadline = _ticks_ms(self.utime) + max(0, int(timeout_ms or 0))
        while self.playback_busy and (_ticks_ms(self.utime) < deadline):
            _sleep_ms(self.utime, poll_ms)
        if self.playback_busy:
            self.playback_wait_timeout_count = self.playback_wait_timeout_count + 1
            return {
                "ok": False,
                "status": "timeout",
                "busy": True,
                "last_event": self.playback_last_event,
                "started_ms": self.playback_started_ms,
                "finished_ms": self.playback_finished_ms,
            }
        return {
            "ok": True,
            "status": "done",
            "busy": False,
            "last_event": self.playback_last_event,
            "started_ms": self.playback_started_ms,
            "finished_ms": self.playback_finished_ms,
        }

    def snapshot(self):
        return {
            "supported": bool(self.supported),
            "opus_supported": bool(self.opus_supported),
            "init_error": self.init_error,
            "stream_open": bool(self.stream_mode),
            "stream_mode": self.stream_mode,
            "stream_open_error": self.stream_open_error,
            "channel": self.channel,
            "volume": self.volume,
            "pa_gpio": self.pa_gpio,
            "thread_supported": bool(self.thread_supported),
            "kws_running": bool(self.kws_running),
            "vad_running": bool(self.vad_running),
            "capture_pump_enabled": bool(self.capture_pump_enabled),
            "capture_pump_running": bool(self.capture_pump_running),
            "capture_pump_frame_ms": self.capture_pump_frame_ms,
            "capture_pump_started_ms": self.capture_pump_started_ms,
            "capture_pump_last_frame_ms": self.capture_pump_last_frame_ms,
            "capture_pump_last_error": self.capture_pump_last_error,
            "capture_pump_frame_count": self.capture_pump_frame_count,
            "playback_busy": bool(self.playback_busy),
            "playback_last_event": self.playback_last_event,
            "playback_started_ms": self.playback_started_ms,
            "playback_finished_ms": self.playback_finished_ms,
            "playback_last_path": self.playback_last_path,
            "playback_last_result": self.playback_last_result,
            "playback_wait_timeout_count": self.playback_wait_timeout_count,
            "play_stream_mode": self.play_stream_mode,
            "play_stream_error": self.play_stream_error,
            "play_stream_sample_rate": self.play_stream_sample_rate,
            "play_stream_written_bytes": self.play_stream_written_bytes,
            "play_stream_written_frames": self.play_stream_written_frames,
        }
