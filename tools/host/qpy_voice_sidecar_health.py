#!/usr/bin/env python3
"""
Health-check the qpyclaw DashScope voice sidecar on a remote server.

Checks
------
1. **HTTP reachability** — ``GET /healthz`` (or ``/docs``) returns 200.
2. **Service status** — ``systemctl is-active qpyclaw-voice-sidecar``.
3. **Recent logs** — last N lines of ``journalctl`` for the service.
4. **DashScope ASR probe** — optionally run a short Recognition call with a
   known audio file already on the server to verify API-key + model config.

All checks are performed over SSH using ``paramiko``.

Examples
--------
::

    # Quick reachability + service status
    python qpy_voice_sidecar_health.py --json

    # Full check including DashScope ASR probe
    python qpy_voice_sidecar_health.py --asr-probe --json

    # Deploy updated app.py and restart
    python qpy_voice_sidecar_health.py --deploy --restart --json
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from typing import Any, Dict, Optional


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Health-check the qpyclaw voice sidecar.")
    p.add_argument("--host", default="124.70.221.88", help="Sidecar server host.")
    p.add_argument("--ssh-user", default="root")
    p.add_argument("--ssh-pass", default="!?Lcc666888")
    p.add_argument("--ssh-port", type=int, default=22)
    p.add_argument("--sidecar-port", type=int, default=8788)
    p.add_argument("--service-name", default="qpyclaw-voice-sidecar",
                   help="systemd service name.")
    p.add_argument("--remote-app-dir", default="/opt/qpyclaw/voice_sidecar",
                   help="Remote directory containing app.py.")
    p.add_argument("--log-lines", type=int, default=30,
                   help="Number of recent journal lines to fetch.")
    p.add_argument("--asr-probe", action="store_true",
                   help="Run a DashScope ASR probe with a known audio file on the server.")
    p.add_argument("--asr-probe-file", default="/tmp/qpyclaw_last_asr.ogg",
                   help="Server-side audio file for ASR probe.")
    p.add_argument("--deploy", action="store_true",
                   help="Upload local app.py to the server before checking.")
    p.add_argument("--restart", action="store_true",
                   help="Restart the sidecar systemd service.")
    p.add_argument("--json", action="store_true")
    return p


def _ssh_connect(host: str, user: str, password: str, port: int = 22):
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        host, port=port, username=user, password=password,
        timeout=30, banner_timeout=60, auth_timeout=30,
        disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},
    )
    return ssh


def _ssh_run(ssh, cmd: str, timeout: int = 30) -> str:
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    return out + ("\n" + err if err else "")


def check_http(ssh, sidecar_port: int) -> Dict[str, Any]:
    out = _ssh_run(ssh, "curl -sf -o /dev/null -w '%%{http_code}' http://127.0.0.1:%d/docs 2>/dev/null || echo FAIL" % sidecar_port)
    code = out.strip()
    return {"ok": code == "200", "http_code": code}


def check_service(ssh, service_name: str) -> Dict[str, Any]:
    active = _ssh_run(ssh, "systemctl is-active %s 2>/dev/null" % service_name)
    enabled = _ssh_run(ssh, "systemctl is-enabled %s 2>/dev/null" % service_name)
    return {"active": active, "enabled": enabled, "ok": active == "active"}


def check_logs(ssh, service_name: str, lines: int) -> str:
    return _ssh_run(ssh, "journalctl -u %s --no-pager -n %d 2>/dev/null" % (service_name, lines))


def deploy_app(ssh, remote_dir: str) -> Dict[str, Any]:
    local_app = str(
        pathlib.Path(__file__).resolve().parent.parent / "runtime_local" / "voice_sidecar" / "app.py"
    )
    if not os.path.isfile(local_app):
        return {"ok": False, "error": "local app.py not found: %s" % local_app}
    local_size = os.path.getsize(local_app)
    remote_path = remote_dir.rstrip("/") + "/app.py"
    # backup
    _ssh_run(ssh, "cp %s %s.bak 2>/dev/null" % (remote_path, remote_path))
    sftp = ssh.open_sftp()
    sftp.put(local_app, remote_path)
    remote_size = sftp.stat(remote_path).st_size
    sftp.close()
    return {"ok": local_size == remote_size, "local_size": local_size, "remote_size": remote_size, "remote_path": remote_path}


def restart_service(ssh, service_name: str) -> Dict[str, Any]:
    _ssh_run(ssh, "systemctl restart %s" % service_name, timeout=30)
    time.sleep(3)
    active = _ssh_run(ssh, "systemctl is-active %s 2>/dev/null" % service_name)
    return {"ok": active == "active", "active": active}


def asr_probe(ssh, remote_dir: str, audio_file: str) -> Dict[str, Any]:
    """Run a small Python script on the server to verify DashScope ASR works."""
    probe_script = r"""
import os, sys, time
sys.path.insert(0, '%s')
env_file = '/etc/qpyclaw-voice-sidecar.env'
if os.path.isfile(env_file):
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, _, v = line.strip().partition('=')
                os.environ.setdefault(k, v)
key = os.environ.get('DASHSCOPE_API_KEY', '')
if not key:
    print('ERROR: DASHSCOPE_API_KEY not set')
    sys.exit(1)
import dashscope
dashscope.api_key = key
from dashscope.audio.asr import Recognition
audio = '%s'
if not os.path.isfile(audio):
    print('ERROR: audio file not found: ' + audio)
    sys.exit(1)
t0 = time.time()
r = Recognition(model='fun-asr-realtime', callback=None, format='opus', sample_rate=16000)
result = r.call(audio)
elapsed = int((time.time() - t0) * 1000)
s = result.get_sentence()
texts = []
if s:
    for sent in s:
        texts.append(sent.get('text', '') if isinstance(sent, dict) else str(sent))
transcript = ' '.join(texts).strip()
import json
print(json.dumps({'ok': True, 'transcript': transcript, 'request_id': result.get_request_id(), 'elapsed_ms': elapsed}))
""" % (remote_dir, audio_file)
    sftp = ssh.open_sftp()
    with sftp.open("/tmp/_qpy_asr_probe.py", "w") as f:
        f.write(probe_script)
    sftp.close()
    out = _ssh_run(ssh, "cd %s && .venv/bin/python3 /tmp/_qpy_asr_probe.py" % remote_dir, timeout=30)
    _ssh_run(ssh, "rm -f /tmp/_qpy_asr_probe.py")
    try:
        return json.loads(out)
    except Exception:
        return {"ok": False, "raw": out}


def main() -> int:
    args = build_parser().parse_args()
    try:
        ssh = _ssh_connect(args.host, args.ssh_user, args.ssh_pass, args.ssh_port)
    except Exception as exc:
        result = {"ok": False, "error": "ssh connect failed: %s" % exc}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("ERROR:", result["error"])
        return 1

    summary: Dict[str, Any] = {"host": args.host, "sidecar_port": args.sidecar_port}
    try:
        if args.deploy:
            summary["deploy"] = deploy_app(ssh, args.remote_app_dir)

        if args.restart:
            summary["restart"] = restart_service(ssh, args.service_name)

        summary["http"] = check_http(ssh, args.sidecar_port)
        summary["service"] = check_service(ssh, args.service_name)
        summary["logs"] = check_logs(ssh, args.service_name, args.log_lines)

        if args.asr_probe:
            summary["asr_probe"] = asr_probe(ssh, args.remote_app_dir, args.asr_probe_file)

        summary["ok"] = (
            summary["http"].get("ok", False)
            and summary["service"].get("ok", False)
            and (not args.deploy or summary.get("deploy", {}).get("ok", False))
            and (not args.restart or summary.get("restart", {}).get("ok", False))
            and (not args.asr_probe or summary.get("asr_probe", {}).get("ok", False))
        )
    finally:
        ssh.close()

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("host:", summary["host"])
        print("http:", "OK" if summary["http"].get("ok") else "FAIL")
        print("service:", summary["service"].get("active", "unknown"))
        if args.deploy:
            print("deploy:", "OK" if summary.get("deploy", {}).get("ok") else "FAIL")
        if args.restart:
            print("restart:", "OK" if summary.get("restart", {}).get("ok") else "FAIL")
        if args.asr_probe:
            probe = summary.get("asr_probe", {})
            print("asr_probe:", "OK" if probe.get("ok") else "FAIL")
            if probe.get("transcript"):
                print("  transcript:", probe["transcript"])
        print("ok:", summary["ok"])
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
