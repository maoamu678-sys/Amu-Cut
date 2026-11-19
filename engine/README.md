# Amu Cut Motion Engine

这是 Amu Cut 的代码化剪辑执行层。它把 Skill 中的剪辑规则转换成可编辑的视频工程文件，并根据当前项目动态检索 B-roll、识别字幕和匹配音效。

## 分工

- Python 读取 SRT，生成 `timeline.json`，检查时间码、字幕重叠、画面安全区和音频规则。
- 没有 SRT 时，Python 调用本地 Whisper 自动生成中文字幕。
- `discover_broll.py` 按每条字幕语义从 Wikimedia Commons 检索和下载新的 B-roll，并保存来源、许可证和本地路径。
- `match_sfx.py` 按字幕关键词和音效文件名匹配独立音效，也接受 `audio-mix.json` 的用户指定。
- Three.js 根据 `timeline.json` 渲染科技商业卡片风的顶部信息栏、关键词字卡和字幕层。
- FFmpeg 负责把原始口播、动态 B-roll、音效和 Three.js 透明叠加层合成为竖屏 MP4。
- 项目目录保留原始素材清单、音频混音说明和修改记录，方便继续调整。

## 依赖

需要 Node.js 18 或更高版本、Python 3.9 或更高版本、Google Chrome 或 Chromium、FFmpeg，以及没有 SRT 时使用的 `openai-whisper` Python 包。

在仓库根目录执行：

```bash
cd engine
npm install
```

如果系统没有 FFmpeg，`export.py` 会直接报告缺少的依赖和安装提示。项目也会优先使用 `ffmpeg-static` 提供的本地二进制文件。

叠加层渲染默认使用 macOS 的 Google Chrome。其他路径可以通过 `AMU_BROWSER_EXECUTABLE` 指定。

## 从视频和字幕生成工程

```bash
python3 src/prepare_project.py \
  --input ../projects/ai-work-efficiency/input/talking-head.mp4 \
  --srt ../projects/ai-work-efficiency/input/talking-head.srt \
  --style tech-business-card \
  --output ../projects/ai-work-efficiency
```

没有 SRT 时可以省略 `--srt`，引擎会调用本地 Whisper：

```bash
python3 src/prepare_project.py \
  --input ../projects/ai-work-efficiency/input/talking-head.mp4 \
  --style tech-business-card \
  --output ../projects/ai-work-efficiency
```

生成后会得到：

- `timeline.json`
- `scene.mjs`
- `broll-sources.csv`
- `audio-mix.json`
- `export.py`
- `project.md`

动态素材处理：

```bash
python3 src/discover_broll.py ../projects/ai-work-efficiency
python3 src/match_sfx.py ../projects/ai-work-efficiency
```

## 检查工程

```bash
python3 src/validate_project.py ../projects/ai-work-efficiency
```

检查结果会明确区分通过、警告和阻断项。自动检查通过之后，还要进行完整速度预览和人工确认。

## 导出视频

```bash
python3 src/export.py \
  ../projects/ai-work-efficiency \
  --input ../projects/ai-work-efficiency/input/talking-head.mp4 \
  --with-overlay \
  --output ../projects/ai-work-efficiency/output/amu-cut-preview.mp4
```

用户提供的 B-roll URL 和音效要求优先级高于自动匹配。完整参考音轨保存在 `audio/references/`，用于风格参考或用户指定片段选择。`broll-sources.csv` 会记录网络来源、许可证和本地文件。自动检索没有找到合适素材时，工程会保留待处理状态并报告原因。
