#!/usr/bin/env python3
"""
Run board-level qpyclaw voice smoke against an EC800MCNLE device.

Modes:
1. text    -> /usr/qpyclaw_board_voice_smoke.py
2. session -> /usr/qpyclaw_board_voice_session.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
import time
from typing import Any, Dict, List

QPY_DEVICE_FS_CLI = pathlib.Path(
    r"C:\Users\kingd\.codex\skills\quecpython-dev\scripts\qpy_device_fs_cli.py"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run qpyclaw board voice smoke over QuecPython REPL."
    )
    parser.add_argument("--port", default="COM6", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument(
        "--mode",
        choices=["text", "session"],
        default="text",
        help="Smoke mode. text uses qpyclaw_board_voice_smoke, session uses qpyclaw_board_voice_session.",
    )
    parser.add_argument(
        "--message",
        default="Please reply with one short sentence and include the word qpysmoke.",
        help="Prompt sent to the board voice helper.",
    )
    parser.add_argument(
        "--open-audio",
        action="store_true",
        help="Enable local audio path in the board helper.",
    )
    parser.add_argument(
        "--soft-reset",
        action="store_true",
        help="Soft reset the device before running smoke.",
    )
    parser.add_argument(
        "--reset-wait-seconds",
        type=float,
        default=12.0,
        help="Host wait time after soft reset.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="REPL timeout seconds.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=70.0,
        help="Host settle time after the smoke script is sent.",
    )
    parser.add_argument(
        "--session-post-wait-ms",
        type=int,
        default=3000,
        help="Extra device wait before collecting final session status in session mode.",
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


def wrap_script_for_repl(script: str, chunk_size: int = 180) -> List[str]:
    chunks: List[str] = []
    start = 0
    size = max(64, int(chunk_size))
    while start < len(script):
        chunks.append(script[start : start + size])
        start += size
    lines = ["_qpy_smoke_chunks=[]"]
    for chunk in chunks:
        lines.append("_qpy_smoke_chunks.append(%r)" % chunk)
    lines.extend(
        [
            "_qpy_smoke_code=''.join(_qpy_smoke_chunks)",
            "exec(_qpy_smoke_code)",
            "del _qpy_smoke_code",
            "del _qpy_smoke_chunks",
        ]
    )
    return lines


def extract_marked_json_object(raw: str, marker: str) -> Dict[str, Any]:
    text = str(raw or "")
    anchor = text.rfind(marker)
    if anchor < 0:
        raise ValueError("marker not found: %s" % marker)
    start = text.find("{", anchor + len(marker))
    if start < 0:
        raise ValueError("json start not found for marker: %s" % marker)
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
        raise ValueError("json end not found for marker: %s" % marker)
    return json.loads(text[start:end])


def build_smoke_script(mode: str, message: str, open_audio: bool, session_post_wait_ms: int) -> str:
    helper_module = "qpyclaw_board_voice_smoke"
    helper_call = (
        "_result=_helper.voice_text_smoke(message=%r, timeout_ms=45000, subscribe=False, open_audio=%s)"
        % (str(message or ""), "True" if open_audio else "False")
    )
    extra_lines = [
        "import qpyclaw_node",
        "_node=getattr(qpyclaw_node,'_LAST_NODE',None)",
        "_ext=getattr(_node,'extension',None)",
        "_board=getattr(_ext,'board',None)",
        "_ui=getattr(_board,'ui',None)",
        "_voice=getattr(_board,'voice',None)",
        "_ui_snapshot=(_ui.snapshot() if _ui is not None else {})",
        "_session_snapshot=(_voice.snapshot() if _voice is not None else {})",
    ]
    if mode == "session":
        helper_module = "qpyclaw_board_voice_session"
        helper_call = (
            "_result=_helper.voice_session_smoke(message=%r, open_audio=%s)"
            % (str(message or ""), "True" if open_audio else "False")
        )
        extra_lines = [
            "import utime",
            "utime.sleep_ms(%d)" % max(0, int(session_post_wait_ms)),
            "_session_snapshot=_helper.voice_session_status(open_audio=%s)" % ("True" if open_audio else "False"),
            "import qpyclaw_node",
            "_node=getattr(qpyclaw_node,'_LAST_NODE',None)",
            "_ext=getattr(_node,'extension',None)",
            "_board=getattr(_ext,'board',None)",
            "_ui=getattr(_board,'ui',None)",
            "_ui_snapshot=(_ui.snapshot() if _ui is not None else {})",
        ]
    lines = [
        "import sys as _sys",
        "import gc",
        "import ujson",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='/usr/board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "gc.collect()",
        "_err=''",
        "_result={}",
        "_ui_snapshot={}",
        "_session_snapshot={}",
        "try:",
        " import %s as _helper" % helper_module,
        " %s" % helper_call,
    ]
    for item in extra_lines:
        lines.append(" " + item)
    lines.extend(
        [
            "except Exception as _e:",
            " _err=repr(_e)",
            "print('QPY_BOARD_VOICE_SMOKE_JSON=' + ujson.dumps({'mode': %r, 'result': _result, 'ui': _ui_snapshot, 'session': _session_snapshot, 'err': _err}))"
            % str(mode),
        ]
    )
    return "\n".join(lines) + "\n"


def run_soft_reset(cli, port: str, baud: int, timeout: int, wait_seconds: float) -> Dict[str, Any]:
    raw = cli.repl_send_lines(
        port,
        int(baud),
        ["import machine", "machine.SoftReset()"],
        timeout=max(20, int(timeout)),
        line_delay_ms=80,
        settle_ms=3000,
    )
    if wait_seconds > 0:
        time.sleep(float(wait_seconds))
    return {
        "ok": "SoftReset:" in raw or "MPY: soft reboot" in raw,
        "raw": raw,
    }


def main() -> int:
    args = build_parser().parse_args()
    cli = load_qpy_fs_cli()
    summary: Dict[str, Any] = {
        "port": args.port,
        "baud": int(args.baud),
        "mode": args.mode,
        "open_audio": bool(args.open_audio),
        "soft_reset": bool(args.soft_reset),
        "ok": False,
    }

    if args.soft_reset:
        summary["reset"] = run_soft_reset(
            cli,
            args.port,
            int(args.baud),
            int(args.timeout),
            float(args.reset_wait_seconds),
        )

    script = build_smoke_script(
        args.mode,
        args.message,
        bool(args.open_audio),
        int(args.session_post_wait_ms),
    )
    raw = cli.repl_send_lines(
        args.port,
        int(args.baud),
        wrap_script_for_repl(script),
        timeout=max(30, int(args.timeout)),
        line_delay_ms=70,
        settle_ms=max(8000, int(float(args.settle_seconds) * 1000)),
    )
    try:
        payload = extract_marked_json_object(raw, "QPY_BOARD_VOICE_SMOKE_JSON=")
        summary["payload"] = payload
        payload_err = str(payload.get("err") or "").strip()
        if args.mode == "session":
            session_payload = payload.get("session") or payload.get("result") or {}
            summary["ok"] = bool(session_payload.get("last_result_ok")) and (not payload_err)
        else:
            summary["ok"] = bool((payload.get("result") or {}).get("ok")) and (not payload_err)
    except Exception as exc:
        summary["error"] = str(exc)
        summary["ok"] = False

    if args.include_raw:
        summary["raw"] = raw

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("mode:", summary["mode"])
        print("ok:", summary["ok"])
        if "payload" in summary:
            print("reply_text:", ((summary["payload"].get("result") or {}).get("reply_text") or ""))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
