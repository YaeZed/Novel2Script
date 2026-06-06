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
    if (status.value.error_message) {
      return "已完成，部分章节待处理";
    }
    return "已完成";
  }
  if (status.value.status === "failed") {
    return "转换失败";
  }
  return `已处理 ${status.value.chapters_done}/${status.value.total_chapters || "?"} 章`;
});

const providerLabel = computed(() => {
  const provider = status.value?.llm_provider;
  if (!provider) {
    return "模式读取中";
  }
  if (provider === "placeholder") {
    return "当前模式：本地占位，不调用外部模型";
  }
  if (provider === "misconfigured") {
    return "当前模式：模型配置需要修正";
  }
  const providerNames: Record<string, string> = {
    anthropic: "Anthropic",
    openai: "OpenAI",
    qwen: "阿里千问",
  };
  return `当前模式：${providerNames[provider] || provider} 真实模型`;
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

      <p v-if="status" class="provider-note" :data-provider="status.llm_provider">
        {{ providerLabel }}
      </p>

      <p v-if="error" class="error-text">{{ error }}</p>
      <p
        v-if="status?.error_message"
        class="status-message"
        :data-kind="status.status === 'completed' ? 'warning' : 'error'"
      >
        {{ status.error_message }}
      </p>

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
