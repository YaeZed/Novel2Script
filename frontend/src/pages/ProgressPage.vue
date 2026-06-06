<script setup lang="ts">
import { computed, onMounted } from "vue";
import { ArrowRight, RefreshCw } from "@lucide/vue";

import AppButton from "../components/AppButton.vue";
import SectionHeader from "../components/SectionHeader.vue";
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
    return "正在读取处理方式";
  }
  if (provider === "placeholder") {
    return "当前处理方式：本地演示，不连接在线智能服务";
  }
  if (provider === "misconfigured") {
    return "当前处理方式需要管理员修正";
  }
  const providerNames: Record<string, string> = {
    anthropic: "Anthropic",
    openai: "OpenAI",
    qwen: "阿里千问",
  };
  return `当前处理方式：${providerNames[provider] || "在线智能服务"}`;
});

onMounted(start);
</script>

<template>
  <section class="single-column">
    <div class="panel progress-panel">
      <SectionHeader :eyebrow="`Task ${taskId.slice(0, 8)}`" :title="progressLabel">
        <StatusPill v-if="status" :status="status.status" />
      </SectionHeader>

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
        <AppButton variant="secondary" @click="refresh">
          <RefreshCw :size="17" aria-hidden="true" />
          <span>刷新</span>
        </AppButton>
        <AppButton
          v-if="isDone && status?.status === 'completed'"
          :to="`/compare/${taskId}`"
        >
          <ArrowRight :size="18" aria-hidden="true" />
          <span>打开对照</span>
        </AppButton>
      </div>
    </div>
  </section>
</template>
