#!/usr/bin/env python3
"""Search and download fresh semantic B-roll for an Amu Cut project."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_URL = "https://commons.wikimedia.org/w/api.php"
IMAGE_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
VIDEO_EXTENSIONS = {"video/mp4": ".mp4", "video/webm": ".webm"}


def request_json(params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "AmuCut/0.4 semantic-broll-search"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def clean_query(text: str, style: str) -> str:
    latin = re.findall(r"[A-Za-z0-9][A-Za-z0-9 -]{1,30}", text)
    chinese = re.sub(r"[^\u4e00-\u9fff]", " ", text).strip()
    style_words = (
        "artificial intelligence technology workplace productivity"
        if style == "tech-business-card"
        else "finance economy business people industry"
    )
    parts = [style_words]
    if latin:
        parts.append(latin[0].strip())
    if chinese:
        parts.append(chinese[:18])
    return " ".join(parts)


def extension_for(info: dict[str, Any]) -> str:
    mime = str(info.get("mime", "")).lower()
    if mime in IMAGE_EXTENSIONS:
        return IMAGE_EXTENSIONS[mime]
    if mime in VIDEO_EXTENSIONS:
        return VIDEO_EXTENSIONS[mime]
    suffix = Path(urllib.parse.urlparse(str(info.get("url", ""))).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm"} else ".bin"


def license_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key, {})
    return str(value.get("value", "")).replace("\n", " ").strip()


def search_commons(query: str, limit: int) -> list[dict[str, Any]]:
    payload = request_json(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata|mediatype",
            "iiurlwidth": 1920,
            "format": "json",
            "formatversion": 2,
        }
    )
    candidates = []
    for page in payload.get("query", {}).get("pages", []):
        image_info = (page.get("imageinfo") or [{}])[0]
        mime = str(image_info.get("mime", "")).lower()
        if mime not in IMAGE_EXTENSIONS and mime not in VIDEO_EXTENSIONS:
            continue
        metadata = image_info.get("extmetadata") or {}
        candidates.append(
            {
                "title": page.get("title", ""),
                "source_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(str(page.get('title', '')).replace(' ', '_'))}",
                "download_url": image_info.get("thumburl") or image_info.get("url"),
                "mime": mime,
                "size": int(image_info.get("size") or 0),
                "license": license_value(metadata, "LicenseShortName") or "Wikimedia Commons license",
                "artist": license_value(metadata, "Artist"),
            }
        )
    return candidates


def download_file(url: str, target: Path, max_bytes: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "AmuCut/0.4 semantic-broll-download"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content_length = int(response.headers.get("Content-Length") or 0)
        if content_length > max_bytes:
            raise ValueError(f"文件超过 {max_bytes} 字节限制")
        total = 0
        with target.open("wb") as output:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"文件超过 {max_bytes} 字节限制")
                output.write(chunk)


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(line for line in stream if not line.startswith("#")))


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "scene_id",
        "query",
        "source_url",
        "download_url",
        "license",
        "local_path",
        "role",
        "used",
        "reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def discover(project_dir: Path, per_scene: int, max_bytes: int, dry_run: bool) -> None:
    timeline_path = project_dir / "timeline.json"
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    broll_dir = project_dir / "assets" / "broll"
    broll_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = project_dir / "broll-sources.csv"
    existing = load_rows(manifest_path)
    rows: list[dict[str, str]] = []

    for scene_index, scene in enumerate(timeline.get("scenes", []), start=1):
        scene_id = str(scene.get("id", f"scene-{scene_index:03d}"))
        broll = scene.setdefault("broll", {})
        query = str(broll.get("query") or clean_query(str(scene.get("subtitle", "")), timeline.get("style", "tech-business-card")))
        preserved = [row for row in existing if row.get("scene_id") == scene_id and (row.get("used") == "user" or row.get("local_path"))]
        if preserved:
            selected = preserved[0]
            if selected.get("used") == "user" and not selected.get("local_path") and selected.get("download_url") and not dry_run:
                suffix = extension_for({"url": selected["download_url"]})
                digest = hashlib.sha1(f"{scene_id}:{selected['download_url']}".encode("utf-8")).hexdigest()[:10]
                target = broll_dir / f"{scene_id}-user-{digest}{suffix}"
                try:
                    if not target.is_file():
                        download_file(selected["download_url"], target, max_bytes)
                    selected["local_path"] = f"assets/broll/{target.name}"
                except (OSError, ValueError, urllib.error.URLError) as exc:
                    print(f"  用户指定素材下载失败：{exc}")
            rows.extend(preserved)
            status = "user-selected" if selected.get("local_path") else "user-pending"
            broll.update({"query": query, "source": selected.get("source_url", ""), "local_path": selected.get("local_path", ""), "duration": float(broll.get("duration") or 1.5), "status": status})
            continue

        print(f"{scene_id} 查询：{query}")
        if dry_run:
            rows.append({"scene_id": scene_id, "query": query, "role": "semantic-fullscreen", "used": "pending", "reason": "dry-run，尚未下载"})
            continue

        candidates = search_commons(query, max(per_scene * 3, 3))
        selected_count = 0
        for candidate in candidates:
            if selected_count >= per_scene:
                break
            if not candidate.get("download_url") or candidate.get("size", 0) > max_bytes:
                continue
            suffix = extension_for(candidate)
            digest = hashlib.sha1(f"{scene_id}:{candidate['download_url']}".encode("utf-8")).hexdigest()[:10]
            target = broll_dir / f"{scene_id}-{digest}{suffix}"
            local_path = f"assets/broll/{target.name}"
            try:
                if not target.is_file():
                    download_file(str(candidate["download_url"]), target, max_bytes)
            except (OSError, ValueError, urllib.error.URLError) as exc:
                print(f"  跳过 {candidate.get('title', '')}：{exc}")
                continue
            used = "yes" if selected_count == 0 else "no"
            rows.append(
                {
                    "scene_id": scene_id,
                    "query": query,
                    "source_url": str(candidate["source_url"]),
                    "download_url": str(candidate["download_url"]),
                    "license": f"{candidate['license']} {candidate.get('artist', '')}".strip(),
                    "local_path": local_path,
                    "role": "semantic-fullscreen",
                    "used": used,
                    "reason": "按字幕语义从 Wikimedia Commons 动态检索",
                }
            )
            if selected_count == 0:
                broll.update({"query": query, "source": str(candidate["source_url"]), "local_path": local_path, "duration": min(3.0, max(1.0, float(scene.get("duration", 1.5)))), "status": "downloaded"})
            selected_count += 1
        if selected_count == 0:
            rows.append({"scene_id": scene_id, "query": query, "role": "semantic-fullscreen", "used": "pending", "reason": "没有找到可下载的候选素材"})
            broll.update({"query": query, "status": "pending"})

    timeline["brollPolicy"].update(
        {
            "sourceMode": "online-search-with-attribution",
            "provider": "wikimedia-commons",
            "userUrlsOverrideAutomaticSearch": True,
            "downloadFreshBatch": True,
        }
    )
    timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_rows(manifest_path, rows)
    print(f"已更新 B-roll 清单：{manifest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Amu Cut 工程目录")
    parser.add_argument("--per-scene", type=int, default=1, help="每个场景下载的候选数量")
    parser.add_argument("--max-bytes", type=int, default=25_000_000, help="单个素材最大字节数")
    parser.add_argument("--dry-run", action="store_true", help="只生成查询，不下载")
    args = parser.parse_args()
    discover(Path(args.project).expanduser().resolve(), args.per_scene, args.max_bytes, args.dry_run)


if __name__ == "__main__":
    main()
