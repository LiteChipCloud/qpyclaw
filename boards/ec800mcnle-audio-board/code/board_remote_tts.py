def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


ujson = _safe_import("ujson")
ubinascii = _safe_import("ubinascii")
request = _safe_import("request")
utime = _safe_import("utime")
uos = _safe_import("uos")


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _ticks_ms():
    if utime is None:
        return 0
    try:
        return utime.ticks_ms()
    except Exception:
        try:
            return int(utime.time() * 1000)
        except Exception:
            return 0


def _sleep_ms(delay_ms):
    if utime is None:
        return
    try:
        utime.sleep_ms(int(delay_ms or 0))
    except Exception:
        pass


def _loads(text):
    if ujson is None:
        raise Exception("ujson unavailable")
    return ujson.loads(text)


def _dumps(data):
    if ujson is None:
        raise Exception("ujson unavailable")
    return ujson.dumps(data)


def _cfg_string(cfg, name, default=""):
    return _string(getattr(cfg, name, default)).strip()


def _cfg_int(cfg, name, default=0):
    try:
        return int(getattr(cfg, name, default))
    except Exception:
        try:
            return int(default)
        except Exception:
            return 0


def _cfg_float(cfg, name, default=0):
    try:
        return float(getattr(cfg, name, default))
    except Exception:
        try:
            return float(default)
        except Exception:
            return 0.0


def _cfg_bool(cfg, name, default=False):
    return _normalize_bool(getattr(cfg, name, default), default)


def _normalize_bool(value, default=False):
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


def _response_text(resp):
    text = getattr(resp, "text", "")
    if isinstance(text, (bytes, bytearray)):
        try:
            return text.decode("utf-8")
        except Exception:
            return _string(text)
    if isinstance(text, str):
        return text
    try:
        chunks = []
        for item in text:
            chunks.append(_string(item))
        return "".join(chunks)
    except Exception:
        return _string(text)


def _response_json(resp):
    json_fn = getattr(resp, "json", None)
    if json_fn:
        try:
            return json_fn()
        except Exception:
            pass
    text = _response_text(resp)
    if not text:
        return {}
    try:
        return _loads(text)
    except Exception:
        return {"text": text}


def _response_error_detail(resp):
    payload = _response_json(resp)
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, (dict, list)):
            try:
                return _dumps(detail)
            except Exception:
                return _string(detail)
        if detail is not None:
            return _string(detail)
        error = payload.get("error")
        if error is not None:
            return _string(error)
        text = payload.get("text")
        if text is not None:
            return _string(text)
        try:
            return _dumps(payload)
        except Exception:
            return _string(payload)
    return _string(payload)


def _response_close(resp):
    if resp is None:
        return
    try:
        resp.close()
    except Exception:
        pass


def _extract_audio(payload):
    if isinstance(payload, dict):
        audio = payload.get("audio")
        if isinstance(audio, dict):
            return audio
        nested = ["data", "result", "payload", "output"]
        index = 0
        while index < len(nested):
            item = payload.get(nested[index])
            audio = _extract_audio(item)
            if audio:
                return audio
            index += 1
    return {}


def _format_extension(format_name):
    name = _string(format_name).strip().lower()
    if name == "wav":
        return ".wav"
    if name == "mp3":
        return ".mp3"
    if name == "pcm":
        return ".pcm"
    if name == "amr":
        return ".amr"
    if name == "aac":
        return ".aac"
    return ".bin"


def _derive_tts_url(asr_url):
    text = _string(asr_url).strip()
    if text.endswith("/api/asr"):
        return text[:-8] + "/api/tts"
    return ""


def _derive_tts_stream_url(raw_url):
    text = _string(raw_url).strip()
    if not text:
        return ""
    if text.startswith("ws://") or text.startswith("wss://"):
        if text.endswith("/api/tts"):
            return text[:-8] + "/ws/tts"
        return text
    if text.startswith("http://"):
        text = "ws://" + text[7:]
    elif text.startswith("https://"):
        text = "wss://" + text[8:]
    if text.endswith("/api/tts"):
        return text[:-8] + "/ws/tts"
    if text.endswith("/api/asr"):
        return text[:-8] + "/ws/tts"
    return text


def _path_pair(raw_path, format_name):
    path = _string(raw_path).replace("\\", "/").strip()
    if not path:
        path = "/usr/qpyclaw/voice_reply" + _format_extension(format_name)
    if path.startswith("/usr/"):
        return path, "U:/" + path[5:]
    if path.startswith("usr/"):
        return path, "U:/" + path[4:]
    if path.startswith("U:/"):
        return path, path
    if path.startswith("U:"):
        return path, path
    if path.startswith("/"):
        return "U:" + path, "U:" + path
    return "U:/" + path.lstrip("/"), "U:/" + path.lstrip("/")


def _ensure_parent_dir(path):
    if uos is None:
        return False
    text = _string(path).replace("\\", "/").strip()
    if not text:
        return False
    parts = text.split("/")
    if len(parts) <= 1:
        return True
    current = parts[0]
    index = 1
    if index < len(parts) and parts[index] == "":
        current = current + "/"
        index = index + 1
    while index < len(parts) - 1:
        part = parts[index]
        if part:
            if current.endswith("/"):
                current = current + part
            else:
                current = current + "/" + part
            try:
                uos.stat(current)
            except Exception:
                try:
                    uos.mkdir(current)
                except Exception:
                    pass
        index = index + 1
    return True


def _write_binary(path, data):
    _ensure_parent_dir(path)
    handle = open(path, "wb")
    try:
        handle.write(data)
    finally:
        handle.close()
    return True


def _decode_base64_audio(payload):
    if ubinascii is None or not hasattr(ubinascii, "a2b_base64"):
        raise Exception("ubinascii.a2b_base64 unavailable")
    text = _string(payload).strip()
    if not text:
        raise Exception("tts audio missing")
    try:
        return ubinascii.a2b_base64(text)
    except Exception as e:
        raise Exception("tts audio base64 decode failed: " + _string(e))


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        try:
            return int(default)
        except Exception:
            return 0


def _directive_value(directive, names, default=None):
    if not isinstance(directive, dict):
        return default
    index = 0
    while index < len(names):
        if names[index] in directive:
            return directive.get(names[index])
        index += 1
    return default


def _clean_payload(data):
    if not isinstance(data, dict):
        return data
    cleaned = {}
    for key in data:
        value = data.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            cleaned[key] = text
            continue
        if isinstance(value, dict):
            nested = _clean_payload(value)
            if nested:
                cleaned[key] = nested
            continue
        cleaned[key] = value
    return cleaned


class RemoteTtsSpeaker(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.provider_name = "remote_tts_http"
        self.last_request_ms = 0
        self.last_status_code = 0
        self.last_error = ""
        self.last_request_payload = {}
        self.last_response_detail = ""
        self.last_text = ""
        self.last_audio_bytes = 0
        self.last_audio_chunks = 0
        self.last_audio_format = ""
        self.last_cache_path = ""
        self.last_play_path = ""
        self.last_play_result = None
        self.last_wait_result = {}
        self.last_transport = ""
        self.last_stream_url = ""
        self.last_stream_request_id = ""
        self.last_stream_response_id = ""
        self.last_stream_error = ""
        self.last_stream_begin = {}
        self.last_stream_end = {}

    def snapshot(self):
        return {
            "provider": self.provider_name,
            "url": self._url(),
            "stream_url": self._stream_url(),
            "stream_enabled": bool(self._stream_enabled()),
            "last_request_ms": int(self.last_request_ms or 0),
            "last_status_code": int(self.last_status_code or 0),
            "last_error": self.last_error,
            "last_stream_error": self.last_stream_error,
            "last_request_payload": self.last_request_payload,
            "last_response_detail": self.last_response_detail,
            "last_text": self.last_text,
            "last_audio_bytes": int(self.last_audio_bytes or 0),
            "last_audio_chunks": int(self.last_audio_chunks or 0),
            "last_audio_format": self.last_audio_format,
            "last_cache_path": self.last_cache_path,
            "last_play_path": self.last_play_path,
            "last_play_result": self.last_play_result,
            "last_wait_result": self.last_wait_result,
            "last_transport": self.last_transport,
            "last_stream_request_id": self.last_stream_request_id,
            "last_stream_response_id": self.last_stream_response_id,
            "last_stream_begin": self.last_stream_begin,
            "last_stream_end": self.last_stream_end,
        }

    def _url(self):
        url = _cfg_string(self.cfg, "VOICE_TTS_HTTP_URL", "")
        if url:
            return url
        return _derive_tts_url(_cfg_string(self.cfg, "VOICE_ASR_HTTP_URL", ""))

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        token = _cfg_string(self.cfg, "VOICE_TTS_HTTP_AUTH_TOKEN", "")
        if not token:
            token = _cfg_string(self.cfg, "VOICE_ASR_HTTP_AUTH_TOKEN", "")
        if token:
            headers["Authorization"] = "Bearer " + token
        extra = getattr(self.cfg, "VOICE_TTS_HTTP_HEADERS", None)
        if not isinstance(extra, dict):
            extra = getattr(self.cfg, "VOICE_ASR_HTTP_HEADERS", None)
        if isinstance(extra, dict):
            for key in extra:
                headers[_string(key)] = _string(extra[key])
        return headers

    def _stream_url(self):
        text = _cfg_string(self.cfg, "VOICE_TTS_STREAM_WS_URL", "")
        if not text:
            text = _cfg_string(self.cfg, "VOICE_TTS_STREAM_URL", "")
        if text:
            return text
        return _derive_tts_stream_url(self._url() or _cfg_string(self.cfg, "VOICE_ASR_HTTP_URL", ""))

    def _stream_headers(self):
        headers = {}
        token = _cfg_string(self.cfg, "VOICE_TTS_STREAM_AUTH_TOKEN", "")
        if not token:
            token = _cfg_string(self.cfg, "VOICE_TTS_HTTP_AUTH_TOKEN", "")
        if not token:
            token = _cfg_string(self.cfg, "VOICE_ASR_HTTP_AUTH_TOKEN", "")
        if token:
            headers["Authorization"] = "Bearer " + token
        extra = getattr(self.cfg, "VOICE_TTS_STREAM_HEADERS", None)
        if not isinstance(extra, dict):
            extra = getattr(self.cfg, "VOICE_TTS_HTTP_HEADERS", None)
        if not isinstance(extra, dict):
            extra = getattr(self.cfg, "VOICE_ASR_HTTP_HEADERS", None)
        if isinstance(extra, dict):
            for key in extra:
                headers[_string(key)] = _string(extra[key])
        return headers

    def _payload(self, result):
        directive = result.get("voice_directive") or {}
        payload = {
            "text": self.last_text,
            "voice": _string(
                _directive_value(directive, ["voice", "speaker", "tts_voice"], None)
                or _cfg_string(self.cfg, "VOICE_TTS_HTTP_VOICE", "")
            ).strip()
            or None,
            "format": _cfg_string(self.cfg, "VOICE_TTS_HTTP_AUDIO_FORMAT", "mp3") or "mp3",
            "sampleRate": _cfg_int(self.cfg, "VOICE_TTS_HTTP_SAMPLE_RATE", 16000) or 16000,
        }
        if not _cfg_bool(self.cfg, "VOICE_TTS_HTTP_MINIMAL_PAYLOAD", True):
            payload["volume"] = _directive_value(directive, ["volume", "tts_volume"], None)
            payload["speechRate"] = _directive_value(
                directive,
                ["speech_rate", "speechRate"],
                _cfg_float(self.cfg, "VOICE_TTS_HTTP_SPEECH_RATE", 0),
            )
            payload["pitchRate"] = _directive_value(
                directive,
                ["pitch_rate", "pitchRate"],
                _cfg_float(self.cfg, "VOICE_TTS_HTTP_PITCH_RATE", 0),
            )
            payload["instructions"] = _string(
                _directive_value(directive, ["instructions", "tts_instructions"], "")
            ).strip() or None
            payload["meta"] = {
                "deviceId": _cfg_string(self.cfg, "DEVICE_ID", ""),
                "deviceName": _cfg_string(self.cfg, "DEVICE_NAME", ""),
                "boardProfile": _cfg_string(self.cfg, "BOARD_PROFILE", ""),
            }
        return _clean_payload(payload)

    def _stream_payload(self, result):
        directive = result.get("voice_directive") or {}
        request_id = "tts_" + _string(_ticks_ms())
        payload = {
            "requestId": request_id,
            "text": self.last_text,
            "voice": _string(
                _directive_value(directive, ["voice", "speaker", "tts_voice"], None)
                or _cfg_string(self.cfg, "VOICE_TTS_STREAM_VOICE", "")
                or _cfg_string(self.cfg, "VOICE_TTS_HTTP_VOICE", "")
            ).strip()
            or None,
            "format": _cfg_string(
                self.cfg,
                "VOICE_TTS_STREAM_AUDIO_FORMAT",
                _cfg_string(self.cfg, "VOICE_TTS_STREAM_FORMAT", "pcm"),
            )
            or "pcm",
            "sampleRate": _cfg_int(self.cfg, "VOICE_TTS_STREAM_SAMPLE_RATE", 16000) or 16000,
        }
        if not _cfg_bool(self.cfg, "VOICE_TTS_STREAM_MINIMAL_PAYLOAD", True):
            payload["volume"] = _directive_value(directive, ["volume", "tts_volume"], None)
            payload["speechRate"] = _directive_value(
                directive,
                ["speech_rate", "speechRate"],
                _cfg_float(self.cfg, "VOICE_TTS_HTTP_SPEECH_RATE", 0),
            )
            payload["pitchRate"] = _directive_value(
                directive,
                ["pitch_rate", "pitchRate"],
                _cfg_float(self.cfg, "VOICE_TTS_HTTP_PITCH_RATE", 0),
            )
            payload["instructions"] = _string(
                _directive_value(directive, ["instructions", "tts_instructions"], "")
            ).strip() or None
            payload["meta"] = {
                "deviceId": _cfg_string(self.cfg, "DEVICE_ID", ""),
                "deviceName": _cfg_string(self.cfg, "DEVICE_NAME", ""),
                "boardProfile": _cfg_string(self.cfg, "BOARD_PROFILE", ""),
            }
        return _clean_payload(payload)

    def _should_skip(self, result):
        directive = result.get("voice_directive") or {}
        if _normalize_bool(_directive_value(directive, ["mute", "silent"], False), False):
            return True
        speak = _directive_value(directive, ["speak", "tts"], None)
        if speak is not None and (not _normalize_bool(speak, True)):
            return True
        return False

    def _stream_enabled(self):
        enabled_value = getattr(self.cfg, "VOICE_TTS_STREAM_ENABLED", None)
        if enabled_value is not None:
            return _normalize_bool(enabled_value, False)
        if _cfg_string(self.cfg, "VOICE_TTS_STREAM_WS_URL", ""):
            return True
        if _cfg_string(self.cfg, "VOICE_TTS_STREAM_URL", ""):
            return True
        return False

    def _ws_bundle(self):
        module = _safe_import("qpyclaw_node")
        if module is None:
            raise Exception("qpyclaw_node unavailable")
        client_ctor = getattr(module, "WsClient", None)
        if client_ctor is None:
            raise Exception("WsClient unavailable")
        return {
            "client_ctor": client_ctor,
            "timeout_type": getattr(module, "WsTimeout", None),
            "closed_type": getattr(module, "WsClosed", None),
        }

    def _stream_audio_format(self, value):
        text = _string(value).strip().lower()
        if text in ("", "pcm", "wav", "wavpcm"):
            return "pcm"
        if text in ("opus", "raw-opus", "raw_opus", "raw-opu", "raw_opu"):
            return "opus"
        raise Exception("unsupported tts stream format: " + text)

    def _stream_drain_ms(self):
        value = getattr(self.cfg, "VOICE_TTS_STREAM_DRAIN_MS", None)
        if value is None:
            value = getattr(self.cfg, "VOICE_TTS_STREAM_END_GRACE_MS", 400)
        return max(0, _safe_int(value, 400))

    def _play_stream(self, controller, result):
        self.provider_name = "remote_tts_ws"
        audio = None
        if controller is not None:
            audio = getattr(controller, "audio", None)
        if audio is None or (not bool(getattr(audio, "supported", False))):
            return {"played": False, "reason": "audio_unavailable"}
        stream_url = self._stream_url()
        if not stream_url:
            return {"played": False, "reason": "tts_stream_url_missing"}

        self.last_transport = "ws"
        self.last_stream_url = stream_url
        self.last_stream_error = ""
        self.last_stream_request_id = ""
        self.last_stream_response_id = ""
        self.last_stream_begin = {}
        self.last_stream_end = {}

        bundle = self._ws_bundle()
        ws = bundle["client_ctor"]()
        ws_timeout_type = bundle.get("timeout_type")
        connect_timeout_sec = _cfg_int(self.cfg, "VOICE_TTS_STREAM_CONNECT_TIMEOUT_SEC", 12) or 12
        recv_timeout_ms = _cfg_int(
            self.cfg,
            "VOICE_TTS_STREAM_RECV_TIMEOUT_MS",
            _cfg_int(self.cfg, "VOICE_TTS_STREAM_TIMEOUT_MS", 15000),
        ) or 15000
        end_grace_ms = _cfg_int(self.cfg, "VOICE_TTS_STREAM_END_GRACE_MS", 300)
        close_after_play = _cfg_bool(self.cfg, "VOICE_TTS_STREAM_CLOSE_AFTER_PLAY", False)
        payload = self._stream_payload(result or {})
        self.last_request_payload = payload
        self.last_stream_request_id = _string(payload.get("requestId")).strip()
        self.last_audio_bytes = 0
        self.last_audio_chunks = 0
        self.last_audio_format = _string(payload.get("format")).strip()
        playback_format = self._stream_audio_format(self.last_audio_format or "pcm")
        playback_sample_rate = int(payload.get("sampleRate") or 16000)

        try:
            ws.connect(stream_url, connect_timeout_sec, headers=self._stream_headers())
            ws.send_text(_dumps(payload))
            try:
                audio.close_playback_stream()
            except Exception:
                pass

            got_end = False
            while True:
                try:
                    frame_text = ws.recv_text(recv_timeout_ms)
                except Exception as e:
                    if ws_timeout_type is not None and isinstance(e, ws_timeout_type):
                        raise Exception("tts stream recv timeout")
                    raise
                frame = _loads(frame_text)
                frame_type = _string(frame.get("type")).strip()
                if frame_type == "tts.begin":
                    self.last_stream_begin = frame
                    self.last_stream_response_id = _string(
                        frame.get("responseId") or frame.get("response_id")
                    ).strip()
                    if frame.get("format") is not None:
                        self.last_audio_format = _string(frame.get("format")).strip()
                        playback_format = self._stream_audio_format(self.last_audio_format)
                    if frame.get("sampleRate") is not None or frame.get("sample_rate") is not None:
                        playback_sample_rate = int(
                            frame.get("sampleRate") or frame.get("sample_rate") or playback_sample_rate
                        )
                    continue
                if frame_type == "tts.chunk":
                    chunk = _string(frame.get("delta") or frame.get("base64")).strip()
                    if not chunk:
                        continue
                    audio_bytes = _decode_base64_audio(chunk)
                    if audio_bytes:
                        try:
                            audio.open_playback_stream(playback_format, playback_sample_rate)
                        except Exception:
                            audio.open_playback_stream("pcm", playback_sample_rate)
                            playback_format = "pcm"
                            self.last_audio_format = playback_format
                        if hasattr(audio, "write_playback_frame"):
                            audio.write_playback_frame(audio_bytes)
                        else:
                            audio.write_frame(audio_bytes)
                        self.last_audio_chunks = self.last_audio_chunks + 1
                        self.last_audio_bytes = self.last_audio_bytes + len(audio_bytes)
                    continue
                if frame_type == "tts.end" or frame_type == "tts.done":
                    self.last_stream_end = frame
                    response_id = _string(
                        frame.get("responseId") or frame.get("response_id")
                    ).strip()
                    if response_id:
                        self.last_stream_response_id = response_id
                    got_end = True
                    break
                if frame_type == "tts.error":
                    detail = frame.get("error")
                    if isinstance(detail, (dict, list)):
                        try:
                            detail = _dumps(detail)
                        except Exception:
                            detail = _string(detail)
                    raise Exception(_string(detail) or "tts stream error")
            if not got_end:
                raise Exception("tts stream ended without end frame")
            if self.last_audio_chunks <= 0 or self.last_audio_bytes <= 0:
                raise Exception("tts stream audio missing")
            _sleep_ms(end_grace_ms)
            if close_after_play:
                try:
                    audio.close_playback_stream(_cfg_int(self.cfg, "VOICE_TTS_STREAM_DRAIN_MS", end_grace_ms))
                except Exception:
                    pass
            return {
                "played": True,
                "transport": "ws",
                "audio_bytes": self.last_audio_bytes,
                "audio_chunks": self.last_audio_chunks,
                "audio_format": self.last_audio_format,
                "stream_url": stream_url,
                "request_id": self.last_stream_request_id,
                "response_id": self.last_stream_response_id,
                "begin": self.last_stream_begin,
                "end": self.last_stream_end,
            }
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def _play_http(self, controller, result):
        self.last_transport = "http"
        self.provider_name = "remote_tts_http"
        self.last_status_code = 0
        self.last_error = ""
        self.last_response_detail = ""
        self.last_audio_bytes = 0
        self.last_audio_chunks = 0
        self.last_audio_format = ""
        self.last_cache_path = ""
        self.last_play_path = ""
        self.last_play_result = None
        self.last_wait_result = {}

        url = self._url()
        if not url:
            return {"played": False, "reason": "tts_url_missing"}
        if request is None:
            raise Exception("request module unavailable")
        audio = None
        if controller is not None:
            audio = getattr(controller, "audio", None)
        if audio is None or (not bool(getattr(audio, "supported", False))):
            return {"played": False, "reason": "audio_unavailable"}

        response = None
        try:
            body = self._payload(result or {})
            self.last_request_payload = body
            body_text = _dumps(body)
            headers = self._headers()
            try:
                response = request.post(url, data=body_text, headers=headers)
            except TypeError as e:
                if "buffer protocol" not in _string(e):
                    raise
                response = request.post(url, data=body_text.encode("utf-8"), headers=headers)
            self.last_status_code = int(getattr(response, "status_code", 0) or 0)
            if self.last_status_code != 200:
                self.last_response_detail = _response_error_detail(response)
                raise Exception(
                    "remote tts http "
                    + _string(self.last_status_code)
                    + ": "
                    + (self.last_response_detail or "unknown")
                )
            payload = _response_json(response)
            audio_payload = _extract_audio(payload)
            base64_text = _string(audio_payload.get("base64") or "").strip()
            if not base64_text:
                raise Exception("remote tts audio missing")
            format_name = _string(
                audio_payload.get("format")
                or body.get("format")
                or _cfg_string(self.cfg, "VOICE_TTS_HTTP_AUDIO_FORMAT", "mp3")
            ).strip() or "mp3"
            audio_bytes = _decode_base64_audio(base64_text)
            self.last_audio_bytes = len(audio_bytes)
            self.last_audio_chunks = 1
            self.last_audio_format = format_name
            cache_raw = _cfg_string(self.cfg, "VOICE_TTS_HTTP_CACHE_PATH", "")
            cache_path, play_path = _path_pair(cache_raw, format_name)
            self.last_cache_path = cache_path
            self.last_play_path = play_path
            _write_binary(cache_path, audio_bytes)
            try:
                audio.stop()
            except Exception:
                pass
            self.last_play_result = audio.play(play_path)
            wait_timeout_ms = _cfg_int(self.cfg, "VOICE_TTS_HTTP_PLAY_TIMEOUT_MS", 20000)
            self.last_wait_result = audio.wait_playback(wait_timeout_ms)
            if not self.last_wait_result.get("ok"):
                return {
                    "played": False,
                    "reason": "playback_timeout",
                    "transport": "http",
                    "status_code": self.last_status_code,
                    "audio_bytes": self.last_audio_bytes,
                    "audio_format": self.last_audio_format,
                    "cache_path": cache_path,
                    "play_path": play_path,
                    "play_result": self.last_play_result,
                    "wait_result": self.last_wait_result,
                }
            return {
                "played": True,
                "transport": "http",
                "status_code": self.last_status_code,
                "audio_bytes": self.last_audio_bytes,
                "audio_format": self.last_audio_format,
                "cache_path": cache_path,
                "play_path": play_path,
                "play_result": self.last_play_result,
                "wait_result": self.last_wait_result,
            }
        finally:
            _response_close(response)

    def __call__(self, controller, result):
        self.last_request_ms = _ticks_ms()
        self.last_error = ""
        self.last_stream_error = ""
        self.last_response_detail = ""
        self.last_text = _string((result or {}).get("reply_text")).strip()
        if not self.last_text:
            return {"played": False, "reason": "empty_reply_text"}
        if self._should_skip(result or {}):
            return {"played": False, "reason": "directive_skip"}

        if self._stream_enabled():
            try:
                return self._play_stream(controller, result)
            except Exception as e:
                self.last_stream_error = _string(e).strip()
                if not _cfg_bool(self.cfg, "VOICE_TTS_STREAM_FALLBACK_TO_HTTP", True):
                    self.last_error = self.last_stream_error
                    raise

        try:
            return self._play_http(controller, result)
        except Exception as e:
            self.last_error = _string(e).strip()
            raise
