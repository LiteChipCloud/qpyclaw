def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


ujson = _safe_import("ujson")
ubinascii = _safe_import("ubinascii")
request = _safe_import("request")
utime = _safe_import("utime")


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


def _normalize_text(value):
    text = _string(value).strip()
    if text:
        return text
    return ""


def _extract_text(payload):
    if isinstance(payload, dict):
        direct_keys = [
            "text",
            "transcript",
            "utterance",
            "result_text",
            "recognized_text",
        ]
        index = 0
        while index < len(direct_keys):
            text = _normalize_text(payload.get(direct_keys[index]))
            if text:
                return text
            index += 1
        nested_keys = [
            "data",
            "result",
            "asr",
            "output",
            "payload",
        ]
        index = 0
        while index < len(nested_keys):
            item = payload.get(nested_keys[index])
            text = _extract_text(item)
            if text:
                return text
            index += 1
        return ""
    if isinstance(payload, list):
        index = 0
        while index < len(payload):
            text = _extract_text(payload[index])
            if text:
                return text
            index += 1
        return ""
    return _normalize_text(payload)


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
        return {
            "text": text,
        }


def _encode_base64(data):
    if not data:
        return ""
    if ubinascii is None or not hasattr(ubinascii, "b2a_base64"):
        raise Exception("ubinascii.b2a_base64 unavailable")
    # Chunked encoding to avoid large contiguous memory allocation.
    # ubinascii.b2a_base64 on the full buffer can require ~1.4x the
    # input size as a single allocation which easily OOMs on EC800M.
    total = len(data)
    if total <= 3072:
        return ubinascii.b2a_base64(data).decode("utf-8").strip()
    parts = []
    offset = 0
    chunk = 3072  # must be multiple of 3 for base64 alignment
    while offset < total:
        end = offset + chunk
        if end > total:
            end = total
        parts.append(ubinascii.b2a_base64(data[offset:end]).decode("utf-8").strip())
        offset = end
    return "".join(parts)


class RemoteAsrTranscriptProvider(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.fixed_text = _cfg_string(self.cfg, "VOICE_ASR_FIXED_TRANSCRIPT", "")
        mode = _cfg_string(self.cfg, "VOICE_TRANSCRIPT_PROVIDER", "").lower()
        if self.fixed_text and mode in ("", "fixed", "mock", "smoke"):
            self.provider_name = "fixed_transcript"
        else:
            self.provider_name = "remote_asr_http"
        self.last_request_ms = 0
        self.last_status_code = 0
        self.last_error = ""
        self.last_audio_bytes = 0
        self.last_result_text = ""

    def snapshot(self):
        return {
            "provider": self.provider_name,
            "url": _cfg_string(self.cfg, "VOICE_ASR_HTTP_URL", ""),
            "fixed_text": bool(self.fixed_text),
            "last_request_ms": int(self.last_request_ms or 0),
            "last_status_code": int(self.last_status_code or 0),
            "last_error": self.last_error,
            "last_audio_bytes": int(self.last_audio_bytes or 0),
            "last_result_text": self.last_result_text,
        }

    def _headers(self):
        headers = {
            "Content-Type": "application/json",
        }
        token = _cfg_string(self.cfg, "VOICE_ASR_HTTP_AUTH_TOKEN", "")
        if token:
            headers["Authorization"] = "Bearer " + token
        extra = getattr(self.cfg, "VOICE_ASR_HTTP_HEADERS", None)
        if isinstance(extra, dict):
            for key in extra:
                headers[_string(key)] = _string(extra[key])
        return headers

    def _payload(self, controller, reason, capture):
        audio_bytes = capture.get("data") or b""
        capture["data"] = b""  # free ref early to help GC
        summary = {}
        for key in capture:
            if key == "data":
                continue
            summary[key] = capture[key]
        audio_len = len(audio_bytes)
        b64 = _encode_base64(audio_bytes)
        audio_bytes = None  # free raw bytes before building dict
        return {
            "provider": self.provider_name,
            "deviceId": _cfg_string(self.cfg, "DEVICE_ID", ""),
            "deviceName": _cfg_string(self.cfg, "DEVICE_NAME", ""),
            "boardProfile": _cfg_string(self.cfg, "BOARD_PROFILE", ""),
            "requestedAtMs": _ticks_ms(),
            "voiceState": _string(getattr(controller, "state", "")).strip(),
            "reason": reason,
            "audio": {
                "encoding": "base64",
                "format": _cfg_string(
                    self.cfg,
                    "VOICE_ASR_HTTP_AUDIO_FORMAT",
                    summary.get("format") or "oggopus",
                ),
                "sampleRate": _cfg_int(
                    self.cfg,
                    "VOICE_ASR_HTTP_SAMPLE_RATE",
                    summary.get("sample_rate") or 16000,
                ),
                "bytes": audio_len,
                "durationMs": int(summary.get("duration_ms") or 0),
                "chunks": int(summary.get("chunks") or 0),
                "truncated": bool(summary.get("truncated")),
                "base64": b64,
            },
        }

    def __call__(self, controller, reason, capture=None):
        if capture is None and controller is not None and hasattr(controller, "take_audio_capture"):
            capture = controller.take_audio_capture("remote_asr_http")
        if not isinstance(capture, dict):
            raise Exception("audio capture unavailable")
        audio_bytes = capture.get("data") or b""
        self.last_audio_bytes = int(len(audio_bytes))
        if self.last_audio_bytes <= 0:
            raise Exception("audio capture empty")
        if self.fixed_text:
            self.last_request_ms = _ticks_ms()
            self.last_status_code = 200
            self.last_error = ""
            self.last_result_text = self.fixed_text
            return {
                "text": self.fixed_text,
                "source": self.provider_name,
                "meta": {
                    "provider": self.provider_name,
                    "status_code": self.last_status_code,
                    "audio_bytes": self.last_audio_bytes,
                    "audio_format": capture.get("format") or "oggopus",
                    "audio_sample_rate": int(capture.get("sample_rate") or 16000),
                    "mode": "fixed",
                },
            }
        if request is None:
            raise Exception("request module unavailable")
        url = _cfg_string(self.cfg, "VOICE_ASR_HTTP_URL", "")
        if not url:
            raise Exception("VOICE_ASR_HTTP_URL missing")
        gc = _safe_import("gc")
        if gc is not None:
            gc.collect()
        body = self._payload(controller, reason, capture)
        capture = None  # free capture ref
        response = None
        self.last_request_ms = _ticks_ms()
        self.last_status_code = 0
        self.last_error = ""
        self.last_result_text = ""
        try:
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
                raise Exception("remote asr http " + _string(self.last_status_code))
            payload = _response_json(response)
            text = _extract_text(payload)
            if not text:
                raise Exception("remote asr transcript missing")
            self.last_result_text = text
            return {
                "text": text,
                "source": self.provider_name,
                "meta": {
                    "provider": self.provider_name,
                    "status_code": self.last_status_code,
                    "audio_bytes": self.last_audio_bytes,
                    "audio_format": body["audio"]["format"],
                    "audio_sample_rate": body["audio"]["sampleRate"],
                },
            }
        except Exception as e:
            self.last_error = _string(e).strip()
            raise
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
