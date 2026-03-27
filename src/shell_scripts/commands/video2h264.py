#!/usr/bin/env python3
"""@brief Video-to-H.264 ffmpeg command module.

@details Provides CLI contract for `video2h264`, validates required positional
input, derives output path by appending `.mp4` suffix to input path token, and
executes deterministic ffmpeg argv for H.264 + AAC transcoding.
@satisfies PRJ-003, DES-008, REQ-095, REQ-096
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from shell_scripts.utils import print_error, require_commands

PROGRAM = "shellscripts"
DESCRIPTION = "Convert a video to H.264/AAC MP4 using ffmpeg."


def _build_output_path(input_path: Path) -> Path:
    """@brief Derive output path for `video2h264`.

    @details Appends literal `.mp4` suffix to full input token without removing
    existing suffixes, preserving parent directory and basename semantics (for
    example `input.mov -> input.mov.mp4`).
    @param input_path {Path} Input video path argument.
    @return {Path} Output path with appended `.mp4` suffix.
    @satisfies REQ-096
    """

    return Path(f"{input_path}.mp4")


def print_help(version: str) -> None:
    """@brief Render command help for `video2h264`.

    @details Prints usage contract with one required input path and deterministic
    output naming rule.
    @param version {str} CLI version string appended to usage output.
    @return {None} Writes help text to stdout.
    @satisfies DES-008, REQ-095, REQ-096
    """

    print(f"Usage: {PROGRAM} video2h264 <input-video> ({version})")
    print()
    print("video2h264 options:")
    print("  <input-video>  - Input video file (required).")
    print("  --help         - Show this help message.")
    print()
    print("Output path is generated as <input-video>.mp4 in the same directory.")


def run(args: list[str]) -> int:
    """@brief Execute H.264 transcoding with ffmpeg.

    @details Validates one positional input argument, checks ffmpeg dependency,
    verifies input file existence, computes `<input>.mp4` output path, and
    executes ffmpeg with fixed codec/pixel-format/bitrate options. Time
    complexity O(1) excluding external ffmpeg processing cost.
    @param args {list[str]} Command arguments excluding command token.
    @return {int} ffmpeg return code; `1` on argument or input validation error.
    @satisfies REQ-095, REQ-096
    """

    if len(args) != 1 or args[0].startswith("-"):
        print_error("Usage: video2h264 <input-video>")
        return 1

    input_path = Path(args[0])
    if not input_path.is_file():
        print_error(f"File not found: {input_path}")
        return 1

    require_commands("ffmpeg")

    output_path = _build_output_path(input_path)
    command = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]
    result = subprocess.run(command)
    return int(result.returncode)
