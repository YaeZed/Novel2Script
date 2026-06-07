<script setup lang="ts">
import { computed } from "vue";
import { Bookmark, BookmarkCheck, Circle, CircleDot, Flag } from "@lucide/vue";

import AppButton from "./AppButton.vue";
import type { SceneMark } from "../types/review";

const props = defineProps<{
  mark: SceneMark;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  "update:mark": [mark: SceneMark];
}>();

const markLabel = computed(() => {
  if (props.mark === "review") return "待处理";
  if (props.mark === "done") return "已确认";
  return "未标记";
});

function setMark(mark: SceneMark) {
  if (!props.disabled) {
    emit("update:mark", mark);
  }
}
</script>

<template>
  <section class="scene-mark-controls" :data-mark="mark" aria-label="当前场标记">
    <div class="scene-mark-current">
      <BookmarkCheck v-if="mark === 'done'" :size="18" aria-hidden="true" />
      <Flag v-else-if="mark === 'review'" :size="18" aria-hidden="true" />
      <Bookmark v-else :size="18" aria-hidden="true" />
      <span>{{ markLabel }}</span>
    </div>

    <div class="scene-mark-actions" role="group" aria-label="标记当前场">
      <AppButton
        variant="secondary"
        :disabled="disabled"
        :aria-pressed="mark === 'review'"
        @click="setMark(mark === 'review' ? 'none' : 'review')"
      >
        <Flag :size="16" aria-hidden="true" />
        <span>待处理</span>
      </AppButton>
      <AppButton
        variant="secondary"
        :disabled="disabled"
        :aria-pressed="mark === 'done'"
        @click="setMark(mark === 'done' ? 'none' : 'done')"
      >
        <CircleDot v-if="mark === 'done'" :size="16" aria-hidden="true" />
        <Circle v-else :size="16" aria-hidden="true" />
        <span>已确认</span>
      </AppButton>
    </div>
  </section>
</template>
