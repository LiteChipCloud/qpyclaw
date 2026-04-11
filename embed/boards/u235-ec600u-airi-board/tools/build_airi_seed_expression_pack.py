#!/usr/bin/env python
"""
Build a minimal AIRI expression pack from the checked-in AIRI prototype image.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pillow_bootstrap import ensure_pillow_path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:
    ensure_pillow_path()
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise SystemExit(
            "Pillow is required. Install it with: python -m pip install pillow"
        ) from exc


WIDTH = 176
HEIGHT = 176

SKIN_BASE = (241, 214, 200, 180)
SKIN_SHADE = (232, 195, 180, 96)
LASH_BROWN = (111, 88, 82, 215)
IRIS_BLUE = (110, 132, 182, 70)
IRIS_GLOW = (196, 223, 255, 72)
MOUTH_PINK = (218, 129, 139, 110)
MOUTH_DEEP = (176, 82, 102, 196)
MOUTH_SOFT = (244, 188, 183, 58)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a seed AIRI RGB565 expression pack.")
    parser.add_argument("--src", required=True, help="Base AIRI image, for example airi-avatar-proto.png.")
    parser.add_argument("--out", required=True, help="Output expressions directory.")
    parser.add_argument("--width", type=int, default=WIDTH, help="Frame width.")
    parser.add_argument("--height", type=int, default=HEIGHT, help="Frame height.")
    parser.add_argument("--zoom", type=int, default=320, help="LVGL zoom.")
    parser.add_argument("--gif-dir", default="", help="Optional directory for exported GIF sources.")
    parser.add_argument("--gif-duration", type=int, default=120, help="Per-frame GIF duration in ms.")
    return parser.parse_args()


def fit_base_image(src: Path, width: int, height: int) -> Image.Image:
    image = Image.open(src).convert("RGBA")
    if image.size != (width, height):
        image = image.resize((width, height), Image.LANCZOS)
    return image


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


def write_rgb565(path: Path, image: Image.Image) -> None:
    path.write_bytes(rgb565_bytes(image))


def clone_image(image: Image.Image) -> Image.Image:
    return image.copy()


def draw_eye_cover(draw: ImageDraw.ImageDraw, cx: float, cy: float, openness: float) -> None:
    lid_bottom = cy + 5.6 + ((1.0 - openness) * 1.0)
    draw.ellipse((cx - 11.6, cy - 1.0, cx + 11.6, lid_bottom), fill=SKIN_BASE)
    draw.ellipse((cx - 9.1, cy + 0.4, cx + 9.1, cy + 3.8), fill=SKIN_SHADE)
    line_y = cy + 1.8 + ((1.0 - openness) * 0.8)
    draw.line((cx - 9.8, line_y, cx + 9.8, line_y + (0.3 if openness < 0.45 else 0.0)), fill=LASH_BROWN, width=2)


def draw_focus_eye(draw: ImageDraw.ImageDraw, cx: float, cy: float, pulse: float) -> None:
    draw.ellipse((cx - 4.8 - pulse, cy - 6.2 - pulse, cx + 4.8 + pulse, cy + 6.2 + pulse), fill=IRIS_BLUE)
    draw.ellipse((cx - 0.8, cy - 4.0, cx + 4.4, cy + 0.8), fill=IRIS_GLOW)
    brow_y = cy - 11.8 - pulse
    draw.line((cx - 10.0, brow_y, cx + 8.5, brow_y - 0.6), fill=(111, 88, 82, 90 + int(pulse * 36)), width=1)


def draw_mouth_open(draw: ImageDraw.ImageDraw, openness: float) -> None:
    outer_rx = 4.0 + (openness * 3.0)
    outer_ry = 3.2 + (openness * 3.8)
    inner_rx = outer_rx - 1.4
    inner_ry = outer_ry - 1.6
    draw.ellipse((88 - 8.5, 96.5, 88 + 8.5, 103.2), fill=SKIN_BASE)
    draw.ellipse((88 - 5.8, 98.1, 88 + 5.8, 103.9), fill=(232, 195, 180, 74))
    draw.ellipse((88 - outer_rx, 99.1 - outer_ry, 88 + outer_rx, 99.1 + outer_ry), fill=MOUTH_PINK)
    draw.ellipse((88 - inner_rx, 100.0 - inner_ry, 88 + inner_rx, 100.0 + inner_ry), fill=MOUTH_DEEP)
    draw.ellipse((88 - inner_rx, 97.4 - (inner_ry * 0.42), 88 + inner_rx, 97.4 + (inner_ry * 0.42)), fill=MOUTH_SOFT)


def compose_frame(base: Image.Image, painter) -> Image.Image:
    frame = clone_image(base)
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    painter(draw)
    return Image.alpha_composite(frame, overlay)


def build_idle_frames(base: Image.Image) -> list[Image.Image]:
    half = compose_frame(base, lambda draw: (draw_eye_cover(draw, 69.0, 57.0, 0.48), draw_eye_cover(draw, 106.0, 57.0, 0.48)))
    closed = compose_frame(base, lambda draw: (draw_eye_cover(draw, 69.0, 57.0, 0.0), draw_eye_cover(draw, 106.0, 57.0, 0.0)))
    return [clone_image(base), clone_image(base), half, closed, half, clone_image(base), clone_image(base)]


def build_listen_frames(base: Image.Image) -> list[Image.Image]:
    pulse_rows = (0.18, 0.34, 0.48, 0.34)
    frames = []
    for pulse in pulse_rows:
        frames.append(
            compose_frame(
                base,
                lambda draw, pulse=pulse: (
                    draw_focus_eye(draw, 69.0, 57.0, pulse),
                    draw_focus_eye(draw, 106.0, 57.0, pulse),
                ),
            )
        )
    return frames


def build_talk_frames(base: Image.Image) -> list[Image.Image]:
    openness_rows = (0.30, 0.62, 0.95, 0.56)
    frames = []
    for openness in openness_rows:
        frames.append(compose_frame(base, lambda draw, openness=openness: draw_mouth_open(draw, openness)))
    return frames


def write_expression(out_root: Path, key: str, frames: list[Image.Image]) -> list[str]:
    expression_dir = out_root / key
    expression_dir.mkdir(parents=True, exist_ok=True)
    frame_paths = []
    for index, frame in enumerate(frames):
        file_name = f"frame-{index:03d}.rgb565"
        write_rgb565(expression_dir / file_name, frame)
        frame_paths.append(f"{key}/{file_name}")
    return frame_paths


def build_manifest(width: int, height: int, zoom: int, expression_files: dict[str, list[str]]) -> dict:
    return {
        "version": 1,
        "default": "idle_blink",
        "expressions": {
            "idle_blink": {
                "width": int(width),
                "height": int(height),
                "zoom": int(zoom),
                "tick_step": 3,
                "loop": True,
                "label": "Idle Blink",
                "frames": expression_files["idle_blink"],
            },
            "listen_focus": {
                "width": int(width),
                "height": int(height),
                "zoom": int(zoom),
                "tick_step": 2,
                "loop": True,
                "label": "Listen Focus",
                "frames": expression_files["listen_focus"],
            },
            "talk_open": {
                "width": int(width),
                "height": int(height),
                "zoom": int(zoom),
                "tick_step": 1,
                "loop": True,
                "label": "Talk Open",
                "frames": expression_files["talk_open"],
            },
        },
    }


def save_preview_sheet(out_root: Path, expressions: dict[str, list[Image.Image]]) -> None:
    groups = ("idle_blink", "listen_focus", "talk_open")
    tile_w = WIDTH
    tile_h = HEIGHT
    gap = 16
    rows = len(groups)
    cols = 7
    sheet = Image.new("RGBA", ((tile_w + gap) * cols + gap, (tile_h + gap) * rows + gap), (10, 18, 34, 255))
    row_index = 0
    while row_index < len(groups):
        key = groups[row_index]
        frames = expressions.get(key) or []
        col_index = 0
        while col_index < len(frames):
            pos_x = gap + (col_index * (tile_w + gap))
            pos_y = gap + (row_index * (tile_h + gap))
            sheet.alpha_composite(frames[col_index], (pos_x, pos_y))
            col_index += 1
        row_index += 1
    sheet.save(out_root / "preview-sheet.png")


def save_expression_gif(path: Path, frames: list[Image.Image], duration_ms: int) -> None:
    if not frames:
        return
    prepared = []
    for frame in frames:
        prepared.append(frame.convert("P", palette=Image.ADAPTIVE))
    prepared[0].save(
        path,
        save_all=True,
        append_images=prepared[1:],
        optimize=False,
        duration=max(20, int(duration_ms or 120)),
        loop=0,
        disposal=2,
    )


def main() -> None:
    args = parse_args()
    src = Path(args.src).expanduser().resolve()
    out_root = Path(args.out).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    base = fit_base_image(src, int(args.width), int(args.height))
    expressions = {
        "idle_blink": build_idle_frames(base),
        "listen_focus": build_listen_frames(base),
        "talk_open": build_talk_frames(base),
    }

    expression_files = {}
    for key, frames in expressions.items():
        expression_files[key] = write_expression(out_root, key, frames)

    manifest = build_manifest(args.width, args.height, args.zoom, expression_files)
    (out_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    save_preview_sheet(out_root, expressions)
    gif_dir = Path(args.gif_dir).expanduser().resolve() if args.gif_dir else None
    if gif_dir is not None:
        gif_dir.mkdir(parents=True, exist_ok=True)
        for key, frames in expressions.items():
            save_expression_gif(gif_dir / (key + ".gif"), frames, args.gif_duration)
    print(f"built seed pack -> {out_root}")


if __name__ == "__main__":
    main()
