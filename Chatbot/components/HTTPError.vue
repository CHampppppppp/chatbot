<template>
  <transition name="fade">
    <div
      class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/25"
    >
      <div
        role="alert"
        class="alert alert-error shadow-xl relative max-w-fit w-full flex flex-col items-center animate-scale-in"
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
            d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span class="font-bold text-2xl">{{ message }}</span>
        <span>{{ detail }}</span>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    default: "",
  },
  detail: {
    type: Error,
    default: "",
  },
});
</script>

<style scoped>
@keyframes scale-in {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
.animate-scale-in {
  animation: scale-in 0.3s;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
