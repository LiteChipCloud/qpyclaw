#!/usr/bin/env python3
"""
Build a board-ready AIRI expression pack from opensource/media GIF assets.

The source-of-truth stays in opensource/media, while the output pack is
generated as RGB565 frames for LVGL animimg under /usr/media/expressions.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any, Dict, List


HOST_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = HOST_DIR.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent.parent
BOARD_TOOLS = PROJECT_ROOT / "embed" / "boards" / "u235-ec600u-airi-board" / "tools"
BUILD_PACK_SCRIPT = BOARD_TOOLS / "build_airi_expression_pack.py"
BOARD_MEDIA_MANIFEST = (
    PROJECT_ROOT
    / "embed"
    / "qpyclaw-node"
    / "deploy"
    / "board-manifests"
    / "u235-ec600u-airi-board-media.json"
)
DEFAULT_SRC_DIR = WORKSPACE_ROOT / "opensource" / "media"
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "embed"
    / "qpyclaw-node"
    / "deploy"
    / "generated"
    / "u235-ec600u-airi-board-expressions"
)
DEFAULT_SYNC_MANIFEST = DEFAULT_OUT_DIR / "sync-manifest.json"

sys.path.insert(0, str(BOARD_TOOLS))

from pillow_bootstrap import ensure_pillow_path

_PIL_CACHE = None


SOURCE_CONFIG = {
    "angry": {"tick_step": 2, "loop": False},
    "confident": {"tick_step": 2, "loop": False},
    "confused": {"tick_step": 3, "loop": True},
    "cool": {"tick_step": 2, "loop": False},
    "crying": {"tick_step": 3, "loop": False},
    "delicious": {"tick_step": 2, "loop": False},
    "embarrassed": {"tick_step": 2, "loop": False},
    "funny": {"tick_step": 2, "loop": True},
    "happy": {"tick_step": 2, "loop": False},
    "kissy": {"tick_step": 2, "loop": False},
    "laughing": {"tick_step": 2, "loop": True},
    "loving": {"tick_step": 2, "loop": False},
    "neutral": {"tick_step": 4, "loop": True},
    "relaxed": {"tick_step": 4, "loop": True},
    "sad": {"tick_step": 3, "loop": False},
    "silly": {"tick_step": 2, "loop": True},
    "sleep": {"tick_step": 4, "loop": True},
    "surprised": {"tick_step": 2, "loop": False},
    "thinking": {"tick_step": 3, "loop": True},
    "winking": {"tick_step": 2, "loop": False},
}


ALIAS_CONFIG = {
    "idle_blink": {"source": "neutral", "tick_step": 3, "loop": True},
    "listen_focus": {"source": "thinking", "tick_step": 2, "loop": True},
    "talk_smile": {"source": "happy", "tick_step": 1, "loop": True},
    "talk_open": {"source": "laughing", "tick_step": 1, "loop": True},
    "happy_pop": {"source": "happy", "tick_step": 2, "loop": True},
    "sad_soft": {"source": "sad", "tick_step": 3, "loop": False},
    "angry_fire": {"source": "angry", "tick_step": 2, "loop": False},
    "sleep_breath": {"source": "sleep", "tick_step": 4, "loop": True},
    "shock_hold": {"source": "surprised", "tick_step": 2, "loop": False},
    "wink_ping": {"source": "winking", "tick_step": 2, "loop": False},
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build LVGL animimg expressions from opensource/media GIF assets."
    )
    parser.add_argument("--src-dir", default=str(DEFAULT_SRC_DIR), help="Source GIF directory.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Generated expression pack directory.")
    parser.add_argument(
        "--board-media-manifest",
        default=str(BOARD_MEDIA_MANIFEST),
        help="Board media manifest rewritten to point at the generated pack.",
    )
    parser.add_argument(
        "--sync-manifest",
        default=str(DEFAULT_SYNC_MANIFEST),
        help="Standalone sync manifest written inside the generated pack.",
    )
    parser.add_argument("--width", type=int, default=176, help="Output frame width.")
    parser.add_argument("--height", type=int, default=176, help="Output frame height.")
    parser.add_argument("--zoom", type=int, default=320, help="Expression zoom stored in manifest.")
    parser.add_argument("--fit", choices=("contain", "cover", "stretch"), default="contain")
    parser.add_argument("--bg", default="#F5F8FF", help="Background color used for transparency.")
    parser.add_argument("--max-frames", type=int, default=10, help="Maximum sampled frames per expression.")
    parser.add_argument("--clean", action="store_true", help="Clear the output directory before generation.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    return parser


def resolve_dir(path_text: str, create: bool) -> pathlib.Path:
    path = pathlib.Path(str(path_text or "")).expanduser().resolve()
    if create:
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise SystemExit("Directory not found: %s" % path)
    return path


def resolve_file(path_text: str) -> pathlib.Path:
    return pathlib.Path(str(path_text or "")).expanduser().resolve()


def list_source_jobs(src_dir: pathlib.Path) -> List[Dict[str, Any]]:
    rows = []
    for key in sorted(SOURCE_CONFIG):
        path = src_dir / (key + ".gif")
        if not path.is_file():
            raise SystemExit("Missing source GIF: %s" % path)
        item = {"key": key, "path": path}
        item.update(SOURCE_CONFIG.get(key) or {})
        rows.append(item)
    return rows


def load_pillow():
    global _PIL_CACHE
    if _PIL_CACHE is not None:
        return _PIL_CACHE
    try:
        from PIL import Image, ImageSequence
    except Exception:
        ensure_pillow_path()
        try:
            from PIL import Image, ImageSequence
        except Exception as exc:
            raise SystemExit(
                "Pillow is required. Install it with: python -m pip install --user Pillow"
            ) from exc
    _PIL_CACHE = (Image, ImageSequence)
    return _PIL_CACHE


def count_frames(path: pathlib.Path) -> int:
    Image, ImageSequence = load_pillow()
    image = Image.open(path)
    try:
        count = 0
        for _frame in ImageSequence.Iterator(image):
            count += 1
        if count <= 0:
            return 1
        return count
    finally:
        try:
            image.close()
        except Exception:
            pass


def sample_step(frame_count: int, max_frames: int) -> int:
    limit = max(1, int(max_frames or 1))
    count = max(1, int(frame_count or 1))
    if count <= limit:
        return 1
    return int(math.ceil(float(count) / float(limit)))


def run_build_pack(
    src_path: pathlib.Path,
    out_dir: pathlib.Path,
    key: str,
    label: str,
    width: int,
    height: int,
    zoom: int,
    fit: str,
    background: str,
    tick_step: int,
    loop: bool,
    frame_step: int,
    max_frames: int,
) -> Dict[str, Any]:
    command = [
        sys.executable,
        str(BUILD_PACK_SCRIPT),
        "--src",
        str(src_path),
        "--out",
        str(out_dir),
        "--key",
        str(key),
        "--label",
        str(label),
        "--width",
        str(int(width)),
        "--height",
        str(int(height)),
        "--zoom",
        str(int(zoom)),
        "--tick-step",
        str(max(1, int(tick_step))),
        "--fit",
        str(fit),
        "--bg",
        str(background),
        "--frame-step",
        str(max(1, int(frame_step))),
        "--max-frames",
        str(max(1, int(max_frames))),
    ]
    if bool(loop):
        command.append("--loop")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "build_airi_expression_pack failed")
    return {
        "command": command,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }


def load_manifest(path: pathlib.Path) -> Dict[str, Any]:
    if not path.is_file():
        raise SystemExit("Generated manifest missing: %s" % path)
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: pathlib.Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def apply_aliases(manifest: Dict[str, Any]) -> Dict[str, Any]:
    expressions = manifest.setdefault("expressions", {})
    for alias_key in ALIAS_CONFIG:
        config = ALIAS_CONFIG[alias_key]
        source_key = config["source"]
        if source_key not in expressions:
            raise SystemExit("Alias source missing from manifest: %s -> %s" % (alias_key, source_key))
        entry = copy.deepcopy(expressions[source_key])
        entry["label"] = alias_key
        entry["tick_step"] = max(1, int(config["tick_step"]))
        entry["loop"] = bool(config["loop"])
        expressions[alias_key] = entry
    manifest["default"] = "idle_blink"
    manifest["source_root"] = "opensource/media"
    manifest["source_type"] = "gif"
    manifest["generated_by"] = "qpy_build_opensource_media_expression_pack.py"
    return manifest


def list_generated_files(root: pathlib.Path) -> List[str]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rows.append(path.relative_to(root).as_posix())
    return rows


def build_sync_manifest(out_dir: pathlib.Path, remote_root: str, files: List[str]) -> Dict[str, Any]:
    return {
        "version": 1,
        "name": "u235-ec600u-airi-board-media",
        "local_root_rel": ".",
        "remote_root": remote_root,
        "files": list(files),
        "preserve_remote_files": [],
        "remove_remote_files": [],
    }


def build_board_media_manifest(
    board_manifest_path: pathlib.Path,
    out_dir: pathlib.Path,
    remote_root: str,
    files: List[str],
) -> Dict[str, Any]:
    return {
        "version": 1,
        "name": "u235-ec600u-airi-board-media",
        "local_root_rel": pathlib.Path(os.path.relpath(str(out_dir), str(board_manifest_path.parent))).as_posix(),
        "remote_root": remote_root,
        "files": list(files),
        "preserve_remote_files": [],
        "remove_remote_files": [],
    }


def print_result(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("status:", result.get("status"))
    print("source_dir:", result.get("source_dir"))
    print("out_dir:", result.get("out_dir"))
    print("expressions:", result.get("expression_count"))
    print("generated_files:", result.get("generated_file_count"))
    print("board_media_manifest:", result.get("board_media_manifest"))


def main() -> None:
    args = build_parser().parse_args()
    src_dir = resolve_dir(args.src_dir, False)
    out_dir = resolve_file(args.out_dir)
    board_media_manifest_path = resolve_file(args.board_media_manifest)
    sync_manifest_path = resolve_file(args.sync_manifest)
    remote_root = "/usr/media/expressions"

    if not BUILD_PACK_SCRIPT.is_file():
        raise SystemExit("build_airi_expression_pack.py not found: %s" % BUILD_PACK_SCRIPT)

    if bool(args.clean) and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = list_source_jobs(src_dir)
    build_rows = []
    for job in jobs:
        frame_count = count_frames(job["path"])
        frame_step = sample_step(frame_count, int(args.max_frames))
        run_info = run_build_pack(
            src_path=job["path"],
            out_dir=out_dir,
            key=job["key"],
            label=job["key"],
            width=int(args.width),
            height=int(args.height),
            zoom=int(args.zoom),
            fit=str(args.fit),
            background=str(args.bg),
            tick_step=int(job["tick_step"]),
            loop=bool(job["loop"]),
            frame_step=frame_step,
            max_frames=int(args.max_frames),
        )
        build_rows.append(
            {
                "key": job["key"],
                "source": str(job["path"]),
                "source_frames": frame_count,
                "frame_step": frame_step,
                "stdout": run_info["stdout"],
            }
        )

    manifest_path = out_dir / "manifest.json"
    manifest = apply_aliases(load_manifest(manifest_path))
    save_json(manifest_path, manifest)

    generated_files = list_generated_files(out_dir)
    sync_manifest = build_sync_manifest(out_dir, remote_root, generated_files)
    save_json(sync_manifest_path, sync_manifest)

    board_media_manifest = build_board_media_manifest(
        board_media_manifest_path,
        out_dir,
        remote_root,
        generated_files,
    )
    save_json(board_media_manifest_path, board_media_manifest)

    result = {
        "status": "ok",
        "source_dir": str(src_dir),
        "out_dir": str(out_dir),
        "manifest": str(manifest_path),
        "sync_manifest": str(sync_manifest_path),
        "board_media_manifest": str(board_media_manifest_path),
        "expression_count": len(manifest.get("expressions") or {}),
        "generated_file_count": len(generated_files),
        "builds": build_rows,
    }
    print_result(result, bool(args.json))


if __name__ == "__main__":
    main()
