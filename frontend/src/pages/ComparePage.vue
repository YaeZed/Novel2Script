<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { CheckCircle2, Download, RefreshCw } from "@lucide/vue";
import { load } from "js-yaml";

import { getResult, type ResultResponse } from "../api/client";
import { scriptSchema, type ScriptDocument } from "../schemas/script";

const props = defineProps<{
  taskId: string;
}>();

const result = ref<ResultResponse | null>(null);
const yamlText = ref("");
const activeScene = ref(0);
const error = ref("");
const validationMessage = ref("");

const script = computed<ScriptDocument | null>(() => {
  if (!yamlText.value.trim()) {
    return null;
  }
  try {
    return scriptSchema.parse(load(yamlText.value));
  } catch {
    return null;
  }
});

const scenes = computed(() => script.value?.acts.flatMap((act) => act.scenes) ?? []);
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
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "结果读取失败";
  }
}

function validateYaml() {
  try {
    scriptSchema.parse(load(yamlText.value));
    validationMessage.value = "YAML 有效";
  } catch (caught) {
    validationMessage.value = caught instanceof Error ? caught.message : "YAML 无效";
  }
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
            <h1>{{ validationMessage || "待校验" }}</h1>
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
        <textarea v-model="yamlText" class="yaml-editor" spellcheck="false" @blur="validateYaml" />
      </div>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>
