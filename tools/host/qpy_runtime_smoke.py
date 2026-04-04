#!/usr/bin/env python3
"""
Run a conservative runtime smoke test against a QuecPython qpyclaw-node device.

Default smoke verifies:
1. qpyclaw_node import and config_local loading
2. RuntimeState and ToolRunner initialization
3. qpy.runtime.status execution
4. qpy.tools.catalog execution
5. qpy.fs.read execution

Optional board smoke also verifies:
1. node_main import
2. qpy.board.status execution
3. qpy.audio.status execution
4. qpy.audio.volume.get execution
5. qpy.power.status execution
6. qpy.ui.status execution

Optional board write smoke additionally verifies:
1. qpy.audio.volume.set
2. qpy.audio.stream.open and qpy.audio.stream.close
3. qpy.power.charge.enable and qpy.power.charge.disable
4. qpy.ui.emotion.show with restore
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys
from typing import Any, Dict, List

QPY_DEVICE_FS_CLI = pathlib.Path(
    r"C:\Users\kingd\.codex\skills\quecpython-dev\scripts\qpy_device_fs_cli.py"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run qpyclaw-node runtime smoke against a QuecPython device."
    )
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument("--timeout", type=int, default=60, help="REPL timeout seconds.")
    parser.add_argument(
        "--fs-read-path",
        default="/usr/qpyclaw_node.py",
        help="Filesystem path for qpy.fs.read smoke.",
    )
    parser.add_argument(
        "--fs-read-max-bytes",
        type=int,
        default=128,
        help="max_bytes argument for qpy.fs.read smoke.",
    )
    parser.add_argument(
        "--board-smoke",
        action="store_true",
        help="Also verify board entry import and EC800MCNLE board/audio tools.",
    )
    parser.add_argument(
        "--board-write-smoke",
        action="store_true",
        help="When board smoke is enabled, also verify write-path board tools and restore state.",
    )
    parser.add_argument(
        "--voice-chat-message",
        default="",
        help="Optional bare-runtime voice.chat message to execute after base smoke.",
    )
    parser.add_argument(
        "--voice-chat-timeout-ms",
        type=int,
        default=45000,
        help="voice.chat timeout in milliseconds when --voice-chat-message is set.",
    )
    parser.add_argument(
        "--voice-session-key",
        default="main",
        help="voice.chat session_key when --voice-chat-message is set.",
    )
    parser.add_argument(
        "--voice-chat-history-limit",
        type=int,
        default=8,
        help="voice.chat history_limit when --voice-chat-message is set.",
    )
    parser.add_argument(
        "--voice-chat-subscribe",
        action="store_true",
        help="Enable subscribe=True for optional voice.chat probe.",
    )
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Include raw REPL transcript in JSON output.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def load_qpy_fs_cli():
    scripts_dir = QPY_DEVICE_FS_CLI.parent
    sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("qpy_device_fs_cli", QPY_DEVICE_FS_CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def single_quote_qpy(text: str) -> str:
    return str(text or "").replace("\\", "/").replace("'", "\\'")


def build_import_lines() -> List[str]:
    return [
        "import sys as _sys",
        "import gc",
        "_mods=getattr(_sys,'modules',{})",
        "_dummy=('qpyclaw_node' in _mods) and _mods.pop('qpyclaw_node')",
        "_dummy=('config_local' in _mods) and _mods.pop('config_local')",
        "_dummy=('node_main' in _mods) and _mods.pop('node_main')",
        "_dummy=('dispatch' in _mods) and _mods.pop('dispatch')",
        "_dummy=('board_bootstrap' in _mods) and _mods.pop('board_bootstrap')",
        "_dummy=('board_audio' in _mods) and _mods.pop('board_audio')",
        "_dummy=('board_power' in _mods) and _mods.pop('board_power')",
        "_dummy=('board_display' in _mods) and _mods.pop('board_display')",
        "_dummy=('board_ui' in _mods) and _mods.pop('board_ui')",
        "_dummy=('board_voice_controller' in _mods) and _mods.pop('board_voice_controller')",
        "_dummy=('board_remote_asr' in _mods) and _mods.pop('board_remote_asr')",
        "_dummy=('board_remote_tts' in _mods) and _mods.pop('board_remote_tts')",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='/usr/app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "gc.collect()",
        "_qpy_import_ok='QPY_IMPORT_' + 'OK'",
        "_qpy_import_error='QPY_IMPORT_' + 'ERROR='",
        "exec('try:\\n import qpyclaw_node\\n print(_qpy_import_ok)\\nexcept Exception as e:\\n print(_qpy_import_error + repr(e))')",
    ]


def build_exec_lines(
    fs_read_path: str,
    fs_read_max_bytes: int,
    board_smoke: bool,
    board_write_smoke: bool,
) -> List[str]:
    safe_path = single_quote_qpy(fs_read_path)
    max_bytes = max(1, int(fs_read_max_bytes))
    lines = [
        "import sys as _sys",
        "import ujson",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='/usr/app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "import qpyclaw_node",
        "cfg = qpyclaw_node.config",
        "state = qpyclaw_node.RuntimeState(cfg)",
    ]
    if board_smoke:
        lines.extend(
            [
                "_p='/usr/board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
                "_p='board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
                "_mods=getattr(_sys,'modules',{})",
                "_dummy=('node_main' in _mods) and _mods.pop('node_main')",
                "_dummy=('dispatch' in _mods) and _mods.pop('dispatch')",
                "_dummy=('board_bootstrap' in _mods) and _mods.pop('board_bootstrap')",
                "_dummy=('board_audio' in _mods) and _mods.pop('board_audio')",
                "_dummy=('board_power' in _mods) and _mods.pop('board_power')",
                "_dummy=('board_display' in _mods) and _mods.pop('board_display')",
                "_dummy=('board_ui' in _mods) and _mods.pop('board_ui')",
                "_dummy=('board_voice_controller' in _mods) and _mods.pop('board_voice_controller')",
                "_dummy=('board_remote_asr' in _mods) and _mods.pop('board_remote_asr')",
                "_dummy=('board_remote_tts' in _mods) and _mods.pop('board_remote_tts')",
                "import node_main",
                "board_entry_import_ok = True",
                "board_entry_module = str(getattr(node_main, '__file__', '') or '')",
                "from board_bootstrap import create_qpyclaw_extension",
                "extension = create_qpyclaw_extension(enable_charge=True, enable_display=True, open_audio=False)",
                "runner = qpyclaw_node.ToolRunner(cfg, state, extension)",
            ]
        )
    else:
        lines.append("runner = qpyclaw_node.ToolRunner(cfg, state)")

    lines.extend(
        [
            "runtime_status = runner.execute({'request_id': 'smoke-runtime-status', 'tool': 'qpy.runtime.status', 'args': {}})",
            "catalog = runner.execute({'request_id': 'smoke-catalog', 'tool': 'qpy.tools.catalog', 'args': {}})",
            "fs_read = runner.execute({'request_id': 'smoke-fs-read', 'tool': 'qpy.fs.read', 'args': {'path': '%s', 'max_bytes': %d}})"
            % (safe_path, max_bytes),
        ]
    )
    if board_smoke:
        lines.extend(
            [
                "board_status = runner.execute({'request_id': 'smoke-board-status', 'tool': 'qpy.board.status', 'args': {}})",
                "audio_status = runner.execute({'request_id': 'smoke-audio-status', 'tool': 'qpy.audio.status', 'args': {}})",
                "audio_volume_get = runner.execute({'request_id': 'smoke-audio-volume-get', 'tool': 'qpy.audio.volume.get', 'args': {}})",
                "power_status = runner.execute({'request_id': 'smoke-power-status', 'tool': 'qpy.power.status', 'args': {}})",
                "ui_status = runner.execute({'request_id': 'smoke-ui-status', 'tool': 'qpy.ui.status', 'args': {}})",
            ]
        )
        if board_write_smoke:
            lines.extend(
                [
                    "_audio_volume = ((audio_volume_get.get('data') or {}).get('volume'))",
                    "_audio_volume = int(_audio_volume if _audio_volume is not None else 0)",
                    "audio_volume_set = runner.execute({'request_id': 'smoke-audio-volume-set', 'tool': 'qpy.audio.volume.set', 'args': {'volume': _audio_volume}})",
                    "audio_stream_open = runner.execute({'request_id': 'smoke-audio-stream-open', 'tool': 'qpy.audio.stream.open', 'args': {}})",
                    "audio_stream_close = runner.execute({'request_id': 'smoke-audio-stream-close', 'tool': 'qpy.audio.stream.close', 'args': {}})",
                    "_power_charge_initial = bool(((power_status.get('data') or {}).get('charge_enabled')))",
                    "power_charge_enable = runner.execute({'request_id': 'smoke-power-charge-enable', 'tool': 'qpy.power.charge.enable', 'args': {}})",
                    "power_charge_disable = runner.execute({'request_id': 'smoke-power-charge-disable', 'tool': 'qpy.power.charge.disable', 'args': {}})",
                    "power_charge_restore = runner.execute({'request_id': ('smoke-power-charge-restore-enable' if _power_charge_initial else 'smoke-power-charge-restore-disable'), 'tool': ('qpy.power.charge.enable' if _power_charge_initial else 'qpy.power.charge.disable'), 'args': {}})",
                    "_ui_emotion_initial = str(((ui_status.get('data') or {}).get('current_emoji') or ''))",
                    "_ui_emotion_target = 'thinking'",
                    "_ui_emotion_target = 'neutral' if _ui_emotion_target == _ui_emotion_initial else _ui_emotion_target",
                    "ui_emotion_show = runner.execute({'request_id': 'smoke-ui-emotion-show', 'tool': 'qpy.ui.emotion.show', 'args': {'emotion': _ui_emotion_target}})",
                    "_ui_emotion_restore = _ui_emotion_initial or 'neutral'",
                    "ui_emotion_restore = runner.execute({'request_id': 'smoke-ui-emotion-restore', 'tool': 'qpy.ui.emotion.show', 'args': {'emotion': _ui_emotion_restore}})",
                ]
            )
    lines.append("loaded_domains = sorted(runner._loaded_domains.keys())")

    payload_parts = [
        " 'config_local_loaded': bool(getattr(cfg, 'CONFIG_LOCAL_LOADED', False))",
        " 'config_local_error': str(getattr(cfg, 'CONFIG_LOCAL_ERROR', '') or '')",
        " 'config_local_source': str(getattr(cfg, 'CONFIG_LOCAL_SOURCE', '') or '')",
        " 'device_model_hint': str(getattr(cfg, 'DEVICE_MODEL_HINT', '') or '')",
        " 'board_profile': str(getattr(cfg, 'BOARD_PROFILE', '') or '')",
        " 'runtime_status': runtime_status.get('status')",
        " 'runtime_result_code': runtime_status.get('result_code')",
        " 'runtime_online': bool(((runtime_status.get('data') or {}).get('online')))",
        " 'runtime_config_source': str((((runtime_status.get('data') or {}).get('config_local') or {}).get('source') or ''))",
        " 'catalog_status': catalog.get('status')",
        " 'catalog_tool_count': len((catalog.get('data') or {}).get('tools') or [])",
        " 'catalog_result_code': catalog.get('result_code')",
        " 'fs_read_status': fs_read.get('status')",
        " 'fs_read_result_code': fs_read.get('result_code')",
        " 'fs_read_path': ((fs_read.get('data') or {}).get('path') or '')",
        " 'fs_read_bytes': len((((fs_read.get('data') or {}).get('content') or '')))",
        " 'loaded_domains': loaded_domains",
    ]
    if board_smoke:
        payload_parts.extend(
            [
                " 'board_entry_import_ok': bool(board_entry_import_ok)",
                " 'board_entry_module': board_entry_module",
                " 'board_status': board_status.get('status')",
                " 'board_result_code': board_status.get('result_code')",
                " 'audio_status': audio_status.get('status')",
                " 'audio_result_code': audio_status.get('result_code')",
                " 'audio_volume_get_status': audio_volume_get.get('status')",
                " 'audio_volume_get_result_code': audio_volume_get.get('result_code')",
                " 'audio_volume': ((audio_volume_get.get('data') or {}).get('volume'))",
                " 'power_status': power_status.get('status')",
                " 'power_result_code': power_status.get('result_code')",
                " 'ui_status': ui_status.get('status')",
                " 'ui_result_code': ui_status.get('result_code')",
            ]
        )
        if board_write_smoke:
            payload_parts.extend(
                [
                    " 'audio_volume_set_status': audio_volume_set.get('status')",
                    " 'audio_volume_set_result_code': audio_volume_set.get('result_code')",
                    " 'audio_volume_set_value': ((audio_volume_set.get('data') or {}).get('volume'))",
                    " 'audio_stream_open_status': audio_stream_open.get('status')",
                    " 'audio_stream_open_result_code': audio_stream_open.get('result_code')",
                    " 'audio_stream_open_value': bool(((((audio_stream_open.get('data') or {}).get('audio') or {}).get('stream_open'))))",
                    " 'audio_stream_close_status': audio_stream_close.get('status')",
                    " 'audio_stream_close_result_code': audio_stream_close.get('result_code')",
                    " 'audio_stream_close_value': bool(((((audio_stream_close.get('data') or {}).get('audio') or {}).get('stream_open'))))",
                    " 'power_charge_initial': bool(_power_charge_initial)",
                    " 'power_charge_enable_status': power_charge_enable.get('status')",
                    " 'power_charge_enable_result_code': power_charge_enable.get('result_code')",
                    " 'power_charge_enable_value': bool(((((power_charge_enable.get('data') or {}).get('power') or {}).get('charge_enabled'))))",
                    " 'power_charge_disable_status': power_charge_disable.get('status')",
                    " 'power_charge_disable_result_code': power_charge_disable.get('result_code')",
                    " 'power_charge_disable_value': bool(((((power_charge_disable.get('data') or {}).get('power') or {}).get('charge_enabled'))))",
                    " 'power_charge_restore_status': power_charge_restore.get('status')",
                    " 'power_charge_restore_result_code': power_charge_restore.get('result_code')",
                    " 'power_charge_restore_value': bool(((((power_charge_restore.get('data') or {}).get('power') or {}).get('charge_enabled'))))",
                    " 'ui_emotion_initial': _ui_emotion_initial",
                    " 'ui_emotion_target': _ui_emotion_target",
                    " 'ui_emotion_show_status': ui_emotion_show.get('status')",
                    " 'ui_emotion_show_result_code': ui_emotion_show.get('result_code')",
                    " 'ui_emotion_show_value': str(((((ui_emotion_show.get('data') or {}).get('ui') or {}).get('current_emoji')) or ''))",
                    " 'ui_emotion_restore_status': ui_emotion_restore.get('status')",
                    " 'ui_emotion_restore_result_code': ui_emotion_restore.get('result_code')",
                    " 'ui_emotion_restore_value': str(((((ui_emotion_restore.get('data') or {}).get('ui') or {}).get('current_emoji')) or ''))",
                ]
            )

    lines.extend(
        [
            "payload = {" + ",".join(payload_parts) + "}",
            "print('QPY_RUNTIME_SMOKE_JSON=' + ujson.dumps(payload))",
        ]
    )
    return lines


def build_exec_board_prepare_lines() -> List[str]:
    lines = [
        "import sys as _sys",
        "import ujson",
        "import gc",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='/usr/app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "import qpyclaw_node",
        "cfg = qpyclaw_node.config",
        "state = qpyclaw_node.RuntimeState(cfg)",
        "_p='/usr/board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_mods=getattr(_sys,'modules',{})",
        "_dummy=('node_main' in _mods) and _mods.pop('node_main')",
        "_dummy=('dispatch' in _mods) and _mods.pop('dispatch')",
        "_dummy=('board_bootstrap' in _mods) and _mods.pop('board_bootstrap')",
        "_dummy=('board_audio' in _mods) and _mods.pop('board_audio')",
        "_dummy=('board_power' in _mods) and _mods.pop('board_power')",
        "_dummy=('board_display' in _mods) and _mods.pop('board_display')",
        "_dummy=('board_ui' in _mods) and _mods.pop('board_ui')",
        "_dummy=('board_voice_controller' in _mods) and _mods.pop('board_voice_controller')",
        "_dummy=('board_remote_asr' in _mods) and _mods.pop('board_remote_asr')",
        "_dummy=('board_remote_tts' in _mods) and _mods.pop('board_remote_tts')",
        "gc.collect()",
        "print('QPY_SMOKE_BOARD_PREP_OK')",
    ]
    return lines


def build_exec_board_import_lines() -> List[str]:
    return [
        "import node_main",
        "print('QPY_SMOKE_BOARD_IMPORT_OK')",
    ]


def build_exec_bootstrap_lines(board_smoke: bool) -> List[str]:
    if board_smoke:
        lines = [
            "board_entry_import_ok = True",
            "board_entry_module = str(getattr(node_main, '__file__', '') or '')",
            "from board_bootstrap import create_qpyclaw_extension",
            "extension = create_qpyclaw_extension(enable_charge=True, enable_display=True, open_audio=False)",
            "runner = qpyclaw_node.ToolRunner(cfg, state, extension)",
            "print('QPY_SMOKE_BOOTSTRAP_OK')",
        ]
        return lines
    lines = [
        "import sys as _sys",
        "import ujson",
        "import gc",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='/usr/app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='app'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "gc.collect()",
        "import qpyclaw_node",
        "cfg = qpyclaw_node.config",
        "state = qpyclaw_node.RuntimeState(cfg)",
        "runner = qpyclaw_node.ToolRunner(cfg, state)",
        "print('QPY_SMOKE_BOOTSTRAP_OK')",
    ]
    return lines


def build_exec_status_lines(fs_read_path: str, fs_read_max_bytes: int, board_smoke: bool) -> List[str]:
    safe_path = single_quote_qpy(fs_read_path)
    max_bytes = max(1, int(fs_read_max_bytes))
    lines = [
        "runtime_status = runner.execute({'request_id': 'smoke-runtime-status', 'tool': 'qpy.runtime.status', 'args': {}})",
        "catalog = runner.execute({'request_id': 'smoke-catalog', 'tool': 'qpy.tools.catalog', 'args': {}})",
        "fs_read = runner.execute({'request_id': 'smoke-fs-read', 'tool': 'qpy.fs.read', 'args': {'path': '%s', 'max_bytes': %d}})"
        % (safe_path, max_bytes),
    ]
    if board_smoke:
        lines.extend(
            [
                "board_status = runner.execute({'request_id': 'smoke-board-status', 'tool': 'qpy.board.status', 'args': {}})",
                "audio_status = runner.execute({'request_id': 'smoke-audio-status', 'tool': 'qpy.audio.status', 'args': {}})",
                "audio_volume_get = runner.execute({'request_id': 'smoke-audio-volume-get', 'tool': 'qpy.audio.volume.get', 'args': {}})",
                "power_status = runner.execute({'request_id': 'smoke-power-status', 'tool': 'qpy.power.status', 'args': {}})",
                "ui_status = runner.execute({'request_id': 'smoke-ui-status', 'tool': 'qpy.ui.status', 'args': {}})",
            ]
        )
    lines.append("print('QPY_SMOKE_STATUS_OK')")
    return lines


def build_exec_voice_chat_lines(
    voice_chat_message: str,
    voice_chat_timeout_ms: int,
    voice_session_key: str,
    voice_chat_subscribe: bool,
    voice_chat_history_limit: int,
) -> List[str]:
    message = str(voice_chat_message or "")
    lines = [
        "_voice_before = qpyclaw_node.voice_status()",
        "_voice_probe = {'enabled': False}",
    ]
    if not message:
        return lines
    safe_message = repr(message)
    safe_session_key = repr(str(voice_session_key or "main"))
    subscribe_text = "True" if bool(voice_chat_subscribe) else "False"
    lines.extend(
        [
            "_voice_probe = {'enabled': True, 'message': %s}" % safe_message,
            "try:",
            " _voice_result = qpyclaw_node.voice_chat(%s, session_key=%s, timeout_ms=%d, subscribe=%s, history_limit=%d)"
            % (
                safe_message,
                safe_session_key,
                int(voice_chat_timeout_ms),
                subscribe_text,
                int(voice_chat_history_limit),
            ),
            " _voice_after = qpyclaw_node.voice_status()",
            " _voice_probe = {'enabled': True, 'ok': True, 'message': %s, 'session_key': %s, 'timeout_ms': %d, 'subscribe': %s, 'history_limit': %d, 'result': _voice_result, 'before': _voice_before, 'after': _voice_after}"
            % (
                safe_message,
                safe_session_key,
                int(voice_chat_timeout_ms),
                subscribe_text,
                int(voice_chat_history_limit),
            ),
            "except Exception as _voice_exc:",
            " _voice_after = qpyclaw_node.voice_status()",
            " _voice_probe = {'enabled': True, 'ok': False, 'message': %s, 'session_key': %s, 'timeout_ms': %d, 'subscribe': %s, 'history_limit': %d, 'error': str(_voice_exc), 'before': _voice_before, 'after': _voice_after}"
            % (
                safe_message,
                safe_session_key,
                int(voice_chat_timeout_ms),
                subscribe_text,
                int(voice_chat_history_limit),
            ),
        ]
    )
    return lines


def build_exec_write_lines() -> List[str]:
    return [
        "_audio_volume_get = globals().get('audio_volume_get') or {}",
        "_audio_volume = int((((_audio_volume_get.get('data') or {}).get('volume')) if isinstance(_audio_volume_get, dict) else 0) or 0)",
        "audio_volume_set = runner.execute({'request_id': 'smoke-audio-volume-set', 'tool': 'qpy.audio.volume.set', 'args': {'volume': _audio_volume}})",
        "audio_stream_open = runner.execute({'request_id': 'smoke-audio-stream-open', 'tool': 'qpy.audio.stream.open', 'args': {}})",
        "audio_stream_close = runner.execute({'request_id': 'smoke-audio-stream-close', 'tool': 'qpy.audio.stream.close', 'args': {}})",
        "_power_status = globals().get('power_status') or {}",
        "_power_charge_initial = bool((((_power_status.get('data') or {}).get('charge_enabled')) if isinstance(_power_status, dict) else False))",
        "power_charge_enable = runner.execute({'request_id': 'smoke-power-charge-enable', 'tool': 'qpy.power.charge.enable', 'args': {}})",
        "power_charge_disable = runner.execute({'request_id': 'smoke-power-charge-disable', 'tool': 'qpy.power.charge.disable', 'args': {}})",
        "power_charge_restore = runner.execute({'request_id': ('smoke-power-charge-restore-enable' if _power_charge_initial else 'smoke-power-charge-restore-disable'), 'tool': ('qpy.power.charge.enable' if _power_charge_initial else 'qpy.power.charge.disable'), 'args': {}})",
        "_ui_status = globals().get('ui_status') or {}",
        "_ui_emotion_initial = str((((_ui_status.get('data') or {}).get('current_emoji')) if isinstance(_ui_status, dict) else '') or '')",
        "_ui_emotion_target = 'thinking'",
        "_ui_emotion_target = 'neutral' if _ui_emotion_target == _ui_emotion_initial else _ui_emotion_target",
        "ui_emotion_show = runner.execute({'request_id': 'smoke-ui-emotion-show', 'tool': 'qpy.ui.emotion.show', 'args': {'emotion': _ui_emotion_target}})",
        "_ui_emotion_restore = _ui_emotion_initial or 'neutral'",
        "ui_emotion_restore = runner.execute({'request_id': 'smoke-ui-emotion-restore', 'tool': 'qpy.ui.emotion.show', 'args': {'emotion': _ui_emotion_restore}})",
        "print('QPY_SMOKE_WRITE_OK')",
    ]


def build_payload_lines(board_smoke: bool, board_write_smoke: bool) -> List[str]:
    lines = [
        "_g = globals()",
        "_runtime_status = _g.get('runtime_status') or {}",
        "_catalog = _g.get('catalog') or {}",
        "_fs_read = _g.get('fs_read') or {}",
        "loaded_domains = sorted(runner._loaded_domains.keys())",
    ]
    if board_smoke:
        lines.extend(
            [
                "_board_status = _g.get('board_status') or {}",
                "_audio_status = _g.get('audio_status') or {}",
                "_audio_volume_get = _g.get('audio_volume_get') or {}",
                "_power_status = _g.get('power_status') or {}",
                "_ui_status = _g.get('ui_status') or {}",
                "_board_entry_import_ok = bool(_g.get('board_entry_import_ok'))",
                "_board_entry_module = str(_g.get('board_entry_module') or '')",
            ]
        )
    if board_write_smoke:
        lines.extend(
            [
                "_audio_volume_set = _g.get('audio_volume_set') or {}",
                "_audio_stream_open = _g.get('audio_stream_open') or {}",
                "_audio_stream_close = _g.get('audio_stream_close') or {}",
                "_power_charge_enable = _g.get('power_charge_enable') or {}",
                "_power_charge_disable = _g.get('power_charge_disable') or {}",
                "_power_charge_restore = _g.get('power_charge_restore') or {}",
                "_ui_emotion_show = _g.get('ui_emotion_show') or {}",
                "_ui_emotion_restore_result = _g.get('ui_emotion_restore') or {}",
                "_power_charge_initial = bool(_g.get('_power_charge_initial'))",
                "_ui_emotion_initial = str(_g.get('_ui_emotion_initial') or '')",
                "_ui_emotion_target = str(_g.get('_ui_emotion_target') or '')",
            ]
        )
    payload_parts = [
        " 'config_local_loaded': bool(getattr(cfg, 'CONFIG_LOCAL_LOADED', False))",
        " 'config_local_error': str(getattr(cfg, 'CONFIG_LOCAL_ERROR', '') or '')",
        " 'config_local_source': str(getattr(cfg, 'CONFIG_LOCAL_SOURCE', '') or '')",
        " 'device_model_hint': str(getattr(cfg, 'DEVICE_MODEL_HINT', '') or '')",
        " 'board_profile': str(getattr(cfg, 'BOARD_PROFILE', '') or '')",
        " 'runtime_status': _runtime_status.get('status')",
        " 'runtime_result_code': _runtime_status.get('result_code')",
        " 'runtime_online': bool(((_runtime_status.get('data') or {}).get('online')))",
        " 'runtime_config_source': str((((_runtime_status.get('data') or {}).get('config_local') or {}).get('source') or ''))",
        " 'catalog_status': _catalog.get('status')",
        " 'catalog_tool_count': len((_catalog.get('data') or {}).get('tools') or [])",
        " 'catalog_result_code': _catalog.get('result_code')",
        " 'fs_read_status': _fs_read.get('status')",
        " 'fs_read_result_code': _fs_read.get('result_code')",
        " 'fs_read_path': ((_fs_read.get('data') or {}).get('path') or '')",
        " 'fs_read_bytes': len((((_fs_read.get('data') or {}).get('content') or '')))",
        " 'loaded_domains': loaded_domains",
        " 'voice_probe': (_g.get('_voice_probe') or {'enabled': False})",
    ]
    if board_smoke:
        payload_parts.extend(
            [
                " 'board_entry_import_ok': _board_entry_import_ok",
                " 'board_entry_module': _board_entry_module",
                " 'board_status': _board_status.get('status')",
                " 'board_result_code': _board_status.get('result_code')",
                " 'audio_status': _audio_status.get('status')",
                " 'audio_result_code': _audio_status.get('result_code')",
                " 'audio_volume_get_status': _audio_volume_get.get('status')",
                " 'audio_volume_get_result_code': _audio_volume_get.get('result_code')",
                " 'audio_volume': ((_audio_volume_get.get('data') or {}).get('volume'))",
                " 'power_status': _power_status.get('status')",
                " 'power_result_code': _power_status.get('result_code')",
                " 'ui_status': _ui_status.get('status')",
                " 'ui_result_code': _ui_status.get('result_code')",
            ]
        )
    if board_write_smoke:
        payload_parts.extend(
            [
                " 'audio_volume_set_status': _audio_volume_set.get('status')",
                " 'audio_volume_set_result_code': _audio_volume_set.get('result_code')",
                " 'audio_volume_set_value': ((_audio_volume_set.get('data') or {}).get('volume'))",
                " 'audio_stream_open_status': _audio_stream_open.get('status')",
                " 'audio_stream_open_result_code': _audio_stream_open.get('result_code')",
                " 'audio_stream_open_value': bool(((((_audio_stream_open.get('data') or {}).get('audio') or {}).get('stream_open'))))",
                " 'audio_stream_close_status': _audio_stream_close.get('status')",
                " 'audio_stream_close_result_code': _audio_stream_close.get('result_code')",
                " 'audio_stream_close_value': bool(((((_audio_stream_close.get('data') or {}).get('audio') or {}).get('stream_open'))))",
                " 'power_charge_initial': _power_charge_initial",
                " 'power_charge_enable_status': _power_charge_enable.get('status')",
                " 'power_charge_enable_result_code': _power_charge_enable.get('result_code')",
                " 'power_charge_enable_value': bool(((((_power_charge_enable.get('data') or {}).get('power') or {}).get('charge_enabled'))))",
                " 'power_charge_disable_status': _power_charge_disable.get('status')",
                " 'power_charge_disable_result_code': _power_charge_disable.get('result_code')",
                " 'power_charge_disable_value': bool(((((_power_charge_disable.get('data') or {}).get('power') or {}).get('charge_enabled'))))",
                " 'power_charge_restore_status': _power_charge_restore.get('status')",
                " 'power_charge_restore_result_code': _power_charge_restore.get('result_code')",
                " 'power_charge_restore_value': bool(((((_power_charge_restore.get('data') or {}).get('power') or {}).get('charge_enabled'))))",
                " 'ui_emotion_initial': _ui_emotion_initial",
                " 'ui_emotion_target': _ui_emotion_target",
                " 'ui_emotion_show_status': _ui_emotion_show.get('status')",
                " 'ui_emotion_show_result_code': _ui_emotion_show.get('result_code')",
                " 'ui_emotion_show_value': str(((((_ui_emotion_show.get('data') or {}).get('ui') or {}).get('current_emoji')) or ''))",
                " 'ui_emotion_restore_status': _ui_emotion_restore_result.get('status')",
                " 'ui_emotion_restore_result_code': _ui_emotion_restore_result.get('result_code')",
                " 'ui_emotion_restore_value': str(((((_ui_emotion_restore_result.get('data') or {}).get('ui') or {}).get('current_emoji')) or ''))",
            ]
        )
    lines.extend(
        [
            "payload = {" + ",".join(payload_parts) + "}",
            "print('QPY_RUNTIME_SMOKE_JSON=' + ujson.dumps(payload))",
        ]
    )
    return lines


def build_exec_script_lines(
    fs_read_path: str,
    fs_read_max_bytes: int,
    board_smoke: bool,
    board_write_smoke: bool,
    voice_chat_message: str,
    voice_chat_timeout_ms: int,
    voice_session_key: str,
    voice_chat_subscribe: bool,
    voice_chat_history_limit: int,
) -> List[str]:
    lines: List[str] = []
    if board_smoke:
        lines.extend(build_exec_board_prepare_lines())
        lines.extend(build_exec_board_import_lines())
        lines.extend(build_exec_bootstrap_lines(True))
    else:
        lines.extend(build_exec_bootstrap_lines(False))
    lines.extend(build_exec_status_lines(fs_read_path, fs_read_max_bytes, board_smoke))
    lines.extend(
        build_exec_voice_chat_lines(
            voice_chat_message,
            int(voice_chat_timeout_ms),
            voice_session_key,
            bool(voice_chat_subscribe),
            int(voice_chat_history_limit),
        )
    )
    if board_smoke and board_write_smoke:
        lines.extend(build_exec_write_lines())
    lines.extend(build_payload_lines(board_smoke, board_write_smoke))
    return lines


def wrap_script_for_repl(lines: List[str], chunk_size: int = 180) -> List[str]:
    script = "\n".join(lines) + "\n"
    chunks: List[str] = []
    step = max(64, int(chunk_size))
    start = 0
    while start < len(script):
        chunks.append(script[start : start + step])
        start += step
    repl_lines = ["_qpy_smoke_chunks=[]"]
    for chunk in chunks:
        repl_lines.append("_qpy_smoke_chunks.append(%r)" % chunk)
    repl_lines.extend(
        [
            "_qpy_smoke_code=''.join(_qpy_smoke_chunks)",
            "exec(_qpy_smoke_code)",
            "del _qpy_smoke_code",
            "del _qpy_smoke_chunks",
        ]
    )
    return repl_lines


def extract_payload(raw: str) -> Dict[str, Any]:
    marker = "QPY_RUNTIME_SMOKE_JSON="
    text = raw or ""
    start = text.rfind(marker)
    if start < 0:
        raise ValueError("smoke payload not found in REPL output")
    start += len(marker)
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        raise ValueError("smoke payload json start not found")
    depth = 0
    in_string = False
    escape = False
    end = -1
    idx = start
    while idx < len(text):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        idx += 1
    if end < 0:
        raise ValueError("smoke payload json end not found")
    return json.loads(text[start:end])


def main() -> int:
    args = build_parser().parse_args()
    board_smoke = bool(args.board_smoke or args.board_write_smoke)
    voice_probe_enabled = bool(str(args.voice_chat_message or "").strip())
    cli = load_qpy_fs_cli()
    raw_import = cli.repl_send_lines(
        args.port,
        int(args.baud),
        build_import_lines(),
        timeout=max(20, int(args.timeout)),
        line_delay_ms=70,
        settle_ms=35000,
    )
    raw = raw_import
    if "QPY_IMPORT_OK" in raw_import:
        exec_lines = wrap_script_for_repl(
            build_exec_script_lines(
                args.fs_read_path,
                int(args.fs_read_max_bytes),
                board_smoke,
                bool(args.board_write_smoke),
                args.voice_chat_message,
                int(args.voice_chat_timeout_ms),
                args.voice_session_key,
                bool(args.voice_chat_subscribe),
                int(args.voice_chat_history_limit),
            )
        )
        exec_settle_ms = 35000 if board_smoke else 15000
        if voice_probe_enabled:
            exec_settle_ms = max(exec_settle_ms, int(args.voice_chat_timeout_ms) + 12000)
        raw_exec = cli.repl_send_lines(
            args.port,
            int(args.baud),
            exec_lines,
            timeout=max(30, int(args.timeout)),
            line_delay_ms=70,
            settle_ms=exec_settle_ms,
        )
        raw = raw_import + "\n" + raw_exec

    summary: Dict[str, Any] = {
        "port": args.port,
        "baud": int(args.baud),
        "fs_read_path": args.fs_read_path,
        "fs_read_max_bytes": int(args.fs_read_max_bytes),
        "board_smoke": board_smoke,
        "board_write_smoke": bool(args.board_write_smoke),
        "voice_probe_enabled": voice_probe_enabled,
        "import_ok": bool("QPY_IMPORT_OK" in raw_import),
        "ok": False,
    }

    try:
        payload = extract_payload(raw)
        summary["payload"] = payload
        ok = bool(
            payload.get("runtime_status") == "succeeded"
            and payload.get("runtime_result_code") == "OK"
            and payload.get("catalog_status") == "succeeded"
            and payload.get("catalog_result_code") == "OK"
            and payload.get("fs_read_status") == "succeeded"
            and payload.get("fs_read_result_code") == "OK"
        )
        if board_smoke:
            ok = bool(
                ok
                and payload.get("board_entry_import_ok")
                and payload.get("board_status") == "succeeded"
                and payload.get("board_result_code") == "OK"
                and payload.get("audio_status") == "succeeded"
                and payload.get("audio_result_code") == "OK"
                and payload.get("audio_volume_get_status") == "succeeded"
                and payload.get("audio_volume_get_result_code") == "OK"
                and payload.get("power_status") == "succeeded"
                and payload.get("power_result_code") == "OK"
                and payload.get("ui_status") == "succeeded"
                and payload.get("ui_result_code") == "OK"
            )
            if args.board_write_smoke:
                ok = bool(
                    ok
                    and payload.get("audio_volume_set_status") == "succeeded"
                    and payload.get("audio_volume_set_result_code") == "OK"
                    and payload.get("audio_stream_open_status") == "succeeded"
                    and payload.get("audio_stream_open_result_code") == "OK"
                    and payload.get("audio_stream_open_value") is True
                    and payload.get("audio_stream_close_status") == "succeeded"
                    and payload.get("audio_stream_close_result_code") == "OK"
                    and payload.get("audio_stream_close_value") is False
                    and payload.get("power_charge_enable_status") == "succeeded"
                    and payload.get("power_charge_enable_result_code") == "OK"
                    and payload.get("power_charge_enable_value") is True
                    and payload.get("power_charge_disable_status") == "succeeded"
                    and payload.get("power_charge_disable_result_code") == "OK"
                    and payload.get("power_charge_disable_value") is False
                    and payload.get("power_charge_restore_status") == "succeeded"
                    and payload.get("power_charge_restore_result_code") == "OK"
                    and payload.get("power_charge_restore_value")
                    == payload.get("power_charge_initial")
                    and payload.get("ui_emotion_show_status") == "succeeded"
                    and payload.get("ui_emotion_show_result_code") == "OK"
                    and payload.get("ui_emotion_show_value") == payload.get("ui_emotion_target")
                    and payload.get("ui_emotion_restore_status") == "succeeded"
                    and payload.get("ui_emotion_restore_result_code") == "OK"
                    and payload.get("ui_emotion_restore_value")
                    == (payload.get("ui_emotion_initial") or "neutral")
                )
        if voice_probe_enabled:
            voice_probe = payload.get("voice_probe") or {}
            ok = bool(ok and voice_probe.get("enabled") and voice_probe.get("ok"))
        summary["ok"] = ok
    except Exception as e:
        summary["error"] = str(e)

    if args.include_raw:
        summary["raw_import"] = raw_import
        if "QPY_IMPORT_OK" in raw_import:
            summary["raw"] = raw
        else:
            summary["raw"] = raw_import

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("port:", summary["port"])
        print("ok:", summary["ok"])
        if "payload" in summary:
            print("runtime_status:", summary["payload"].get("runtime_status"))
            print("catalog_status:", summary["payload"].get("catalog_status"))
            print("catalog_tool_count:", summary["payload"].get("catalog_tool_count"))
            print("fs_read_status:", summary["payload"].get("fs_read_status"))
            print("fs_read_bytes:", summary["payload"].get("fs_read_bytes"))
            if board_smoke:
                print("board_status:", summary["payload"].get("board_status"))
                print("audio_status:", summary["payload"].get("audio_status"))
                print("power_status:", summary["payload"].get("power_status"))
                print("ui_status:", summary["payload"].get("ui_status"))
                if args.board_write_smoke:
                    print("audio_volume_set_status:", summary["payload"].get("audio_volume_set_status"))
                    print("audio_stream_open_status:", summary["payload"].get("audio_stream_open_status"))
                    print("audio_stream_close_status:", summary["payload"].get("audio_stream_close_status"))
                    print("power_charge_restore_status:", summary["payload"].get("power_charge_restore_status"))
                    print("ui_emotion_restore_status:", summary["payload"].get("ui_emotion_restore_status"))
        if "error" in summary:
            print("error:", summary["error"])
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
