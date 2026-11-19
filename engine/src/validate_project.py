#!/usr/bin/env python3
"""Validate an Amu Cut project without claiming visual acceptance."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(project_dir: Path) -> tuple[list[str], list[str], list[str]]:
    passed: list[str] = []
    warnings: list[str] = []
    blocked: list[str] = []

    timeline_path = project_dir / "timeline.json"
    if not timeline_path.is_file():
        return [], [], [f"缺少 {timeline_path}"]

    try:
        timeline = load_json(timeline_path)
    except json.JSONDecodeError as exc:
        return [], [], [f"timeline.json 不是有效 JSON：{exc}"]

    if timeline.get("format") == {"width": 1080, "height": 1920, "fps": 30, "pixelFormat": "yuv420p"}:
        passed.append("竖屏输出规格为 1080x1920 / 30fps")
    else:
        blocked.append("输出规格不是 Amu Cut 默认的 1080x1920 / 30fps")

    if timeline.get("style") in {"tech-business-card", "finance-story"}:
        passed.append(f"剪辑模式有效：{timeline['style']}")
    else:
        blocked.append("剪辑模式无效")

    source = timeline.get("source", {})
    for key in ("video", "srt"):
        if not source.get(key) or not (project_dir / source[key]).is_file():
            blocked.append(f"找不到 source.{key} 指向的文件")
    if not blocked or all("source." not in item for item in blocked):
        passed.append("源视频和字幕文件存在")

    scenes = timeline.get("scenes", [])
    if not scenes:
        blocked.append("时间线没有场景")
    else:
        previous_end = -1.0
        for scene in scenes:
            start = float(scene.get("start", -1))
            duration = float(scene.get("duration", -1))
            end = start + duration
            if start < 0 or duration <= 0:
                blocked.append(f"场景 {scene.get('id', '?')} 的时间无效")
            if start < previous_end:
                blocked.append(f"场景 {scene.get('id', '?')} 与前一个场景重叠")
            subtitle = str(scene.get("subtitle", "")).strip()
            if len(subtitle) > 28:
                warnings.append(f"场景 {scene.get('id', '?')} 字幕较长，需要完整速度预览确认可读性")
            previous_end = max(previous_end, end)
        passed.append(f"时间线检查完成，共 {len(scenes)} 个口播场景")

    audio = timeline.get("audio", {})
    if audio.get("music") == "off":
        passed.append("背景音乐默认关闭")
    else:
        warnings.append("工程打开了背景音乐，需要确认这是用户明确要求")
    if audio.get("approvedSfxPeakDbtp") == -2.3:
        passed.append("音效峰值参考为约 -2.3 dBTP")
    else:
        warnings.append("音效峰值参考未使用约 -2.3 dBTP")

    broll_policy = timeline.get("brollPolicy", {})
    if broll_policy.get("freshBatch") is True:
        passed.append("工程要求建立新的语义 B-roll 批次")
    if broll_policy.get("strangerFaces") == "avoid-blur-or-replace":
        passed.append("工程包含陌生人脸处理规则")

    broll_file = project_dir / "broll-sources.csv"
    if not broll_file.is_file():
        blocked.append("缺少 B-roll 来源清单")
    elif "# Fill this file" in broll_file.read_text(encoding="utf-8"):
        warnings.append("B-roll 来源清单仍是模板，真实导出前需要补齐")
    else:
        passed.append("B-roll 来源清单存在")

    return passed, warnings, blocked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".")
    args = parser.parse_args()
    passed, warnings, blocked = validate(Path(args.project).expanduser().resolve())
    print("通过")
    for item in passed:
        print(f"  ✓ {item}")
    print("警告")
    for item in warnings:
        print(f"  ! {item}")
    print("阻断")
    for item in blocked:
        print(f"  ✗ {item}")
    raise SystemExit(1 if blocked else 0)


if __name__ == "__main__":
    main()
