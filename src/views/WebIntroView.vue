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
        <h1>Sea Lantern</h1>
        <p class="subtitle">更现代、更流畅的 Minecraft 服务器管理体验</p>
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
          <h3>功能介绍</h3>
          <ul>
            <li>服务器创建、导入、启停与状态监控</li>
            <li>控制台实时日志和命令管理</li>
            <li>配置编辑、玩家管理、模组/插件下载</li>
            <li>多语言与个性化主题系统</li>
          </ul>
        </article>

        <article class="panel">
          <h3>快速教程</h3>
          <ol>
            <li v-for="step in tutorialSteps" :key="step">{{ step }}</li>
          </ol>
        </article>
      </section>

      <section class="gallery">
        <h3>界面照片</h3>
        <div class="gallery-grid">
          <figure v-for="shot in screenshots" :key="shot" class="gallery-item">
            <img :src="shot" alt="Sea Lantern screenshot" loading="lazy" />
          </figure>
        </div>
      </section>

      <section class="customizer">
        <h3>外观自定义</h3>
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
  padding: 24px 0;
  background: #071022;
  color: #e5f2ff;
}

.hero {
  position: relative;
  width: min(1100px, 94vw);
  margin: 0 auto;
  border: 1px solid rgba(147, 197, 253, 0.35);
  border-radius: 20px;
  padding: 28px;
  overflow: hidden;
  backdrop-filter: blur(8px);
  box-shadow: 0 24px 80px rgba(2, 6, 23, 0.45);
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

.hero-header h1 { margin: 0; }
.hero-header h1 {
  font-size: clamp(32px, 4vw, 52px);
  letter-spacing: 0.5px;
}
.subtitle { margin: 8px 0 0; opacity: 0.92; }
.desc { margin-top: 10px; color: #c4d8f2; }
.meta { margin-top: 8px; }

.actions { margin: 16px 0; display: flex; gap: 10px; flex-wrap: wrap; }
.btn {
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 10px;
  padding: 8px 12px;
  color: #fff;
  text-decoration: none;
  background: rgba(10, 18, 28, 0.35);
}
.btn.primary { background: rgba(52, 211, 153, 0.25); }

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.panel {
  border: 1px solid rgba(147, 197, 253, 0.28);
  border-radius: 12px;
  padding: 14px;
  background: linear-gradient(180deg, rgba(10, 21, 38, 0.72), rgba(9, 16, 28, 0.45));
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

.gallery {
  margin-top: 14px;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.gallery-item {
  margin: 0;
  border: 1px solid rgba(147, 197, 253, 0.3);
  border-radius: 10px;
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
  transform: scale(1.03);
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
  .content-grid,
  .gallery-grid,
  .customizer-controls {
    grid-template-columns: 1fr;
  }
}
</style>
