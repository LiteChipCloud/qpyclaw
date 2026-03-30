#!/usr/bin/env python3
"""
Synchronize board UI media assets to a QuecPython device media partition.

This script exists because the generic /usr sync flow normalizes device paths
to Unix-style roots, while EC800MCNLE emoji assets live under U:/media.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any, Dict, List

HOST_DIR = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host"
)
DEFAULT_BOARD_MANIFEST_DIR = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\embed"
    r"\qpyclaw-node\deploy\board-manifests"
)


def load_qpy_fs_cli():
    skill_scripts = pathlib.Path(
        r"C:\Users\kingd\.codex\skills\quecpython-dev\scripts"
    )
    sys.path.insert(0, str(skill_scripts))
    import qpy_device_fs_cli as cli  # type: ignore

    return cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync qpyclaw board media assets to U:/media or another device media root."
    )
    parser.add_argument("--profile", required=True, help="Board profile key.")
    parser.add_argument("--manifest", default="", help="Board media manifest path override.")
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument("--timeout", type=int, default=40, help="Per-operation timeout seconds.")
    parser.add_argument("--skip-remove", action="store_true", help="Skip manifest remove list handling.")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync only.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def resolve_manifest(profile: str, override: str) -> pathlib.Path:
    text = str(override or "").strip()
    if text:
        path = pathlib.Path(text).resolve()
    else:
        path = (DEFAULT_BOARD_MANIFEST_DIR / (str(profile).strip() + "-media.json")).resolve()
    if not path.is_file():
        raise SystemExit("Board media manifest not found: %s" % path)
    return path


def load_manifest(path: pathlib.Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit("Failed to load manifest %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise SystemExit("Manifest must be a JSON object: %s" % path)
    return data


def normalize_rel_path(value: str) -> str:
    text = str(value or "").replace("\\", "/").strip()
    if not text:
        raise ValueError("empty relative path")
    parts: List[str] = []
    for item in text.split("/"):
        if item in {"", "."}:
            continue
        if item == "..":
            raise ValueError("parent traversal not allowed: %s" % value)
        parts.append(item)
    if not parts:
        raise ValueError("empty relative path")
    return "/".join(parts)


def is_drive_root_path(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:($|/)", str(value or "")))


def normalize_remote_root(value: str) -> str:
    text = str(value or "").replace("\\", "/").strip()
    if not text:
        raise ValueError("empty remote root")
    text = re.sub(r"/{2,}", "/", text)
    if is_drive_root_path(text):
        if len(text) == 2:
            return text + "/"
        return text.rstrip("/") or (text[:2] + "/")
    if not text.startswith("/"):
        text = "/" + text
    if len(text) > 1 and text.endswith("/"):
        text = text[:-1]
    return text


def join_remote_path(remote_root: str, rel_path: str) -> str:
    rel = str(rel_path or "").replace("\\", "/").strip("/")
    base = normalize_remote_root(remote_root)
    if not rel:
        return base
    if is_drive_root_path(base):
        return base.rstrip("/") + "/" + rel
    if base == "/":
        return "/" + rel
    return base + "/" + rel


def resolve_local_root(manifest_path: pathlib.Path, manifest: Dict[str, Any]) -> pathlib.Path:
    local_root_rel = str(manifest.get("local_root_rel") or "").strip()
    if not local_root_rel:
        raise SystemExit("Manifest local_root_rel is required: %s" % manifest_path)
    local_root = (manifest_path.parent / local_root_rel).resolve()
    if not local_root.is_dir():
        raise SystemExit("Local root is not a directory: %s" % local_root)
    return local_root


def build_plan(
    manifest_path: pathlib.Path,
    manifest: Dict[str, Any],
    skip_remove: bool,
) -> Dict[str, Any]:
    local_root = resolve_local_root(manifest_path, manifest)
    remote_root = normalize_remote_root(str(manifest.get("remote_root") or ""))
    raw_files = manifest.get("files") or []
    if not isinstance(raw_files, list) or not raw_files:
        raise SystemExit("Manifest files list is required: %s" % manifest_path)

    rel_files: List[str] = []
    local_files: List[pathlib.Path] = []
    dir_set = {""}
    for raw in raw_files:
        rel = normalize_rel_path(str(raw))
        src = local_root.joinpath(*rel.split("/"))
        if not src.is_file():
            raise SystemExit("Manifest file missing under local root: %s" % src)
        rel_files.append(rel)
        local_files.append(src)
        parent = pathlib.PurePosixPath(rel).parent.as_posix()
        parent = "" if parent == "." else parent
        while parent not in {"", "."}:
            dir_set.add(parent)
            next_parent = pathlib.PurePosixPath(parent).parent.as_posix()
            parent = "" if next_parent == "." else next_parent

    remove_rel: List[str] = []
    if not skip_remove:
        for raw in manifest.get("remove_remote_files") or []:
            remove_rel.append(normalize_rel_path(str(raw)))

    return {
        "manifest_path": str(manifest_path),
        "manifest_name": str(manifest.get("name") or ""),
        "manifest_version": int(manifest.get("version") or 1),
        "local_root": local_root,
        "remote_root": remote_root,
        "rel_files": rel_files,
        "local_files": local_files,
        "directories": sorted(dir_set),
        "remove_rel": remove_rel,
    }


def safe_remove_remote_file(cli, port: str, baud: int, remote_path: str, timeout: int) -> Dict[str, Any]:
    result = cli.run_repl_op(
        port,
        baud,
        [
            "import uos",
            "_code=\"def _qrm(p):\\n try:\\n  uos.remove(p)\\n except Exception:\\n  pass\\n\"",
            "exec(_code)",
            "_qrm('%s')" % cli.single_quote_qpy(remote_path),
            "print('rm_ok')",
        ],
        success_token="rm_ok",
        timeout=timeout,
    )
    return result


def run_mkdir(cli, port: str, baud: int, remote_dir: str, timeout: int) -> Dict[str, Any]:
    return cli.run_repl_op(
        port,
        baud,
        [
            "import ql_fs",
            "ql_fs.mkdirs('%s')" % cli.single_quote_qpy(remote_dir),
            "print('mkdir_ok')",
        ],
        success_token="mkdir_ok",
        timeout=timeout,
    )


def run_push_repl_flex(
    cli,
    port: str,
    baud: int,
    src: pathlib.Path,
    remote_dir: str,
    remote_name: str,
    timeout: int,
) -> Dict[str, Any]:
    data = src.read_bytes()
    chunks = cli.chunk_hex(data, chunk_size=96)
    remote_path = join_remote_path(remote_dir, remote_name)
    remote_dir_qpy = cli.single_quote_qpy(remote_dir)
    remote_path_qpy = cli.single_quote_qpy(remote_path)
    tmp_path_qpy = cli.single_quote_qpy(remote_path + ".tmp")
    remote_name_qpy = cli.single_quote_qpy(remote_name)
    tmp_name_qpy = cli.single_quote_qpy(remote_name + ".tmp")

    code = (
        "def _qpush(path,tmp_path,dir_path,file_name,tmp_name,chunks):\n"
        " ql_fs.mkdirs(dir_path)\n"
        " entries=uos.listdir(dir_path)\n"
        " if tmp_name in entries:\n"
        "  uos.remove(tmp_path)\n"
        " f=open(tmp_path,'wb')\n"
        " w=0\n"
        " for h in chunks:\n"
        "  w += f.write(ubinascii.unhexlify(h))\n"
        " f.close()\n"
        " entries=uos.listdir(dir_path)\n"
        " if file_name in entries:\n"
        "  uos.remove(path)\n"
        " uos.rename(tmp_path,path)\n"
        " s=uos.stat(path)[6]\n"
        " return (w,s)\n"
    )
    lines: List[str] = [
        "import ql_fs,uos,ubinascii",
        "_code=%r" % code,
        "exec(_code)",
        "_chunks=[]",
    ]
    for hx in chunks:
        lines.append("_chunks.append('%s')" % hx)
    lines.extend(
        [
            "_ret=_qpush('%s','%s','%s','%s','%s',_chunks)"
            % (
                remote_path_qpy,
                tmp_path_qpy,
                remote_dir_qpy,
                remote_name_qpy,
                tmp_name_qpy,
            ),
            "print('push_ok %d %d' % (_ret[0],_ret[1]))",
        ]
    )
    raw = cli.repl_send_lines(
        port,
        baud,
        lines,
        timeout=max(15, timeout),
        line_delay_ms=55,
        settle_ms=1800,
    )
    matches = re.findall(r"push_ok\s+(\d+)\s+(\d+)", raw or "")
    local_size = len(data)
    if matches:
        written = int(matches[-1][0])
        remote_size = int(matches[-1][1])
    else:
        written = -1
        remote_size = -1
    has_error = any(x in raw for x in ["ERR:", "Traceback", "ParserError", "At line:"])
    return {
        "ok": (written == local_size) and (remote_size == local_size) and (not has_error),
        "raw": raw,
        "local_size": local_size,
        "remote_size": remote_size,
        "bytes_written": written,
        "remote_path": remote_path,
        "chunks": len(chunks),
        "diagnostics": [],
    }


def main() -> int:
    args = build_parser().parse_args()
    cli = load_qpy_fs_cli()
    manifest_path = resolve_manifest(args.profile, args.manifest)
    manifest = load_manifest(manifest_path)
    plan = build_plan(manifest_path, manifest, bool(args.skip_remove))
    timeout = max(12, int(args.timeout))

    summary: Dict[str, Any] = {
        "flow": "qpy-board-media-sync",
        "profile": args.profile,
        "manifest": plan["manifest_path"],
        "manifest_name": plan["manifest_name"],
        "manifest_version": plan["manifest_version"],
        "local_root": str(plan["local_root"]),
        "remote_root": plan["remote_root"],
        "port": args.port,
        "baud": int(args.baud),
        "dry_run": bool(args.dry_run),
        "planned_directories": [join_remote_path(plan["remote_root"], rel) for rel in plan["directories"]],
        "planned_files": [
            {
                "local_file": str(src),
                "remote_path": join_remote_path(plan["remote_root"], rel),
            }
            for rel, src in zip(plan["rel_files"], plan["local_files"])
        ],
        "planned_remove": [join_remote_path(plan["remote_root"], rel) for rel in plan["remove_rel"]],
        "mkdir": [],
        "push": [],
        "remove": [],
        "ok": True,
    }

    if args.dry_run:
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print(
                "dry-run ok: %d dirs, %d files, %d removals -> %s"
                % (
                    len(summary["planned_directories"]),
                    len(summary["planned_files"]),
                    len(summary["planned_remove"]),
                    plan["remote_root"],
                )
            )
        return 0

    for rel in plan["directories"]:
        remote_dir = join_remote_path(plan["remote_root"], rel)
        result = run_mkdir(cli, args.port, int(args.baud), remote_dir, timeout)
        row = {"remote_dir": remote_dir, "ok": bool(result.get("ok")), "raw": result.get("raw", "")}
        summary["mkdir"].append(row)
        if not row["ok"]:
            summary["ok"] = False
            break

    if summary["ok"]:
        for rel in plan["remove_rel"]:
            remote_path = join_remote_path(plan["remote_root"], rel)
            result = safe_remove_remote_file(cli, args.port, int(args.baud), remote_path, timeout)
            row = {"remote_path": remote_path, "ok": bool(result.get("ok")), "raw": result.get("raw", "")}
            summary["remove"].append(row)
            if not row["ok"]:
                summary["ok"] = False
                break

    if summary["ok"]:
        for rel, src in zip(plan["rel_files"], plan["local_files"]):
            rel_parent = pathlib.PurePosixPath(rel).parent.as_posix()
            rel_parent = "" if rel_parent == "." else rel_parent
            remote_dir = join_remote_path(plan["remote_root"], rel_parent)
            result = run_push_repl_flex(
                cli,
                args.port,
                int(args.baud),
                src,
                remote_dir,
                src.name,
                timeout,
            )
            row = {
                "local_file": str(src),
                "remote_dir": remote_dir,
                "remote_path": result.get("remote_path"),
                "remote_name": src.name,
                "ok": bool(result.get("ok")),
                "remote_size": result.get("remote_size"),
                "local_size": result.get("local_size"),
                "diagnostics": result.get("diagnostics", []),
                "raw": result.get("raw", ""),
            }
            summary["push"].append(row)
            if not row["ok"]:
                summary["ok"] = False
                break

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("flow:", summary["flow"])
        print("profile:", summary["profile"])
        print("manifest:", summary["manifest"])
        print("remote_root:", summary["remote_root"])
        print("media_sync:", "OK" if summary["ok"] else "FAIL")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
