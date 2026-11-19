# Amu Cut Motion Engine

这是 Amu Cut 的代码化剪辑执行层。它把 Skill 中的剪辑规则转换成可编辑的视频工程文件。

## 分工

- Python 读取 SRT，生成 `timeline.json`，检查时间码、字幕重叠、画面安全区和音频规则。
- Three.js 根据 `timeline.json` 渲染科技商业卡片风的顶部信息栏、关键词字卡和字幕层。
- FFmpeg 负责把原始口播、音效和 Three.js 透明叠加层合成为竖屏 MP4。
- 项目目录保留原始素材清单、音频混音说明和修改记录，方便继续调整。

## 依赖

需要 Node.js 18 或更高版本、Python 3.9 或更高版本、Google Chrome 或 Chromium 和 FFmpeg。

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

生成后会得到：

- `timeline.json`
- `scene.mjs`
- `broll-sources.csv`
- `audio-mix.json`
- `export.py`
- `project.md`

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

当前第一版已经把工程输入、时间线、Three.js 字幕和字卡叠加层、FFmpeg 合成接口连接起来。B-roll 的具体素材路径写在 `broll-sources.csv`，需要在真实项目中补齐后再进入导出。
