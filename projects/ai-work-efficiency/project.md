# Amu Cut 工程记录

## 工程目的

制作一条关于 AI 工具如何提高工作效率的中文竖屏口播视频。

## 当前方案

- 剪辑模式：科技商业卡片风
- 画布：1080x1920，30fps
- 人声：优先
- 背景音乐：默认关闭
- 音效：只用于语义、节奏和转折，峰值参考约 -2.3 dBTP
- B-roll：根据每条口播语义联网检索新的画面，单段全屏通常 1–3 秒
- 陌生人脸：避开、模糊或替换
- 字幕：用户提供 SRT 时优先使用，缺少 SRT 时使用本地 Whisper 自动生成
- 音效：支持按文件名自动匹配，也支持在 `audio-mix.json` 中按场景指定

## 工程文件

- `timeline.json`：时间、字幕、关键词、B-roll 和音效位置
- `scene.mjs`：Three.js 场景入口
- `broll-sources.csv`：B-roll 来源和排除记录
- `audio-mix.json`：人声、音效、背景音乐和用户覆盖规则
- `audio/references/`：从用户提供的参考视频提取出的声音风格参考
- `audio/sfx/`：用户希望自动匹配的独立音效文件
- `export.py`：FFmpeg 导出入口

## 动态素材命令

```bash
python3 ../../engine/src/discover_broll.py .
python3 ../../engine/src/match_sfx.py .
python3 ../../engine/src/validate_project.py .
```

`discover_broll.py` 会按字幕语义搜索 Wikimedia Commons，并把来源、下载地址和许可证写入 `broll-sources.csv`。用户手动提供的素材记录优先级更高。

参考视频提取出的完整音轨用于声音风格参考。需要加入成片时，在 `audio-mix.json` 的 `requests` 中指定音效文件和场景。

## 状态

- 自动检查：待执行
- 完整速度预览：待执行
- 人工确认：待执行
- 导出：待执行
