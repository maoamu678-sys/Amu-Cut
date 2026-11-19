# AI 工具提高工作效率示例工程

这是 Amu Cut 的第一份代码化剪辑工程模板，使用 `tech-business-card` 科技商业卡片风。

把一条真实的竖屏口播 MP4 和匹配的 SRT 放入 `input/`，再运行：

```bash
cd ../../engine
python3 src/prepare_project.py \
  --input ../projects/ai-work-efficiency/input/talking-head.mp4 \
  --srt ../projects/ai-work-efficiency/input/talking-head.srt \
  --style tech-business-card \
  --output ../projects/ai-work-efficiency
```

工程生成后，先执行自动检查，再补充 `broll-sources.csv` 和音效来源，最后进入预览和导出。
