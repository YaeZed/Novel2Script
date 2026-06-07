<script setup lang="ts">
import { CheckCircle2, Download } from "@lucide/vue";

import AppButton from "./AppButton.vue";
import SectionHeader from "./SectionHeader.vue";

defineProps<{
  title: string;
  detail: string;
  status: "idle" | "dirty" | "valid" | "invalid";
  canDownload: boolean;
}>();

const emit = defineEmits<{
  download: [];
  validate: [];
}>();
</script>

<template>
  <SectionHeader eyebrow="剧本草稿" :title="title">
    <AppButton variant="icon" aria-label="检查剧本格式" title="检查剧本格式" @click="emit('validate')">
      <CheckCircle2 :size="17" aria-hidden="true" />
    </AppButton>
    <AppButton
      variant="icon"
      aria-label="下载剧本文件"
      title="下载剧本文件"
      :disabled="!canDownload"
      @click="emit('download')"
    >
      <Download :size="17" aria-hidden="true" />
    </AppButton>
  </SectionHeader>

  <p v-if="detail" class="validation-note" :data-status="status">
    {{ detail }}
  </p>
</template>
