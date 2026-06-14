<template>
  <div class="letter-container">
    <!-- 信封 -->
    <!-- <div
      class="envelope float"
      ref="envelopeRef"
      @click="openEnvelope"
      v-if="!isOpened"
    >
      <div class="envelope-flap" ref="flapRef"></div>
      <div class="envelope-body"></div>
      <div class="stamp">校长信</div>
    </div> -->

    <!-- 信件内容 -->
    <component
      class="letter"
      id="letter"
      ref="letterRef"
      :is="isReply ? Letter2 : Letter1"
    />
  </div>
</template>

<script setup>
import { useHead } from "nuxt/app";
import { ref, onMounted } from "vue";
import Letter1 from "~/components/Letter1.vue";
import Letter2 from "~/components/Letter2.vue";

// 添加路由守卫
definePageMeta({
  middleware: "auth",
});

// SEO
useHead({
  title: "校长信",
  meta: [{ name: "description", content: "校长信内容页面" }],
});

// 使用 ref 创建对模板元素的引用
const envelopeRef = ref(null);
const flapRef = ref(null);
const isReply = ref(false);

const isOpened = ref(false);

const route = useRoute();

// 打开信封的函数
function openEnvelope() {
  // 停止浮动动画
  envelopeRef.value.classList.remove("float");

  // 打开信封封口
  flapRef.value.classList.add("open");

  // 延迟显示信件
  setTimeout(() => {
    isOpened.value = true;
    // 信封淡出
    envelopeRef.value.style.transform = "scale(0.8)";
    envelopeRef.value.style.transition = "all 0.5s ease";
  }, 800);
}

onMounted(() => {
  const envelope = envelopeRef.value;
  if (envelope) {
    // 添加加载动画
    envelope.style.opacity = "0";
    envelope.style.transform = "translateY(50px)";

    setTimeout(() => {
      envelope.style.transition = "all 1s ease";
      envelope.style.opacity = "1";
      envelope.style.transform = "translateY(0)";
    }, 100);
  }

  route.query.action && route.query.action === "reply"
    ? (isReply.value = true)
    : (isReply.value = false);
});
</script>

<style scoped>
@import "~/assets/css/letter-content.css";
.letter-container {
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  background: url("~/public/images/letter-bg.png");
  width: 100vw;
  height: 100vh;
}

/* 信封样式 */
.envelope {
  width: 350px;
  height: 250px;
  background: var(--base-100);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: transform 0.5s ease;
}

.envelope:hover {
  transform: translateY(-5px);
}

/* 信封封口（三角形） */
.envelope-flap {
  position: absolute;
  width: 0;
  height: 0;
  border-left: 175px solid transparent;
  border-right: 175px solid transparent;
  border-top: 125px solid var(--base-200);
  z-index: 2;
  transform-origin: top center;
  transition: transform 1s ease;
  transition: all 1s ease;
}

.envelope-flap.open {
  transform: rotateX(180deg);
}

/* 信封主体 */
.envelope-body {
  position: absolute;
  width: 100%;
  height: 100%;
  background: var(--base-100);
}

/* 装饰线条 */
.envelope-body::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
  border-left: 175px solid var(--base-200);
  border-right: 175px solid var(--base-200);
  border-bottom: 125px solid transparent;
  transition: all 1s ease;
}

/* 邮票装饰 */
.stamp {
  position: absolute;
  width: 60px;
  height: 70px;
  background: var(--error);
  top: 20px;
  right: 20px;
  z-index: 3;
  border: 3px dashed var(--base-content);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--base-content);
  font-weight: bold;
  font-size: 12px;
  transform: rotate(15deg);
}

/* 动画关键帧 */
@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.envelope.float {
  animation: float 3s ease-in-out infinite;
}

/* 响应式设计 */
@media (max-width: 600px) {
  .container {
    width: 280px;
    height: 200px;
  }

  .envelope {
    width: 280px;
    height: 200px;
  }

  .envelope-body::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 0;
    height: 0;
    border-left: 140px solid #e8e8e8;
    border-right: 140px solid #e8e8e8;
    border-bottom: 100px solid transparent;
  }

  .envelope-flap {
    border-left: 140px solid transparent;
    border-right: 140px solid transparent;
    border-top: 100px solid #e0e0e0;
  }
}
</style>
