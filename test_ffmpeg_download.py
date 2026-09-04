"""Тест загрузки ffmpeg (то, что делает кнопка «Скачать ffmpeg»)."""
import queue

import app

q: queue.Queue = queue.Queue()
app.download_ffmpeg(q)
while not q.empty():
    k, p = q.get()
    if k == "progress":
        continue
    print(k, p)
print("ffmpeg dir:", app.find_ffmpeg_dir())
assert (app.data_dir() / "ffmpeg.exe").is_file()
assert (app.data_dir() / "ffprobe.exe").is_file()
print("FFMPEG_DL_OK")
