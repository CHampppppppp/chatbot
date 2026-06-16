<template>
  <!-- Prompt Messages Container -->
  <div class="flex grow overflow-y-auto w-full flex-col px-1 pb-1">
    <!-- Prompt Messages -->
    <div
      ref="messageContainerRef"
      class="grow space-y-6 rounded-xl overflow-y-auto h-full bg-slate-200 p-4 text-sm leading-6 text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-300 sm:text-base sm:leading-7"
    >
      <!-- 文件预览 -->
      <div
        v-if="filePreview.image_url"
        class="sticky top-2 rounded-lg glass bg-white w-11/12 mx-auto h-20 flex items-center justify-between p-2"
        style="background-color: #9db1d0; color: #4d6ea1"
      >
        <img
          :src="filePreview.image_url"
          alt="图片预览"
          class="max-h-16 object-contain"
        />
        <p class="title text-lg font-semibold">{{ filePreview.filename }}</p>
      </div>
      <div v-for="(item, index) in messages" :key="index">
        <div class="flex items-start" v-if="item.role == 'assistant'">
          <img
            class="mr-2 h-8 w-8 rounded-full"
            src="~/public/images/genius.png"
          />
          <div
            class="flex flex-col rounded-b-xl rounded-tr-xl bg-slate-50 p-4 dark:bg-slate-800 sm:max-w-md md:max-w-2xl"
            @click="handleClickBubble"
          >
            <div
              class="whitespace-pre-wrap unselectable"
              v-html="formatAssistantMessage(item.message)"
            ></div>
            <!-- 显示图片加载骨架 -->
            <ImageSkeleton
              v-if="item.message.startsWith('正在为你生成图像：')"
              width="16rem"
              height="16rem"
              loadingText="正在生成图像..."
            />
            <div
              v-if="item.imageUrls && item.imageUrls.length > 0"
              class="mt-3"
            >
              <div
                v-for="(imageUrl, imgIndex) in item.imageUrls"
                :key="imgIndex"
                class="image-container"
              >
                <!-- 点击预览图片 -->
                <ImageViewer
                  :src="imageUrl"
                  :alt="`生成的图片 ${imgIndex + 1}`"
                >
                  <img
                    :src="imageUrl"
                    :alt="`生成的图片 ${imgIndex + 1}`"
                    class="generated-image"
                    loading="lazy"
                    @load="scrollToBottom"
                    @error="handleImageError"
                  />
                </ImageViewer>
              </div>
            </div>
          </div>
        </div>

        <!-- 用户消息 -->
        <div
          class="flex flex-row-reverse items-start"
          v-if="
            item.role == 'user' &&
            item.message &&
            !rolePrompts.includes(item.message)
          "
        >
          <img
            class="ml-2 h-8 w-8 rounded-full"
            src="~/public/images/user.jpg"
          />
          <div
            class="flex min-h-[85px] rounded-b-xl rounded-tl-xl bg-slate-50 p-4 dark:bg-slate-800 sm:min-h-0 sm:max-w-md md:max-w-2xl"
          >
            <p class="whitespace-pre-wrap unselectable">{{ item.message }}</p>
          </div>
          <div
            class="mr-2 mt-1 flex flex-col-reverse gap-2 text-slate-500 sm:flex-row"
          ></div>
        </div>
      </div>
    </div>
    <!-- Prompt message input -->
    <div class="mt-2 grow">
      <label for="chat-input" class="sr-only">你可以在这里向我提问</label>
      <div class="my-4 grid grid-cols-5 gap-1 mx-2">
        <div
          v-for="(button, index) in buttonGroup"
          class="tooltip tooltip-primary"
          :data-tip="button.tooltip"
        >
          <button
            :key="index"
            class="btn btn-sm btn-outline btn-primary w-full"
            :class="props.currentRole == button.role ? 'btn-active' : ''"
            :disabled="loading != 0"
            @click="button.click"
          >
            <span
              class="loading loading-spinner"
              v-if="button.loading == loading"
            ></span>
            {{ button.name }}
          </button>
        </div>
      </div>
      <div class="relative">
        <textarea
          id="chat-input"
          v-model="message"
          @keypress="handleKeyPress"
          class="text-primary block w-full resize-none rounded-xl border-none bg-slate-200 p-4 pl-6 pr-20 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 dark:bg-slate-900 dark:text-slate-200 dark:placeholder-slate-400 dark:focus:ring-blue-600 sm:text-base"
          placeholder="作品创作过程遇到问题时，可以在这里向校园精灵提问哦！(Enter发送，Shift+Enter换行)"
          rows="5"
        />
        <button
          @click="sendMessage"
          :disabled="loading != 0 && message.trim() == ''"
          class="btn absolute bottom-2 right-2.5 rounded-lg bg-blue-700 text-sm font-medium text-white hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800 sm:text-base btn-sm"
        >
          <span
            class="loading loading-spinner loading-sm"
            v-if="loading == 6"
          ></span
          >发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import { records } from "~/api/platform";
import "viewerjs/dist/viewer.css";
import ImageViewer from "./ImageViewer.vue";
// 存储viewer实例
const viewer = ref(null);

// 初始化回调
const inited = (instance) => {
  viewer.value = instance;
};

// 显示预览
const show = () => {
  viewer.value?.show();
};

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatAssistantMessage(value) {
  const escaped = escapeHtml(value);
  return escaped.replace(/https?:\/\/[^\s<]+/g, (url) => {
    return `<a class="underline text-blue-500" href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
}

// 角色配置常量
const ROLE_CONFIGS = [
  {
    role: "inspirationSuperman",
    name: "灵感超人",
    loading: 1,
    tooltip: "提供创作等方面的灵感",
  },
  {
    role: "intelligentArtist",
    name: "智能画家",
    loading: 2,
    tooltip: "根据你的描述生成图片",
  },
  {
    role: "computerDoctor",
    name: "电脑博士",
    loading: 3,
    tooltip: "解答电脑、软件、编程等相关问题",
  },
  {
    role: "cultureMaster",
    name: "文化达人",
    loading: 4,
    tooltip: "提供历史、文化、艺术等方面的知识",
  },
  {
    role: "eloquentWarrior",
    name: "妙语奇兵",
    loading: 5,
    tooltip: "帮你润色文案、精准翻译",
  },
];

const message = ref("");

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  rolePrompts: {
    type: Object,
  },
  loading: {
    type: Number,
    required: true,
  },
  currentRole: {
    type: String,
  },
  filePreview: {
    image_url: String,
    filename: String,
  },
});

const emit = defineEmits([
  "add",
  "inspirationSuperman",
  "intelligentArtist",
  "computerDoctor",
  "cultureMaster",
  "eloquentWarrior",
  "clickBubble",
]);

const sendMessage = async () => {
  if (!message.value?.trim()) {
    return;
  }
  emit("add", message.value);
  await nextTick();
  scrollToBottom();
  message.value = "";
};

// 通用角色处理函数
const handleRoleAction = (roleType) => {
  const messageToSend = message.value?.trim() || "";
  emit(roleType, messageToSend);
  message.value = "";

  scrollToBottom();
  // 数据埋点
  records(2, {
    name: ROLE_CONFIGS.find((config) => config.role === roleType)?.name,
    time: new Date().toISOString(),
  }).catch((error) => {
    console.error("记录角色点击失败:", error);
  });
};

// 动态生成按钮组，为每个角色配置添加click处理函数
const buttonGroup = ref(
  ROLE_CONFIGS.map((config) => ({
    ...config,
    click: () => handleRoleAction(config.role),
  }))
);

defineExpose({
  sendMessage,
});

// 滚动到底部
const messageContainerRef = ref(null);
watch(
  () => props.messages,
  async () => {
    await nextTick(); // 确保DOM更新后再滚动
    scrollToBottom();
  }
);

function scrollToBottom() {
  messageContainerRef.value.scrollTop = messageContainerRef.value.scrollHeight;
}

// 处理Enter键
const handleKeyPress = async (event) => {
  if (event.key === "Enter") {
    if (event.shiftKey) {
      // Shift+Enter 允许换行，不阻止默认行为
      return;
    } else {
      // 单独按Enter发送消息
      event.preventDefault();
      await sendMessage();
    }
  }
};

function handleClickBubble(e) {
  emit("clickBubble", e);
}
</script>

<style>
/* styles */
.button-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 2px; /* 按钮之间的间距 */
}

.button-container .btn {
  flex: 1 1 calc(20% - 10px); /* 每行展示 5 个按钮，确保宽度合适 */
  min-width: 100px; /* 根据需要设置最小宽度 */
}

/* 图片样式 */
.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.generated-image {
  max-width: 100%;
  max-height: 300px;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.generated-image:hover {
  transform: scale(1.05);
}
</style>
