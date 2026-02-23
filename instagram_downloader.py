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
import http.cookiejar
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import instaloader
except ImportError:
    print("Ошибка: instaloader не установлен.")
    print("Установите его командой: pip install instaloader")
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


def load_cookies_from_file(cookies_file: str) -> dict:
    """Загружает cookies из Netscape-формата cookies.txt."""
    jar = http.cookiejar.MozillaCookieJar()
    try:
        jar.load(cookies_file, ignore_discard=True, ignore_expires=True)
    except Exception as e:
        print(f"Ошибка чтения cookies.txt: {e}")
        sys.exit(1)
    cookies = {c.name: c.value for c in jar if "instagram.com" in c.domain}
    if not cookies:
        print("Предупреждение: в cookies.txt не найдены cookies для instagram.com")
    return cookies


def build_instaloader(output_dir: str, cookies: dict | None = None) -> instaloader.Instaloader:
    """Создаёт и настраивает экземпляр Instaloader."""
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern="",
        dirname_pattern=output_dir,
        filename_pattern="{owner_username}_{date_utc:%Y%m%d}_{mediaid}",
    )
    if cookies:
        L.context._session.cookies.update(cookies)
    return L


def download_videos(url: str, output_dir: str, cookies_file: str | None = None) -> None:
    """Основная функция скачивания видео."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    url_info = parse_instagram_url(url)
    content_type = url_info["type"]

    print(f"\nТип контента: {content_type}")
    print(f"URL: {url}")
    print(f"Папка для сохранения: {output_path.resolve()}\n")

    cookies = None
    if cookies_file:
        cookies = load_cookies_from_file(cookies_file)

    L = build_instaloader(str(output_path), cookies)

    print("=" * 50)
    print("Начинаем загрузку...")
    print("=" * 50)

    try:
        if content_type == "profile":
            username = url_info["username"]
            print(f"Скачивание всех видео профиля: {username}")
            profile = instaloader.Profile.from_username(L.context, username)
            count = 0
            for post in profile.get_posts():
                if post.is_video:
                    L.download_post(post, target=output_path)
                    count += 1
            print(f"\nЗагрузка завершена! Скачано видео: {count}")

        elif content_type == "post":
            match = re.search(r"/(p|reel)/([A-Za-z0-9_-]+)", url)
            if not match:
                print("Ошибка: не удалось извлечь shortcode из URL")
                sys.exit(1)
            shortcode = match.group(2)
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            if not post.is_video:
                print("Это фото, не видео. Скачивание пропущено.")
                return
            L.download_post(post, target=output_path)
            print("\nЗагрузка завершена!")

        elif content_type == "stories":
            match = re.search(r"/stories/([\w.]+)", url)
            if not match:
                print("Ошибка: не удалось извлечь имя пользователя из URL сторис")
                sys.exit(1)
            stories_user = match.group(1)
            profile = instaloader.Profile.from_username(L.context, stories_user)
            L.download_stories(userids=[profile.userid], filename_target=output_path)
            print("\nЗагрузка завершена!")

        else:
            print(f"Неизвестный тип URL: {url}")
            sys.exit(1)

    except instaloader.exceptions.ProfileNotExistsException:
        print("\nОшибка: профиль не найден или аккаунт удалён")
        sys.exit(1)
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        print("\nОшибка: приватный аккаунт. Войдите в Instagram и экспортируйте cookies.")
        print("  1. Установите расширение 'Get cookies.txt LOCALLY'")
        print("  2. Откройте instagram.com, нажмите Export")
        print("  3. Запустите: python instagram_downloader.py <url> -c cookies.txt")
        sys.exit(1)
    except instaloader.exceptions.LoginRequiredException:
        print("\nОшибка: требуется авторизация. Используйте -c cookies.txt")
        sys.exit(1)
    except instaloader.exceptions.ConnectionException as e:
        print(f"\nОшибка соединения: {e}")
        print("Instagram мог заблокировать запрос. Попробуйте позже.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nЗагрузка прервана пользователем.")
        sys.exit(0)


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
        help="(Устарело) Используйте -c cookies.txt вместо этого флага",
    )

    args = parser.parse_args()

    # Нормализуем URL
    url = args.url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    if args.browser and not args.cookies:
        print(f"Автоматическое получение cookies из '{args.browser}' не поддерживается.")
        print("\nЭкспортируйте cookies вручную:")
        print("  1. Установите расширение 'Get cookies.txt LOCALLY' в браузере")
        print("     Opera: Меню → Расширения → Магазин Chrome → найдите расширение")
        print("  2. Войдите в Instagram, откройте instagram.com")
        print("  3. Нажмите на иконку расширения → Export → сохраните как cookies.txt")
        print("  4. Запустите: python instagram_downloader.py <url> -c cookies.txt")
        sys.exit(0)

    download_videos(url, args.output, args.cookies)


if __name__ == "__main__":
    main()
