#!/usr/bin/env python3
"""
Synchronize board-specific code to /usr/board using a board manifest.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any, Dict, List, Optional

HOST_DIR = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host"
)
DEFAULT_SYNC_SCRIPT = HOST_DIR / "qpy_usr_mirror_sync.py"
DEFAULT_BOARD_MANIFEST_DIR = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\embed"
    r"\qpyclaw-node\deploy\board-manifests"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync qpyclaw board-specific code to /usr/board."
    )
    parser.add_argument("--profile", required=True, help="Board profile key.")
    parser.add_argument("--manifest", default="", help="Board manifest path override.")
    parser.add_argument(
        "--sync-script",
        default=str(DEFAULT_SYNC_SCRIPT),
        help="Underlying generic sync script path.",
    )
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument("--timeout", type=int, default=40, help="Per-operation timeout seconds.")
    parser.add_argument("--subprocess-timeout", type=int, default=600, help="Child timeout seconds.")
    parser.add_argument("--skip-remove", action="store_true", help="Pass through to qpy_usr_mirror_sync.py.")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync only.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def resolve_manifest(profile: str, override: str) -> pathlib.Path:
    text = str(override or "").strip()
    if text:
        path = pathlib.Path(text).resolve()
    else:
        path = (DEFAULT_BOARD_MANIFEST_DIR / (str(profile).strip() + ".json")).resolve()
    if not path.is_file():
        raise SystemExit("Board manifest not found: %s" % path)
    return path


def build_command(args, manifest_path: pathlib.Path) -> List[str]:
    command = [
        sys.executable,
        str(pathlib.Path(args.sync_script).resolve()),
        "--manifest",
        str(manifest_path),
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
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
            "json": None,
            "parse_error": "timeout",
        }

    stdout = (cp.stdout or "").strip()
    stderr = (cp.stderr or "").strip()
    parsed: Optional[Dict[str, Any]] = None
    parse_error = ""
    if stdout:
        try:
            parsed = json.loads(stdout)
        except Exception as e:
            parse_error = "failed to parse child JSON: %s" % e
    else:
        parse_error = "child stdout is empty"

    return {
        "ok": cp.returncode == 0 and bool(isinstance(parsed, dict) and parsed.get("ok")),
        "exit_code": cp.returncode,
        "timed_out": False,
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed,
        "parse_error": parse_error,
        "command": command,
    }


def main() -> int:
    args = build_parser().parse_args()
    manifest_path = resolve_manifest(args.profile, args.manifest)
    result = run_json_command(
        build_command(args, manifest_path),
        timeout=int(args.subprocess_timeout),
    )

    summary: Dict[str, Any] = {
        "flow": "qpy-board-code-sync",
        "profile": args.profile,
        "manifest": str(manifest_path),
        "port": args.port,
        "baud": int(args.baud),
        "dry_run": bool(args.dry_run),
        "ok": bool(result.get("ok")),
        "exit_code": result.get("exit_code"),
        "timed_out": bool(result.get("timed_out")),
        "result": result.get("json"),
    }
    if result.get("stderr"):
        summary["stderr"] = result.get("stderr")
    if result.get("parse_error"):
        summary["parse_error"] = result.get("parse_error")
        if result.get("stdout"):
            summary["stdout"] = result.get("stdout")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("flow:", summary["flow"])
        print("profile:", summary["profile"])
        print("manifest:", summary["manifest"])
        print("dry_run:", summary["dry_run"])
        print("board_sync:", "OK" if summary["ok"] else "FAIL")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
