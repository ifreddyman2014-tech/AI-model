# Instagram Video Downloader

Скрипт для скачивания всех видео с Instagram профиля или отдельного поста/рила.

## Установка

```bash
pip install -r requirements.txt
```

> **Опционально:** Для конвертации видео установите [FFmpeg](https://ffmpeg.org/download.html)

## Использование

### Скачать все видео с профиля
```bash
python instagram_downloader.py https://www.instagram.com/username/
```

### Скачать видео в конкретную папку
```bash
python instagram_downloader.py https://www.instagram.com/username/ -o ./мои_видео
```

### Скачать один пост или Reel
```bash
python instagram_downloader.py https://www.instagram.com/p/POST_ID/
python instagram_downloader.py https://www.instagram.com/reel/REEL_ID/
```

### Приватные аккаунты — через файл cookies
```bash
python instagram_downloader.py https://www.instagram.com/username/ -c cookies.txt
```

### Приватные аккаунты — через браузер
```bash
python instagram_downloader.py https://www.instagram.com/username/ -b chrome
python instagram_downloader.py https://www.instagram.com/username/ -b firefox
```

## Параметры

| Параметр | Описание |
|----------|----------|
| `url` | Ссылка на профиль или пост Instagram |
| `-o`, `--output` | Папка для сохранения (по умолчанию: `./instagram_videos`) |
| `-c`, `--cookies` | Путь к файлу `cookies.txt` |
| `-b`, `--browser` | Браузер для автоматического получения cookies (`chrome`, `firefox`, `safari`, `edge`) |

## Как получить cookies.txt

Если аккаунт приватный или Instagram требует авторизацию:

1. Установите расширение **"Get cookies.txt LOCALLY"** в Chrome или Firefox
2. Войдите в свой аккаунт Instagram в браузере
3. Откройте `instagram.com` и нажмите на иконку расширения
4. Экспортируйте cookies в файл `cookies.txt`
5. Используйте флаг `-c cookies.txt`

## Примечания

- Скрипт скачивает только видео (фотографии пропускаются)
- Instagram может временно блокировать запросы — подождите и попробуйте снова
- Видео сохраняются в формате MP4 с именем `username_дата_id.mp4`
- Скачивание контента возможно только при наличии прав на его просмотр
