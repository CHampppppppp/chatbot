<template>
  <div
    class="w-screen h-screen bg-[url('/images/auth-bg.png')] bg-no-repeat bg-center bg-cover flex flex-col items-center justify-center gap-12 overflow-auto py-10"
  >
    <!-- 课程选择 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 w-3/4">
      <!-- 向世界 -->
      <div
        ref="course1"
        @click="goToCourse(1)"
        class="card flex-1 bg-white/50 text-info-content hover:bg-white hover:border-primary hover:border-2 transition-all border-2 border-transparent"
      >
        <div class="card-body p-10 aspect-video">
          <div
            class="rounded-full w-fit bg-primary text-white text-3xl font-bold px-6 py-1 mx-auto"
          >
            向世界介绍我的学校
          </div>
          <p class="indent-8 text-xl leading-8 text-black">
            亲爱的同学，这是一款专为“向世界介绍你的学校”项目定制开发的校园精灵智能体工具，它不仅能帮你轻松制作校园海报和创意网页，还能在激发设计灵感、解答软件疑惑、图片生成等方面提供快速反馈，更有智能评分功能助你更好地完善作品，快来使用该工具创作你的作品吧！
          </p>
        </div>
      </div>
      <!-- 市花 -->
      <div
        ref="course2"
        @click="goToCourse(2)"
        class="card flex-1 bg-white/50 text-info-content hover:bg-white hover:border-primary hover:border-2 transition-all border-2 border-transparent"
      >
        <div class="card-body p-10 aspect-video">
          <div
            class="rounded-full w-fit bg-primary text-white text-3xl font-bold px-6 py-1 mx-auto"
          >
            市花名片
          </div>
          <p class="indent-8 text-xl leading-8 text-black">
            亲爱的同学，这是一款专为“市花名片”项目定制开发的智能体工具，它不仅能帮你制作出色的名片，还能在激发设计灵感、解答软件疑惑、图片生成等方面提供智能支持，更有智能评分功能助你更好地完善作品，快来使用该工具创作你的作品吧！
          </p>
        </div>
      </div>
    </div>

    <div class="min-h-fit">
      <button
        class="btn btn-primary rounded-full min-w-40 font-bold text-xl text-white"
        @click="enterHome"
      >
        进入
      </button>
    </div>

    <!-- <div class="min-h-fit">
      <div class="flex flex-col w-full items-center gap-4 md:flex-row">
        <img
          src="/images/auth-hero@2x.png"
          width="120"
          loading="lazy"
          fetchpriority="high"
        />

        <div class="w-full flex flex-col relative py-7 box-content">
          <input
            v-model="authorizationCode"
            class="input input-bordered input-lg grow rounded-2xl"
            :class="{ 'input-error': errorMessage }"
            placeholder="请填写邀请码"
            @input="errorMessage = ''"
          />
          <div v-if="errorMessage" class="text-error text-sm absolute bottom-0">
            {{ errorMessage }}
          </div>
        </div>
        <button
          :disabled="authorizationCode.trim() === ''"
          class="btn bg-primary rounded-full min-w-20 md:w-40 text-primary-content"
          @click="submitAuthorization"
        >
          提交
        </button>
      </div>

      <p
        class="text-base-content font-bold text-xl text-center bg-white/30 glass rounded-xl"
      >
        本工具邀请码为定向发放，暂不开放自主申请，感谢您的关注与理解
      </p>
    </div> -->
  </div>
</template>

<script setup>
import axios from "axios";
const authorizationCode = ref("");
const errorMessage = ref("");
const basePath = ref("");
const selectedCourseId = ref("1");

function buildAppUrl(path) {
  const base = useRuntimeConfig().public.webBaseUrl.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

async function submitAuthorization() {
  // 清空之前的错误信息
  errorMessage.value = "";

  // 在这里处理授权码的提交逻辑
  if (authorizationCode.value.trim() === "") {
    errorMessage.value = "请输入有效的授权码！";
    return;
  }

  if (basePath.value.trim() === "") {
    errorMessage.value = "需要先选择一门课程";
    return;
  }

  try {
    await axios.get(`/users/authorization`, {
      baseURL: useRuntimeConfig().public.apiBase,
      params: {
        code: authorizationCode.value,
        course_id: selectedCourseId.value,
      },
    });

    window.location.href = buildAppUrl(basePath.value);
  } catch (e) {
    // errorMessage.value = e.response.data.detail.error || "授权码错误";
    errorMessage.value = "授权码错误";
    return;
  }
}

function enterHome() {
  if (basePath.value.trim() === "") {
    errorMessage.value = "需要先选择一门课程";
    return;
  }

  window.location.href = buildAppUrl(basePath.value);
}

const course1 = ref(null);
const course2 = ref(null);
async function goToCourse(course_id) {
  if (typeof window !== "undefined") {
    localStorage.setItem("base_path", `app${course_id}`);
    basePath.value = `app${course_id}`;
    selectedCourseId.value = String(course_id);
  }

  // 移除两个课程的选中样式,恢复透明边框
  course1.value.classList.remove("border-primary", "bg-white");
  course1.value.classList.add("border-transparent", "bg-white/50");
  course2.value.classList.remove("border-primary", "bg-white");
  course2.value.classList.add("border-transparent", "bg-white/50");

  // 给选中的课程添加样式
  if (course_id == 1) {
    course1.value.classList.remove("border-transparent", "bg-white/50");
    course1.value.classList.add("border-primary", "bg-white");
  } else if (course_id == 2) {
    course2.value.classList.remove("border-transparent", "bg-white/50");
    course2.value.classList.add("border-primary", "bg-white");
  }
}

onMounted(() => {
  basePath.value = localStorage.getItem("base_path") || "";

  if (basePath.value == "app1") {
    course1.value.classList.remove("border-transparent", "bg-white/50");
    course1.value.classList.add("border-primary", "bg-white");
  } else if (basePath.value == "app2") {
    course2.value.classList.remove("border-transparent", "bg-white/50");
    course2.value.classList.add("border-primary", "bg-white");
  }
});
</script>
