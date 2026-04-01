#!/usr/bin/env python3
"""
Verify end-to-end ASR on an EC800MCNLE device with the DashScope voice sidecar.

Modes
-----
- **natural** (default): exec ``_main.py``, let the runtime auto-enter
  ``listening`` via ``BOARD_DEBUG_FORCE_LISTEN_ON_BOOT``, then query the
  final voice state once.  The user should speak into the mic during the
  hands-off window.  No REPL interaction happens while the device is
  listening so KWS / VAD are not disrupted.

- **manual**: exec ``_main.py``, then manually set up the audio capture
  pipeline (stop KWS → open stream → frame callback → capture pump → VAD),
  record for ``--record-seconds``, take the capture, base64-encode, POST to
  the sidecar ``/api/asr``, and print the transcript.

Both modes produce a JSON summary on ``--json``.

Examples
--------
::

    # Natural flow — speak after "HANDS-OFF" prompt
    python qpy_voice_asr_smoke.py --port COM6 --json

    # Manual capture — 5s recording window
    python qpy_voice_asr_smoke.py --port COM6 --mode manual --record-seconds 5 --json
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


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def load_qpy_fs_cli():
    scripts_dir = QPY_DEVICE_FS_CLI.parent
    sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("qpy_device_fs_cli", QPY_DEVICE_FS_CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="E2E ASR smoke for qpyclaw voice chain.")
    p.add_argument("--port", default="COM6", help="REPL serial port.")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument(
        "--mode", choices=["natural", "manual"], default="natural",
        help="natural = runtime auto-listen; manual = host-driven capture + HTTP ASR.",
    )
    p.add_argument("--boot-wait", type=float, default=30.0,
                   help="Seconds to wait after exec _main.py before first status check.")
    p.add_argument("--boot-retry-wait", type=float, default=30.0,
                   help="Extra seconds if first status check shows voice not ready.")
    p.add_argument("--handsoff-seconds", type=float, default=60.0,
                   help="(natural) Seconds to keep REPL silent while user speaks.")
    p.add_argument("--record-seconds", type=float, default=5.0,
                   help="(manual) Seconds to capture audio.")
    p.add_argument("--asr-url", default="http://124.70.221.88:8788/api/asr")
    p.add_argument("--asr-token", default="")
    p.add_argument("--timeout", type=int, default=90, help="Per-REPL-call timeout.")
    p.add_argument("--include-raw", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def repl_send(cli, port: str, baud: int, lines: List[str],
              timeout: int = 30, settle_ms: int = 3000) -> Dict[str, str]:
    """Send REPL lines and parse ``KEY=VALUE`` output into a dict."""
    raw = cli.repl_send_lines(port, baud, lines, timeout=timeout, settle_ms=settle_ms)
    results: Dict[str, str] = {}
    results["__raw__"] = raw
    for token in raw.replace("<CR>", "").replace("<LF>", "\n").split("\n"):
        t = token.strip().lstrip("> ").strip()
        if t and "=" in t and not t.startswith(">>>") and not t.startswith("_q"):
            k, _, v = t.partition("=")
            results[k] = v
    return results


# ---------------------------------------------------------------------------
# boot
# ---------------------------------------------------------------------------

_RUNTIME_REFS = [
    'import sys,gc; sys.path.append("/usr"); sys.path.append("/usr/board")',
    'import qpyclaw_node',
    '_n=getattr(qpyclaw_node,"_LAST_NODE",None)',
    '_e=getattr(_n,"extension",None) if _n else None',
    '_b=getattr(_e,"board",None) if _e else None',
    '_a=getattr(_b,"audio",None) if _b else None',
    '_v=getattr(_b,"voice",None) if _b else None',
]


def boot_runtime(cli, port: str, baud: int, timeout: int,
                 boot_wait: float, retry_wait: float) -> Dict[str, str]:
    """Exec ``_main.py`` and wait until ``_v`` (voice controller) is available."""
    cli.repl_send_lines(
        port, baud,
        ['exec(open("/usr/_main.py").read())'],
        timeout=max(15, timeout), settle_ms=5000,
    )
    time.sleep(boot_wait)
    r = repl_send(cli, port, baud, _RUNTIME_REFS + [
        'print("VOICE=" + str(_v is not None))',
        'print("STATE=" + str(_v.state if _v else "N/A"))',
        'print("KWS=" + str(_v.kws_running if _v else "N/A"))',
    ], timeout=15, settle_ms=2000)
    if r.get("VOICE") != "True" and retry_wait > 0:
        time.sleep(retry_wait)
        r = repl_send(cli, port, baud, _RUNTIME_REFS + [
            'print("VOICE=" + str(_v is not None))',
            'print("STATE=" + str(_v.state if _v else "N/A"))',
            'print("KWS=" + str(_v.kws_running if _v else "N/A"))',
        ], timeout=15, settle_ms=2000)
    return r


# ---------------------------------------------------------------------------
# natural mode
# ---------------------------------------------------------------------------

def run_natural(cli, port: str, baud: int, args) -> Dict[str, Any]:
    """Boot, hands-off, then read final state once."""
    summary: Dict[str, Any] = {"mode": "natural"}
    boot = boot_runtime(cli, port, baud, args.timeout, args.boot_wait, args.boot_retry_wait)
    summary["boot_voice_ready"] = boot.get("VOICE") == "True"
    summary["boot_state"] = boot.get("STATE", "")
    if not summary["boot_voice_ready"]:
        summary["ok"] = False
        summary["error"] = "voice controller not ready after boot"
        return summary

    time.sleep(args.handsoff_seconds)

    r = repl_send(cli, port, baud, [
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
        summary["raw_boot"] = boot.get("__raw__", "")
        summary["raw_result"] = r.get("__raw__", "")
    return summary


# ---------------------------------------------------------------------------
# manual mode
# ---------------------------------------------------------------------------

def run_manual(cli, port: str, baud: int, args) -> Dict[str, Any]:
    """Boot, manually set up capture, record, encode, POST, parse."""
    summary: Dict[str, Any] = {"mode": "manual"}
    boot = boot_runtime(cli, port, baud, args.timeout, args.boot_wait, args.boot_retry_wait)
    summary["boot_voice_ready"] = boot.get("VOICE") == "True"
    if not summary["boot_voice_ready"]:
        summary["ok"] = False
        summary["error"] = "voice controller not ready after boot"
        return summary

    # Setup capture pipeline
    repl_send(cli, port, baud, [
        '_a.stop_kws()',
        '_a.open_stream()',
        '_a.set_frame_callback(_v._on_audio_frame)',
        '_a.ensure_capture_pump()',
        '_v._audio_capture_begin("asr_smoke")',
        '_a.start_vad()',
    ], timeout=15, settle_ms=2000)

    time.sleep(args.record_seconds)

    # Take capture + encode
    r_cap = repl_send(cli, port, baud, [
        '_cap=_v.take_audio_capture("asr_smoke")',
        '_d=_cap.get("data",b"")',
        'print("BYTES=" + str(len(_d)))',
        'print("FMT=" + str(_cap.get("format","")))',
        'from board_remote_asr import _encode_base64',
        'gc.collect()',
        '_b64=_encode_base64(_d)',
        'print("B64=" + str(len(_b64)))',
    ], timeout=30, settle_ms=3000)
    summary["audio_bytes"] = int(r_cap.get("BYTES", "0") or 0)
    summary["audio_format"] = r_cap.get("FMT", "")
    summary["b64_len"] = int(r_cap.get("B64", "0") or 0)

    if summary["audio_bytes"] <= 0:
        summary["ok"] = False
        summary["error"] = "no audio captured"
        return summary

    # Build and send HTTP ASR
    token_header = ""
    if args.asr_token:
        token_header = ',"Authorization":"Bearer %s"' % args.asr_token
    r_asr = repl_send(cli, port, baud, [
        'import ujson,request',
        '_p=ujson.dumps({"provider":"asr_smoke","audio":{"encoding":"base64","format":"oggopus","sampleRate":16000,"base64":_b64}})',
        'del _b64',
        'gc.collect()',
        '_r=request.post("%s",data=_p,headers={"Content-Type":"application/json"%s})' % (args.asr_url, token_header),
        'print("HTTP=" + str(_r.status_code))',
        '_j=_r.json()',
        '_r.close()',
        'del _p',
        'gc.collect()',
        'print("OK=" + str(_j.get("ok",False)))',
        'print("TEXT=" + str(_j.get("text","")))',
        '_m=_j.get("meta",{})',
        'print("AFMT=" + str(_m.get("audio_format","")))',
        'print("MS=" + str(_m.get("elapsed_ms",0)))',
        'del _j,_m',
        'gc.collect()',
    ], timeout=args.timeout, settle_ms=15000)
    summary["http_status"] = int(r_asr.get("HTTP", "0") or 0)
    summary["asr_ok"] = r_asr.get("OK", "")
    summary["transcript"] = r_asr.get("TEXT", "")
    summary["asr_format"] = r_asr.get("AFMT", "")
    summary["asr_elapsed_ms"] = int(r_asr.get("MS", "0") or 0)
    summary["ok"] = r_asr.get("HTTP") == "200" and r_asr.get("OK") == "True"
    if args.include_raw:
        summary["raw_boot"] = boot.get("__raw__", "")
        summary["raw_cap"] = r_cap.get("__raw__", "")
        summary["raw_asr"] = r_asr.get("__raw__", "")
    return summary


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    args = build_parser().parse_args()
    cli = load_qpy_fs_cli()
    if args.mode == "natural":
        summary = run_natural(cli, args.port, args.baud, args)
    else:
        summary = run_manual(cli, args.port, args.baud, args)
    summary["port"] = args.port
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for k, v in summary.items():
            if k.startswith("raw"):
                continue
            print(f"{k}: {v}")
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
