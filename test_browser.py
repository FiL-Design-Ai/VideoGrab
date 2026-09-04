"""Тест режима «через браузер» на сайте с бот-защитой."""
import time
from pathlib import Path

import app as appmod

URL = "https://720video.me/video.39172/shikarnyy-gruppovoy-minet-s-uchastiem-samyh-goryachih-suchek"
OUT = Path(r"d:\Загрузки\VideoGrab\test_out_browser")
OUT.mkdir(parents=True, exist_ok=True)

root = appmod.App()
root.dir_entry.delete(0, "end")
root.dir_entry.insert(0, str(OUT))
root.url_entry.insert(0, URL)
root._start_browser()

deadline = time.time() + 480
last = ""
while root._busy and time.time() < deadline:
    root.update()
    st = root.status_label.cget("text")
    if st != last:
        print("status:", st, flush=True)
        last = st
    pl = root.progress_label.cget("text")
    if pl != getattr(root, "_last_pl", ""):
        print("progress:", pl, flush=True)
        root._last_pl = pl
    time.sleep(0.1)

print("FINAL:", root.status_label.cget("text"), flush=True)
print("files:", [(p.name, p.stat().st_size) for p in OUT.iterdir()], flush=True)
root.destroy()
