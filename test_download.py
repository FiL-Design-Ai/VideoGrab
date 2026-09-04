"""Головная проверка движка загрузки без GUI."""
import queue
import threading
from pathlib import Path

import app

URL = "https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4"



def drain(q: queue.Queue, worker: threading.Thread):
    while worker.is_alive() or not q.empty():
        try:
            kind, payload = q.get(timeout=1)
        except queue.Empty:
            continue
        if kind != "progress":
            print(f"[{kind}] {payload}")


def run_case(mode: str, quality: str, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    q: queue.Queue = queue.Queue()
    cancel = threading.Event()
    worker = threading.Thread(
        target=app.run_download, args=(URL, mode, quality, outdir, q, cancel)
    )
    worker.start()
    drain(q, worker)
    worker.join()
    files = [p.name for p in outdir.iterdir()]
    print(f"-> {mode}: файлы = {files}")
    return files


print("=== CASE 1: видео, качество Лучшее ===")
video_files = run_case(app.MODE_VIDEO, "Лучшее", Path(r"d:\Загрузки\VideoGrab\test_out\video"))

print("=== CASE 2: аудио в MP3 ===")
audio_files = run_case(app.MODE_AUDIO, "Лучшее", Path(r"d:\Загрузки\VideoGrab\test_out\audio"))

assert any(p.endswith(".mp4") for p in video_files), "видео не скачалось"
assert any(p.endswith(".mp3") for p in audio_files), "mp3 не сконвертировался"
print("ALL_OK")
