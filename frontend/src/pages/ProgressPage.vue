<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { ArrowRight, RefreshCw } from "@lucide/vue";

import StatusPill from "../components/StatusPill.vue";
import { useTaskPolling } from "../composables/useTaskPolling";

const props = defineProps<{
  taskId: string;
}>();

const { status, error, isDone, start, refresh } = useTaskPolling(props.taskId);

const progressLabel = computed(() => {
  if (!status.value) {
    return "准备中";
  }
  if (status.value.status === "completed") {
    return "已完成";
  }
  if (status.value.status === "failed") {
    return "转换失败";
  }
  return `已处理 ${status.value.chapters_done}/${status.value.total_chapters || "?"} 章`;
});

onMounted(start);
</script>

<template>
  <section class="single-column">
    <div class="panel progress-panel">
      <div class="progress-header">
        <div>
          <p class="eyebrow">Task {{ taskId.slice(0, 8) }}</p>
          <h1>{{ progressLabel }}</h1>
        </div>
        <StatusPill v-if="status" :status="status.status" />
      </div>

      <div class="meter" aria-label="转换进度">
        <span :style="{ width: `${status?.progress ?? 8}%` }"></span>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
      <p v-if="status?.error_message" class="error-text">{{ status.error_message }}</p>

      <div class="action-row">
        <button class="secondary-action" type="button" @click="refresh">
          <RefreshCw :size="17" aria-hidden="true" />
          <span>刷新</span>
        </button>
        <RouterLink
          v-if="isDone && status?.status === 'completed'"
          class="primary-action"
          :to="`/compare/${taskId}`"
        >
          <ArrowRight :size="18" aria-hidden="true" />
          <span>打开对照</span>
        </RouterLink>
      </div>
    </div>
  </section>
</template>
