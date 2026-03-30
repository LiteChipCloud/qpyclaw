#!/usr/bin/env python3
"""
Operate OpenClaw nodes by SSH-ing into the gateway host and executing
server-local raw websocket RPC against ws://127.0.0.1:18789.

Why this exists:
1. The current official server-local CLI path can regress independently.
2. This desktop can also hit public-gateway timeout/path issues.
3. The gateway host itself can already complete:
   websocket upgrade -> connect.challenge -> connect -> node.list/node.invoke

This tool keeps qpyclaw device operations moving with a minimal host-side
dependency surface.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import sys
import uuid
from pathlib import Path


def _add_vendor_path() -> None:
    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    vendor = repo_root / ".vendor"
    if vendor.is_dir():
        sys.path.insert(0, str(vendor))


_add_vendor_path()

PARAMIKO_IMPORT_ERROR = ""

try:
    import paramiko  # type: ignore
except Exception as exc:  # pragma: no cover - host environment guard
    paramiko = None  # type: ignore
    PARAMIKO_IMPORT_ERROR = str(exc)


REMOTE_RPC_SCRIPT = r"""
import base64
import hashlib
import json
import os
import socket
import sys
import uuid

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def read_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise RuntimeError("socket closed while reading")
        data.extend(chunk)
    return bytes(data)


def recv_frame(sock):
    first = read_exact(sock, 2)
    byte1, byte2 = first[0], first[1]
    opcode = byte1 & 0x0F
    masked = bool(byte2 & 0x80)
    length = byte2 & 0x7F
    if length == 126:
        length = int.from_bytes(read_exact(sock, 2), "big")
    elif length == 127:
        length = int.from_bytes(read_exact(sock, 8), "big")
    mask_key = read_exact(sock, 4) if masked else b""
    payload = read_exact(sock, length)
    if masked:
        payload = bytes(payload[i] ^ mask_key[i % 4] for i in range(length))
    return opcode, payload


def send_json(sock, obj):
    payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = bytearray([0x81])
    length = len(payload)
    mask = os.urandom(4)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header.extend(length.to_bytes(2, "big"))
    else:
        header.append(0x80 | 127)
        header.extend(length.to_bytes(8, "big"))
    header.extend(mask)
    masked = bytes(payload[i] ^ mask[i % 4] for i in range(length))
    sock.sendall(bytes(header) + masked)


def recv_json(sock):
    while True:
        opcode, payload = recv_frame(sock)
        if opcode != 1:
            continue
        return json.loads(payload.decode("utf-8"))


def connect_operator(sock, payload):
    challenge = recv_json(sock)
    connect_req = {
        "type": "req",
        "id": "connect-1",
        "method": "connect",
        "params": {
            "minProtocol": 3,
            "maxProtocol": 3,
            "client": {
                "id": payload.get("client_id") or "cli",
                "displayName": payload.get("client_display_name") or "qpyclaw-server-ops",
                "version": payload.get("client_version") or "0.1.0",
                "platform": payload.get("client_platform") or "linux",
                "mode": payload.get("client_mode") or "cli",
            },
            "caps": [],
            "auth": {"token": payload["token"]},
            "role": "operator",
            "scopes": ["operator.admin"],
        },
    }
    send_json(sock, connect_req)
    hello = recv_json(sock)
    return challenge, hello


def run_node_list(sock, request_timeout_ms, connected_only):
    send_json(
        sock,
        {
            "type": "req",
            "id": "node-list-1",
            "method": "node.list",
            "params": {},
        },
    )
    response = recv_json(sock)
    if not response.get("ok"):
        raise RuntimeError("node.list failed: %s" % json.dumps(response.get("error")))
    payload = response.get("payload") or {}
    nodes = payload.get("nodes") or []
    if connected_only:
        nodes = [node for node in nodes if isinstance(node, dict) and node.get("connected")]
    return response, nodes


def resolve_node(nodes, selector):
    if not selector:
        raise RuntimeError("node selector is required")
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("nodeId") == selector:
            return node
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("displayName") == selector:
            return node
    raise RuntimeError("node not found: %s" % selector)


def run_invoke(sock, node_id, command, params, timeout_ms):
    request_id = "invoke-" + uuid.uuid4().hex
    send_json(
        sock,
        {
            "type": "req",
            "id": request_id,
            "method": "node.invoke",
            "params": {
                "nodeId": node_id,
                "command": command,
                "params": params,
                "timeoutMs": int(timeout_ms),
                "idempotencyKey": "qpyclaw-%s-%s"
                % (str(command).replace(".", "-"), uuid.uuid4().hex),
            },
        },
    )
    while True:
        response = recv_json(sock)
        if response.get("type") == "res" and response.get("id") == request_id:
            return response


def main():
    payload = json.loads(sys.argv[1])
    cfg_path = payload["config_path"]
    if payload.get("gateway_token"):
        token = payload["gateway_token"]
    else:
        cfg = json.load(open(cfg_path, "r", encoding="utf-8"))
        token = (((cfg.get("gateway") or {}).get("auth") or {}).get("token")) or ""
    if not token:
        raise RuntimeError("gateway token is empty")

    ws_url = payload.get("gateway_url") or "ws://127.0.0.1:18789"
    if not ws_url.startswith("ws://"):
        raise RuntimeError("only ws:// is supported by this raw server-local operator tool")
    host_port = ws_url[len("ws://") :]
    path = "/"
    if "/" in host_port:
        host_port, path = host_port.split("/", 1)
        path = "/" + path
    if ":" in host_port:
        host, port_text = host_port.rsplit(":", 1)
        port = int(port_text)
    else:
        host = host_port
        port = 80

    sock = socket.create_connection((host, port), 8)
    sock.settimeout(max(5, int(payload.get("socket_timeout_sec") or 20)))
    try:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            "GET %s HTTP/1.1\r\n"
            "Host: %s:%d\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "User-Agent: qpyclaw-server-ops\r\n"
            "\r\n"
        ) % (path, host, port, key)
        sock.sendall(request.encode("utf-8"))

        header = bytearray()
        while b"\r\n\r\n" not in header:
            chunk = sock.recv(4096)
            if not chunk:
                raise RuntimeError("socket closed before websocket upgrade completed")
            header.extend(chunk)

        challenge, hello = connect_operator(
            sock,
            {
                "token": token,
                "client_id": payload.get("client_id"),
                "client_display_name": payload.get("client_display_name"),
                "client_version": payload.get("client_version"),
                "client_platform": payload.get("client_platform"),
                "client_mode": payload.get("client_mode"),
            },
        )

        request_timeout_ms = int(payload.get("timeout_ms") or 15000)
        node_list_response, nodes = run_node_list(
            sock,
            request_timeout_ms,
            bool(payload.get("connected_only")),
        )

        mode = payload["mode"]
        if mode == "node-list":
            print(
                json.dumps(
                    {
                        "ok": True,
                        "mode": mode,
                        "hello": hello,
                        "challenge": challenge,
                        "nodes": nodes,
                    },
                    ensure_ascii=True,
                )
            )
            return

        selected = resolve_node(nodes, payload.get("node"))
        response = run_invoke(
            sock,
            str(selected.get("nodeId")),
            str(payload["command"]),
            payload.get("params") or {},
            request_timeout_ms,
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": mode,
                    "hello": hello,
                    "challenge": challenge,
                    "selectedNode": selected,
                    "invoke": response,
                    "nodeList": node_list_response,
                },
                ensure_ascii=True,
            )
        )
    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Operate OpenClaw nodes through SSH or direct public websocket RPC."
    )
    parser.add_argument(
        "--transport",
        choices=["ssh", "direct"],
        default="ssh",
        help="Use SSH server-local RPC or direct public websocket RPC.",
    )
    parser.add_argument("--ssh-host", required=True, help="Gateway server SSH host.")
    parser.add_argument("--ssh-port", type=int, default=22, help="Gateway server SSH port.")
    parser.add_argument("--ssh-user", default="root", help="Gateway server SSH user.")
    parser.add_argument(
        "--ssh-password",
        default="",
        help="Gateway server SSH password. Prefer --ssh-password-env.",
    )
    parser.add_argument(
        "--ssh-password-env",
        default="OPENCLAW_SSH_PASSWORD",
        help="Environment variable that holds the SSH password.",
    )
    parser.add_argument(
        "--gateway-config",
        default="/home/openclaw/.openclaw/openclaw.json",
        help="Remote OpenClaw config path used to read the gateway token.",
    )
    parser.add_argument(
        "--gateway-url",
        default="ws://127.0.0.1:18789",
        help="Remote gateway websocket URL as seen from the server.",
    )
    parser.add_argument(
        "--gateway-token",
        default="",
        help="Optional explicit gateway token. Usually leave empty and load from remote config.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=15000,
        help="node.invoke timeout in milliseconds.",
    )
    parser.add_argument(
        "--socket-timeout-sec",
        type=int,
        default=20,
        help="Remote raw websocket socket timeout in seconds.",
    )
    parser.add_argument("--client-id", default="cli")
    parser.add_argument("--client-display-name", default="qpyclaw-server-ops")
    parser.add_argument("--client-version", default="0.1.0")
    parser.add_argument("--client-platform", default="linux")
    parser.add_argument("--client-mode", default="cli")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    node_list = subparsers.add_parser("node-list", help="List nodes via server-local raw RPC.")
    node_list.add_argument(
        "--connected-only",
        action="store_true",
        help="Only keep currently connected nodes.",
    )

    node_invoke = subparsers.add_parser("node-invoke", help="Invoke one node command.")
    node_invoke.add_argument(
        "--node",
        required=True,
        help="Exact nodeId or exact displayName.",
    )
    node_invoke.add_argument("--command", required=True, help="Node command to invoke.")
    node_invoke.add_argument(
        "--params-json",
        default="{}",
        help="JSON object passed as node.invoke params.",
    )
    node_invoke.add_argument(
        "--param",
        action="append",
        default=[],
        help="Additional invoke param in key=value form. Easier than JSON in PowerShell.",
    )
    node_invoke.add_argument(
        "--connected-only",
        action="store_true",
        help="Only search among currently connected nodes.",
    )

    return parser


def resolve_ssh_password(args: argparse.Namespace) -> str:
    if args.ssh_password:
        return str(args.ssh_password)
    if args.ssh_password_env:
        value = os.environ.get(str(args.ssh_password_env), "").strip()
        if value:
            return value
    raise SystemExit("missing SSH password; use --ssh-password or --ssh-password-env")


def _parse_scalar_value(text: str):
    raw = str(text)
    try:
        return json.loads(raw)
    except Exception:
        return raw


def parse_invoke_params(args: argparse.Namespace) -> dict:
    try:
        data = json.loads(args.params_json or "{}")
    except Exception as exc:
        raise SystemExit("invalid --params-json: %s" % exc)
    if not isinstance(data, dict):
        raise SystemExit("--params-json must decode to a JSON object")
    for item in list(getattr(args, "param", []) or []):
        text = str(item)
        if "=" not in text:
            raise SystemExit("invalid --param %r; expected key=value" % text)
        key, value = text.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit("invalid --param %r; key cannot be empty" % text)
        data[key] = _parse_scalar_value(value.strip())
    return data


def build_remote_payload(args: argparse.Namespace) -> dict:
    payload = {
        "mode": args.mode,
        "config_path": args.gateway_config,
        "gateway_url": args.gateway_url,
        "gateway_token": args.gateway_token,
        "timeout_ms": int(args.timeout_ms),
        "socket_timeout_sec": int(args.socket_timeout_sec),
        "client_id": args.client_id,
        "client_display_name": args.client_display_name,
        "client_version": args.client_version,
        "client_platform": args.client_platform,
        "client_mode": args.client_mode,
        "connected_only": bool(getattr(args, "connected_only", False)),
    }
    if args.mode == "node-invoke":
        payload["node"] = args.node
        payload["command"] = args.command
        payload["params"] = parse_invoke_params(args)
    return payload


def resolve_direct_gateway_url(args: argparse.Namespace) -> str:
    url = str(args.gateway_url or "").strip()
    if (not url) or url == "ws://127.0.0.1:18789":
        host = str(args.ssh_host or "").strip()
        if not host:
            raise SystemExit("direct mode requires --gateway-url or --ssh-host")
        return "ws://%s:18789" % host
    return url


class SocketReader(object):

    def __init__(self, sock: socket.socket, initial: bytes = b""):
        self.sock = sock
        self.buffer = bytearray(initial or b"")

    def read_exact(self, size: int) -> bytes:
        while len(self.buffer) < size:
            chunk = self.sock.recv(size - len(self.buffer))
            if not chunk:
                raise RuntimeError("socket closed while reading")
            self.buffer.extend(chunk)
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        return data


def read_exact(stream, size: int) -> bytes:
    if hasattr(stream, "read_exact"):
        return stream.read_exact(size)
    sock = getattr(stream, "sock", stream)
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise RuntimeError("socket closed while reading")
        data.extend(chunk)
    return bytes(data)


def recv_frame(stream):
    first = read_exact(stream, 2)
    byte1, byte2 = first[0], first[1]
    opcode = byte1 & 0x0F
    masked = bool(byte2 & 0x80)
    length = byte2 & 0x7F
    if length == 126:
        length = int.from_bytes(read_exact(stream, 2), "big")
    elif length == 127:
        length = int.from_bytes(read_exact(stream, 8), "big")
    mask_key = read_exact(stream, 4) if masked else b""
    payload = read_exact(stream, length)
    if masked:
        payload = bytes(payload[i] ^ mask_key[i % 4] for i in range(length))
    return opcode, payload


def send_json(endpoint, obj: dict) -> None:
    sock = getattr(endpoint, "sock", endpoint)
    payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = bytearray([0x81])
    length = len(payload)
    mask = os.urandom(4)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header.extend(length.to_bytes(2, "big"))
    else:
        header.append(0x80 | 127)
        header.extend(length.to_bytes(8, "big"))
    header.extend(mask)
    masked = bytes(payload[i] ^ mask[i % 4] for i in range(length))
    sock.sendall(bytes(header) + masked)


def recv_json(stream) -> dict:
    while True:
        opcode, payload = recv_frame(stream)
        if opcode != 1:
            continue
        return json.loads(payload.decode("utf-8"))


def connect_operator_direct(
    stream,
    gateway_token: str,
    client_id: str,
    client_display_name: str,
    client_version: str,
    client_platform: str,
    client_mode: str,
):
    challenge = recv_json(stream)
    connect_req = {
        "type": "req",
        "id": "connect-1",
        "method": "connect",
        "params": {
            "minProtocol": 3,
            "maxProtocol": 3,
            "client": {
                "id": client_id,
                "displayName": client_display_name,
                "version": client_version,
                "platform": client_platform,
                "mode": client_mode,
            },
            "caps": [],
            "auth": {"token": gateway_token},
            "role": "operator",
            "scopes": ["operator.admin"],
        },
    }
    send_json(stream, connect_req)
    hello = recv_json(stream)
    return challenge, hello


def run_node_list_direct(stream, connected_only: bool):
    send_json(
        stream,
        {
            "type": "req",
            "id": "node-list-1",
            "method": "node.list",
            "params": {},
        },
    )
    response = recv_json(stream)
    if not response.get("ok"):
        raise RuntimeError("node.list failed: %s" % json.dumps(response.get("error")))
    payload = response.get("payload") or {}
    nodes = payload.get("nodes") or []
    if connected_only:
        nodes = [node for node in nodes if isinstance(node, dict) and node.get("connected")]
    return response, nodes


def resolve_node_direct(nodes: list, selector: str) -> dict:
    if not selector:
        raise RuntimeError("node selector is required")
    for node in nodes:
        if isinstance(node, dict) and node.get("nodeId") == selector:
            return node
    for node in nodes:
        if isinstance(node, dict) and node.get("displayName") == selector:
            return node
    raise RuntimeError("node not found: %s" % selector)


def run_invoke_direct(
    stream, node_id: str, command: str, params: dict, timeout_ms: int
) -> dict:
    request_id = "invoke-" + uuid.uuid4().hex
    send_json(
        stream,
        {
            "type": "req",
            "id": request_id,
            "method": "node.invoke",
            "params": {
                "nodeId": node_id,
                "command": command,
                "params": params,
                "timeoutMs": int(timeout_ms),
                "idempotencyKey": "qpyclaw-%s-%s"
                % (str(command).replace(".", "-"), uuid.uuid4().hex),
            },
        },
    )
    while True:
        response = recv_json(stream)
        if response.get("type") == "res" and response.get("id") == request_id:
            return response


def run_direct_rpc(args: argparse.Namespace) -> dict:
    gateway_token = str(args.gateway_token or "").strip()
    if not gateway_token:
        raise SystemExit("direct mode requires --gateway-token")

    gateway_url = resolve_direct_gateway_url(args)
    if not gateway_url.startswith("ws://"):
        raise SystemExit("direct mode only supports ws:// gateway urls")

    host_port = gateway_url[len("ws://") :]
    path = "/"
    if "/" in host_port:
        host_port, path = host_port.split("/", 1)
        path = "/" + path
    if ":" in host_port:
        host, port_text = host_port.rsplit(":", 1)
        port = int(port_text)
    else:
        host = host_port
        port = 80

    sock = socket.create_connection((host, port), 8)
    sock.settimeout(max(5, int(args.socket_timeout_sec or 20)))
    try:
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            "GET %s HTTP/1.1\r\n"
            "Host: %s:%d\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "User-Agent: qpyclaw-server-ops\r\n"
            "\r\n"
        ) % (path, host, port, key)
        sock.sendall(request.encode("utf-8"))

        header = bytearray()
        while b"\r\n\r\n" not in header:
            chunk = sock.recv(4096)
            if not chunk:
                raise RuntimeError("socket closed before websocket upgrade completed")
            header.extend(chunk)
        split_at = header.find(b"\r\n\r\n")
        leftover = b""
        if split_at >= 0:
            leftover = bytes(header[split_at + 4 :])
        stream = SocketReader(sock, leftover)

        challenge, hello = connect_operator_direct(
            stream,
            gateway_token,
            args.client_id,
            args.client_display_name,
            args.client_version,
            args.client_platform,
            args.client_mode,
        )

        node_list_response, nodes = run_node_list_direct(
            stream, bool(getattr(args, "connected_only", False))
        )

        payload = {
            "ok": True,
            "mode": args.mode,
            "hello": hello,
            "challenge": challenge,
        }
        if args.mode == "node-list":
            payload["nodes"] = nodes
            payload["list"] = node_list_response
            return payload

        selected = resolve_node_direct(nodes, args.node)
        invoke = run_invoke_direct(
            stream,
            str(selected.get("nodeId") or ""),
            args.command,
            parse_invoke_params(args),
            int(args.timeout_ms),
        )
        payload["selectedNode"] = selected
        payload["list"] = node_list_response
        payload["invoke"] = invoke
        return payload
    finally:
        try:
            sock.close()
        except Exception:
            pass


def run_remote_rpc(args: argparse.Namespace) -> dict:
    if (paramiko is None) or (not hasattr(paramiko, "SSHClient")):
        detail = PARAMIKO_IMPORT_ERROR or "paramiko has no SSHClient"
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error": "paramiko unavailable",
                    "detail": detail,
                    "hint": "use --transport direct with --gateway-token for public websocket RPC",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    password = resolve_ssh_password(args)
    remote_payload = build_remote_payload(args)
    remote_command = "python3 - %s <<'PY'\n%s\nPY" % (
        json.dumps(json.dumps(remote_payload, ensure_ascii=False)),
        REMOTE_RPC_SCRIPT,
    )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=args.ssh_host,
        port=int(args.ssh_port),
        username=args.ssh_user,
        password=password,
        timeout=15,
    )
    try:
        stdin, stdout, stderr = client.exec_command(remote_command, timeout=90)
        raw_stdout = stdout.read().decode("utf-8", errors="replace").strip()
        raw_stderr = stderr.read().decode("utf-8", errors="replace").strip()
        exit_status = stdout.channel.recv_exit_status()
    finally:
        client.close()

    if exit_status != 0:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "exit_status": exit_status,
                    "stderr": raw_stderr,
                    "stdout": raw_stdout,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    if not raw_stdout:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error": "remote stdout is empty",
                    "stderr": raw_stderr,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    try:
        payload = json.loads(raw_stdout)
    except Exception as exc:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error": "failed to parse remote JSON",
                    "detail": str(exc),
                    "stdout": raw_stdout,
                    "stderr": raw_stderr,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    if raw_stderr:
        payload["remote_stderr"] = raw_stderr
    return payload


def summarize_node(node: dict) -> dict:
    return {
        "nodeId": node.get("nodeId"),
        "displayName": node.get("displayName"),
        "platform": node.get("platform"),
        "deviceFamily": node.get("deviceFamily"),
        "connected": node.get("connected"),
        "paired": node.get("paired"),
        "connectedAtMs": node.get("connectedAtMs"),
        "remoteIp": node.get("remoteIp"),
        "caps": node.get("caps") or [],
        "commandCount": len(node.get("commands") or []),
    }


def print_human(payload: dict) -> None:
    mode = payload.get("mode")
    print("mode: %s" % mode)
    hello = payload.get("hello") or {}
    if isinstance(hello, dict):
        server = hello.get("payload") if hello.get("type") == "res" else hello
        print("hello_ok: true")
        print("protocol: %s" % ((server.get("payload") or {}).get("protocol") if isinstance(server.get("payload"), dict) else server.get("protocol")))

    if mode == "node-list":
        nodes = payload.get("nodes") or []
        print("nodes: %d" % len(nodes))
        for node in nodes:
            item = summarize_node(node)
            print(
                "- %s | %s | connected=%s paired=%s commands=%d"
                % (
                    item.get("nodeId"),
                    item.get("displayName"),
                    item.get("connected"),
                    item.get("paired"),
                    item.get("commandCount"),
                )
            )
        return

    selected = payload.get("selectedNode") or {}
    item = summarize_node(selected) if isinstance(selected, dict) else {}
    print("selected_node: %s" % item.get("nodeId"))
    print("selected_name: %s" % item.get("displayName"))
    invoke = payload.get("invoke") or {}
    print("invoke_ok: %s" % invoke.get("ok"))
    inner = invoke.get("payload") or {}
    if isinstance(inner, dict):
        print("command: %s" % inner.get("command"))
        tool_payload = inner.get("payload") or {}
        if isinstance(tool_payload, dict):
            print("tool_status: %s" % tool_payload.get("status"))
            print("result_code: %s" % tool_payload.get("result_code"))
            print("duration_ms: %s" % tool_payload.get("duration_ms"))
            data = tool_payload.get("data")
            if data is not None:
                print("data_json:")
                print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    args = build_parser().parse_args()
    if args.transport == "direct":
        payload = run_direct_rpc(args)
    else:
        payload = run_remote_rpc(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
