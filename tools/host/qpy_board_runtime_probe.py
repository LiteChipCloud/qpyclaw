#!/usr/bin/env python3
"""
Launch and probe the EC800MCNLE board runtime from the host side.

Workflow:
1. Optionally dispatch `/usr/qpyclaw_board_dispatch.py` on the device.
2. Wait for the board thread to bring `qpyclaw-node` online.
3. Read `qpyclaw_node.debug_snapshot()`.
4. Execute a small set of local board/runtime commands.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys
import time
from typing import Any, Dict, List

QPY_DEVICE_FS_CLI = pathlib.Path(
    r"C:\Users\kingd\.codex\skills\quecpython-dev\scripts\qpy_device_fs_cli.py"
)

DEFAULT_COMMANDS = [
    "qpy.runtime.status",
    "qpy.board.status",
    "qpy.audio.status",
    "qpy.power.status",
    "qpy.ui.status",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch qpyclaw board dispatch and probe runtime health."
    )
    parser.add_argument("--port", default="COM19", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument("--timeout", type=int, default=90, help="REPL timeout seconds.")
    parser.add_argument(
        "--dispatch-path",
        default="/usr/qpyclaw_board_dispatch.py",
        help="Device script used to start board runtime.",
    )
    parser.add_argument(
        "--skip-dispatch",
        action="store_true",
        help="Do not re-run dispatch; only probe current runtime state.",
    )
    parser.add_argument(
        "--dispatch-settle-seconds",
        type=float,
        default=6.0,
        help="Host wait time after dispatch before probing.",
    )
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="Additional local command to execute. Defaults are used when omitted.",
    )
    parser.add_argument(
        "--include-raw",
        action="store_true",
        help="Include raw REPL transcripts in JSON output.",
    )
    parser.add_argument(
        "--probe-attempts",
        type=int,
        default=3,
        help="Maximum probe attempts after dispatch.",
    )
    parser.add_argument(
        "--probe-retry-seconds",
        type=float,
        default=2.0,
        help="Wait time between probe retries.",
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


def normalize_exec_path(path: str) -> str:
    text = str(path or "").strip().replace("\\", "/")
    while text.startswith("/"):
        text = text[1:]
    return text or "usr/qpyclaw_board_dispatch.py"


def dispatch_module_name(dispatch_path: str) -> str:
    exec_path = normalize_exec_path(dispatch_path)
    name = pathlib.PurePosixPath(exec_path).name
    if name.lower().endswith(".py"):
        name = name[:-3]
    return name or "qpyclaw_board_dispatch"


def build_dispatch_lines(dispatch_path: str) -> List[str]:
    module_name = dispatch_module_name(dispatch_path)
    return [
        "import sys as _sys",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_mods=getattr(_sys,'modules',None)",
        "(_mods.pop('%s') if (_mods is not None and '%s' in _mods) else None)" % (module_name, module_name),
        "import %s as _dispatch" % module_name,
        "print('QPY_BOARD_DISPATCH_OK=' + str(_dispatch.main()))",
    ]


def build_probe_lines(commands: List[str]) -> List[str]:
    lines = [
        "import sys as _sys",
        "import ujson",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='/usr/board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "import qpyclaw_node",
        "_node=getattr(qpyclaw_node, '_LAST_NODE', None)",
        "_snapshot_fn=getattr(qpyclaw_node, 'debug_snapshot', None)",
        "_snapshot=({'has_runtime': False, 'has_state': False, 'has_transport': False, 'has_runner': False, 'has_worker': False, 'boot_event_queued': False, 'online': False, 'last_exception': 'debug_snapshot_missing', 'state': None} if (_node is None and _snapshot_fn is None) else (_node.debug_snapshot() if (_node is not None and hasattr(_node, 'debug_snapshot')) else _snapshot_fn()))",
        "_payload={'snapshot': _snapshot, 'commands': []}",
    ]
    idx = 0
    for tool in commands:
        safe_tool = single_quote_qpy(tool)
        request_id = "board-probe-%d" % idx
        lines.append(
            "_payload['commands'].append({'tool':'%s','result':({'status':'failed','result_code':'RUNTIME_NOT_STARTED','tool':'%s','requested_tool':'%s','error':'qpyclaw board runtime not started','data':None} if _node is None else _node.execute_local('%s', {}, '%s'))})"
            % (safe_tool, safe_tool, safe_tool, safe_tool, request_id)
        )
        idx += 1
    lines.append("print('QPY_BOARD_RUNTIME_PROBE_JSON=' + ujson.dumps(_payload))")
    return lines


def extract_marked_json_object(raw: str, marker: str) -> Dict[str, Any]:
    text = str(raw or "")
    anchor = text.rfind(marker)
    if anchor < 0:
        raise ValueError("marker not found: %s" % marker)
    start = text.find("{", anchor + len(marker))
    if start < 0:
        raise ValueError("json object start not found for marker: %s" % marker)
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
        raise ValueError("json object end not found for marker: %s" % marker)
    return json.loads(text[start:end])


def run_dispatch(cli, port: str, baud: int, dispatch_path: str, timeout: int) -> Dict[str, Any]:
    raw = cli.repl_send_lines(
        port,
        int(baud),
        build_dispatch_lines(dispatch_path),
        timeout=max(15, int(timeout)),
        line_delay_ms=80,
        settle_ms=3500,
    )
    has_error = any(x in raw for x in ["ERR:", "Traceback", "ParserError", "At line:"])
    ok = bool("QPY_BOARD_DISPATCH_OK=True" in raw) and (not has_error)
    return {
        "ok": ok,
        "dispatch_path": dispatch_path,
        "raw": raw,
    }


def run_probe(
    cli,
    port: str,
    baud: int,
    commands: List[str],
    timeout: int,
    attempts: int,
    retry_seconds: float,
) -> Dict[str, Any]:
    max_attempts = max(1, int(attempts))
    wait_seconds = max(0.0, float(retry_seconds))
    last_raw = ""
    last_payload: Dict[str, Any] = {}
    last_error = ""
    attempt = 0
    while attempt < max_attempts:
        raw = cli.repl_send_lines(
            port,
            int(baud),
            build_probe_lines(commands),
            timeout=max(20, int(timeout)),
            line_delay_ms=90,
            settle_ms=3000 + (attempt * 1500),
        )
        last_raw = raw
        try:
            payload = extract_marked_json_object(raw, "QPY_BOARD_RUNTIME_PROBE_JSON=")
            last_payload = payload
            snapshot = payload.get("snapshot") or {}
            results = payload.get("commands") or []
            if bool(snapshot.get("online")) and len(results) >= len(commands):
                return {
                    "raw": raw,
                    "payload": payload,
                    "attempts_used": attempt + 1,
                    "error": "",
                }
            last_error = "runtime not online yet"
        except Exception as exc:
            last_error = str(exc)
        attempt += 1
        if attempt < max_attempts and wait_seconds:
            time.sleep(wait_seconds)
    return {
        "raw": last_raw,
        "payload": last_payload,
        "attempts_used": max_attempts,
        "error": last_error,
    }


def summarize_ok(probe_payload: Dict[str, Any], commands: List[str]) -> bool:
    snapshot = probe_payload.get("snapshot") or {}
    ok = bool(
        snapshot.get("has_runtime")
        and snapshot.get("online")
        and snapshot.get("has_extension")
        and snapshot.get("extension_name")
    )
    results = probe_payload.get("commands") or []
    if len(results) < len(commands):
        return False
    for item in results:
        result = item.get("result") or {}
        if result.get("status") != "succeeded":
            return False
        if result.get("result_code") != "OK":
            return False
    return ok


def build_text_summary(summary: Dict[str, Any]) -> str:
    lines = [
        "port: %s" % summary["port"],
        "ok: %s" % summary["ok"],
        "used_existing_runtime: %s" % bool(summary.get("used_existing_runtime")),
        "dispatch_attempted: %s" % bool(summary.get("dispatch_attempted")),
        "dispatch_ok: %s" % summary["dispatch_ok"],
    ]
    payload = summary.get("payload") or {}
    snapshot = payload.get("snapshot") or {}
    state = snapshot.get("state") or {}
    lines.extend(
        [
            "online: %s" % bool(snapshot.get("online")),
            "extension: %s" % str(snapshot.get("extension_name") or ""),
            "node_id: %s" % str(state.get("node_id") or ""),
            "logical_device_id: %s" % str(state.get("logical_device_id") or ""),
        ]
    )
    for item in payload.get("commands") or []:
        result = item.get("result") or {}
        lines.append(
            "%s: %s/%s"
            % (
                str(item.get("tool") or ""),
                str(result.get("status") or ""),
                str(result.get("result_code") or ""),
            )
        )
    if summary.get("error"):
        lines.append("error: %s" % summary["error"])
    if summary.get("dispatch_warning"):
        lines.append("dispatch_warning: %s" % summary["dispatch_warning"])
    if summary.get("probe_warning"):
        lines.append("probe_warning: %s" % summary["probe_warning"])
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    cli = load_qpy_fs_cli()
    commands = [str(x).strip() for x in (args.command or []) if str(x).strip()]
    if not commands:
        commands = list(DEFAULT_COMMANDS)

    summary: Dict[str, Any] = {
        "port": args.port,
        "baud": int(args.baud),
        "dispatch_path": args.dispatch_path,
        "dispatch_wait_seconds": float(args.dispatch_settle_seconds),
        "probe_attempts": int(args.probe_attempts),
        "probe_retry_seconds": float(args.probe_retry_seconds),
        "commands": commands,
        "dispatch_attempted": False,
        "dispatch_ok": bool(args.skip_dispatch),
        "used_existing_runtime": False,
        "ok": False,
    }

    raw_dispatch = ""
    raw_probe = ""
    try:
        pre_probe = run_probe(
            cli,
            args.port,
            int(args.baud),
            commands,
            int(args.timeout),
            1,
            0.0,
        )
        pre_payload = pre_probe.get("payload") or {}
        if summarize_ok(pre_payload, commands):
            raw_probe = pre_probe.get("raw") or ""
            summary["used_existing_runtime"] = True
            summary["probe_attempts_used"] = int(pre_probe.get("attempts_used") or 0)
            summary["payload"] = pre_payload
            summary["ok"] = True
        else:
            if not args.skip_dispatch:
                summary["dispatch_attempted"] = True
                dispatch = run_dispatch(cli, args.port, int(args.baud), args.dispatch_path, int(args.timeout))
                summary["dispatch_ok"] = bool(dispatch.get("ok"))
                raw_dispatch = dispatch.get("raw") or ""
                if not dispatch.get("ok"):
                    summary["dispatch_warning"] = "board dispatch did not report success token"
                wait_seconds = max(0.0, float(args.dispatch_settle_seconds))
                if wait_seconds:
                    time.sleep(wait_seconds)

            probe = run_probe(
                cli,
                args.port,
                int(args.baud),
                commands,
                int(args.timeout),
                int(args.probe_attempts),
                float(args.probe_retry_seconds),
            )
            raw_probe = probe.get("raw") or ""
            payload = probe.get("payload") or {}
            summary["probe_attempts_used"] = int(probe.get("attempts_used") or 0)
            summary["payload"] = payload
            if probe.get("error"):
                summary["probe_warning"] = str(probe.get("error") or "")
            summary["ok"] = summarize_ok(payload, commands)
    except Exception as exc:
        summary["error"] = str(exc)

    if args.include_raw:
        if raw_dispatch:
            summary["raw_dispatch"] = raw_dispatch
        if raw_probe:
            summary["raw_probe"] = raw_probe

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(build_text_summary(summary))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
