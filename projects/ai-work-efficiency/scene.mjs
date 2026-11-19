// 这是示例工程的可编辑场景入口。
// 真实项目会由 engine/src/prepare_project.py 根据项目风格生成同结构文件。
export const projectStyle = "tech-business-card";
export const canvas = { width: 1080, height: 1920, fps: 30 };

export function getVisualConfig() {
  return {
    label: "科技商业卡片",
    panelColor: "#13101b",
    accentColor: "#f4c430",
    subtitleY: 1690,
    keywordY: 326,
  };
}

export function getSceneSpec(timeline) {
  return {
    style: projectStyle,
    canvas,
    scenes: timeline.scenes,
  };
}
