"""Тест прямой загрузки (Playerjs-embed) без прокси через движок приложения."""
import queue
import threading
from pathlib import Path

import app

URL = "https://m.vtrahe.bet/movie/posle-dvoynogo-proniknoveniya-goryachey-devke-napisali-v-rotik/"
OUT = Path(r"d:\Загрузки\VideoGrab\test_out_playerjs")
OUT.mkdir(exist_ok=True)

q: queue.Queue = queue.Queue()
cancel = threading.Event()
t = threading.Thread(
    target=app.run_download, args=(URL, app.MODE_VIDEO, "240p", OUT, q, cancel), daemon=True)
t.start()

last = ""
while t.is_alive():
    try:
        kind, payload = q.get(timeout=1)
    except queue.Empty:
        continue
    if kind == "progress":
        last = payload["text"]
        continue
    print(kind, payload, flush=True)

print("last progress:", last, flush=True)
print("files:", [(p.name, p.stat().st_size) for p in OUT.iterdir()], flush=True)
