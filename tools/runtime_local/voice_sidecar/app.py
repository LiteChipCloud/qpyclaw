#!/usr/bin/env python3
"""
qpyclaw DashScope voice sidecar.

This service keeps the device-side HTTP contract simple:
1. `/api/asr` accepts base64 audio payloads from qpyclaw-node.
2. `/api/tts` synthesizes reply text into base64 audio.
3. `/ws/tts` streams TTS audio delta frames to the device.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import hmac
import json
import logging
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("qpyclaw-voice-sidecar")

import dashscope
from dashscope.audio.asr import Recognition
from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime
from dashscope.audio.qwen_tts_realtime import QwenTtsRealtimeCallback
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import BaseModel
from pydantic import Field


APP_VERSION = "0.1.0"


def _env_text(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return int(default)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return float(default)


def _bool_value(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off"):
        return False
    return bool(default)


def _require_api_key() -> str:
    api_key = _env_text("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="DASHSCOPE_API_KEY missing")
    dashscope.api_key = api_key
    return api_key


def _optional_workspace() -> str | None:
    text = _env_text("DASHSCOPE_WORKSPACE_ID", "")
    if text:
        return text
    return None


def _extract_proxy_token(authorization: str | None) -> str:
    raw = str(authorization or "").strip()
    actual = raw
    if raw.lower().startswith("bearer "):
        actual = raw[7:].strip()
    return actual


def _is_proxy_authorized(authorization: str | None) -> bool:
    expected = _env_text("QPYCLAW_VOICE_PROXY_TOKEN", "")
    if not expected:
        return True
    actual = _extract_proxy_token(authorization)
    if not actual:
        return False
    return bool(hmac.compare_digest(actual, expected))


def _require_proxy_auth(authorization: str | None) -> None:
    if not _is_proxy_authorized(authorization):
        raise HTTPException(status_code=401, detail="unauthorized")


def _decode_base64_audio(text: str) -> bytes:
    payload = str(text or "").strip()
    if not payload:
        raise HTTPException(status_code=400, detail="audio.base64 required")
    try:
        return base64.b64decode(payload, validate=True)
    except binascii.Error:
        try:
            return base64.b64decode(payload)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid audio.base64") from exc


def _safe_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            out[str(key)] = _safe_jsonable(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_safe_jsonable(item) for item in value]
    return str(value)


def _is_ogg_container(audio_bytes: bytes) -> bool:
    """Check if audio bytes start with OggS magic header."""
    return len(audio_bytes) >= 4 and audio_bytes[:4] == b"OggS"


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _transcode_audio_to_wav(
    audio_bytes: bytes,
    input_suffix: str = ".opus",
    sample_rate: int = 16000,
) -> tuple[bytes, str]:
    """Transcode audio to PCM WAV via ffmpeg auto-probe.

    Returns ``(wav_bytes, info_string)``.  Raises HTTPException on failure.
    """
    if not _has_ffmpeg():
        raise HTTPException(status_code=500, detail="ffmpeg not available")
    fd_in, path_in = tempfile.mkstemp(prefix="qpy_asr_in_", suffix=input_suffix)
    fd_out, path_out = tempfile.mkstemp(prefix="qpy_asr_out_", suffix=".wav")
    os.close(fd_in)
    os.close(fd_out)
    try:
        with open(path_in, "wb") as f:
            f.write(audio_bytes)
        cmd = [
            "ffmpeg", "-y", "-i", path_in,
            "-ar", str(sample_rate), "-ac", "1",
            "-c:a", "pcm_s16le", "-f", "wav", path_out,
        ]
        cp = subprocess.run(cmd, capture_output=True, timeout=15)
        if cp.returncode != 0:
            stderr = (cp.stderr or b"").decode("utf-8", errors="replace")[:300]
            logger.warning("ffmpeg transcode failed (rc=%d): %s", cp.returncode, stderr)
            raise HTTPException(status_code=502, detail="ffmpeg transcode failed: " + stderr[:200])
        wav_bytes = Path(path_out).read_bytes()
        info = "transcode(%s→wav): in=%d wav=%d sr=%d" % (input_suffix, len(audio_bytes), len(wav_bytes), sample_rate)
        logger.info(info)
        return wav_bytes, info
    finally:
        for p in (path_in, path_out):
            try:
                os.remove(p)
            except Exception:
                pass


def _normalize_audio_format(value: str) -> tuple[str, str]:
    text = str(value or "").strip().lower()
    if text in ("wav", "wave"):
        return "wav", ".wav"
    if text in ("mp3",):
        return "mp3", ".mp3"
    if text in ("pcm", "pcm16"):
        return "pcm", ".pcm"
    if text in ("opus",):
        return "opus", ".opus"
    if text in ("oggopus", "ogg_opus", "ogg-opus", "ogg"):
        return "opus", ".ogg"
    if text in ("amr",):
        return "amr", ".amr"
    if text in ("aac",):
        return "aac", ".aac"
    if text in ("flac",):
        return "flac", ".flac"
    if text in ("m4a",):
        return "m4a", ".m4a"
    return text or "wav", ".bin"


def _flatten_asr_text(sentences: Any) -> str:
    if not isinstance(sentences, list):
        return ""
    parts = []
    for item in sentences:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if text:
            parts.append(text)
    return " ".join(parts).strip()


class AsrAudioPayload(BaseModel):
    encoding: str = "base64"
    format: str = "wav"
    sample_rate: int = Field(default=16000, alias="sampleRate")
    bytes_count: int | None = Field(default=None, alias="bytes")
    duration_ms: int | None = Field(default=None, alias="durationMs")
    chunks: int | None = None
    truncated: bool | None = None
    base64_audio: str = Field(alias="base64")

    model_config = {
        "populate_by_name": True,
    }


class AsrRequest(BaseModel):
    provider: str | None = None
    device_id: str | None = Field(default=None, alias="deviceId")
    device_name: str | None = Field(default=None, alias="deviceName")
    board_profile: str | None = Field(default=None, alias="boardProfile")
    requested_at_ms: int | None = Field(default=None, alias="requestedAtMs")
    voice_state: str | None = Field(default=None, alias="voiceState")
    reason: Any = None
    audio: AsrAudioPayload

    model_config = {
        "populate_by_name": True,
    }


class TtsRequest(BaseModel):
    text: str
    voice: str | None = None
    format: str | None = None
    sample_rate: int | None = Field(default=None, alias="sampleRate")
    volume: int | None = None
    speech_rate: float | None = Field(default=None, alias="speechRate")
    pitch_rate: float | None = Field(default=None, alias="pitchRate")
    instructions: str | None = None
    optimize_instructions: bool | None = Field(default=None, alias="optimizeInstructions")
    meta: dict[str, Any] | None = None

    model_config = {
        "populate_by_name": True,
    }


AsrAudioPayload.model_rebuild()
AsrRequest.model_rebuild()
TtsRequest.model_rebuild()


class _QwenTtsCollector(QwenTtsRealtimeCallback):
    def __init__(self) -> None:
        self.audio = bytearray()
        self.done = False
        self.error: dict[str, Any] | None = None
        self.events: list[dict[str, Any]] = []
        self.response_id = ""
        self.first_audio_delay_ms: float | None = None
        self._lock = threading.Lock()

    def on_open(self) -> None:
        with self._lock:
            self.events.append({"type": "open"})

    def on_close(self, close_status_code, close_msg) -> None:
        with self._lock:
            self.events.append(
                {
                    "type": "close",
                    "close_status_code": close_status_code,
                    "close_msg": str(close_msg),
                }
            )

    def on_event(self, message: dict[str, Any]) -> None:
        if not isinstance(message, dict):
            return
        event_type = str(message.get("type") or "")
        with self._lock:
            self.events.append({"type": event_type})
            if event_type == "response.created":
                response = message.get("response") or {}
                self.response_id = str(response.get("id") or "")
            elif event_type == "response.audio.delta":
                delta = message.get("delta") or ""
                if delta:
                    self.audio.extend(base64.b64decode(delta))
            elif event_type == "response.done":
                self.done = True
            elif event_type == "error":
                self.error = _safe_jsonable(message)


def _tts_timeout_sec() -> float:
    return max(3.0, _env_float("QPYCLAW_TTS_TIMEOUT_SEC", 20.0))


def _asr_model() -> str:
    return _env_text("QPYCLAW_ASR_MODEL", "fun-asr-realtime")


def _tts_model() -> str:
    return _env_text("QPYCLAW_TTS_MODEL", "qwen3-tts-flash-realtime")


def _tts_voice() -> str:
    return _env_text("QPYCLAW_TTS_VOICE", "Cherry")


def _tts_audio_format() -> str:
    return _env_text("QPYCLAW_TTS_AUDIO_FORMAT", "wav")


def _tts_sample_rate() -> int:
    return max(8000, _env_int("QPYCLAW_TTS_SAMPLE_RATE", 24000))


def _tts_ws_max_text_chars() -> int:
    return max(256, _env_int("QPYCLAW_TTS_WS_MAX_TEXT_CHARS", 8192))


def _tts_ws_queue_max() -> int:
    return max(16, _env_int("QPYCLAW_TTS_WS_QUEUE_MAX", 256))


def _run_asr(payload: AsrRequest) -> dict[str, Any]:
    _require_api_key()
    workspace = _optional_workspace()
    audio_bytes = _decode_base64_audio(payload.audio.base64_audio)
    format_name, suffix = _normalize_audio_format(payload.audio.format)
    sample_rate = int(payload.audio.sample_rate or 16000)
    request_started = time.time()
    transcoded_info = ""

    # The EC800M Opus module produces concatenated raw Opus frames without
    # an Ogg container.  DashScope fun-asr-realtime expects a proper Ogg/Opus
    # container (or another supported format) when format="opus".  Detect
    # the raw-frame case and transcode to WAV so DashScope can parse it.
    if format_name == "opus" and len(audio_bytes) > 4 and not _is_ogg_container(audio_bytes):
        logger.info(
            "ASR: detected raw Opus frames (%d bytes, no OggS header), transcoding to WAV",
            len(audio_bytes),
        )
        audio_bytes, transcoded_info = _transcode_audio_to_wav(audio_bytes, ".opus", sample_rate)
        format_name = "wav"
        suffix = ".wav"

    logger.info(
        "ASR: format=%s audio_bytes=%d", format_name, len(audio_bytes),
    )

    fd, temp_path = tempfile.mkstemp(prefix="qpyclaw_asr_", suffix=suffix)
    os.close(fd)
    try:
        with open(temp_path, "wb") as handle:
            handle.write(audio_bytes)
        recognizer = Recognition(
            model=_asr_model(),
            callback=None,
            format=format_name,
            sample_rate=sample_rate,
            workspace=workspace,
            disfluency_removal_enabled=True,
        )
        result = recognizer.call(temp_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="dashscope asr failed: " + str(exc)) from exc
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

    sentences = _safe_jsonable(result.get_sentence())
    transcript = _flatten_asr_text(sentences)
    elapsed_ms = int((time.time() - request_started) * 1000)
    logger.info(
        "ASR: transcript=%r elapsed=%dms request_id=%s",
        transcript, elapsed_ms, result.get_request_id(),
    )
    return {
        "ok": True,
        "text": transcript,
        "source": "dashscope_fun_asr_realtime",
        "meta": {
            "provider": "dashscope",
            "model": _asr_model(),
            "workspace": bool(workspace),
            "request_id": result.get_request_id(),
            "audio_format": format_name,
            "audio_format_original": str(payload.audio.format or ""),
            "audio_suffix": suffix,
            "audio_bytes": len(audio_bytes),
            "sample_rate": sample_rate,
            "transcoded": bool(transcoded_info),
            "transcoded_info": transcoded_info,
            "elapsed_ms": elapsed_ms,
            "usage": _safe_jsonable(getattr(result, "usage", None)),
            "sentences": sentences,
            "reason": _safe_jsonable(payload.reason),
            "device_id": payload.device_id or "",
            "device_name": payload.device_name or "",
            "board_profile": payload.board_profile or "",
        },
    }


def _run_tts(payload: TtsRequest) -> dict[str, Any]:
    _require_api_key()
    workspace = _optional_workspace()
    text = str(payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")

    collector = _QwenTtsCollector()
    client = QwenTtsRealtime(
        model=_tts_model(),
        callback=collector,
        workspace=workspace,
    )
    started = time.time()
    try:
        client.connect()
        client.update_session(
            voice=str(payload.voice or _tts_voice()),
            audio_format=str(payload.format or _tts_audio_format()),
            sample_rate=int(payload.sample_rate or _tts_sample_rate()),
            mode="commit",
            volume=payload.volume,
            speech_rate=payload.speech_rate,
            pitch_rate=payload.pitch_rate,
            instructions=payload.instructions,
            optimize_instructions=_bool_value(payload.optimize_instructions, False)
            if payload.optimize_instructions is not None
            else None,
        )
        client.append_text(text)
        client.commit()
        deadline = time.time() + _tts_timeout_sec()
        while time.time() < deadline:
            if collector.error is not None:
                break
            if collector.done:
                break
            time.sleep(0.05)
        collector.first_audio_delay_ms = client.get_first_audio_delay()
        if collector.error is not None:
            raise HTTPException(status_code=502, detail="dashscope tts failed: " + json.dumps(collector.error, ensure_ascii=False))
        if not collector.done:
            raise HTTPException(status_code=504, detail="dashscope tts timeout")
        if not collector.audio:
            raise HTTPException(status_code=502, detail="dashscope tts produced empty audio")
        try:
            client.finish()
            time.sleep(0.1)
        except Exception:
            pass
    finally:
        try:
            client.close()
        except Exception:
            pass

    audio_format = str(payload.format or _tts_audio_format())
    audio_bytes = bytes(collector.audio)
    elapsed_ms = int((time.time() - started) * 1000)
    return {
        "ok": True,
        "source": "dashscope_qwen3_tts_realtime",
        "text": text,
        "voice": str(payload.voice or _tts_voice()),
        "audio": {
            "encoding": "base64",
            "format": audio_format,
            "sampleRate": int(payload.sample_rate or _tts_sample_rate()),
            "bytes": len(audio_bytes),
            "base64": base64.b64encode(audio_bytes).decode("ascii"),
        },
        "meta": {
            "provider": "dashscope",
            "model": _tts_model(),
            "workspace": bool(workspace),
            "response_id": collector.response_id,
            "elapsed_ms": elapsed_ms,
            "first_audio_delay_ms": collector.first_audio_delay_ms,
            "events": collector.events,
        },
    }


class _QwenTtsStreamCollector(QwenTtsRealtimeCallback):
    def __init__(self, event_queue: queue.Queue) -> None:
        self.event_queue = event_queue
        self.done = False
        self.error: dict[str, Any] | None = None
        self.events: list[dict[str, Any]] = []
        self.response_id = ""
        self.first_audio_delay_ms: float | None = None
        self.chunk_count = 0
        self.audio_bytes = 0
        self._lock = threading.Lock()

    def _emit(self, payload: dict[str, Any]) -> None:
        try:
            self.event_queue.put_nowait(payload)
        except queue.Full:
            self.error = {"type": "sidecar.queue_full", "detail": "tts stream queue full"}
            self.done = True

    def on_open(self) -> None:
        with self._lock:
            self.events.append({"type": "open"})

    def on_close(self, close_status_code, close_msg) -> None:
        with self._lock:
            self.events.append(
                {
                    "type": "close",
                    "close_status_code": close_status_code,
                    "close_msg": str(close_msg),
                }
            )

    def on_event(self, message: dict[str, Any]) -> None:
        if not isinstance(message, dict):
            return
        event_type = str(message.get("type") or "")
        with self._lock:
            self.events.append({"type": event_type})
            if event_type == "response.created":
                response = message.get("response") or {}
                self.response_id = str(response.get("id") or "")
                self._emit({"type": "tts.begin", "response_id": self.response_id})
            elif event_type == "response.audio.delta":
                delta = str(message.get("delta") or "").strip()
                if delta:
                    self.chunk_count += 1
                    try:
                        self.audio_bytes += len(base64.b64decode(delta))
                    except Exception:
                        pass
                    self._emit(
                        {
                            "type": "tts.chunk",
                            "seq": self.chunk_count,
                            "delta": delta,
                        }
                    )
            elif event_type == "response.done":
                self.done = True
                self._emit({"type": "tts.done"})
            elif event_type == "error":
                self.error = _safe_jsonable(message)
                self.done = True
                self._emit({"type": "tts.error", "error": self.error})


def _run_tts_stream(payload: TtsRequest, event_queue: queue.Queue) -> dict[str, Any]:
    _require_api_key()
    workspace = _optional_workspace()
    text = str(payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")

    collector = _QwenTtsStreamCollector(event_queue)
    client = QwenTtsRealtime(
        model=_tts_model(),
        callback=collector,
        workspace=workspace,
    )
    started = time.time()
    try:
        client.connect()
        client.update_session(
            voice=str(payload.voice or _tts_voice()),
            audio_format=str(payload.format or _tts_audio_format()),
            sample_rate=int(payload.sample_rate or _tts_sample_rate()),
            mode="commit",
            volume=payload.volume,
            speech_rate=payload.speech_rate,
            pitch_rate=payload.pitch_rate,
            instructions=payload.instructions,
            optimize_instructions=_bool_value(payload.optimize_instructions, False)
            if payload.optimize_instructions is not None
            else None,
        )
        client.append_text(text)
        client.commit()
        deadline = time.time() + _tts_timeout_sec()
        while time.time() < deadline:
            if collector.error is not None:
                break
            if collector.done:
                break
            time.sleep(0.05)
        collector.first_audio_delay_ms = client.get_first_audio_delay()
        if collector.error is not None:
            raise HTTPException(
                status_code=502,
                detail="dashscope tts failed: "
                + json.dumps(collector.error, ensure_ascii=False),
            )
        if not collector.done:
            raise HTTPException(status_code=504, detail="dashscope tts timeout")
        try:
            client.finish()
            time.sleep(0.1)
        except Exception:
            pass
    finally:
        try:
            client.close()
        except Exception:
            pass

    elapsed_ms = int((time.time() - started) * 1000)
    return {
        "ok": True,
        "source": "dashscope_qwen3_tts_realtime",
        "text": text,
        "voice": str(payload.voice or _tts_voice()),
        "format": str(payload.format or _tts_audio_format()),
        "sampleRate": int(payload.sample_rate or _tts_sample_rate()),
        "meta": {
            "provider": "dashscope",
            "model": _tts_model(),
            "workspace": bool(workspace),
            "response_id": collector.response_id,
            "elapsed_ms": elapsed_ms,
            "first_audio_delay_ms": collector.first_audio_delay_ms,
            "events": collector.events,
            "chunks": collector.chunk_count,
            "audio_bytes": collector.audio_bytes,
        },
    }


def _queue_get_with_timeout(items: queue.Queue, timeout_sec: float) -> Any:
    try:
        return items.get(timeout=max(0.01, timeout_sec))
    except queue.Empty:
        return None


def _new_ws_request_id() -> str:
    return "ttsws_" + str(int(time.time() * 1000)) + "_" + str(threading.get_ident())


def _build_tts_request(payload: dict[str, Any]) -> TtsRequest:
    validator = getattr(TtsRequest, "model_validate", None)
    if callable(validator):
        return validator(payload)
    parser = getattr(TtsRequest, "parse_obj", None)
    if callable(parser):
        return parser(payload)
    return TtsRequest(**payload)


def _ws_error_detail(exc: Exception) -> tuple[int, str]:
    if isinstance(exc, HTTPException):
        status_code = int(exc.status_code or 500)
        detail = exc.detail
    else:
        status_code = 500
        detail = str(exc)
    if isinstance(detail, (dict, list)):
        try:
            return status_code, json.dumps(detail, ensure_ascii=False)
        except Exception:
            return status_code, str(detail)
    return status_code, str(detail)


async def _ws_send_json(websocket: WebSocket, payload: dict[str, Any]) -> None:
    await websocket.send_text(json.dumps(payload, ensure_ascii=False))


async def _ws_send_error(
    websocket: WebSocket,
    request_id: str,
    exc: Exception,
    stage: str,
) -> None:
    status_code, detail = _ws_error_detail(exc)
    await _ws_send_json(
        websocket,
        {
            "type": "tts.error",
            "requestId": request_id,
            "ok": False,
            "stage": stage,
            "statusCode": status_code,
            "error": detail,
        },
    )


app = FastAPI(
    title="qpyclaw DashScope Voice Sidecar",
    version=APP_VERSION,
)


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    api_key = _env_text("DASHSCOPE_API_KEY", "")
    return {
        "ok": True,
        "service": "qpyclaw-voice-sidecar",
        "version": APP_VERSION,
        "dashscope_api_key": bool(api_key),
        "dashscope_workspace": bool(_optional_workspace()),
        "asr_model": _asr_model(),
        "tts_model": _tts_model(),
        "tts_voice": _tts_voice(),
        "tts_ws_max_text_chars": _tts_ws_max_text_chars(),
        "tts_ws_queue_max": _tts_ws_queue_max(),
    }


@app.post("/api/asr")
def api_asr(
    request: AsrRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_proxy_auth(authorization)
    return _run_asr(request)


@app.post("/api/tts")
def api_tts(
    request: TtsRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_proxy_auth(authorization)
    return _run_tts(request)


@app.websocket("/ws/tts")
async def ws_tts(websocket: WebSocket) -> None:
    authorization = websocket.headers.get("authorization")
    if not _is_proxy_authorized(authorization):
        await websocket.close(code=4401, reason="unauthorized")
        return
    await websocket.accept()

    request_id = _new_ws_request_id()
    request: TtsRequest | None = None
    try:
        raw_text = await websocket.receive_text()
        if len(raw_text) > _tts_ws_max_text_chars():
            raise HTTPException(status_code=413, detail="request frame too large")
        payload = json.loads(raw_text)
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="request payload must be object")
        request_id = str(payload.get("requestId") or payload.get("request_id") or request_id).strip() or request_id
        request = _build_tts_request(payload)
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await _ws_send_error(websocket, request_id, exc, "request.parse")
        await websocket.close(code=1003)
        return

    assert request is not None
    event_queue = queue.Queue(maxsize=_tts_ws_queue_max())
    worker_result: dict[str, Any] = {}
    worker_error: dict[str, Exception] = {}

    def _worker_main() -> None:
        try:
            worker_result["summary"] = _run_tts_stream(request, event_queue)
        except Exception as exc:
            worker_error["error"] = exc
        finally:
            try:
                event_queue.put_nowait({"type": "worker.done"})
            except Exception:
                pass

    worker = threading.Thread(target=_worker_main, daemon=True)
    worker.start()

    loop = asyncio.get_running_loop()
    begin_sent = False
    chunks_sent = 0
    response_id = ""
    tts_format = str(request.format or _tts_audio_format())
    tts_sample_rate = int(request.sample_rate or _tts_sample_rate())
    tts_voice = str(request.voice or _tts_voice())

    try:
        while True:
            event = await loop.run_in_executor(None, _queue_get_with_timeout, event_queue, 0.2)
            if event is None:
                if (not worker.is_alive()) and event_queue.empty():
                    break
                continue

            event_type = str(event.get("type") or "")
            if event_type == "tts.begin":
                response_id = str(event.get("response_id") or response_id)
                await _ws_send_json(
                    websocket,
                    {
                        "type": "tts.begin",
                        "requestId": request_id,
                        "source": "dashscope_qwen3_tts_realtime",
                        "model": _tts_model(),
                        "voice": tts_voice,
                        "format": tts_format,
                        "sampleRate": tts_sample_rate,
                        "responseId": response_id,
                    },
                )
                begin_sent = True
                continue

            if event_type == "tts.chunk":
                delta = str(event.get("delta") or "").strip()
                if not delta:
                    continue
                if not begin_sent:
                    await _ws_send_json(
                        websocket,
                        {
                            "type": "tts.begin",
                            "requestId": request_id,
                            "source": "dashscope_qwen3_tts_realtime",
                            "model": _tts_model(),
                            "voice": tts_voice,
                            "format": tts_format,
                            "sampleRate": tts_sample_rate,
                            "responseId": response_id,
                        },
                    )
                    begin_sent = True
                chunks_sent = int(event.get("seq") or (chunks_sent + 1))
                await _ws_send_json(
                    websocket,
                    {
                        "type": "tts.chunk",
                        "requestId": request_id,
                        "seq": chunks_sent,
                        "encoding": "base64",
                        "delta": delta,
                    },
                )
                continue

            if event_type == "tts.error":
                error_payload = event.get("error")
                detail = "unknown tts stream error"
                if error_payload is not None:
                    if isinstance(error_payload, (dict, list)):
                        try:
                            detail = json.dumps(error_payload, ensure_ascii=False)
                        except Exception:
                            detail = str(error_payload)
                    else:
                        detail = str(error_payload)
                await _ws_send_json(
                    websocket,
                    {
                        "type": "tts.error",
                        "requestId": request_id,
                        "ok": False,
                        "stage": "tts.stream",
                        "statusCode": 502,
                        "error": detail,
                    },
                )
                return

            if event_type == "worker.done":
                break

        if worker_error.get("error") is not None:
            await _ws_send_error(websocket, request_id, worker_error["error"], "tts.run")
            return

        summary = worker_result.get("summary") or {}
        meta = summary.get("meta") or {}
        response_id = str(meta.get("response_id") or response_id)
        if not begin_sent:
            await _ws_send_json(
                websocket,
                {
                    "type": "tts.begin",
                    "requestId": request_id,
                    "source": "dashscope_qwen3_tts_realtime",
                    "model": _tts_model(),
                    "voice": tts_voice,
                    "format": tts_format,
                    "sampleRate": tts_sample_rate,
                    "responseId": response_id,
                },
            )
        await _ws_send_json(
            websocket,
            {
                "type": "tts.end",
                "requestId": request_id,
                "ok": True,
                "responseId": response_id,
                "chunks": int(meta.get("chunks") or chunks_sent),
                "audioBytes": int(meta.get("audio_bytes") or 0),
                "elapsedMs": int(meta.get("elapsed_ms") or 0),
                "firstAudioDelayMs": meta.get("first_audio_delay_ms"),
            },
        )
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await _ws_send_error(websocket, request_id, exc, "ws.send")
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=_env_text("QPYCLAW_VOICE_SIDECAR_HOST", "0.0.0.0"),
        port=_env_int("QPYCLAW_VOICE_SIDECAR_PORT", 8788),
        reload=False,
    )
