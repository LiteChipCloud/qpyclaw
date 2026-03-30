def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


class BoardAudio(object):

    def __init__(self, channel=0, volume=5, pa_gpio=29, opus_bitrate=6000):
        self.channel = channel
        self.volume = volume
        self.pa_gpio = pa_gpio
        self.opus_bitrate = opus_bitrate
        self.audio_mod = _safe_import("audio")
        self.opus_mod = _safe_import("Opus")
        self.supported = bool(self.audio_mod and self.opus_mod)
        self.init_error = ""
        self.aud = None
        self.rec = None
        self.pcm = None
        self.opus = None
        self.vad_skip = 0
        self.kws_callback = None
        self.vad_callback = None

        if not self.supported:
            self.init_error = "audio or Opus module unavailable"
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
        _ = event
        return None

    def _require_supported(self):
        if not self.supported:
            raise Exception(self.init_error or "board audio unsupported")

    def play(self, path):
        self._require_supported()
        return self.aud.play(0, 1, path)

    def stop(self):
        self._require_supported()
        return self.aud.stopAll()

    def open_stream(self):
        self._require_supported()
        if self.opus is not None:
            return True
        self.pcm = self.audio_mod.Audio.PCM(0, 1, 16000, 2, 1, 15)
        self.opus = self.opus_mod(self.pcm, 0, self.opus_bitrate)
        return True

    def close_stream(self):
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
        return True

    def read_frame(self, frame_ms=60):
        self._require_supported()
        if self.opus is None:
            self.open_stream()
        return self.opus.read(frame_ms)

    def write_frame(self, data):
        self._require_supported()
        if self.opus is None:
            self.open_stream()
        return self.opus.write(data)

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

    def start_kws(self, wakeword="_xiao_zhi_xiao_zhi", threshold=0.7):
        self._require_supported()
        self.rec.ovkws_start(wakeword, threshold)
        return True

    def stop_kws(self):
        self._require_supported()
        self.rec.ovkws_stop()
        return True

    def start_vad(self):
        self._require_supported()
        self.vad_skip = 0
        self.rec.vad_start()
        return True

    def stop_vad(self):
        self._require_supported()
        self.rec.vad_stop()
        return True

    def get_volume(self):
        self._require_supported()
        return self.aud.getVolume()

    def set_volume(self, volume):
        self._require_supported()
        self.aud.setVolume(volume)
        self.volume = volume
        return volume

    def snapshot(self):
        return {
            "supported": bool(self.supported),
            "init_error": self.init_error,
            "stream_open": self.opus is not None,
            "channel": self.channel,
            "volume": self.volume,
            "pa_gpio": self.pa_gpio,
        }
