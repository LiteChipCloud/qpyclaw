#!/usr/bin/env python3
"""
Run high-level HTTPS / WebSocket probes on a QuecPython device over REPL.

This complements the low-level TLS matrix probe by testing official
QuecPython-facing APIs such as `request` and `uwebsocket`.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def load_qpy_fs_cli():
    skill_scripts = pathlib.Path(
        r"C:\Users\kingd\.codex\skills\quecpython-dev\scripts"
    )
    sys.path.insert(0, str(skill_scripts))
    import qpy_device_fs_cli as cli  # type: ignore

    return cli


PROBE_TEMPLATE = r"""
def _probe(https_url, ws_url):
    out = []

    def log(stage, status, detail):
        try:
            out.append({
                "stage": stage,
                "status": status,
                "detail": str(detail),
            })
        except Exception as e:
            out.append({
                "stage": stage,
                "status": "error",
                "detail": "log-failed:" + str(e),
            })

    if https_url:
        try:
            import request
            log("import.request", "ok", "request")
            try:
                resp = request.get(https_url, decode=False)
                log("https.status", "ok", getattr(resp, "status_code", None))
                try:
                    log("https.headers", "ok", getattr(resp, "headers", None))
                except Exception as e:
                    log("https.headers", "error", e)
            except Exception as e:
                log("https.request", "error", e)
        except Exception as e:
            log("import.request", "error", e)

    if ws_url:
        try:
            import uwebsocket
            log("import.uwebsocket", "ok", "uwebsocket")
            try:
                ws = uwebsocket.Client.connect(ws_url, debug=False)
                log("ws.connect", "ok", "connected")
                try:
                    ws.close()
                    log("ws.close", "ok", "closed")
                except Exception as e:
                    log("ws.close", "error", e)
            except Exception as e:
                log("ws.connect", "error", e)
        except Exception as e:
            log("import.uwebsocket", "error", e)

    print("QPY_HIGHLEVEL_BEGIN")
    print(ujson.dumps(out))
    print("QPY_HIGHLEVEL_END")

import ujson
_probe(%(https_url)r, %(ws_url)r)
"""


def extract_json_between_markers(raw: str, begin: str, end: str):
    text = raw.replace("<CR><LF>", "\n").replace("<CR>", "\n").replace("<LF>", "\n")
    start = text.rfind(begin)
    stop = text.rfind(end)
    if start < 0 or stop < 0 or stop <= start:
        return None
    payload = text[start + len(begin):stop].strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe high-level QuecPython HTTPS / WebSocket APIs over REPL."
    )
    parser.add_argument("--port", default="COM14")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--https-url", default="")
    parser.add_argument("--ws-url", default="")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.https_url and not args.ws_url:
        parser.error("Provide --https-url and/or --ws-url")

    cli = load_qpy_fs_cli()
    code = PROBE_TEMPLATE % {
        "https_url": args.https_url,
        "ws_url": args.ws_url,
    }
    lines = [
        "_code=%r" % code,
        "exec(_code)",
    ]
    raw = cli.repl_send_lines(
        args.port,
        args.baud,
        lines,
        timeout=max(20, int(args.timeout)),
        line_delay_ms=60,
        settle_ms=12000,
        busy_retries=2,
        busy_wait_ms=300,
    )
    parsed = extract_json_between_markers(
        raw, "QPY_HIGHLEVEL_BEGIN", "QPY_HIGHLEVEL_END"
    )
    payload = {
        "https_url": args.https_url,
        "ws_url": args.ws_url,
        "parsed": parsed,
        "raw": raw,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if parsed is not None:
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        else:
            print(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
