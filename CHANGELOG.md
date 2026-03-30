# Changelog

All notable changes to this project will be documented in this file.

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
