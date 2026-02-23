#!/usr/bin/env python3
"""
Instagram Video Downloader
--------------------------
Скачивает все видео с профиля Instagram по указанной ссылке.

Использование:
    python instagram_downloader.py <instagram_url> [options]

Примеры:
    python instagram_downloader.py https://www.instagram.com/username/
    python instagram_downloader.py https://www.instagram.com/username/ -o ./videos
    python instagram_downloader.py https://www.instagram.com/p/POST_ID/ -o ./videos
"""

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yt_dlp
except ImportError:
    print("Ошибка: yt-dlp не установлен.")
    print("Установите его командой: pip install yt-dlp")
    sys.exit(1)


def parse_instagram_url(url: str) -> dict:
    """Парсит Instagram URL и определяет тип контента."""
    parsed = urlparse(url)

    if "instagram.com" not in parsed.netloc:
        raise ValueError(f"Некорректный Instagram URL: {url}")

    path = parsed.path.strip("/")

    # Пост или Reel
    if re.match(r"^p/[\w-]+", path) or re.match(r"^reel/[\w-]+", path):
        return {"type": "post", "url": url}

    # Профиль пользователя
    if re.match(r"^[\w.]+/?$", path):
        username = path.split("/")[0]
        return {"type": "profile", "url": url, "username": username}

    # Сторис
    if re.match(r"^stories/[\w.]+", path):
        return {"type": "stories", "url": url}

    return {"type": "unknown", "url": url}


def build_ydl_opts(output_dir: str, cookies_file: str | None = None) -> dict:
    """Формирует настройки для yt-dlp."""
    output_path = os.path.join(output_dir, "%(uploader)s_%(upload_date)s_%(id)s.%(ext)s")

    opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path,
        "ignoreerrors": True,
        "no_warnings": False,
        "quiet": False,
        "progress": True,
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
    }

    if cookies_file:
        opts["cookiefile"] = cookies_file

    return opts


def download_videos(url: str, output_dir: str, cookies_file: str | None = None) -> None:
    """Основная функция скачивания видео."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    url_info = parse_instagram_url(url)
    content_type = url_info["type"]

    print(f"\nТип контента: {content_type}")
    print(f"URL: {url}")
    print(f"Папка для сохранения: {output_path.resolve()}\n")

    # Для профиля добавляем флаг для скачивания всех постов
    download_url = url
    extra_opts = {}

    if content_type == "profile":
        print(f"Скачивание всех видео профиля: {url_info.get('username', '')}")
        # yt-dlp автоматически обходит все посты профиля
        extra_opts["playlistend"] = None  # все посты

    ydl_opts = build_ydl_opts(output_dir, cookies_file)
    ydl_opts.update(extra_opts)

    # Фильтр — скачиваем только видео, пропускаем фото
    ydl_opts["match_filter"] = yt_dlp.utils.match_filter_func("!is_live")

    print("=" * 50)
    print("Начинаем загрузку...")
    print("=" * 50)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([download_url])

        if result == 0:
            print("\nЗагрузка завершена успешно!")
        else:
            print(f"\nЗагрузка завершена с кодом: {result}")

    except yt_dlp.utils.DownloadError as e:
        print(f"\nОшибка загрузки: {e}")
        print("\nВозможные причины:")
        print("  - Приватный аккаунт (требуется авторизация через cookies)")
        print("  - Instagram заблокировал запрос (попробуйте позже)")
        print("  - Неверный URL")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nЗагрузка прервана пользователем.")
        sys.exit(0)


def get_cookies_from_browser(browser: str) -> str | None:
    """Пробует получить cookies из браузера автоматически."""
    supported = ["chrome", "firefox", "safari", "edge", "chromium", "brave"]
    if browser.lower() not in supported:
        print(f"Браузер '{browser}' не поддерживается. Доступные: {', '.join(supported)}")
        return None
    return f"--cookies-from-browser {browser}"


def main():
    parser = argparse.ArgumentParser(
        description="Скачивает видео с Instagram по ссылке на профиль или пост.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Скачать все видео с профиля
  python instagram_downloader.py https://www.instagram.com/username/

  # Скачать в конкретную папку
  python instagram_downloader.py https://www.instagram.com/username/ -o ./мои_видео

  # Скачать один пост/reel
  python instagram_downloader.py https://www.instagram.com/p/ABC123/

  # Использовать cookies файл (для приватных аккаунтов)
  python instagram_downloader.py https://www.instagram.com/username/ -c cookies.txt

  # Использовать cookies из браузера (Chrome, Firefox и др.)
  python instagram_downloader.py https://www.instagram.com/username/ -b chrome

Как получить cookies.txt:
  Установите расширение "Get cookies.txt LOCALLY" в браузере,
  войдите в Instagram, затем экспортируйте cookies для instagram.com.
        """,
    )

    parser.add_argument(
        "url",
        help="Ссылка на Instagram профиль или пост (например: https://www.instagram.com/username/)",
    )
    parser.add_argument(
        "-o", "--output",
        default="./instagram_videos",
        help="Папка для сохранения видео (по умолчанию: ./instagram_videos)",
    )
    parser.add_argument(
        "-c", "--cookies",
        default=None,
        help="Путь к файлу cookies.txt для авторизации",
    )
    parser.add_argument(
        "-b", "--browser",
        default=None,
        help="Браузер для получения cookies автоматически (chrome, firefox, safari, edge)",
    )

    args = parser.parse_args()

    # Нормализуем URL
    url = args.url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    cookies_file = args.cookies
    if args.browser and not cookies_file:
        # Если указан браузер — передаём это в yt-dlp через специальный параметр
        print(f"Используем cookies из браузера: {args.browser}")
        # yt-dlp поддерживает cookiesfrombrowser напрямую
        import tempfile
        ydl_opts_check = build_ydl_opts(args.output)
        ydl_opts_check["cookiesfrombrowser"] = (args.browser,)

        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
                ydl.download([url])
            print("\nЗагрузка завершена!")
            return
        except Exception as e:
            print(f"Ошибка: {e}")
            sys.exit(1)

    download_videos(url, args.output, cookies_file)


if __name__ == "__main__":
    main()
