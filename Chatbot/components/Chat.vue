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
        <button
          class="btn btn-ghost btn-sm btn-circle text-current"
          aria-label="删除附件"
          @click="$emit('removeFilePreview')"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
      <div v-for="(item, index) in messages" :key="index">
        <div class="flex flex-col items-start" v-if="item.role == 'assistant'">
          <div class="flex items-start">
            <img
              class="mr-2 h-8 w-8 rounded-full"
              src="~/public/images/genius.png"
            />
            <div
              class="flex flex-col rounded-b-xl rounded-tr-xl bg-slate-50 p-4 dark:bg-slate-800 sm:max-w-md md:max-w-2xl"
              @click="handleClickBubble"
            >
              <div
                class="markdown-body unselectable"
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
          <!-- 反馈按钮 -->
          <div
            v-if="item.id && !item.message.startsWith('正在为你')"
            class="ml-10 mt-1 flex items-center gap-2"
          >
            <button
              class="btn btn-xs btn-ghost"
              :class="{ 'btn-active text-success': item.feedback === 'like' }"
              @click="handleFeedback(item, 'like')"
              aria-label="点赞"
            >
              👍
            </button>
            <button
              class="btn btn-xs btn-ghost"
              :class="{ 'btn-active text-error': item.feedback === 'dislike' }"
              @click="handleFeedback(item, 'dislike')"
              aria-label="点踩"
            >
              👎
            </button>
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
import MarkdownIt from "markdown-it";
import { records, sendFeedback } from "~/api/platform";
import "viewerjs/dist/viewer.css";
import ImageViewer from "./ImageViewer.vue";

// Markdown 渲染器：禁用原始 HTML，避免 AI 返回的 HTML 造成 XSS
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
});

// 只允许 http/https/mailto 链接，过滤掉 javascript: 等危险协议
const defaultLinkOpenRender =
  md.renderer.rules.link_open ||
  ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options));
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const hrefIndex = tokens[idx].attrIndex("href");
  if (hrefIndex >= 0) {
    const href = tokens[idx].attrs[hrefIndex][1];
    if (!/^https?:\/\//i.test(href) && !/^mailto:/i.test(href)) {
      tokens[idx].attrs[hrefIndex][1] = "#";
      tokens[idx].attrPush(["onclick", "return false;"]);
    }
    tokens[idx].attrPush(["target", "_blank"]);
    tokens[idx].attrPush(["rel", "noopener noreferrer"]);
    if (env?.role === "computerDoctor") {
      tokens[idx].attrPush(["class", "resource-link"]);
      tokens[idx].attrPush(["data-resource-role", "computerDoctor"]);
    }
  }
  return defaultLinkOpenRender(tokens, idx, options, env, self);
};
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

function formatAssistantMessage(value) {
  let normalized = String(value || "");

  // 大模型有时会直接返回 HTML <a> 标签，先把它转成 markdown 链接
  normalized = normalized.replace(
    /<a\b[^>]*\bhref=["'](https?:\/\/[^"']+)["'][^>]*>([^<]*)<\/a>/gi,
    (match, url, text) => {
      return `[${text || url}](${url})`;
    }
  );

  // 兜底：阿里云 Agent 默认模板可能输出 ![ResourceVideoUrl](url) / ![ResourceTextbook](url)
  // 这种图片语法在前端会被渲染成破损图片，统一转成普通 Markdown 链接
  normalized = normalized.replace(
    /!\[(ResourceVideoUrl|ResourceTextbook)]\(([^)]+)\)/gi,
    (match, type, target) => {
      const label = type === "ResourceVideoUrl" ? "视频资源" : "教材资源";
      return `[${label}](${target})`;
    }
  );

  // 去掉其它 HTML 标签，只保留文本
  normalized = normalized.replace(/<[^>]+>/g, "");

  // 用 markdown-it 渲染，html: false 已经禁用了原始 HTML，linkify 会自动识别纯 URL
  return md.render(normalized, { role: props.currentRole });
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
  "removeFilePreview",
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
  emit(roleType, "");
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

async function handleFeedback(item, feedback) {
  if (!item.id) return;
  const newFeedback = item.feedback === feedback ? null : feedback;
  try {
    await sendFeedback(item.id, newFeedback);
    item.feedback = newFeedback;
  } catch (error) {
    console.error("发送反馈失败:", error);
  }
}

function handleImageError(e) {
  console.error("图片加载失败:", e);
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

.markdown-body {
  line-height: 1.6;
}

.markdown-body a {
  color: #2563eb;
  text-decoration: underline;
}

.markdown-body a:hover {
  color: #1d4ed8;
}

.markdown-body :deep(p) {
  margin-bottom: 0.5rem;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  font-weight: bold;
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-left: 1.25rem;
  margin-bottom: 0.5rem;
}

.markdown-body :deep(li) {
  margin-bottom: 0.25rem;
}

.markdown-body :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.875em;
}

.markdown-body :deep(pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.75rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 0.5rem;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #cbd5e1;
  padding-left: 0.75rem;
  margin-left: 0;
  margin-bottom: 0.5rem;
  color: #64748b;
}

.markdown-body :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
}
</style>
