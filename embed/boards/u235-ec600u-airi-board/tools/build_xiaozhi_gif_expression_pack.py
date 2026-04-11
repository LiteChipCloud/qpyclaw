#!/usr/bin/env python
"""
Build a storage-aware XiaoZhi GIF expression pack for the U235 AIRI board.

The source GIF set is animated but far too large to mirror in full on the board.
This builder keeps a compact animated core set for the expressions used by the
current AIRI scene and then adds zero-cost alias entries for the remaining
emotion names by reusing the core frame lists.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUILD_AIRI_PACK = HERE / "build_airi_expression_pack.py"
DEFAULT_SRC_DIR = Path(r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\opensource\media")
DEFAULT_OUT_DIR = (
    Path(r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw")
    / "embed"
    / "boards"
    / "u235-ec600u-airi-board"
    / "resource"
    / "ui"
    / "airi"
    / "xiaozhi-gif-lvgl-expressions"
)
DEFAULT_BOARD_MEDIA_MANIFEST = (
    Path(r"C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw")
    / "embed"
    / "qpyclaw-node"
    / "deploy"
    / "board-manifests"
    / "u235-ec600u-airi-board-xiaozhi-gif-media.json"
)


def manifest_local_root_rel(out_dir: Path) -> str:
    board_manifest_dir = DEFAULT_BOARD_MEDIA_MANIFEST.parent.resolve()
    try:
        return Path(os.path.relpath(str(Path(out_dir).resolve()), str(board_manifest_dir))).as_posix()
    except Exception:
        return (
            Path("../../../boards/u235-ec600u-airi-board/resource/ui/airi")
            / Path(out_dir).name
        ).as_posix()


CORE_BUILD_PLAN = (
    {
        "key": "idle_blink",
        "src": "neutral.gif",
        "label": "Idle Blink",
        "tick_step": 4,
        "loop": True,
        "frame_step": 15,
        "max_frames": 5,
    },
    {
        "key": "listen_focus",
        "src": "thinking.gif",
        "label": "Listen Focus",
        "tick_step": 3,
        "loop": True,
        "frame_step": 10,
        "max_frames": 4,
    },
    {
        "key": "talk_smile",
        "src": "happy.gif",
        "label": "Talk Smile",
        "tick_step": 2,
        "loop": True,
        "frame_step": 4,
        "max_frames": 3,
    },
    {
        "key": "talk_open",
        "src": "laughing.gif",
        "label": "Talk Open",
        "tick_step": 2,
        "loop": True,
        "frame_step": 7,
        "max_frames": 3,
    },
    {
        "key": "happy_pop",
        "src": "happy.gif",
        "label": "Happy Pop",
        "tick_step": 2,
        "loop": False,
        "frame_step": 3,
        "max_frames": 4,
    },
    {
        "key": "sad_soft",
        "src": "sad.gif",
        "label": "Sad Soft",
        "tick_step": 3,
        "loop": False,
        "frame_step": 10,
        "max_frames": 4,
    },
    {
        "key": "angry_fire",
        "src": "angry.gif",
        "label": "Angry Fire",
        "tick_step": 2,
        "loop": False,
        "frame_step": 6,
        "max_frames": 3,
    },
    {
        "key": "sleep_breath",
        "src": "sleep.gif",
        "label": "Sleep Breath",
        "tick_step": 4,
        "loop": True,
        "frame_step": 5,
        "max_frames": 4,
    },
    {
        "key": "shock_hold",
        "src": "surprised.gif",
        "label": "Shock Hold",
        "tick_step": 2,
        "loop": False,
        "frame_step": 6,
        "max_frames": 3,
    },
    {
        "key": "wink_ping",
        "src": "winking.gif",
        "label": "Wink Ping",
        "tick_step": 2,
        "loop": False,
        "frame_step": 16,
        "max_frames": 3,
    },
)


ALIAS_TO_CORE = {
    "neutral": "idle_blink",
    "relaxed": "idle_blink",
    "thinking": "listen_focus",
    "confused": "listen_focus",
    "happy": "happy_pop",
    "laughing": "talk_open",
    "loving": "happy_pop",
    "cool": "happy_pop",
    "confident": "happy_pop",
    "delicious": "happy_pop",
    "funny": "talk_smile",
    "sad": "sad_soft",
    "crying": "sad_soft",
    "angry": "angry_fire",
    "sleep": "sleep_breath",
    "surprised": "shock_hold",
    "winking": "wink_ping",
    "embarrassed": "wink_ping",
    "kissy": "wink_ping",
    "silly": "talk_smile",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build XiaoZhi GIF pack for AIRI board runtime.")
    parser.add_argument("--src-dir", default=str(DEFAULT_SRC_DIR), help="Source XiaoZhi GIF directory.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output expressions directory.")
    parser.add_argument("--width", type=int, default=176, help="Output frame width.")
    parser.add_argument("--height", type=int, default=176, help="Output frame height.")
    parser.add_argument("--zoom", type=int, default=320, help="LVGL zoom.")
    parser.add_argument(
        "--frame-format",
        choices=("png", "rgb565"),
        default="png",
        help="Board frame payload format. PNG is preferred when LVGL file decoders are available.",
    )
    parser.add_argument("--fit", choices=("contain", "cover", "stretch"), default="contain")
    parser.add_argument("--bg", default="#FFFFFF", help="Background color used for transparent pixels.")
    parser.add_argument(
        "--board-media-manifest",
        default=str(DEFAULT_BOARD_MEDIA_MANIFEST),
        help="Optional qpy_board_media_sync manifest output path.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    return parser.parse_args()


def resolve_dir(path_text: str, must_exist: bool) -> Path:
    path = Path(str(path_text or "")).expanduser().resolve()
    if must_exist and not path.is_dir():
        raise SystemExit("Directory not found: %s" % path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_builder(
    src_dir: Path,
    out_dir: Path,
    width: int,
    height: int,
    zoom: int,
    frame_format: str,
    fit: str,
    bg: str,
    item: dict,
) -> None:
    src_path = src_dir / item["src"]
    if not src_path.is_file():
        raise SystemExit("Missing source GIF: %s" % src_path)
    cmd = [
        sys.executable,
        str(BUILD_AIRI_PACK),
        "--src",
        str(src_path),
        "--out",
        str(out_dir),
        "--key",
        str(item["key"]),
        "--width",
        str(int(width)),
        "--height",
        str(int(height)),
        "--zoom",
        str(int(zoom)),
        "--frame-format",
        str(frame_format),
        "--tick-step",
        str(int(item["tick_step"])),
        "--label",
        str(item["label"]),
        "--fit",
        str(fit),
        "--bg",
        str(bg),
        "--frame-step",
        str(int(item["frame_step"])),
        "--max-frames",
        str(int(item["max_frames"])),
    ]
    if bool(item.get("loop")):
        cmd.append("--loop")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout or ("build failed for %s" % item["key"]))


def manifest_path(out_dir: Path) -> Path:
    return out_dir / "manifest.json"


def load_manifest(out_dir: Path) -> dict:
    path = manifest_path(out_dir)
    if not path.is_file():
        raise SystemExit("Manifest missing after build: %s" % path)
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(out_dir: Path, manifest: dict) -> None:
    manifest_path(out_dir).write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def add_alias_entries(manifest: dict) -> list[str]:
    rows = manifest.setdefault("expressions", {})
    added = []
    for alias_key, core_key in ALIAS_TO_CORE.items():
        if alias_key in rows:
            continue
        source = rows.get(core_key)
        if not isinstance(source, dict):
            continue
        rows[alias_key] = {
            "width": int(source.get("width") or 176),
            "height": int(source.get("height") or 176),
            "zoom": int(source.get("zoom") or 320),
            "tick_step": int(source.get("tick_step") or 2),
            "loop": bool(source.get("loop")),
            "label": alias_key,
            "frame_format": str(source.get("frame_format") or ""),
            "frames": list(source.get("frames") or []),
        }
        added.append(alias_key)
    return added


def list_relative_files(out_dir: Path) -> list[str]:
    rows = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file():
            rows.append(path.relative_to(out_dir).as_posix())
    return rows


def write_board_media_manifest(out_dir: Path, manifest_path_text: str) -> Path:
    target = Path(str(manifest_path_text or "")).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 1,
        "name": "u235-ec600u-airi-board-xiaozhi-gif-media",
        "local_root_rel": manifest_local_root_rel(out_dir),
        "remote_root": "/usr/media/expressions",
        "files": list_relative_files(out_dir),
        "preserve_remote_files": [],
        "remove_remote_files": [],
    }
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> None:
    args = parse_args()
    src_dir = resolve_dir(args.src_dir, True)
    out_dir = resolve_dir(args.out, False)

    for item in CORE_BUILD_PLAN:
        run_builder(
            src_dir=src_dir,
            out_dir=out_dir,
            width=int(args.width),
            height=int(args.height),
            zoom=int(args.zoom),
            frame_format=str(args.frame_format),
            fit=str(args.fit),
            bg=str(args.bg),
            item=item,
        )

    manifest = load_manifest(out_dir)
    alias_added = add_alias_entries(manifest)
    save_manifest(out_dir, manifest)
    board_manifest = write_board_media_manifest(out_dir, args.board_media_manifest)
    rel_files = list_relative_files(out_dir)
    result = {
        "status": "ok",
        "src_dir": str(src_dir),
        "out_dir": str(out_dir),
        "frame_format": str(args.frame_format),
        "core_keys": [item["key"] for item in CORE_BUILD_PLAN],
        "alias_keys": alias_added,
        "file_count": len(rel_files),
        "board_media_manifest": str(board_manifest),
        "files": rel_files,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("built xiaozhi gif pack -> %s" % out_dir)
    print("board media manifest -> %s" % board_manifest)
    print("core keys -> %s" % ", ".join(result["core_keys"]))
    print("alias keys -> %s" % ", ".join(alias_added))


if __name__ == "__main__":
    main()
