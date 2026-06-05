<script setup lang="ts">
import { FileText } from "@lucide/vue";
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <FileText :size="22" aria-hidden="true" />
        <span>小说转剧本</span>
      </RouterLink>
      <nav class="topbar__nav" aria-label="主导航">
        <RouterLink to="/">上传</RouterLink>
      </nav>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>
