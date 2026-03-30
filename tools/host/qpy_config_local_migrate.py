#!/usr/bin/env python3
"""
Migrate legacy /usr/app/config_local.py to the canonical /usr/config_local.py.

This is intentionally non-destructive by default:
1. read legacy file from the device
2. copy it to the canonical target
3. keep the legacy file unless --cleanup-legacy is set
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys
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
        description="Migrate legacy device config_local.py to /usr/config_local.py."
    )
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument(
        "--source-path",
        default="/usr/app/config_local.py",
        help="Legacy config path to read from the device.",
    )
    parser.add_argument(
        "--target-path",
        default="/usr/config_local.py",
        help="Canonical config path to write on the device.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing target file.",
    )
    parser.add_argument(
        "--cleanup-legacy",
        action="store_true",
        help="Delete the legacy source file after copy succeeds.",
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Include migrated config content in output.",
    )
    parser.add_argument("--timeout", type=int, default=40, help="Per-operation timeout seconds.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


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
    match = re.search(r"QPY_CONFIG_LOCAL_JSON=(\{.*?\})", raw or "")
    if not match:
        return {"ok": False, "raw": raw, "content": ""}
    try:
        payload = json.loads(match.group(1))
    except Exception:
        return {"ok": False, "raw": raw, "content": ""}
    return {
        "ok": True,
        "raw": raw,
        "content": str(payload.get("content") or ""),
    }


def remove_remote_file(cli, port: str, baud: int, remote_path: str, timeout: int) -> Dict[str, Any]:
    result = cli.run_repl_op(
        port,
        baud,
        [
            "import uos",
            "uos.remove('%s')" % cli.single_quote_qpy(remote_path),
            "print('rm_ok')",
        ],
        success_token="rm_ok",
        timeout=max(12, timeout),
    )
    return result


def main() -> int:
    args = build_parser().parse_args()
    bootstrap = load_bootstrap_module()
    cli = bootstrap.load_qpy_fs_cli()
    source_path = bootstrap.normalize_remote_path(args.source_path)
    target_path = bootstrap.normalize_remote_path(args.target_path)
    timeout = max(12, int(args.timeout))

    summary: Dict[str, Any] = {
        "flow": "qpy-config-local-migrate",
        "port": args.port,
        "baud": int(args.baud),
        "source_path": source_path,
        "target_path": target_path,
        "force": bool(args.force),
        "cleanup_legacy": bool(args.cleanup_legacy),
        "source_exists": False,
        "target_exists": False,
        "copied": False,
        "cleanup_done": False,
        "ok": True,
    }

    source_exists = bootstrap.remote_file_exists(cli, args.port, int(args.baud), source_path, timeout)
    target_exists = bootstrap.remote_file_exists(cli, args.port, int(args.baud), target_path, timeout)
    summary["source_exists"] = bool(source_exists)
    summary["target_exists"] = bool(target_exists)

    if not source_exists:
        summary["ok"] = False
        summary["error"] = "legacy source config not found"
    elif target_exists and not args.force:
        summary["skipped_existing_target"] = True
    else:
        read_result = read_remote_text(cli, args.port, int(args.baud), source_path, timeout)
        if not read_result.get("ok"):
            summary["ok"] = False
            summary["error"] = "failed to read legacy config"
            summary["read_raw"] = read_result.get("raw", "")
        else:
            content = str(read_result.get("content") or "")
            content = content.replace("\r\n", "\n").replace("\r", "\n")
            push_result = bootstrap.push_remote_content(
                cli,
                args.port,
                int(args.baud),
                target_path,
                content,
                timeout,
            )
            summary["copied"] = bool(push_result.get("ok"))
            summary["target_remote_size"] = push_result.get("remote_size")
            summary["target_local_size"] = push_result.get("local_size")
            summary["diagnostics"] = push_result.get("diagnostics", [])
            if args.show_content:
                summary["content"] = content
            if not summary["copied"]:
                summary["ok"] = False
                summary["push_raw"] = push_result.get("raw", "")
            elif args.cleanup_legacy and source_path != target_path:
                cleanup_result = remove_remote_file(
                    cli,
                    args.port,
                    int(args.baud),
                    source_path,
                    timeout,
                )
                summary["cleanup_done"] = bool(cleanup_result.get("ok"))
                if not summary["cleanup_done"]:
                    summary["ok"] = False
                    summary["cleanup_raw"] = cleanup_result.get("raw", "")

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("flow:", summary["flow"])
        print("source:", summary["source_path"])
        print("target:", summary["target_path"])
        print("ok:", summary["ok"])
        if summary.get("skipped_existing_target"):
            print("target already exists; migration skipped")
        elif summary.get("copied"):
            print("copied: OK")
        if summary.get("cleanup_done"):
            print("cleanup legacy: OK")
        if summary.get("error"):
            print("error:", summary["error"])
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
