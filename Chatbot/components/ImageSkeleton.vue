<template>
  <div class="image-skeleton" :style="{ width: width, height: height }">
    <div class="skeleton-shimmer"></div>
    <div class="skeleton-icon">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        class="w-12 h-12"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    </div>
    <div class="skeleton-text" v-if="showText">
      {{ loadingText }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const props = defineProps({
  width: {
    type: String,
    default: "16rem", // 对应 w-64
  },
  height: {
    type: String,
    default: "16rem", // 对应 h-64
  },
  loadingText: {
    type: String,
    default: "图片生成中...",
  },
  showText: {
    type: Boolean,
    default: true,
  },
});

const dots = ref("");
const dotInterval = ref(null);

onMounted(() => {
  // 添加动态省略号效果
  dotInterval.value = setInterval(() => {
    if (dots.value.length >= 3) {
      dots.value = "";
    } else {
      dots.value += ".";
    }
  }, 500);
});

onUnmounted(() => {
  if (dotInterval.value) {
    clearInterval(dotInterval.value);
  }
});
</script>

<script>
import { onUnmounted } from "vue";
</script>

<style scoped>
.image-skeleton {
  position: relative;
  background: linear-gradient(90deg, #e0e7ef 0%, #f0f4f8 50%, #e0e7ef 100%);
  background-size: 200% 100%;
  border-radius: 0.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.skeleton-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.5),
    transparent
  );
  animation: shimmer 2s infinite;
}

.skeleton-icon {
  color: #94a3b8;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  z-index: 1;
}

.skeleton-text {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
  z-index: 1;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 暗色模式支持 */
@media (prefers-color-scheme: dark) {
  .image-skeleton {
    background: linear-gradient(90deg, #1e293b 0%, #334155 50%, #1e293b 100%);
  }

  .skeleton-shimmer {
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.1),
      transparent
    );
  }

  .skeleton-icon {
    color: #475569;
  }

  .skeleton-text {
    color: #94a3b8;
  }
}
</style>
