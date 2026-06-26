<template>
  <div id="app" class="flex max-h-screen w-dvw min-w-fit size-dvw">
    <!-- 中间任务描述区域 -->
    <div class="w-2/5">
      <div
        class="bg-base-100 p-4 pr-2 h-screen w-full grid grid-col-1 gap-y-2.5"
      >
        <div class="flex flex-col items-start">
          <!-- 任务描述区域标题和按钮 -->
          <div class="flex justify-between items-center mb-2">
            <div class="flex items-center">
              <h2
                class="text-xl font-bold"
                style="user-select: text"
                contenteditable="false"
              >
                任务要求
              </h2>
              <button
                class="ml-2 p-1 rounded hover:bg-base-200 text-base-content transition-colors"
                aria-label="放大"
                @click="increaseFontSize"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                  <path d="M11 8v6" />
                  <path d="M8 11h6" />
                </svg>
              </button>
              <button
                class="ml-2 p-1 rounded hover:bg-base-200 text-base-content transition-colors"
                aria-label="缩小"
                @click="decreaseFontSize"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <circle cx="11" cy="11" r="8" />
                  <path d="M21 21l-4.35-4.35" />
                  <path d="M8 11h6" />
                </svg>
              </button>
            </div>
          </div>
          <!-- 文字展示区域的内容 -->
          <div class="w-full grow">
            <textarea
              v-model="describe"
              class="text-editor h-full w-full rounded-lg textarea"
              :style="{ fontSize: fontSize + 'px' }"
              disabled
              @change="changeText"
            />
          </div>
        </div>

        <div class="flex flex-col items-start">
          <!-- 评价标准 -->
          <div class="bg-base-100 flex items-center mb-2">
            <!-- 评价标准区域标题和按钮 -->
            <h2
              class="text-xl font-bold"
              style="user-select: text"
              contenteditable="false"
            >
              评价标准
            </h2>
          </div>
          <!-- 文字展示区域的内容 -->
          <div class="w-full grow">
            <textarea
              v-html="standard"
              class="text-editor h-full w-full rounded-lg textarea"
              :style="{ fontSize: fontSize + 'px' }"
              disabled
              @change="changeText"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧聊天窗口 -->
    <div class="w-3/5 bg-base-100 p-4 h-screen pl-2">
      <div class="w-full h-full flex flex-col">
        <div class="flex justify-between items-center mb-2">
          <div class="flex items-center gap-4">
            <h2 class="text-xl font-bold">校园精灵智能体</h2>
            <button
              class="btn btn-soft btn-success btn-sm text-white"
              @click="openProfileDialog"
            >
              我的画像
            </button>
            <button
              :disabled="loadingIndex != 0"
              class="btn btn-soft btn-info btn-sm text-white grow"
              @click="resetIdentity"
            >
              重置身份
            </button>
            <button
              class="btn btn-soft btn-error btn-sm text-white"
              @click="logout"
            >
              退出登录
            </button>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="relative">
              <button
                class="btn btn-info btn-soft btn-sm text-white w-full h-full"
                @click="triggerFileInput"
              >
                上传图片
              </button>
              <input
                @change="uploadImage"
                type="file"
                ref="imageInput"
                accept="image/*"
                class="hidden"
              />
            </div>
            <NuxtLink to="/submit-task">
              <button class="btn btn-primary btn-sm text-white">
                提交作品
              </button>
            </NuxtLink>
          </div>
        </div>
        <Chat
          :messages="chatMessages"
          :loading="loadingIndex"
          :image-urls="imageUrls"
          :rolePrompts="rolePrompts"
          :currentRole="currentRole"
          :filePreview="filePreview"
          @add="chat"
          @inspirationSuperman="handleRoleChat($event, 'inspirationSuperman')"
          @intelligentArtist="handleRoleChat($event, 'intelligentArtist')"
          @computerDoctor="handleRoleChat($event, 'computerDoctor')"
          @cultureMaster="handleRoleChat($event, 'cultureMaster')"
          @eloquentWarrior="handleRoleChat($event, 'eloquentWarrior')"
          @clickBubble="handleClickResourceVideo($event)"
          @removeFilePreview="removeFilePreview"
        />
      </div>
    </div>

    <!-- 加载等待动画 -->
    <div
      class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50"
      v-if="screenLoding"
    >
      <span class="loading loading-spinner text-info loading-lg"></span>
    </div>

    <!-- 访问资源链接后的评分问卷 -->
    <dialog
      ref="ResourceRate"
      id="resource_rate"
      class="card modal"
      closedby="none"
    >
      <form @submit="handleRate" method="dialog">
        <div class="card-body bg-base-100 text-center rounded-lg">
          <h1 class="card-title text-3xl">你觉得推荐的资源怎么样？</h1>
          <div class="rating rating-lg mx-auto mt-4">
            <input
              v-model="resourceRate"
              type="radio"
              name="rating-8"
              value="1"
              class="mask mask-star-2 bg-orange-400"
            />
            <input
              v-model="resourceRate"
              type="radio"
              name="rating-8"
              value="2"
              class="mask mask-star-2 bg-orange-400"
            />
            <input
              v-model="resourceRate"
              type="radio"
              name="rating-8"
              value="3"
              class="mask mask-star-2 bg-orange-400"
            />
            <input
              v-model="resourceRate"
              type="radio"
              name="rating-8"
              value="4"
              class="mask mask-star-2 bg-orange-400"
            />
            <input
              v-model="resourceRate"
              type="radio"
              name="rating-8"
              value="5"
              class="mask mask-star-2 bg-orange-400"
            />
          </div>
          <div class="card-actions justify-center mt-12">
            <button class="btn btn-info">提交</button>
          </div>
        </div>
      </form>
    </dialog>

    <!-- 用户画像弹窗 -->
    <dialog ref="ProfileDialog" class="card modal" closedby="any">
      <div class="card-body bg-base-100 rounded-lg max-w-md w-full">
        <div class="flex justify-between items-center mb-4">
          <h2 class="card-title text-2xl">我的画像</h2>
          <button class="btn btn-sm btn-circle btn-ghost" @click="closeProfileDialog">✕</button>
        </div>

        <div v-if="profileLoading" class="flex justify-center py-8">
          <span class="loading loading-spinner loading-md"></span>
        </div>

        <div v-else class="space-y-4">
          <div class="form-control">
            <label class="label"><span class="label-text font-medium">姓名</span></label>
            <input :value="profileForm.real_name || '—'" type="text" class="input input-bordered bg-base-200" readonly />
          </div>
          <div class="form-control">
            <label class="label"><span class="label-text font-medium">学校</span></label>
            <input :value="profileForm.school || '—'" type="text" class="input input-bordered bg-base-200" readonly />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label"><span class="label-text font-medium">年级</span></label>
              <input :value="profileForm.grade || '—'" type="text" class="input input-bordered bg-base-200" readonly />
            </div>
            <div class="form-control">
              <label class="label"><span class="label-text font-medium">班级</span></label>
              <input :value="profileForm.Class || '—'" type="text" class="input input-bordered bg-base-200" readonly />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label"><span class="label-text font-medium">知识储备</span></label>
              <input
                :value="profileDimensions.knowledge_reserve !== null ? profileDimensions.knowledge_reserve + ' / 5' : '—'"
                type="text"
                class="input input-bordered bg-base-200"
                readonly
              />
            </div>
            <div class="form-control">
              <label class="label"><span class="label-text font-medium">活跃度</span></label>
              <input
                :value="profileDimensions.active_score !== null ? profileDimensions.active_score + ' 分' : '—'"
                type="text"
                class="input input-bordered bg-base-200"
                readonly
              />
            </div>
          </div>
        </div>

        <div v-if="!profileLoading" class="card-actions justify-end mt-6 gap-2">
          <button class="btn btn-primary" @click="closeProfileDialog">关闭</button>
        </div>
      </div>
    </dialog>

    <!-- 图像服务次数提示 -->
    <div
      v-if="imageAlertShow"
      class="alert alert-info fixed top-4 w-fit left-1/2 -translate-x-1/2 z-50 transition-all"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="stroke-current shrink-0 h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <div class="flex flex-col">
        <span
          >图像生成还剩下:
          <span class="text-white font-bold">{{ generateImageTimes }}</span>
          次</span
        >
        <span
          >图像编辑还剩下:
          <span class="text-white font-bold">{{ editImageTimes }}</span>
          次</span
        >
      </div>
    </div>
  </div>
</template>
<script setup>
import Chat from "@/components/Chat.vue";
import { showError, useFetch, useRuntimeConfig, useNuxtApp } from "nuxt/app";

const { $axios } = useNuxtApp();
import { fetchChatStream } from "~/api/platform";
import {
  records,
  getProfile,
  updateProfile,
  getDimensions,
  startEvalSession,
  appendEvalSessionMessage,
  endEvalSession,
} from "~/api/platform";

definePageMeta({
  middleware: "auth",
});

// SEO
useHead({
  title: "首页",
  meta: [
    {
      name: "description",
      content: "校园精灵智能体首页，提供电子板报制作指导和智能聊天功能。",
    },
    { name: "keywords", content: "校园精灵, 电子板报, 智能体, AI助手" },
  ],
});

// 以18px为初始字体大小
const fontSize = ref(18);
const increaseFontSize = () => {
  if (fontSize.value >= 30) return; // 限制最大字体大小为30
  fontSize.value++; // 增加字体大小
};

const ResourceRate = ref(null);
const isImgRate = ref(false);

// 用户画像
const ProfileDialog = ref(null);
const profileLoading = ref(false);
const profileSaving = ref(false);
const profileForm = ref({
  real_name: "",
  school: "",
  grade: "",
  Class: "",
});
const profileDimensions = ref({
  knowledge_reserve: null,
  active_score: null,
});

async function openProfileDialog() {
  ProfileDialog.value.showModal();
  profileLoading.value = true;
  try {
    const [profileRes, dimRes] = await Promise.all([
      getProfile(),
      getDimensions().catch(() => null),
    ]);
    const d = profileRes?.data || profileRes;
    if (d) {
      profileForm.value = {
        real_name: d.real_name || "",
        school: d.school || "",
        grade: d.grade || "",
        Class: d.class || d.Class || "",
      };
    }
    const dimData = dimRes?.data || dimRes;
    if (dimData) {
      profileDimensions.value = {
        knowledge_reserve: dimData.knowledge_reserve ?? null,
        active_score: dimData.active_score ?? null,
      };
    }
  } catch (e) {
    console.error("获取画像失败", e);
  } finally {
    profileLoading.value = false;
  }
}

function closeProfileDialog() {
  ProfileDialog.value.close();
}

async function saveProfile() {
  profileSaving.value = true;
  try {
    const payload = { ...profileForm.value };
    await updateProfile(payload);
    closeProfileDialog();
  } catch (e) {
    console.error("保存画像失败", e);
  } finally {
    profileSaving.value = false;
  }
}

// 会话评分相关
const evalSessionId = ref(null);
const pendingEvalMessages = ref([]);

async function ensureEvalSession() {
  if (evalSessionId.value) return;
  try {
    const res = await startEvalSession();
    evalSessionId.value = res.data?.session_id || res.session_id;
    pendingEvalMessages.value = [];
  } catch (e) {
    console.error("创建评分会话失败:", e);
  }
}

function queueEvalMessage(role, content) {
  if (!content || !evalSessionId.value) return;
  // 只保留 user/assistant 的有效对话，过滤系统提示和开场白
  if (role !== "user" && role !== "assistant") return;
  pendingEvalMessages.value.push({ role, content });
}

async function flushEvalMessages() {
  if (!evalSessionId.value || pendingEvalMessages.value.length === 0) return;
  try {
    await appendEvalSessionMessage(
      evalSessionId.value,
      pendingEvalMessages.value
    );
    pendingEvalMessages.value = [];
  } catch (e) {
    console.error("追加评分消息失败:", e);
  }
}

async function finishEvalSession() {
  await flushEvalMessages();
  if (!evalSessionId.value) return;
  try {
    await endEvalSession(evalSessionId.value);
  } catch (e) {
    console.error("结束评分会话失败:", e);
  } finally {
    evalSessionId.value = null;
    pendingEvalMessages.value = [];
  }
}

// 图片服务剩余次数
const generateImageTimes = ref(0);
const editImageTimes = ref(0);

const imageAlertShow = ref(false);

const decreaseFontSize = () => {
  if (fontSize.value <= 8) return;
  fontSize.value--; // 减少字体大小，但不小于8
};

const loadingIndex = ref(0);
const screenLoding = ref(false);
const describe =
  ref(`1、开展“向世界介绍我的学校”主题学习，制作一份图文并茂、交互丰富的学校数字板报，可使用Word、PPT或网页制作工具；
2、确定作品的整体结构，将数字板报规划为标题页、内容页等页面，并为作品命名；
3、明确数字板报的页面内容、媒体资源类型（如图片、超链接）及资源获取方式等，尽可能图文并茂并增强交互性；
4、设计作品中文字、图片等素材的呈现方式，加入超链接等元素以增加生动性和互动效果；
5、在创作过程中需使用校园精灵智能体辅助内容生成、资源搜索或设计优化；
6、完成作品后，将文件导出为JPG、JPEG或PNG格式提交。
`);

const standard = ref(`作品满分为100分，可参考以下评价标准：
1、科学性：作品主题明确，内容合法、合理；注明资源的来源。
2、艺术性：作品版式布局合理、层次清晰、色彩搭配美观。
3、技术性：作品中的文字、图片、音频、视频等资源的处理与表达恰当合理。
4、完整性：作品有主题页、内容页，结构完整。
5、创新性：作品构思、创作方式及媒体运用等方面具有独到之处。
6、丰富性：作品多方位、多角度地诠释学习主题，图文并茂并增强交互性。`);

const imageUrls = ref([]);

// chat
const chatMessages = ref([
  {
    message: "你好😊",
    role: "user",
  },
  {
    message:
      "Hi，我是校园精灵，你可以跟我直接对话，也可以根据自身需求点击对应的小精灵对话哦！😉",
    role: "assistant",
  },
]);

let currentChat = null;
const chat = async (message) => {
  if (message) {
    chatMessages.value.push({
      message: message,
      role: "user",
    });
    await ensureEvalSession();
    queueEvalMessage("user", message);
  }

  const config = roleConfigs[currentRole.value];
  if (currentRole.value === "chat") {
    loadingIndex.value = 6;
  }
  if (!config) {
    console.error(`未找到角色配置: ${currentRole.value}`);
    return;
  }

  let hasImage = false;

  let lastMessageIndex = computed(() => {
    return chatMessages.value.length - 1;
  });

  let start_rec = ref(false);
  const onMessage = (event, controller) => {
    if (event.data == "[DONE]") {
      loadingIndex.value = 0;
      controller.abort();
      start_rec.value = false;

      // 推荐资源处理
      const handledMessage = processResource(
        chatMessages.value[lastMessageIndex.value].message
      );
      chatMessages.value[lastMessageIndex.value].message = handledMessage;
      chatMessages.value = [...chatMessages.value]; // 强制更新

      // 查询图像服务剩余次数
      if (hasImage) {
        getImageTimes();
      }

      // 数据埋点
      const question = chatMessages.value[lastMessageIndex.value - 1].message;
      const message = chatMessages.value[lastMessageIndex.value].message;
      const meta = {
        prompt: question,
        answer: message,
      };

      if (currentRole.value === "chat") {
        records(4, {
          name: roleConfigs[currentRole.value].name,
          time: new Date().toISOString(),
          content: meta,
        });
      } else {
        records(3, {
          name: roleConfigs[currentRole.value].name,
          time: new Date().toISOString(),
          content: meta,
        });
      }

      // 本轮对话结束，把 assistant 回复追加到评分会话
      queueEvalMessage("assistant", message);
      flushEvalMessages();
    } else if (event.data.startsWith("![Generated Image](")) {
      // 接收图像
      processImageGenerationResponse(event.data, lastMessageIndex.value);
      hasImage = true;
    } else {
      if (!start_rec.value) {
        start_rec.value = true;
        let newMessage = {
          role: "assistant",
          message: event.data,
          id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        };
        chatMessages.value.push(newMessage);
      } else {
        chatMessages.value[lastMessageIndex.value].message += event.data;
        chatMessages.value[lastMessageIndex.value].message = chatMessages.value[
          lastMessageIndex.value
        ].message.replace(/<br\/>/g, "\n");
      }
    }
    chatMessages.value = [...chatMessages.value]; // 强制更新
  };
  if (currentChat) {
    currentChat.abort();
    currentChat = null;
  }

  const runtimeConfig = useRuntimeConfig();
  const url = `${runtimeConfig.public.apiBase}/platform/${config.endpoint}`;
  const data = chatMessages.value
    .filter((item) => item.role === "user" || item.role === "assistant")
    .slice(-5)
    .map((item) => {
      return {
        content: item.message, // 创建一个新的键 content 并赋予 message 的值
        role: item.role, // 保留 role 键和值
      };
    });

  let formdata = null;
  if (
    config.endpoint === "intelligentArtist" &&
    typeof window !== "undefined"
  ) {
    formdata = new window.FormData();
    formdata.append("messages", JSON.stringify(data));
    if (imageInput.value.files[0])
      formdata.append("image", imageInput.value.files[0]);
  }
  currentChat = fetchChatStream(
    url,
    config.endpoint === "intelligentArtist" && formdata
      ? formdata
      : { messages: data, role: config.endpoint },
    onMessage
  );
};

// 处理图像生成响应的工具函数
const processImageGenerationResponse = (message, lastMessageIndex) => {
  const match = message.match(/!\[Generated Image\]\((.*?)\)/);
  if (match) {
    const url = match[1];
    // imageUrls初始化
    if (!chatMessages.value[lastMessageIndex].imageUrls) {
      chatMessages.value[lastMessageIndex].imageUrls = [];
      chatMessages.value[lastMessageIndex].message = chatMessages.value[
        lastMessageIndex
      ].message.replace("正在为你生成图像：", "图像生成成功：");
    }
    chatMessages.value[lastMessageIndex].imageUrls.push(url);

    // 如果有生成图像，显示评分问卷
    isImgRate.value = true;
    ResourceRate.value.classList.remove("hidden");
    ResourceRate.value.show();
  }
};

const processResource = (message) => {
  // 处理资源链接和教材页码
  const videoUrl = message.match(/!\[ResourceVideoUrl\]\((.*?)\)/);
  const textBook = message.match(/!\[ResourceTextbook\]\((.*?)\)/);

  const processed_videoUrl = message.replace(
    /!\[ResourceVideoUrl\]\((.*?)\)/g,
    "$1"
  );
  const processed = processed_videoUrl.replace(
    /!\[ResourceTextbook\]\((.*?)\)/g,
    "$1"
  );

  resourceVideoUrl.value = videoUrl ? videoUrl : "";
  resourceTextBook.value = textBook ? textBook[1] : "";
  return processed;
};

// 角色配置
const roleConfigs = {
  chat: {
    name: "校园精灵",
    loadingIndex: 0,
    endpoint: "chat",
  },
  inspirationSuperman: {
    name: "灵感超人",
    loadingIndex: 1,
    endpoint: "inspirationSuperman",
  },
  intelligentArtist: {
    name: "智能画家",
    loadingIndex: 2,
    endpoint: "intelligentArtist",
  },
  computerDoctor: {
    name: "电脑博士",
    loadingIndex: 3,
    endpoint: "computerDoctor",
  },
  cultureMaster: {
    name: "文化达人",
    loadingIndex: 4,
    endpoint: "cultureMaster",
  },
  eloquentWarrior: {
    name: "妙语奇兵",
    loadingIndex: 5,
    endpoint: "eloquentWarrior",
  },
};

const currentRole = ref("chat");

// 角色提示词（给大模型看的 system prompt）
const rolePrompts = [
  `
        现在你是校园精灵
        开场语：Hi，我是校园精灵，你可以跟我直接对话，也可以根据自身需求点击对应的小精灵对话哦！
        角色设定：
            名称：校园精灵
            身份：校园电子板报制作精灵
        风格控制：
            1.回避复杂术语，尽量提问启发而不是直接给答案；
            2.每次回答的字数控制在100字以内；
            3.拒绝回答与学习无关的内容。
    `,
  `
        现在你是灵感超人
        开场语：Hi，我是校园精灵“灵感超人”，善于提供创意并激发你的灵感，欢迎与我交流！
        角色设定：
            名称：灵感超人
            身份：校园创意助手，电子板报灵感激发者
            性格：活泼有趣、脑洞大开，善于用比喻和故事引导思考
        技能：
            为电子板报提供主题创意（如校园文化、未来学校等）
            建议视觉设计灵感（排版/配色/互动元素）
            用提问式引导帮助学生自己发现创意
        交互规则：
            1.当学生需要电子板报的主题时
            建议学生从“校园特色场景”“校园特色文化”“学生的一天”“未来学校”四个主题选择一个主题，可以为学生提供1-2个想法。
            2.当学生提到未来学校时
            当学生提到主题包括“未来学校”，可以给一些未来学校的设计建议，同时让学生联想自己的学校可以有哪些改进之处，另外，也可以让学生思考下随着科技的发展，学校可以增加哪些智能设备，可以为学生提供1-2个想法。
            3.当学生需要为自己的电子板报主题起一个有创意的名字时
            名字应尽量短小精悍，符合“向世界介绍我的学校”主题，可以为学生提供1-2个想法。
            4.鼓励创作
            读取学生的想法，并鼓励学生的想法。
        风格控制：
            1.回避复杂术语，尽量提问启发而不是直接给答案；
            2.每次回答的字数控制在100字以内；
            3.拒绝回答与学习无关的内容。
            `,
  `
        现在你是智能画家
        开场语：Hi，我是校园精灵“智能画家”，擅长将文字转为图片，或者编辑修改图片，欢迎将文字发给我！
        提示词设计：
        角色设定：
          名称：智能画家
          身份：校园AI绘图助手，文字转图片、通用图像编辑专家
          技能：
            根据文字描述生成高质量插画/图片
            支持多种风格（卡通/水彩/科幻/手绘等）
            为电子板报、校园海报提供视觉素材
            对传入的图片进行编辑和修改
        交互规则：
        1.	当用户想要生成图片时：
          如果没有提到生成什么风格，确认需求：“收到！你想生成的是______（复述用户描述），对吗？需要调整风格吗？（比如：卡通/写实/水彩）？”并补充建议：“小提示：描述越详细，图片越精准哦！比如加上颜色/动作/场景细节”，否则直接开始生成
        2.	生成图片后：
          展示图片：“这是根据你的描述生成的图！如果不喜欢的话，可以修改关键词或换风格重新生成！”
          引导优化：“如果想调整，可以告诉我修改方向！”
        3.	风格推荐（若用户无明确要求）：“不确定风格？试试这些：
          卡通版：适合校园生活场景
          水彩风：适合文艺主题
          科幻感：适合‘未来学校’设计！”
        4.  当用户的意图是修改图片或者转换图片风格时：
          你应该总是认为用户已经提交了图片并直接开始处理图片
          调用图像编辑API对图像进行处理
          你需要认真阅读用户的意图，理解用户的需求，选择合适的图像编辑function进行图像编辑
          如要求转换图片为法国绘本风格或者金箔艺术风格则function应该是stylization_all，要求人形象装扮，比如增加配饰（如戴墨镜/戴耳环）、换发色等则function应该是description_edit，此外还还有别的function根据具体用户意图选择
        风格控制：
          1.不生成真人肖像或复杂版权内容
        将以上所有要求和用户提到的风格提炼，形成简短精确的图像生成提示词传递给图像生成服务
      `,
  `
        现在你是电脑博士
        开场语：Hi，我是校园精灵“电脑博士”，精通电脑操作，尤其是Word、PPT的制作，欢迎与我交流！
        角色设定：
            名称：电脑博士
            身份：校园电脑操作专家，Office软件导师
            专长：
                精通Word/PPT电子板报制作全流程
                能解决排版、动画、图文混排等技术问题
                提供简单易懂的步骤指导
        交互规则：
        1.当用户提问时：
            分步指导：例如，“跟我这样做：1.点击[插入]-[图片]；2.右键图片选择[环绕文字]-[四周型]
        风格控制：
          简短分步骤，标注重点
          每次回答的字数控制在100字以内；
          回避专业术语
          如果需要鼓励则补充一句：“做得很棒！”，并提出下一步可以尝试做什么

    `,
  `
        现在你是文化达人
        开场语：Hi，我是校园精灵“文化达人”，中华传统文化的宝藏我烂熟于心，欢迎与我探讨！
        角色设定：
            名称：文化达人
            身份：校园传统文化小导师，中华文化百事通
            性格：博学又亲切，像一本会说话的“趣味文化百科”
        技能：
            讲解节日习俗、非遗技艺、历史典故
            帮校园生活融入传统文化元素
            用故事+互动问答让文化知识更生动
        交互规则：
            1. 当学生提问具体文化主题时：文字讲解控制在100字以内。
            2. 当学生想结合校园文化时，创意融合，文字讲解控制在100字以内。
        风格控制：
            1. 涉及历史日期/典籍原文时标注出处
            2. 简短100字以内，标注重点
            3. 拒绝回答与传统文化无关的内容。

    `,
  `
        现在你是妙语奇兵
        开场语：Hi，我是校园精灵“妙语奇兵”，擅长中文和英文两种语言，欢迎与我交流！
        角色设定：
            名称：妙语奇兵
            身份：校园语言特工队，双语转换专家
            超能力：
                中英文语句精准互译
                为板报文案润色升级
                用地道表达替换生硬翻译
        交互规则：
            1.翻译模式：中英精准互译。
            2.润色模式：根据用户发的原句，为学生润色。或者根据学生发的原句，问一下学生的需求是什么，然后根据需求润色。
        风格控制：
            1.翻译要信达雅优先，保留原意不加戏。
            2.润色的句子内容不超过100字。
    `,
];

// 角色开场白（给学生看的本地展示）
const roleGreetings = [
  "Hi，我是校园精灵，你可以跟我直接对话，也可以根据自身需求点击对应的小精灵对话哦！😊",
  "Hi，我是校园精灵“灵感超人”，善于提供创意并激发你的灵感，欢迎与我交流！💡",
  "Hi，我是校园精灵“智能画家”，擅长将文字转为图片，或者编辑修改图片，欢迎将文字发给我！🎨",
  "Hi，我是校园精灵“电脑博士”，精通电脑操作，尤其是Word、PPT的制作，欢迎与我交流！💻",
  "Hi，我是校园精灵“文化达人”，中华传统文化的宝藏我烂熟于心，欢迎与我探讨！📚",
  "Hi，我是校园精灵“妙语奇兵”，擅长中文和英文两种语言，欢迎与我交流！✨",
];

const resetIdentity = () => {
  currentRole.value = "chat";
  chatMessages.value.push({
    message: roleGreetings[0],
    role: "assistant",
  });
};

const logout = async () => {
  await finishEvalSession();
  try {
    await $axios.post("/users/logout");
  } catch (error) {
    console.error("退出登录失败:", error);
  } finally {
    localStorage.removeItem("userInfo");
    await navigateTo("/login");
  }
};

async function getImageTimes() {
  // 获取图像服务剩余次数
  const { data, error } = await useFetch("/platform/image-quota", {
    method: "GET",
    baseURL: useRuntimeConfig().public.apiBase,
    credentials: "include",
  });
  if (error.value) {
    showError("获取图像服务剩余次数失败", error.value);
    return;
  }
  console.log("图像服务剩余次数", JSON.stringify(data.value));
  generateImageTimes.value = data.value.data.generate.remaining;
  editImageTimes.value = data.value.data.edit.remaining;

  // 显示次数提示和定时自动关闭
  imageAlertShow.value = true;
  setTimeout(() => {
    imageAlertShow.value = false;
  }, 5000);
}

// 统一的角色聊天函数
const handleRoleChat = (message, role) => {
  currentRole.value = role;
  loadingIndex.value = roleConfigs[role].loadingIndex;

  // 如果用户没有输入内容，只是切换角色，不发起网络请求，直接显示本地开场白
  if (!message || message.trim() === "") {
    chatMessages.value.push({
      message: roleGreetings[loadingIndex.value],
      role: "assistant",
    });
    chatMessages.value = [...chatMessages.value];
    loadingIndex.value = 0;
    return;
  }

  chatMessages.value.push({
    message: rolePrompts[loadingIndex.value],
    role: "system",
  });
  chatMessages.value.push({
    message:
      "如果你需要回复html等可以被浏览器渲染的内容，请在回复时进行转义，比如使用&lt;div&gt;代替<div>",
    role: "system",
  });

  chat(message);

  // 数据埋点
  records(2, {
    name: roleConfigs[role].name,
    time: new Date().toISOString(),
  });
};

const imageInput = ref(null);
const filePreview = ref({
  image_url: "",
  filename: "",
});

const triggerFileInput = () => {
  imageInput.value?.click();
};

const uploadImage = () => {
  // 图像编辑-图片预览
  const file = imageInput.value.files[0];
  if (file) {
    filePreview.value = {
      image_url: URL.createObjectURL(file),
      filename: file.name,
    };
  }
};

const removeFilePreview = () => {
  filePreview.value = {
    image_url: "",
    filename: "",
  };
  if (imageInput.value) {
    imageInput.value.value = "";
  }
};

let resourceVideoTimer = null;
const hasClickResourceVideo = ref(false);
const resourceVideoUrl = ref("");
const resourceTextBook = ref("");
const resourceRate = ref(5);
function handleClickResourceVideo(e) {
  // 电脑博士资源链接强制评分
  const resourceLink = e.target.closest(
    'a.resource-link[data-resource-role="computerDoctor"]'
  );
  if (resourceLink && currentRole.value === "computerDoctor") {
    resourceVideoTimer = 0;
    resourceVideoUrl.value = resourceLink.href;
    resourceTextBook.value = "";
    isImgRate.value = false;
    ResourceRate.value?.classList.remove("hidden");
    if (!ResourceRate.value?.open) {
      ResourceRate.value?.showModal();
    }
    return;
  }

  // 记录点击视频链接
  if (e.target.id === "resource_video") {
    resourceVideoTimer = Date.now();
    setTimeout(() => {
      hasClickResourceVideo.value = true;
    }, 50);

    resourceVideoUrl.value = e.target.href;
    if (!ResourceRate.value.classList.contains("hidden")) {
      ResourceRate.value.classList.add("hidden");
    }
  }
}

async function handleVisibilityChange() {
  if (document.hidden === false && hasClickResourceVideo.value) {
    resourceVideoTimer = Date.now() - resourceVideoTimer; // 计算得到时间差
    hasClickResourceVideo.value = false; // 重置观看状态
    // 显示问卷
    ResourceRate.value.classList.remove("hidden");
    ResourceRate.value.showModal();
  }
}

async function handleRate(event) {
  event.preventDefault();
  ResourceRate.value.close();
  ResourceRate.value.classList.add("hidden");

  // 数据埋点
  const type = isImgRate.value ? 9 : 7;
  await records(type, {
    name: "资源评分",
    videoUrl: resourceVideoUrl.value,
    text_book: resourceTextBook.value,
    rate: resourceRate.value,
    time: resourceVideoTimer,
  });

  // 恢复记录状态
  isImgRate.value = false;
  resourceRate.value = 5;
}

// const AlertMap = [
//   { min: 0, max: 1, val: "alert-error" },
//   { min: 2, max: 3, val: "alert-warning" },
//   { min: 4, max: 6, val: "alert-info" },
//   { min: 7, max: 10, val: "alert-success" },
// ];

// 根据剩余次数判断警告的类型
// function getTimesAlertClass() {
//   const matched = AlertMap.find(
//     (alert) => times >= alert.min && times <= alert.max
//   );
//   if (matched) {
//     return `alert ${matched.val} z-50 fixed top-4`;
//   }
// }

onMounted(() => {
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onBeforeUnmount(() => {
  finishEvalSession();
});

// 页面关闭/刷新时尽量通知后端结束会话
if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    finishEvalSession();
  });
}
</script>

<style>
/* CSS 过渡效果 */
.transition-width {
  transition: width 0.3s;
}
.transition-all {
  transition: all 0.3s;
}

.text-editor {
  padding: 10px;
  font-size: 18px;
  background-color: var(
    --base-200
  ); /* 设置为一个不同的背景颜色，表示不可编辑 */
  color: var(--base-content);
  cursor: not-allowed; /* 设置鼠标光标为禁止符号 */
  max-width: 100%;
  overflow: auto;
}

.text-editor img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}
</style>
