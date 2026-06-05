<script setup lang="ts">
import { computed } from "vue";
import { AlertCircle, CheckCircle, Clock, LoaderCircle } from "@lucide/vue";

import type { ConversionStatus } from "../api/client";

const props = defineProps<{
  status: ConversionStatus;
}>();

const statusLabel = computed(() => {
  const labels: Record<ConversionStatus, string> = {
    pending: "等待中",
    processing: "转换中",
    completed: "已完成",
    failed: "失败",
  };
  return labels[props.status];
});
</script>

<template>
  <span class="status-pill" :data-status="status">
    <CheckCircle v-if="status === 'completed'" :size="16" aria-hidden="true" />
    <AlertCircle v-else-if="status === 'failed'" :size="16" aria-hidden="true" />
    <LoaderCircle v-else-if="status === 'processing'" :size="16" aria-hidden="true" class="spin" />
    <Clock v-else :size="16" aria-hidden="true" />
    <span>{{ statusLabel }}</span>
  </span>
</template>
