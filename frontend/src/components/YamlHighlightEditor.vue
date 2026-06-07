<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { Check, Highlighter, X } from "@lucide/vue";

import type { HighlightColor, TextHighlight } from "../types/review";

const props = defineProps<{
  modelValue: string;
  highlights: TextHighlight[];
  editorLabel: string;
  placeholder: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
  "add-highlight": [highlight: Omit<TextHighlight, "id">];
  "remove-highlight": [id: string];
  "clear-highlights": [];
  blur: [];
  input: [];
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const mirrorRef = ref<HTMLElement | null>(null);
const menu = ref<{
  visible: boolean;
  start: number;
  end: number;
  top: number;
  left: number;
}>({
  visible: false,
  start: 0,
  end: 0,
  top: 0,
  left: 0,
});
const dismissedSelection = ref<{ start: number; end: number } | null>(null);

const colorOptions: Array<{ color: HighlightColor; label: string }> = [
  { color: "red", label: "红" },
  { color: "orange", label: "橙" },
  { color: "yellow", label: "黄" },
  { color: "green", label: "绿" },
  { color: "blue", label: "蓝" },
];

const sortedHighlights = computed(() => (
  props.highlights
    .filter((highlight) => (
      highlight.start >= 0
      && highlight.end > highlight.start
      && highlight.end <= props.modelValue.length
    ))
    .sort((left, right) => left.start - right.start || left.end - right.end)
));

const highlightedSegments = computed(() => {
  const segments: Array<{
    key: string;
    text: string;
    color?: HighlightColor;
    id?: string;
  }> = [];
  let cursor = 0;

  for (const highlight of sortedHighlights.value) {
    if (highlight.start < cursor) {
      continue;
    }
    if (highlight.start > cursor) {
      segments.push({
        key: `plain:${cursor}:${highlight.start}`,
        text: props.modelValue.slice(cursor, highlight.start),
      });
    }
    segments.push({
      key: highlight.id,
      id: highlight.id,
      text: props.modelValue.slice(highlight.start, highlight.end),
      color: highlight.color,
    });
    cursor = highlight.end;
  }

  if (cursor < props.modelValue.length) {
    segments.push({
      key: `plain:${cursor}:end`,
      text: props.modelValue.slice(cursor),
    });
  }

  return segments.length ? segments : [{ key: "empty", text: props.modelValue }];
});

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement;
  emit("update:modelValue", target.value);
  emit("input");
  dismissedSelection.value = null;
  hideMenu();
}

function handleScroll() {
  syncMirrorScroll();
  hideMenu();
}

function handleSelection() {
  window.setTimeout(showMenuForSelection, 0);
}

function handleDocumentSelectionChange() {
  if (document.activeElement === textareaRef.value) {
    showMenuForSelection();
  }
}

function showMenuForSelection() {
  const editor = textareaRef.value;
  if (!editor || editor.selectionEnd <= editor.selectionStart) {
    dismissedSelection.value = null;
    hideMenu();
    return;
  }

  const selectionStart = editor.selectionStart;
  const selectionEnd = editor.selectionEnd;
  if (isDismissedSelection(selectionStart, selectionEnd)) {
    hideMenu();
    return;
  }

  const selectedText = props.modelValue.slice(selectionStart, selectionEnd);
  if (!selectedText.trim()) {
    hideMenu();
    return;
  }

  const editorRect = editor.getBoundingClientRect();
  const selectionTop = lineTopForOffset(editor, props.modelValue, selectionStart) - editor.scrollTop;

  menu.value = {
    visible: true,
    start: selectionStart,
    end: selectionEnd,
    top: Math.max(10, Math.min(editor.clientHeight - 12, selectionTop + 30)),
    left: Math.min(editor.clientWidth - 230, Math.max(10, editorRect.width * 0.44)),
  };
}

function addHighlight(color: HighlightColor) {
  const { start, end } = menu.value;
  const selectedText = props.modelValue.slice(start, end);
  if (!selectedText.trim()) {
    hideMenu();
    return;
  }
  emit("add-highlight", {
    start,
    end,
    color,
    text: selectedText,
  });
  dismissedSelection.value = null;
  hideMenu();
  void nextTick(() => {
    const editor = textareaRef.value;
    if (!editor) {
      return;
    }
    editor.focus();
    editor.setSelectionRange(end, end);
    syncMirrorScroll();
  });
}

function hideMenu() {
  if (menu.value.visible && menu.value.end > menu.value.start) {
    dismissedSelection.value = {
      start: menu.value.start,
      end: menu.value.end,
    };
  }
  menu.value.visible = false;
}

function dismissMenu() {
  if (menu.value.end > menu.value.start) {
    dismissedSelection.value = {
      start: menu.value.start,
      end: menu.value.end,
    };
  }
  hideMenu();
  void nextTick(() => textareaRef.value?.focus());
}

function isDismissedSelection(start: number, end: number) {
  return dismissedSelection.value?.start === start && dismissedSelection.value.end === end;
}

function keepTextareaSelection(event: MouseEvent) {
  event.preventDefault();
  event.stopPropagation();
}

function syncMirrorScroll() {
  const editor = textareaRef.value;
  const mirror = mirrorRef.value;
  if (!editor || !mirror) {
    return;
  }
  mirror.scrollTop = editor.scrollTop;
  mirror.scrollLeft = editor.scrollLeft;
}

function lineTopForOffset(editor: HTMLTextAreaElement, text: string, offset: number) {
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
  mirror.textContent = text.slice(0, offset);

  const marker = document.createElement("span");
  marker.textContent = "\u200b";
  mirror.appendChild(marker);
  document.body.appendChild(mirror);
  const markerTop = marker.offsetTop;
  mirror.remove();
  return markerTop;
}

function focusEditor() {
  textareaRef.value?.focus();
}

defineExpose({
  getTextarea: () => textareaRef.value,
});

onMounted(() => {
  document.addEventListener("selectionchange", handleDocumentSelectionChange);
});

onBeforeUnmount(() => {
  document.removeEventListener("selectionchange", handleDocumentSelectionChange);
});
</script>

<template>
  <div class="yaml-highlight-editor" @mouseleave="handleSelection">
    <pre ref="mirrorRef" class="yaml-highlight-layer" aria-hidden="true"><template
      v-for="segment in highlightedSegments"
      :key="segment.key"
    ><mark
      v-if="segment.color"
      :data-color="segment.color"
    >{{ segment.text }}</mark><span v-else>{{ segment.text }}</span></template></pre>

    <textarea
      ref="textareaRef"
      :value="modelValue"
      class="yaml-editor yaml-highlight-input"
      :aria-label="editorLabel"
      :placeholder="placeholder"
      spellcheck="false"
      @input="handleInput"
      @blur="emit('blur')"
      @scroll="handleScroll"
      @mouseup="handleSelection"
      @keyup="handleSelection"
      @select="handleSelection"
      @focus="syncMirrorScroll"
    />

    <div
      v-if="menu.visible"
      class="highlight-menu"
      :style="{ top: `${menu.top}px`, left: `${menu.left}px` }"
      role="toolbar"
      @mousedown.stop
      aria-label="颜色标记"
    >
      <Highlighter :size="16" aria-hidden="true" />
      <button
        v-for="option in colorOptions"
        :key="option.color"
        type="button"
        class="highlight-swatch"
        :data-color="option.color"
        :aria-label="`标记为${option.label}色`"
        :title="`标记为${option.label}色`"
        @mousedown="keepTextareaSelection"
        @click.stop="addHighlight(option.color)"
      >
        <Check :size="13" aria-hidden="true" />
      </button>
      <button type="button" class="highlight-clear" aria-label="关闭标记菜单" title="关闭" @mousedown="keepTextareaSelection" @click.stop="dismissMenu">
        <X :size="14" aria-hidden="true" />
      </button>
    </div>

    <div v-if="highlights.length" class="highlight-status">
      <button type="button" class="highlight-count" title="颜色标记保存在当前浏览器" @click="focusEditor">
        {{ highlights.length }} 处颜色标记
      </button>
      <button type="button" class="highlight-reset" title="清除全部颜色标记" @click="emit('clear-highlights')">
        清除
      </button>
    </div>
  </div>
</template>
