from threading import Thread

from django.db import close_old_connections

from converter.models import ConversionTask
from converter.services.error_messages import format_conversion_error
from converter.services.pipeline import run_conversion_task


def start_conversion_task(task: ConversionTask) -> None:
    worker = Thread(target=_run_and_capture_failure, args=(task.id,), daemon=True)
    worker.start()


def _run_and_capture_failure(task_id) -> None:
    close_old_connections()
    task = ConversionTask.objects.filter(id=task_id).first()
    if not task:
        close_old_connections()
        return
    try:
        run_conversion_task(task)
    except Exception as exc:  # noqa: BLE001
        task.status = ConversionTask.Status.FAILED
        task.error_message = format_conversion_error(exc)
        task.progress = 100
        task.save(update_fields=["status", "error_message", "progress", "updated_at"])
    finally:
        close_old_connections()
