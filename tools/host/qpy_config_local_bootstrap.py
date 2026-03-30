#!/usr/bin/env python3
"""
Render and optionally push a device-local config_local.py from a board profile.

This standardizes first-flash bring-up without overwriting an existing
device-side config_local.py unless explicitly forced.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile
from typing import Any, Dict

DEFAULT_PROFILE_REGISTRY = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\embed"
    r"\qpyclaw-node\deploy\config-local-profiles.json"
)
LEGACY_CONFIG_REMOTE_PATH = "/usr/app/config_local.py"


def load_qpy_fs_cli():
    skill_scripts = pathlib.Path(
        r"C:\Users\kingd\.codex\skills\quecpython-dev\scripts"
    )
    sys.path.insert(0, str(skill_scripts))
    import qpy_device_fs_cli as cli  # type: ignore

    return cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap qpyclaw-node device-local config_local.py from a board profile."
    )
    parser.add_argument(
        "--profiles",
        default=str(DEFAULT_PROFILE_REGISTRY),
        help="Board profile registry JSON path.",
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Profile key defined in config-local-profiles.json.",
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
        help="Override OPENCLAW_AUTH_TOKEN. Default placeholder if omitted.",
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
        help="REMOTE_SIGNER_HTTP_URL when device-auth-mode=remote_signer_http.",
    )
    parser.add_argument(
        "--remote-signer-auth-token",
        default="",
        help="REMOTE_SIGNER_HTTP_AUTH_TOKEN when device-auth-mode=remote_signer_http.",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional local output path for rendered config_local.py.",
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Include rendered Python content in stdout/json output.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push rendered config to the device.",
    )
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument(
        "--remote-path",
        default="/usr/config_local.py",
        help="Device-side target path. Default /usr/config_local.py.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing remote file. Default is protect-existing.",
    )
    parser.add_argument("--timeout", type=int, default=40, help="Per-operation timeout seconds.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def load_profiles(path: pathlib.Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit("Failed to load profile registry %s: %s" % (path, e))
    if not isinstance(data, dict):
        raise SystemExit("Profile registry must be a JSON object: %s" % path)
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise SystemExit("Profile registry missing profiles: %s" % path)
    return data


def mask_secret(value: str) -> str:
    text = str(value or "")
    if not text:
        return ""
    if len(text) <= 6:
        return "*" * len(text)
    return text[:3] + ("*" * (len(text) - 5)) + text[-2:]


def normalize_remote_path(value: str) -> str:
    text = str(value or "").replace("\\", "/").strip()
    if not text:
        raise SystemExit("remote path required")
    if not text.startswith("/usr/") and text != "/usr":
        raise SystemExit("remote path must stay under /usr: %s" % text)
    while "//" in text:
        text = text.replace("//", "/")
    if len(text) > 1 and text.endswith("/"):
        text = text[:-1]
    return text


def parent_remote_dir(remote_path: str) -> str:
    path = pathlib.PurePosixPath(remote_path)
    parent = path.parent.as_posix()
    return parent or "/"


def remote_file_name(remote_path: str) -> str:
    return pathlib.PurePosixPath(remote_path).name


def coalesce(*values: str) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def resolve_values(profile_name: str, profile: Dict[str, Any], args) -> Dict[str, str]:
    values = {
        "profile_name": profile_name,
        "device_id": coalesce(args.device_id, profile.get("default_device_id"), "qpyclaw_node_001"),
        "device_name": coalesce(args.device_name, profile.get("default_device_name"), "qpyclaw Node"),
        "device_model_hint": coalesce(profile.get("device_model_hint"), ""),
        "board_profile": coalesce(profile.get("board_profile"), profile_name),
        "client_display_name": coalesce(
            args.client_display_name,
            profile.get("default_client_display_name"),
            "qpyclaw QuecPython Node",
        ),
        "tenant_id": coalesce(args.tenant_id, profile.get("default_tenant_id"), "tenant_demo"),
        "ws_url": coalesce(
            args.ws_url,
            profile.get("default_ws_url"),
            "wss://your-public-openclaw-gateway.example.com:10503",
        ),
        "auth_token": coalesce(args.auth_token, "replace_with_real_gateway_token"),
        "device_auth_mode": str(args.device_auth_mode or "none"),
        "remote_signer_url": coalesce(args.remote_signer_url, "http://your-signer.example.com:8787/sign"),
        "remote_signer_auth_token": coalesce(args.remote_signer_auth_token, "replace_me"),
    }
    return values


def render_config_local(profile_name: str, profile: Dict[str, Any], values: Dict[str, str]) -> str:
    lines = [
        "# Generated by qpy_config_local_bootstrap.py",
        "# Profile: %s" % profile_name,
        "# Safe default: do not commit real device tokens.",
        "",
    ]
    notes = profile.get("notes") or []
    if isinstance(notes, list):
        for note in notes:
            text = str(note or "").strip()
            if text:
                lines.append("# " + text)
        if notes:
            lines.append("")

    lines.extend([
        'DEVICE_ID = %r' % values["device_id"],
        'DEVICE_NAME = %r' % values["device_name"],
        'DEVICE_MODEL_HINT = %r' % values["device_model_hint"],
        'BOARD_PROFILE = %r' % values["board_profile"],
        "",
        'OPENCLAW_WS_URL = %r' % values["ws_url"],
        'OPENCLAW_AUTH_TOKEN = %r' % values["auth_token"],
        'OPENCLAW_CLIENT_DISPLAY_NAME = %r' % values["client_display_name"],
        'TENANT_ID = %r' % values["tenant_id"],
        'OPENCLAW_DEVICE_AUTH_MODE = %r' % values["device_auth_mode"],
        "",
    ])

    if values["device_auth_mode"] == "remote_signer_http":
        lines.extend([
            'REMOTE_SIGNER_HTTP_URL = %r' % values["remote_signer_url"],
            'REMOTE_SIGNER_HTTP_AUTH_TOKEN = %r' % values["remote_signer_auth_token"],
            "",
        ])
    else:
        lines.extend([
            "# Optional official signed-device path:",
            '# REMOTE_SIGNER_HTTP_URL = "http://your-signer.example.com:8787/sign"',
            '# REMOTE_SIGNER_HTTP_AUTH_TOKEN = "replace_me"',
            "",
        ])

    lines.extend([
        "# Keep config.py on generic repo defaults.",
        "# Put device-local gateway/token/board identity here only.",
        "",
    ])
    return "\n".join(lines)


def write_local_output(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def remote_file_exists(cli, port: str, baud: int, remote_path: str, timeout: int) -> bool:
    result = cli.run_ls_repl(
        port,
        baud,
        parent_remote_dir(remote_path),
        timeout=max(12, timeout),
    )
    if not result.get("ok"):
        return False
    filename = remote_file_name(remote_path)
    for row in result.get("rows") or []:
        if row.get("name") == filename and row.get("type") == "file":
            return True
    return False


def push_remote_content(cli, port: str, baud: int, remote_path: str, content: str, timeout: int) -> Dict[str, Any]:
    tmp_path = None
    try:
        normalized = str(content or "").replace("\r\n", "\n").replace("\r", "\n")
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            encoding="utf-8",
            newline="\n",
            suffix=".py",
        ) as tmp:
            tmp.write(normalized)
            tmp_path = tmp.name
        return cli.run_push_repl(
            port,
            baud,
            tmp_path,
            parent_remote_dir(remote_path),
            remote_file_name(remote_path),
            timeout=max(15, timeout),
        )
    finally:
        if tmp_path:
            try:
                pathlib.Path(tmp_path).unlink()
            except Exception:
                pass


def main() -> int:
    args = build_parser().parse_args()
    profile_registry_path = pathlib.Path(args.profiles).resolve()
    data = load_profiles(profile_registry_path)
    profiles = data.get("profiles") or {}
    profile = profiles.get(args.profile)
    if not isinstance(profile, dict):
        raise SystemExit("Unknown profile: %s" % args.profile)

    remote_path = normalize_remote_path(args.remote_path)
    values = resolve_values(args.profile, profile, args)
    content = render_config_local(args.profile, profile, values)
    timeout = max(12, int(args.timeout))

    summary: Dict[str, Any] = {
        "profiles": str(profile_registry_path),
        "profile": args.profile,
        "version": int(data.get("version") or 1),
        "device_id": values["device_id"],
        "device_name": values["device_name"],
        "device_model_hint": values["device_model_hint"],
        "board_profile": values["board_profile"],
        "tenant_id": values["tenant_id"],
        "ws_url": values["ws_url"],
        "auth_token_masked": mask_secret(values["auth_token"]),
        "device_auth_mode": values["device_auth_mode"],
        "remote_signer_url": values["remote_signer_url"] if values["device_auth_mode"] == "remote_signer_http" else "",
        "remote_signer_auth_token_masked": (
            mask_secret(values["remote_signer_auth_token"])
            if values["device_auth_mode"] == "remote_signer_http"
            else ""
        ),
        "out": "",
        "push": {
            "requested": bool(args.push),
            "remote_path": remote_path,
            "legacy_remote_path": LEGACY_CONFIG_REMOTE_PATH,
            "force": bool(args.force),
            "attempted": False,
            "skipped_existing": False,
            "skipped_legacy_existing": False,
            "legacy_exists": False,
            "ok": None,
        },
        "ok": True,
    }

    if args.out:
        out_path = pathlib.Path(args.out).resolve()
        write_local_output(out_path, content)
        summary["out"] = str(out_path)

    if args.push:
        cli = load_qpy_fs_cli()
        exists = remote_file_exists(cli, args.port, int(args.baud), remote_path, timeout)
        legacy_exists = False
        if remote_path != LEGACY_CONFIG_REMOTE_PATH:
            legacy_exists = remote_file_exists(
                cli,
                args.port,
                int(args.baud),
                LEGACY_CONFIG_REMOTE_PATH,
                timeout,
            )
        summary["push"]["legacy_exists"] = bool(legacy_exists)
        if exists and not args.force:
            summary["push"]["skipped_existing"] = True
            summary["push"]["ok"] = True
        elif legacy_exists and not args.force:
            summary["push"]["skipped_legacy_existing"] = True
            summary["push"]["ok"] = True
        else:
            result = push_remote_content(
                cli,
                args.port,
                int(args.baud),
                remote_path,
                content,
                timeout,
            )
            summary["push"]["attempted"] = True
            summary["push"]["ok"] = bool(result.get("ok"))
            summary["push"]["remote_size"] = result.get("remote_size")
            summary["push"]["local_size"] = result.get("local_size")
            summary["push"]["diagnostics"] = result.get("diagnostics", [])
            if not summary["push"]["ok"]:
                summary["ok"] = False
                summary["push"]["raw"] = result.get("raw", "")

    if args.show_content:
        summary["content"] = content

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("profile:", summary["profile"])
        print("device_id:", summary["device_id"])
        print("board_profile:", summary["board_profile"])
        if summary["out"]:
            print("wrote:", summary["out"])
        if args.push:
            if summary["push"]["skipped_existing"]:
                print("push: skipped existing %s" % remote_path)
            elif summary["push"]["skipped_legacy_existing"]:
                print(
                    "push: skipped because legacy config still exists at %s"
                    % LEGACY_CONFIG_REMOTE_PATH
                )
            else:
                print("push: %s -> %s" % ("OK" if summary["push"]["ok"] else "FAIL", remote_path))
        if args.show_content:
            print("")
            print(content)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
