#!/usr/bin/env python3
"""
Run a staged plain TCP/HTTP/WebSocket probe on a QuecPython device over REPL.

Stages:
1. DNS + raw TCP connect
2. Optional plain HTTP GET
3. Plain WebSocket Upgrade
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
def _probe(host, port, path, run_http):
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

    try:
        import usocket as socket
        log("import.usocket", "ok", "usocket")
    except Exception as e:
        import socket
        log("import.usocket", "fallback", e)

    try:
        addr = socket.getaddrinfo(host, port)[0][-1]
        log("dns", "ok", addr)
    except Exception as e:
        log("dns", "error", e)
        print("PLAIN_WS_PROBE_BEGIN")
        print(ujson.dumps(out))
        print("PLAIN_WS_PROBE_END")
        return

    def run_stage(stage_name, request_text):
        sock = None
        try:
            sock = socket.socket()
            sock.settimeout(12)
            sock.connect(addr)
            log(stage_name + ".tcp", "ok", "connected")
            sock.write(request_text.encode())
            log(stage_name + ".write", "ok", "sent")
            buf = sock.recv(256)
            if buf:
                try:
                    preview = buf.decode()
                except Exception:
                    preview = str(buf)
                log(stage_name + ".read", "ok", preview[:200])
            else:
                log(stage_name + ".read", "eof", "")
        except Exception as e:
            log(stage_name, "error", e)
        finally:
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                pass

    sep = chr(13) + chr(10)

    if run_http:
        http_req = (
            "GET " + path + " HTTP/1.1" + sep +
            "Host: " + host + sep +
            "Connection: close" + sep + sep
        )
        run_stage("http_get", http_req)

    ws_req = (
        "GET " + path + " HTTP/1.1" + sep +
        "Host: " + host + sep +
        "Connection: Upgrade" + sep +
        "Upgrade: websocket" + sep +
        "Sec-WebSocket-Key: dGVzdF9xcHljbGF3X3BsYWlu" + sep +
        "Sec-WebSocket-Version: 13" + sep + sep
    )
    run_stage("ws_upgrade", ws_req)

    print("PLAIN_WS_PROBE_BEGIN")
    print(ujson.dumps(out))
    print("PLAIN_WS_PROBE_END")

import ujson
_probe(%(host)r, %(port)d, %(path)r, %(run_http)s)
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
        description="Probe plain TCP/HTTP/WebSocket stages on a QuecPython device."
    )
    parser.add_argument("--port", default="COM14")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port-num", type=int, required=True)
    parser.add_argument("--path", default="/")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cli = load_qpy_fs_cli()
    code = PROBE_TEMPLATE % {
        "host": args.host,
        "port": args.port_num,
        "path": args.path,
        "run_http": "True" if args.http else "False",
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
        raw, "PLAIN_WS_PROBE_BEGIN", "PLAIN_WS_PROBE_END"
    )
    payload = {
        "host": args.host,
        "port": args.port_num,
        "path": args.path,
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
