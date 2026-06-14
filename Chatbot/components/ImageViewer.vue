<template>
  <div class="image-viewer-wrapper">
    <span ref="trigger" class="image-viewer-trigger">
      <slot>
        <img :src="src" class="image-viewer-thumb" :alt="alt" />
      </slot>
    </span>
    <transition name="viewer-fade">
      <div
        v-if="visible"
        class="image-viewer-modal"
        @mousedown="startDrag"
        @wheel.prevent="onWheel"
        @click.self="closeViewer"
        tabindex="0"
        @keydown.esc="closeViewer"
      >
        <div
          class="image-viewer-content"
          :style="contentStyle"
          ref="imgContainer"
        >
          <img :src="src" :alt="alt" draggable="false" />
        </div>
        <button class="viewer-close" @click="closeViewer"></button>
        <div class="viewer-controls">
          <button @click="zoomIn">＋</button>
          <button @click="zoomOut">－</button>
          <button @click="reset">重置</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const isZooming = ref(false);
const imgContainer = ref(null);

const props = defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: "" },
});

const visible = ref(false);
const scale = ref(1);
const pos = ref({ x: 0, y: 0 });
const dragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const imgStart = ref({ x: 0, y: 0 });
const contentStyle = computed(() => {
  return {
    transform: `translate(${pos.value.x}px, ${pos.value.y}px) scale(${scale.value})`,
    transition:
      dragging.value || isZooming.value
        ? "none"
        : "transform 0.2s cubic-bezier(.4,2,.3,1)",
  };
});

const openViewer = () => {
  visible.value = true;
  scale.value = 1;
  pos.value = { x: 0, y: 0 };
  setTimeout(() => {
    imgContainer.value?.focus();
  }, 10);
};

// 自动为插槽内容绑定点击事件
import { onMounted, onBeforeUnmount } from "vue";
const trigger = ref(null);
let clickHandler = null;
onMounted(() => {
  clickHandler = (e) => {
    isZooming.value = true;
    clearTimeout(onWheel._timer);
    onWheel._timer = setTimeout(() => {
      isZooming.value = false;
    }, 40); // 40ms后恢复动画，体验更丝滑
    // 只在未弹出预览时响应
    if (!visible.value) openViewer();
  };
  if (trigger.value) {
    trigger.value.addEventListener("click", clickHandler);
  }
});
onBeforeUnmount(() => {
  if (trigger.value && clickHandler) {
    trigger.value.removeEventListener("click", clickHandler);
  }
});
const closeViewer = () => {
  visible.value = false;
};
const ZOOM_STEP = 0.2; // 按钮缩放步进
const zoomIn = () => {
  scale.value = Math.min(scale.value + ZOOM_STEP, 3);
};
const zoomOut = () => {
  scale.value = Math.max(scale.value - ZOOM_STEP, 0.2);
};

const reset = () => {
  scale.value = 1;
  pos.value = { x: 0, y: 0 };
};
const onWheel = (e) => {
  // 丝滑缩放，缩放以图片容器中心为缩放中心，滚轮缩放时 transition 始终为 none
  const ZOOM_SENSITIVITY = 0.0025;
  const prevScale = scale.value;
  let newScale = prevScale * (1 + e.deltaY * ZOOM_SENSITIVITY);
  newScale = Math.max(0.2, Math.min(3, newScale));
  const imgEl = imgContainer.value.querySelector("img");
  if (!imgEl) return;
  // 获取容器中心点坐标
  const containerRect = imgContainer.value.getBoundingClientRect();
  const centerX = containerRect.left + containerRect.width / 2;
  const centerY = containerRect.top + containerRect.height / 2;
  // 图片当前中心点坐标
  const imgRect = imgEl.getBoundingClientRect();
  const imgCenterX = imgRect.left + imgRect.width / 2;
  const imgCenterY = imgRect.top + imgRect.height / 2;
  // 计算缩放后 pos 的偏移，使图片视觉中心保持在容器中心
  const dx = (imgCenterX - centerX) * (newScale / prevScale - 1);
  const dy = (imgCenterY - centerY) * (newScale / prevScale - 1);
  pos.value.x -= dx;
  pos.value.y -= dy;
  scale.value = newScale;
  isZooming.value = true;
  clearTimeout(onWheel._timer);
  onWheel._timer = setTimeout(() => {
    isZooming.value = false;
  }, 200);
};

const startDrag = (e) => {
  dragging.value = true;
  dragStart.value = { x: e.clientX, y: e.clientY };
  imgStart.value = { ...pos.value };
  window.addEventListener("mousemove", onDrag);
  window.addEventListener("mouseup", stopDrag);
};
const onDrag = (e) => {
  if (!dragging.value) return;
  const dx = e.clientX - dragStart.value.x;
  const dy = e.clientY - dragStart.value.y;
  pos.value = {
    x: imgStart.value.x + dx,
    y: imgStart.value.y + dy,
  };
};
const stopDrag = () => {
  dragging.value = false;
  window.removeEventListener("mousemove", onDrag);
  window.removeEventListener("mouseup", stopDrag);
};

// const contentStyle = computed(() => ({
//   transform: `translate(${pos.value.x}px, ${pos.value.y}px) scale(${scale.value})`,
//   transition: dragging.value
//     ? "none"
//     : "transform 0.2s cubic-bezier(.4,2,.3,1)",
// }));
</script>

<style scoped>
.image-viewer-wrapper {
  display: inline-block;
}
.image-viewer-thumb {
  cursor: pointer;
  max-width: 100%;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.2s;
}
.image-viewer-thumb:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
}
.viewer-fade-enter-active,
.viewer-fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 2, 0.3, 1);
}
.viewer-fade-enter-from,
.viewer-fade-leave-to {
  opacity: 0;
}
.image-viewer-modal {
  position: fixed;
  z-index: 9999;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: modal-in 0.3s cubic-bezier(0.4, 2, 0.3, 1);
}
@keyframes modal-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.image-viewer-content {
  outline: none;
  max-width: 80vw;
  max-height: 80vh;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
  cursor: grab;
  user-select: none;
  transition: box-shadow 0.2s;
}
.image-viewer-content img {
  display: block;
  max-width: 100%;
  max-height: 100%;
  pointer-events: none;
}
.viewer-close {
  position: absolute;
  top: 32px;
  right: 48px;
  font-size: 2rem;
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  z-index: 10;
  transition: color 0.2s;
}
.viewer-close:hover {
  color: #ff5252;
}
.viewer-controls {
  position: absolute;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 16px;
  z-index: 10;
}
.viewer-controls button {
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: background 0.2s;
}
.viewer-controls button:hover {
  background: #e0e0e0;
}
@media (max-width: 600px) {
  .image-viewer-content {
    max-width: 96vw;
    max-height: 60vh;
  }
  .viewer-close {
    top: 16px;
    right: 16px;
  }
  .viewer-controls {
    bottom: 16px;
  }
}
</style>
