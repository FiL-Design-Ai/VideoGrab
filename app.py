"""VideoGrab — простой загрузчик видео для Windows.

Тонкий графический интерфейс поверх yt-dlp: вставил ссылку, выбрал
режим/качество, нажал «Скачать». Поддерживает видео с 1000+ сайтов,
плейлисты и извлечение звука в MP3.
"""
from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urljoin

import tkinter as tk
import customtkinter as ctk
import yt_dlp

try:
    import winsound
except Exception:
    winsound = None

try:
    import pystray
    from PIL import Image
    _HAS_PYSTRAY = True
except Exception:
    _HAS_PYSTRAY = False

APP_NAME = "VideoGrab"
APP_VERSION = "1.0.0"

LANG_LABELS = {
    "en": "English",
    "ru": "Русский",
    "zh": "中文",
}
LABEL_TO_LANG = {v: k for k, v in LANG_LABELS.items()}

TRANSLATIONS = {
    "en": {
        "app_title": "VideoGrab — Video Downloader",
        "to_tray": "To Tray",
        "settings": "⚙ Settings",
        "logs": "📋 Logs",
        "ffmpeg_ready": "✓ ffmpeg ready",
        "ffmpeg_missing": "⚠ ffmpeg missing",
        "download_ffmpeg": "Download ffmpeg",
        "ffmpeg_downloading": "Downloading ffmpeg (~110 MB)…",
        "ffmpeg_installed": "ffmpeg installed ✓",
        "hero_title": "Paste video or playlist link",
        "hero_sub": "(YouTube, VK, Rutube, direct mp4)",
        "paste_btn": "📋 Paste",
        "download_btn": "⬇ DOWNLOAD",
        "format": "Format:",
        "mode_video": "Video",
        "mode_audio": "Audio (MP3)",
        "quality": "Quality:",
        "quality_best": "Best",
        "active_downloads": "ACTIVE DOWNLOADS",
        "clear_done": "Clear completed",
        "clear_all": "Clear all",
        "empty_title": "Download list is empty",
        "empty_sub": "Paste video or playlist link above to start downloading",
        "ready_status": "● Ready to work",
        "cancel": "⏹ Cancel",
        "downloads_folder": "📁 Downloads folder",
        "btn_open": "Open",
        "btn_retry": "Retry",
        "status_in_queue": "In queue",
        "status_done": "Done",
        "status_error": "Error",
        "status_cancelled": "Cancelled",
        "status_connecting": "connecting…",
        "status_stopping": "Stopping…",
        "status_done_check": "Done ✓",
        "status_download_done": "Download finished! ✓",
        "status_download_complete": "✔ Download finished",
        "status_enqueued": "→ Enqueued: ",
        "status_downloading_item": "Downloading [{i}/{n}]…",
        "link_copied": "Link copied",
        "file_open_err": "Failed to open file: ",
        "folder_open_err": "Failed to open folder: ",
        "enter_url_err": "Please paste a video link",
        "mkdir_err": "Failed to create folder: ",
        "settings_window_title": "VideoGrab Settings",
        "settings_header": "⚙  Application Settings",
        "settings_lang": "Interface language:",
        "settings_dir": "Download folder:",
        "settings_browse": "Browse…",
        "settings_proxy": "Proxy server (HTTP / SOCKS5):",
        "settings_proxy_ph": "e.g. 127.0.0.1:7897 or http://user:pass@host:port",
        "settings_save": "Save",
        "settings_cancel": "Cancel",
        "status_queue_errors": "Queue finished with errors",
        "tray_bg_notice": "Download continues in background. App minimized to tray.",
        "all_done_notice": "All queued downloads finished successfully! ✓",
        "log_window_title": "VideoGrab Event Log",
        "log_header": "📋 Event Log",
        "log_clear": "Clear log",
        "tray_open": "Open VideoGrab",
        "tray_hide": "Minimize to tray",
        "tray_folder": "Downloads folder",
        "tray_exit": "Exit",
        "q_top": "⚡ Download next (Priority)",
        "q_up": "▲ Move up",
        "q_down": "▼ Move down",
        "q_delete": "✕ Remove",
        "q_skip": "⏭ Skip / Next",
        "copy_link": "📋 Copy link",
        "meta_source": "Source: {domain}",
        "meta_ready": "Ready to download",
        "available_qualities": "Available qualities",
        "select_folder_title": "Choose save folder",
        "status_direct_download": "Downloading video directly…",
        "err_cdn_resume": "CDN does not support resuming after disconnect",
        "err_cdn_abort": "CDN dropped connection; try again or choose lower quality",
        "status_reconnecting_at": "Dropped at {done} — resuming…",
        "cdn_geo_blocked": "403: Site/CDN rejected your IP — VPN/proxy required",
        "cdn_403_hint": "403: Site CDN rejected your IP (geo-blocking detected). Enable VPN/proxy and retry.",
        "cdn_403_proxy_hint": "System proxy {sp} is configured — launch it and set this address in Settings.",
        "cdn_responded": "CDN responded {code}",
        "pp_merger": "Muxing video and audio…",
        "pp_extract_audio": "Converting to MP3…",
        "pp_move_files": "Moving file to destination…",
        "pp_video_convert": "Converting video…",
        "browser_not_found": "Chrome or Edge browser not found for browser mode",
        "browser_mode_prefix": "Browser mode",
        "browser_cdp_timeout": "Browser did not respond to CDP",
        "browser_opening_page": "Opening page in browser…",
        "browser_video_started": "Video playback detected — capturing stream…",
        "browser_received": "received",
        "browser_stream_finished": "Stream finished — saving file…",
        "browser_timeout_hint": "Download timed out: if player required action, click Play in browser; if 'Video file not found' appeared, CDN blocked your IP (VPN/proxy needed)",
        "browser_mode_tag": "browser",
        "ffmpeg_download_failed": "Failed to download ffmpeg",
        "unexpected_error": "Unexpected error. Log saved to:",
        "log_received": "Received",
        "log_error": "Error",
    },
    "ru": {
        "app_title": "VideoGrab — загрузчик видео",
        "to_tray": "В трей",
        "settings": "⚙ Настройки",
        "logs": "📋 Журнал",
        "ffmpeg_ready": "✓ ffmpeg готов",
        "ffmpeg_missing": "⚠ ffmpeg не найден",
        "download_ffmpeg": "Скачать ffmpeg",
        "ffmpeg_downloading": "Скачиваю ffmpeg (~110 МБ)…",
        "ffmpeg_installed": "ffmpeg установлен ✓",
        "hero_title": "Вставьте ссылку на видео или плейлист",
        "hero_sub": "(YouTube, ВК, Rutube, прямые mp4)",
        "paste_btn": "📋 Вставить",
        "download_btn": "⬇ СКАЧАТЬ",
        "format": "Формат:",
        "mode_video": "Видео",
        "mode_audio": "Аудио (MP3)",
        "quality": "Качество:",
        "quality_best": "Лучшее",
        "active_downloads": "АКТИВНЫЕ ЗАГРУЗКИ",
        "clear_done": "Очистить завершённые",
        "clear_all": "Очистить всё",
        "empty_title": "Список загрузок пуст",
        "empty_sub": "Вставьте ссылку на видео или плейлист выше",
        "ready_status": "● Готов к работе",
        "cancel": "⏹ Отмена",
        "downloads_folder": "📁 Папка загрузок",
        "btn_open": "Открыть",
        "btn_retry": "Повторить",
        "status_in_queue": "В очереди",
        "status_done": "Готово",
        "status_error": "Ошибка",
        "status_cancelled": "Отменено",
        "status_connecting": "подключение…",
        "status_stopping": "Останавливаю…",
        "status_done_check": "Готово ✓",
        "status_download_done": "Загрузка завершена! ✓",
        "status_download_complete": "✔ Загрузка завершена",
        "status_enqueued": "→ В очередь: ",
        "status_downloading_item": "Качаю [{i}/{n}]…",
        "link_copied": "Ссылка скопирована",
        "file_open_err": "Не удалось открыть файл: ",
        "folder_open_err": "Не удалось открыть папку: ",
        "enter_url_err": "Вставьте ссылку на видео",
        "mkdir_err": "Не удалось создать папку: ",
        "settings_window_title": "Настройки VideoGrab",
        "settings_header": "⚙  Настройки приложения",
        "settings_lang": "Язык интерфейса:",
        "settings_dir": "Папка сохранения видео:",
        "settings_browse": "Обзор…",
        "settings_proxy": "Прокси-сервер (HTTP / SOCKS5):",
        "settings_proxy_ph": "напр. 127.0.0.1:7897 или http://user:pass@host:port",
        "settings_save": "Сохранить",
        "settings_cancel": "Отмена",
        "status_queue_errors": "Очередь завершена с ошибками",
        "tray_bg_notice": "Загрузка продолжается в фоне. Приложение свёрнуто в трей.",
        "all_done_notice": "Все загрузки в очереди успешно завершены! ✓",
        "log_window_title": "Журнал событий VideoGrab",
        "log_header": "📋 Журнал событий",
        "log_clear": "Очистить лог",
        "tray_open": "Открыть VideoGrab",
        "tray_hide": "Свернуть в трей",
        "tray_folder": "Папка загрузок",
        "tray_exit": "Выход",
        "q_top": "⚡ Качать первым (В начало)",
        "q_up": "▲ Поднять выше",
        "q_down": "▼ Опустить ниже",
        "q_delete": "✕ Удалить",
        "q_skip": "⏭ Пропустить / Далее",
        "copy_link": "📋 Скопировать ссылку",
        "meta_source": "Источник: {domain}",
        "meta_ready": "Готово к загрузке",
        "available_qualities": "Доступные качества",
        "select_folder_title": "Папка для сохранения",
        "status_direct_download": "Скачиваю видео напрямую…",
        "err_cdn_resume": "CDN не поддержал докачку после обрыва",
        "err_cdn_abort": "CDN оборвал соединение; попробуйте ещё раз или выберите качество ниже",
        "status_reconnecting_at": "Обрыв на {done} — докачиваю…",
        "cdn_geo_blocked": "403: сайт/CDN не пускает ваш IP — нужен VPN/прокси",
        "cdn_403_hint": "403: CDN сайта не пускает ваш IP (похоже на геоблокировку). Включите VPN/прокси и повторите.",
        "cdn_403_proxy_hint": "В системе настроен прокси {sp} — запустите его и укажите этот адрес в «Настройках».",
        "cdn_responded": "CDN ответил {code}",
        "pp_merger": "Склейка видео и аудио…",
        "pp_extract_audio": "Конвертация в MP3…",
        "pp_move_files": "Перенос файла в папку…",
        "pp_video_convert": "Конвертация видео…",
        "browser_not_found": "Chrome/Edge не найден для режима браузера",
        "browser_mode_prefix": "Браузер-режим",
        "browser_cdp_timeout": "Браузер не ответил на CDP",
        "browser_opening_page": "Открываю страницу в браузере…",
        "browser_video_started": "Видео пошло — принимаю поток…",
        "browser_received": "получено",
        "browser_stream_finished": "Поток завершён — сохраняю файл…",
        "browser_timeout_hint": "Не дождался загрузки: если плеер требовал действия — кликните play в браузере; если «Video file not found» — CDN не пускает IP, нужен VPN/прокси",
        "browser_mode_tag": "браузер",
        "ffmpeg_download_failed": "ffmpeg не скачался",
        "unexpected_error": "Непредвиденная ошибка. Журнал сохранён:",
        "log_received": "Получено",
        "log_error": "Ошибка",
    },
    "zh": {
        "app_title": "VideoGrab — 视频下载器",
        "to_tray": "最小化到托盘",
        "settings": "⚙ 设置",
        "logs": "📋 日志",
        "ffmpeg_ready": "✓ ffmpeg 就绪",
        "ffmpeg_missing": "⚠ 未找到 ffmpeg",
        "download_ffmpeg": "下载 ffmpeg",
        "ffmpeg_downloading": "正在下载 ffmpeg (~110 MB)…",
        "ffmpeg_installed": "ffmpeg 安装完成 ✓",
        "hero_title": "粘贴视频或播放列表链接",
        "hero_sub": "(YouTube、VK、Rutube、直链 mp4)",
        "paste_btn": "📋 粘贴",
        "download_btn": "⬇ 开始下载",
        "format": "格式:",
        "mode_video": "视频",
        "mode_audio": "音频 (MP3)",
        "quality": "清晰度:",
        "quality_best": "最佳",
        "active_downloads": "正在下载",
        "clear_done": "清除已完成",
        "clear_all": "清除全部",
        "empty_title": "下载列表为空",
        "empty_sub": "在上方粘贴视频或播放列表链接以开始下载",
        "ready_status": "● 就绪",
        "cancel": "⏹ 取消",
        "downloads_folder": "📁 下载文件夹",
        "btn_open": "打开",
        "btn_retry": "重试",
        "status_in_queue": "排队中",
        "status_done": "已完成",
        "status_error": "错误",
        "status_cancelled": "已取消",
        "status_connecting": "正在连接…",
        "status_stopping": "正在停止…",
        "status_done_check": "已完成 ✓",
        "status_download_done": "下载完成! ✓",
        "status_download_complete": "✔ 下载已完成",
        "status_enqueued": "→ 已加入队列: ",
        "status_downloading_item": "正在下载 [{i}/{n}]…",
        "link_copied": "链接已复制",
        "file_open_err": "无法打开文件: ",
        "folder_open_err": "无法打开文件夹: ",
        "enter_url_err": "请粘贴视频链接",
        "mkdir_err": "无法创建文件夹: ",
        "settings_window_title": "VideoGrab 设置",
        "settings_header": "⚙  应用设置",
        "settings_lang": "界面语言:",
        "settings_dir": "保存文件夹:",
        "settings_browse": "浏览…",
        "settings_proxy": "代理服务器 (HTTP / SOCKS5):",
        "settings_proxy_ph": "例如 127.0.0.1:7897 或 http://user:pass@host:port",
        "settings_save": "保存",
        "settings_cancel": "取消",
        "status_queue_errors": "队列下载完成，但存在错误",
        "tray_bg_notice": "下载在后台继续进行。应用已最小化到托盘。",
        "all_done_notice": "队列中的所有下载均已成功完成! ✓",
        "log_window_title": "VideoGrab 事件日志",
        "log_header": "📋 事件日志",
        "log_clear": "清除日志",
        "tray_open": "打开 VideoGrab",
        "tray_hide": "最小化到托盘",
        "tray_folder": "下载文件夹",
        "tray_exit": "退出",
        "q_top": "⚡ 优先下载 (置顶)",
        "q_up": "▲ 上移",
        "q_down": "▼ 下移",
        "q_delete": "✕ 删除",
        "q_skip": "⏭ 跳过 / 下一个",
        "copy_link": "📋 复制链接",
        "meta_source": "来源: {domain}",
        "meta_ready": "准备下载",
        "available_qualities": "可用清晰度",
        "select_folder_title": "选择保存文件夹",
        "status_direct_download": "正在直接下载视频…",
        "err_cdn_resume": "CDN 不支持断点续传",
        "err_cdn_abort": "CDN 中断连接；请重试或选择更低清晰度",
        "status_reconnecting_at": "在 {done} 处中断 — 正在恢复…",
        "cdn_geo_blocked": "403: 网站/CDN 拒绝了您的 IP — 需要 VPN/代理",
        "cdn_403_hint": "403: 网站 CDN 拒绝了您的 IP（检测到区域限制）。请开启 VPN/代理并重试。",
        "cdn_403_proxy_hint": "系统中配置了代理 {sp} — 请启动它并在“设置”中填入该地址。",
        "cdn_responded": "CDN 响应 {code}",
        "pp_merger": "合并视频与音频…",
        "pp_extract_audio": "转换为 MP3…",
        "pp_move_files": "移动文件到目标文件夹…",
        "pp_video_convert": "转换视频…",
        "browser_not_found": "未找到用于浏览器模式的 Chrome 或 Edge",
        "browser_mode_prefix": "浏览器模式",
        "browser_cdp_timeout": "浏览器未响应 CDP",
        "browser_opening_page": "正在浏览器中打开页面…",
        "browser_video_started": "检测到视频播放 — 正在接收媒体流…",
        "browser_received": "已接收",
        "browser_stream_finished": "媒体流完成 — 正在保存文件…",
        "browser_timeout_hint": "下载超时：如果播放器需要操作，请在浏览器中点击播放；如果出现“Video file not found”，说明 CDN 屏蔽了 IP，需要 VPN/代理",
        "browser_mode_tag": "浏览器",
        "ffmpeg_download_failed": "下载 ffmpeg 失败",
        "unexpected_error": "发生未知错误。日志已保存至:",
        "log_received": "已收到",
        "log_error": "错误",
    },
}

LANG_LABELS = {
    "en": "English",
    "ru": "Русский",
    "zh": "中文",
}
LABEL_TO_LANG = {v: k for k, v in LANG_LABELS.items()}

_CURRENT_LANG = "en"

def set_current_lang(lang: str) -> None:
    global _CURRENT_LANG
    if lang in TRANSLATIONS:
        _CURRENT_LANG = lang

def get_current_lang() -> str:
    return _CURRENT_LANG

def tr_global(key: str, lang: str | None = None, **kwargs) -> str:
    l = lang or _CURRENT_LANG
    table = TRANSLATIONS.get(l) or TRANSLATIONS["en"]
    text = table.get(key) or TRANSLATIONS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text

SIZE_UNITS = {
    "ru": ("Б", "КБ", "МБ", "ГБ", "ТБ"),
    "en": ("B", "KB", "MB", "GB", "TB"),
    "zh": ("B", "KB", "MB", "GB", "TB"),
}

QUALITIES = ("Best", "1080p", "720p", "480p")
MODE_VIDEO = "Video"
MODE_AUDIO = "Audio (MP3)"

def is_audio_mode(mode: str) -> bool:
    return "MP3" in mode or mode in ("Audio", "Аудио", "音频", MODE_AUDIO)

ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
DANGER = "#dc2626"
OK_GREEN = "#16a34a"
CARD_BG = ("#f3f4f6", "#161920")
CARD_BORDER = ("#e5e7eb", "#232732")



# ---------------------------------------------------------------------------
# Пути и настройки
# ---------------------------------------------------------------------------

def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def base_dir() -> Path:
    """Папка с ресурсами приложения (в сборке — _internal)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    p = Path(os.environ.get("APPDATA") or Path.home()) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def downloads_folder() -> Path:
    """Системная папка «Загрузки» (учитывает перенаправление OneDrive)."""
    try:
        import ctypes
        from ctypes import wintypes

        guid = "{374DE290-123F-4565-9164-39C4925E467B}"
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        if ctypes.windll.shell32.SHGetKnownFolderPath(guid, 0, None, buf) == 0 and buf.value:
            return Path(os.path.normpath(buf.value))
    except Exception:
        pass
    return Path(os.path.normpath(str(Path.home() / "Downloads")))


def default_download_dir() -> Path:
    return Path(os.path.normpath(str(downloads_folder() / APP_NAME)))


CONFIG_PATH = data_dir() / "config.json"


def load_config() -> dict:
    cfg = {
        "download_dir": os.path.normpath(str(default_download_dir())),
        "quality": QUALITIES[0],
        "mode": MODE_VIDEO,
        "lang": "en",  # Default language is English
    }
    try:
        saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        for key in cfg:
            if key in saved:
                cfg[key] = os.path.normpath(saved[key]) if key == "download_dir" else saved[key]
    except Exception:
        pass
    return cfg


def save_config(cfg: dict) -> None:
    try:
        to_save = dict(cfg)
        if "download_dir" in to_save:
            to_save["download_dir"] = os.path.normpath(str(to_save["download_dir"]))
        CONFIG_PATH.write_text(json.dumps(to_save, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def find_ffmpeg_dir() -> Path | None:
    """Ищет ffmpeg: рядом с приложением → в _internal → скачанный → в PATH."""
    candidates = []
    if is_frozen():
        candidates.append(base_dir())
        candidates.append(Path(sys.executable).parent)
    candidates.append(data_dir())
    candidates.append(Path(__file__).resolve().parent / "vendor" / "ffmpeg")
    for c in candidates:
        if (c / "ffmpeg.exe").is_file():
            return c
    which = shutil.which("ffmpeg")
    return Path(which).parent if which else None


FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def download_ffmpeg(events: queue.Queue, cancel_event: threading.Event | None = None) -> None:
    """Скачивает официальный статический ffmpeg и раскладывает его в data_dir()."""
    import io
    import urllib.request
    import zipfile

    req = urllib.request.Request(FFMPEG_ZIP_URL, headers={"User-Agent": APP_NAME})
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("content-length") or 0) or None
        buf = io.BytesIO()
        done = 0
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise Cancelled()
            chunk = r.read(1 << 18)
            if not chunk:
                break
            buf.write(chunk)
            done += len(chunk)
            events.put(("progress", {
                "fraction": done / total if total else None,
                "text": (f"ffmpeg: {human_size(done)} / {human_size(total)}"
                         if total else f"ffmpeg: {human_size(done)}"),
            }))
    with zipfile.ZipFile(buf) as z:
        for member in z.namelist():
            name = member.rsplit("/", 1)[-1]
            if name in ("ffmpeg.exe", "ffprobe.exe"):
                (data_dir() / name).write_bytes(z.read(member))
    if not (data_dir() / "ffmpeg.exe").is_file():
        raise RuntimeError("ffmpeg.exe not found in archive")


# ---------------------------------------------------------------------------
# Движок загрузки (работает в фоновом потоке)
# ---------------------------------------------------------------------------

class Cancelled(Exception):
    pass


def video_format(quality: str) -> str:
    if not (quality.endswith("p") and quality[:-1].isdigit()):
        return "bestvideo*+bestaudio/best"
    h = int(quality[:-1])
    return (
        f"bestvideo*[height<={h}]+bestaudio/best[height<={h}]"
        "/bestvideo*+bestaudio/best"
    )


def human_size(n, lang: str | None = None) -> str:
    if n is None:
        return "?"
    n = float(n)
    l = lang or _CURRENT_LANG
    units = SIZE_UNITS.get(l, SIZE_UNITS["en"])
    for unit in units:
        if n < 1024 or unit == units[-1]:
            return f"{n:.0f} {unit}" if unit == units[0] else f"{n:.1f} {unit}"
        n /= 1024
    return "?"


def human_progress(d: dict, lang: str | None = None) -> str:
    l = lang or _CURRENT_LANG
    parts = []
    done = d.get("downloaded_bytes") or 0
    total = d.get("total_bytes") or d.get("total_bytes_estimate")
    parts.append(f"{human_size(done, l)} / {human_size(total, l)}" if total else human_size(done, l))
    if d.get("speed"):
        speed_unit = "/с" if l == "ru" else "/s"
        parts.append(f"{human_size(d['speed'], l)}{speed_unit}")
    eta = d.get("eta")
    if eta is not None:
        eta = int(eta)
        mm_ss = f"{eta // 60:02d}:{eta % 60:02d}"
        if l == "ru":
            parts.append(f"осталось {mm_ss}")
        elif l == "zh":
            parts.append(f"剩余 {mm_ss}")
        else:
            parts.append(f"{mm_ss} left")
    return "  •  ".join(parts)


def clean_error(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        last = lines[-1]
        for prefix in ("ERROR: ", "[download] "):
            if last.startswith(prefix):
                last = last[len(prefix):]
        return last
    return text


def run_download(url: str, mode: str, quality: str, outdir: Path,
                 events: queue.Queue, cancel_event: threading.Event,
                 proxy: str | None = None) -> tuple[str, str]:
    def progress_hook(d):
        if cancel_event.is_set():
            raise Cancelled()
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            events.put(("progress", {
                "fraction": (done / total) if total else None,
                "text": human_progress(d),
                "file": os.path.basename(d.get("filename") or ""),
            }))
        elif status == "finished":
            name = os.path.basename(d.get("filename") or "")
            if name:
                events.put(("file_downloaded", name))

    def pp_hook(d):
        if d.get("status") != "started":
            return
        pp = d.get("postprocessor", "")
        pp_keys = {
            "Merger": "pp_merger",
            "ExtractAudio": "pp_extract_audio",
            "MoveFiles": "pp_move_files",
            "VideoConvert": "pp_video_convert",
        }
        if pp in pp_keys:
            events.put(("status", tr_global(pp_keys[pp])))

    opts = {
        "paths": {"home": str(outdir)},
        "outtmpl": "%(title)s [%(id)s].%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 2,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 4,
        "windowsfilenames": True,
        "socket_timeout": 12,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [pp_hook],
        # как браузер: файл отдаётся только с Referer со страницы (анти-хотлинк)
        "http_headers": {
            "Referer": url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        },
    }
    if proxy:
        opts["proxy"] = proxy if "://" in proxy else f"http://{proxy}"
    ffmpeg_dir = find_ffmpeg_dir()
    if ffmpeg_dir:
        opts["ffmpeg_location"] = str(ffmpeg_dir)
    cookies = data_dir() / "cookies.txt"
    if cookies.is_file():
        opts["cookiefile"] = str(cookies)

    if is_audio_mode(mode):
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        opts["format"] = video_format(quality)
        opts["merge_output_format"] = "mp4"

    try:
        if not is_audio_mode(mode):
            done = playerjs_try_download(url, quality, outdir, events, cancel_event, proxy)
            if done is not None:
                if done:
                    events.put(("finished_ok", None))
                    return ("finished_ok", "")
                return ("error", "Playerjs CDN error")
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        events.put(("finished_ok", None))
        return ("finished_ok", "")
    except Cancelled:
        events.put(("cancelled", None))
        return ("cancelled", "")
    except yt_dlp.utils.DownloadError as e:
        err = clean_error(str(e))
        events.put(("error", err))
        return ("error", err)
    except Exception as e:  # noqa: BLE001 — показываем любую ошибку в UI
        err = f"{type(e).__name__}: {e}"
        events.put(("error", err))
        return ("error", err)


def cleanup_partial(outdir: Path) -> None:
    """Удаляет недокачанные .part/.ytdl после отмены."""
    try:
        for p in outdir.iterdir():
            if p.suffix in (".part", ".ytdl"):
                p.unlink(missing_ok=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Прямая загрузка с сайтов, чей плеер (Playerjs) держит подписанные mp4-ссылки
# в embed-странице: yt-dlp такие не извлекает, но файл отдаётся напрямую.
# ---------------------------------------------------------------------------

def _playerjs_embed_url(html: str, page_url: str) -> str | None:
    m = re.search(r'<meta\s+property="og:video"\s+content="([^"]+)"', html)
    if not m:
        m = re.search(r"""["']((?:https?:)?//[^"'\s]+/embed/\d+)""", html)
    if not m:
        m = re.search(r"/embed/(\d+)", html)
        if m:
            return urljoin(page_url, f"/embed/{m.group(1)}")
    if not m:
        return None
    u = m.group(1).replace("&amp;", "&")
    if u.startswith("//"):
        u = "https:" + u
    return u if u.startswith("http") else urljoin(page_url, u)


def _playerjs_files(html: str) -> list[tuple[int, str]]:
    """[(высота, url)] из Playerjs file:"[240p] url,[720p] url" или одна ссылка."""
    pairs = [(int(q[:-1]), u.replace("&amp;", "&"))
             for q, u in re.findall(r"\[(\d+p)\]\s*(https?://[^,\s\"']+)", html)]
    if pairs:
        return sorted(pairs)
    return [(0, u.replace("&amp;", "&"))
            for u in re.findall(r"""file:\s*["'](https?://[^"']+)["']""", html)]


def _pick_quality(files: list[tuple[int, str]], quality: str) -> str:
    if quality.endswith("p") and quality[:-1].isdigit():
        below = [u for h, u in files if h <= int(quality[:-1])]
        if below:
            return below[-1]
    return files[-1][1]


def _playerjs_probe(url: str, proxy: str | None):
    """(сессия, [(высота, url)], заголовок, poster_url) или None, если сайт не распознан."""
    try:
        from curl_cffi import requests as cr
    except ImportError:
        return None
    kwargs: dict = {"impersonate": "chrome", "timeout": 30}
    if proxy:
        kwargs["proxies"] = {"http": proxy, "https": proxy}
    try:
        s = cr.Session()
        resp = s.get(url, **kwargs)
        if "text/html" not in (resp.headers.get("content-type") or ""):
            return None
        page = resp.text
        title = ""
        t_main = re.search(r"<title>([^<]+)</title>", page)
        if t_main:
            title = t_main.group(1).strip()
        poster = ""
        m_p = re.search(r'og:image.*?content=[\x22\x27]([^\x22\x27]+)', page) or \
              re.search(r'poster:\s*[\x22\x27]([^\x22\x27]+)', page)
        if m_p:
            poster = m_p.group(1).replace("&amp;", "&")

        if "new Playerjs(" not in page:
            embed = _playerjs_embed_url(page, url)
            if not embed:
                return None
            page = s.get(embed, headers={"Referer": url}, **kwargs).text
            if not poster:
                m_p2 = re.search(r'poster:\s*[\x22\x27]([^\x22\x27]+)', page)
                if m_p2:
                    poster = m_p2.group(1).replace("&amp;", "&")
        if "new Playerjs(" not in page:
            return None
        files = _playerjs_files(page)
        if not files:
            return None
        if not title:
            t = re.search(r"<title>([^<]+)</title>", page)
            if t:
                title = t.group(1).strip()
        return s, files, title, poster
    except Exception:
        return None


def playerjs_analyze(url: str, proxy: str | None = None) -> list[int] | None:
    """Доступные высоты видео (по убыванию) или None, если сайт не распознан."""
    probe = _playerjs_probe(url, proxy)
    if not probe:
        return None
    return sorted({h for h, _ in probe[1]}, reverse=True)


def fetch_video_meta(url: str, proxy: str | None = None) -> dict:
    """Быстрое извлечение названия, обложки и доступных качеств ролика."""
    meta: dict = {
        "url": url,
        "title": "",
        "thumb_url": None,
        "thumb_image": None,
        "heights": None,
    }
    # 1. Попытка через Playerjs
    try:
        probe = _playerjs_probe(url, proxy)
        if probe:
            s, files, title, poster = probe
            meta["heights"] = sorted({h for h, _ in files}, reverse=True)
            meta["title"] = title.strip()
            meta["thumb_url"] = poster or None
    except Exception:
        pass

    # 2. Попытка через yt-dlp flat extract (для YouTube, VK и др.)
    if not meta["title"]:
        try:
            opts = {
                "skip_download": True,
                "extract_flat": "in_playlist",
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 8,
            }
            if proxy:
                opts["proxy"] = proxy if "://" in proxy else f"http://{proxy}"
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    meta["title"] = (info.get("title") or "").strip()
                    if not meta["thumb_url"]:
                        meta["thumb_url"] = info.get("thumbnail")
        except Exception:
            pass

    # 3. Скачиваем миниатюру в память (112x63)
    if meta.get("thumb_url"):
        try:
            import io
            from PIL import Image
            from curl_cffi import requests as cr
            s_img = cr.Session()
            kw = {"timeout": 8}
            if proxy:
                kw["proxies"] = {"http": proxy, "https": proxy}
            r_img = s_img.get(meta["thumb_url"], **kw)
            if r_img.status_code == 200 and r_img.content:
                pil_img = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                pil_img.thumbnail((112, 63), Image.Resampling.LANCZOS)
                meta["thumb_image"] = pil_img
        except Exception:
            pass

    return meta


def playerjs_try_download(url: str, quality: str, outdir: Path, events: queue.Queue,
                          cancel_event: threading.Event, proxy: str | None):
    """None — сайт не распознан; True — скачано; False — распознан, но ошибка (уже выдана)."""
    probe = _playerjs_probe(url, proxy)
    if not probe:
        return None
    s, files, title = probe[:3]
    kwargs: dict = {"impersonate": "chrome", "timeout": 30}
    if proxy:
        kwargs["proxies"] = {"http": proxy, "https": proxy}

    media = _pick_quality(files, quality)
    name = re.sub(r"[\\/:*?\"<>|]+", "_", title.strip())[:120] or "video"
    path = outdir / f"{name}.mp4"

    events.put(("status", tr_global("status_direct_download")))
    import time as _time
    total: int | None = None
    done = 0
    tries = 0
    t0 = _time.time()
    f = path.open("wb")
    try:
        while True:
            if cancel_event.is_set():
                raise Cancelled()
            headers = {"Referer": url}
            if done:
                headers["Range"] = f"bytes={done}-"
            try:
                tries += 1
                r = s.get(media, headers=headers, stream=True, **dict(kwargs, timeout=60))
                if r.status_code == 416 and done:
                    if not total or done >= total:
                        break  # файл уже докачан
                    events.put(("error", tr_global("err_cdn_resume")))
                    return False
                if r.status_code >= 400:
                    events.put(("error", cdn_block_hint() if r.status_code == 403
                                else tr_global("cdn_responded", code=r.status_code)))
                    return False
                if r.status_code == 200 and done:
                    events.put(("error", tr_global("err_cdn_resume")))
                    return False
                if total is None:
                    if r.status_code == 206:
                        m = re.search(r"/(\d+)\s*$", r.headers.get("content-range") or "")
                        total = int(m.group(1)) if m else None
                    else:
                        total = int(r.headers.get("content-length") or 0) or None
                for chunk in r.iter_content(1 << 18):
                    if cancel_event.is_set():
                        raise Cancelled()
                    f.write(chunk)
                    done += len(chunk)
                    elapsed = max(_time.time() - t0, 1)
                    speed = done / elapsed
                    speed_unit = "/с" if get_current_lang() == "ru" else "/s"
                    parts = [f"{human_size(done)} / {human_size(total)}" if total else human_size(done),
                             f"{human_size(speed)}{speed_unit}"]
                    if total and speed > 0:
                        eta = int((total - done) / speed)
                        mm_ss = f"{eta // 60:02d}:{eta % 60:02d}"
                        if get_current_lang() == "ru":
                            parts.append(f"осталось {mm_ss}")
                        elif get_current_lang() == "zh":
                            parts.append(f"剩余 {mm_ss}")
                        else:
                            parts.append(f"{mm_ss} left")
                    events.put(("progress", {
                        "fraction": done / total if total else None,
                        "text": "  •  ".join(parts),
                        "file": path.name,
                    }))
                if total and done < total:
                    if tries >= 5:
                        events.put(("error", tr_global("err_cdn_abort")))
                        return False
                    events.put(("status", tr_global("status_reconnecting_at", done=human_size(done))))
                    continue
                break  # поток дошёл до конца
            except Cancelled:
                raise
            except Exception:
                if not done or tries >= 5:
                    events.put(("error", tr_global("err_cdn_abort")))
                    return False
                events.put(("status", tr_global("status_reconnecting_at", done=human_size(done))))
    except Cancelled:
        f.close()
        path.unlink(missing_ok=True)
        raise
    except Exception as e:
        f.close()
        path.unlink(missing_ok=True)
        events.put(("error", f"{type(e).__name__}: {e}"))
        return False
    f.close()
    events.put(("file_downloaded", path.name))
    return True


# ---------------------------------------------------------------------------
# Режим «через браузер»: реальный Chrome/Edge + CDP.
# Нужен для сайтов с бот-защитой, которая отсекает любые программные клиенты:
# браузер скачивает файл сам, а мы лишь направляем его и следим за прогрессом.
# ---------------------------------------------------------------------------

def find_browser_exe() -> Path | None:
    roots = [
        os.environ.get("PROGRAMFILES", ""),
        os.environ.get("PROGRAMFILES(X86)", ""),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    names = [
        "Google/Chrome/Application/chrome.exe",
        "Microsoft/Edge/Application/msedge.exe",
    ]
    for root in roots:
        for name in names:
            p = Path(root) / name
            if p.is_file():
                return p
    return None


def system_proxy_server() -> str | None:
    """ProxyServer из настроек системы (даже если прокси сейчас выключен)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
            return winreg.QueryValueEx(key, "ProxyServer")[0]
    except Exception:
        return None


def cdn_block_hint() -> str:
    hint = tr_global("cdn_403_hint")
    sp = system_proxy_server()
    if sp:
        hint += " " + tr_global("cdn_403_proxy_hint", sp=sp)
    return hint


class BrowserDownloader:
    PORT = 9334

    def __init__(self, url: str, outdir: Path, events: queue.Queue,
                 cancel_event: threading.Event, proxy: str | None = None):
        self.url = url
        self.outdir = outdir
        self.events = events
        self.cancel_event = cancel_event
        self.proxy = proxy
        self.proc = None

    def _emit(self, kind, payload=None):
        self.events.put((kind, payload))

    def run(self) -> tuple[str, str]:
        import json as _json
        import time as _time
        import urllib.request

        import websocket

        exe = find_browser_exe()
        if exe is None:
            err = tr_global("browser_not_found")
            self._emit("error", err)
            return ("error", err)

        profiles = []
        real = Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data"
        if "chrome" in exe.name and real.is_dir() and not (real / "lockfile").exists():
            profiles.append(real)  # настоящий профиль: cookies и история как у человека
        profiles.append(data_dir() / "browser_profile")

        last_err = None
        for profile in profiles:
            if self.cancel_event.is_set():
                self._emit("cancelled", None)
                return ("cancelled", "")
            argv = [
                str(exe), f"--remote-debugging-port={self.PORT}",
                f"--user-data-dir={profile}",
                "--no-first-run", "--no-default-browser-check", "--start-maximized",
                "--remote-allow-origins=*",
            ]
            if self.proxy:
                argv.append(f"--proxy-server={self.proxy}")
            self.proc = subprocess.Popen(argv)
            try:
                self._run_ws(_json, _time, urllib, websocket)
                return ("finished_ok", "")
            except Cancelled:
                self._emit("cancelled", None)
                return ("cancelled", "")
            except Exception as e:  # noqa: BLE001
                last_err = e
            finally:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        err = f"{tr_global('browser_mode_prefix')}: {type(last_err).__name__}: {last_err}"
        self._emit("error", err)
        return ("error", err)

    def _run_ws(self, _json, _time, urllib, websocket):
        base = f"http://127.0.0.1:{self.PORT}"
        target = None
        for _ in range(40):
            if self.cancel_event.is_set():
                raise Cancelled()
            try:
                tabs = _json.load(urllib.request.urlopen(f"{base}/json", timeout=2))
                target = next((t for t in tabs if t["type"] == "page"), None)
                if target:
                    break
            except Exception:
                _time.sleep(0.5)
        if not target:
            raise RuntimeError(tr_global("browser_cdp_timeout"))

        ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=5)
        msg_id = 0

        def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            ws.send(_json.dumps({"id": msg_id, "method": method, "params": params or {}}))

        send("Network.enable")
        send("Page.enable")
        send("Runtime.enable")
        send("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(self.outdir),
        })
        self._emit("status", tr_global("browser_opening_page"))
        send("Page.navigate", {"url": self.url})

        video_req = None
        body_msg_id = None
        received = 0
        title = "video"
        next_click = _time.time() + 4
        clicks_left = 8
        deadline = _time.time() + 300

        while _time.time() < deadline:
            if self.cancel_event.is_set():
                raise Cancelled()
            if _time.time() >= next_click:
                if clicks_left > 0:
                    send("Runtime.evaluate", {"expression":
                          "(()=>{const p=document.getElementById('kt_player')||document.getElementById('player')"
                          "||document.querySelector('video');"
                          "if(!p)return 'noplayer';const r=p.getBoundingClientRect();"
                          "return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2})})()"})
                    clicks_left -= 1
                else:
                    send("Runtime.evaluate", {"expression": "'T:'+document.title"})
                next_click = _time.time() + 4

            try:
                ws.settimeout(0.5)
                ev = _json.loads(ws.recv())
            except websocket.WebSocketTimeoutException:
                continue
            except Exception:
                break

            method = ev.get("method")
            if ev.get("id") and "result" in ev:
                val = ev["result"].get("result", {})
                if val.get("type") == "string" and str(val.get("value", "")).startswith("{"):
                    pt = _json.loads(val["value"])
                    for etype in ("mousePressed", "mouseReleased"):
                        send("Input.dispatchMouseEvent",
                             {"type": etype, "x": pt["x"], "y": pt["y"],
                              "button": "left", "clickCount": 1})
                elif ev["id"] == body_msg_id:
                    self._save_body(val, title)
                    self._emit("finished_ok", None)
                    return
                elif val.get("type") == "string" and str(val.get("value", "")).startswith("T:"):
                    title = self._safe_title(val["value"][2:])
            elif method == "Network.responseReceived":
                resp = ev["params"].get("response", {})
                rurl = resp.get("url", "")
                if (resp.get("status") or 0) >= 400 and (
                        "get_file" in rurl or "cdnservice" in rurl
                        or resp.get("mimeType", "").startswith("video")):
                    self._emit("error", cdn_block_hint())
                    return
                if resp.get("mimeType", "").startswith("video") and not video_req:
                    video_req = ev["params"].get("requestId")
                    self._emit("status", tr_global("browser_video_started"))
            elif method == "Network.dataReceived":
                if ev["params"].get("requestId") == video_req:
                    received += ev["params"].get("dataLength", 0)
                    self._emit("progress", {"fraction": None,
                                            "text": f"{tr_global('browser_received')} {human_size(received)}"})
            elif method == "Network.loadingFinished":
                if ev["params"].get("requestId") == video_req and body_msg_id is None:
                    self._emit("status", tr_global("browser_stream_finished"))
                    body_msg_id = msg_id + 1
                    send("Network.getResponseBody", {"requestId": video_req})

        raise RuntimeError(tr_global("browser_timeout_hint"))

    def _safe_title(self, title: str) -> str:
        import re as _re
        name = _re.sub(r"[\\\\/:*?\"<>|]+", "_", title).strip()
        return name[:120] or "video"

    def _save_body(self, val: dict, title: str) -> None:
        import base64 as _b64
        body = val.get("body", "")
        if val.get("base64Encoded"):
            data = _b64.b64decode(body)
        else:
            data = body.encode("utf-8", "surrogateescape")
        path = self.outdir / f"{title}.mp4"
        path.write_bytes(data)
        self._emit("file_downloaded", path.name)

    def _poll_files(self, before: set) -> str | None:
        """Имя завершённого нового файла в outdir или None."""
        try:
            now = {p.name for p in self.outdir.iterdir()}
        except Exception:
            return None
        if any(n.endswith(".crdownload") for n in now):
            sizes = [p.stat().st_size for p in self.outdir.iterdir()
                     if p.name.endswith(".crdownload")]
            if sizes:
                self._emit("progress", {"fraction": None,
                                        "text": f"{tr_global('browser_received')} {human_size(sizes[0])}"})
            return None
        fresh = [n for n in now - before if not n.endswith(".crdownload")]
        return fresh[0] if fresh else None


# ---------------------------------------------------------------------------
# Интерфейс
# ---------------------------------------------------------------------------

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.events: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self._busy = False
        self._outdir = Path(self.cfg["download_dir"])
        self._analyze_after: str | None = None
        self._analyzed_url: str | None = None
        self._queue: list[dict] = []
        self._worker_alive = False
        self._current: dict | None = None
        self._ff_busy = False
        self._q_sel = -1
        self._current_meta: dict | None = None
        self._thumb_img_ref = None
        self._tray = None

        self.lang = self.cfg.get("lang", "en")
        set_current_lang(self.lang)
        if self.cfg.get("quality") in ("Best", "Лучшее", "最佳"):
            self.cfg["quality"] = self.tr("quality_best")

        self.title(f"{APP_NAME} {APP_VERSION} — {self.tr('app_title')}")
        self.geometry("760x650")
        self.minsize(680, 520)
        self._set_icon()
        self._build_ui()
        self._init_tray()
        self._apply_language(self.lang)

        self.after(100, self._poll_events)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def tr(self, key: str, **kwargs) -> str:
        return tr_global(key, lang=self.lang, **kwargs)

    # -- трей и уведомления ---------------------------------------------------

    def _init_tray(self):
        if not _HAS_PYSTRAY:
            return
        try:
            ico_path = base_dir() / "assets" / "icon.ico"
            if not ico_path.is_file():
                ico_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
            if ico_path.is_file():
                image = Image.open(str(ico_path))
            else:
                image = Image.new("RGBA", (32, 32), (47, 126, 247, 255))

            self._tray = pystray.Icon("VideoGrab", image, f"{APP_NAME} — {self.tr('app_title')}")
            self._update_tray_menu()
            threading.Thread(target=self._tray.run, daemon=True).start()
        except Exception:
            self._tray = None

    def _update_tray_menu(self):
        if getattr(self, "_tray", None) is None:
            return
        try:
            menu = pystray.Menu(
                pystray.MenuItem(self.tr("tray_open"), self._tray_restore, default=True),
                pystray.MenuItem(self.tr("tray_hide"), self._tray_hide),
                pystray.MenuItem(self.tr("tray_folder"), lambda *_: self.after(0, self._open_folder)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(self.tr("tray_exit"), self._tray_exit),
            )
            self._tray.menu = menu
            self._tray.title = f"{APP_NAME} — {self.tr('app_title')}"
        except Exception:
            pass

    def _tray_restore(self, *_):
        self.after(0, self._restore_window)

    def _restore_window(self):
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()

    def _tray_hide(self, *_):
        self.after(0, self.withdraw)

    def _tray_exit(self, *_):
        self.after(0, self._force_exit)

    def _notify(self, title: str, message: str):
        if winsound is not None:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
        if getattr(self, "_tray", None) is not None:
            try:
                self._tray.notify(message, title)
            except Exception:
                pass

    # -- построение интерфейса ------------------------------------------------

    def _set_icon(self):
        icon = base_dir() / "assets" / "icon.ico"
        if not icon.is_file():
            icon = Path(__file__).resolve().parent / "assets" / "icon.ico"
        try:
            if icon.is_file():
                self.iconbitmap(str(icon))
        except Exception:
            pass

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._log_history = []
        self._settings_window = None
        self._log_window = None

        # -------------------------------------------------------------------
        # 1. Шапка (Header): Логотип, ffmpeg, кнопки Настройки, Журнал, В трей
        # -------------------------------------------------------------------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 8))

        # Слева: Логотип и бейдж
        logo_box = ctk.CTkFrame(header, fg_color="transparent")
        logo_box.pack(side="left")
        ctk.CTkLabel(
            logo_box, text=f"⬇  {APP_NAME}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            logo_box, text="PRO",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=("#2563eb", "#1d4ed8"),
            text_color="#ffffff",
            corner_radius=4, padx=6, pady=1,
        ).pack(side="left", padx=(8, 0))

        # Справа: кнопки
        if _HAS_PYSTRAY:
            self.tray_button = ctk.CTkButton(
                header, text=self.tr("to_tray"), width=70, height=28,
                fg_color=("gray85", "#222533"), hover_color=("gray75", "#2d3245"),
                text_color=("gray20", "gray85"), corner_radius=8,
                font=ctk.CTkFont(size=11), command=self.withdraw,
            )
            self.tray_button.pack(side="right", padx=(8, 0))

        self.settings_btn = ctk.CTkButton(
            header, text=self.tr("settings"), width=92, height=28,
            fg_color=("gray85", "#222533"), hover_color=("gray75", "#2d3245"),
            text_color=("gray20", "gray85"), corner_radius=8,
            font=ctk.CTkFont(size=11), command=self._open_settings_window,
        )
        self.settings_btn.pack(side="right", padx=(8, 0))

        self.log_btn = ctk.CTkButton(
            header, text=self.tr("logs"), width=76, height=28,
            fg_color=("gray85", "#222533"), hover_color=("gray75", "#2d3245"),
            text_color=("gray20", "gray85"), corner_radius=8,
            font=ctk.CTkFont(size=11), command=self._open_log_window,
        )
        self.log_btn.pack(side="right", padx=(8, 0))

        self.ffmpeg_label = ctk.CTkLabel(
            header, text=self.tr("ffmpeg_ready"), font=ctk.CTkFont(size=11),
            text_color=OK_GREEN,
        )
        self.ffmpeg_label.pack(side="right", padx=(8, 4))

        self.ffmpeg_button = ctk.CTkButton(
            header, text=self.tr("download_ffmpeg"), width=115, height=28,
            fg_color="#dc2626", hover_color="#b91c1c", corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"), command=self._download_ffmpeg,
        )

        # -------------------------------------------------------------------
        # 2. Hero-карточка: Ввод ссылки + параметры + запуск
        # -------------------------------------------------------------------
        self.hero_card = ctk.CTkFrame(
            self, corner_radius=14,
            fg_color=("gray92", "#181a24"), border_width=1.5,
            border_color=("#3b82f6", "#2563eb"),
        )
        self.hero_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        self.hero_card.grid_columnconfigure(0, weight=1)

        # Подсказка
        hero_top = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        hero_top.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        self.hero_title_lbl = ctk.CTkLabel(
            hero_top, text=self.tr("hero_title"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.hero_title_lbl.pack(side="left")
        self.hero_sub_lbl = ctk.CTkLabel(
            hero_top, text=self.tr("hero_sub"),
            font=ctk.CTkFont(size=11), text_color=("gray45", "gray60"),
        )
        self.hero_sub_lbl.pack(side="left", padx=(6, 0))

        # Строка ввода
        input_box = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        input_box.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        input_box.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            input_box, height=42, corner_radius=10,
            placeholder_text="https://...",
            font=ctk.CTkFont(size=13),
            border_color=("gray75", "#2e3447"),
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.url_entry.bind("<Return>", lambda _e: self._start())
        self.url_entry.bind("<Button-3>", lambda _e: (self._paste_from_clipboard(), "break")[1])
        self.url_entry.bind("<FocusOut>", self._schedule_analyze)

        self.paste_btn = ctk.CTkButton(
            input_box, text=self.tr("paste_btn"), width=95, height=42, corner_radius=10,
            fg_color=("gray82", "#232634"), hover_color=("gray75", "#2e3245"),
            text_color=("gray15", "gray90"), font=ctk.CTkFont(size=12, weight="bold"),
            command=self._paste_from_clipboard,
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 8))

        self.dl_button = ctk.CTkButton(
            input_box, text=self.tr("download_btn"), width=120, height=42, corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self._start,
        )
        self.dl_button.grid(row=0, column=2, padx=(0, 6))

        self.browser_button = ctk.CTkButton(
            input_box, text="🌐", width=42, height=42, corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color=("gray82", "#232634"), hover_color=("gray75", "#2e3245"),
            text_color=("gray15", "gray90"),
            command=self._start_browser,
        )
        self.browser_button.grid(row=0, column=3)

        # Превью ролика (раскрывается при получении метаданных)
        self.preview_card = ctk.CTkFrame(
            self.hero_card, corner_radius=10,
            fg_color=("gray85", "#1f2230"), border_width=1, border_color=("gray75", "#2d3345"),
        )
        self.preview_card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.preview_card.grid_columnconfigure(1, weight=1)

        self.thumb_label = ctk.CTkLabel(self.preview_card, text="", width=96, height=54)
        self.thumb_label.grid(row=0, column=0, rowspan=2, padx=(8, 10), pady=6)

        self.video_title_label = ctk.CTkLabel(
            self.preview_card, text="", font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w", justify="left"
        )
        self.video_title_label.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(6, 0))

        self.video_meta_label = ctk.CTkLabel(
            self.preview_card, text="", font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray65"), anchor="w"
        )
        self.video_meta_label.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(0, 6))
        self.preview_card.grid_remove()

        # Быстрые селекторы
        hero_opts = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        hero_opts.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

        initial_qualities = [self.tr("quality_best")] + [q for q in QUALITIES if q != "Best"]
        self.mode_seg = ctk.CTkSegmentedButton(
            hero_opts, values=[self.tr("mode_video"), self.tr("mode_audio")],
            height=26, corner_radius=6, font=ctk.CTkFont(size=11),
            command=self._on_mode_change,
        )
        self.mode_seg.pack(side="left")

        self.quality_label = ctk.CTkLabel(hero_opts, text=self.tr("quality"), font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"))
        self.quality_label.pack(side="left", padx=(14, 6))
        self.quality_menu = ctk.CTkOptionMenu(
            hero_opts, values=initial_qualities, width=95, height=26, corner_radius=6,
            font=ctk.CTkFont(size=11),
            variable=ctk.StringVar(value=self.cfg.get("quality", initial_qualities[0])),
        )
        self.quality_menu.pack(side="left")

        # -------------------------------------------------------------------
        # 3. Список активных загрузок (Центральная область)
        # -------------------------------------------------------------------
        feed_header = ctk.CTkFrame(self, fg_color="transparent")
        feed_header.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 4))

        self.queue_count_label = ctk.CTkLabel(
            feed_header, text=self.tr("active_downloads"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray40", "gray60"),
        )
        self.queue_count_label.pack(side="left")

        self.clear_done_btn = ctk.CTkButton(
            feed_header, text=self.tr("clear_done"), width=130, height=22,
            fg_color="transparent", hover_color=("gray85", "#222533"),
            text_color=ACCENT, font=ctk.CTkFont(size=11),
            command=self._q_clear_done,
        )
        self.clear_done_btn.pack(side="right")

        self.clear_all_btn = ctk.CTkButton(
            feed_header, text=self.tr("clear_all"), width=80, height=22,
            fg_color="transparent", hover_color=("gray85", "#222533"),
            text_color=("gray40", "gray60"), font=ctk.CTkFont(size=11),
            command=self._q_clear_all,
        )
        self.clear_all_btn.pack(side="right", padx=(0, 6))

        self.queue_scroll = ctk.CTkScrollableFrame(
            self, corner_radius=12,
            fg_color=("gray94", "#151722"), border_width=1, border_color=("gray85", "#202331"),
        )
        self.queue_scroll.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))

        # -------------------------------------------------------------------
        # 4. Нижний статус-бар (Footer)
        # -------------------------------------------------------------------
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 12))

        self.status_label = ctk.CTkLabel(
            bottom, text=self.tr("ready_status"), anchor="w",
            font=ctk.CTkFont(size=12), text_color=("gray30", "gray70"),
        )
        self.status_label.pack(side="left")

        self.cancel_button = ctk.CTkButton(
            bottom, text=self.tr("cancel"), width=90, height=30, corner_radius=8,
            state="disabled", fg_color=DANGER, hover_color="#b91c1c",
            font=ctk.CTkFont(size=11, weight="bold"), command=self._cancel,
        )
        self.cancel_button.pack(side="right", padx=(8, 0))

        self.folder_btn = ctk.CTkButton(
            bottom, text=self.tr("downloads_folder"), width=130, height=30, corner_radius=8,
            fg_color=("gray85", "#222533"), hover_color=("gray75", "#2d3245"),
            text_color=("gray20", "gray85"),
            font=ctk.CTkFont(size=11), command=self._open_folder,
        )
        self.folder_btn.pack(side="right")

        # -------------------------------------------------------------------
        # 5. Скрытые / фоновые элементы (для полной совместимости с ядром)
        # -------------------------------------------------------------------
        self._hidden_support = ctk.CTkFrame(self)
        self.dir_entry = ctk.CTkEntry(self._hidden_support)
        self.dir_entry.insert(0, os.path.normpath(self.cfg.get("download_dir", str(default_download_dir()))))
        self.proxy_entry = ctk.CTkEntry(self._hidden_support)
        if self.cfg.get("proxy"):
            self.proxy_entry.insert(0, self.cfg["proxy"])
        self.proxy_badge = ctk.CTkLabel(self._hidden_support, text="")
        self.proxy_panel = ctk.CTkFrame(self._hidden_support)
        self.proxy_toggle_btn = ctk.CTkButton(self._hidden_support, text="proxy")
        self.proxy_spoiler_row = self._hidden_support
        self.progress = ctk.CTkProgressBar(self._hidden_support)
        self.progress.set(0)
        self.progress_label = ctk.CTkLabel(self._hidden_support, text="")
        self.tabs = self._hidden_support
        self.log = ctk.CTkTextbox(self._hidden_support)

        self.mode_seg.set(self.tr("mode_audio") if is_audio_mode(self.cfg.get("mode", MODE_VIDEO)) else self.tr("mode_video"))
        self._on_mode_change(self.mode_seg.get())

        self.url_entry.focus_set()
        self.bind("<Control-v>", self._paste_kb)
        self.bind("<Control-V>", self._paste_kb)

    def _apply_language(self, lang: str | None = None):
        if lang:
            self.lang = lang
            self.cfg["lang"] = lang
        set_current_lang(self.lang)
        self.title(f"{APP_NAME} {APP_VERSION} — {self.tr('app_title')}")
        if hasattr(self, "tray_button") and self.tray_button:
            self.tray_button.configure(text=self.tr("to_tray"))
        if hasattr(self, "settings_btn") and self.settings_btn:
            self.settings_btn.configure(text=self.tr("settings"))
        if hasattr(self, "log_btn") and self.log_btn:
            self.log_btn.configure(text=self.tr("logs"))
        if hasattr(self, "ffmpeg_button") and self.ffmpeg_button:
            self.ffmpeg_button.configure(text=self.tr("download_ffmpeg"))
        self._show_ffmpeg_state()

        if hasattr(self, "hero_title_lbl") and self.hero_title_lbl:
            self.hero_title_lbl.configure(text=self.tr("hero_title"))
        if hasattr(self, "hero_sub_lbl") and self.hero_sub_lbl:
            self.hero_sub_lbl.configure(text=self.tr("hero_sub"))
        if hasattr(self, "paste_btn") and self.paste_btn:
            self.paste_btn.configure(text=self.tr("paste_btn"))
        if hasattr(self, "dl_button") and self.dl_button:
            self.dl_button.configure(text=self.tr("download_btn"))
        if hasattr(self, "mode_seg") and self.mode_seg:
            is_audio = is_audio_mode(self.mode_seg.get())
            self.mode_seg.configure(values=[self.tr("mode_video"), self.tr("mode_audio")])
            self.mode_seg.set(self.tr("mode_audio") if is_audio else self.tr("mode_video"))
        if hasattr(self, "quality_label") and self.quality_label:
            self.quality_label.configure(text=self.tr("quality"))
        if hasattr(self, "quality_menu") and self.quality_menu:
            curr_vals = list(self.quality_menu.cget("values") or [])
            if curr_vals:
                curr_selected = self.quality_menu.get()
                was_best = curr_selected in ("Best", "Лучшее", "最佳", curr_vals[0])
                curr_vals[0] = self.tr("quality_best")
                self.quality_menu.configure(values=curr_vals)
                if was_best:
                    self.quality_menu.set(curr_vals[0])

        if hasattr(self, "clear_done_btn") and self.clear_done_btn:
            self.clear_done_btn.configure(text=self.tr("clear_done"))
        if hasattr(self, "clear_all_btn") and self.clear_all_btn:
            self.clear_all_btn.configure(text=self.tr("clear_all"))

        if hasattr(self, "cancel_button") and self.cancel_button:
            self.cancel_button.configure(text=self.tr("cancel"))
        if hasattr(self, "folder_btn") and self.folder_btn:
            self.folder_btn.configure(text=self.tr("downloads_folder"))
        if hasattr(self, "status_label") and self.status_label:
            cur = self.status_label.cget("text")
            if cur in ("● Готов к работе", "● Ready to work", "● 就绪", "● Ready"):
                self._set_status(self.tr("ready_status"))

        if getattr(self, "_current_meta", None) and hasattr(self, "video_meta_label"):
            url = self.url_entry.get().strip()
            domain = url.split("/")[2] if "//" in url else ""
            meta_source = self.tr("meta_source", domain=domain)
            meta_ready = self.tr("meta_ready")
            self.video_meta_label.configure(text=f"{meta_source}  •  {meta_ready}")

        self._refresh_queue_ui()
        self._update_tray_menu()

    def _open_settings_window(self):
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.focus()
            return
        w = ctk.CTkToplevel(self)
        w.title(self.tr("settings_window_title"))
        w.geometry("520x330")
        w.resizable(False, False)
        self._settings_window = w

        w_head_lbl = ctk.CTkLabel(w, text=self.tr("settings_header"), font=ctk.CTkFont(size=16, weight="bold"))
        w_head_lbl.pack(anchor="w", padx=20, pady=(16, 12))

        # Выбор языка
        f_lang = ctk.CTkFrame(w, fg_color="transparent")
        f_lang.pack(fill="x", padx=20, pady=(0, 10))
        w_lang_lbl = ctk.CTkLabel(f_lang, text=self.tr("settings_lang"), font=ctk.CTkFont(size=12, weight="bold"))
        w_lang_lbl.pack(anchor="w", pady=(0, 4))

        selected_lang_var = ctk.StringVar(value=LANG_LABELS.get(self.lang, "English"))

        def _on_lang_picked(choice: str):
            code = LABEL_TO_LANG.get(choice, "en")
            self._apply_language(code)
            w.title(self.tr("settings_window_title"))
            w_head_lbl.configure(text=self.tr("settings_header"))
            w_lang_lbl.configure(text=self.tr("settings_lang"))
            w_dir_lbl.configure(text=self.tr("settings_dir"))
            w_browse_btn.configure(text=self.tr("settings_browse"))
            w_proxy_lbl.configure(text=self.tr("settings_proxy"))
            w_save_btn.configure(text=self.tr("settings_save"))
            w_cancel_btn.configure(text=self.tr("settings_cancel"))

        w_lang_menu = ctk.CTkOptionMenu(
            f_lang, values=["English", "Русский", "中文"],
            height=34, font=ctk.CTkFont(size=12),
            variable=selected_lang_var, command=_on_lang_picked,
        )
        w_lang_menu.pack(anchor="w")

        # Папка
        f_dir = ctk.CTkFrame(w, fg_color="transparent")
        f_dir.pack(fill="x", padx=20, pady=(0, 10))
        w_dir_lbl = ctk.CTkLabel(f_dir, text=self.tr("settings_dir"), font=ctk.CTkFont(size=12, weight="bold"))
        w_dir_lbl.pack(anchor="w", pady=(0, 4))
        r_dir = ctk.CTkFrame(f_dir, fg_color="transparent")
        r_dir.pack(fill="x")
        r_dir.grid_columnconfigure(0, weight=1)
        w_dir_entry = ctk.CTkEntry(r_dir, height=34, font=ctk.CTkFont(size=12))
        w_dir_entry.insert(0, self.dir_entry.get())
        w_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        def _choose():
            self._choose_dir()
            w_dir_entry.delete(0, "end")
            w_dir_entry.insert(0, self.dir_entry.get())
        w_browse_btn = ctk.CTkButton(r_dir, text=self.tr("settings_browse"), width=86, height=34, command=_choose)
        w_browse_btn.grid(row=0, column=1)

        # Прокси
        f_proxy = ctk.CTkFrame(w, fg_color="transparent")
        f_proxy.pack(fill="x", padx=20, pady=(0, 14))
        w_proxy_lbl = ctk.CTkLabel(f_proxy, text=self.tr("settings_proxy"), font=ctk.CTkFont(size=12, weight="bold"))
        w_proxy_lbl.pack(anchor="w", pady=(0, 4))
        w_proxy_entry = ctk.CTkEntry(f_proxy, height=34, font=ctk.CTkFont(size=12),
                                     placeholder_text=self.tr("settings_proxy_ph"))
        w_proxy_entry.insert(0, self.proxy_entry.get())
        w_proxy_entry.pack(fill="x")

        # Кнопки
        def _save():
            code = LABEL_TO_LANG.get(selected_lang_var.get(), "en")
            self._apply_language(code)
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, w_dir_entry.get().strip())
            self._outdir = Path(os.path.normpath(w_dir_entry.get().strip() or str(default_download_dir())))
            self.cfg["download_dir"] = str(self._outdir)
            self.proxy_entry.delete(0, "end")
            self.proxy_entry.insert(0, w_proxy_entry.get().strip())
            self.cfg["proxy"] = w_proxy_entry.get().strip()
            self.cfg["lang"] = code
            save_config(self.cfg)
            w.destroy()

        b_row = ctk.CTkFrame(w, fg_color="transparent")
        b_row.pack(fill="x", padx=20, pady=(6, 0))
        w_save_btn = ctk.CTkButton(b_row, text=self.tr("settings_save"), width=120, height=32, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=_save)
        w_save_btn.pack(side="right")
        w_cancel_btn = ctk.CTkButton(b_row, text=self.tr("settings_cancel"), width=90, height=32, fg_color="gray30", hover_color="gray25", command=w.destroy)
        w_cancel_btn.pack(side="right", padx=(0, 8))

    def _open_log_window(self):
        if self._log_window is not None and self._log_window.winfo_exists():
            self._log_window.focus()
            return
        w = ctk.CTkToplevel(self)
        w.title(self.tr("log_window_title"))
        w.geometry("640x420")
        self._log_window = w

        top = ctk.CTkFrame(w, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(top, text=self.tr("log_header"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        txt = ctk.CTkTextbox(w, font=ctk.CTkFont(size=12), wrap="word")
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        txt.insert("end", "".join(self._log_history))
        txt.configure(state="disabled")

        def _clear():
            self._log_history.clear()
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            txt.configure(state="disabled")

        ctk.CTkButton(top, text=self.tr("log_clear"), width=96, height=26, fg_color="gray30",
                       hover_color="gray25", font=ctk.CTkFont(size=11), command=_clear).pack(side="right")

    def _toggle_proxy_panel(self):
        self._open_settings_window()

    def _on_proxy_change(self, event=None):
        val = self.proxy_entry.get().strip()
        self.cfg["proxy"] = val

    # -- служебное --------------------------------------------------------------

    def _show_ffmpeg_state(self):
        if find_ffmpeg_dir():
            self.ffmpeg_label.configure(text=self.tr("ffmpeg_ready"), text_color=OK_GREEN)
            self.ffmpeg_button.pack_forget()
        else:
            self.ffmpeg_label.configure(text=self.tr("ffmpeg_missing"),
                                        text_color=DANGER)
            self.ffmpeg_button.configure(text=self.tr("download_ffmpeg"))
            self.ffmpeg_button.pack(side="right", padx=(8, 0))

    def _download_ffmpeg(self):
        if self._ff_busy:
            return
        self._ff_busy = True
        self.ffmpeg_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress.set(0)
        self._set_status(self.tr("ffmpeg_downloading"))
        threading.Thread(target=self._ffmpeg_worker, daemon=True).start()

    def _ffmpeg_worker(self):
        try:
            download_ffmpeg(self.events, self.cancel_event)
            self.events.put(("ffmpeg_installed", None))
        except Cancelled:
            self.events.put(("cancelled", None))
        except Exception as e:
            self.events.put(("error", f"{self.tr('ffmpeg_download_failed')}: {type(e).__name__}: {e}"))

    def _log(self, text: str):
        if not hasattr(self, "_log_history"):
            self._log_history = []
        self._log_history.append(text + "\n")
        try:
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        except Exception:
            pass

    def _set_status(self, text: str, color: str | None = None):
        self.status_label.configure(text=text, text_color=color or ("gray90" if ctk.get_appearance_mode() == "Dark" else "gray10"))

    def _paste_from_clipboard(self):
        try:
            text = self.clipboard_get().strip()
        except Exception:
            return
        if text:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
            self.url_entry.focus_set()
            self._schedule_analyze()

    # -- предварительный анализ ссылки (доступные качества) -------------------

    def _schedule_analyze(self, *_):
        url = self.url_entry.get().strip()
        if not url or url == self._analyzed_url:
            return
        if self._analyze_after is not None:
            self.after_cancel(self._analyze_after)
        self._analyze_after = self.after(800, lambda: self._start_analyze(url))

    def _start_analyze(self, url: str):
        self._analyze_after = None
        if url != self.url_entry.get().strip():
            return
        self._analyzed_url = url
        threading.Thread(target=self._analyze_worker, args=(url,), daemon=True).start()

    def _analyze_worker(self, url: str):
        meta = fetch_video_meta(url, self.proxy_entry.get().strip() or None)
        self.events.put(("analysis", {"url": url, "meta": meta}))

    def _apply_analysis(self, url: str, meta: dict):
        if url != self.url_entry.get().strip():
            return
        self._current_meta = meta
        heights = meta.get("heights")
        if heights:
            values = [self.tr("quality_best")] + [f"{h}p" for h in heights]
            self._log(f"✔ {self.tr('available_qualities')}: {', '.join(values[1:])}")
        else:
            values = [self.tr("quality_best")] + [q for q in QUALITIES if q != "Best"]
        self.quality_menu.configure(values=values)
        if self.quality_menu.get() not in values:
            self.quality_menu.set(values[0])

        title = meta.get("title")
        thumb = meta.get("thumb_image")
        if title or thumb:
            if title:
                self.video_title_label.configure(text=title[:85])
                domain = url.split("/")[2] if "//" in url else ""
                meta_source = self.tr("meta_source", domain=domain)
                meta_ready = self.tr("meta_ready")
                self.video_meta_label.configure(text=f"{meta_source}  •  {meta_ready}")
            if thumb:
                try:
                    ctk_img = ctk.CTkImage(thumb, size=(112, 63))
                    self._thumb_img_ref = ctk_img
                    self.thumb_label.configure(image=ctk_img)
                except Exception:
                    pass
            self.preview_card.grid()

    def _paste_kb(self, event=None):
        # Ctrl+V работает из любого места окна, а не только когда поле в фокусе
        try:
            focused = self.focus_get()
        except Exception:
            focused = None
        if focused not in (self.url_entry, self.url_entry._entry):
            self._paste_from_clipboard()
            return "break"
        return None

    def _choose_dir(self):
        from tkinter import filedialog
        chosen = filedialog.askdirectory(initialdir=self._outdir if self._outdir.is_dir() else str(downloads_folder()),
                                         title=self.tr("select_folder_title"))
        if chosen:
            chosen_norm = os.path.normpath(chosen)
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, chosen_norm)
            self._outdir = Path(chosen_norm)
            self.cfg["download_dir"] = chosen_norm
            save_config(self.cfg)

    def _on_mode_change(self, value: str):
        if value == MODE_AUDIO:
            self.quality_menu.configure(state="disabled")
        else:
            self.quality_menu.configure(state="normal")

    def _open_folder(self):
        path = self._outdir if self._outdir.is_dir() else default_download_dir()
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(path))  # noqa: S606 — стандартный механизм Windows
        except Exception as e:
            self._set_status(f"{self.tr('folder_open_err')}{e}", DANGER)

    # -- очередь загрузок --------------------------------------------------------

    def _start(self):
        self._enqueue(browser=False)

    def _start_browser(self):
        self._enqueue(browser=True)

    def _enqueue(self, browser: bool):
        urls = [u for u in self.url_entry.get().strip().split() if u]
        if not urls:
            self._set_status(self.tr("enter_url_err"), DANGER)
            return
        outdir = Path(os.path.normpath(self.dir_entry.get().strip() or str(default_download_dir())))
        try:
            outdir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._set_status(f"{self.tr('mkdir_err')}{e}", DANGER)
            return

        self._outdir = outdir
        self.cfg.update({
            "download_dir": os.path.normpath(str(outdir)),
            "quality": self.quality_menu.get(),
            "mode": self.mode_seg.get(),
            "proxy": self.proxy_entry.get().strip(),
        })
        save_config(self.cfg)
        proxy = self.proxy_entry.get().strip() or None
        for u in urls:
            title = ""
            if self._current_meta and self._current_meta.get("url") == u:
                title = self._current_meta.get("title") or ""
            self._queue.append({
                "url": u, "title": title, "browser": browser, "outdir": outdir, "proxy": proxy,
                "mode": self.mode_seg.get(), "quality": self.quality_menu.get(),
                "status": "waiting", "note": "",
            })
        b_tag = f" ({self.tr('browser_mode_tag')})" if browser else ""
        self._log(f"{self.tr('status_enqueued')}{len(urls)}{b_tag}")
        self._refresh_queue_ui()
        if not self._worker_alive:
            self.cancel_event.clear()
        self._ensure_worker()

    def _ensure_worker(self):
        if self._worker_alive:
            return
        self._worker_alive = True
        self._busy = True
        self.cancel_button.configure(state="normal")
        threading.Thread(target=self._queue_worker, daemon=True).start()

    def _queue_worker(self):
        try:
            while True:
                item = next((i for i in self._queue if i["status"] == "waiting"), None)
                if item is None:
                    break
                item["status"] = "running"
                self.events.put(("item_start", {"item": item,
                                                "i": self._queue.index(item) + 1,
                                                "n": len(self._queue)}))
                try:
                    if item["browser"]:
                        result, note = BrowserDownloader(item["url"], item["outdir"], self.events,
                                                         self.cancel_event, item["proxy"]).run()
                    else:
                        result, note = run_download(item["url"], item["mode"], item["quality"],
                                                    item["outdir"], self.events, self.cancel_event,
                                                    item["proxy"])
                except Cancelled:
                    result, note = "cancelled", ""
                except Exception as e:  # noqa: BLE001
                    result, note = "error", f"{type(e).__name__}: {e}"

                if result == "cancelled":
                    cleanup_partial(item["outdir"])
                    self.cancel_event.clear()  # отмена съедена, следующий элемент качается
                self.events.put(("item_result", {"item": item, "result": result,
                                                 "note": note}))
        finally:
            self._worker_alive = False
            self.events.put(("queue_idle", None))

    def _on_item_start(self, item: dict, i: int, n: int):
        self.progress.set(0)
        self.progress_label.configure(text="")
        self._set_status(self.tr("status_downloading_item").format(i=i, n=n))
        b_tag = f"({self.tr('browser_mode_tag')}) " if item["browser"] else ""
        self._log(f"→ [{i}/{n}] {b_tag}{item['url']}")
        self._refresh_queue_ui()

    def _cancel(self):
        self.cancel_event.set()
        self._set_status(self.tr("status_stopping"))

    def _finish(self, ok: bool, message: str):
        if not self._worker_alive:
            self._busy = False
            self.cancel_button.configure(state="disabled")
        self._set_status(message, OK_GREEN if ok else DANGER)
        if ok:
            self.progress.set(1)

    # -- управление очередью ------------------------------------------------------

    _Q_MARK = {"waiting": "…", "running": "▶", "done": "✓", "error": "✗", "cancelled": "—"}

    def _q_pct(self, it: dict) -> str:
        fr = it.get("fraction")
        return f"{int(fr * 100)}%" if fr is not None else "…"

    def _q_detail(self, it: dict) -> str:
        st = it["status"]
        if st == "running":
            return it.get("note") or self.tr("status_connecting")
        if st == "waiting":
            mode = it.get("mode", MODE_VIDEO)
            d = self.tr("mode_video") if mode == MODE_VIDEO else self.tr("mode_audio")
            if mode == MODE_VIDEO and it.get("quality"):
                d += f", {it['quality']}"
            if it.get("browser"):
                d += " (browser)"
            return d
        if st == "done":
            size = f" • {it['size_text']}" if it.get("size_text") else ""
            return f"{it.get('file') or self.tr('status_done')}{size}"
        return it.get("note") or st

    def _refresh_queue_ui(self):
        wait = sum(i["status"] == "waiting" for i in self._queue)
        done = sum(i["status"] == "done" for i in self._queue)
        err = sum(i["status"] in ("error", "cancelled") for i in self._queue)
        self.queue_count_label.configure(
            text=f"{self.tr('active_downloads').upper()} ({len(self._queue)})"
        )
        for w in self.queue_scroll.winfo_children():
            w.destroy()
        self._q_run_widgets = None

        if not self._queue:
            empty = ctk.CTkFrame(self.queue_scroll, fg_color="transparent")
            empty.pack(expand=True, fill="both", pady=48)
            ctk.CTkLabel(empty, text="📥", font=ctk.CTkFont(size=38)).pack(pady=(0, 6))
            ctk.CTkLabel(
                empty, text=self.tr("empty_title"),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("gray30", "gray75"),
            ).pack()
            ctk.CTkLabel(
                empty, text=self.tr("empty_sub"),
                font=ctk.CTkFont(size=11),
                text_color=("gray45", "gray60"),
            ).pack(pady=(3, 0))
            return

        for idx, it in enumerate(self._queue):
            st = it["status"]
            is_sel = (idx == self._q_sel)

            row = ctk.CTkFrame(
                self.queue_scroll, corner_radius=10,
                fg_color=("#ffffff", "#191b26"),
                border_width=1,
                border_color=ACCENT if is_sel else ("#e2e8f0", "#252938"),
            )
            row.pack(fill="x", pady=4, padx=2)
            row.grid_columnconfigure(1, weight=1)

            # Левая колонка: значок / иконка формата
            icon_box = ctk.CTkFrame(
                row, width=48, height=44, corner_radius=8,
                fg_color=("#eff6ff", "#222636"),
            )
            icon_box.grid(row=0, column=0, padx=(10, 8), pady=8)
            icon_box.pack_propagate(False)

            icon_symbol = "🎵" if it.get("mode") == MODE_AUDIO else "🎬"
            if st == "done":
                icon_symbol = "✓"
            elif st in ("error", "cancelled"):
                icon_symbol = "✕"

            ctk.CTkLabel(
                icon_box, text=icon_symbol, font=ctk.CTkFont(size=18),
                text_color=OK_GREEN if st == "done" else (DANGER if st in ("error", "cancelled") else ACCENT),
            ).pack(expand=True)

            # Центральная колонка: название, прогресс-бар, детали
            mid = ctk.CTkFrame(row, fg_color="transparent")
            mid.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=6)
            mid.grid_columnconfigure(0, weight=1)

            title = it.get("file") or it.get("title") or it["url"]
            tl = ctk.CTkLabel(
                mid, text=title[:76], anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            tl.grid(row=0, column=0, sticky="ew")

            widgets = {"title": tl}

            if st == "running":
                bar = ctk.CTkProgressBar(mid, height=5, corner_radius=3, progress_color=ACCENT)
                bar.grid(row=1, column=0, sticky="ew", pady=(3, 2))
                bar.set(it.get("fraction") or 0)
                widgets["bar"] = bar

            detail_text = self._q_detail(it)
            dl = ctk.CTkLabel(
                mid, text=detail_text, anchor="w",
                text_color=OK_GREEN if st == "done" else (DANGER if st in ("error", "cancelled") else ("gray40", "gray60")),
                font=ctk.CTkFont(size=11),
            )
            dl.grid(row=2 if st == "running" else 1, column=0, sticky="ew")
            widgets["detail"] = dl

            # Правая колонка: кнопки действий
            right_box = ctk.CTkFrame(row, fg_color="transparent")
            right_box.grid(row=0, column=2, padx=(0, 10), pady=8)

            if st == "done":
                act_btn = ctk.CTkButton(
                    right_box, text=self.tr("btn_open"), width=74, height=28, corner_radius=6,
                    fg_color=("gray85", "#252a38"), hover_color=("gray75", "#303646"),
                    text_color=("gray20", "gray85"), font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda i=idx: self._q_open(i),
                )
                act_btn.pack(side="left", padx=(0, 4))
                del_btn = ctk.CTkButton(
                    right_box, text="✕", width=26, height=28, corner_radius=6,
                    fg_color=("gray88", "#242835"), hover_color=("gray78", "#303444"),
                    text_color=("gray40", "gray70"), font=ctk.CTkFont(size=11),
                    command=lambda i=idx: (self._queue.pop(i), self._refresh_queue_ui()),
                )
                del_btn.pack(side="left")
            elif st == "running":
                pct_lbl = ctk.CTkLabel(
                    right_box, text=self._q_pct(it), width=48,
                    font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT,
                )
                pct_lbl.pack(side="left", padx=(0, 6))
                widgets["right"] = pct_lbl
                cancel_btn = ctk.CTkButton(
                    right_box, text="✕", width=28, height=28, corner_radius=6,
                    fg_color=("gray85", "#2a2228"), hover_color=("#fecaca", "#451a1a"),
                    text_color=DANGER, font=ctk.CTkFont(size=12, weight="bold"),
                    command=self._q_skip_active,
                )
                cancel_btn.pack(side="left")
            elif st in ("error", "cancelled"):
                retry_btn = ctk.CTkButton(
                    right_box, text=self.tr("btn_retry"), width=76, height=28, corner_radius=6,
                    fg_color=("gray85", "#252a38"), hover_color=("gray75", "#303646"),
                    font=ctk.CTkFont(size=11),
                    command=lambda i=idx: (self._q_select(i), self._q_retry()),
                )
                retry_btn.pack(side="left", padx=(0, 4))
                del_btn = ctk.CTkButton(
                    right_box, text="✕", width=26, height=28, corner_radius=6,
                    fg_color=("gray88", "#242835"), hover_color=("gray78", "#303444"),
                    text_color=("gray40", "gray70"), font=ctk.CTkFont(size=11),
                    command=lambda i=idx: (self._queue.pop(i), self._refresh_queue_ui()),
                )
                del_btn.pack(side="left")
            else:  # waiting
                top_btn = ctk.CTkButton(
                    right_box, text="⚡", width=28, height=28, corner_radius=6,
                    fg_color=("#dbeafe", "#1e293b"), hover_color=("#bfdbfe", "#334155"),
                    text_color=ACCENT, font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda i=idx: self._q_move_top(i),
                )
                top_btn.pack(side="left", padx=(0, 3))
                up_btn = ctk.CTkButton(
                    right_box, text="▲", width=24, height=28, corner_radius=6,
                    fg_color=("gray88", "#222636"), hover_color=("gray78", "#2c3144"),
                    text_color=("gray30", "gray80"), font=ctk.CTkFont(size=9),
                    command=lambda i=idx: self._q_move_up(i),
                )
                up_btn.pack(side="left", padx=(0, 2))
                down_btn = ctk.CTkButton(
                    right_box, text="▼", width=24, height=28, corner_radius=6,
                    fg_color=("gray88", "#222636"), hover_color=("gray78", "#2c3144"),
                    text_color=("gray30", "gray80"), font=ctk.CTkFont(size=9),
                    command=lambda i=idx: self._q_move_down(i),
                )
                down_btn.pack(side="left", padx=(0, 3))
                del_btn = ctk.CTkButton(
                    right_box, text="✕", width=24, height=28, corner_radius=6,
                    fg_color=("gray88", "#242835"), hover_color=("#fecaca", "#3d1f22"),
                    text_color=("gray40", "gray70"), font=ctk.CTkFont(size=11),
                    command=lambda i=idx: (self._queue.pop(i), self._refresh_queue_ui()),
                )
                del_btn.pack(side="left")

            if st == "running":
                self._q_run_widgets = widgets

            for wgt in (row, mid, tl, dl, icon_box):
                wgt.bind("<Button-1>", lambda _e, i=idx: self._q_select(i))
                wgt.bind("<Double-Button-1>", lambda _e, i=idx: self._q_open(i))
                wgt.bind("<Button-3>", lambda e, i=idx: self._q_context_menu(e, i))

    def _q_open(self, idx: int):
        if not (0 <= idx < len(self._queue)):
            return
        it = self._queue[idx]
        if it["status"] == "done" and it.get("file"):
            p = it["outdir"] / it["file"]
            if p.is_file():
                try:
                    os.startfile(str(p))  # noqa: S606 — открываем скачанный файл
                    return
                except Exception as e:
                    self._set_status(f"{self.tr('file_open_err')}{e}", DANGER)
                    return
        self._q_select(idx)

    def _q_copy(self, idx: int):
        if 0 <= idx < len(self._queue):
            self.clipboard_clear()
            self.clipboard_append(self._queue[idx]["url"])
            self._set_status(self.tr("link_copied"))

    def _q_select(self, idx: int):
        self._q_sel = idx
        self._refresh_queue_ui()

    def _q_move_top(self, idx: int):
        if not (0 <= idx < len(self._queue)):
            return
        item = self._queue.pop(idx)
        insert_idx = 1 if (self._queue and self._queue[0]["status"] == "running") else 0
        self._queue.insert(insert_idx, item)
        self._q_sel = insert_idx
        self._refresh_queue_ui()

    def _q_move_up(self, idx: int):
        if not (0 <= idx < len(self._queue)):
            return
        min_idx = 1 if (self._queue and self._queue[0]["status"] == "running") else 0
        if idx > min_idx:
            self._queue[idx], self._queue[idx - 1] = self._queue[idx - 1], self._queue[idx]
            self._q_sel = idx - 1
            self._refresh_queue_ui()

    def _q_move_down(self, idx: int):
        if not (0 <= idx < len(self._queue) - 1):
            return
        self._queue[idx], self._queue[idx + 1] = self._queue[idx + 1], self._queue[idx]
        self._q_sel = idx + 1
        self._refresh_queue_ui()

    def _q_skip_active(self):
        self.cancel_event.set()
        self._set_status(self.tr("status_stopping"))

    def _q_context_menu(self, event, idx: int):
        if not (0 <= idx < len(self._queue)):
            return
        m = tk.Menu(self, tearoff=0)
        it = self._queue[idx]
        st = it["status"]
        if st == "waiting":
            m.add_command(label=self.tr("q_top"), command=lambda: self._q_move_top(idx))
            m.add_command(label=self.tr("q_up"), command=lambda: self._q_move_up(idx))
            m.add_command(label=self.tr("q_down"), command=lambda: self._q_move_down(idx))
            m.add_separator()
        elif st == "running":
            m.add_command(label=self.tr("q_skip"), command=self._q_skip_active)
            m.add_separator()
        elif st in ("error", "cancelled"):
            m.add_command(label=self.tr("btn_retry"), command=lambda: (self._q_select(idx), self._q_retry()))
            m.add_separator()
        elif st == "done":
            m.add_command(label=self.tr("btn_open"), command=lambda: self._q_open(idx))
            m.add_separator()
        m.add_command(label=self.tr("copy_link"), command=lambda: self._q_copy(idx))
        if st != "running":
            m.add_command(label=self.tr("q_delete"), command=lambda: (self._queue.pop(idx), self._refresh_queue_ui()))
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _q_remove(self):
        if 0 <= self._q_sel < len(self._queue) and self._queue[self._q_sel]["status"] == "waiting":
            self._queue.pop(self._q_sel)
            self._q_sel = -1
            self._refresh_queue_ui()

    def _q_retry(self):
        if 0 <= self._q_sel < len(self._queue) and \
                self._queue[self._q_sel]["status"] in ("error", "cancelled"):
            self._queue[self._q_sel]["status"] = "waiting"
            self._queue[self._q_sel]["note"] = ""
            self._refresh_queue_ui()
            self._ensure_worker()

    def _q_clear_done(self):
        self._queue = [i for i in self._queue if i["status"] in ("waiting", "running")]
        self._q_sel = -1
        self._refresh_queue_ui()

    def _q_clear_all(self):
        self._queue = [i for i in self._queue if i["status"] == "running"]
        self._q_sel = -1
        self._refresh_queue_ui()

    def _poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    if payload["fraction"] is not None:
                        self.progress.set(payload["fraction"])
                    self.progress_label.configure(text=payload["text"])
                    if self._current is not None:
                        cur = self._current
                        cur["note"] = payload["text"]
                        cur["fraction"] = payload["fraction"]
                        if payload.get("file"):
                            cur["file"] = payload["file"]
                        w = self._q_run_widgets
                        if w:
                            if payload["fraction"] is not None:
                                w["bar"].set(payload["fraction"])
                                w["right"].configure(text=f"{int(payload['fraction'] * 100)}%")
                            w["detail"].configure(text=payload["text"])
                            if payload.get("file"):
                                w["title"].configure(text=f"▶ {payload['file'][:88]}")
                elif kind == "item_start":
                    self._current = payload["item"]
                    self._on_item_start(payload["item"], payload["i"], payload["n"])
                elif kind == "item_result":
                    it = payload["item"]
                    it["status"] = {"finished_ok": "done", "error": "error",
                                    "cancelled": "cancelled"}.get(payload["result"], "error")
                    it["note"] = payload["note"][:60] if payload["result"] == "error" else ""
                    if it["status"] == "done" and it.get("file"):
                        try:
                            it["size_text"] = human_size(
                                (it["outdir"] / it["file"]).stat().st_size)
                        except Exception:
                            pass
                    self._current = None
                    self._refresh_queue_ui()
                elif kind == "file_downloaded":
                    self._log(f"✓ {self.tr('log_received')}: {payload}")
                    if self._current is not None:
                        self._current["file"] = payload
                elif kind == "status":
                    self._set_status(payload)
                elif kind == "analysis":
                    self._apply_analysis(payload["url"], payload.get("meta") or {"heights": payload.get("heights")})
                elif kind == "finished_ok":
                    self._log(self.tr("status_download_complete"))
                    self._notify(APP_NAME, self.tr("status_download_done"))
                elif kind == "ffmpeg_installed":
                    self._ff_busy = False
                    self._show_ffmpeg_state()
                    self._finish(True, self.tr("ffmpeg_installed"))
                    self._log(f"✔ {self.tr('ffmpeg_installed')}")
                elif kind == "error":
                    if self._ff_busy:
                        self._ff_busy = False
                    self._log(f"✗ {self.tr('log_error')}: {payload}")
                    if not self._worker_alive:
                        self._finish(False, self.tr("status_error"))
                    if not find_ffmpeg_dir():
                        self.ffmpeg_button.configure(state="normal")
                    if "403" in str(payload) or "CDN" in str(payload):
                        self._log(f"! {cdn_block_hint()}")
                        self._set_status(self.tr("cdn_geo_blocked"), DANGER)
                    self._refresh_queue_ui()
                elif kind == "cancelled":
                    if self._ff_busy:
                        self._ff_busy = False
                    if not self._worker_alive:
                        self._finish(False, self.tr("status_cancelled"))
                    self._log(f"— {self.tr('status_cancelled')}")
                    if not find_ffmpeg_dir():
                        self.ffmpeg_button.configure(state="normal")
                elif kind == "queue_idle":
                    self._current = None
                    self._refresh_queue_ui()
                    if any(i["status"] == "error" for i in self._queue):
                        self._finish(False, self.tr("status_queue_errors"))
                        self._notify(APP_NAME, self.tr("status_queue_errors"))
                    elif any(i["status"] == "cancelled" for i in self._queue):
                        self._finish(False, self.tr("status_cancelled"))
                    else:
                        self._finish(True, self.tr("status_done_check"))
                        self._notify(APP_NAME, self.tr("all_done_notice"))
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _on_close(self):
        if self._busy and getattr(self, "_tray", None) is not None:
            self.withdraw()
            self._notify(APP_NAME, self.tr("tray_bg_notice"))
            return
        self._force_exit()

    def _force_exit(self):
        save_config(self.cfg)
        self.cancel_event.set()
        if getattr(self, "_tray", None) is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.destroy()


def main():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    try:
        App().mainloop()
    except Exception:
        # без консоли исключение иначе пропало бы молча
        import traceback
        log = data_dir() / "crash.log"
        try:
            log.write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            pass
        try:
            from tkinter import messagebox
            messagebox.showerror(APP_NAME, f"{tr_global('unexpected_error')}\n{log}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
