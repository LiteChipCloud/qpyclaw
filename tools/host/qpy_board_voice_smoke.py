#!/usr/bin/env python3
"""
Run board-level qpyclaw voice smoke against an EC800MCNLE device.

Modes:
1. text    -> create board-aware runtime and call `qpyclaw_node.voice_chat(...)`
2. session -> create board-aware runtime and inject transcript through the board voice controller
3. asr     -> exec `_main.py`, let runtime auto-listen, user speaks, verify ASR transcript
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
        choices=["text", "session", "asr"],
        default="text",
        help="Smoke mode. text=voice_chat, session=board voice controller, asr=real mic ASR verify.",
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
        "--asr-boot-wait",
        type=float,
        default=30.0,
        help="(asr) Seconds to wait after exec _main.py for runtime to initialize.",
    )
    parser.add_argument(
        "--asr-handsoff-seconds",
        type=float,
        default=60.0,
        help="(asr) Seconds to keep REPL silent while user speaks into mic.",
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
    lines = [
        "import sys as _sys",
        "import gc",
        "import ujson",
        "import utime",
        "_p='/usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='usr'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='/usr/board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "_p='board'; _dummy=(_p in _sys.path) or _sys.path.append(_p)",
        "gc.collect()",
        "_err=''",
        "_result={}",
        "_ui_snapshot={}",
        "_session_snapshot={}",
        "def _ticks_ms():",
        " try:",
        "  return utime.ticks_ms()",
        " except Exception:",
        "  try:",
        "   return int(utime.time() * 1000)",
        "  except Exception:",
        "   return 0",
        "def _ticks_add(base_ms, delta_ms):",
        " try:",
        "  return utime.ticks_add(base_ms, int(delta_ms))",
        " except Exception:",
        "  return int(base_ms or 0) + int(delta_ms or 0)",
        "def _ticks_diff(left_ms, right_ms):",
        " try:",
        "  return utime.ticks_diff(left_ms, right_ms)",
        " except Exception:",
        "  return int(left_ms or 0) - int(right_ms or 0)",
        "def _sleep_ms(delay_ms):",
        " try:",
        "  utime.sleep_ms(int(delay_ms or 0))",
        " except Exception:",
        "  pass",
        "def _take_ui_snapshot(board):",
        " ui = getattr(board, 'ui', None)",
        " return ui.snapshot() if ui is not None else {}",
        "def _take_voice_snapshot(voice):",
        " return voice.snapshot() if voice is not None else {}",
        "def _ensure_runtime(open_audio=False, enable_voice=False, voice_auto_start=False):",
        " import qpyclaw_node",
        " node = getattr(qpyclaw_node, '_LAST_NODE', None)",
        " board = None",
        " if node is not None:",
        "  try:",
        "   snapshot = node.debug_snapshot()",
        "  except Exception:",
        "   snapshot = {}",
        "  board = getattr(getattr(node, 'extension', None), 'board', None)",
        "  if (not bool(snapshot.get('has_extension'))) or board is None:",
        "   node = None",
        "   board = None",
        " if node is None:",
        "  from board_bootstrap import create_qpyclaw_extension",
        "  extension = create_qpyclaw_extension(enable_charge=True, enable_display=True, open_audio=bool(open_audio), enable_voice=bool(enable_voice), voice_auto_start=bool(voice_auto_start))",
        "  node = qpyclaw_node.create_runtime(extension=extension)",
        "  board = getattr(getattr(node, 'extension', None), 'board', None)",
        " voice = getattr(board, 'voice', None)",
        " if voice is not None:",
        "  try:",
        "   voice.configure(enabled=bool(enable_voice), auto_start=bool(voice_auto_start), audio_enabled=bool(open_audio))",
        "  except Exception:",
        "   pass",
        " return qpyclaw_node, node, board, voice",
        "def _pump_runtime_until(node, voice, timeout_ms=45000, step_delay_ms=20, baseline_turn_count=None):",
        " deadline = _ticks_add(_ticks_ms(), int(timeout_ms))",
        " snapshot = _take_voice_snapshot(voice)",
        " if baseline_turn_count is None:",
        "  baseline_turn_count = int(snapshot.get('turn_count') or 0)",
        " while True:",
        "  node.step()",
        "  snapshot = _take_voice_snapshot(voice)",
        "  if int(snapshot.get('turn_count') or 0) > int(baseline_turn_count or 0):",
        "   if (not snapshot.get('worker_busy')) and int(snapshot.get('pending_transcripts') or 0) <= 0:",
        "    return snapshot",
        "  if snapshot.get('last_result_ok') is not None and (not snapshot.get('worker_busy')) and int(snapshot.get('pending_transcripts') or 0) <= 0:",
        "   return snapshot",
        "  if _ticks_diff(deadline, _ticks_ms()) <= 0:",
        "   return snapshot",
        "  _sleep_ms(step_delay_ms)",
        "try:",
    ]
    if mode == "session":
        lines.extend(
            [
                " qpyclaw_node, node, board, voice = _ensure_runtime(open_audio=%s, enable_voice=True, voice_auto_start=True)" % ("True" if open_audio else "False"),
                " if voice is None:",
                "  raise Exception('board voice controller unavailable')",
                " before = _take_voice_snapshot(voice)",
                " baseline_turn_count = int(before.get('turn_count') or 0)",
                " voice.start()",
                " _result = voice.inject_transcript(%r, source='host-smoke')" % str(message or ""),
                " _sleep_ms(%d)" % max(0, int(session_post_wait_ms)),
                " _session_snapshot = _pump_runtime_until(node, voice, timeout_ms=45000, step_delay_ms=20, baseline_turn_count=baseline_turn_count)",
                " _ui_snapshot = _take_ui_snapshot(board)",
                " _result = {'ok': bool(_session_snapshot.get('last_result_ok')), 'controller': _result, 'final': _session_snapshot}",
            ]
        )
    else:
        lines.extend(
            [
                " qpyclaw_node, node, board, voice = _ensure_runtime(open_audio=%s, enable_voice=True, voice_auto_start=False)" % ("True" if open_audio else "False"),
                " _result = qpyclaw_node.voice_chat(%r, timeout_ms=45000, subscribe=False, runtime=node)" % str(message or ""),
                " _ui_snapshot = _take_ui_snapshot(board)",
                " _session_snapshot = _take_voice_snapshot(voice)",
            ]
        )
    lines.extend(
        [
            "except Exception as _e:",
            " _err = repr(_e)",
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


def _repl_kv(cli, port: str, baud: int, lines: List[str],
             timeout: int = 15, settle_ms: int = 3000) -> Dict[str, str]:
    """Send REPL lines and parse KEY=VALUE output into a dict."""
    raw = cli.repl_send_lines(port, baud, lines, timeout=timeout, settle_ms=settle_ms)
    results: Dict[str, str] = {"__raw__": raw}
    for token in raw.replace("<CR>", "").replace("<LF>", "\n").split("\n"):
        t = token.strip().lstrip("> ").strip()
        if t and "=" in t and not t.startswith(">>>") and not t.startswith("_q"):
            k, _, v = t.partition("=")
            results[k] = v
    return results


_RUNTIME_REFS = [
    'import sys as _sys,gc',
    '_p="/usr"; _dummy=(_p in _sys.path) or _sys.path.append(_p)',
    '_p="/usr/board"; _dummy=(_p in _sys.path) or _sys.path.append(_p)',
    'import qpyclaw_node',
    '_n=getattr(qpyclaw_node,"_LAST_NODE",None)',
    '_e=getattr(_n,"extension",None) if _n else None',
    '_b=getattr(_e,"board",None) if _e else None',
    '_v=getattr(_b,"voice",None) if _b else None',
]


def run_asr_smoke(cli, port: str, baud: int, args) -> Dict[str, Any]:
    """ASR smoke: soft-reset, exec _main.py, hands-off, then verify voice state."""
    summary: Dict[str, Any] = {"mode": "asr", "ok": False}

    # Step 0: soft reset for a clean slate
    print("[asr] soft-resetting device ...")
    reset_result = run_soft_reset(cli, port, baud, int(args.timeout), 8.0)
    summary["soft_reset"] = reset_result.get("ok", False)
    if not reset_result.get("ok"):
        summary["error"] = "soft reset failed"
        return summary

    # Step 1: exec _main.py
    print("[asr] exec _main.py ...")
    cli.repl_send_lines(
        port, baud,
        ['exec(open("/usr/_main.py").read())'],
        timeout=max(15, int(args.timeout)),
        settle_ms=5000,
    )
    boot_wait = float(args.asr_boot_wait)
    print("[asr] waiting %.0fs for runtime boot ..." % boot_wait)
    time.sleep(boot_wait)

    # Step 2: verify voice controller ready (retry a few times)
    voice_ready = False
    for attempt in range(4):
        r = _repl_kv(cli, port, baud, _RUNTIME_REFS + [
            'print("VOICE=" + str(_v is not None))',
            'print("STATE=" + str(_v.state if _v else "N/A"))',
        ], timeout=15, settle_ms=2000)
        if r.get("VOICE") == "True":
            voice_ready = True
            break
        print("[asr] voice not ready (attempt %d/4), waiting 10s ..." % (attempt + 1))
        time.sleep(10)
    summary["boot_voice_ready"] = voice_ready
    summary["boot_state"] = r.get("STATE", "")
    if not voice_ready:
        summary["error"] = "voice controller not ready after boot"
        summary["boot_raw"] = r.get("__raw__", "")
        return summary

    # Step 3: hands-off — user speaks
    handsoff = float(args.asr_handsoff_seconds)
    print("="*60)
    print("  HANDS-OFF for %.0fs — SPEAK into the mic now!" % handsoff)
    print("  Say wake word + sentence (e.g. '小智小智，今天天气怎么样')")
    print("="*60)
    time.sleep(handsoff)

    # Step 4: query result once
    r = _repl_kv(cli, port, baud, [
        'print("STATE=" + str(_v.state))',
        'print("TURNS=" + str(_v.turn_count))',
        'print("TRANSCRIPT=" + str(_v.last_transcript))',
        'print("TSRC=" + str(_v.last_transcript_source))',
        'print("REPLY=" + str((_v.last_reply_text or "")[:200]))',
        'print("ERROR=" + str(_v.last_error))',
        'print("RESULT_OK=" + str(_v.last_result_ok))',
    ], timeout=15, settle_ms=3000)
    summary["state"] = r.get("STATE", "")
    summary["turns"] = int(r.get("TURNS", "0") or 0)
    summary["transcript"] = r.get("TRANSCRIPT", "")
    summary["transcript_source"] = r.get("TSRC", "")
    summary["reply"] = r.get("REPLY", "")
    summary["error"] = r.get("ERROR", "")
    summary["result_ok"] = r.get("RESULT_OK", "")
    summary["ok"] = summary["turns"] > 0 and r.get("RESULT_OK") == "True"
    if args.include_raw:
        summary["raw"] = r.get("__raw__", "")
    return summary


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

    if args.mode == "asr":
        summary = run_asr_smoke(cli, args.port, int(args.baud), args)
        summary["port"] = args.port
        summary["baud"] = int(args.baud)
    else:
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
        if summary.get("transcript"):
            print("transcript:", summary["transcript"])
        if summary.get("reply"):
            print("reply:", summary["reply"])
        if "payload" in summary:
            print("reply_text:", ((summary["payload"].get("result") or {}).get("reply_text") or ""))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
