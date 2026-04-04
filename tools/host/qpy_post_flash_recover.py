#!/usr/bin/env python3
"""
Standard post-flash recovery flow for qpyclaw-node.

Sequence:
1. Restore runtime files to device /usr via manifest-driven sync.
2. Restore optional board-specific code and media manifests.
3. Bootstrap device-local config_local.py from a board profile.

By default, config bootstrap still protects an existing device
config_local.py unless --force-config is explicitly set.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any, Dict, List

HOST_DIR = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host"
)
DEFAULT_SYNC_SCRIPT = HOST_DIR / "qpy_usr_mirror_sync.py"
DEFAULT_BOARD_SYNC_SCRIPT = HOST_DIR / "qpy_board_code_sync.py"
DEFAULT_BOARD_MEDIA_SYNC_SCRIPT = HOST_DIR / "qpy_board_media_sync.py"
DEFAULT_CONFIG_SCRIPT = HOST_DIR / "qpy_config_local_bootstrap.py"
DEFAULT_SMOKE_SCRIPT = HOST_DIR / "qpy_runtime_smoke.py"
DEFAULT_BOARD_PROBE_SCRIPT = HOST_DIR / "qpy_board_runtime_probe.py"
DEFAULT_BOARD_MANIFEST_DIR = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\embed"
    r"\qpyclaw-node\deploy\board-manifests"
)

SECRET_FLAGS = {
    "--auth-token",
    "--remote-signer-auth-token",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the standard qpyclaw-node post-flash recovery flow."
    )
    parser.add_argument(
        "--sync-script",
        default=str(DEFAULT_SYNC_SCRIPT),
        help="Host runtime sync script path.",
    )
    parser.add_argument(
        "--config-script",
        default=str(DEFAULT_CONFIG_SCRIPT),
        help="Host config bootstrap script path.",
    )
    parser.add_argument(
        "--board-sync-script",
        default=str(DEFAULT_BOARD_SYNC_SCRIPT),
        help="Host board sync script path.",
    )
    parser.add_argument(
        "--board-media-sync-script",
        default=str(DEFAULT_BOARD_MEDIA_SYNC_SCRIPT),
        help="Host board media sync script path.",
    )
    parser.add_argument(
        "--smoke-script",
        default=str(DEFAULT_SMOKE_SCRIPT),
        help="Host runtime smoke script path.",
    )
    parser.add_argument(
        "--board-probe-script",
        default=str(DEFAULT_BOARD_PROBE_SCRIPT),
        help="Host board runtime probe script path.",
    )
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=40,
        help="Per-operation timeout passed to child scripts.",
    )
    parser.add_argument(
        "--subprocess-timeout",
        type=int,
        default=600,
        help="Whole child-process timeout seconds.",
    )

    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip runtime manifest sync.",
    )
    parser.add_argument(
        "--skip-config",
        action="store_true",
        help="Skip config_local bootstrap.",
    )
    parser.add_argument(
        "--skip-board-sync",
        action="store_true",
        help="Skip board-specific code sync.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without changing the device.",
    )
    parser.add_argument(
        "--skip-board-media-sync",
        action="store_true",
        help="Skip board-specific media sync.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run qpy_runtime_smoke.py after recovery succeeds.",
    )
    parser.add_argument(
        "--board-probe",
        action="store_true",
        help="Run qpy_board_runtime_probe.py after recovery succeeds.",
    )

    parser.add_argument(
        "--manifest",
        default="",
        help="Runtime manifest path override for qpy_usr_mirror_sync.py.",
    )
    parser.add_argument(
        "--board-manifest",
        default="",
        help="Board manifest path override for board code sync.",
    )
    parser.add_argument(
        "--board-media-manifest",
        default="",
        help="Board media manifest path override for board media sync.",
    )
    parser.add_argument(
        "--local-root",
        default="",
        help="Local runtime source root override for qpy_usr_mirror_sync.py.",
    )
    parser.add_argument(
        "--remote-root",
        default="",
        help="Remote runtime root override for qpy_usr_mirror_sync.py.",
    )
    parser.add_argument(
        "--ignore-manifest",
        action="store_true",
        help="Pass through to qpy_usr_mirror_sync.py.",
    )
    parser.add_argument(
        "--skip-remove",
        action="store_true",
        help="Pass through to qpy_usr_mirror_sync.py.",
    )

    parser.add_argument(
        "--profiles",
        default="",
        help="Profile registry path override for qpy_config_local_bootstrap.py.",
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Board profile key for config_local bootstrap.",
    )
    parser.add_argument(
        "--config-remote-path",
        default="/usr/config_local.py",
        help="Target remote path for config_local bootstrap.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Overwrite an existing config_local target path.",
    )
    parser.add_argument(
        "--show-config-content",
        action="store_true",
        help="Include rendered config content in wrapper JSON/text output.",
    )
    parser.add_argument("--device-id", default="", help="Override DEVICE_ID.")
    parser.add_argument("--device-name", default="", help="Override DEVICE_NAME.")
    parser.add_argument(
        "--client-display-name",
        default="",
        help="Override OPENCLAW_CLIENT_DISPLAY_NAME.",
    )
    parser.add_argument("--tenant-id", default="", help="Override TENANT_ID.")
    parser.add_argument("--ws-url", default="", help="Override OPENCLAW_WS_URL.")
    parser.add_argument(
        "--auth-token",
        default="",
        help="Override OPENCLAW_AUTH_TOKEN.",
    )
    parser.add_argument(
        "--device-auth-mode",
        choices=["none", "remote_signer_http"],
        default="none",
        help="Rendered OPENCLAW_DEVICE_AUTH_MODE.",
    )
    parser.add_argument(
        "--remote-signer-url",
        default="",
        help="REMOTE_SIGNER_HTTP_URL for config bootstrap.",
    )
    parser.add_argument(
        "--remote-signer-auth-token",
        default="",
        help="REMOTE_SIGNER_HTTP_AUTH_TOKEN for config bootstrap.",
    )
    parser.add_argument(
        "--smoke-fs-read-path",
        default="/usr/qpyclaw_node.py",
        help="Filesystem path passed to qpy_runtime_smoke.py.",
    )
    parser.add_argument(
        "--smoke-fs-read-max-bytes",
        type=int,
        default=128,
        help="max_bytes passed to qpy_runtime_smoke.py.",
    )
    parser.add_argument(
        "--smoke-include-raw",
        action="store_true",
        help="Include raw REPL transcript in smoke JSON output.",
    )
    parser.add_argument(
        "--board-probe-include-raw",
        action="store_true",
        help="Include raw REPL transcript in board probe JSON output.",
    )
    parser.add_argument(
        "--board-probe-skip-dispatch",
        action="store_true",
        help="Probe current board runtime without re-running dispatch.py.",
    )
    parser.add_argument(
        "--board-probe-attempts",
        type=int,
        default=3,
        help="Maximum qpy_board_runtime_probe.py attempts.",
    )
    parser.add_argument(
        "--board-probe-retry-seconds",
        type=float,
        default=2.0,
        help="Retry wait passed to qpy_board_runtime_probe.py.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def append_opt(command: List[str], flag: str, value: str) -> None:
    text = str(value or "").strip()
    if text:
        command.extend([flag, text])


def mask_command(command: List[str]) -> List[str]:
    masked: List[str] = []
    hide_next = False
    for token in command:
        if hide_next:
            masked.append("***")
            hide_next = False
            continue
        masked.append(token)
        if token in SECRET_FLAGS:
            hide_next = True
    return masked


def run_json_command(command: List[str], timeout: int) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(30, int(timeout)),
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "exit_code": None,
            "timed_out": True,
            "command": mask_command(command),
            "stdout": (e.stdout or ""),
            "stderr": (e.stderr or ""),
            "json": None,
            "parse_error": "timeout",
        }

    stdout = (cp.stdout or "").strip()
    stderr = (cp.stderr or "").strip()
    parsed = None
    parse_error = ""
    if stdout:
        try:
            parsed = json.loads(stdout)
        except Exception as e:
            parse_error = "failed to parse child JSON: %s" % e
    else:
        parse_error = "child stdout is empty"

    child_ok = bool(isinstance(parsed, dict) and parsed.get("ok"))
    return {
        "ok": cp.returncode == 0 and child_ok,
        "exit_code": cp.returncode,
        "timed_out": False,
        "command": mask_command(command),
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed,
        "parse_error": parse_error,
    }


def build_sync_command(args) -> List[str]:
    command = [
        sys.executable,
        str(pathlib.Path(args.sync_script).resolve()),
        "--port",
        args.port,
        "--baud",
        str(int(args.baud)),
        "--timeout",
        str(int(args.timeout)),
        "--json",
    ]
    append_opt(command, "--manifest", args.manifest)
    append_opt(command, "--local-root", args.local_root)
    append_opt(command, "--remote-root", args.remote_root)
    if args.ignore_manifest:
        command.append("--ignore-manifest")
    if args.skip_remove:
        command.append("--skip-remove")
    if args.dry_run:
        command.append("--dry-run")
    return command


def resolve_board_manifest(args) -> str:
    text = str(args.board_manifest or "").strip()
    if text:
        return str(pathlib.Path(text).resolve())
    candidate = (DEFAULT_BOARD_MANIFEST_DIR / (str(args.profile).strip() + ".json")).resolve()
    if candidate.is_file():
        return str(candidate)
    return ""


def build_board_sync_command(args, board_manifest: str) -> List[str]:
    command = [
        sys.executable,
        str(pathlib.Path(args.board_sync_script).resolve()),
        "--profile",
        args.profile,
        "--manifest",
        board_manifest,
        "--port",
        args.port,
        "--baud",
        str(int(args.baud)),
        "--timeout",
        str(int(args.timeout)),
        "--json",
    ]
    if args.skip_remove:
        command.append("--skip-remove")
    if args.dry_run:
        command.append("--dry-run")
    return command


def resolve_board_media_manifest(args) -> str:
    text = str(args.board_media_manifest or "").strip()
    if text:
        return str(pathlib.Path(text).resolve())
    candidate = (DEFAULT_BOARD_MANIFEST_DIR / (str(args.profile).strip() + "-media.json")).resolve()
    if candidate.is_file():
        return str(candidate)
    return ""


def build_board_media_sync_command(args, board_media_manifest: str) -> List[str]:
    command = [
        sys.executable,
        str(pathlib.Path(args.board_media_sync_script).resolve()),
        "--profile",
        args.profile,
        "--manifest",
        board_media_manifest,
        "--port",
        args.port,
        "--baud",
        str(int(args.baud)),
        "--timeout",
        str(int(args.timeout)),
        "--json",
    ]
    if args.skip_remove:
        command.append("--skip-remove")
    if args.dry_run:
        command.append("--dry-run")
    return command


def build_config_command(args) -> List[str]:
    command = [
        sys.executable,
        str(pathlib.Path(args.config_script).resolve()),
        "--profile",
        args.profile,
        "--port",
        args.port,
        "--baud",
        str(int(args.baud)),
        "--timeout",
        str(int(args.timeout)),
        "--remote-path",
        args.config_remote_path,
        "--device-auth-mode",
        args.device_auth_mode,
        "--json",
    ]
    append_opt(command, "--profiles", args.profiles)
    append_opt(command, "--device-id", args.device_id)
    append_opt(command, "--device-name", args.device_name)
    append_opt(command, "--client-display-name", args.client_display_name)
    append_opt(command, "--tenant-id", args.tenant_id)
    append_opt(command, "--ws-url", args.ws_url)
    append_opt(command, "--auth-token", args.auth_token)
    append_opt(command, "--remote-signer-url", args.remote_signer_url)
    append_opt(command, "--remote-signer-auth-token", args.remote_signer_auth_token)
    if args.show_config_content:
        command.append("--show-content")
    if not args.dry_run:
        command.append("--push")
    if args.force_config:
        command.append("--force")
    return command


def build_smoke_command(args) -> List[str]:
    command = [
        sys.executable,
        str(pathlib.Path(args.smoke_script).resolve()),
        "--port",
        args.port,
        "--baud",
        str(int(args.baud)),
        "--timeout",
        str(int(args.timeout)),
        "--fs-read-path",
        args.smoke_fs_read_path,
        "--fs-read-max-bytes",
        str(int(args.smoke_fs_read_max_bytes)),
        "--json",
    ]
    if args.smoke_include_raw:
        command.append("--include-raw")
    return command


def build_board_probe_command(args) -> List[str]:
    command = [
        sys.executable,
        str(pathlib.Path(args.board_probe_script).resolve()),
        "--port",
        args.port,
        "--baud",
        str(int(args.baud)),
        "--timeout",
        str(int(args.timeout)),
        "--probe-attempts",
        str(int(args.board_probe_attempts)),
        "--probe-retry-seconds",
        str(float(args.board_probe_retry_seconds)),
        "--json",
    ]
    if args.board_probe_include_raw:
        command.append("--include-raw")
    if args.board_probe_skip_dispatch:
        command.append("--skip-dispatch")
    return command


def summarize_child(result: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "ok": bool(result.get("ok")),
        "exit_code": result.get("exit_code"),
        "timed_out": bool(result.get("timed_out")),
        "command": result.get("command"),
    }
    if result.get("json") is not None:
        summary["result"] = result.get("json")
    if result.get("stderr"):
        summary["stderr"] = result.get("stderr")
    if result.get("parse_error"):
        summary["parse_error"] = result.get("parse_error")
        if result.get("stdout"):
            summary["stdout"] = result.get("stdout")
    return summary


def main() -> int:
    args = build_parser().parse_args()

    summary: Dict[str, Any] = {
        "flow": "qpyclaw-node-post-flash-recover",
        "port": args.port,
        "baud": int(args.baud),
        "profile": args.profile,
        "dry_run": bool(args.dry_run),
        "steps": [
            "runtime_sync" if not args.skip_sync else "runtime_sync_skipped",
            "board_sync" if not args.skip_board_sync else "board_sync_skipped",
            "board_media_sync" if not args.skip_board_media_sync else "board_media_sync_skipped",
            "config_bootstrap" if not args.skip_config else "config_bootstrap_skipped",
            "runtime_smoke"
            if bool(args.smoke) and not bool(args.dry_run)
            else ("runtime_smoke_requested_but_dry_run" if bool(args.smoke) else "runtime_smoke_not_requested"),
            "board_runtime_probe"
            if bool(args.board_probe) and not bool(args.dry_run)
            else ("board_runtime_probe_requested_but_dry_run" if bool(args.board_probe) else "board_runtime_probe_not_requested"),
        ],
        "sync": {
            "requested": not bool(args.skip_sync),
            "skipped": bool(args.skip_sync),
        },
        "config": {
            "requested": not bool(args.skip_config),
            "skipped": bool(args.skip_config),
            "remote_path": args.config_remote_path,
        },
        "board_sync": {
            "requested": not bool(args.skip_board_sync),
            "skipped": bool(args.skip_board_sync),
        },
        "board_media_sync": {
            "requested": not bool(args.skip_board_media_sync),
            "skipped": bool(args.skip_board_media_sync),
        },
        "smoke": {
            "requested": bool(args.smoke),
            "skipped": not bool(args.smoke),
            "fs_read_path": args.smoke_fs_read_path,
            "fs_read_max_bytes": int(args.smoke_fs_read_max_bytes),
        },
        "board_probe": {
            "requested": bool(args.board_probe),
            "skipped": not bool(args.board_probe),
            "skip_dispatch": bool(args.board_probe_skip_dispatch),
            "attempts": int(args.board_probe_attempts),
            "retry_seconds": float(args.board_probe_retry_seconds),
        },
        "ok": True,
    }

    if not args.skip_sync:
        sync_result = run_json_command(
            build_sync_command(args),
            timeout=int(args.subprocess_timeout),
        )
        summary["sync"] = summarize_child(sync_result)
        summary["sync"]["requested"] = True
        summary["sync"]["skipped"] = False
        if not sync_result.get("ok"):
            summary["ok"] = False
            if not args.skip_config:
                summary["config"] = {
                    "requested": True,
                    "skipped": True,
                    "remote_path": args.config_remote_path,
                    "reason": "runtime sync failed",
                }
            if not args.skip_board_sync:
                summary["board_sync"] = {
                    "requested": True,
                    "skipped": True,
                    "reason": "runtime sync failed",
                }
            if not args.skip_board_media_sync:
                summary["board_media_sync"] = {
                    "requested": True,
                    "skipped": True,
                    "reason": "runtime sync failed",
                }

    board_manifest = ""
    if not args.skip_board_sync:
        board_manifest = resolve_board_manifest(args)
        if not board_manifest:
            summary["board_sync"] = {
                "requested": False,
                "skipped": True,
                "reason": "no_board_manifest",
            }
        elif summary["ok"]:
            board_result = run_json_command(
                build_board_sync_command(args, board_manifest),
                timeout=int(args.subprocess_timeout),
            )
            summary["board_sync"] = summarize_child(board_result)
            summary["board_sync"]["requested"] = True
            summary["board_sync"]["skipped"] = False
            summary["board_sync"]["manifest"] = board_manifest
            if not board_result.get("ok"):
                summary["ok"] = False

    board_media_manifest = ""
    if not args.skip_board_media_sync:
        board_media_manifest = resolve_board_media_manifest(args)
        if not board_media_manifest:
            summary["board_media_sync"] = {
                "requested": False,
                "skipped": True,
                "reason": "no_board_media_manifest",
            }
        elif summary["ok"]:
            board_media_result = run_json_command(
                build_board_media_sync_command(args, board_media_manifest),
                timeout=int(args.subprocess_timeout),
            )
            summary["board_media_sync"] = summarize_child(board_media_result)
            summary["board_media_sync"]["requested"] = True
            summary["board_media_sync"]["skipped"] = False
            summary["board_media_sync"]["manifest"] = board_media_manifest
            if not board_media_result.get("ok"):
                summary["ok"] = False

    if summary["ok"] and not args.skip_config:
        config_result = run_json_command(
            build_config_command(args),
            timeout=int(args.subprocess_timeout),
        )
        summary["config"] = summarize_child(config_result)
        summary["config"]["requested"] = True
        summary["config"]["skipped"] = False
        summary["config"]["remote_path"] = args.config_remote_path
        if not config_result.get("ok"):
            summary["ok"] = False

    if bool(args.smoke):
        if bool(args.dry_run):
            summary["smoke"] = {
                "requested": True,
                "skipped": True,
                "reason": "dry_run",
                "fs_read_path": args.smoke_fs_read_path,
                "fs_read_max_bytes": int(args.smoke_fs_read_max_bytes),
            }
        elif summary["ok"]:
            smoke_result = run_json_command(
                build_smoke_command(args),
                timeout=int(args.subprocess_timeout),
            )
            summary["smoke"] = summarize_child(smoke_result)
            summary["smoke"]["requested"] = True
            summary["smoke"]["skipped"] = False
            summary["smoke"]["fs_read_path"] = args.smoke_fs_read_path
            summary["smoke"]["fs_read_max_bytes"] = int(args.smoke_fs_read_max_bytes)
            if not smoke_result.get("ok"):
                summary["ok"] = False
        else:
            summary["smoke"] = {
                "requested": True,
                "skipped": True,
                "reason": "prior_step_failed",
                "fs_read_path": args.smoke_fs_read_path,
                "fs_read_max_bytes": int(args.smoke_fs_read_max_bytes),
            }

    if bool(args.board_probe):
        if bool(args.dry_run):
            summary["board_probe"] = {
                "requested": True,
                "skipped": True,
                "reason": "dry_run",
                "skip_dispatch": bool(args.board_probe_skip_dispatch),
                "attempts": int(args.board_probe_attempts),
                "retry_seconds": float(args.board_probe_retry_seconds),
            }
        elif summary["ok"]:
            board_probe_result = run_json_command(
                build_board_probe_command(args),
                timeout=int(args.subprocess_timeout),
            )
            summary["board_probe"] = summarize_child(board_probe_result)
            summary["board_probe"]["requested"] = True
            summary["board_probe"]["skipped"] = False
            summary["board_probe"]["skip_dispatch"] = bool(args.board_probe_skip_dispatch)
            summary["board_probe"]["attempts"] = int(args.board_probe_attempts)
            summary["board_probe"]["retry_seconds"] = float(args.board_probe_retry_seconds)
            if not board_probe_result.get("ok"):
                summary["ok"] = False
        else:
            summary["board_probe"] = {
                "requested": True,
                "skipped": True,
                "reason": "prior_step_failed",
                "skip_dispatch": bool(args.board_probe_skip_dispatch),
                "attempts": int(args.board_probe_attempts),
                "retry_seconds": float(args.board_probe_retry_seconds),
            }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("flow:", summary["flow"])
        print("profile:", summary["profile"])
        print("dry_run:", summary["dry_run"])
        if summary["sync"].get("requested"):
            print("runtime_sync:", "OK" if summary["sync"].get("ok") else "FAIL")
        else:
            print("runtime_sync: skipped")
        if summary["board_sync"].get("requested"):
            print("board_sync:", "OK" if summary["board_sync"].get("ok") else "FAIL")
        else:
            print("board_sync: skipped")
        if summary["board_media_sync"].get("requested"):
            print("board_media_sync:", "OK" if summary["board_media_sync"].get("ok") else "FAIL")
        else:
            print("board_media_sync: skipped")
        if summary["config"].get("requested"):
            print("config_bootstrap:", "OK" if summary["config"].get("ok") else "FAIL")
            print("config_remote_path:", summary["config"].get("remote_path"))
        else:
            print("config_bootstrap: skipped")
        if summary["smoke"].get("requested") and not summary["smoke"].get("skipped"):
            print("runtime_smoke:", "OK" if summary["smoke"].get("ok") else "FAIL")
        elif summary["smoke"].get("requested"):
            print("runtime_smoke: skipped")
        else:
            print("runtime_smoke: not requested")
        if summary["board_probe"].get("requested") and not summary["board_probe"].get("skipped"):
            print("board_runtime_probe:", "OK" if summary["board_probe"].get("ok") else "FAIL")
        elif summary["board_probe"].get("requested"):
            print("board_runtime_probe: skipped")
        else:
            print("board_runtime_probe: not requested")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
