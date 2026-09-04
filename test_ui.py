"""Интеграционный тест UI: гоняет реальные обработчики кнопок и цикл событий Tk."""
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import app as appmod


URL = "https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4"
OUT = Path(r"d:\Загрузки\VideoGrab\test_out_ui")
OUT.mkdir(parents=True, exist_ok=True)

root = appmod.App()
root.dir_entry.delete(0, "end")
root.dir_entry.insert(0, str(OUT))
root.url_entry.insert(0, URL)

root._start()  # то же, что делает кнопка «СКАЧАТЬ»
assert root._busy, "загрузка не стартовала"
assert root.cancel_button.cget("state") == "normal"
assert len(root._queue) == 1 and root._queue[0]["status"] in ("waiting", "running")

deadline = time.time() + 180
while root._busy and time.time() < deadline:
    root.update()
    time.sleep(0.05)

status = root.status_label.cget("text")
print("статус:", status)
print("прогресс-лейбл:", root.progress_label.cget("text"))
files = sorted(p.name for p in OUT.iterdir())
print("файлы:", files)

assert not root._busy, "не завершилось за отведённое время"
assert status in ("Done ✓", "Готово ✓", "已完成 ✓"), f"неожиданный статус: {status}"
assert root._queue[0]["status"] == "done"
assert any(p.endswith(".mp4") for p in files)

# отмена: стартуем и сразу отменяем
root.url_entry.delete(0, "end")
root.url_entry.insert(0, URL)
root._start()
root.update()
root._cancel()
deadline = time.time() + 60
while root._busy and time.time() < deadline:
    root.update()
    time.sleep(0.05)
print("статус после отмены:", root.status_label.cget("text"))
assert root.status_label.cget("text") in ("Cancelled", "Отменено", "已取消")

root.destroy()
print("UI_OK")
