import { computed, onBeforeUnmount, ref } from "vue";

import { getStatus, type StatusResponse } from "../api/client";

export function useTaskPolling(taskId: string) {
  const status = ref<StatusResponse | null>(null);
  const error = ref("");
  const isPolling = ref(false);
  let timer: number | undefined;

  const isDone = computed(() => status.value?.status === "completed" || status.value?.status === "failed");

  async function refresh() {
    try {
      status.value = await getStatus(taskId);
      error.value = "";
      if (isDone.value) {
        stop();
      }
    } catch (caught) {
      error.value = "暂时读不到处理进度，请确认处理服务已打开，稍后再刷新。";
    }
  }

  function start() {
    if (isPolling.value) {
      return;
    }
    isPolling.value = true;
    void refresh();
    timer = window.setInterval(refresh, 1500);
  }

  function stop() {
    if (timer) {
      window.clearInterval(timer);
      timer = undefined;
    }
    isPolling.value = false;
  }

  onBeforeUnmount(stop);

  return { status, error, isPolling, isDone, start, stop, refresh };
}

