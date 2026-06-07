<script setup lang="ts">
import { computed } from "vue";
import { Eye, Minus, Moon, Plus, Sun, Type } from "@lucide/vue";

import AppButton from "./AppButton.vue";

const props = defineProps<{
  theme: "light" | "dark";
  size: "compact" | "comfortable" | "spacious";
}>();

const emit = defineEmits<{
  "update:theme": [theme: "light" | "dark"];
  "update:size": [size: "compact" | "comfortable" | "spacious"];
}>();

const themeOptions = [
  { value: "light", label: "浅色护眼", icon: Sun },
  { value: "dark", label: "深色护眼", icon: Moon },
] as const;

const sizeOrder = ["compact", "comfortable", "spacious"] as const;

const sizeLabel = computed(() => {
  if (props.size === "compact") return "紧凑";
  if (props.size === "spacious") return "大字";
  return "舒适";
});

const sizeIndex = computed(() => sizeOrder.indexOf(props.size));

function stepSize(direction: -1 | 1) {
  const nextIndex = Math.min(sizeOrder.length - 1, Math.max(0, sizeIndex.value + direction));
  emit("update:size", sizeOrder[nextIndex]);
}
</script>

<template>
  <section class="reading-controls" aria-label="阅读设置">
    <div class="control-group">
      <span class="control-label">
        <Eye :size="16" aria-hidden="true" />
        阅读模式
      </span>
      <div class="control-segmented" role="group" aria-label="阅读模式">
        <button
          v-for="option in themeOptions"
          :key="option.value"
          type="button"
          :class="{ active: theme === option.value }"
          @click="emit('update:theme', option.value)"
        >
          <component :is="option.icon" :size="16" aria-hidden="true" />
          <span>{{ option.label }}</span>
        </button>
      </div>
    </div>

    <div class="control-group control-group--inline">
      <span class="control-label">
        <Type :size="16" aria-hidden="true" />
        阅读字号
      </span>
      <div class="reader-stepper" aria-label="阅读字号">
        <AppButton
          variant="icon"
          aria-label="缩小字号"
          title="缩小字号"
          :disabled="sizeIndex <= 0"
          @click="stepSize(-1)"
        >
          <Minus :size="16" aria-hidden="true" />
        </AppButton>
        <strong>{{ sizeLabel }}</strong>
        <AppButton
          variant="icon"
          aria-label="放大字号"
          title="放大字号"
          :disabled="sizeIndex >= sizeOrder.length - 1"
          @click="stepSize(1)"
        >
          <Plus :size="16" aria-hidden="true" />
        </AppButton>
      </div>
    </div>
  </section>
</template>
