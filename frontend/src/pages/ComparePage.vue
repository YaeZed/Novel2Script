<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { CheckCircle2, Download, RefreshCw } from "@lucide/vue";
import { YAMLException, load } from "js-yaml";
import { ZodError, type ZodIssue } from "zod";

import { getResult, type ResultResponse } from "../api/client";
import { scriptSchema, type ScriptDocument } from "../schemas/script";

const props = defineProps<{
  taskId: string;
}>();

const result = ref<ResultResponse | null>(null);
const yamlText = ref("");
const activeScene = ref(0);
const error = ref("");
const validationStatus = ref<"idle" | "dirty" | "valid" | "invalid">("idle");
const validationDetail = ref("");
const lastValidScript = ref<ScriptDocument | null>(null);

const validationTitle = computed(() => {
  if (validationStatus.value === "valid") {
    return "YAML 有效";
  }
  if (validationStatus.value === "invalid") {
    return "YAML 需要修正";
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
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "结果读取失败";
  }
}

function validateYaml() {
  try {
    const parsed = scriptSchema.parse(load(yamlText.value));
    lastValidScript.value = parsed;
    validationStatus.value = "valid";
    validationDetail.value = "结构符合 Act / Scene / Beat 约定。";
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
    return `YAML 语法错误：${caught.reason || caught.message}`;
  }
  return "YAML 无效，请检查缩进、字段名和字段值。";
}

function formatZodIssue(issue: ZodIssue | undefined) {
  if (!issue) {
    return "剧本结构不符合 Schema。";
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
  return parts.join(" / ") || "当前 YAML";
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

watch(scenes, (nextScenes) => {
  if (activeScene.value >= nextScenes.length) {
    activeScene.value = Math.max(nextScenes.length - 1, 0);
  }
});

onMounted(loadResult);
</script>

<template>
  <section class="compare-layout">
    <aside class="panel scene-rail">
      <div class="rail-header">
        <p class="eyebrow">Scenes</p>
        <button class="icon-button" type="button" aria-label="刷新结果" @click="loadResult">
          <RefreshCw :size="17" aria-hidden="true" />
        </button>
      </div>
      <button
        v-for="(scene, index) in scenes"
        :key="`${scene.source_chapter}-${scene.number}`"
        class="scene-button"
        :class="{ active: activeScene === index }"
        type="button"
        @click="activeScene = index"
      >
        <span>{{ scene.number }}</span>
        <strong>{{ scene.title }}</strong>
      </button>
    </aside>

    <div class="compare-main">
      <div class="panel compare-pane">
        <div class="pane-header">
          <div>
            <p class="eyebrow">原文</p>
            <h1>{{ currentChapter?.title || "未选择场景" }}</h1>
          </div>
        </div>
        <article class="source-text">{{ currentChapter?.text }}</article>
      </div>

      <div class="panel compare-pane">
        <div class="pane-header">
          <div>
            <p class="eyebrow">剧本 YAML</p>
            <h1>{{ validationTitle }}</h1>
          </div>
          <div class="toolbar">
            <button class="icon-button" type="button" aria-label="校验 YAML" @click="validateYaml">
              <CheckCircle2 :size="17" aria-hidden="true" />
            </button>
            <button class="icon-button" type="button" aria-label="下载 YAML" @click="downloadYaml">
              <Download :size="17" aria-hidden="true" />
            </button>
          </div>
        </div>
        <p
          v-if="validationDetail"
          class="validation-note"
          :data-status="validationStatus"
        >
          {{ validationDetail }}
        </p>
        <textarea
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
