#!/usr/bin/env python3
"""Match user-requested or local SFX files to timeline moments."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SFX_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg"}
TOKEN_GROUPS = {
    "whoosh": {"转场", "切换", "进入", "离开", "then", "now", "first"},
    "click": {"点击", "按钮", "打开", "工具", "界面", "click", "ui", "tap"},
    "impact": {"重点", "注意", "结论", "关键", "重要", "impact", "hit", "boom"},
    "digital": {"数据", "数字", "AI", "自动", "效率", "digital", "data", "tech"},
}


def tokens(text: str) -> set[str]:
    latin = {item.lower() for item in re.findall(r"[A-Za-z0-9]+", text)}
    chinese = set(re.findall(r"[\u4e00-\u9fff]{2,4}", text))
    return latin | chinese


def score(path: Path, text: str) -> int:
    file_tokens = tokens(path.stem.replace("_", " ").replace("-", " "))
    text_tokens = tokens(text)
    value = len(file_tokens & text_tokens) * 4
    for group in TOKEN_GROUPS.values():
        if file_tokens & group and text_tokens & group:
            value += 2
    return value


def match(project_dir: Path) -> None:
    timeline_path = project_dir / "timeline.json"
    audio_path = project_dir / "audio-mix.json"
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    audio_mix = json.loads(audio_path.read_text(encoding="utf-8")) if audio_path.is_file() else {}
    sfx_dir = project_dir / "audio" / "sfx"
    files = sorted(path for path in sfx_dir.glob("**/*") if path.is_file() and path.suffix.lower() in SFX_EXTENSIONS)
    requests = {str(item.get("scene_id")): item for item in audio_mix.get("requests", [])}
    uses = []

    for scene in timeline.get("scenes", []):
        scene_id = str(scene.get("id"))
        request = requests.get(scene_id)
        chosen: Path | None = None
        mode = "none"
        if request and request.get("source"):
            candidate = project_dir / str(request["source"])
            if candidate.is_file():
                chosen = candidate
                mode = "user-requested"
            else:
                raise SystemExit(f"用户指定的音效不存在：{candidate}")
        elif files:
            ranked = sorted(files, key=lambda path: score(path, f"{scene.get('keyword', '')} {scene.get('subtitle', '')}"), reverse=True)
            if ranked and score(ranked[0], f"{scene.get('keyword', '')} {scene.get('subtitle', '')}") > 0:
                chosen = ranked[0]
                mode = "automatic-filename-match"

        sfx = scene.setdefault("sfx", {})
        if chosen:
            relative = chosen.relative_to(project_dir).as_posix()
            duration = min(0.45, max(0.18, float(scene.get("duration", 0.3))))
            sfx.update({"source": relative, "duration": duration, "volume": 0.28, "match": mode, "peak_dbtp": -2.3})
            uses.append({"scene_id": scene_id, "source": relative, "start": float(scene.get("start", 0)), "duration": duration, "volume": 0.28, "match": mode})
        else:
            sfx.update({"source": "", "duration": 0, "match": "pending"})

    audio_mix["uses"] = uses
    audio_mix.setdefault("matching", {})["mode"] = "user-requested-or-local-sfx-filename-match"
    audio_path.write_text(json.dumps(audio_mix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已匹配音效：{len(uses)} 条")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Amu Cut 工程目录")
    args = parser.parse_args()
    match(Path(args.project).expanduser().resolve())


if __name__ == "__main__":
    main()
