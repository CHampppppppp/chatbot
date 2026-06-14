<template>
  <div class="min-h-screen flex items-center justify-center bg-base-200">
    <!-- 全局提示 -->
    <div
      v-if="generated_code"
      role="alert"
      class="alert alert-success alert-vertical sm:alert-horizontal fixed top-2 max-w-fit"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-6 w-6 shrink-0 stroke-current"
        fill="none"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <div>
        <h3 class="font-bold">生成课程码成功！</h3>
        <div class="text-xs">生成的课程码是：{{ generated_code }}</div>
      </div>
      <button
        v-if="!copied"
        class="btn btn-sm btn-soft"
        id="copy-btn"
        :data-clipboard-text="generated_code"
        @click="() => (copied = true)"
      >
        复制课程码
      </button>
      <button class="btn btn-sm" v-else disabled>
        <svg
          t="1753847506778"
          class="icon"
          viewBox="0 0 1024 1024"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          p-id="5091"
          width="20"
          height="20"
        >
          <path
            d="M892.8 245.12L440.32 697.6 259.2 516.48a32 32 0 1 0-45.44 45.44l226.56 226.56 45.44-45.44 452.48-452.48a32 32 0 1 0-45.44-45.44z"
            fill="currentColor"
            p-id="5092"
          ></path>
        </svg>
      </button>
    </div>

    <div class="bg-base-100 rounded-lg shadow-lg p-8 max-w-sm w-full">
      <form @submit="submitForm">
        <div class="mb-4">
          <label>账号</label>
          <label
            for="userid"
            class="validator text-base-content text-sm font-bold mb-2"
          >
            <div
              class="flex items-center rounded-lg px-2 border-solid border-2 border-base-300"
            >
              <svg
                class="h-[1em] opacity-50"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
              >
                <g
                  stroke-linejoin="round"
                  stroke-linecap="round"
                  stroke-width="2.5"
                  fill="none"
                  stroke="currentColor"
                >
                  <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </g>
              </svg>
              <input
                type="text"
                id="userid"
                v-model="userid"
                class="w-full p-2 rounded-lg focus:outline-none"
                required
                @input="() => (useridRequired = false)"
              />
            </div>
          </label>

          <p v-if="useridRequired" class="text-error text-xs">请输入账号!</p>
        </div>
        <div class="mb-4">
          <label>课程码</label>
          <label
            for="password"
            class="validator text-base-content text-sm font-bold"
          >
            <div
              class="flex items-center rounded-lg px-2 border-solid border-2 border-base-300"
            >
              <svg
                class="h-[1em] opacity-50"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
              >
                <g
                  stroke-linejoin="round"
                  stroke-linecap="round"
                  stroke-width="2.5"
                  fill="none"
                  stroke="currentColor"
                >
                  <path
                    d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"
                  ></path>
                  <circle
                    cx="16.5"
                    cy="7.5"
                    r=".5"
                    fill="currentColor"
                  ></circle>
                </g>
              </svg>
              <input
                type="password"
                id="password"
                v-model="password"
                class="w-full p-2 rounded-lg focus:outline-none focus:border-primary"
                required
              />
            </div>
          </label>
        </div>

        <button
          type="submit"
          class="w-full bg-primary text-primary-content p-2 rounded-lg hover:bg-primary/90"
        >
          登录
        </button>
      </form>
      <button
        type="click"
        class="w-full bg-success text-success-content p-2 rounded-lg hover:bg-success/90 mt-4"
        @click="generateCode"
      >
        生成课程码
      </button>
    </div>
  </div>
</template>

<script setup>
import eventBus from "~/utils/eventBus";
import ClipboardJS from "clipboard";
import { navigateTo } from "nuxt/app";

const { $axios } = useNuxtApp();

// SEO
useHead({
  title: "登录",
  meta: [
    {
      name: "description",
      content: "校园精灵智能体登录页面，输入账号和课程码进行登录。",
    },
  ],
});

const userid = ref("");
const password = ref("");
const generated_code = ref(null);
const copied = ref(false);
const useridRequired = ref(false);
let clipboard = null;

const submitForm = async (event) => {
  event.preventDefault();
  const data = new window.FormData();
  data.append("username", userid.value);
  data.append("password", password.value);
  const response = await $axios.post("/users/login", data);
  if (response.status == "200") {
    console.log("登录成功", response.data);
    await navigateTo("/letter");
  }
};

const generateCode = async () => {
  if (userid.value.trim() === "") {
    useridRequired.value = true;
    return;
  }

  const response = await $axios.get("/classes/create", {
    params: {
      user_id: userid.value,
    },
  });
  if (response.data?.data) {
    generated_code.value = response.data.data;
  }
};

// 初始化 Clipboard.js
onMounted(() => {
  clipboard = new ClipboardJS("#copy-btn");
});

// 清理资源
onUnmounted(() => {
  if (clipboard) {
    clipboard.destroy();
  }
});
</script>
