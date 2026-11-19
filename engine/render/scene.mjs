import * as THREE from "../node_modules/three/build/three.module.js";

const stage = document.querySelector("#stage");
const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(0, 1080, 1920, 0, -10, 10);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(1080, 1920, false);
renderer.setClearColor(0x000000, 0);
stage.appendChild(renderer.domElement);

const root = new THREE.Group();
scene.add(root);

function roundedPanel(width, height, color, opacity, radius = 24) {
  const shape = new THREE.Shape();
  const x = 0;
  const y = 0;
  shape.moveTo(x + radius, y);
  shape.lineTo(x + width - radius, y);
  shape.quadraticCurveTo(x + width, y, x + width, y + radius);
  shape.lineTo(x + width, y + height - radius);
  shape.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  shape.lineTo(x + radius, y + height);
  shape.quadraticCurveTo(x, y + height, x, y + height - radius);
  shape.lineTo(x, y + radius);
  shape.quadraticCurveTo(x, y, x + radius, y);
  const geometry = new THREE.ShapeGeometry(shape);
  const material = new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false });
  return new THREE.Mesh(geometry, material);
}

function textTexture(text, options = {}) {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  const fontSize = options.fontSize ?? 48;
  const fontWeight = options.fontWeight ?? 700;
  const fontFamily = options.fontFamily ?? "Arial, sans-serif";
  const padding = options.padding ?? 16;
  context.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
  const metrics = context.measureText(text);
  canvas.width = Math.ceil(metrics.width + padding * 2);
  canvas.height = Math.ceil(fontSize * 1.5 + padding * 2);
  context.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
  context.textBaseline = "middle";
  context.fillStyle = options.fill ?? "#ffffff";
  context.strokeStyle = options.stroke ?? "#15121f";
  context.lineWidth = options.strokeWidth ?? 8;
  context.lineJoin = "round";
  context.strokeText(text, padding, canvas.height / 2);
  context.fillText(text, padding, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return { texture, width: canvas.width, height: canvas.height };
}

function textSprite(text, options = {}) {
  const { texture, width, height } = textTexture(text, options);
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
  const sprite = new THREE.Sprite(material);
  const scale = options.scale ?? 1;
  sprite.scale.set(width * scale, height * scale, 1);
  return sprite;
}

function clearGroup() {
  while (root.children.length) {
    const child = root.children.pop();
    child.traverse?.((object) => {
      object.geometry?.dispose?.();
      object.material?.map?.dispose?.();
      object.material?.dispose?.();
    });
  }
}

function visibleSceneAt(time, project) {
  clearGroup();
  const style = project.style;
  const config = window.__AMU_STYLE_CONFIG__ ?? {};
  const accent = config.accentColor ?? (style === "finance-story" ? "#ff2f63" : "#f4c430");
  const panel = roundedPanel(936, 108, config.panelColor ?? "#13101b", 0.72, 28);
  panel.position.set(72, 112);
  root.add(panel);

  const label = textSprite(config.label ?? (style === "finance-story" ? "财经人物叙事" : "科技商业卡片"), {
    fontSize: 42,
    fill: "#ffffff",
    stroke: "#13101b",
    strokeWidth: 6,
    scale: 0.8,
  });
  label.position.set(170, 166, 1);
  root.add(label);

  const sceneData = project.scenes.find((item) => time >= item.start && time < item.start + item.duration);
  if (sceneData) {
    const subtitle = textSprite(sceneData.subtitle, {
      fontSize: 48,
      fill: "#ffffff",
      stroke: "#15121f",
      strokeWidth: 10,
      scale: 0.82,
    });
    subtitle.position.set(540, config.subtitleY ?? 1690, 1);
    root.add(subtitle);

    if (sceneData.keyword) {
      const card = roundedPanel(410, 112, accent, 0.94, 26);
      card.position.set(72, 270);
      root.add(card);
      const keyword = textSprite(sceneData.keyword, {
        fontSize: 46,
        fill: "#17121c",
        stroke: "#ffffff",
        strokeWidth: 0,
        scale: 0.86,
      });
      keyword.position.set(277, config.keywordY ?? 326, 1);
      root.add(keyword);
    }
  }
}

window.__AMU_READY__ = () => renderer.render(scene, camera);
window.__AMU_RENDER_AT__ = (time) => {
  const project = window.__AMU_PROJECT__;
  if (!project) return;
  visibleSceneAt(time, project);
  renderer.render(scene, camera);
};

window.__AMU_RENDER_AT__(0);
