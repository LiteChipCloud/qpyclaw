# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1-alpha.1] - 2026-04-01

### Fixed

1. Fixed ASR `remote asr transcript missing` — device was sending raw Opus frames; now prefers `record_stream` (Ogg/Opus container) in `board_audio.py`
2. Fixed audio capture format detection — `open_stream()` now called before `_audio_capture_begin()` in `board_voice_controller.py`
3. Fixed device OOM during base64 encoding — chunked 3KB encoding in `board_remote_asr.py`
4. Added sidecar safety net — raw Opus auto-detection and ffmpeg transcode fallback in `app.py`
5. Changed default `VOICE_ASR_HTTP_AUDIO_FORMAT` from `opus` to `oggopus`

### Added

1. Added `qpy_voice_asr_smoke.py` — E2E ASR verification tool with natural and manual modes
2. Added `qpy_voice_sidecar_health.py` — sidecar health-check, deploy, restart, and DashScope ASR probe tool

### Changed

1. Cleaned up sidecar `app.py` debug logging (removed `/tmp` file writes, kept concise production logs)
2. Removed 45 temporary debug scripts from `tools/host/`
3. Updated capability matrix — voice chain now marked as verified

### Verified

1. Verified full KWS → VAD → ASR → Chat → TTS → idle cycle on EC800MCNLE device
2. Verified DashScope `fun-asr-realtime` recognizes Ogg/Opus audio from device
3. Verified chunked base64 encoding works without OOM on 45KB+ audio

## [0.1.0-alpha.1] - 2026-03-30

Recommended first public tag:

1. `v0.1.0-alpha.1`

### Added

1. Bootstrapped the standalone `qpyclaw` repository layout
2. Added single-file QuecPython runtime `qpyclaw_node.py`
3. Added device-local `config_local.py` override workflow
4. Added manifest-driven `/usr` runtime recovery and sync flow
5. Added host-side recover, smoke, board sync, media sync, and operator tools
6. Added `EC800MCNLE` audio-board bootstrap, display, UI, power, and audio board code
7. Added public-facing docs: Quickstart, config sample, alpha release notes

### Verified

1. Verified `Mode B: qpyclaw-node -> Official OpenClaw Gateway`
2. Verified `EC800KCNLC` non-peripheral runtime path
3. Verified `EC800MCNLE` audio-board board-runtime path
4. Verified cellular disconnect recovery and Gateway reconnect
5. Verified `qpy.ui.emotion.show` with board media resources

### Documentation

1. Reworked the root README into a public project landing page
2. Added hardware purchase reference for the current development board
3. Added project positioning, architecture, product, research, and bring-up documents

### Notes

1. The repository is suitable for an `Alpha / Developer Preview` release
2. Official `main.py` cold-boot auto-start is still kept in development mode
3. Full voice-session capability is still in progress and is not yet a stable public promise
