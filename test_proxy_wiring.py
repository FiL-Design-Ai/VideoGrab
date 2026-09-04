"""Проверка, что прокси реально прокидывается в движок yt-dlp."""
import queue
import threading

import app

q: queue.Queue = queue.Queue()
cancel = threading.Event()
t = threading.Thread(
    target=app.run_download,
    args=("https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4",
          app.MODE_VIDEO, "Лучшее", app.Path(r"d:\Загрузки\VideoGrab\test_out"),
          q, cancel, "127.0.0.1:59999"),
)
t.start()
t.join(60)
kinds = []
while not q.empty():
    kind, payload = q.get()
    kinds.append(kind)
    print(kind, payload)
assert "error" in kinds, "ожидали ошибку прокси"
print("PROXY_WIRING_OK")
