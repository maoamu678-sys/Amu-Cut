#!/usr/bin/env python3
"""Match brief sound effects to speech cues and user directions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from discover_broll import download_file
from export import find_ffmpeg, has_audio_stream

EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
CUES = {
    "mouse click": ("点击", "点开", "按钮", "打开", "鼠标", "click", "tap", "界面"),
    "keyboard typing": ("打字", "输入", "键盘", "typing", "keyboard"),
    "page turn": ("翻页", "翻开", "书页", "page", "paper"),
    "short whoosh": ("切换", "转场", "翻转", "whoosh", "swipe"),
    "notification beep": ("提示音", "通知", "提醒", "notify", "beep"),
    "soft impact": ("重点", "关键", "结论", "重要", "impact", "hit"),
    "digital tick": ("数据", "自动", "效率", "工具", "digital", "tick"),
}


def cues(text):
    text = text.casefold()
    return [query for query, words in CUES.items() if any(w in text for w in words)]


def local_score(path, text):
    name = path.stem.casefold()
    words = set(re.findall(r"[a-z0-9]+", name))
    matches = words.intersection(re.findall(r"[a-z0-9]+", text.casefold()))
    return 2 * len(matches) + sum(q in cues(name) or bool(words.intersection(q.split())) for q in cues(text))


def online_candidates(query):
    params = urllib.parse.urlencode({"q": query, "license": "cc0", "page_size": 8})
    req = urllib.request.Request("https://api.openverse.org/v1/audio/?" + params,
                                 headers={"User-Agent": "AmuCut/0.4 (https://github.com/maoamu678-sys/Amu-Cut)"})
    with urllib.request.urlopen(req, timeout=15) as response:
        results = json.load(response).get("results", [])
    for item in results:
        if item.get("license") == "cc0" and item.get("category") not in {"music", "speech"}:
            yield {"download_url": item.get("url"), "source_url": item.get("foreign_landing_url"),
                   "creator": item.get("creator"), "license": "CC0", "license_url": item.get("license_url")}


def fetch_sound(record, project, ffmpeg):
    url = record.get("download_url") or ""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("需要可以直接下载音频的 HTTP(S) 地址")
    folder = project / "audio" / "downloads"
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(parsed.path).suffix.lower()
    name = hashlib.sha256(url.encode()).hexdigest()[:24]
    path = folder / (name + (suffix if suffix in EXTENSIONS else ".audio"))
    if not path.exists():
        download_file(url, path, 10_000_000)
    if not has_audio_stream(ffmpeg, path):
        path.unlink(missing_ok=True)
        raise ValueError("下载内容没有可解码的音轨")
    return path


# Times refer to the labelled moments in the first supplied demonstration.
REFERENCE_CUES = {
    "疑问": (2.38, 0.65),
    "突然转折": (3.27, 0.54),
    "心跳": (6.55, 0.64),
    "知识点": (9.58, 0.60),
    "单字强调": (13.55, 0.56),
}


def reference_excerpt(project, cue, ffmpeg):
    if cue not in REFERENCE_CUES or not ffmpeg:
        raise ValueError("参考落点或 FFmpeg 不可用")
    root = Path(__file__).resolve().parents[2]
    original = root / "projects/ai-work-efficiency/audio/references/reference-01.mp3"
    if not original.exists():
        raise ValueError("参考音轨缺失，请安装完整仓库")
    start, duration = REFERENCE_CUES[cue]
    folder = project / "audio" / "references" / "excerpts"
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / f"{cue}.wav"
    command = [ffmpeg, "-v", "error", "-y", "-ss", str(start), "-i", str(original),
               "-t", str(duration), "-af", f"afade=t=in:d=0.008,afade=t=out:st={duration-0.04}:d=0.04",
               "-c:a", "pcm_s16le", str(output)]
    subprocess.run(command, check=True)
    return output, {"reference": "reference-01.mp3", "offset": start, "length": duration, "cue": cue}


def match(project):
    timeline_path = project / "timeline.json"
    audio_path = project / "audio-mix.json"
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    mix = json.loads(audio_path.read_text(encoding="utf-8")) if audio_path.exists() else {}
    settings = mix.setdefault("matching", {})
    online = settings.get("online", True)
    files = sorted(p for p in (project / "audio" / "sfx").rglob("*")
                   if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in EXTENSIONS)
    requests = {str(r["scene_id"]): r for r in mix.get("requests", [])}
    previous = {str(r["scene_id"]): r for r in mix.get("uses", [])}
    ffmpeg = find_ffmpeg(project)
    uses, pending, searches = [], [], {}
    for scene in timeline.get("scenes", []):
        sid = str(scene["id"])
        request = requests.get(sid, {})
        text = scene.get("subtitle", "") + " " + scene.get("keyword", "")
        queries = cues(text)
        query = request.get("query") or next(iter(queries), "")
        sfx = scene.setdefault("sfx", {})
        sfx.update(source="", duration=0, match="none")
        if request.get("mute") or (settings.get("enabled", True) is False):
            continue
        path, credit, mode = None, {}, "user-requested"
        try:
            if request.get("source"):
                path = (project / request["source"]).resolve()
                if not path.is_file():
                    raise ValueError(f"指定文件不存在 {path.name}")
            elif request.get("reference_cue"):
                path, credit = reference_excerpt(project, request["reference_cue"], ffmpeg)
                mode = "reference-excerpt"
            elif request.get("download_url"):
                credit = {key: request[key] for key in ("download_url","source_url","creator","license") if key in request}
                if not ffmpeg:
                    raise ValueError("需要 FFmpeg 验证音频文件")
                path = fetch_sound(credit, project, ffmpeg)
            else:
                if files and not request.get("query"):
                    best = max(files, key=lambda p: local_score(p, text))
                    if local_score(best, text):
                        path, mode = best, "automatic-filename-match"
                if not path and settings.get("use_reference_cues") and not request.get("query"):
                    cue = next((label for label in REFERENCE_CUES if label in text), None)
                    if cue:
                        path, credit = reference_excerpt(project, cue, ffmpeg)
                        mode = "reference-excerpt"
                if not path and query and online:
                    if not ffmpeg:
                        raise ValueError("需要 FFmpeg 验证音频文件")
                    old = previous.get(sid, {})
                    if old.get("match") == "online" and old.get("query") == query and (project / old["source"]).is_file():
                        path, credit = project / old["source"], old["credit"]
                    else:
                        if query not in searches:
                            searches[query] = list(online_candidates(query))
                        for candidate in searches[query]:
                            try:
                                path = fetch_sound(candidate, project, ffmpeg)
                            except (ValueError, OSError) as exc:
                                print(f"{sid} 跳过候选音效 {exc}")
                                continue
                            credit = candidate
                            break
                    mode = "online"
                    if not path:
                        raise ValueError("没有可下载的匹配音效")
            if not path:
                continue
            start = float(request.get("start", scene.get("start", 0)))
            offset = float(request.get("source_start", 0))
            duration = float(request.get("duration", min(0.45, float(scene["duration"]))))
            volume = float(request.get("volume", 0.28))
            if not (start >= 0 and offset >= 0 and duration > 0 and 0 <= volume <= 1):
                raise ValueError("检查起点、截取时长和音量")
            if path.is_relative_to(project):
                path = path.relative_to(project)
            use = dict(scene_id=sid, source=str(path), start=start, source_start=offset,
                       duration=duration, volume=volume, match=mode, query=query, credit=credit)
            uses.append(use)
            sfx.update(use)
        except (OSError, ValueError) as exc:
            pending.append(dict(scene_id=sid, query=query, reason=str(exc)))
            sfx["match"] = "pending"
    settings["mode"] = "user-local-or-online"
    mix.update(uses=uses, pending=pending)
    for path, data in ((audio_path, mix), (timeline_path, timeline)):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已匹配 {len(uses)} 条音效，{len(pending)} 条待处理。")
    for row in pending:
        print(row["scene_id"], row["reason"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Amu Cut 工程目录")
    match(Path(parser.parse_args().project).expanduser().resolve())
