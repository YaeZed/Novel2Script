<script setup lang="ts">
import { computed, onMounted } from "vue";
import {
  ArrowRight,
  CheckCircle2,
  Circle,
  FileText,
  ListChecks,
  RefreshCw,
  RotateCcw,
} from "@lucide/vue";

import AppButton from "../components/AppButton.vue";
import SectionHeader from "../components/SectionHeader.vue";
import StatusPill from "../components/StatusPill.vue";
import { useTaskPolling } from "../composables/useTaskPolling";

const props = defineProps<{
  taskId: string;
}>();

const { status, error, isDone, start, refresh } = useTaskPolling(props.taskId);

const shortTaskId = computed(() => props.taskId.slice(0, 8));

const progressValue = computed(() => {
  const value = status.value?.progress ?? 8;
  return Math.max(8, Math.min(100, value));
});

const progressLabel = computed(() => {
  if (!status.value) {
    return "正在接收素材";
  }
  if (status.value.status === "completed") {
    return status.value.error_message ? "初稿已完成，部分章节待处理" : "剧本初稿已完成";
  }
  if (status.value.status === "failed") {
    return "转换没有完成";
  }
  if (!status.value.total_chapters) {
    return "正在整理章节";
  }
  return `已处理 ${status.value.chapters_done}/${status.value.total_chapters} 章`;
});

const stageDescription = computed(() => {
  if (!status.value) {
    return "页面正在读取任务状态。";
  }
  if (status.value.status === "pending") {
    return "素材已提交，正在等待处理服务接手。";
  }
  if (status.value.status === "processing") {
    if (!status.value.total_chapters) {
      return "正在拆分章节，稍后会显示每章预览。";
    }
    const nextChapter = status.value.chapters[status.value.chapters_done];
    if (nextChapter) {
      return `正在处理「${nextChapter.title}」。`;
    }
    return "正在整理剧本初稿。";
  }
  if (status.value.status === "completed") {
    if (status.value.error_message) {
      return "可以进入对照编辑，页面中已标出需要人工补看的章节。";
    }
    return "可以进入对照编辑，继续检查原文和剧本初稿。";
  }
  return "请根据下方提示处理后重试。";
});

const providerLabel = computed(() => {
  const provider = status.value?.llm_provider;
  if (!provider) {
    return "正在读取处理方式";
  }
  if (provider === "placeholder") {
    return "本地演示，不连接在线智能服务";
  }
  if (provider === "misconfigured") {
    return "处理方式需要管理员修正";
  }
  const providerNames: Record<string, string> = {
    anthropic: "Anthropic",
    openai: "OpenAI",
    qwen: "阿里千问",
  };
  return providerNames[provider] || "在线智能服务";
});

const sourceLabel = computed(() => {
  if (!status.value) {
    return "读取中";
  }
  if (status.value.source_format === "epub") {
    return "电子书";
  }
  if (status.value.input_name === "pasted-text.txt") {
    return "粘贴文本";
  }
  return status.value.input_name?.toLowerCase().endsWith(".txt") ? "文本文件" : "粘贴文本";
});

const chapterRows = computed(() => status.value?.chapters ?? []);
const canViewPartialResult = computed(() => Boolean(status.value?.can_view_result));

const chapterSummary = computed(() => {
  if (!status.value) {
    return "等待章节信息";
  }
  if (!status.value.total_chapters) {
    return "正在识别章节";
  }
  return hasSplitChapters.value
    ? `${sourceChapterCount.value} 章素材 · ${status.value.total_chapters} 个处理段`
    : `${status.value.total_chapters} 章素材`;
});

const sourceChapterCount = computed(() => {
  const baseTitles = new Set(
    chapterRows.value.map((chapter) => chapter.title.replace(/（分块 \d+\/\d+）$/, ""))
  );
  return baseTitles.size;
});

const hasSplitChapters = computed(() => chapterRows.value.some((chapter) => /（分块 \d+\/\d+）$/.test(chapter.title)));

function chapterState(index: number) {
  if (!status.value || status.value.status === "failed") {
    return "waiting";
  }
  if (status.value.status === "completed" || index <= status.value.chapters_done) {
    return "done";
  }
  if (status.value.status === "processing" && index === status.value.chapters_done + 1) {
    return "active";
  }
  return "waiting";
}

function chapterStateLabel(index: number) {
  const state = chapterState(index);
  if (state === "done") return "已处理";
  if (state === "active") return "处理中";
  return "等待中";
}

onMounted(start);
</script>

<template>
  <section class="progress-layout">
    <div class="panel progress-panel">
      <SectionHeader
        :eyebrow="`任务 ${shortTaskId}`"
        :title="progressLabel"
        :description="stageDescription"
      >
        <StatusPill v-if="status" :status="status.status" />
      </SectionHeader>

      <div class="progress-readout" aria-label="转换进度">
        <div class="meter">
          <span :style="{ width: `${progressValue}%` }"></span>
        </div>
        <strong>{{ progressValue }}%</strong>
      </div>

      <dl class="progress-facts">
        <div>
          <dt>来源</dt>
          <dd>{{ sourceLabel }}</dd>
        </div>
        <div>
          <dt>素材</dt>
          <dd>{{ chapterSummary }}</dd>
        </div>
        <div>
          <dt>方式</dt>
          <dd>{{ providerLabel }}</dd>
        </div>
      </dl>

      <p v-if="error" class="status-message" data-kind="error">{{ error }}</p>
      <p
        v-if="status?.error_message"
        class="status-message"
        :data-kind="status.status === 'completed' ? 'warning' : 'error'"
      >
        {{ status.error_message }}
      </p>

      <div class="progress-next-step">
        <CheckCircle2 v-if="status?.status === 'completed'" :size="20" aria-hidden="true" />
        <RotateCcw v-else-if="status?.status === 'failed'" :size="20" aria-hidden="true" />
        <FileText v-else :size="20" aria-hidden="true" />
        <span>
          {{
            status?.status === "completed"
              ? "下一步：进入对照编辑"
              : status?.status === "failed"
                ? "下一步：返回重新提交"
                : "下一步：等待章节处理完成"
          }}
        </span>
      </div>

      <div class="action-row progress-actions">
        <AppButton variant="secondary" @click="refresh">
          <RefreshCw :size="17" aria-hidden="true" />
          <span>刷新</span>
        </AppButton>
        <AppButton
          v-if="canViewPartialResult && status?.status !== 'completed'"
          :to="`/compare/${taskId}`"
          variant="secondary"
        >
          <ListChecks :size="17" aria-hidden="true" />
          <span>查看已处理</span>
        </AppButton>
        <AppButton
          v-if="isDone && status?.status === 'completed'"
          :to="`/compare/${taskId}`"
        >
          <ArrowRight :size="18" aria-hidden="true" />
          <span>打开对照</span>
        </AppButton>
        <AppButton
          v-else-if="isDone && status?.status === 'failed'"
          to="/"
          variant="secondary"
        >
          <RotateCcw :size="17" aria-hidden="true" />
          <span>重新提交</span>
        </AppButton>
      </div>
    </div>

    <aside class="panel chapter-preview-panel" aria-label="素材预览">
      <SectionHeader
        eyebrow="素材"
        title="逐段预览"
        :description="chapterSummary"
      />

      <div v-if="chapterRows.length" class="chapter-preview-list">
        <article
          v-for="chapter in chapterRows"
          :key="chapter.index"
          class="chapter-preview-item"
          :data-state="chapterState(chapter.index)"
        >
          <div class="chapter-preview-marker" aria-hidden="true">
            <CheckCircle2 v-if="chapterState(chapter.index) === 'done'" :size="17" />
            <RefreshCw v-else-if="chapterState(chapter.index) === 'active'" :size="17" class="spin" />
            <Circle v-else :size="17" />
          </div>
          <div>
            <div class="chapter-preview-heading">
              <strong>{{ chapter.title }}</strong>
              <span>{{ chapterStateLabel(chapter.index) }}</span>
            </div>
            <p>{{ chapter.excerpt || "这一章已进入队列。" }}</p>
          </div>
        </article>
      </div>

      <div v-else class="empty-preview">
        <FileText :size="24" aria-hidden="true" />
        <span>章节预览生成后会显示在这里。</span>
      </div>
    </aside>
  </section>
</template>
