#!/usr/bin/env python3
"""
Synchronize a local runtime source tree to a QuecPython device /usr path.

This is intended for post-flash recovery, where the module file system is
reset and the qpyclaw runtime needs to be restored quickly.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any, Dict, List

DEFAULT_LOCAL_ROOT = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\embed"
    r"\qpyclaw-node\code"
)
DEFAULT_MANIFEST = pathlib.Path(
    r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\embed"
    r"\qpyclaw-node\deploy\runtime-manifest.json"
)
REMOTE_DRIVE_ROOT_RE = re.compile(r"^[A-Za-z]:(?:$|/.*)")


def load_qpy_fs_cli():
    skill_scripts = pathlib.Path(
        r"C:\Users\kingd\.codex\skills\quecpython-dev\scripts"
    )
    sys.path.insert(0, str(skill_scripts))
    import qpy_device_fs_cli as cli  # type: ignore

    return cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync a local qpyclaw runtime source tree to a QuecPython device."
    )
    parser.add_argument("--port", default="COM14", help="REPL port.")
    parser.add_argument("--baud", type=int, default=115200, help="REPL baudrate.")
    parser.add_argument(
        "--local-root",
        default="",
        help="Local runtime source root. Defaults to manifest local_root_rel or the canonical code directory.",
    )
    parser.add_argument(
        "--remote-root",
        default="",
        help="Remote root directory. Defaults to manifest remote_root or /usr.",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="Runtime deploy manifest path.",
    )
    parser.add_argument(
        "--ignore-manifest",
        action="store_true",
        help="Ignore manifest and sync the whole local tree rooted at --local-root.",
    )
    parser.add_argument(
        "--skip-remove",
        action="store_true",
        help="Skip manifest-declared stale-file cleanup on the device.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the sync plan without touching the device.",
    )
    parser.add_argument("--timeout", type=int, default=40, help="Per-operation timeout seconds.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser


def normalize_rel_path(value: str) -> str:
    text = str(value or "").replace("\\", "/").strip()
    if not text:
        raise ValueError("empty relative path")
    parts = []
    for item in text.split("/"):
        if item in {"", "."}:
            continue
        if item == "..":
            raise ValueError("parent traversal not allowed: %s" % value)
        parts.append(item)
    if not parts:
        raise ValueError("empty relative path")
    return "/".join(parts)


def normalize_remote_root(value: str) -> str:
    text = str(value or "/usr").replace("\\", "/").strip()
    if not text:
        text = "/usr"
    if REMOTE_DRIVE_ROOT_RE.match(text):
        if len(text) > 3 and text.endswith("/"):
            text = text[:-1]
        return text
    if not text.startswith("/"):
        text = "/" + text
    while "//" in text:
        text = text.replace("//", "/")
    if len(text) > 1 and text.endswith("/"):
        text = text[:-1]
    return text


def join_remote_path(remote_root: str, rel_path: str) -> str:
    rel = str(rel_path or "").replace("\\", "/").strip("/")
    if not rel:
        return remote_root
    if remote_root == "/":
        return "/" + rel
    return remote_root + "/" + rel


def local_from_rel(local_root: pathlib.Path, rel_path: str) -> pathlib.Path:
    rel = normalize_rel_path(rel_path)
    return local_root.joinpath(*rel.split("/"))


def load_manifest(path: pathlib.Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit("Failed to load manifest %s: %s" % (path, e))
    if not isinstance(data, dict):
        raise SystemExit("Manifest must be a JSON object: %s" % path)
    return data


def resolve_local_root(arg_value: str, manifest_path: pathlib.Path, manifest: Dict[str, Any]) -> pathlib.Path:
    if str(arg_value or "").strip():
        return pathlib.Path(arg_value).resolve()
    local_root_rel = str(manifest.get("local_root_rel") or "").strip()
    if local_root_rel:
        return (manifest_path.parent / local_root_rel).resolve()
    return DEFAULT_LOCAL_ROOT.resolve()


def resolve_source_root(
    manifest_path: pathlib.Path,
    default_local_root: pathlib.Path,
    raw_entry: Dict[str, Any],
) -> pathlib.Path:
    source_root_rel = str(raw_entry.get("source_root_rel") or "").strip()
    if source_root_rel:
        return (manifest_path.parent / source_root_rel).resolve()
    return default_local_root


def parse_manifest_file_entry(
    manifest_path: pathlib.Path,
    default_local_root: pathlib.Path,
    raw_entry: Any,
) -> tuple[str, pathlib.Path]:
    if isinstance(raw_entry, str):
        rel_path = normalize_rel_path(raw_entry)
        return rel_path, local_from_rel(default_local_root, rel_path)
    if not isinstance(raw_entry, dict):
        raise SystemExit("Manifest files entries must be strings or objects: %s" % manifest_path)
    rel_path = normalize_rel_path(str(raw_entry.get("path") or raw_entry.get("target") or ""))
    source_path = normalize_rel_path(str(raw_entry.get("source_path") or raw_entry.get("source") or rel_path))
    source_root = resolve_source_root(manifest_path, default_local_root, raw_entry)
    return rel_path, local_from_rel(source_root, source_path)


def resolve_remote_root(arg_value: str, manifest: Dict[str, Any]) -> str:
    if str(arg_value or "").strip():
        return normalize_remote_root(arg_value)
    return normalize_remote_root(str(manifest.get("remote_root") or "/usr"))


def build_manifest_plan(
    manifest_path: pathlib.Path,
    manifest: Dict[str, Any],
    local_root: pathlib.Path,
    remote_root: str,
    skip_remove: bool,
) -> Dict[str, Any]:
    raw_files = manifest.get("files") or []
    if not isinstance(raw_files, list) or not raw_files:
        raise SystemExit("Manifest files list is required: %s" % manifest_path)

    rel_files: List[str] = []
    local_files: List[pathlib.Path] = []
    dir_set = {""}
    for raw in raw_files:
        rel, src = parse_manifest_file_entry(manifest_path, local_root, raw)
        if not src.is_file():
            raise SystemExit("Manifest file missing under local root: %s" % src)
        rel_files.append(rel)
        local_files.append(src)
        parent = pathlib.PurePosixPath(rel).parent.as_posix()
        if parent == ".":
            parent = ""
        while parent not in {"", "."}:
            dir_set.add(parent)
            next_parent = pathlib.PurePosixPath(parent).parent.as_posix()
            parent = "" if next_parent == "." else next_parent

    raw_remove = [] if skip_remove else (manifest.get("remove_remote_files") or [])
    rel_remove: List[str] = []
    for raw in raw_remove:
        rel_remove.append(normalize_rel_path(raw))

    raw_preserve = manifest.get("preserve_remote_files") or []
    rel_preserve: List[str] = []
    for raw in raw_preserve:
        rel_preserve.append(normalize_rel_path(raw))

    directories = sorted(dir_set)
    return {
        "mode": "manifest",
        "manifest_path": str(manifest_path),
        "manifest_name": str(manifest.get("name") or ""),
        "manifest_version": int(manifest.get("version") or 1),
        "local_root": local_root,
        "remote_root": remote_root,
        "rel_files": rel_files,
        "local_files": local_files,
        "directories": directories,
        "remove_rel": rel_remove,
        "preserve_rel": rel_preserve,
    }


def build_full_tree_plan(local_root: pathlib.Path, remote_root: str) -> Dict[str, Any]:
    directories: List[str] = [""]
    rel_files: List[str] = []
    local_files: List[pathlib.Path] = []
    for path in sorted(local_root.rglob("*")):
        rel = path.relative_to(local_root).as_posix()
        if path.is_dir():
            directories.append(rel)
        elif path.is_file():
            rel_files.append(rel)
            local_files.append(path)
    return {
        "mode": "full-tree",
        "manifest_path": "",
        "manifest_name": "",
        "manifest_version": 0,
        "local_root": local_root,
        "remote_root": remote_root,
        "rel_files": rel_files,
        "local_files": local_files,
        "directories": sorted(set(directories)),
        "remove_rel": [],
        "preserve_rel": [],
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


def is_no_space_push_failure(result: Dict[str, Any]) -> bool:
    raw = str(result.get("raw", "") or "")
    diagnostics = result.get("diagnostics", []) or []
    if "OSError: 28" in raw:
        return True
    for item in diagnostics:
        if "OSError: 28" in str(item):
            return True
    return False


def is_memory_push_failure(result: Dict[str, Any]) -> bool:
    raw = str(result.get("raw", "") or "")
    diagnostics = result.get("diagnostics", []) or []
    if "MemoryError" in raw:
        return True
    for item in diagnostics:
        if "MemoryError" in str(item):
            return True
    return False


def is_effective_push_success(result: Dict[str, Any]) -> bool:
    try:
        local_size = int(result.get("local_size"))
        bytes_written = int(result.get("bytes_written"))
        remote_size = int(result.get("remote_size"))
    except Exception:
        return False
    if local_size < 0:
        return False
    return bytes_written == local_size and remote_size == local_size


def should_stream_push(src: pathlib.Path) -> bool:
    try:
        return int(src.stat().st_size) > 49152
    except Exception:
        return False


def _stream_init_push(cli, port: str, baud: int, remote_dir: str, tmp_path: str, timeout: int) -> Dict[str, Any]:
    remote_dir_qpy = cli.single_quote_qpy(remote_dir)
    tmp_path_qpy = cli.single_quote_qpy(tmp_path)
    lines = [
        "import ql_fs,uos",
        "_code=\"def _qinit(dir_path,tmp_path):\\n ql_fs.mkdirs(dir_path)\\n try:\\n  uos.remove(tmp_path)\\n except Exception:\\n  pass\\n return True\\n\"",
        "exec(_code)",
        "_ret=_qinit('%s','%s')" % (remote_dir_qpy, tmp_path_qpy),
        "print('stream_init_ok')",
    ]
    raw = cli.repl_send_lines(
        port,
        baud,
        lines,
        timeout=max(12, timeout),
        line_delay_ms=12,
        settle_ms=260,
    )
    has_error = any(x in raw for x in ["ERR:", "Traceback", "ParserError", "At line:"])
    return {"ok": ("stream_init_ok" in raw or "True" in raw) and (not has_error), "raw": raw}


def _stream_append_push(
    cli,
    port: str,
    baud: int,
    tmp_path: str,
    hex_batch: List[str],
    expected_bytes: int,
    timeout: int,
) -> Dict[str, Any]:
    tmp_path_qpy = cli.single_quote_qpy(tmp_path)
    lines = [
        "import ubinascii",
        "_code=\"def _qappend(path,items):\\n f=open(path,'ab')\\n w=0\\n for h in items:\\n  w += f.write(ubinascii.unhexlify(h))\\n f.close()\\n return w\\n\"",
        "exec(_code)",
        "_items=[]",
    ]
    for hx in hex_batch:
        lines.append("_items.append('%s')" % hx)
    lines.extend([
        "_w=_qappend('%s',_items)" % tmp_path_qpy,
        "print('stream_append_ok %d' % _w)",
    ])
    raw = cli.repl_send_lines(
        port,
        baud,
        lines,
        timeout=max(12, timeout),
        line_delay_ms=10,
        settle_ms=220,
    )
    matches = re.findall(r"stream_append_ok\s+(\d+)", raw or "")
    written = int(matches[-1]) if matches else -1
    has_error = any(x in raw for x in ["ERR:", "Traceback", "ParserError", "At line:"])
    return {
        "ok": (written == expected_bytes) and (not has_error),
        "raw": raw,
        "bytes_written": written,
    }


def _stream_finish_push(
    cli,
    port: str,
    baud: int,
    remote_dir: str,
    remote_path: str,
    tmp_path: str,
    remote_name: str,
    timeout: int,
) -> Dict[str, Any]:
    remote_dir_qpy = cli.single_quote_qpy(remote_dir)
    remote_path_qpy = cli.single_quote_qpy(remote_path)
    tmp_path_qpy = cli.single_quote_qpy(tmp_path)
    remote_name_qpy = cli.single_quote_qpy(remote_name)
    lines = [
        "import uos",
        "_code=\"def _qfinish(path,tmp_path,dir_path,file_name):\\n entries=uos.listdir(dir_path)\\n if file_name in entries:\\n  uos.remove(path)\\n uos.rename(tmp_path,path)\\n return uos.stat(path)[6]\\n\"",
        "exec(_code)",
        "_s=_qfinish('%s','%s','%s','%s')" % (
            remote_path_qpy,
            tmp_path_qpy,
            remote_dir_qpy,
            remote_name_qpy,
        ),
        "print('stream_finish_ok %d' % _s)",
    ]
    raw = cli.repl_send_lines(
        port,
        baud,
        lines,
        timeout=max(12, timeout),
        line_delay_ms=12,
        settle_ms=240,
    )
    matches = re.findall(r"stream_finish_ok\s+(\d+)", raw or "")
    remote_size = int(matches[-1]) if matches else -1
    has_error = any(x in raw for x in ["ERR:", "Traceback", "ParserError", "At line:"])
    return {"ok": (remote_size >= 0) and (not has_error), "raw": raw, "remote_size": remote_size}


def _read_remote_size(cli, port: str, baud: int, path: str, timeout: int) -> int:
    pure_path = pathlib.PurePosixPath(str(path or "").replace("\\", "/"))
    parent = pure_path.parent.as_posix() or "/"
    name = pure_path.name
    if not name:
        return -1
    result = cli.run_ls_repl(
        port,
        baud,
        parent,
        timeout=max(12, timeout),
    )
    if not result.get("ok"):
        return -1
    for row in result.get("rows") or []:
        if row.get("name") != name or row.get("type") != "file":
            continue
        try:
            return int(row.get("size"))
        except Exception:
            return -1
    return -1


def run_stream_push_repl(
    cli,
    port: str,
    baud: int,
    src: pathlib.Path,
    remote_dir: str,
    remote_name: str,
    timeout: int,
    chunk_size: int = 512,
    batch_chunks: int = 32,
) -> Dict[str, Any]:
    data = src.read_bytes()
    remote_path = join_remote_path(remote_dir, remote_name)
    tmp_path = remote_path + ".tmp"
    offset = _read_remote_size(cli, port, baud, tmp_path, timeout)
    if offset < 0 or offset > len(data) or (offset % int(chunk_size)) != 0:
        init_result = _stream_init_push(cli, port, baud, remote_dir, tmp_path, timeout)
        if not init_result.get("ok"):
            return {
                "ok": False,
                "raw": init_result.get("raw", ""),
                "local_size": len(data),
                "bytes_written": 0,
                "remote_size": -1,
                "remote_path": remote_path,
                "chunks": len(cli.chunk_hex(data, chunk_size=chunk_size)),
                "backend": "repl_stream",
                "diagnostics": ["STREAM_INIT_FAILED"],
            }
        offset = 0

    chunks = cli.chunk_hex(data[offset:], chunk_size=chunk_size)
    total_written = offset
    index = 0
    while index < len(chunks):
        batch = chunks[index : index + batch_chunks]
        expected_bytes = 0
        for hx in batch:
            expected_bytes += len(bytes.fromhex(hx))
        expected_total = total_written + expected_bytes
        append_result = _stream_append_push(
            cli,
            port,
            baud,
            tmp_path,
            batch,
            expected_bytes,
            timeout=max(12, timeout),
        )
        if not append_result.get("ok"):
            remote_size_after = _read_remote_size(
                cli,
                port,
                baud,
                tmp_path,
                timeout=max(12, timeout),
            )
            if remote_size_after == expected_total:
                total_written = expected_total
                index += batch_chunks
                continue
            retry_result = _stream_append_push(
                cli,
                port,
                baud,
                tmp_path,
                batch,
                expected_bytes,
                timeout=max(12, timeout),
            )
            if not retry_result.get("ok"):
                remote_size_retry = _read_remote_size(
                    cli,
                    port,
                    baud,
                    tmp_path,
                    timeout=max(12, timeout),
                )
                if remote_size_retry == expected_total:
                    total_written = expected_total
                    index += batch_chunks
                    continue
                diagnostics = ["STREAM_APPEND_FAILED", "STREAM_APPEND_RETRY_FAILED"]
                diagnostics.append("TMP_SIZE_AFTER=%d" % int(remote_size_after))
                diagnostics.append("TMP_SIZE_RETRY=%d" % int(remote_size_retry))
                return {
                    "ok": False,
                    "raw": retry_result.get("raw", "") or append_result.get("raw", ""),
                    "local_size": len(data),
                    "bytes_written": total_written + int(retry_result.get("bytes_written", 0) or 0),
                    "remote_size": int(remote_size_retry),
                    "remote_path": remote_path,
                    "chunks": len(chunks),
                    "backend": "repl_stream",
                    "diagnostics": diagnostics,
                }
            append_result = retry_result
        total_written += expected_bytes
        index += batch_chunks

    finish_result = _stream_finish_push(
        cli,
        port,
        baud,
        remote_dir,
        remote_path,
        tmp_path,
        remote_name,
        timeout=max(12, timeout),
    )
    final_remote_size = int(finish_result.get("remote_size", -1))
    diagnostics: List[str] = []
    if final_remote_size != len(data):
        stat_remote_size = _read_remote_size(
            cli,
            port,
            baud,
            remote_path,
            timeout=max(12, timeout),
        )
        if stat_remote_size >= 0:
            final_remote_size = int(stat_remote_size)
    if (not bool(finish_result.get("ok"))) and final_remote_size == len(data):
        diagnostics.append("STREAM_FINISH_CONFIRMED_BY_STAT")
    return {
        "ok": total_written == len(data) and final_remote_size == len(data),
        "raw": finish_result.get("raw", ""),
        "local_size": len(data),
        "bytes_written": total_written,
        "remote_size": int(final_remote_size),
        "remote_path": remote_path,
        "chunks": len(chunks),
        "backend": "repl_stream",
        "diagnostics": diagnostics,
    }


def main() -> int:
    args = build_parser().parse_args()
    cli = load_qpy_fs_cli()

    timeout = max(12, int(args.timeout))
    manifest_path = pathlib.Path(args.manifest).resolve()
    use_manifest = (not bool(args.ignore_manifest)) and manifest_path.is_file()
    manifest: Dict[str, Any] = {}
    if use_manifest:
        manifest = load_manifest(manifest_path)

    if use_manifest:
        local_root = resolve_local_root(args.local_root, manifest_path, manifest)
        remote_root = resolve_remote_root(args.remote_root, manifest)
        plan = build_manifest_plan(
            manifest_path,
            manifest,
            local_root,
            remote_root,
            bool(args.skip_remove),
        )
    else:
        local_root = pathlib.Path(args.local_root or LEGACY_LOCAL_ROOT).resolve()
        remote_root = normalize_remote_root(args.remote_root or "/usr")
        plan = build_full_tree_plan(local_root, remote_root)

    if not local_root.is_dir():
        raise SystemExit("Local root is not a directory: %s" % local_root)

    summary: Dict[str, Any] = {
        "mode": plan["mode"],
        "manifest": plan["manifest_path"],
        "manifest_name": plan["manifest_name"],
        "manifest_version": plan["manifest_version"],
        "local_root": str(local_root),
        "remote_root": remote_root,
        "port": args.port,
        "baud": int(args.baud),
        "dry_run": bool(args.dry_run),
        "preserve_remote_files": plan["preserve_rel"],
        "planned_directories": [join_remote_path(remote_root, rel) for rel in plan["directories"]],
        "planned_files": [
            {
                "local_file": str(src),
                "remote_path": join_remote_path(remote_root, rel),
            }
            for rel, src in zip(plan["rel_files"], plan["local_files"])
        ],
        "planned_remove": [join_remote_path(remote_root, rel) for rel in plan["remove_rel"]],
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
                "dry-run ok: %d dirs, %d files, %d removals (%s)"
                % (
                    len(summary["planned_directories"]),
                    len(summary["planned_files"]),
                    len(summary["planned_remove"]),
                    summary["mode"],
                )
            )
        return 0

    for rel in plan["directories"]:
        remote_dir = join_remote_path(remote_root, rel)
        result = cli.run_repl_op(
            args.port,
            int(args.baud),
            [
                "import ql_fs",
                "ql_fs.mkdirs('%s')" % cli.single_quote_qpy(remote_dir),
                "print('mkdir_ok')",
            ],
            success_token="mkdir_ok",
            timeout=timeout,
        )
        row = {"remote_dir": remote_dir, "ok": bool(result.get("ok")), "raw": result.get("raw", "")}
        summary["mkdir"].append(row)
        if not row["ok"]:
            summary["ok"] = False
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                print("mkdir failed:", remote_dir)
                print(row["raw"])
            return 1

    for rel in plan["remove_rel"]:
        remote_path = join_remote_path(remote_root, rel)
        result = safe_remove_remote_file(
            cli,
            args.port,
            int(args.baud),
            remote_path,
            timeout=timeout,
        )
        row = {"remote_path": remote_path, "ok": bool(result.get("ok")), "raw": result.get("raw", "")}
        summary["remove"].append(row)
        if not row["ok"]:
            summary["ok"] = False
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                print("remove failed:", remote_path)
                print(row["raw"])
            return 1

    for rel, src in zip(plan["rel_files"], plan["local_files"]):
        rel_parent = pathlib.PurePosixPath(rel).parent.as_posix()
        if rel_parent == ".":
            rel_parent = ""
        remote_dir = join_remote_path(remote_root, rel_parent)
        remote_name = pathlib.PurePosixPath(rel).name
        remote_path = join_remote_path(remote_dir, remote_name)
        try:
            local_size = int(src.stat().st_size)
        except Exception:
            local_size = -1
        remote_size_before = _read_remote_size(
            cli,
            args.port,
            int(args.baud),
            remote_path,
            timeout=timeout,
        )
        if local_size >= 0 and remote_size_before == local_size:
            summary["push"].append(
                {
                    "local_file": str(src),
                    "remote_dir": remote_dir,
                    "remote_path": remote_path,
                    "remote_name": remote_name,
                    "ok": True,
                    "remote_size": int(remote_size_before),
                    "local_size": int(local_size),
                    "diagnostics": ["SKIPPED_SAME_SIZE"],
                    "raw": "",
                    "retried_after_no_space": False,
                    "deleted_existing_before_retry": False,
                    "delete_existing_raw": "",
                }
            )
            continue
        if should_stream_push(src):
            result = run_stream_push_repl(
                cli,
                args.port,
                int(args.baud),
                src,
                remote_dir,
                remote_name,
                timeout=timeout,
            )
        else:
            result = cli.run_push_repl(
                args.port,
                int(args.baud),
                str(src),
                remote_dir,
                remote_name,
                timeout=timeout,
            )
        retry_delete_old = False
        retry_delete_raw = ""
        retried = False
        if (not bool(result.get("ok"))) and is_memory_push_failure(result):
            retried = True
            result = run_stream_push_repl(
                cli,
                args.port,
                int(args.baud),
                src,
                remote_dir,
                remote_name,
                timeout=timeout,
            )
        if (not bool(result.get("ok"))) and is_no_space_push_failure(result):
            retry_delete_old = True
            delete_result = safe_remove_remote_file(
                cli,
                args.port,
                int(args.baud),
                remote_path,
                timeout=timeout,
            )
            retry_delete_raw = delete_result.get("raw", "")
            if bool(delete_result.get("ok")):
                retried = True
                result = cli.run_push_repl(
                    args.port,
                    int(args.baud),
                    str(src),
                    remote_dir,
                    remote_name,
                    timeout=timeout,
                )
        effective_ok = bool(result.get("ok")) or is_effective_push_success(result)
        diagnostics = list(result.get("diagnostics", []) or [])
        if effective_ok and (not bool(result.get("ok"))):
            diagnostics.append("EFFECTIVE_SUCCESS_DESPITE_STALE_ERROR_OUTPUT")
        row = {
            "local_file": str(src),
            "remote_dir": remote_dir,
            "remote_path": remote_path,
            "remote_name": remote_name,
            "ok": effective_ok,
            "remote_size": result.get("remote_size"),
            "local_size": result.get("local_size"),
            "diagnostics": diagnostics,
            "raw": result.get("raw", ""),
            "retried_after_no_space": bool(retried),
            "deleted_existing_before_retry": bool(retry_delete_old),
            "delete_existing_raw": retry_delete_raw,
        }
        summary["push"].append(row)
        if not row["ok"]:
            summary["ok"] = False
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                print("push failed:", src)
                print(row["raw"])
            return 1

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(
            "sync ok: %d dirs, %d files, %d removals -> %s (%s)"
            % (
                len(summary["mkdir"]),
                len(summary["push"]),
                len(summary["remove"]),
                remote_root,
                summary["mode"],
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
