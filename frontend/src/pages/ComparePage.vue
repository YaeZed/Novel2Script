<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { CheckCircle2, Download, RefreshCw } from "@lucide/vue";
import { YAMLException, load } from "js-yaml";
import { ZodError, type ZodIssue } from "zod";

import { getResult, type ResultResponse } from "../api/client";
import AppButton from "../components/AppButton.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { scriptSchema, type ScriptDocument } from "../schemas/script";

const props = defineProps<{
  taskId: string;
}>();

const result = ref<ResultResponse | null>(null);
const yamlText = ref("");
const yamlEditor = ref<HTMLTextAreaElement | null>(null);
const sourceTextPane = ref<HTMLElement | null>(null);
const activeScene = ref(0);
const sourceScrollByScene = ref<Record<string, number>>({});
const error = ref("");
const validationStatus = ref<"idle" | "dirty" | "valid" | "invalid">("idle");
const validationDetail = ref("");
const lastValidScript = ref<ScriptDocument | null>(null);

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

const scenes = computed(() => lastValidScript.value?.acts.flatMap((act) => act.scenes) ?? []);
const currentScene = computed(() => scenes.value[activeScene.value]);
const currentChapter = computed(() => {
  const chapterIndex = currentScene.value?.source_chapter;
  return result.value?.chapters.find((chapter) => chapter.index === chapterIndex);
});

async function loadResult() {
  try {
    result.value = await getResult(props.taskId);
    yamlText.value = result.value.script_yaml;
    validateYaml();
    activeScene.value = 0;
    sourceScrollByScene.value = {};
    restoreSceneScrollState();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "结果读取失败";
  }
}

function validateYaml() {
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

onMounted(loadResult);
</script>

<template>
  <section class="compare-layout">
    <aside class="panel scene-rail">
      <SectionHeader eyebrow="场景">
        <AppButton variant="icon" aria-label="刷新结果" @click="loadResult">
          <RefreshCw :size="17" aria-hidden="true" />
        </AppButton>
      </SectionHeader>
      <button
        v-for="(scene, index) in scenes"
        :key="`${scene.source_chapter}-${scene.number}`"
        class="scene-button"
        :class="{ active: activeScene === index }"
        type="button"
        @click="selectScene(index)"
      >
        <span>{{ scene.number }}</span>
        <strong>{{ scene.title }}</strong>
      </button>
    </aside>

    <div class="compare-main">
      <div class="panel compare-pane">
        <SectionHeader eyebrow="原文" :title="currentChapter?.title || '未选择场景'" />
        <article ref="sourceTextPane" class="source-text" @scroll="rememberActiveSourceScroll">{{ currentChapter?.text }}</article>
      </div>

      <div class="panel compare-pane">
        <SectionHeader eyebrow="剧本" :title="validationTitle">
          <AppButton variant="icon" aria-label="检查剧本格式" @click="validateYaml">
            <CheckCircle2 :size="17" aria-hidden="true" />
          </AppButton>
          <AppButton variant="icon" aria-label="下载剧本文件" @click="downloadYaml">
            <Download :size="17" aria-hidden="true" />
          </AppButton>
        </SectionHeader>
        <p
          v-if="validationDetail"
          class="validation-note"
          :data-status="validationStatus"
        >
          {{ validationDetail }}
        </p>
        <textarea
          ref="yamlEditor"
          v-model="yamlText"
          class="yaml-editor"
          spellcheck="false"
          @input="markDirty"
          @blur="validateYaml"
        />
      </div>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>
