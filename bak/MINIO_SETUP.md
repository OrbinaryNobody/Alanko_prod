# Инструкция по использованию внешних URL для MinIO

## Описание

Этот проект настроен так, чтобы файлы в MinIO были доступны как из backend сервиса, так и из браузера. Используется разделение на:
- **Внутренний адрес** (MINIO_INTERNAL_URL): используется backend для загрузки файлов в MinIO
- **Публичный адрес** (MINIO_PUBLIC_URL): используется для генерации ссылок, которые отправляются в браузер

## Структура MinIO

В MinIO создаются 4 отдельных bucket'а:
- `alanko-videos` - видео от учителей
- `alanko-certificates` - сертификаты достижений  
- `alanko-student-photos` - фото студентов
- `alanko-documents` - документы сайта

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

1. Файл загружается в MinIO через backend
2. FileService генерирует presigned URL с использованием внутреннего адреса (`minio:9000`)
3. Адрес автоматически заменяется на публичный URL из переменной `MINIO_PUBLIC_URL`
4. Клиент получает в ответе публичный URL, который работает в браузере

Пример ответа API:
```json
{
  "file": "http://localhost:9000/alanko-certificates/uuid-filename.pdf?token=..."
}
```

При развертывании на VPS эта ссылка будет:
```json
{
  "file": "http://your-domain.com:9000/alanko-certificates/uuid-filename.pdf?token=..."
}
```
