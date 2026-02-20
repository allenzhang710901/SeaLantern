<script setup lang="ts">
import { ref } from "vue";

const gradientA = ref("#34d399");
const gradientB = ref("#3b82f6");
const waveSpeed = ref(16);
const sticker = ref("✨");

const tutorialSteps = [
  "1. 下载客户端后创建/导入你的 Minecraft 服务器。",
  "2. 在首页一键启动，打开控制台查看日志与执行命令。",
  "3. 使用配置编辑、玩家管理、模组/插件下载完善运营。",
  "4. 在个性化里调整主题、背景、字体和语言。",
];

const screenshots = [
  "/screenshots/intro-1.svg",
  "/screenshots/intro-2.svg",
  "/screenshots/intro-3.svg",
  "/screenshots/intro-4.svg",
];

type Ripple = { id: number; x: number; y: number };
type PlacedSticker = { id: number; x: number; y: number; emoji: string };

const ripples = ref<Ripple[]>([]);
const placedStickers = ref<PlacedSticker[]>([]);

function handlePointerMove(event: MouseEvent) {
  const card = event.currentTarget as HTMLElement;
  const rect = card.getBoundingClientRect();
  const rippleId = Date.now() + Math.random();
  ripples.value.push({ id: rippleId, x: event.clientX - rect.left, y: event.clientY - rect.top });
  setTimeout(() => {
    ripples.value = ripples.value.filter((r) => r.id !== rippleId);
  }, 900);
}

function placeSticker(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (target.closest("button, input, select, a")) return;

  const card = event.currentTarget as HTMLElement;
  const rect = card.getBoundingClientRect();
  placedStickers.value.push({
    id: Date.now() + Math.random(),
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
    emoji: sticker.value,
  });
}

function clearStickers() {
  placedStickers.value = [];
}
</script>

<template>
  <main
    class="web-intro"
    :style="{
      '--g1': gradientA,
      '--g2': gradientB,
      '--wave-speed': `${waveSpeed}s`,
    }"
  >
    <section class="hero" @mousemove="handlePointerMove" @click="placeSticker">
      <div class="water-bg" />

      <header class="hero-header">
        <h1 class="hero-title">Sea Lantern</h1>
        <p class="subtitle">更现代、更流畅的 Minecraft 服务器管理体验</p>
        <div class="hero-tags"><span>桌面应用</span><span>Web 预览</span><span>开源项目</span></div>
        <div class="hero-metrics">
          <div class="metric"><strong>10+</strong><span>核心功能模块</span></div>
          <div class="metric"><strong>3</strong><span>分钟快速上手</span></div>
          <div class="metric"><strong>100%</strong><span>本地自主管理</span></div>
        </div>
        <p class="desc">
          Web 版当前以介绍与预览为主；完整能力（本地文件、进程管理、系统托盘等）请下载桌面端。
        </p>
        <div class="meta">👤 创作者：allenzhang710901</div>
      </header>

      <div class="actions">
        <a class="btn primary" href="https://github.com/FPSZ/SeaLantern/releases" target="_blank" rel="noreferrer">点击下载</a>
        <a class="btn" href="https://github.com/FPSZ/SeaLantern" target="_blank" rel="noreferrer">查看源码</a>
      </div>

      <section class="content-grid">
        <article class="panel">
          <h3>✨ 功能介绍</h3>
          <ul>
            <li>服务器创建、导入、启停与状态监控</li>
            <li>控制台实时日志和命令管理</li>
            <li>配置编辑、玩家管理、模组/插件下载</li>
            <li>多语言与个性化主题系统</li>
          </ul>
        </article>

        <article class="panel">
          <h3>🚀 快速教程</h3>
          <ol class="timeline">
            <li v-for="step in tutorialSteps" :key="step">{{ step }}</li>
          </ol>
        </article>
      </section>

      <section class="gallery">
        <h3>🖼️ 界面照片</h3>
        <div class="gallery-grid">
          <figure v-for="shot in screenshots" :key="shot" class="gallery-item">
            <img :src="shot" alt="Sea Lantern screenshot" loading="lazy" />
          </figure>
        </div>
      </section>

      <section class="customizer">
        <h3>🎨 外观自定义</h3>
        <div class="customizer-controls">
          <label>渐变色 A <input v-model="gradientA" type="color" /></label>
          <label>渐变色 B <input v-model="gradientB" type="color" /></label>
          <label>波动速度 <input v-model.number="waveSpeed" type="range" min="6" max="30" /></label>
          <label>
            小贴图
            <select v-model="sticker">
              <option>✨</option>
              <option>🌊</option>
              <option>🧭</option>
              <option>🪼</option>
              <option>🐟</option>
            </select>
          </label>
          <button class="btn" @click.stop="clearStickers">清空贴图</button>
        </div>
      </section>

      <span v-for="item in placedStickers" :key="item.id" class="sticker" :style="{ left: `${item.x}px`, top: `${item.y}px` }">
        {{ item.emoji }}
      </span>
      <span v-for="ripple in ripples" :key="ripple.id" class="ripple" :style="{ left: `${ripple.x}px`, top: `${ripple.y}px` }" />
    </section>
  </main>
</template>

<style scoped>
.web-intro {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 28px 0;
  background:
    radial-gradient(circle at 15% 12%, rgba(59, 130, 246, 0.18), transparent 26%),
    radial-gradient(circle at 85% 88%, rgba(16, 185, 129, 0.12), transparent 24%),
    #071022;
  color: #e5f2ff;
}

.hero {
  position: relative;
  width: min(1120px, 94vw);
  margin: 0 auto;
  border: 1px solid rgba(147, 197, 253, 0.44);
  border-radius: 24px;
  padding: 34px;
  overflow: hidden;
  backdrop-filter: blur(10px);
  background: linear-gradient(180deg, rgba(10, 20, 36, 0.76), rgba(6, 13, 24, 0.58));
  box-shadow: 0 28px 90px rgba(2, 6, 23, 0.5);
}

.water-bg {
  position: absolute;
  inset: -40%;
  background: radial-gradient(circle at 20% 30%, var(--g1), transparent 40%),
    radial-gradient(circle at 80% 70%, var(--g2), transparent 45%),
    linear-gradient(120deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.02));
  animation: flow var(--wave-speed) linear infinite;
  z-index: -1;
}

@keyframes flow {
  0% { transform: translate3d(-3%, -2%, 0) rotate(0deg); }
  50% { transform: translate3d(3%, 2%, 0) rotate(180deg); }
  100% { transform: translate3d(-3%, -2%, 0) rotate(360deg); }
}

.hero-title {
  margin: 0;
  font-size: clamp(36px, 4.2vw, 56px);
  letter-spacing: 0.6px;
  text-shadow: 0 4px 22px rgba(56, 189, 248, 0.28);
}
.subtitle { margin: 10px 0 0; opacity: 0.95; }
.hero-tags {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.hero-tags span {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(147, 197, 253, 0.45);
  background: rgba(30, 58, 95, 0.45);
}
.desc { margin-top: 10px; color: #c4d8f2; }
.meta { margin-top: 8px; }

.hero-metrics {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid rgba(147, 197, 253, 0.35);
  background: rgba(11, 27, 47, 0.45);
}

.metric strong {
  font-size: 20px;
  line-height: 1.2;
}

.metric span {
  font-size: 12px;
  color: #bfdbfe;
}

.actions { margin: 20px 0; display: flex; gap: 12px; flex-wrap: wrap; }
.btn {
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 12px;
  padding: 10px 14px;
  color: #fff;
  text-decoration: none;
  background: rgba(10, 18, 28, 0.35);
}
.btn.primary { background: linear-gradient(135deg, rgba(52, 211, 153, 0.38), rgba(59, 130, 246, 0.38)); }

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.panel {
  border: 1px solid rgba(147, 197, 253, 0.28);
  border-radius: 14px;
  padding: 16px;
  background: linear-gradient(180deg, rgba(13, 31, 55, 0.72), rgba(8, 16, 29, 0.46));
}

.panel h3,
.gallery h3,
.customizer h3 {
  margin: 0 0 10px;
}

.panel ul,
.panel ol {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
}

.timeline {
  list-style: none;
  padding-left: 0 !important;
}

.timeline li {
  position: relative;
  padding: 8px 0 8px 20px;
}

.timeline li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 16px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, #34d399, #38bdf8);
}

.timeline li::after {
  content: "";
  position: absolute;
  left: 3px;
  top: 26px;
  bottom: -8px;
  width: 2px;
  background: rgba(147, 197, 253, 0.25);
}

.timeline li:last-child::after {
  display: none;
}

.gallery {
  margin-top: 18px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.gallery-item {
  margin: 0;
  border: 1px solid rgba(147, 197, 253, 0.3);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(7, 15, 30, 0.55);
}

.gallery-item img {
  width: 100%;
  height: 150px;
  object-fit: cover;
  display: block;
  transition: transform 0.35s ease;
}

.gallery-item:hover img {
  transform: scale(1.045);
}

.customizer {
  margin-top: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 14px;
  background: rgba(9, 16, 28, 0.35);
}

.customizer-controls {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  align-items: center;
}

.ripple {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  transform: translate(-50%, -50%);
  animation: ripple 0.9s ease-out forwards;
  pointer-events: none;
}

@keyframes ripple {
  from { opacity: 0.8; transform: translate(-50%, -50%) scale(0.2); }
  to { opacity: 0; transform: translate(-50%, -50%) scale(9); }
}

.sticker {
  position: absolute;
  transform: translate(-50%, -50%);
  font-size: 22px;
  pointer-events: none;
}

@media (max-width: 900px) {
  .hero-metrics,
  .content-grid,
  .gallery-grid,
  .customizer-controls {
    grid-template-columns: 1fr;
  }
}
</style>
