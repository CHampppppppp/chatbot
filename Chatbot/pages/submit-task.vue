<template>
  <div
    class="min-h-screen bg-base-200 flex flex-col items-center justify-center p-4"
  >
    <!-- 返回主页按钮 -->
    <NuxtLink to="/">
      <button class="absolute top-5 left-5 btn btn-square">
        <svg
          t="1761675116435"
          class="icon"
          viewBox="0 0 1024 1024"
          version="1.1"
          xmlns="http://www.w3.org/2000/svg"
          p-id="6306"
          width="30"
          height="30"
        >
          <path
            d="M862.485 481.154H234.126l203.3-203.3c12.497-12.497 12.497-32.758 0-45.255s-32.758-12.497-45.255 0L135.397 489.373c-12.497 12.497-12.497 32.758 0 45.254l256.774 256.775c6.249 6.248 14.438 9.372 22.627 9.372s16.379-3.124 22.627-9.372c12.497-12.497 12.497-32.759 0-45.255l-203.3-203.301h628.36c17.036 0 30.846-13.81 30.846-30.846s-13.81-30.846-30.846-30.846z"
            fill="currentColor"
            p-id="6307"
          ></path>
        </svg>
      </button>
    </NuxtLink>
    <!-- 文件名提示 -->
    <div
      role="alert"
      class="alert alert-info fixed z-50 top-4 text-white max-w-max"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        class="h-6 w-6 shrink-0 stroke-current"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        ></path>
      </svg>
      <span>文件名格式：平台登录账号+电子板报名称</span>
    </div>

    <div class="card w-full max-w-lg bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-3xl mb-6">作品智能评分</h2>
        <!-- Form Start -->
        <form @submit.prevent="handleSubmit">
          <!-- File Input -->
          <div class="form-control mb-4 w-full h-35">
            <label name="fileInput">
              <div
                class="glass border-2 border-dashed border-base-300 rounded-lg p-6 text-center cursor-pointer hover:bg-base-200 transition-colors duration-300 h-auto flex items-center justify-center"
                @dragover.prevent
                @drop.prevent="handleDropFiles"
              >
                <input
                  type="file"
                  ref="fileInput"
                  @change="handleFileChange"
                  class="hidden"
                  :disabled="isUploading"
                  accept=".jpeg,.jpg,.png,.bmp,.tiff,.webp"
                  multiple
                />
                <div
                  class="flex flex-col items-center justify-center space-y-2 pointer-events-none"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-12 w-12 text-base-content/50"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <p class="text-base-content/80">
                    <span class="text-info font-semibold">点击上传</span
                    >或拖拽文件到此
                  </p>
                </div>
              </div>
            </label>
            <div class="flex justify-between">
              <label class="label mt-2"> 单个文件最大5MB</label>
              <label class="label mt-2"> 支持拖拽上传</label>
            </div>
          </div>

          <!-- 文件预览 -->
          <div class="max-h-64 overflow-y-auto px-2" v-if="selectedFiles">
            <div
              v-for="(selectedFile, index) in selectedFiles"
              :key="index"
              class="preview-file my-4 p-3 border border-base-300 rounded-lg text-sm bg-base-200 glass flex items-center justify-between"
            >
              <div
                class="preview-info flex items-center justify-between w-full"
              >
                <div>
                  <p><strong>文件:</strong> {{ selectedFile.name }}</p>
                  <p>
                    <strong>大小:</strong>
                    {{ (selectedFile.size / 1024).toFixed(2) }} KB
                  </p>
                </div>

                <!-- 预览缩略图 -->
                <div v-if="!selectedFile.type.includes('pdf')" class="avatar">
                  <div class="w-12 rounded">
                    <img :src="createObjectURL(selectedFile)" />
                  </div>
                </div>
              </div>

              <!-- 删除按钮 -->
              <div
                class="delete-btn hidden flex justify-center items-center m-2"
                @click="deleteFile(index)"
              >
                <img src="/public/images/删除.svg" class="max-w-6 max" />
              </div>
            </div>
          </div>

          <!-- 文件过大警报 -->
          <div role="alert" class="alert alert-error" v-if="oversize">
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
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>文件大小超过限制</span>
          </div>

          <!-- 进度条 -->
          <div v-if="isUploading" class="w-full mb-4">
            <progress
              class="progress progress-primary w-full"
              :value="uploadProgress"
              max="100"
            ></progress>
            <p class="text-center text-sm mt-1">{{ uploadProgress }}%</p>
          </div>

          <!-- 警告信息 -->
          <div
            role="alert"
            v-if="alertMessage"
            class="alert shadow-lg mb-4 flex justify-start items-center"
            :class="alertType"
          >
            <div>
              <svg
                v-if="uploadStatus === 'success'"
                xmlns="http://www.w3.org/2000/svg"
                class="stroke-current flex-shrink-0 h-6 w-6"
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
              <svg
                v-if="uploadStatus === 'error'"
                xmlns="http://www.w3.org/2000/svg"
                class="stroke-current flex-shrink-0 h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{{ alertMessage }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="card-actions justify-end mt-6">
            <button
              type="submit"
              class="btn btn-primary w-full"
              :class="{ loading: isUploading }"
              :disabled="!selectedFiles || isUploading || oversize"
            >
              {{ isUploading ? "上传中..." : "提交" }}
            </button>
            <span class="text-sm text-gray-500 m-auto">
              评分结果由AI生成，仅供参考
            </span>
          </div>
        </form>
        <!-- Form End -->
      </div>
    </div>

    <!-- 评价内容 -->
    <div
      class="glass rounded-lg w-10/12 bg-base-100 shadow-xl my-4 p-4 overflow-auto"
    >
      <h3 class="text-xl font-extrabold subpixel-antialiased">作品评价</h3>
      <span
        class="loading loading-spinner text-primary"
        v-if="uploadStatus == 'success' && !justifyContent"
      ></span>
      <MarkdownIt
        :breaks="true"
        :html="true"
        :source="justifyContent"
        :highlight="{
          highlight: (str, lang) => {
            if (lang && hljs.getLanguage(lang)) {
              try {
                return hljs.highlight(str, { language: lang }).value;
              } catch (__) {}
            }
            return '';
          },
        }"
        class="text-balance text-pretty subpixel-antialiased overflow-auto"
      />
    </div>
  </div>
</template>

<script setup>
import { records } from "~/api/platform";
import MarkdownIt from "vue3-markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/monokai.css";

const { $axios } = useNuxtApp();

// 添加路由守卫
definePageMeta({
  middleware: "auth",
});

// SEO
useHead({
  title: "提交作品",
  meta: [
    {
      name: "description",
      content: "提交您的电子板报作品，展示您的创意和才华。",
    },
  ],
});

const fileInput = ref(null);
const oversize = ref(false);
const previewRef = ref(null);
const selectedFiles = ref(null);
const uploadProgress = ref(0);
const uploadStatus = ref("idle"); // idle, uploading, success, error
const alertMessage = ref("");

// 评分提示词
const judgePrompt = `[角色]
你是一名资深的信息科技教育评价专家，同时也是项目式学习（PBL）的指导教师。你正在评审一份来自学生提交的“向世界介绍我的学校”主题的数字作品——“学校数字海报”。 
[背景]
这份“学校数字海报”要求学生综合运用多媒体（文字、图片、音频、视频等），制作一份图文并茂、有声有色的作品，来介绍他们的学校，包括学校历史、设施、学生生活、国际交流等元素，旨在向全球观众展示学校的魅力和独特之处。 
[任务]
你的核心任务是根据以下六个维度的“评价标准”，对学生的作品进行全面、深入的评价，提供具体的、建设性的反馈，并给出一个量化的分数。 
[评价标准]
你必须严格按照以下六个维度逐一进行分析：
科学性: 作品主题明确，内容合法、合理；注明资源的来源。
艺术性: 作品版式布局合理、层次清晰、色彩搭配美观。
技术性: 作品中的文字、图片、音频、视频等资源的处理与表达恰当合理。
完整性: 作品有主题页、内容页，结构完整。
创新性: 作品构思、创作方式及媒体运用等方面具有独到之处。
丰富性: 作品多方位、多角度地诠释学习主题，图文并茂并增强交互性。 
[评分规则]
总分为 100 分。如果作品内容和主题无关，则直接指出并判定为0分。
以上六个维度的占比相同，即每个维度满分 100 分，最后总分 = (科学性 + 艺术性 + 技术性 + 完整性 + 创新性 + 丰富性) / 6。
在为每个维度打分时，请使用 5 分制进行内部评估，然后转换为百分制（例如：5 分 = 100 分，4 分 = 80 分，3 分 = 60 分，2 分 = 40 分，1 分 = 20 分，0 分 = 0 分）。
必须在评价报告中清晰地展示每个维度的得分和最终总分。 
[输入]
[传递的“{"image": 图像文件}”结构的列表] 
[输出要求]
请你按照以下结构化格式生成评价报告，确保每个维度都有清晰的评价、反馈和得分： 
“学校数字海报”作品评价报告
一、 总体评价
[在此处简要概述你对作品的整体印象，点明作品最突出的亮点和最需要改进的地方。]
二、 量化评分概览
科学性: [得分] / 100
艺术性: [得分] / 100
技术性: [得分] / 100
完整性: [得分] / 100
创新性: [得分] / 100
丰富性: [得分] / 100
最终总分 (平均分): [计算总分] / 100
三、 分项评价与反馈 
1.科学性 (得分: [填写得分]/100)
评价: [基于标准，评价作品的主题是否明确？内容是否科学合理？是否正确引用了来源？]
反馈 (优点): [具体说明在科学性方面做得好的地方。]
反馈 (改进建议): [具体说明在内容准确性或资源引用方面可以如何改进。] 
2.艺术性 (得分: [填写得分]/100)
评价: [基于标准，评价作品的版式、层次感和色彩搭配。]
反馈 (优点): [具体说明在视觉设计上出彩的地方，例如“色彩搭配和谐”或“布局重点突出”。]
反馈 (改进建议): [具体说明在美观性上可以提升的地方，例如“建议调整字体大小以增强可读性”或“部分图片分辨率可以更高”。] 
3.技术性 (得分: [填写得分]/100)
评价: [基于标准，评价多媒体（文、图、音、视频）的运用是否恰当、流畅？]
反馈 (优点): [具体说明技术处理的亮点，例如“音频清晰，背景音乐搭配得当”或“视频剪辑流畅”。]
反馈 (改进建议): [具体说明技术处理的不足，例如“部分图片被拉伸变形”或“音频音量忽高忽低”。] 
4.完整性 (得分: [填写得分]/100)
评价: [基于标准，评价作品结构是否完整，是否包含主题页和必要的内容页。]
反馈 (优点): [具体说明结构完整性的表现，例如“导航清晰，结构完整”。]
反馈 (改进建议): [具体说明在结构上可能需要补充的地方，例如“建议增加一个‘国际交流’页面”或“缺少关于学校愿景的介绍”。] 
5.创新性 (得分: [填写得分]/100)
评价: [基于标准，评价作品在概念、表现形式、互动方式或信息呈现上是否具有新颖独到的地方。]
反馈 (优点): [具体说明在创新性方面做得好的地方，例如“独特的交互设计，让用户能以新颖的方式探索学校信息”。]
反馈 (改进建议): [具体说明在创新性方面可以进一步突破的地方，例如“可以考虑增加更多互动玩法，例如虚拟校园游览或全球问答”或“尝试更具颠覆性的视觉风格，跳出传统海报模式”。] 
6.丰富性 (得分: [填写得分]/100)
评价: [基于标准，评价作品包含的信息种类、深度和广度是否足够，是否能提供多维度的认识。]
反馈 (优点): [具体说明在内容丰富度上做得好的地方，例如“不仅介绍了学校设施，还详细阐述了学生生活和国际项目”或“包含了学校在不同文化背景下的表现，以及相关的全球故事”。]
反馈 (改进建议): [具体说明在内容上可以补充或拓展的地方，例如“建议增加学校在可持续发展中的作用”或“可以加入国际学生的小故事或跨文化交流案例，增加趣味性”。]
`;

const isUploading = computed(() => uploadStatus.value === "uploading");
const alertType = computed(() => {
  if (uploadStatus.value === "success") return "alert-success";
  if (uploadStatus.value === "error") return "alert-error";
  return "";
});

const createObjectURL = (file) => URL.createObjectURL(file);
const revokeObjectURL = (url) => URL.revokeObjectURL(url);

const isOversize = (files) => {
  let fileArray = Array.from(files);
  oversize.value = false;
  fileArray.forEach((file) => {
    if (file.size > 5 * 1024 * 1024) {
      oversize.value = true;
      return;
    }
  });
};

function removeDragData(ev) {
  if (ev.dataTransfer.items) {
    ev.dataTransfer.items.clear();
  }
}

function handleDropFiles(ev) {
  console.log("ev = ", ev);
  if (ev.dataTransfer.items) {
    for (var i = 0; i < ev.dataTransfer.items.length; i++) {
      if (ev.dataTransfer.items[i].kind === "file") {
        var file = ev.dataTransfer.items[i].getAsFile();
        console.log("... file[" + i + "].name = " + file.name);
        selectedFiles.value = [...(selectedFiles.value || []), file];
      }
    }
  } else {
    for (var i = 0; i < ev.dataTransfer.files.length; i++) {
      console.log(
        "... file[" + i + "].name = " + ev.dataTransfer.files[i].name
      );
      selectedFiles.value = [...(selectedFiles.value || []), file];
    }
  }

  isOversize(selectedFiles.value);

  // Pass event to removeDragData for cleanup
  removeDragData(ev);
}

const handleFileChange = (event) => {
  let files = event.target.files;
  if (files) {
    selectedFiles.value = files;
    uploadStatus.value = "idle";
    alertMessage.value = "";
  }

  oversize.value = false;
  files = Array.from(files);

  isOversize(files);

  files.forEach(() => {
    revokeObjectURL(previewRef.value?.src);
  });
};

const deleteFile = (index) => {
  if (selectedFiles.value && selectedFiles.value.length > index) {
    const filesArray = Array.from(selectedFiles.value);
    filesArray.splice(index, 1);
    selectedFiles.value = filesArray;
    isOversize(selectedFiles.value);
  }
};

const resetForm = () => {
  selectedFiles.value = null;
  uploadProgress.value = 0;

  if (fileInput.value) {
    fileInput.value.value = "";
  }
};

const simulateUpload = () => {
  return new Promise((resolve, reject) => {
    alertMessage.value = "";
    uploadStatus.value = "uploading";
    uploadProgress.value = 0;

    const interval = setInterval(() => {
      uploadProgress.value += 15;
      if (uploadProgress.value >= 100) {
        clearInterval(interval);
        resolve();
      }
    }, 200);
  });
};

const handleSubmit = async () => {
  if (!selectedFiles.value) {
    alertMessage.value = "请先选择文件";
    uploadStatus.value = "error";
    return;
  }
  if (oversize.value) {
    alertMessage.value = "文件大小超过限制";
    uploadStatus.value = "error";
    return;
  }

  // 通义万相支持的图像类型
  const accept_types = new Set([
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/bmp",
    "image/tiff",
    "image/webp",
  ]);
  for (const file of selectedFiles.value) {
    if (!accept_types.has(file.type)) {
      alertMessage.value =
        "文件格式错误，支持上传格式：jpeg, jpg, png, bmp, tiff, webp";
      uploadStatus.value = "error";
      return;
    }
  }

  try {
    const formData = new window.FormData();

    // 正确处理文件数据 - 遍历文件列表并逐个添加
    if (selectedFiles.value) {
      const filesArray = Array.from(selectedFiles.value);
      filesArray.forEach((file) => {
        formData.append("homework", file);
      });
    }

    await $axios.post("/tasks/submit", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    await simulateUpload();

    alertMessage.value = "文件上传成功，请等待评价结果！";

    await fetchScore(selectedFiles.value);

    uploadStatus.value = "success";
  } catch (error) {
    uploadStatus.value = "error";
    alertMessage.value = error.response.data.detail.error;
  }
};

// 获取作品评分
import { fetchChatStream } from "~/api/platform";
const justifyContent = ref("这里会显示评价内容");
let lastJudgeController = null;
async function fetchScore(files) {
  const config = useRuntimeConfig();
  let formdata = new window.FormData();
  for (const file of files) {
    formdata.append("files", file);
  }
  formdata.append("prompt", judgePrompt);

  // 先终止上一次连接
  if (lastJudgeController) {
    lastJudgeController.abort();
    lastJudgeController = null;
  }

  // 清空之前的内容
  justifyContent.value = "";
  fetchChatStream(
    config.public.apiBase + "/tasks/judge",
    formdata,
    (event, controller) => {
      // 保存当前 controller
      if (!lastJudgeController) lastJudgeController = controller;
      // 追加流式内容
      if (event.data) {
        if (event.data === "[DONE]") {
          // 数据埋点
          records(6, {
            time: new Date().toISOString(),
            files: () => {
              let uploadFiles = [];
              for (const file of files) {
                uploadFiles.push(file);
              }
              return uploadFiles;
            },
            full_response: justifyContent.value,
          });

          // 重置变量
          controller.abort();
          lastJudgeController = null;
        } else {
          justifyContent.value += event.data;
        }
      }
    }
  );
}
</script>

<style scoped>
.delete-btn:hover {
  cursor: pointer;
}

.preview-file:hover {
  .preview-info {
    width: 85%;
    transition: all 0.5s linear;
  }

  .delete-btn {
    width: auto;
    display: inline-flex;
  }
}
</style>
