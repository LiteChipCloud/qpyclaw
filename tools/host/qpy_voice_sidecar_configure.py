#!/usr/bin/env python3
"""
Patch a device-side qpyclaw config_local.py for the DashScope voice sidecar.

Non-goals:
1. Do not rewrite unrelated gateway/token settings.
2. Do not print real secrets in stdout.
3. Do not require manual editing once the device REPL port is back.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
from typing import Any, Dict

HOST_DIR = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host"
)
QPY_BOOTSTRAP = HOST_DIR / "qpy_config_local_bootstrap.py"


def load_bootstrap_module():
    spec = importlib.util.spec_from_file_location("qpy_config_local_bootstrap", QPY_BOOTSTRAP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Patch /usr/config_local.py to use the qpyclaw DashScope voice sidecar."
    )
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument(
        "--remote-path",
        default="/usr/config_local.py",
        help="Device-side config path. Default /usr/config_local.py.",
    )
    parser.add_argument(
        "--voice-enabled",
        choices=["keep", "true", "false"],
        default="keep",
        help="Whether to patch VOICE_ENABLED. Default keep.",
    )
    parser.add_argument(
        "--provider",
        default="remote_asr_http",
        help="VOICE_TRANSCRIPT_PROVIDER value.",
    )
    parser.add_argument(
        "--asr-url",
        default="http://124.70.221.88:8788/api/asr",
        help="VOICE_ASR_HTTP_URL value.",
    )
    parser.add_argument(
        "--asr-auth-token",
        required=True,
        help="VOICE_ASR_HTTP_AUTH_TOKEN value.",
    )
    parser.add_argument(
        "--audio-format",
        default="oggopus",
        help="VOICE_ASR_HTTP_AUDIO_FORMAT value.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="VOICE_ASR_HTTP_SAMPLE_RATE value.",
    )
    parser.add_argument(
        "--tts-enabled",
        choices=["keep", "true", "false"],
        default="keep",
        help="Whether to patch VOICE_TTS_HTTP_ENABLED. Default keep.",
    )
    parser.add_argument(
        "--tts-url",
        default="",
        help="VOICE_TTS_HTTP_URL value. Default derives from --asr-url.",
    )
    parser.add_argument(
        "--tts-auth-token",
        default="",
        help="VOICE_TTS_HTTP_AUTH_TOKEN value. Default reuses --asr-auth-token.",
    )
    parser.add_argument(
        "--tts-audio-format",
        default="mp3",
        help="VOICE_TTS_HTTP_AUDIO_FORMAT value.",
    )
    parser.add_argument(
        "--tts-sample-rate",
        type=int,
        default=16000,
        help="VOICE_TTS_HTTP_SAMPLE_RATE value.",
    )
    parser.add_argument(
        "--tts-voice",
        default="Cherry",
        help="VOICE_TTS_HTTP_VOICE value.",
    )
    parser.add_argument(
        "--tts-cache-path",
        default="/usr/qpyclaw/voice_reply.mp3",
        help="VOICE_TTS_HTTP_CACHE_PATH value.",
    )
    parser.add_argument(
        "--tts-play-timeout-ms",
        type=int,
        default=20000,
        help="VOICE_TTS_HTTP_PLAY_TIMEOUT_MS value.",
    )
    parser.add_argument(
        "--tts-stream-enabled",
        choices=["keep", "true", "false"],
        default="keep",
        help="Whether to patch VOICE_TTS_STREAM_ENABLED. Default keep.",
    )
    parser.add_argument(
        "--tts-stream-url",
        default="",
        help="VOICE_TTS_STREAM_URL value. Default derives from --tts-url / --asr-url.",
    )
    parser.add_argument(
        "--tts-stream-auth-token",
        default="",
        help="VOICE_TTS_STREAM_AUTH_TOKEN value. Default reuses --tts-auth-token or --asr-auth-token.",
    )
    parser.add_argument(
        "--tts-stream-format",
        default="opus",
        help="VOICE_TTS_STREAM_FORMAT value.",
    )
    parser.add_argument(
        "--tts-stream-sample-rate",
        type=int,
        default=16000,
        help="VOICE_TTS_STREAM_SAMPLE_RATE value.",
    )
    parser.add_argument(
        "--tts-stream-voice",
        default="",
        help="VOICE_TTS_STREAM_VOICE value. Default uses --tts-voice.",
    )
    parser.add_argument(
        "--tts-stream-connect-timeout-sec",
        type=int,
        default=8,
        help="VOICE_TTS_STREAM_CONNECT_TIMEOUT_SEC value.",
    )
    parser.add_argument(
        "--tts-stream-timeout-ms",
        type=int,
        default=15000,
        help="VOICE_TTS_STREAM_TIMEOUT_MS value.",
    )
    parser.add_argument(
        "--tts-stream-close-after-play",
        choices=["keep", "true", "false"],
        default="keep",
        help="Whether to patch VOICE_TTS_STREAM_CLOSE_AFTER_PLAY. Default keep.",
    )
    parser.add_argument(
        "--headers-json",
        default='{"X-Device-Class":"qpyclaw-node"}',
        help="VOICE_ASR_HTTP_HEADERS JSON object.",
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Include patched config content in output.",
    )
    parser.add_argument("--timeout", type=int, default=45, help="Per-operation timeout seconds.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def derive_tts_url(asr_url: str) -> str:
    text = str(asr_url or "").strip()
    if text.endswith("/api/asr"):
        return text[:-8] + "/api/tts"
    return text


def to_ws_url(url: str) -> str:
    text = str(url or "").strip()
    if not text:
        return ""
    if text.startswith("ws://") or text.startswith("wss://"):
        return text
    if text.startswith("http://"):
        return "ws://" + text[7:]
    if text.startswith("https://"):
        return "wss://" + text[8:]
    return text


def derive_tts_stream_url(tts_url: str, asr_url: str) -> str:
    text = to_ws_url(tts_url)
    if text:
        if text.endswith("/api/tts"):
            return text[:-8] + "/ws/tts"
        return text
    derived_tts = derive_tts_url(asr_url)
    text = to_ws_url(derived_tts)
    if text.endswith("/api/tts"):
        return text[:-8] + "/ws/tts"
    return text


def read_remote_text(cli, port: str, baud: int, remote_path: str, timeout: int) -> Dict[str, Any]:
    path_qpy = cli.single_quote_qpy(remote_path)
    lines = [
        "import ujson",
        "_code=\"def _qread(p):\\n f=open(p,'r')\\n try:\\n  return f.read()\\n finally:\\n  f.close()\\n\"",
        "exec(_code)",
        "_txt=_qread('%s')" % path_qpy,
        "print('QPY_CONFIG_LOCAL_JSON=' + ujson.dumps({'content': _txt}))",
    ]
    raw = cli.repl_send_lines(
        port,
        baud,
        lines,
        timeout=max(12, timeout),
        line_delay_ms=70,
        settle_ms=4000,
    )
    marker = "QPY_CONFIG_LOCAL_JSON="
    text = raw or ""
    start = text.rfind(marker)
    if start < 0:
        return {"ok": False, "raw": raw, "content": ""}
    start += len(marker)
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        return {"ok": False, "raw": raw, "content": ""}
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
        return {"ok": False, "raw": raw, "content": ""}
    try:
        payload = json.loads(text[start:end])
    except Exception:
        return {"ok": False, "raw": raw, "content": ""}
    return {"ok": True, "raw": raw, "content": str(payload.get("content") or "")}


def mask_secret(value: str) -> str:
    text = str(value or "")
    if not text:
        return ""
    if len(text) <= 6:
        return "*" * len(text)
    return text[:3] + ("*" * (len(text) - 5)) + text[-2:]


def format_py_value(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    return repr(value)


def patch_assignment(content: str, key: str, value: Any) -> tuple[str, bool]:
    rendered = "%s = %s" % (key, format_py_value(value))
    pattern = re.compile(r"(?m)^%s\s*=.*$" % re.escape(key))
    if pattern.search(content):
        return pattern.sub(rendered, content), True
    text = content
    if text and not text.endswith("\n"):
        text += "\n"
    text += rendered + "\n"
    return text, False


def main() -> int:
    args = build_parser().parse_args()
    bootstrap = load_bootstrap_module()
    cli = bootstrap.load_qpy_fs_cli()
    remote_path = bootstrap.normalize_remote_path(args.remote_path)
    timeout = max(12, int(args.timeout))

    try:
        headers = json.loads(args.headers_json or "{}")
    except Exception as exc:
        raise SystemExit("invalid --headers-json: %s" % exc)
    if not isinstance(headers, dict):
        raise SystemExit("--headers-json must decode to a JSON object")

    exists = bootstrap.remote_file_exists(cli, args.port, int(args.baud), remote_path, timeout)
    resolved_tts_url = str(args.tts_url or derive_tts_url(args.asr_url))
    resolved_tts_auth_token = str(args.tts_auth_token or args.asr_auth_token)
    resolved_tts_stream_url = str(args.tts_stream_url or derive_tts_stream_url(resolved_tts_url, args.asr_url))
    resolved_tts_stream_auth_token = str(
        args.tts_stream_auth_token or args.tts_auth_token or args.asr_auth_token
    )
    resolved_tts_stream_voice = str(args.tts_stream_voice or args.tts_voice)

    summary: Dict[str, Any] = {
        "flow": "qpy-voice-sidecar-configure",
        "port": args.port,
        "baud": int(args.baud),
        "remote_path": remote_path,
        "remote_exists": bool(exists),
        "voice_enabled_mode": args.voice_enabled,
        "provider": args.provider,
        "asr_url": args.asr_url,
        "asr_auth_token_masked": mask_secret(args.asr_auth_token),
        "audio_format": args.audio_format,
        "sample_rate": int(args.sample_rate),
        "tts_enabled_mode": args.tts_enabled,
        "tts_url": resolved_tts_url,
        "tts_auth_token_masked": mask_secret(resolved_tts_auth_token),
        "tts_audio_format": args.tts_audio_format,
        "tts_sample_rate": int(args.tts_sample_rate),
        "tts_voice": args.tts_voice,
        "tts_cache_path": args.tts_cache_path,
        "tts_play_timeout_ms": int(args.tts_play_timeout_ms),
        "tts_stream_enabled_mode": args.tts_stream_enabled,
        "tts_stream_url": resolved_tts_stream_url,
        "tts_stream_auth_token_masked": mask_secret(resolved_tts_stream_auth_token),
        "tts_stream_format": args.tts_stream_format,
        "tts_stream_sample_rate": int(args.tts_stream_sample_rate),
        "tts_stream_voice": resolved_tts_stream_voice,
        "tts_stream_connect_timeout_sec": int(args.tts_stream_connect_timeout_sec),
        "tts_stream_timeout_ms": int(args.tts_stream_timeout_ms),
        "tts_stream_close_after_play_mode": args.tts_stream_close_after_play,
        "headers": headers,
        "patched_keys": [],
        "created_keys": [],
        "ok": True,
    }

    if not exists:
        summary["ok"] = False
        summary["error"] = "remote config_local.py not found"
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print("ok: False")
            print("error:", summary["error"])
        return 1

    read_result = read_remote_text(cli, args.port, int(args.baud), remote_path, timeout)
    if not read_result.get("ok"):
        summary["ok"] = False
        summary["error"] = "failed to read remote config_local.py"
        summary["read_raw"] = read_result.get("raw", "")
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print("ok: False")
            print("error:", summary["error"])
        return 1

    content = str(read_result.get("content") or "").replace("\r\n", "\n").replace("\r", "\n")
    updates = [
        ("VOICE_TRANSCRIPT_PROVIDER", str(args.provider)),
        ("VOICE_ASR_HTTP_URL", str(args.asr_url)),
        ("VOICE_ASR_HTTP_AUTH_TOKEN", str(args.asr_auth_token)),
        ("VOICE_ASR_HTTP_HEADERS", headers),
        ("VOICE_ASR_HTTP_AUDIO_FORMAT", str(args.audio_format)),
        ("VOICE_ASR_HTTP_SAMPLE_RATE", int(args.sample_rate)),
        ("VOICE_TTS_HTTP_URL", resolved_tts_url),
        ("VOICE_TTS_HTTP_AUTH_TOKEN", resolved_tts_auth_token),
        ("VOICE_TTS_HTTP_HEADERS", headers),
        ("VOICE_TTS_HTTP_AUDIO_FORMAT", str(args.tts_audio_format)),
        ("VOICE_TTS_HTTP_SAMPLE_RATE", int(args.tts_sample_rate)),
        ("VOICE_TTS_HTTP_VOICE", str(args.tts_voice)),
        ("VOICE_TTS_HTTP_CACHE_PATH", str(args.tts_cache_path)),
        ("VOICE_TTS_HTTP_PLAY_TIMEOUT_MS", int(args.tts_play_timeout_ms)),
        ("VOICE_TTS_STREAM_URL", resolved_tts_stream_url),
        ("VOICE_TTS_STREAM_WS_URL", resolved_tts_stream_url),
        ("VOICE_TTS_STREAM_AUTH_TOKEN", resolved_tts_stream_auth_token),
        ("VOICE_TTS_STREAM_HEADERS", headers),
        ("VOICE_TTS_STREAM_FORMAT", str(args.tts_stream_format)),
        ("VOICE_TTS_STREAM_AUDIO_FORMAT", str(args.tts_stream_format)),
        ("VOICE_TTS_STREAM_SAMPLE_RATE", int(args.tts_stream_sample_rate)),
        ("VOICE_TTS_STREAM_VOICE", resolved_tts_stream_voice),
        ("VOICE_TTS_STREAM_CONNECT_TIMEOUT_SEC", int(args.tts_stream_connect_timeout_sec)),
        ("VOICE_TTS_STREAM_TIMEOUT_MS", int(args.tts_stream_timeout_ms)),
        ("VOICE_TTS_STREAM_RECV_TIMEOUT_MS", int(args.tts_stream_timeout_ms)),
    ]
    if args.voice_enabled == "true":
        updates.insert(0, ("VOICE_ENABLED", True))
    elif args.voice_enabled == "false":
        updates.insert(0, ("VOICE_ENABLED", False))
    if args.tts_enabled == "true":
        updates.append(("VOICE_TTS_HTTP_ENABLED", True))
    elif args.tts_enabled == "false":
        updates.append(("VOICE_TTS_HTTP_ENABLED", False))
    if args.tts_stream_enabled == "true":
        updates.append(("VOICE_TTS_STREAM_ENABLED", True))
    elif args.tts_stream_enabled == "false":
        updates.append(("VOICE_TTS_STREAM_ENABLED", False))
    if args.tts_stream_close_after_play == "true":
        updates.append(("VOICE_TTS_STREAM_CLOSE_AFTER_PLAY", True))
    elif args.tts_stream_close_after_play == "false":
        updates.append(("VOICE_TTS_STREAM_CLOSE_AFTER_PLAY", False))

    patched_content = content
    for key, value in updates:
        patched_content, existed = patch_assignment(patched_content, key, value)
        if existed:
            summary["patched_keys"].append(key)
        else:
            summary["created_keys"].append(key)

    push_result = bootstrap.push_remote_content(
        cli,
        args.port,
        int(args.baud),
        remote_path,
        patched_content,
        timeout,
    )
    summary["push_ok"] = bool(push_result.get("ok"))
    summary["remote_size"] = push_result.get("remote_size")
    summary["local_size"] = push_result.get("local_size")
    summary["diagnostics"] = push_result.get("diagnostics", [])
    if args.show_content:
        summary["content"] = patched_content
    if not summary["push_ok"]:
        summary["ok"] = False
        summary["push_raw"] = push_result.get("raw", "")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("flow:", summary["flow"])
        print("remote:", summary["remote_path"])
        print("ok:", summary["ok"])
        print("patched keys:", ", ".join(summary["patched_keys"]))
        print("created keys:", ", ".join(summary["created_keys"]))
        if summary.get("error"):
            print("error:", summary["error"])
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
