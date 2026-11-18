# Amu Cut 风格档案

## 两种模式共用的口播基线

- 自然中近景为主，允许轻微推近；顶部可使用深色半透明信息栏。
- 单行白色描边字幕优先，关键词字卡保持克制并避开脸部、嘴部和关键动作。
- 默认不添加背景音乐。音效只服务于语义、节奏和转折，使用已批准音效时以约 `-2.3 dBTP` 作为峰值控制参考。
- 每条视频优先使用新的语义 B-roll，并维护已用画面排除表；复用旧画面时记录原因。
- B-roll 通常全屏呈现 1–3 秒，陌生人脸要避开、模糊或替换。

## 1. 科技商业卡片风

| 项目 | 规则 |
| --- | --- |
| 适用主题 | AI、科技、工具、商业分析、效率 |
| 主色 | 深紫、墨黑、白色 |
| 强调色 | 警示黄、亮紫 |
| 节奏 | 紧凑、直接、高信息密度 |
| 主体 | 自然中近景，人物下方或中央 |
| 字幕 | 单行白色描边字幕，关键词用黄/紫强调 |
| 字卡 | 短句、少量、跟随结论出现 |
| B-roll | 界面、数据、图表、产品、商业场景 |
| 音频 | 人声优先，默认无背景音乐；音效克制，跟随语义节奏 |

## 2. 财经人物叙事风

| 项目 | 规则 |
| --- | --- |
| 适用主题 | 财经、宏观经济、商业人物、行业和生活解释 |
| 主色 | 米白、白色、深灰 |
| 强调色 | 热粉、金色 |
| 节奏 | 亲近、清楚、有故事感 |
| 主体 | 人物优先，保持情绪和停顿 |
| 字幕 | 浅底深灰字，深底白字 |
| 字卡 | 强调数字、人物、因果和结论 |
| B-roll | 城市、行业、商品、人物关系、图表 |
| 音频 | 人声优先，默认无背景音乐；音效克制，跟随语义转折 |

## 共通边界

- 这是视觉语法参考，不是对任何真实账号的复制。
- 参考截图只用于提炼色彩、信息层级、构图和节奏。
- 不使用真实账号的头像、昵称、ID、页面截图、Logo 或独家文案。
- 字幕和字卡必须避开人物脸部、嘴部和关键动作。
- 每个视频建立新的语义 B-roll 排除记录。

## 配置示例

```yaml
project: Amu Cut
default_mode: ask_or_recommend
music: off_by_default
sfx: approved_only
sfx_peak_reference: "-2.3 dBTP"
caption: one_line_readable_face_safe
broll: fresh_semantic_first
broll_duration: 1-3s_fullscreen
broll_stranger_faces: avoid_or_blur
modes:
  tech-business-card:
    palette: [deep-purple, ink-black, white, warning-yellow]
    topics: [ai, technology, tools, business]
  finance-story:
    palette: [off-white, white, dark-gray, hot-pink, gold]
    topics: [finance, economy, people, industry]
```
