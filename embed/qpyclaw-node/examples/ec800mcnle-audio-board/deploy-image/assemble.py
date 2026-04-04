#!/usr/bin/env python3
"""Assemble a device /usr/ mirror from repo sources for EC800MCNLE audio board.

Usage:
    python assemble.py [--output <dir>] [--clean]

The assembled directory can be synced to the device via host tools.
"""

import argparse
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
EMBED_ROOT = os.path.join(REPO_ROOT, "embed")

NODE_CODE = os.path.join(EMBED_ROOT, "qpyclaw-node", "code")
COMPONENTS = os.path.join(EMBED_ROOT, "components")
BOARD_CODE = os.path.join(EMBED_ROOT, "boards", "ec800mcnle-audio-board", "code")

# Files deployed to /usr/ (device root)
USR_FILES = [
    # (source_dir, filename)
    (NODE_CODE, "_main.py"),
    (NODE_CODE, "config.py"),
    (NODE_CODE, "qpyclaw_node.py"),
    (NODE_CODE, "transport.py"),
    (NODE_CODE, "tools.py"),
    (NODE_CODE, "voice.py"),
    (NODE_CODE, "dispatch.py"),
    (NODE_CODE, "node_main.py"),
    (COMPONENTS, "ws_client.py"),
    (COMPONENTS, "cellular.py"),
]

# Files deployed to /usr/board/
BOARD_FILES = [
    (BOARD_CODE, "board_bootstrap.py"),
    (BOARD_CODE, "board_audio.py"),
    (BOARD_CODE, "board_display.py"),
    (BOARD_CODE, "board_power.py"),
    (BOARD_CODE, "board_ui.py"),
    (BOARD_CODE, "board_voice_controller.py"),
    (BOARD_CODE, "board_remote_asr.py"),
    (BOARD_CODE, "board_remote_tts.py"),
]

# Example config (copied but NOT overwriting existing config_local.py)
EXAMPLE_CONFIG = os.path.join(
    EMBED_ROOT, "qpyclaw-node", "examples", "ec800mcnle-audio-board", "config_local.example.py"
)


def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def assemble(output_dir, clean=False):
    if clean and os.path.isdir(output_dir):
        shutil.rmtree(output_dir)

    usr_dir = os.path.join(output_dir, "usr")
    board_dir = os.path.join(usr_dir, "board")

    copied = 0
    missing = []

    for source_dir, filename in USR_FILES:
        src = os.path.join(source_dir, filename)
        dst = os.path.join(usr_dir, filename)
        if not os.path.isfile(src):
            missing.append(src)
            continue
        copy_file(src, dst)
        copied += 1

    for source_dir, filename in BOARD_FILES:
        src = os.path.join(source_dir, filename)
        dst = os.path.join(board_dir, filename)
        if not os.path.isfile(src):
            missing.append(src)
            continue
        copy_file(src, dst)
        copied += 1

    # Copy example config as reference (not as config_local.py to avoid overwriting)
    if os.path.isfile(EXAMPLE_CONFIG):
        copy_file(EXAMPLE_CONFIG, os.path.join(usr_dir, "config_local.example.py"))
        copied += 1

    return copied, missing


def main():
    parser = argparse.ArgumentParser(description="Assemble EC800MCNLE audio board deploy image")
    parser.add_argument(
        "--output", "-o",
        default=os.path.join(SCRIPT_DIR, "output"),
        help="Output directory (default: ./output)",
    )
    parser.add_argument("--clean", action="store_true", help="Remove output dir before assembling")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output)
    copied, missing = assemble(output_dir, clean=args.clean)

    print("Assembled {} files -> {}".format(copied, output_dir))
    if missing:
        print("WARNING: {} source files not found:".format(len(missing)))
        for path in missing:
            print("  - " + path)
        sys.exit(1)
    else:
        print("All source files found. Image ready.")
        print()
        print("Device layout:")
        for root, dirs, files in os.walk(os.path.join(output_dir, "usr")):
            level = root.replace(os.path.join(output_dir, "usr"), "/usr")
            level = level.replace("\\", "/")
            indent = "  " * (level.count("/") - 1)
            print("{}{}/ ({} files)".format(indent, os.path.basename(root) or "usr", len(files)))
            for f in sorted(files):
                print("{}  {}".format(indent, f))


if __name__ == "__main__":
    main()
