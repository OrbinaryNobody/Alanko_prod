# Инструкция по использованию внешних URL для MinIO

## Описание

Этот проект настроен так, чтобы файлы в MinIO были доступны как из backend сервиса, так и из браузера. Используется разделение на:
- **Внутренний адрес** (MINIO_INTERNAL_URL): используется backend для загрузки файлов в MinIO
- **Публичный адрес** (MINIO_PUBLIC_URL): используется для генерации ссылок, которые отправляются в браузер

## Структура MinIO

В MinIO создаются 6 отдельных bucket'ов:
- `alanko-news` - публичные изображения опубликованных новостей
- `alanko-student-photos` - публичные фотографии студентов для главной страницы
- `alanko-achievement-videos` - публичные видео достижений
- `alanko-videos` - приватные видео ответов учеников на задания
- `alanko-certificates` - приватные сертификаты и achievement-файлы
- `alanko-documents` - приватные документы сайта

Публичными являются только `alanko-news`, `alanko-student-photos` и `alanko-achievement-videos`. Нельзя делать `alanko-videos` публичным, потому что в нем находятся учебные видео учеников.

## Локальная разработка

1. Убедиться, что в `.env` файле установлено:
```
MINIO_INTERNAL_URL=minio:9000
MINIO_PUBLIC_URL=http://localhost:9000
```

2. Запустить docker-compose:
```bash
docker-compose up -d
```

3. MinIO будет доступен в браузере по адресу:
```
http://localhost:9001  # консоль MinIO
http://localhost:9000  # API MinIO
```

## Развертывание на VPS

Для развертывания на сервере нужно обновить `.env`:

```
MINIO_INTERNAL_URL=minio:9000  # остается тем же (используется backend)
MINIO_PUBLIC_URL=http://your-domain.com:9000  # изменить на реальный домен или IP
```

Например:
```
MINIO_PUBLIC_URL=http://185.123.456.789:9000
# или
MINIO_PUBLIC_URL=http://api.example.com:9000
```

Убедиться, что в docker-compose проброшены порты (по умолчанию уже проброшены):
```yaml
ports:
  - "9000:9000"  # MinIO API
  - "9001:9001"  # MinIO Console
```

## Как это работает

1. Файл загружается в MinIO через backend.
2. Для public bucket клиент получает URL через `MINIO_PUBLIC_URL`.
3. Для private bucket backend выдает временный presigned URL.

Пример ответа API:
```json
{
  "file": "http://localhost:9000/alanko-certificates/uuid-filename.pdf?token=..."
}
```

## Миграция старых achievement-видео

Если achievement-видео раньше загружались в `alanko-videos`, сначала выполните проверку:

```bash
python scripts/migrate_achievement_videos.py --dry-run
```

После проверки выполните перенос:

```bash
python scripts/migrate_achievement_videos.py
```

После миграции проверьте, что achievement objects находятся в `alanko-achievement-videos`, а task videos остались в приватном `alanko-videos`.

При развертывании на VPS эта ссылка будет:
```json
{
  "file": "http://your-domain.com:9000/alanko-certificates/uuid-filename.pdf?token=..."
}
```
