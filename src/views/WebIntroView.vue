<script setup lang="ts">
import { ref } from "vue";

const gradientA = ref("#34d399");
const gradientB = ref("#3b82f6");
const waveSpeed = ref(16);
const sticker = ref("✨");

type Ripple = {
  id: number;
  x: number;
  y: number;
};

type PlacedSticker = {
  id: number;
  x: number;
  y: number;
  emoji: string;
};

const ripples = ref<Ripple[]>([]);
const placedStickers = ref<PlacedSticker[]>([]);

function handlePointerMove(event: MouseEvent) {
  const card = event.currentTarget as HTMLElement;
  const rect = card.getBoundingClientRect();
  const rippleId = Date.now() + Math.random();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  ripples.value.push({ id: rippleId, x, y });
  setTimeout(() => {
    ripples.value = ripples.value.filter((r) => r.id !== rippleId);
  }, 900);
}

function placeSticker(event: MouseEvent) {
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

      <h1>Sea Lantern</h1>
      <p class="subtitle">Web 版当前为介绍页（桌面端功能请下载客户端）</p>

      <div class="meta">
        <span>👤 创作者：allenzhang710901</span>
      </div>

      <div class="actions">
        <a class="btn primary" href="https://github.com/FPSZ/SeaLantern/releases" target="_blank" rel="noreferrer">点击下载</a>
        <a class="btn" href="https://github.com/FPSZ/SeaLantern" target="_blank" rel="noreferrer">GitHub</a>
      </div>

      <ul class="features">
        <li>✅ 服务器管理（导入/启动/停止）</li>
        <li>✅ 控制台、配置编辑、玩家管理</li>
        <li>✅ Mods/Plugins 搜索与安装（含依赖）</li>
        <li>✅ 多语言与个性化设置</li>
      </ul>

      <div class="customizer">
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
  display: grid;
  place-items: center;
  background: #071022;
  color: #e5f2ff;
}

.hero {
  position: relative;
  width: min(980px, 92vw);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 28px;
  overflow: hidden;
  backdrop-filter: blur(8px);
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

.subtitle { opacity: 0.92; }
.meta { margin: 10px 0 16px; }
.actions { display: flex; gap: 10px; margin-bottom: 14px; }
.features { margin: 0 0 16px; padding-left: 18px; line-height: 1.7; }

.customizer {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  align-items: center;
  font-size: 13px;
}

.btn {
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 10px;
  padding: 8px 12px;
  color: #fff;
  text-decoration: none;
  background: rgba(10, 18, 28, 0.35);
}
.btn.primary { background: rgba(52, 211, 153, 0.25); }

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
  .customizer { grid-template-columns: 1fr 1fr; }
}
</style>
