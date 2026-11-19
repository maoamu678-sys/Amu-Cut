# Amu Cut

属于 Amu Cut 的中文竖屏口播视频剪辑 Skill，同时包含基于 Three.js、Python 和 FFmpeg 的代码化视频工程执行层。

## 当前能力

- `tech-business-card`：科技、AI、工具和商业分析的紧凑卡片风。
- `finance-story`：财经、经济、人物和行业解释的叙事风。
- 口播结构整理、字幕可读性、语义 B-roll、声音整理、验收和交付状态记录。
- 人声优先、默认无背景音乐、已批准音效约 `-2.3 dBTP`、全屏 1–3 秒新语义 B-roll 和陌生人脸规避。
- 通过 `engine/` 生成可修改的 `timeline.json`、`scene.mjs`、B-roll 清单、音频混音说明、导出脚本和工程记录。

本项目提炼的是通用剪辑方法，不复制任何真实账号的头像、账号信息、Logo、独家文案或页面资产。

## 从 GitHub 调取

本仓库同时包含 Skill 规则和代码化剪辑执行层。其他使用者可以在支持 GitHub Skill 的工具中安装仓库：

```text
https://github.com/maoamu678-sys/Amu-Cut
```

安装后可以调用 `Amu Cut`。需要生成实际视频工程时，使用仓库中的 `engine/`，并准备自己的口播视频、SRT、B-roll 和音效素材。

## 目录

- `SKILL.md`：Skill 主规则。
- `references/account-style-profiles.md`：两套风格档案。
- `references/first-run-brief.md`：首次试跑单。
- `references/acceptance-checklist.md`：验收清单。
- `references/broll-exclusion-template.md`：B-roll 排除表。
- `references/project-status.md`：项目状态记录。
- `agents/openai.yaml`：展示名称和默认提示。
- `engine/`：Three.js 画面叠加、Python 时间线检查和 FFmpeg 导出入口。
- `projects/ai-work-efficiency/`：AI 工具提高工作效率的科技商业卡片风示例工程。

## 代码化剪辑流程

先准备一条口播 MP4 和匹配的 SRT，然后执行：

```bash
cd engine
npm install
python3 src/prepare_project.py \
  --input ../projects/ai-work-efficiency/input/talking-head.mp4 \
  --srt ../projects/ai-work-efficiency/input/talking-head.srt \
  --style tech-business-card \
  --output ../projects/ai-work-efficiency
python3 src/validate_project.py ../projects/ai-work-efficiency
```

工程会保留可修改的时间线和场景代码。完成 B-roll 与音效来源后，再使用 `export.py` 进入 FFmpeg 导出阶段。

## 开发方式

1. 先用一个真实项目试跑。
2. 用户作为项目经理确认模式、内容取舍和完整速度预览。
3. 根据反馈修改规则和参考文档。
4. 通过 GitHub 的正常流程记录版本和发布说明。

当前版本：`v0.3.0-dev`。
