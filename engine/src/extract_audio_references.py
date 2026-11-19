#!/usr/bin/env python3
"""Extract compact audio reference tracks from user-provided videos."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def find_ffmpeg() -> str | None:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    engine_dir = Path(__file__).resolve().parents[1]
    bundled = engine_dir / "node_modules" / "ffmpeg-static" / "ffmpeg"
    return str(bundled) if bundled.is_file() else None


def extract(videos: list[Path], output_dir: Path) -> None:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit("找不到 FFmpeg。请在 engine 目录执行 npm install。")
    output_dir.mkdir(parents=True, exist_ok=True)
    references = []
    for index, video in enumerate(videos, start=1):
        if not video.is_file():
            raise SystemExit(f"找不到音效参考视频：{video}")
        output = output_dir / f"reference-{index:02d}.mp3"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(video),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "44100",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "64k",
                str(output),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        references.append(
            {
                "source_video": str(video),
                "local_path": str(output.relative_to(output_dir.parent.parent)),
                "role": "reference-only",
                "auto_mix": False,
                "note": "完整音轨作为声音风格参考保存。需要加入成片时，先在 audio-mix.json 中指定片段或替换为单独音效文件。",
            }
        )
        print(f"已提取：{output}")
    profile = {
        "schemaVersion": "0.1",
        "references": references,
        "matching": {
            "mode": "user-requested-or-local-sfx-filename-match",
            "referenceTracksAreNotMixedAutomatically": True,
            "approvedPeakDbtp": -2.3,
        },
    }
    (output_dir / "audio-reference-profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已生成声音参考档案：{output_dir / 'audio-reference-profile.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="声音参考输出目录")
    parser.add_argument("videos", nargs="+", help="一个或多个参考视频")
    args = parser.parse_args()
    extract([Path(item).expanduser().resolve() for item in args.videos], Path(args.output).expanduser().resolve())


if __name__ == "__main__":
    main()
