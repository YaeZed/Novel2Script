<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { ArrowRight, FileUp, Sparkles } from "@lucide/vue";

import { createConversion } from "../api/client";

const router = useRouter();
const mode = ref<"text" | "file" | "sample">("text");
const text = ref("");
const selectedFile = ref<File | null>(null);
const isSubmitting = ref(false);
const error = ref("");

const sampleText = `第一章 雨夜
雨声落在旧戏院的玻璃棚顶上。
林照：今晚不能再等了。
沈岚抬头，看见后台门缝里漏出一线冷光。

第二章 后台
灯牌忽明忽暗，木地板发出轻响。
沈岚：你听见了吗？
林照没有回答，只把那封皱掉的信塞进口袋。`;

const canSubmit = computed(() => {
  if (mode.value === "file") {
    return Boolean(selectedFile.value);
  }
  if (mode.value === "sample") {
    return true;
  }
  return text.value.trim().length > 0;
});

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  selectedFile.value = target.files?.[0] ?? null;
}

async function submit() {
  if (!canSubmit.value || isSubmitting.value) {
    return;
  }
  isSubmitting.value = true;
  error.value = "";

  try {
    const response = await createConversion({
      text: mode.value === "sample" ? sampleText : text.value,
      file: mode.value === "file" ? selectedFile.value ?? undefined : undefined,
    });
    await router.push(`/progress/${response.task_id}`);
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "提交失败";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <section class="page-grid upload-page">
    <div class="panel input-panel">
      <div class="page-heading">
        <p class="eyebrow">Novel to Script</p>
        <h1>生成第一版剧本 YAML</h1>
      </div>

      <div class="segmented" role="tablist" aria-label="输入方式">
        <button :class="{ active: mode === 'text' }" type="button" @click="mode = 'text'">粘贴</button>
        <button :class="{ active: mode === 'file' }" type="button" @click="mode = 'file'">文件</button>
        <button :class="{ active: mode === 'sample' }" type="button" @click="mode = 'sample'">示例</button>
      </div>

      <textarea
        v-if="mode === 'text'"
        v-model="text"
        class="source-input"
        rows="16"
        placeholder="粘贴小说文本"
      />

      <label v-else-if="mode === 'file'" class="file-drop">
        <FileUp :size="28" aria-hidden="true" />
        <span>{{ selectedFile?.name || "选择 TXT 或 EPUB" }}</span>
        <input type="file" accept=".txt,.epub,text/plain,application/epub+zip" @change="onFileChange" />
      </label>

      <textarea v-else class="source-input" rows="16" :value="sampleText" readonly />

      <p v-if="error" class="error-text">{{ error }}</p>

      <button class="primary-action" type="button" :disabled="!canSubmit || isSubmitting" @click="submit">
        <Sparkles v-if="isSubmitting" :size="18" aria-hidden="true" class="spin" />
        <ArrowRight v-else :size="18" aria-hidden="true" />
        <span>{{ isSubmitting ? "转换中" : "开始转换" }}</span>
      </button>
    </div>

    <aside class="panel snapshot-panel" aria-label="输出预览">
      <div class="yaml-preview">
        <span>acts:</span>
        <span>  - number: 1</span>
        <span>    scenes:</span>
        <span>      - title: 第一章 雨夜</span>
        <span>        beats:</span>
        <span>          - type: dialogue</span>
      </div>
    </aside>
  </section>
</template>
