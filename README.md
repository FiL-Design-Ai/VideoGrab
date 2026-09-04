# ⬇ VideoGrab PRO (v1.0.0)

**VideoGrab** is a modern, lightweight, and powerful GUI video & audio downloader for Windows built with Python, CustomTkinter, and yt-dlp.

[**English**](#english) | [**Русский**](#русский)

---

## English

### ✨ Key Features

- 🌐 **Multilingual Interface**: Full localization for **English (default)**, **Русский (Russian)**, and **中文 (Simplified Chinese)** with instant switching in settings.
- ⚡ **Priority Queue Management**:
  - **⚡ Priority / Download next**: Instantly move any item to the top of the pending queue.
  - **▲ / ▼ Reorder**: Fine-grained position adjustments.
  - **Context Menu**: Right-click on any queue item for quick actions (Priority, Move up/down, Copy link, Retry, Remove).
  - **Real-time Progress Streaming**: Live download speeds, downloaded size, percentage, and ETA calculations without UI freezing.
- 🎬 **Hero Metadata Preview**: Automatically detects video title, poster thumbnail, and available resolutions (1080p, 720p, 480p, etc.) upon link insertion.
- 🚀 **Dual Download Engine**:
  - **yt-dlp Engine**: Supports 1000+ sites (YouTube, VK, Rutube, Vimeo, Twitter/X, TikTok, and direct MP4/M3U8 streams).
  - **Direct Playerjs Engine**: High-speed direct downloading for Playerjs-based streaming platforms (e.g. KVS engines) without unnecessary transcoding.
- 🛡 **CDP Browser Mode**: Built-in headless Chrome/Edge integration to bypass Cloudflare/CDN bot protections by replaying genuine human actions and capturing direct media streams.
- 🎵 **Audio Extraction**: Single-click audio extraction directly to high-quality MP3 (192 kbps).
- ⚙ **Proxy & Geo-block Bypass**: Built-in HTTP & SOCKS5 proxy support to seamlessly bypass regional CDN restrictions.
- 🔔 **System Tray & Notifications**: Minimize to system tray near the clock, Windows Toast notifications upon completion, and background task processing.
- 📦 **Automated FFmpeg Setup**: Detects system FFmpeg or downloads official static binaries with 1 click.

### 📥 Running from Source

`powershell
# 1. Clone the repository
git clone https://github.com/FiL-Design-Ai/VideoGrab.git
cd VideoGrab

# 2. Set up virtual environment
python -m venv .venv
.venv\Scriptsctivate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch application
python app.py
`

### 🔨 Building Portable Executable (.exe)

`powershell
build.bat
`
The compiled, standalone portable folder is generated under dist\VideoGrab\VideoGrab.exe.

---

## Русский

### ✨ Основные возможности

- 🌐 **Мультиязычный интерфейс**: Полная локализация на **English (по умолчанию)**, **Русский** и **中文 (китайский)** с мгновенным переключением в Настройках.
- ⚡ **Управление приоритетом очереди**:
  - **⚡ Качать первым**: Мгновенный подъем выбранного видео в начало списка ожидания.
  - **▲ / ▼ Перемещение**: Точная настройка порядка загрузки.
  - **Контекстное меню**: Правый клик по элементу открывает меню (Качать первым, Поднять/Опустить, Копировать ссылку, Повторить, Удалить).
  - **Прямой стриминг прогресса**: Реальное отображение скорости (МБ/с), размера, процентов и оставшегося времени без задержек и зависаний.
- 🎬 **Hero-превью и метаданные**: Автоматическое определение названия ролика, обложки и списка доступных качеств (1080p, 720p, 480p и т.д.) при вставке ссылки.
- 🚀 **Гибридный движок загрузки**:
  - **Движок yt-dlp**: Поддержка 1000+ сайтов (YouTube, VK, Rutube, TikTok, Twitter и прямые mp4/hls потоки).
  - **Прямой Playerjs-движок**: Прямой перехват и скоростное скачивание видео с плееров Playerjs/KVS без лишней перекодировки.
- 🛡 **Режим «Через браузер» (CDP)**: Автоматический запуск реального Chrome/Edge для сайтов с жесткой защитой от ботов (CDN77/Cloudflare) — перехват медиа-потока прямо из плеера.
- 🎵 **Конвертация в аудио**: Быстрое извлечение чистой звуковой дорожки в MP3 (192 kbps).
- ⚙ **Поддержка Прокси**: Встроенная поддержка HTTP и SOCKS5 прокси для обхода геоблокировок CDN.
- 🔔 **Системный трей и уведомления**: Сворачивание в трей возле часов, фоновая работа, звуковые сигналы и Windows Toast-уведомления.
- 📦 **Удобный FFmpeg**: Автопоиск системного ffmpeg или скачивание официального статического архива в один клик.

### 📄 Лицензия и правовая информация
Программа создана для загрузки общедоступного контента и личных архивов в соответствии с законодательством. Уважайте авторские права создателей контента.
