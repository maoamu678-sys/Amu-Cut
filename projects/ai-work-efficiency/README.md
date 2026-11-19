# AI 工具提高工作效率示例工程

这是 Amu Cut 的第一份代码化剪辑工程模板，使用 `tech-business-card` 科技商业卡片风。

把一条真实的竖屏口播 MP4 放入 `input/`。有 SRT 时一起放入，没有 SRT 时让本地 Whisper 自动处理字幕。

有 SRT 时运行：

```bash
cd ../../engine
python3 src/prepare_project.py \
  --input ../projects/ai-work-efficiency/input/talking-head.mp4 \
  --srt ../projects/ai-work-efficiency/input/talking-head.srt \
  --style tech-business-card \
  --output ../projects/ai-work-efficiency
```

没有 SRT 时运行：

```bash
cd ../../engine
python3 src/prepare_project.py \
  --input ../projects/ai-work-efficiency/input/talking-head.mp4 \
  --style tech-business-card \
  --output ../projects/ai-work-efficiency
```

工程生成后，按字幕语义联网检索 B-roll，并匹配用户提供的音效：

```bash
python3 src/discover_broll.py ../projects/ai-work-efficiency
python3 src/match_sfx.py ../projects/ai-work-efficiency
python3 src/validate_project.py ../projects/ai-work-efficiency
```

最后进入预览和导出。用户指定的素材和音效可以覆盖自动匹配结果。
