def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def _ticks_ms():
    utime = _safe_import("utime")
    if utime is None:
        return 0
    try:
        return utime.ticks_ms()
    except Exception:
        try:
            return int(utime.time() * 1000)
        except Exception:
            return 0


def _ticks_diff(newer, older):
    utime = _safe_import("utime")
    if utime is not None and hasattr(utime, "ticks_diff"):
        try:
            return utime.ticks_diff(newer, older)
        except Exception:
            pass
    return int(newer or 0) - int(older or 0)


def _audio_format_from_mode(stream_mode):
    mode = str(stream_mode or "").strip()
    if mode == "record_stream":
        return "oggopus"
    if mode == "opus":
        return "opus"
    if mode:
        return mode
    return "unknown"


class BoardVoiceSessionController(object):

    def __init__(
        self,
        board,
        enabled=False,
        auto_start=False,
        audio_enabled=True,
        transcript_provider=None,
        reply_handler=None,
        speaker=None,
        wake_timeout_ms=4000,
        listen_timeout_ms=15000,
    ):
        self.board = board
        self.audio = getattr(board, "audio", None)
        self.ui = getattr(board, "ui", None)
        self.runtime = None
        self.enabled = bool(enabled)
        self.auto_start = bool(auto_start)
        self.audio_enabled = bool(audio_enabled)
        self.transcript_provider = transcript_provider
        self.reply_handler = reply_handler
        self.speaker = speaker
        self.wake_timeout_ms = int(wake_timeout_ms or 4000)
        self.listen_timeout_ms = int(listen_timeout_ms or 15000)
        self._thread = _safe_import("_thread")
        self._lock = None
        if self._thread is not None and hasattr(self._thread, "allocate_lock"):
            try:
                self._lock = self._thread.allocate_lock()
            except Exception:
                self._lock = None
        self.thread_supported = bool(
            self._thread is not None
            and hasattr(self._thread, "start_new_thread")
            and self._lock is not None
        )
        self.active = False
        self.auto_started = False
        self.state = "idle"
        self.state_reason = ""
        self.state_changed_ms = 0
        self.kws_running = False
        self.vad_running = False
        self.worker_busy = False
        self.worker_threaded = False
        self.abort_inflight = False
        self.pending_listen_after_abort = False
        self.pending_kws = 0
        self.pending_vad_begin = 0
        self.pending_vad_end = 0
        self.pending_transcripts = []
        self.last_kws_event = None
        self.last_vad_event = None
        self.last_transcript = ""
        self.last_transcript_source = ""
        self.last_reply_text = ""
        self.last_voice_directive = {}
        self.last_reply_handler_result = {}
        self.last_speaker_result = {}
        self.last_result = None
        self.last_result_ok = None
        self.last_error = ""
        self.last_error_ms = 0
        self.last_turn_started_ms = 0
        self.last_turn_finished_ms = 0
        self.turn_count = 0
        self.abort_count = 0
        self.audio_capture_enabled = False
        self.audio_capture_reason = ""
        self.audio_capture_started_ms = 0
        self.audio_capture_last_frame_ms = 0
        self.audio_capture_bytes = 0
        self.audio_capture_chunks = 0
        self.audio_capture_format = ""
        self.audio_capture_sample_rate = 16000
        self.audio_capture_truncated = False
        self.audio_capture_drop_count = 0
        self.audio_capture_max_bytes = 65536
        self.audio_capture_buffer = []
        self.last_audio_capture = {}
        self._state_emotions = {
            "idle": "neutral",
            "wake": "surprised",
            "listening": "relaxed",
            "thinking": "thinking",
            "speaking": "happy",
            "aborting": "confused",
            "error": "confused",
            "stopped": "sleepy",
        }

    def _acquire(self):
        if self._lock is not None:
            self._lock.acquire()

    def _release(self):
        if self._lock is not None:
            try:
                self._lock.release()
            except Exception:
                pass

    def _string(self, value):
        if value is None:
            return ""
        try:
            return str(value)
        except Exception:
            return ""

    def configure(
        self,
        enabled=None,
        auto_start=None,
        audio_enabled=None,
        transcript_provider=None,
        reply_handler=None,
        speaker=None,
    ):
        if enabled is not None:
            self.enabled = bool(enabled)
        if auto_start is not None:
            self.auto_start = bool(auto_start)
        if audio_enabled is not None:
            self.audio_enabled = bool(audio_enabled)
        if transcript_provider is not None:
            self.transcript_provider = transcript_provider
        if reply_handler is not None:
            self.reply_handler = reply_handler
        if speaker is not None:
            self.speaker = speaker
        return self.snapshot()

    def bind_runtime(self, runtime):
        self.runtime = runtime
        return True

    def _voice_runtime(self):
        runtime = self.runtime
        if runtime is None or (not hasattr(runtime, "voice")):
            return None
        return runtime.voice

    def _note_error(self, message):
        self.last_error = self._string(message).strip()
        self.last_error_ms = _ticks_ms()
        return self.last_error

    def _show_state(self, state):
        if self.ui is None:
            return False
        emotion = self._state_emotions.get(state) or "neutral"
        if state == "speaking":
            directive_emotion = self._directive_emotion(self.last_voice_directive)
            if directive_emotion:
                emotion = directive_emotion
        try:
            self.ui.show_emotion(emotion)
            return True
        except Exception:
            return False

    def _state_caption(self, state):
        mapping = {
            "idle": "READY",
            "wake": "WAKE",
            "listening": "LISTENING",
            "thinking": "THINKING",
            "speaking": "REPLY",
            "aborting": "ABORTING",
            "error": "ERROR",
            "stopped": "STOPPED",
        }
        text = mapping.get(self._string(state).strip())
        if text:
            return text
        raw = self._string(state).strip().upper()
        if raw:
            return raw
        return "READY"

    def _show_status_text(self, state):
        if self.ui is None or not hasattr(self.ui, "show_status"):
            return False
        try:
            self.ui.show_status(self._state_caption(state))
            return True
        except Exception:
            return False

    def _show_message_text(self, text):
        if self.ui is None or not hasattr(self.ui, "show_message"):
            return False
        try:
            self.ui.show_message(text)
            return True
        except Exception:
            return False

    def _set_state(self, state, reason=""):
        self._acquire()
        try:
            self.state = self._string(state).strip() or "idle"
            self.state_reason = self._string(reason).strip()
            self.state_changed_ms = _ticks_ms()
        finally:
            self._release()
        self._show_state(self.state)
        self._show_status_text(self.state)
        return self.state

    def _directive_emotion(self, directive):
        if not isinstance(directive, dict):
            return ""
        keys = ["emotion", "emoji", "expression", "mood"]
        index = 0
        while index < len(keys):
            value = self._string(directive.get(keys[index])).strip()
            if value:
                return value
            index += 1
        return ""

    def _normalize_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        text = self._string(value).strip().lower()
        if text in ("1", "true", "yes", "on", "start", "speech", "speaking", "begin"):
            return True
        if text in ("0", "false", "no", "off", "stop", "end", "silence", "idle"):
            return False
        return bool(value)

    def _current_audio_capture_summary_locked(self, reason=""):
        now = _ticks_ms()
        started_ms = int(self.audio_capture_started_ms or 0)
        duration_ms = 0
        if started_ms > 0:
            duration_ms = _ticks_diff(now, started_ms)
        return {
            "enabled": bool(self.audio_capture_enabled),
            "reason": self._string(reason or self.audio_capture_reason).strip(),
            "started_ms": started_ms,
            "last_frame_ms": int(self.audio_capture_last_frame_ms or 0),
            "bytes": int(self.audio_capture_bytes or 0),
            "chunks": int(self.audio_capture_chunks or 0),
            "format": self._string(self.audio_capture_format).strip(),
            "sample_rate": int(self.audio_capture_sample_rate or 16000),
            "truncated": bool(self.audio_capture_truncated),
            "drop_count": int(self.audio_capture_drop_count or 0),
            "duration_ms": int(duration_ms or 0),
        }

    def _audio_capture_reset_locked(self):
        self.audio_capture_enabled = False
        self.audio_capture_reason = ""
        self.audio_capture_started_ms = 0
        self.audio_capture_last_frame_ms = 0
        self.audio_capture_bytes = 0
        self.audio_capture_chunks = 0
        self.audio_capture_format = ""
        self.audio_capture_sample_rate = 16000
        self.audio_capture_truncated = False
        self.audio_capture_drop_count = 0
        self.audio_capture_buffer = []
        return True

    def _audio_capture_begin(self, reason):
        format_name = ""
        if self.audio is not None:
            format_name = _audio_format_from_mode(getattr(self.audio, "stream_mode", ""))
        self._acquire()
        try:
            self._audio_capture_reset_locked()
            self.audio_capture_enabled = True
            self.audio_capture_reason = self._string(reason).strip()
            self.audio_capture_started_ms = _ticks_ms()
            self.audio_capture_last_frame_ms = self.audio_capture_started_ms
            self.audio_capture_format = format_name
            self.audio_capture_sample_rate = 16000
        finally:
            self._release()
        return True

    def _audio_capture_cancel(self, reason):
        self._acquire()
        try:
            summary = self._current_audio_capture_summary_locked(reason)
            summary["cancelled"] = True
            self.last_audio_capture = summary
            self._audio_capture_reset_locked()
        finally:
            self._release()
        return summary

    def _join_audio_chunks(self, chunks):
        if not chunks:
            return b""
        try:
            return b"".join(chunks)
        except Exception:
            pass
        out = bytearray()
        index = 0
        while index < len(chunks):
            try:
                out.extend(chunks[index])
            except Exception:
                pass
            index += 1
        return bytes(out)

    def take_audio_capture(self, reason="provider"):
        self._acquire()
        try:
            summary = self._current_audio_capture_summary_locked(reason)
            chunks = self.audio_capture_buffer
            self.last_audio_capture = summary
            self._audio_capture_reset_locked()
        finally:
            self._release()
        payload = {}
        for key in summary:
            payload[key] = summary[key]
        payload["data"] = self._join_audio_chunks(chunks)
        return payload

    def audio_capture_snapshot(self):
        self._acquire()
        try:
            data = self._current_audio_capture_summary_locked()
        finally:
            self._release()
        return data

    def _push_transcript(self, job):
        self._acquire()
        try:
            self.pending_transcripts.append(job)
        finally:
            self._release()
        return len(self.pending_transcripts)

    def _pop_transcript(self):
        self._acquire()
        try:
            if not self.pending_transcripts:
                return None
            return self.pending_transcripts.pop(0)
        finally:
            self._release()

    def _has_pending_transcripts(self):
        self._acquire()
        try:
            return bool(self.pending_transcripts)
        finally:
            self._release()

    def _clear_pending_inputs(self):
        self._acquire()
        try:
            self.pending_kws = 0
            self.pending_vad_begin = 0
            self.pending_vad_end = 0
            self.pending_transcripts = []
        finally:
            self._release()
        return True

    def _normalize_transcript_job(self, payload, default_source):
        if isinstance(payload, dict):
            text = self._string(payload.get("text")).strip()
            if not text:
                return None
            return {
                "text": text,
                "source": self._string(payload.get("source") or default_source).strip() or default_source,
                "meta": payload,
                "queued_ms": _ticks_ms(),
            }
        text = self._string(payload).strip()
        if not text:
            return None
        return {
            "text": text,
            "source": self._string(default_source).strip() or "manual",
            "meta": {},
            "queued_ms": _ticks_ms(),
        }

    def _resolve_provider_transcript(self, reason, capture=None):
        provider = self.transcript_provider
        if provider is None:
            return None
        context = reason
        if not isinstance(context, dict):
            context = {"reason": reason}
        if capture is None:
            capture = self.take_audio_capture("provider")
        if isinstance(capture, dict):
            audio_meta = {}
            for key in capture:
                if key == "data":
                    continue
                audio_meta[key] = capture[key]
            context["audio"] = audio_meta
        try:
            try:
                payload = provider(self, context, capture)
            except TypeError:
                payload = provider(self, context)
        except Exception as e:
            self._note_error("transcript_provider: " + self._string(e))
            return None
        return self._normalize_transcript_job(payload, "provider")

    def _has_audio(self):
        return bool(self.audio_enabled) and self.audio is not None and bool(getattr(self.audio, "supported", False))

    def start(self):
        self.enabled = True
        if self.active:
            return self.snapshot()
        self.active = True
        if self._has_audio():
            try:
                self.audio.set_frame_callback(self._on_audio_frame)
            except Exception as e:
                self._note_error("set_frame_callback: " + self._string(e))
            try:
                self.audio.set_kws_callback(self._on_kws)
            except Exception as e:
                self._note_error("set_kws_callback: " + self._string(e))
            try:
                self.audio.set_vad_callback(self._on_vad)
            except Exception as e:
                self._note_error("set_vad_callback: " + self._string(e))
            try:
                self.audio.start_kws()
                self.kws_running = True
            except Exception as e:
                self.kws_running = False
                self._note_error("start_kws: " + self._string(e))
        self._set_state("idle", "started")
        return self.snapshot()

    def stop(self):
        self.auto_started = False
        self.active = False
        self.pending_listen_after_abort = False
        self.abort_inflight = False
        self._clear_pending_inputs()
        self._audio_capture_cancel("stop")
        self._stop_vad()
        self._stop_kws()
        self._set_state("stopped", "stopped")
        return self.snapshot()

    def _stop_kws(self):
        if not self._has_audio() or not self.kws_running:
            self.kws_running = False
            return False
        try:
            self.audio.stop_kws()
        except Exception as e:
            self._note_error("stop_kws: " + self._string(e))
        self.kws_running = False
        return True

    def _start_kws(self):
        if not self._has_audio():
            return False
        if self.kws_running:
            return True
        try:
            self.audio.start_kws()
            self.kws_running = True
            return True
        except Exception as e:
            self.kws_running = False
            self._note_error("start_kws: " + self._string(e))
            return False

    def _stop_vad(self):
        if not self._has_audio() or not self.vad_running:
            self.vad_running = False
            return False
        try:
            self.audio.stop_vad()
        except Exception as e:
            self._note_error("stop_vad: " + self._string(e))
        self.vad_running = False
        return True

    def _start_vad(self):
        if not self._has_audio():
            return False
        if self.vad_running:
            return True
        try:
            self.audio.start_vad()
            self.vad_running = True
            return True
        except Exception as e:
            self.vad_running = False
            self._note_error("start_vad: " + self._string(e))
            return False

    def _on_kws(self, event):
        self._acquire()
        try:
            self.last_kws_event = event
            self.pending_kws = self.pending_kws + 1
        finally:
            self._release()
        return True

    def _on_vad(self, state):
        is_speech = self._normalize_bool(state)
        self._acquire()
        try:
            self.last_vad_event = state
            if is_speech:
                self.pending_vad_begin = self.pending_vad_begin + 1
            else:
                self.pending_vad_end = self.pending_vad_end + 1
        finally:
            self._release()
        return True

    def _on_audio_frame(self, data):
        if (not self.audio_capture_enabled) or (not data):
            return False
        accepted = False
        size = 0
        try:
            size = len(data)
        except Exception:
            size = 0
        if size <= 0:
            return False
        self._acquire()
        try:
            if self.audio_capture_enabled:
                self.audio_capture_last_frame_ms = _ticks_ms()
                next_bytes = self.audio_capture_bytes + size
                if next_bytes <= self.audio_capture_max_bytes:
                    self.audio_capture_buffer.append(data)
                    self.audio_capture_bytes = next_bytes
                    self.audio_capture_chunks = self.audio_capture_chunks + 1
                    accepted = True
                else:
                    self.audio_capture_truncated = True
                    self.audio_capture_drop_count = self.audio_capture_drop_count + 1
        finally:
            self._release()
        return accepted

    def _begin_listening(self, reason):
        if not self.active:
            return False
        try:
            if self._has_audio():
                self.audio.stop()
        except Exception:
            pass
        self._stop_kws()
        if self._has_audio():
            try:
                self.audio.open_stream()
            except Exception as e:
                self._note_error("open_stream: " + self._string(e))
        self._audio_capture_begin(reason)
        self._start_vad()
        self._set_state("listening", reason)
        self._show_message_text("")
        return True

    def _handle_kws(self):
        if not self.active:
            return False
        if self.worker_busy:
            self.pending_listen_after_abort = True
            self.abort("wakeword")
            return True
        return self._begin_listening("wakeword")

    def _handle_vad_begin(self):
        if not self.active:
            return False
        if self.state in ("thinking", "speaking", "aborting"):
            return False
        self._set_state("listening", "speech")
        return True

    def _handle_vad_end(self):
        if not self.active:
            return False
        self._stop_vad()
        capture = self.take_audio_capture("vad_end")
        if self.worker_busy:
            return False
        if self._has_pending_transcripts():
            return True
        job = self._resolve_provider_transcript(
            {"reason": "vad_end", "vad_event": self.last_vad_event},
            capture=capture,
        )
        if job is None:
            self._set_state("idle", "transcript-missing")
            return False
        self._push_transcript(job)
        return True

    def inject_transcript(self, text, source="manual"):
        if not self.active:
            self.start()
        job = self._normalize_transcript_job({"text": text, "source": source}, source or "manual")
        if job is None:
            raise Exception("text required")
        if self.vad_running:
            self._stop_vad()
        self._audio_capture_cancel("inject")
        self._push_transcript(job)
        if self.state in ("idle", "wake", "stopped"):
            self._set_state("listening", "transcript-queued")
        return self.snapshot()

    def begin_listening(self, reason="manual"):
        if not self.active:
            self.start()
        if self.worker_busy:
            return False
        ok = self._begin_listening(reason or "manual")
        if ok:
            self._set_state("listening", reason or "manual")
        return ok

    def _next_turn_job(self):
        if self.worker_busy:
            return None
        return self._pop_transcript()

    def _runtime_voice_chat(self, job):
        voice = self._voice_runtime()
        if voice is None:
            raise Exception("runtime voice unavailable")
        return voice.chat(job.get("text") or "")

    def _runtime_voice_abort(self):
        voice = self._voice_runtime()
        if voice is None:
            return {"ok": False, "status": "voice-unavailable"}
        return voice.abort()

    def _default_reply_handler(self, result):
        directive = result.get("voice_directive") or {}
        emotion = self._directive_emotion(directive)
        if emotion:
            try:
                self.ui.show_emotion(emotion)
            except Exception:
                pass
        reply_text = self._string(result.get("reply_text")).strip()
        if reply_text:
            try:
                print("[qpyclaw-voice] " + reply_text)
            except Exception:
                pass
            self._show_message_text(reply_text)
        return {"emotion": emotion, "reply_text": reply_text}

    def _run_speaker(self, result):
        speaker = self.speaker
        if speaker is None:
            return {"played": False}
        # Release input-side audio ownership before playback. Some EC800M
        # firmware builds will return audio error 28 if KWS/VAD or the
        # capture stream is still active when starting speaker playback.
        self._audio_capture_cancel("speaker")
        self._stop_vad()
        self._stop_kws()
        if self._has_audio():
            try:
                self.audio.close_stream()
            except Exception:
                pass
            try:
                self.audio.stop()
            except Exception:
                pass
        return speaker(self, result)

    def _handle_reply(self, result):
        handler = self.reply_handler
        if handler is None:
            handler = self._default_reply_handler
        try:
            handler_result = handler(self, result)
        except TypeError:
            handler_result = handler(result)
        speaker_result = self._run_speaker(result)
        return {
            "handler": handler_result,
            "speaker": speaker_result,
        }

    def _finish_turn(self, ok, result, error_text):
        if ok:
            self.last_result_ok = True
            self.last_result = result
            self.last_reply_text = self._string(result.get("reply_text")).strip()
            directive = result.get("voice_directive")
            if isinstance(directive, dict):
                self.last_voice_directive = directive
            else:
                self.last_voice_directive = {}
            self._set_state("speaking", "reply-ready")
            try:
                reply_result = self._handle_reply(result)
                if isinstance(reply_result, dict):
                    self.last_reply_handler_result = reply_result.get("handler") or {}
                    self.last_speaker_result = reply_result.get("speaker") or {}
                else:
                    self.last_reply_handler_result = {}
                    self.last_speaker_result = {}
            except Exception as e:
                self.last_reply_handler_result = {}
                self.last_speaker_result = {
                    "played": False,
                    "reason": "reply_handler_exception",
                    "error": self._string(e),
                }
                self._note_error("reply_handler: " + self._string(e))
            if self.pending_listen_after_abort and self.active:
                self.pending_listen_after_abort = False
                self._begin_listening("wake-restart")
            elif self.active:
                self._set_state("idle", "reply-finished")
            else:
                self._set_state("stopped", "reply-finished")
            return True

        self.last_result_ok = False
        self.last_result = {
            "ok": False,
            "status": "error",
            "error": self._string(error_text).strip(),
        }
        self.last_reply_text = ""
        self.last_voice_directive = {}
        self.last_reply_handler_result = {}
        self.last_speaker_result = {}
        self._note_error(error_text)
        if self.pending_listen_after_abort and self.active:
            self.pending_listen_after_abort = False
            self._begin_listening("wake-restart")
        else:
            self._set_state("error", "voice-failed")
            self._show_message_text(error_text)
        return False

    def _run_turn_job(self, job):
        ok = False
        result = None
        error_text = ""
        try:
            result = self._runtime_voice_chat(job)
            ok = bool(isinstance(result, dict) and result.get("ok"))
            if not ok:
                error_text = self._string((result or {}).get("status") or "voice chat failed")
        except Exception as e:
            error_text = self._string(e)
        finish_ok = False
        try:
            finish_ok = self._finish_turn(ok, result or {}, error_text)
        finally:
            self._acquire()
            try:
                self.worker_busy = False
                self.worker_threaded = False
                self.last_turn_finished_ms = _ticks_ms()
            finally:
                self._release()
        return finish_ok

    def _start_turn(self, job):
        if job is None:
            return False
        self._acquire()
        try:
            if self.worker_busy:
                return False
            self.worker_busy = True
            self.worker_threaded = False
            self.turn_count = self.turn_count + 1
            self.last_turn_started_ms = _ticks_ms()
            self.last_turn_finished_ms = 0
            self.last_transcript = self._string(job.get("text")).strip()
            self.last_transcript_source = self._string(job.get("source") or "manual").strip() or "manual"
        finally:
            self._release()
        self._set_state("thinking", self.last_transcript_source)
        self._show_message_text(self.last_transcript)
        if self.thread_supported:
            try:
                self.worker_threaded = True
                self._thread.start_new_thread(self._run_turn_job, (job,))
                return True
            except Exception as e:
                self.worker_threaded = False
                self._note_error("voice_thread: " + self._string(e))
        return self._run_turn_job(job)

    def _run_abort_job(self):
        error_text = ""
        try:
            self._runtime_voice_abort()
        except Exception as e:
            error_text = self._string(e)
        self._acquire()
        try:
            self.abort_inflight = False
        finally:
            self._release()
        if error_text and (not self.worker_busy):
            self._note_error("abort: " + error_text)
        if (not self.worker_busy) and self.active:
            if self.pending_listen_after_abort:
                self.pending_listen_after_abort = False
                self._begin_listening("abort-finished")
            else:
                self._set_state("idle", "aborted")
        return True

    def abort(self, reason="manual"):
        self.abort_count = self.abort_count + 1
        self.pending_kws = 0
        self.pending_vad_begin = 0
        self.pending_vad_end = 0
        self._audio_capture_cancel(reason)
        self._stop_vad()
        try:
            if self._has_audio():
                self.audio.stop()
        except Exception:
            pass
        self.abort_inflight = True
        self._set_state("aborting", reason)
        if self.thread_supported:
            try:
                self._thread.start_new_thread(self._run_abort_job, ())
                return self.snapshot()
            except Exception as e:
                self._note_error("abort_thread: " + self._string(e))
        self._run_abort_job()
        return self.snapshot()

    def _state_timed_out(self):
        now = _ticks_ms()
        if self.state == "wake":
            return _ticks_diff(now, self.state_changed_ms) >= self.wake_timeout_ms
        if self.state == "listening":
            return _ticks_diff(now, self.state_changed_ms) >= self.listen_timeout_ms
        return False

    def _handle_timeouts(self):
        if not self._state_timed_out():
            return False
        self._stop_vad()
        if self.state == "listening":
            capture = self.take_audio_capture("timeout")
            if self.worker_busy:
                return False
            if self._has_pending_transcripts():
                return True
            job = None
            if isinstance(capture, dict) and int(capture.get("bytes") or 0) > 0:
                job = self._resolve_provider_transcript(
                    {"reason": "timeout", "vad_event": self.last_vad_event},
                    capture=capture,
                )
            if job is not None:
                self._push_transcript(job)
                return True
        else:
            self._audio_capture_cancel("timeout")
        self._set_state("idle", "listen-timeout")
        return True

    def step(self):
        if self.enabled and self.auto_start and (not self.active):
            self.start()
            self.auto_started = True
        if not self.active:
            return False
        while self.pending_kws > 0:
            self.pending_kws = self.pending_kws - 1
            self._handle_kws()
        while self.pending_vad_begin > 0:
            self.pending_vad_begin = self.pending_vad_begin - 1
            self._handle_vad_begin()
        while self.pending_vad_end > 0:
            self.pending_vad_end = self.pending_vad_end - 1
            self._handle_vad_end()
        if (not self.worker_busy) and (not self.vad_running):
            job = self._next_turn_job()
            if job is not None:
                self._start_turn(job)
        self._handle_timeouts()
        if (
            self._has_audio()
            and self.active
            and (not self.kws_running)
            and (not self.vad_running)
            and (not self.worker_busy)
            and self.state in ("idle", "error")
        ):
            self._start_kws()
        return True

    def snapshot(self):
        voice = self._voice_runtime()
        voice_online = None
        voice_available = voice is not None
        if voice_available:
            try:
                voice_online = bool(getattr(voice, "online", False))
            except Exception:
                voice_online = None
        runtime_online = False
        if self.runtime is not None and hasattr(self.runtime, "state"):
            try:
                runtime_online = bool(getattr(self.runtime.state, "online", False))
            except Exception:
                runtime_online = False
        return {
            "available": True,
            "enabled": bool(self.enabled),
            "auto_start": bool(self.auto_start),
            "audio_enabled": bool(self.audio_enabled),
            "auto_started": bool(self.auto_started),
            "active": bool(self.active),
            "state": self.state,
            "state_reason": self.state_reason,
            "state_changed_ms": self.state_changed_ms,
            "kws_running": bool(self.kws_running),
            "vad_running": bool(self.vad_running),
            "worker_busy": bool(self.worker_busy),
            "worker_threaded": bool(self.worker_threaded),
            "abort_inflight": bool(self.abort_inflight),
            "pending_kws": int(self.pending_kws),
            "pending_vad_begin": int(self.pending_vad_begin),
            "pending_vad_end": int(self.pending_vad_end),
            "pending_transcripts": len(self.pending_transcripts),
            "last_kws_event": self.last_kws_event,
            "last_vad_event": self.last_vad_event,
            "audio_capture": self.audio_capture_snapshot(),
            "last_audio_capture": self.last_audio_capture,
            "last_transcript": self.last_transcript,
            "last_transcript_source": self.last_transcript_source,
            "last_reply_text": self.last_reply_text,
            "last_voice_directive": self.last_voice_directive,
            "last_reply_handler_result": self.last_reply_handler_result,
            "last_speaker_result": self.last_speaker_result,
            "last_result_ok": self.last_result_ok,
            "last_result": self.last_result,
            "last_error": self.last_error,
            "last_error_ms": self.last_error_ms,
            "last_turn_started_ms": self.last_turn_started_ms,
            "last_turn_finished_ms": self.last_turn_finished_ms,
            "turn_count": self.turn_count,
            "abort_count": self.abort_count,
            "runtime_attached": self.runtime is not None,
            "runtime_online": runtime_online,
            "voice_available": voice_available,
            "voice_online": voice_online,
            "thread_supported": bool(self.thread_supported),
        }
