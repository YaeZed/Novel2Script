<script setup lang="ts">
import { computed } from "vue";
import { BookmarkCheck, FileText, Flag, RefreshCw } from "@lucide/vue";

import AppButton from "./AppButton.vue";
import SectionHeader from "./SectionHeader.vue";
import type { SceneMark } from "../types/review";

defineProps<{
  scenes: Array<{
    id: string;
    number: number;
    title: string;
    sourceTitle: string;
    beatCount: number;
    summary?: string;
    mark?: SceneMark;
  }>;
  activeIndex: number;
}>();

const emit = defineEmits<{
  refresh: [];
  select: [index: number];
}>();

const title = computed(() => "场景列表");

function markLabel(mark: SceneMark | undefined) {
  if (mark === "review") return "待处理";
  if (mark === "done") return "已确认";
  return "";
}
</script>

<template>
  <aside class="panel scene-rail" aria-label="场景列表">
    <SectionHeader eyebrow="场景" :title="title">
      <AppButton variant="icon" aria-label="刷新结果" title="刷新结果" @click="emit('refresh')">
        <RefreshCw :size="17" aria-hidden="true" />
      </AppButton>
    </SectionHeader>

    <div v-if="scenes.length" class="scene-list">
      <button
        v-for="(scene, index) in scenes"
        :key="scene.id"
        class="scene-button"
        :class="{ active: activeIndex === index }"
        type="button"
        @click="emit('select', index)"
      >
        <span class="scene-button-index">{{ scene.number }}</span>
        <span class="scene-button-copy">
          <strong>{{ scene.title }}</strong>
          <small>{{ scene.sourceTitle }} · {{ scene.beatCount }} 个节拍</small>
          <span v-if="scene.mark && scene.mark !== 'none'" class="scene-mark-badge" :data-mark="scene.mark">
            <Flag v-if="scene.mark === 'review'" :size="12" aria-hidden="true" />
            <BookmarkCheck v-else :size="12" aria-hidden="true" />
            {{ markLabel(scene.mark) }}
          </span>
          <span v-if="scene.summary" class="scene-button-summary">{{ scene.summary }}</span>
        </span>
      </button>
    </div>

    <div v-else class="empty-scene-list">
      <FileText :size="22" aria-hidden="true" />
      <span>已有剧本草稿后会显示场景。</span>
    </div>
  </aside>
</template>
