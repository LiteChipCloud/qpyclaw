#!/usr/bin/env python
"""
Build a board-friendly AIRI expression pack from a GIF or image sequence.

Examples:

python build_airi_expression_pack.py ^
  --src C:\\assets\\idle_blink.gif ^
  --out C:\\pack\\expressions ^
  --key idle_blink ^
  --width 176 --height 176 --zoom 320 --tick-step 3 --loop

python build_airi_expression_pack.py ^
  --src C:\\assets\\talk_open ^
  --out C:\\pack\\expressions ^
  --key talk_open ^
  --width 176 --height 176 --zoom 320 --tick-step 1 --loop
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pillow_bootstrap import ensure_pillow_path

try:
    from PIL import Image, ImageSequence
except ImportError as exc:
    ensure_pillow_path()
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        raise SystemExit(
            "Pillow is required. Install it with: python -m pip install pillow"
        ) from exc


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build AIRI expression frames for board runtime.")
    parser.add_argument("--src", required=True, help="GIF file or image sequence directory.")
    parser.add_argument("--out", required=True, help="Output expression pack directory.")
    parser.add_argument("--key", required=True, help="Expression key, for example idle_blink.")
    parser.add_argument("--width", type=int, default=176, help="Output frame width.")
    parser.add_argument("--height", type=int, default=176, help="Output frame height.")
    parser.add_argument("--zoom", type=int, default=320, help="LVGL zoom value.")
    parser.add_argument("--tick-step", type=int, default=2, help="Board ticks per frame.")
    parser.add_argument("--label", default="", help="Optional human-readable label.")
    parser.add_argument("--manifest-name", default="manifest.json", help="Manifest file name.")
    parser.add_argument("--fit", choices=("contain", "cover", "stretch"), default="contain")
    parser.add_argument("--bg", default="#FFFFFF", help="Background color used for transparency.")
    parser.add_argument("--frame-step", type=int, default=1, help="Keep every Nth source frame.")
    parser.add_argument("--max-frames", type=int, default=0, help="Optional max frame count after sampling.")
    parser.add_argument("--keep-duplicates", action="store_true", help="Write every sampled frame even when payloads repeat.")
    parser.add_argument(
        "--frame-format",
        choices=("rgb565", "png"),
        default="rgb565",
        help="Output frame payload format.",
    )
    parser.add_argument("--loop", action="store_true", help="Loop the expression.")
    return parser.parse_args()


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = (value or "").strip().lstrip("#")
    if len(text) != 6:
        raise ValueError("bg must look like #RRGGBB")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def load_frames(src: Path) -> list[Image.Image]:
    if src.is_dir():
        rows = []
        for path in sorted(src.iterdir()):
            if path.suffix.lower() in SUPPORTED_EXTS and path.is_file():
                rows.append(Image.open(path))
        if not rows:
            raise ValueError(f"no frames found under {src}")
        return rows
    if src.suffix.lower() == ".gif":
        image = Image.open(src)
        rows = []
        for frame in ImageSequence.Iterator(image):
            rows.append(frame.copy())
        if not rows:
            raise ValueError(f"gif has no frames: {src}")
        return rows
    return [Image.open(src)]


def select_frames(frames: list[Image.Image], frame_step: int, max_frames: int) -> list[Image.Image]:
    rows = []
    step = max(1, int(frame_step or 1))
    index = 0
    while index < len(frames):
        rows.append(frames[index])
        index += step
    limit = int(max_frames or 0)
    if limit > 0 and len(rows) > limit:
        rows = rows[:limit]
    if not rows and frames:
        rows = [frames[0]]
    return rows


def fit_frame(image: Image.Image, width: int, height: int, fit: str, bg: tuple[int, int, int]) -> Image.Image:
    source = image.convert("RGBA")
    target = Image.new("RGBA", (width, height), bg + (255,))
    if fit == "stretch":
        rendered = source.resize((width, height), Image.LANCZOS)
        target.alpha_composite(rendered, (0, 0))
        return target.convert("RGB")
    src_w, src_h = source.size
    scale_x = width / float(src_w)
    scale_y = height / float(src_h)
    scale = min(scale_x, scale_y) if fit == "contain" else max(scale_x, scale_y)
    draw_w = max(1, int(round(src_w * scale)))
    draw_h = max(1, int(round(src_h * scale)))
    rendered = source.resize((draw_w, draw_h), Image.LANCZOS)
    pos_x = int((width - draw_w) / 2)
    pos_y = int((height - draw_h) / 2)
    target.alpha_composite(rendered, (pos_x, pos_y))
    return target.convert("RGB")


def rgb565_bytes(image: Image.Image) -> bytes:
    rgb = image.convert("RGB")
    out = bytearray()
    pixels = rgb.load()
    pos_y = 0
    while pos_y < rgb.height:
        pos_x = 0
        while pos_x < rgb.width:
            red, green, blue = pixels[pos_x, pos_y]
            value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | ((blue & 0xF8) >> 3)
            out.append(value & 0xFF)
            out.append((value >> 8) & 0xFF)
            pos_x += 1
        pos_y += 1
    return bytes(out)


def payload_hash(payload: bytes) -> str:
    return hashlib.sha1(payload).hexdigest()


def frame_file_ext(frame_format: str) -> str:
    if str(frame_format or "").strip().lower() == "png":
        return ".png"
    return ".rgb565"


def build_payload_index(out_root: Path, frame_ext: str) -> dict[str, str]:
    rows = {}
    pattern = "*" + str(frame_ext or "")
    for path in sorted(out_root.rglob(pattern)):
        try:
            payload = path.read_bytes()
            key = payload_hash(payload)
            rel = path.relative_to(out_root).as_posix()
            if key not in rows:
                rows[key] = rel
        except Exception:
            pass
    return rows


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "default": "", "expressions": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    src = Path(args.src).expanduser().resolve()
    out_root = Path(args.out).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    expression_dir = out_root / args.key
    expression_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_root / args.manifest_name
    background = parse_hex_color(args.bg)
    frame_ext = frame_file_ext(args.frame_format)

    frames = select_frames(load_frames(src), args.frame_step, args.max_frames)
    payload_index = build_payload_index(out_root, frame_ext)
    frame_names = []
    for index, frame in enumerate(frames):
        rendered = fit_frame(frame, args.width, args.height, args.fit, background)
        if str(args.frame_format) == "png":
            payload = rendered.convert("RGB").tobytes()
        else:
            payload = rgb565_bytes(rendered)
        frame_name = "frame-%03d%s" % (index, frame_ext)
        target = expression_dir / frame_name
        rel_path = f"{args.key}/{frame_name}"
        if bool(args.keep_duplicates):
            if str(args.frame_format) == "png":
                rendered.save(target, format="PNG", optimize=True)
            else:
                target.write_bytes(payload)
            frame_names.append(rel_path)
            continue
        key = payload_hash(payload)
        cached_path = payload_index.get(key)
        if cached_path:
            frame_names.append(cached_path)
            continue
        if str(args.frame_format) == "png":
            rendered.save(target, format="PNG", optimize=True)
        else:
            target.write_bytes(payload)
        payload_index[key] = rel_path
        frame_names.append(rel_path)

    manifest = load_manifest(manifest_path)
    expressions = manifest.setdefault("expressions", {})
    expressions[args.key] = {
        "width": int(args.width),
        "height": int(args.height),
        "zoom": int(args.zoom),
        "tick_step": max(1, int(args.tick_step)),
        "loop": bool(args.loop),
        "label": args.label or args.key,
        "frame_format": str(args.frame_format),
        "frames": frame_names,
    }
    if not manifest.get("default"):
        manifest["default"] = args.key
    save_manifest(manifest_path, manifest)
    print(f"built {args.key} with {len(frame_names)} frames -> {expression_dir}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
