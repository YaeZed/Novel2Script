<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RefreshCw } from "@lucide/vue";
import { YAMLException, load } from "js-yaml";
import { ZodError, type ZodIssue } from "zod";

import { getResult, getStatus, type ResultResponse, type StatusResponse } from "../api/client";
import AppButton from "../components/AppButton.vue";
import SceneNavigator from "../components/SceneNavigator.vue";
import ScriptValidationPanel from "../components/ScriptValidationPanel.vue";
import SectionHeader from "../components/SectionHeader.vue";
import StatusPill from "../components/StatusPill.vue";
import { scriptSchema, type ScriptDocument } from "../schemas/script";

const props = defineProps<{
  taskId: string;
}>();

type Scene = ScriptDocument["acts"][number]["scenes"][number];

const result = ref<ResultResponse | null>(null);
const status = ref<StatusResponse | null>(null);
const yamlText = ref("");
const yamlEditor = ref<HTMLTextAreaElement | null>(null);
const sourceTextPane = ref<HTMLElement | null>(null);
const activeScene = ref(0);
const sourceScrollByScene = ref<Record<string, number>>({});
const error = ref("");
const validationStatus = ref<"idle" | "dirty" | "valid" | "invalid">("idle");
const validationDetail = ref("");
const lastValidScript = ref<ScriptDocument | null>(null);
const serverYamlText = ref("");
const pendingResult = ref<ResultResponse | null>(null);
const hasPendingServerUpdate = ref(false);
const hasLocalDraftEdits = ref(false);
let pollingTimer: number | undefined;

const progressValue = computed(() => {
  const value = status.value?.progress ?? (result.value?.status === "completed" ? 100 : 8);
  return Math.max(8, Math.min(100, value));
});

const progressTitle = computed(() => {
  if (!status.value) {
    return "正在读取处理进度";
  }
  if (status.value.status === "completed") {
    return status.value.error_message ? "初稿已完成，部分内容待处理" : "剧本初稿已完成";
  }
  if (status.value.status === "failed") {
    return "处理没有完成";
  }
  if (!status.value.total_chapters) {
    return "正在整理素材";
  }
  return `已处理 ${status.value.chapters_done}/${status.value.total_chapters} 段`;
});

const progressDescription = computed(() => {
  if (hasPendingServerUpdate.value) {
    return "后续内容已有更新。你正在编辑当前草稿，页面不会自动覆盖。";
  }
  if (!status.value) {
    return "页面会在后台读取最新进度。";
  }
  if (status.value.status === "processing") {
    return "可以先检查已完成内容，后续处理好后会自动补进来。";
  }
  if (status.value.status === "completed") {
    return "所有已生成内容都已载入，可以继续对照和编辑。";
  }
  if (status.value.status === "failed" && result.value?.script_yaml) {
    return "处理已停止，但已完成的部分仍可查看和整理。";
  }
  if (status.value.status === "failed") {
    return "当前没有可查看的剧本草稿，请返回重新提交。";
  }
  return "已有内容生成后会显示在这里。";
});

const validationTitle = computed(() => {
  if (validationStatus.value === "valid") {
    return "格式正确";
  }
  if (validationStatus.value === "invalid") {
    return "格式需要修正";
  }
  if (validationStatus.value === "dirty") {
    return "有未校验修改";
  }
  return "待校验";
});

const sceneEntries = computed(() => (
  lastValidScript.value?.acts.flatMap((act) => (
    act.scenes.map((scene) => ({
      actTitle: act.title,
      scene,
    }))
  )) ?? []
));

const scenes = computed(() => sceneEntries.value.map((entry) => entry.scene));
const currentSceneEntry = computed(() => sceneEntries.value[activeScene.value]);
const currentScene = computed(() => currentSceneEntry.value?.scene);
const currentChapter = computed(() => {
  const chapterIndex = currentScene.value?.source_chapter;
  return result.value?.chapters.find((chapter) => chapter.index === chapterIndex);
});

const sceneItems = computed(() => (
  sceneEntries.value.map((entry, index) => ({
    id: sceneStorageKey(index),
    number: entry.scene.number,
    title: entry.scene.title,
    sourceTitle: chapterTitleForScene(entry.scene),
    beatCount: entry.scene.beats.length,
    summary: entry.scene.summary,
  }))
));

const currentSceneSummary = computed(() => (
  currentScene.value?.summary || "这一场还没有摘要，可以先对照原文检查节拍是否完整。"
));

const currentSceneCharacters = computed(() => {
  const names = sceneCharacterNames(currentScene.value);
  return names.length ? names.join("、") : "旁白/动作";
});

const currentSceneFacts = computed(() => {
  if (!currentScene.value) {
    return [];
  }
  return [
    { label: "场次", value: `第 ${currentScene.value.number} 场` },
    { label: "来源", value: chapterTitleForScene(currentScene.value) },
    { label: "结构", value: `${currentScene.value.beats.length} 个节拍` },
    { label: "角色", value: currentSceneCharacters.value },
  ];
});

const currentSceneTitle = computed(() => {
  if (!currentScene.value) {
    return "未选择场景";
  }
  const actTitle = currentSceneEntry.value?.actTitle;
  return actTitle ? `${actTitle} · ${currentScene.value.title}` : currentScene.value.title;
});

const canDownload = computed(() => Boolean(yamlText.value.trim()));

function chapterTitleForScene(scene: Scene) {
  return result.value?.chapters.find((chapter) => chapter.index === scene.source_chapter)?.title
    || `素材 ${scene.source_chapter}`;
}

function sceneCharacterNames(scene: Scene | undefined) {
  if (!scene) {
    return [];
  }
  return Array.from(
    new Set(
      scene.beats
        .map((beat) => beat.character?.trim())
        .filter((name): name is string => Boolean(name)),
    ),
  ).slice(0, 4);
}

async function refreshCompareState() {
  try {
    status.value = await getStatus(props.taskId);
    error.value = "";
    if (status.value.can_view_result) {
      await loadResult();
    }
    if (status.value.status === "completed" || status.value.status === "failed") {
      stopPolling();
    }
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "进度读取失败";
  }
}

async function loadResult(options: { force?: boolean; resetSelection?: boolean } = {}) {
  try {
    const nextResult = await getResult(props.taskId);
    applyResult(nextResult, options);
    error.value = "";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "结果读取失败";
  }
}

function applyResult(
  nextResult: ResultResponse,
  options: { force?: boolean; resetSelection?: boolean } = {},
) {
  const nextYaml = nextResult.script_yaml || "";
  if (!nextYaml.trim()) {
    result.value = nextResult;
    return;
  }

  if (nextYaml === serverYamlText.value && result.value) {
    result.value = nextResult;
    return;
  }

  if (hasLocalDraftEdits.value && !options.force) {
    if (nextYaml !== serverYamlText.value) {
      pendingResult.value = nextResult;
      hasPendingServerUpdate.value = true;
    }
    return;
  }

  const activeIdentity = sceneIdentity(currentScene.value);
  result.value = nextResult;
  yamlText.value = nextYaml;
  serverYamlText.value = nextYaml;
  pendingResult.value = null;
  hasPendingServerUpdate.value = false;
  hasLocalDraftEdits.value = false;
  validateYaml();

  if (options.resetSelection) {
    activeScene.value = 0;
    sourceScrollByScene.value = {};
  } else {
    restoreActiveScene(activeIdentity);
  }
  restoreSceneScrollState();
}

function applyPendingResult() {
  if (pendingResult.value) {
    applyResult(pendingResult.value, { force: true });
    return;
  }
  void loadResult({ force: true });
}

function validateYaml() {
  if (!yamlText.value.trim()) {
    lastValidScript.value = null;
    validationStatus.value = "idle";
    validationDetail.value = "已处理内容生成后会显示在这里。";
    return;
  }

  try {
    const parsed = scriptSchema.parse(load(yamlText.value));
    lastValidScript.value = parsed;
    validationStatus.value = "valid";
    validationDetail.value = "剧本结构完整，可以继续编辑。";
  } catch (caught) {
    validationStatus.value = "invalid";
    validationDetail.value = formatValidationError(caught);
  }
}

function markDirty() {
  hasLocalDraftEdits.value = true;
  if (validationStatus.value === "valid" || validationStatus.value === "invalid") {
    validationStatus.value = "dirty";
    validationDetail.value = "当前修改尚未校验；左侧仍显示上一次有效结构。";
  }
}

function formatValidationError(caught: unknown) {
  if (caught instanceof ZodError) {
    return formatZodIssue(caught.issues[0]);
  }
  if (caught instanceof YAMLException) {
    return `文本格式错误：${caught.reason || caught.message}`;
  }
  return "剧本格式无效，请检查缩进、字段名和字段值。";
}

function formatZodIssue(issue: ZodIssue | undefined) {
  if (!issue) {
    return "剧本结构不完整。";
  }

  const path = issue.path.join(".");
  const location = humanizePath(issue.path);
  if (issue.code === "invalid_enum_value" && path.endsWith(".type")) {
    return `${location}：type 只能是 dialogue、action 或 direction，当前是 ${String(issue.received)}。`;
  }
  if (issue.code === "invalid_type") {
    return `${location}：字段类型不正确，期望 ${issue.expected}。`;
  }
  if (issue.code === "too_small") {
    return `${location}：至少需要 ${issue.minimum} 项。`;
  }
  return `${location}：${issue.message}`;
}

function humanizePath(path: Array<string | number>) {
  const parts: string[] = [];
  for (let index = 0; index < path.length; index += 1) {
    const segment = path[index];
    const next = path[index + 1];
    if (segment === "acts" && typeof next === "number") {
      parts.push(`第 ${next + 1} 幕`);
      index += 1;
    } else if (segment === "scenes" && typeof next === "number") {
      parts.push(`第 ${next + 1} 场`);
      index += 1;
    } else if (segment === "beats" && typeof next === "number") {
      parts.push(`第 ${next + 1} 个节拍`);
      index += 1;
    } else if (typeof segment === "string") {
      parts.push(`字段 ${segment}`);
    }
  }
  return parts.join(" / ") || "当前剧本";
}

function downloadYaml() {
  if (!yamlText.value.trim()) {
    return;
  }
  const blob = new Blob([yamlText.value], { type: "text/yaml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "script.yaml";
  link.click();
  URL.revokeObjectURL(url);
}

function selectScene(index: number) {
  rememberActiveSourceScroll();
  activeScene.value = index;
  restoreSceneScrollState();
}

async function restoreSceneScrollState() {
  await nextTick();
  restoreSourceScroll();
  scrollYamlToActiveScene();
}

function rememberActiveSourceScroll() {
  const pane = sourceTextPane.value;
  if (!pane) {
    return;
  }

  sourceScrollByScene.value[sceneStorageKey(activeScene.value)] = pane.scrollTop;
}

function restoreSourceScroll() {
  const pane = sourceTextPane.value;
  if (!pane) {
    return;
  }

  pane.scrollTop = sourceScrollByScene.value[sceneStorageKey(activeScene.value)] ?? 0;
}

function sceneStorageKey(index: number) {
  const scene = scenes.value[index];
  if (!scene) {
    return `missing:${index}`;
  }
  return `${index}:${scene.source_chapter}:${scene.number}:${scene.title}`;
}

function sceneIdentity(scene: ScriptDocument["acts"][number]["scenes"][number] | undefined) {
  if (!scene) {
    return "";
  }
  return `${scene.source_chapter}:${scene.title}`;
}

function restoreActiveScene(identity: string) {
  if (!identity) {
    activeScene.value = Math.min(activeScene.value, Math.max(scenes.value.length - 1, 0));
    return;
  }
  const nextIndex = scenes.value.findIndex((scene) => sceneIdentity(scene) === identity);
  activeScene.value = nextIndex >= 0 ? nextIndex : Math.min(activeScene.value, Math.max(scenes.value.length - 1, 0));
}

function scrollYamlToActiveScene() {
  const editor = yamlEditor.value;
  if (!editor) {
    return;
  }

  const lineIndex = findSceneYamlLineIndex(activeScene.value);
  if (lineIndex < 0) {
    return;
  }

  const offset = offsetForLine(yamlText.value, lineIndex);
  editor.setSelectionRange(offset, offset);
  editor.scrollTop = yamlScrollTopForLine(editor, yamlText.value, lineIndex);
}

function findSceneYamlLineIndex(sceneIndex: number) {
  const lines = yamlText.value.split("\n");
  const blocks = findSceneYamlBlocks(lines);
  return blocks[sceneIndex] ?? -1;
}

function findSceneYamlBlocks(lines: string[]) {
  const sceneBlocks: number[] = [];

  for (let index = 0; index < lines.length; index += 1) {
    const match = /^(\s*)-\s+number:\s+\d+\s*$/.exec(lines[index]);
    if (!match) {
      continue;
    }

    const indent = match[1].length;
    const block = lines.slice(index, findYamlListBlockEnd(lines, index, indent));
    if (isSceneYamlBlock(block, indent)) {
      sceneBlocks.push(index);
    }
  }

  return sceneBlocks;
}

function findYamlListBlockEnd(lines: string[], startIndex: number, indent: number) {
  for (let index = startIndex + 1; index < lines.length; index += 1) {
    const match = /^(\s*)-\s+\S/.exec(lines[index]);
    if (match && match[1].length <= indent) {
      return index;
    }
  }
  return lines.length;
}

function isSceneYamlBlock(block: string[], indent: number) {
  const childIndent = indent + 2;
  return block.some((line) => directChildLineStartsWith(line, childIndent, "source_chapter:"))
    && block.some((line) => directChildLineStartsWith(line, childIndent, "beats:"));
}

function directChildLineStartsWith(line: string, indent: number, prefix: string) {
  return line.slice(0, indent) === " ".repeat(indent) && line.slice(indent).startsWith(prefix);
}

function yamlScrollTopForLine(editor: HTMLTextAreaElement, text: string, lineIndex: number) {
  const markerTop = measureTextareaLineTop(editor, text, lineIndex);
  return Math.max(0, markerTop - editor.clientHeight * 0.18);
}

function measureTextareaLineTop(editor: HTMLTextAreaElement, text: string, lineIndex: number) {
  const styles = window.getComputedStyle(editor);
  const mirror = document.createElement("div");
  const mirroredProperties = [
    "boxSizing",
    "width",
    "fontFamily",
    "fontSize",
    "fontWeight",
    "fontStyle",
    "letterSpacing",
    "lineHeight",
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
    "borderTopWidth",
    "borderRightWidth",
    "borderBottomWidth",
    "borderLeftWidth",
  ] as const;

  for (const property of mirroredProperties) {
    mirror.style[property] = styles[property];
  }

  mirror.style.position = "absolute";
  mirror.style.visibility = "hidden";
  mirror.style.left = "-9999px";
  mirror.style.top = "0";
  mirror.style.height = "auto";
  mirror.style.whiteSpace = "pre-wrap";
  mirror.style.overflowWrap = "break-word";
  mirror.style.wordBreak = "normal";
  mirror.style.width = `${editor.clientWidth}px`;

  const lines = text.split("\n");
  mirror.textContent = lineIndex > 0 ? `${lines.slice(0, lineIndex).join("\n")}\n` : "";

  const marker = document.createElement("span");
  marker.textContent = "\u200b";
  mirror.appendChild(marker);
  document.body.appendChild(mirror);
  const markerTop = marker.offsetTop;
  mirror.remove();
  return markerTop;
}

function offsetForLine(text: string, lineIndex: number) {
  if (lineIndex <= 0) {
    return 0;
  }

  let offset = 0;
  const lines = text.split("\n");
  for (let index = 0; index < lineIndex; index += 1) {
    offset += lines[index].length + 1;
  }
  return offset;
}

watch(scenes, (nextScenes) => {
  if (activeScene.value >= nextScenes.length) {
    activeScene.value = Math.max(nextScenes.length - 1, 0);
    restoreSceneScrollState();
  }
});

function startPolling() {
  void refreshCompareState();
  pollingTimer = window.setInterval(refreshCompareState, 2500);
}

function stopPolling() {
  if (pollingTimer) {
    window.clearInterval(pollingTimer);
    pollingTimer = undefined;
  }
}

onMounted(startPolling);
onBeforeUnmount(stopPolling);
</script>

<template>
  <section class="compare-shell">
    <div class="panel compare-progress-panel">
      <SectionHeader
        eyebrow="处理进度"
        :title="progressTitle"
        :description="progressDescription"
      >
        <StatusPill v-if="status" :status="status.status" />
      </SectionHeader>
      <div class="progress-readout compare-progress-readout" aria-label="处理进度">
        <div class="meter">
          <span :style="{ width: `${progressValue}%` }"></span>
        </div>
        <strong>{{ progressValue }}%</strong>
      </div>
      <div v-if="hasPendingServerUpdate" class="compare-update-row">
        <span>新处理好的内容还没有载入。</span>
        <AppButton variant="secondary" @click="applyPendingResult">
          <RefreshCw :size="17" aria-hidden="true" />
          <span>载入新内容</span>
        </AppButton>
      </div>
    </div>

    <section class="compare-layout">
      <SceneNavigator
        :scenes="sceneItems"
        :active-index="activeScene"
        @refresh="refreshCompareState"
        @select="selectScene"
      />

      <div class="compare-main">
        <div class="panel compare-pane">
          <SectionHeader
            eyebrow="原文依据"
            :title="currentSceneTitle"
            :description="currentChapter?.title ? `来源：${currentChapter.title}` : '选择场景后显示原文依据。'"
          />

          <div v-if="currentScene" class="scene-context">
            <p class="scene-summary">{{ currentSceneSummary }}</p>
            <dl class="scene-facts">
              <div v-for="fact in currentSceneFacts" :key="fact.label">
                <dt>{{ fact.label }}</dt>
                <dd>{{ fact.value }}</dd>
              </div>
            </dl>
          </div>

          <article ref="sourceTextPane" class="source-text" @scroll="rememberActiveSourceScroll">
            <template v-if="currentChapter?.text">{{ currentChapter.text }}</template>
            <span v-else class="empty-source">原文载入后会显示在这里。</span>
          </article>
        </div>

        <div class="panel compare-pane">
          <ScriptValidationPanel
            :title="validationTitle"
            :detail="validationDetail"
            :status="validationStatus"
            :can-download="canDownload"
            @validate="validateYaml"
            @download="downloadYaml"
          />
          <textarea
            ref="yamlEditor"
            v-model="yamlText"
            class="yaml-editor"
            aria-label="剧本草稿编辑区"
            placeholder="处理好的剧本文件会显示在这里。"
            spellcheck="false"
            @input="markDirty"
            @blur="validateYaml"
          />
        </div>
      </div>
    </section>

    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>
