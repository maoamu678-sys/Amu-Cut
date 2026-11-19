#!/usr/bin/env python3
"""Export a normalized Amu Cut vertical video with FFmpeg."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


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


def resolve_project_path(project_dir: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else project_dir / path


def has_audio_stream(ffmpeg: str, input_path: Path) -> bool:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(input_path)],
        capture_output=True,
        text=True,
    )
    return bool(re.search(r"Audio:", result.stderr))


def media_duration(ffmpeg: str, input_path: Path) -> float:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(input_path)],
        capture_output=True,
        text=True,
    )
    match = re.search(r"Duration:\s+(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def broll_assets(project_dir: Path, timeline: dict[str, Any]) -> list[dict[str, Any]]:
    assets = []
    for scene in timeline.get("scenes", []):
        broll = scene.get("broll") or {}
        local_path = str(broll.get("local_path") or "").strip()
        if not local_path:
            continue
        path = resolve_project_path(project_dir, local_path)
        if not path.is_file():
            continue
        assets.append(
            {
                "path": path,
                "start": float(scene.get("start", 0)),
                "duration": min(3.0, max(0.1, float(broll.get("duration") or scene.get("duration", 1.0)))),
            }
        )
    return assets


def sfx_uses(project_dir: Path) -> list[dict[str, Any]]:
    mix_path = project_dir / "audio-mix.json"
    if not mix_path.is_file():
        return []
    mix = json.loads(mix_path.read_text(encoding="utf-8"))
    uses = []
    for item in mix.get("uses", []):
        source = str(item.get("source") or "").strip()
        if not source:
            continue
        path = resolve_project_path(project_dir, source)
        if not path.is_file():
            raise SystemExit(f"音效文件不存在：{path}")
        uses.append({
            "path": path,
            "start": max(0.0, float(item.get("start", 0))),
            "source_start": max(0.0, float(item.get("source_start", 0))),
            "duration": max(0.05, float(item.get("duration", 0.3))),
            "volume": max(0.0, min(1.0, float(item.get("volume", 0.28)))),
        })
    return uses


def render_overlay(project_dir: Path, overlay_dir: Path, timeline: dict) -> None:
    node = shutil.which("node")
    if not node:
        raise SystemExit("当前环境找不到 Node.js，无法渲染 Three.js 叠加层")
    engine_dir = find_engine_dir(project_dir)
    command = [node, str(engine_dir / "src" / "render_overlay.mjs"), str(project_dir), str(overlay_dir)]
    subprocess.run(command, check=True)
    if not list(overlay_dir.glob("overlay-*.png")):
        raise SystemExit("Three.js 没有生成叠加帧，请检查 timeline.json 是否包含场景")


def build_export_command(
    ffmpeg: str,
    input_path: Path,
    output_path: Path,
    timeline: dict[str, Any],
    overlay_dir: Path | None,
    broll: list[dict[str, Any]],
    sfx: list[dict[str, Any]],
) -> list[str]:
    fps = str(timeline["format"]["fps"])
    base_filter = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p"
    )
    command = [ffmpeg, "-y", "-i", str(input_path)]
    for asset in broll:
        if asset["path"].suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            command.extend(["-loop", "1", "-i", str(asset["path"])])
        else:
            command.extend(["-stream_loop", "-1", "-i", str(asset["path"])])
    for item in sfx:
        command.extend(["-i", str(item["path"])])
    overlay_input = None
    if overlay_dir is not None:
        overlay_input = 1 + len(broll) + len(sfx)
        command.extend(["-framerate", fps, "-i", str(overlay_dir / "overlay-%06d.png")])

    filters = [f"[0:v]{base_filter}[base0]"]
    current_video = "base0"
    for index, asset in enumerate(broll):
        overlay_label = f"broll{index}"
        next_video = f"v{index + 1}"
        start = asset["start"]
        end = start + asset["duration"]
        filters.append(
            f"[{index + 1}:v]trim=duration={asset['duration']:.3f},setpts=PTS-STARTPTS+{start:.6f}/TB,"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,format=rgba[{overlay_label}]"
        )
        filters.append(
            f"[{current_video}][{overlay_label}]overlay=0:0:eof_action=pass:repeatlast=0:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{next_video}]"
        )
        current_video = next_video

    if overlay_input is not None:
        filters.append(f"[{overlay_input}:v]format=rgba[caption]")
        filters.append(f"[{current_video}][caption]overlay=0:0:format=auto[vout]")
    else:
        filters.append(f"[{current_video}]null[vout]")

    audio_exists = has_audio_stream(ffmpeg, input_path)
    input_duration = media_duration(ffmpeg, input_path)
    audio_labels = []
    if audio_exists:
        filters.append("[0:a]aresample=44100[voice]")
        audio_labels.append("[voice]")
    elif sfx:
        filters.append(f"anullsrc=channel_layout=stereo:sample_rate=44100:d={max(input_duration, 0.1):.3f}[voice]")
        audio_labels.append("[voice]")

    sfx_input_start = 1 + len(broll)
    for index, item in enumerate(sfx):
        delay = round(item["start"] * 1000)
        label = f"sfx{index}"
        filters.append(
            f"[{sfx_input_start + index}:a]atrim=start={item['source_start']:.3f}:duration={item['duration']:.3f},asetpts=PTS-STARTPTS,"
            f"volume={item['volume']:.3f},adelay={delay}|{delay}[{label}]"
        )
        audio_labels.append(f"[{label}]")

    if audio_labels:
        filters.append(
            f"{''.join(audio_labels)}amix=inputs={len(audio_labels)}:duration=first:dropout_transition=0,"
            "alimiter=limit=0.98[aout]"
        )

    command.extend(["-filter_complex", ";".join(filters), "-map", "[vout]"])
    if audio_labels:
        command.extend(["-map", "[aout]"])
    else:
        command.extend(["-map", "0:a?"])
    command.extend(
        [
            "-r",
            fps,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-t",
            f"{max(input_duration, 0.1):.3f}",
            str(output_path),
        ]
    )
    return command


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

    broll = broll_assets(project_dir, timeline)
    sfx = sfx_uses(project_dir)
    overlay_dir = None
    if args.with_overlay:
        overlay_dir = project_dir / "output" / "overlay"
        render_overlay(project_dir, overlay_dir, timeline)
    command = build_export_command(ffmpeg, input_path, output_path, timeline, overlay_dir, broll, sfx)
    print("工程时间线已读取")
    print(f"风格：{timeline.get('styleName', timeline.get('style'))}")
    print(f"场景数：{len(timeline.get('scenes', []))}")
    print(f"B-roll 叠加：{len(broll)} 条")
    print(f"音效混合：{len(sfx)} 条")
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
