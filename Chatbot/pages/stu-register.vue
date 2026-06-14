<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
    <div class="max-w-2xl mx-auto py-8">
      <!-- 页面标题 -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">学生账号注册</h1>
        <p class="text-gray-600">
          为学生创建新的账号，学生将使用您提供的课程码登录
        </p>
      </div>

      <!-- 注册表单 -->
      <div class="card bg-white shadow-xl">
        <div class="card-body">
          <form @submit.prevent="handleRegister" class="space-y-6">
            <!-- 学生姓名输入 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text text-lg font-medium">学生姓名</span>
                <span class="label-text-alt text-red-500">*</span>
              </label>
              <input
                v-model="studentName"
                type="text"
                placeholder="请输入学生的真实姓名"
                class="input input-bordered input-primary w-full"
                :class="{ 'input-error': errors.studentName }"
                required
              />
              <label v-if="errors.studentName" class="label">
                <span class="label-text-alt text-error">{{
                  errors.studentName
                }}</span>
              </label>
              <label
                v-if="generatedUsername && !errors.studentName"
                class="label"
              >
                <span class="label-text-alt text-info"
                  >生成的用户名: {{ generatedUsername }}</span
                >
              </label>
            </div>

            <!-- 课程码输入 -->
            <div class="form-control">
              <label class="label">
                <span class="label-text text-lg font-medium">课程码</span>
                <span class="label-text-alt text-red-500">*</span>
              </label>
              <input
                v-model="classCode"
                type="text"
                placeholder="请输入课程码"
                class="input input-bordered input-primary w-full"
                :class="{ 'input-error': errors.classCode }"
                required
              />
              <label v-if="errors.classCode" class="label">
                <span class="label-text-alt text-error">{{
                  errors.classCode
                }}</span>
              </label>
              <label class="label">
                <span class="label-text-alt text-gray-500"
                  >学生将使用此课程码登录系统</span
                >
              </label>
            </div>

            <!-- 提交按钮 -->
            <div class="form-control mt-8">
              <button
                type="submit"
                class="btn btn-primary btn-lg w-full"
                :class="{ loading: isSubmitting }"
                :disabled="
                  isSubmitting || !studentName.trim() || !classCode.trim()
                "
              >
                <span v-if="!isSubmitting">注册学生账号</span>
                <span v-else>正在注册...</span>
              </button>
            </div>
          </form>

          <!-- 成功提示 -->
          <div v-if="successMessage" class="alert alert-success mt-6">
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
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{{ successMessage }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from "vue";
import eventBus from "~/utils/eventBus.js";
import pinyin from "pinyin";

// 页面元数据
definePageMeta({
  middleware: "auth",
  title: "学生账号注册",
});

// SEO
useHead({
  title: "学生账号注册",
  meta: [
    {
      name: "description",
      content: "教师为学生注册新账号，学生使用课程码登录系统。",
    },
  ],
});

// 响应式数据
const studentName = ref("");
const classCode = ref("");
const generatedUsername = ref("");
const isSubmitting = ref(false);
const successMessage = ref("");
const errors = reactive({
  studentName: "",
  classCode: "",
});

// 获取 axios 实例
const { $axios } = useNuxtApp();

// 汉字转拼音函数
const chineseToPinyin = (chinese) => {
  try {
    // 使用 pinyin 库进行转换，不带声调，小写
    const pinyinArray = pinyin(chinese, {
      style: pinyin.STYLE_NORMAL,
      heteronym: false,
    });
    return pinyinArray.flat().join("").toLowerCase();
  } catch (error) {
    console.error("拼音转换失败:", error);
    // 如果拼音转换失败，使用简化的映射表作为备选
    const pinyinMap = {
      张: "zhang",
      王: "wang",
      李: "li",
      赵: "zhao",
      陈: "chen",
      刘: "liu",
      杨: "yang",
      黄: "huang",
      周: "zhou",
      吴: "wu",
      徐: "xu",
      孙: "sun",
      朱: "zhu",
      马: "ma",
      胡: "hu",
      郭: "guo",
      林: "lin",
      何: "he",
      高: "gao",
      梁: "liang",
      郑: "zheng",
      罗: "luo",
      宋: "song",
      谢: "xie",
      唐: "tang",
      韩: "han",
      冯: "feng",
      于: "yu",
      董: "dong",
      萧: "xiao",
      程: "cheng",
      曹: "cao",
      袁: "yuan",
      邓: "deng",
      许: "xu",
      傅: "fu",
      沈: "shen",
      曾: "zeng",
      彭: "peng",
      吕: "lv",
      // 常见名字
      明: "ming",
      华: "hua",
      建: "jian",
      文: "wen",
      军: "jun",
      伟: "wei",
      强: "qiang",
      磊: "lei",
      洋: "yang",
      勇: "yong",
      艳: "yan",
      娟: "juan",
      敏: "min",
      静: "jing",
      丽: "li",
      红: "hong",
      玉: "yu",
      秀: "xiu",
      英: "ying",
      慧: "hui",
    };

    return chinese
      .split("")
      .map((char) => pinyinMap[char] || char.toLowerCase())
      .join("");
  }
};

// 监听学生姓名变化，自动生成用户名
watch(studentName, (newName) => {
  if (newName.trim()) {
    generatedUsername.value = chineseToPinyin(newName.trim());
    errors.studentName = "";
  } else {
    generatedUsername.value = "";
  }
});

// 监听课程码变化
watch(classCode, () => {
  errors.classCode = "";
});

// 验证表单
const validateForm = () => {
  let isValid = true;

  // 清空之前的错误
  Object.keys(errors).forEach((key) => {
    errors[key] = "";
  });

  // 验证学生姓名
  if (!studentName.value.trim()) {
    errors.studentName = "请输入学生姓名";
    isValid = false;
  } else if (studentName.value.trim().length < 2) {
    errors.studentName = "学生姓名至少需要2个字符";
    isValid = false;
  }

  // 验证课程码
  if (!classCode.value.trim()) {
    errors.classCode = "请输入课程码";
    isValid = false;
  } else if (classCode.value.trim().length < 4) {
    errors.classCode = "课程码至少需要4个字符";
    isValid = false;
  }

  return isValid;
};

// 处理注册
const handleRegister = async () => {
  if (!validateForm()) {
    return;
  }

  isSubmitting.value = true;
  successMessage.value = "";

  try {
    const response = await $axios.post("/users/register", {
      real_name: studentName.value,
      username: generatedUsername.value,
      class_code: classCode.value.trim(),
    });

    if (response.data) {
      successMessage.value = `学生 ${studentName.value} 注册成功！用户名为：${
        generatedUsername.value
      }，班级码为：${classCode.value.trim()}`;

      // 重置表单
      studentName.value = "";
      classCode.value = "";
      generatedUsername.value = "";

      // 3秒后清除成功消息
      //   setTimeout(() => {
      //     successMessage.value = "";
      //   }, 3000);
    }
  } catch (error) {
    console.error("注册失败:", error);
    // 错误已通过 eventBus 在 axios 拦截器中处理
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
/* 页面过渡动画 */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 自定义样式 */
.card {
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1),
    0 10px 10px -5px rgb(0 0 0 / 0.04);
}

.input:focus {
  transform: scale(1.01);
  transition: transform 0.2s ease;
}

.btn {
  transition: all 0.2s ease;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
}
</style>
