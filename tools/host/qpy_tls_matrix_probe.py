#!/usr/bin/env python3
"""
Run a staged TLS/WebSocket probe on a QuecPython device over REPL.

Stages:
1. DNS + raw TCP connect
2. TLS wrap without SNI
3. TLS wrap with SNI
4. HTTPS GET over TLS
5. WebSocket Upgrade over TLS
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
def _probe(host, port, path):
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
        import ussl
        log("import.ussl", "ok", "ussl")
    except Exception as e:
        log("import.ussl", "error", e)
        print("TLS_MATRIX_BEGIN")
        print(ujson.dumps(out))
        print("TLS_MATRIX_END")
        return

    try:
        addr = socket.getaddrinfo(host, port)[0][-1]
        log("dns", "ok", addr)
    except Exception as e:
        log("dns", "error", e)
        print("TLS_MATRIX_BEGIN")
        print(ujson.dumps(out))
        print("TLS_MATRIX_END")
        return

    def try_tls(stage_name, use_sni, send_http, send_ws):
        sock = None
        tls_sock = None
        try:
            sock = socket.socket()
            sock.settimeout(12)
            sock.connect(addr)
            log(stage_name + ".tcp", "ok", "connected")
            if use_sni:
                tls_sock = ussl.wrap_socket(sock, server_hostname=host)
                log(stage_name + ".wrap", "ok", "sni")
            else:
                tls_sock = ussl.wrap_socket(sock)
                log(stage_name + ".wrap", "ok", "no-sni")

            if hasattr(tls_sock, "settimeout"):
                tls_sock.settimeout(12)
                log(stage_name + ".settimeout", "ok", "12")
            else:
                log(stage_name + ".settimeout", "skip", "unsupported")

            if send_http:
                sep = chr(13) + chr(10)
                req = (
                    "GET " + path + " HTTP/1.1" + sep +
                    "Host: " + host + sep +
                    "Connection: close" + sep + sep
                )
                tls_sock.write(req.encode())
                log(stage_name + ".http.write", "ok", "sent")
                buf = tls_sock.read(256)
                if buf:
                    try:
                        preview = buf.decode()
                    except Exception:
                        preview = str(buf)
                    log(stage_name + ".http.read", "ok", preview[:200])
                else:
                    log(stage_name + ".http.read", "eof", "")

            if send_ws:
                sep = chr(13) + chr(10)
                req = (
                    "GET " + path + " HTTP/1.1" + sep +
                    "Host: " + host + sep +
                    "Connection: Upgrade" + sep +
                    "Upgrade: websocket" + sep +
                    "Sec-WebSocket-Key: dGVzdF9xcHljbGF3X3Byb2Jl" + sep +
                    "Sec-WebSocket-Version: 13" + sep + sep
                )
                tls_sock.write(req.encode())
                log(stage_name + ".ws.write", "ok", "sent")
                buf = tls_sock.read(256)
                if buf:
                    try:
                        preview = buf.decode()
                    except Exception:
                        preview = str(buf)
                    log(stage_name + ".ws.read", "ok", preview[:200])
                else:
                    log(stage_name + ".ws.read", "eof", "")

        except Exception as e:
            log(stage_name, "error", e)
        finally:
            try:
                if tls_sock is not None:
                    tls_sock.close()
            except Exception:
                pass
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                pass

    try_tls("tls_no_sni", False, False, False)
    try_tls("tls_with_sni", True, False, False)
    try_tls("https_with_sni", True, True, False)
    try_tls("wss_upgrade_with_sni", True, False, True)

    print("TLS_MATRIX_BEGIN")
    print(ujson.dumps(out))
    print("TLS_MATRIX_END")

import ujson
_probe(%(host)r, %(port)d, %(path)r)
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
    parser = argparse.ArgumentParser(description="Probe TLS/WSS stages on a QuecPython device.")
    parser.add_argument("--port", default="COM14")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--host", default="282r41l383.oicp.vip")
    parser.add_argument("--port-num", type=int, default=443)
    parser.add_argument("--path", default="/")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cli = load_qpy_fs_cli()
    code = PROBE_TEMPLATE % {
        "host": args.host,
        "port": args.port_num,
        "path": args.path,
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
    parsed = extract_json_between_markers(raw, "TLS_MATRIX_BEGIN", "TLS_MATRIX_END")
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
