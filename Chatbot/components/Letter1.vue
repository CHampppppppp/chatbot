<template>
  <!-- 信件内容 -->
  <div>
    <h2 class="text-2xl font-black subpixel-antialiased">
      《向世界介绍我的学校作品征集》
    </h2>
    <h3>亲爱的同学们：</h3>
    <p>
      学校每年的校庆活动是学校发展的一个重要里程碑。为了庆祝这一盛大节日,
      我们将组织一系列丰富多彩的活动,
      鼓励全校师生共同回顾学校的发展历程、展望学校未来,
      向世界各地展现学校的风采和特色。
    </p>
    <p>
      学校决定在小学高年级征集<strong class="text-blue-600"
        >“向世界介绍我的学校”</strong
      >作品。参选学生需通过信息技术软件制作一份<strong>主题电子板报</strong>,
      电子板报需至少包含两部分内容：<strong class="text-blue-600"
        >一是现实中学校的亮点特色</strong
      >
      (例如, 校园特色场所、校园特色文化、学生的一天) ,
      <strong class="text-blue-600">二是你心中未来的理想学校</strong>。
    </p>
    <p>
      最佳作品的创作者将被授予“校园数字宣传员”荣誉证书。这是一次展示个人才华、传递校园文化的珍贵机会,
      期待同学们用自己的巧思和热情, 让世界看到我们学校的风采!
    </p>
    <div class="date">{{ currentDate }}</div>

    <NuxtLink to="/" class="button-container w-fit mx-auto">
      <button class="btn btn-primary w-40 rounded-full mx-auto">
        参与活动
      </button>
    </NuxtLink>
  </div>
</template>

<script setup>
import { ref } from "vue";
const now = new Date();
const currentDate = `${now.getFullYear()}年${
  now.getMonth() + 1
}月${now.getDate()}日`;
</script>
<style scoped>
/* 按钮样式 */
button {
  background: linear-gradient(135deg, #9681e6 0%, #764ba2 100%);
  border: none;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

@media (max-width: 600px) {
  /* 按钮响应式样式 */
  .button-container {
    width: 100% !important;
    margin: 15px auto 0 auto !important;
  }

  button {
    width: 100%;
    font-size: 14px;
    padding: 10px 20px;
    min-width: unset;
  }
}
</style>
