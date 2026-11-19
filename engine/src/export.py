#!/usr/bin/env python3
"""Export a normalized Amu Cut vertical video with FFmpeg."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def find_ffmpeg(project_dir: Path) -> str | None:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    candidates = [
        project_dir / "node_modules" / "ffmpeg-static" / "ffmpeg",
        project_dir.parent.parent / "engine" / "node_modules" / "ffmpeg-static" / "ffmpeg",
        Path(__file__).resolve().parents[1] / "node_modules" / "ffmpeg-static" / "ffmpeg",
    ]
    return next((str(path) for path in candidates if path.is_file()), None)


def find_engine_dir(project_dir: Path) -> Path:
    candidates = [
        project_dir / "engine",
        project_dir.parent.parent / "engine",
        Path(__file__).resolve().parents[1],
    ]
    for candidate in candidates:
        if (candidate / "src" / "render_overlay.mjs").is_file():
            return candidate
    raise SystemExit("找不到 Amu Cut engine 目录，无法渲染 Three.js 叠加层")


def render_overlay(project_dir: Path, overlay_dir: Path, timeline: dict) -> None:
    node = shutil.which("node")
    if not node:
        raise SystemExit("当前环境找不到 Node.js，无法渲染 Three.js 叠加层")
    engine_dir = find_engine_dir(project_dir)
    command = [node, str(engine_dir / "src" / "render_overlay.mjs"), str(project_dir), str(overlay_dir)]
    subprocess.run(command, check=True)
    if not list(overlay_dir.glob("overlay-*.png")):
        raise SystemExit("Three.js 没有生成叠加帧，请检查 timeline.json 是否包含场景")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Amu Cut 工程目录")
    parser.add_argument("--input", required=True, help="待合成的口播视频")
    parser.add_argument("--output", required=True, help="导出的 MP4")
    parser.add_argument("--dry-run", action="store_true", help="只检查，不导出")
    parser.add_argument(
        "--with-overlay",
        action="store_true",
        help="先渲染 Three.js 字幕和字卡叠加层，再交给 FFmpeg 合成",
    )
    args = parser.parse_args()

    project_dir = Path(args.project).expanduser().resolve()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    timeline_path = project_dir / "timeline.json"
    if not timeline_path.is_file():
        raise SystemExit(f"找不到工程时间线 {timeline_path}")
    if not input_path.is_file():
        raise SystemExit(f"找不到输入视频 {input_path}")

    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_ffmpeg(project_dir)
    if not ffmpeg:
        raise SystemExit(
            "当前环境找不到 FFmpeg。请安装 FFmpeg，或在 engine 目录执行 npm install 以使用 ffmpeg-static。"
        )

    base_video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p"
    )
    if args.with_overlay:
        overlay_dir = project_dir / "output" / "overlay"
        render_overlay(project_dir, overlay_dir, timeline)
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-framerate",
            str(timeline["format"]["fps"]),
            "-i",
            str(overlay_dir / "overlay-%06d.png"),
            "-filter_complex",
            f"[0:v]{base_video_filter}[base];[1:v]format=rgba[overlay];[base][overlay]overlay=0:0:format=auto[v]",
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-r",
            str(timeline["format"]["fps"]),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        ]
    else:
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-vf",
            base_video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]
    print("工程时间线已读取")
    print(f"风格：{timeline.get('styleName', timeline.get('style'))}")
    print(f"场景数：{len(timeline.get('scenes', []))}")
    print("当前导出阶段：完成竖屏规格、视频编码和人声保留")
    if args.with_overlay:
        print("Three.js 叠加层：已纳入当前导出命令")
    else:
        print("Three.js 叠加层：未启用。需要叠加字幕和字卡时加上 --with-overlay")
    if args.dry_run:
        print("dry-run：未执行 FFmpeg")
        print(" ".join(command))
        return

    subprocess.run(command, check=True)
    print(f"已导出：{output_path}")


if __name__ == "__main__":
    main()
