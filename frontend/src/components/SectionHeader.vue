<script setup lang="ts">
defineProps<{
  eyebrow?: string;
  title?: string;
  description?: string;
}>();
</script>

<template>
  <header class="section-header">
    <div class="section-title">
      <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
      <h1 v-if="title">{{ title }}</h1>
      <p v-if="description" class="section-description">{{ description }}</p>
    </div>
    <div v-if="$slots.default" class="section-actions">
      <slot></slot>
    </div>
  </header>
</template>
