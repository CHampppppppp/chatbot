<template>
  <div class="p-6 w-full mx-auto">
    <h2 class="text-2xl font-bold mb-6 text-center">学生行为记录导出</h2>
    <div class="flex justify-end mb-4">
      <button class="btn btn-primary" @click="exportExcel">导出为 Excel</button>
    </div>
    <div class="overflow-x-auto">
      <table class="table table-zebra w-full">
        <thead>
          <tr>
            <!-- <th>记录ID</th> -->
            <th>类型</th>
            <th>用户账号</th>
            <th>时间</th>
            <th v-for="(v, k) in extraKeys" :key="k">{{ k }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in recordsTable" :key="item.id">
            <!-- <td>{{ item.id }}</td> -->
            <td>{{ item.type }}</td>
            <td>{{ item.user_id }}</td>
            <td>{{ item.create_time }}</td>
            <td v-for="k in extraKeysArr" :key="k" class="whitespace-pre-wrap">
              {{
                (() => {
                  if (k === "time") return formatTime(item[k]);
                  else if (item[k] == null) return "-";
                  else if (k == "content") {
                    try {
                      return JSON.stringify(item[k], null, 2)
                        .replace(/\\n/g, "\n")
                        .replace(/\\t/g, "\t");
                    } catch {
                      return item[k];
                    }
                  } else {
                    return item[k];
                  }
                })()
              }}
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!recordsTable.length" class="text-center text-base-content/40 py-8">
        暂无记录
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useNuxtApp } from "nuxt/app";
import { ref, computed, onMounted } from "vue";
const nuxtApp = useNuxtApp();
const $axios = nuxtApp.$axios as import("axios").AxiosInstance;
const records = ref<any[]>([]);

const metaAttrMap: Record<string, any> = {
  code: "课程码",
  // time: "时间",
  name: "按钮名称",
  content: "行为内容",
  files: "上传文件",
  // full_response: "完整评价",
};

// 计算表格展示用的扁平化数据
const recordsTable = computed(() =>
  Array.isArray(records.value) ? records.value.map(flattenRecord) : []
);

// 计算所有 meta 字段的 key 集合
const extraKeysArr = computed(() => {
  const set = new Set<string>();
  if (Array.isArray(records.value)) {
    records.value.forEach((item) => {
      const meta = parseMeta(item.meta);
      Object.keys(meta).forEach((k) => {
        if (k in metaAttrMap) set.add(k);
      });
    });
  }
  return Array.from(set);
});
const extraKeys = computed(() => {
  const obj: Record<string, true> = {};
  extraKeysArr.value.forEach((k) => {
    obj[metaAttrMap[k]] = true;
  });
  return obj;
});
const typeMap: Record<number, string> = {
  1: "登录",
  2: "点击按钮",
  3: "对话内容",
  4: "校园精灵",
  5: "上传作品",
  6: "评价作品",
};

function parseMeta(meta: string) {
  try {
    return JSON.parse(meta);
  } catch {
    return {};
  }
}

function formatTime(time: string) {
  if (!time) return "-";
  return new Date(time).toLocaleString();
}

const getRecords = async () => {
  try {
    const response = await $axios.get("/records/get");
    records.value = response.data.data || [];
    // console.log("获取记录成功: ", JSON.stringify(response.data.data));
  } catch (error) {
    console.error("获取记录失败: ", error);
    records.value = [];
  }
};

function flattenRecord(item: any) {
  const meta = parseMeta(item.meta);
  return {
    id: item.id,
    type: typeMap[item.type] || item.type,
    user_id: item.user_id,
    create_time: formatTime(item.create_time),
    ...meta,
  };
}

async function exportExcel() {
  if (!records.value.length) return;
  // 只在客户端执行
  if (typeof window === "undefined") return;
  const XLSX = await import("xlsx");
  // 字段映射：表头中文
  const headerMap = {
    // id: "记录ID",
    type: "类型",
    user_id: "用户账号",
    create_time: "时间",
    ...metaAttrMap,
  };
  // 获取所有表格字段顺序
  const fields = [
    // "id",
    "type",
    "user_id",
    "create_time",
    ...extraKeysArr.value,
  ];
  // 构造带中文表头的数据，优先从 meta 取值，避免 content 字段丢失
  const data = records.value.map((item) => {
    const meta = parseMeta(item.meta);
    const row = flattenRecord(item);
    const newRow = {};
    fields.forEach((f) => {
      let val = meta[f] !== undefined ? meta[f] : row[f];
      // content 或任意 Object 类型都格式化
      if (f === "content" && val != null) {
        try {
          val = JSON.stringify(val, null, 2)
            .replace(/\\n/g, "\n")
            .replace(/\\t/g, "\t");
        } catch {
          // fallback
          val = String(val);
        }
      } else if (val && typeof val === "object") {
        try {
          val = JSON.stringify(val, null, 2);
        } catch {
          val = String(val);
        }
      }
      newRow[headerMap[f] ? headerMap[f] : f] = val;
    });
    return newRow;
  });
  // 生成表头顺序
  const header = fields.map((f) => (headerMap[f] ? headerMap[f] : f));
  const ws = XLSX.utils.json_to_sheet(data, { header });
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Records");
  XLSX.writeFile(wb, "records.xlsx");
}

onMounted(() => {
  getRecords();
});
</script>
