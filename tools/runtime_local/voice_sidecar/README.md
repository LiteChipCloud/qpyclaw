# qpyclaw DashScope Voice Sidecar

This service keeps QuecPython device code simple and moves DashScope SDK complexity to server side.

Current endpoints:
1. `POST /api/asr`: upload base64 audio and get transcript text.
2. `POST /api/tts`: upload text and get full base64 audio payload.
3. `GET /healthz`: sidecar health and effective model config.
4. `WS /ws/tts`: streaming TTS. The server pushes `tts.begin -> tts.chunk -> tts.end` frames.

## Directory

```text
tools/runtime_local/voice_sidecar/
├─ app.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Or:

```bash
uvicorn app:app --host 0.0.0.0 --port 8788
```

## Environment Variables

Required:

```env
DASHSCOPE_API_KEY=...
QPYCLAW_VOICE_PROXY_TOKEN=...
```

Optional:

```env
DASHSCOPE_WORKSPACE_ID=...
QPYCLAW_ASR_MODEL=fun-asr-realtime
QPYCLAW_TTS_MODEL=qwen3-tts-flash-realtime
QPYCLAW_TTS_VOICE=Cherry
QPYCLAW_TTS_AUDIO_FORMAT=wav
QPYCLAW_TTS_SAMPLE_RATE=24000
QPYCLAW_TTS_TIMEOUT_SEC=20
QPYCLAW_TTS_WS_MAX_TEXT_CHARS=8192
QPYCLAW_TTS_WS_QUEUE_MAX=256
QPYCLAW_VOICE_SIDECAR_HOST=0.0.0.0
QPYCLAW_VOICE_SIDECAR_PORT=8788
```

## HTTP ASR Contract (`POST /api/asr`)

Request:

```json
{
  "deviceId": "qpyclaw_ec800m_audio_001",
  "audio": {
    "encoding": "base64",
    "format": "opus",
    "sampleRate": 16000,
    "base64": "<base64-audio>"
  }
}
```

Response:

```json
{
  "ok": true,
  "text": "hello world",
  "source": "dashscope_fun_asr_realtime",
  "meta": {
    "provider": "dashscope",
    "model": "fun-asr-realtime"
  }
}
```

## HTTP TTS Contract (`POST /api/tts`)

Request:

```json
{
  "text": "Hello from qpyclaw.",
  "voice": "Cherry",
  "format": "wav",
  "sampleRate": 24000
}
```

Response:

```json
{
  "ok": true,
  "source": "dashscope_qwen3_tts_realtime",
  "audio": {
    "encoding": "base64",
    "format": "wav",
    "sampleRate": 24000,
    "bytes": 49964,
    "base64": "<base64-audio>"
  }
}
```

## Streaming TTS Contract (`WS /ws/tts`)

Auth:
1. Use header `Authorization: Bearer <QPYCLAW_VOICE_PROXY_TOKEN>`.
2. If token check is disabled (`QPYCLAW_VOICE_PROXY_TOKEN` empty), WS is open.

Client first frame (text JSON):

```json
{
  "requestId": "tts_turn_001",
  "text": "Hello from qpyclaw stream.",
  "voice": "Cherry",
  "format": "pcm",
  "sampleRate": 16000
}
```

Server push frames (text JSON):

`tts.begin`

```json
{
  "type": "tts.begin",
  "requestId": "tts_turn_001",
  "source": "dashscope_qwen3_tts_realtime",
  "model": "qwen3-tts-flash-realtime",
  "voice": "Cherry",
  "format": "pcm",
  "sampleRate": 16000,
  "responseId": "..."
}
```

`tts.chunk` (repeat)

```json
{
  "type": "tts.chunk",
  "requestId": "tts_turn_001",
  "seq": 1,
  "encoding": "base64",
  "delta": "<base64-audio-delta>"
}
```

`tts.end`

```json
{
  "type": "tts.end",
  "requestId": "tts_turn_001",
  "ok": true,
  "responseId": "...",
  "chunks": 42,
  "audioBytes": 18234,
  "elapsedMs": 912
}
```

Error frame:

```json
{
  "type": "tts.error",
  "requestId": "tts_turn_001",
  "ok": false,
  "stage": "request.parse",
  "statusCode": 400,
  "error": "..."
}
```

## Notes

1. `/ws/tts` streams DashScope `response.audio.delta` chunks directly.
2. `/api/tts` is retained as a file-based/fallback path.
3. Device can choose stream-first and fallback to `/api/tts` when needed.
