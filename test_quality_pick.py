"""Проверка выбора качества экстрактором на живом embed."""
import re

from curl_cffi import requests as cr

import app

PAGE = "https://m.vtrahe.bet/movie/posle-dvoynogo-proniknoveniya-goryachey-devke-napisali-v-rotik/"

print("playerjs_analyze:", app.playerjs_analyze(PAGE))
assert app.playerjs_analyze(PAGE) == [720, 480, 360, 240]
assert app.playerjs_analyze("https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4") is None

s = cr.Session(impersonate="chrome")
page = s.get(PAGE, timeout=30).text
embed = app._playerjs_embed_url(page, PAGE)
print("embed:", embed)
emb = s.get(embed, headers={"Referer": PAGE}, timeout=30).text
files = app._playerjs_files(emb)
print("доступные:", [h for h, _ in files])

for q in ("Лучшее", "1080p", "720p", "480p", "240p"):
    url = app._pick_quality(files, q)
    h = next(hh for hh, uu in files if uu == url)
    print(f"{q:>8} -> {h}p")
