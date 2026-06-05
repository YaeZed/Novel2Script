import { createRouter, createWebHistory } from "vue-router";

import ComparePage from "./pages/ComparePage.vue";
import ProgressPage from "./pages/ProgressPage.vue";
import UploadPage from "./pages/UploadPage.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: UploadPage },
    { path: "/progress/:taskId", component: ProgressPage, props: true },
    { path: "/compare/:taskId", component: ComparePage, props: true },
  ],
});

