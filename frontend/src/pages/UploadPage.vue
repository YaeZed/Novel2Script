<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowRight,
  ClipboardPaste,
  FileArchive,
  FileText,
  FileUp,
  Sparkles,
} from "@lucide/vue";

import AppButton from "../components/AppButton.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { createConversion } from "../api/client";

const router = useRouter();
const mode = ref<"text" | "file" | "sample">("text");
const text = ref("");
const selectedFile = ref<File | null>(null);
const isSubmitting = ref(false);
const error = ref("");
const fileInput = ref<HTMLInputElement | null>(null);

const sampleText = `第一章 雨夜
雨声落在旧戏院的玻璃棚顶上。
林照：今晚不能再等了。
沈岚抬头，看见后台门缝里漏出一线冷光。

第二章 后台
灯牌忽明忽暗，木地板发出轻响。
沈岚：你听见了吗？
林照没有回答，只把那封皱掉的信塞进口袋。`;

const currentText = computed(() => {
  if (mode.value === "sample") {
    return sampleText;
  }
  if (mode.value === "text") {
    return text.value;
  }
  return "";
});

const textCharacterCount = computed(() => currentText.value.trim().length);

const canSubmit = computed(() => {
  if (mode.value === "file") {
    return Boolean(selectedFile.value);
  }
  if (mode.value === "sample") {
    return true;
  }
  return text.value.trim().length > 0;
});

const readinessLabel = computed(() => {
  if (mode.value === "file") {
    if (!selectedFile.value) {
      return "等待选择 TXT 或 EPUB 文件";
    }
    return `${selectedFile.value.name} · ${formatFileSize(selectedFile.value.size)}`;
  }
  if (mode.value === "sample") {
    return `示例素材 · ${textCharacterCount.value} 字`;
  }
  if (!textCharacterCount.value) {
    return "等待粘贴小说正文";
  }
  return `已输入 ${textCharacterCount.value} 字`;
});

const modeDescription = computed(() => {
  if (mode.value === "file") {
    return "支持常见文本文件和电子书文件，系统会先分章，再生成剧本。";
  }
  if (mode.value === "sample") {
    return "用内置短文本快速跑通转换、进度和对照页面。";
  }
  return "直接粘贴小说正文，保留章节标题和对白格式会让拆分更稳定。";
});

const previewLines = computed(() => {
  if (mode.value === "file") {
    if (!selectedFile.value) {
      return ["来源：文件", "状态：等待选择", "可选：文本文件、电子书文件"];
    }
    return [
      "来源：文件",
      `文件：${selectedFile.value.name}`,
      `大小：${formatFileSize(selectedFile.value.size)}`,
      `类型：${selectedFile.value.name.toLowerCase().endsWith(".epub") ? "电子书" : "文本"}`,
    ];
  }

  const lines = currentText.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 6);

  if (!lines.length) {
    return ["来源：粘贴文本", "状态：等待内容", "建议：保留章节和换行"];
  }

  return ["来源：粘贴文本", `字数：${textCharacterCount.value}`, ...lines];
});

interface ResponseLikeError {
  message?: string;
  response?: {
    data?: unknown;
    status?: number;
  };
}

function selectMode(nextMode: "text" | "file" | "sample") {
  mode.value = nextMode;
  error.value = "";
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  selectedFile.value = target.files?.[0] ?? null;
  error.value = "";
}

function openFilePicker() {
  fileInput.value?.click();
}

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

async function submit() {
  if (!canSubmit.value || isSubmitting.value) {
    return;
  }
  isSubmitting.value = true;
  error.value = "";

  try {
    const response = await createConversion({
      text: mode.value === "sample" ? sampleText : mode.value === "text" ? text.value : undefined,
      file: mode.value === "file" ? selectedFile.value ?? undefined : undefined,
    });
    await router.push(`/progress/${response.task_id}`);
  } catch (caught) {
    error.value = formatSubmitError(caught);
  } finally {
    isSubmitting.value = false;
  }
}

function formatSubmitError(caught: unknown) {
  if (isResponseLikeError(caught)) {
    if (!caught.response) {
      return "提交失败：暂时连不上处理服务，请确认服务已打开后重试。";
    }

    return `提交失败：${extractResponseMessage(caught.response.data) || "请检查输入内容后重试。"}`;
  }

  return "提交失败：请检查输入内容后重试。";
}

function isResponseLikeError(caught: unknown): caught is ResponseLikeError {
  return typeof caught === "object" && caught !== null && ("response" in caught || "message" in caught);
}

function extractResponseMessage(data: unknown): string {
  if (typeof data === "string") {
    return data;
  }
  if (!data || typeof data !== "object") {
    return "";
  }

  const payload = data as Record<string, unknown>;
  for (const key of ["detail", "non_field_errors", "text", "file"]) {
    const value = payload[key];
    if (typeof value === "string") {
      return value;
    }
    if (Array.isArray(value) && typeof value[0] === "string") {
      return value[0];
    }
  }
  return "";
}
</script>

<template>
  <section class="page-grid upload-page">
    <div class="panel input-panel">
      <SectionHeader
        eyebrow="小说转剧本"
        title="生成第一版剧本"
        description="把小说文本交给系统处理，完成后进入原文与剧本对照编辑。"
      />

      <div class="segmented" role="tablist" aria-label="输入方式">
        <button
          :class="{ active: mode === 'text' }"
          type="button"
          role="tab"
          :aria-selected="mode === 'text'"
          @click="selectMode('text')"
        >
          <ClipboardPaste :size="16" aria-hidden="true" />
          <span>粘贴</span>
        </button>
        <button
          :class="{ active: mode === 'file' }"
          type="button"
          role="tab"
          :aria-selected="mode === 'file'"
          @click="selectMode('file')"
        >
          <FileArchive :size="16" aria-hidden="true" />
          <span>文件</span>
        </button>
        <button
          :class="{ active: mode === 'sample' }"
          type="button"
          role="tab"
          :aria-selected="mode === 'sample'"
          @click="selectMode('sample')"
        >
          <FileText :size="16" aria-hidden="true" />
          <span>示例</span>
        </button>
      </div>

      <p class="input-guidance">{{ modeDescription }}</p>

      <div class="source-frame">
        <textarea
          v-if="mode === 'text'"
          v-model="text"
          class="source-input"
          rows="16"
          placeholder="粘贴小说正文，建议保留章节标题、人物对白和段落换行。"
          aria-label="粘贴小说文本"
        />

        <div v-else-if="mode === 'file'" class="file-drop">
          <FileUp :size="30" aria-hidden="true" />
          <strong>{{ selectedFile?.name || "选择文本文件或电子书" }}</strong>
          <span>{{ selectedFile ? formatFileSize(selectedFile.size) : "文件内容会用于生成剧本初稿" }}</span>
          <AppButton variant="secondary" @click="openFilePicker">
            <FileUp :size="17" aria-hidden="true" />
            <span>{{ selectedFile ? "更换文件" : "选择文件" }}</span>
          </AppButton>
          <input
            ref="fileInput"
            hidden
            type="file"
            accept=".txt,.epub,text/plain,application/epub+zip"
            @change="onFileChange"
          />
        </div>

        <textarea
          v-else
          class="source-input"
          rows="16"
          :value="sampleText"
          readonly
          aria-label="示例小说文本"
        />
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>

      <div class="submit-bar">
        <span>{{ readinessLabel }}</span>
      </div>

      <AppButton variant="primary" :disabled="!canSubmit || isSubmitting" @click="submit">
        <Sparkles v-if="isSubmitting" :size="18" aria-hidden="true" class="spin" />
        <ArrowRight v-else :size="18" aria-hidden="true" />
        <span>{{ isSubmitting ? "转换中" : "开始转换" }}</span>
      </AppButton>
    </div>

    <aside class="panel snapshot-panel" aria-label="输出预览">
      <SectionHeader
        eyebrow="素材"
        title="素材状态"
        :description="readinessLabel"
      />
      <div class="yaml-preview">
        <span v-for="line in previewLines" :key="line">{{ line }}</span>
      </div>
      <dl class="upload-facts">
        <div>
          <dt>输入</dt>
          <dd>粘贴文本 / 文本文件 / 电子书</dd>
        </div>
        <div>
          <dt>输出</dt>
          <dd>可编辑的剧本初稿</dd>
        </div>
        <div>
          <dt>下一步</dt>
          <dd>自动进入处理进度页</dd>
        </div>
      </dl>
    </aside>
  </section>
</template>
