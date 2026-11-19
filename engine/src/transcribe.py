#!/usr/bin/env python3
"""Generate an SRT file when a project does not provide one."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_ffmpeg() -> str | None:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    engine_dir = Path(__file__).resolve().parents[1]
    bundled = engine_dir / "node_modules" / "ffmpeg-static" / "ffmpeg"
    return str(bundled) if bundled.is_file() else None


def transcribe(input_path: Path, output_path: Path, language: str, model: str) -> None:
    try:
        import whisper  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "没有找到本地 Whisper。请先执行 python3 -m pip install openai-whisper，"
            "然后重新运行本工具。"
        ) from exc

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise SystemExit(
            "Whisper 需要 FFmpeg。请在 engine 目录执行 npm install，"
            "或在系统中安装 FFmpeg。"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="amu-cut-transcribe-") as temp_dir:
        environment = os.environ.copy()
        environment["PATH"] = f"{Path(ffmpeg).parent}{os.pathsep}{environment.get('PATH', '')}"
        command = [
            sys.executable,
            "-m",
            "whisper",
            str(input_path),
            "--model",
            model,
            "--language",
            language,
            "--task",
            "transcribe",
            "--output_format",
            "srt",
            "--output_dir",
            temp_dir,
            "--fp16",
            "False",
        ]
        subprocess.run(command, check=True, env=environment)
        generated = Path(temp_dir) / f"{input_path.stem}.srt"
        if not generated.is_file():
            candidates = sorted(Path(temp_dir).glob("*.srt"))
            generated = candidates[0] if candidates else generated
        if not generated.is_file():
            raise SystemExit("Whisper 没有生成 SRT 文件，请检查音频和模型输出。")
        shutil.copy2(generated, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="需要识别的 MP4 或音频文件")
    parser.add_argument("--output", required=True, help="输出 SRT 文件")
    parser.add_argument("--language", default="zh", help="语音语言，默认 zh")
    parser.add_argument("--model", default="turbo", help="Whisper 模型，默认 turbo")
    args = parser.parse_args()
    transcribe(Path(args.input).expanduser().resolve(), Path(args.output).expanduser().resolve(), args.language, args.model)
    print(f"已生成字幕：{Path(args.output).expanduser().resolve()}")


if __name__ == "__main__":
    main()
