# Актуальный аудит backend Alanko

Дата: 2026-08-26

## Область

Проверены безопасность, надежность, эффективность, масштабируемость и скорость ответа текущего backend в `bak/app`. Онлайн-оплата исключена. В документе оставлены только актуальные открытые проблемы.

# 1. Безопасность

## P0-1. Любой сайт может обращаться к API

Файл: [bak/app/main.py](bak/app/main.py#L53-L55)

Используются `allow_origins=["*"]`, `allow_origin_regex=r".*"` и `allow_credentials=True`. Браузерный сайт с любого домена может пытаться отправлять запросы к API от имени пользователя, который уже вошел в систему.

Опасные последствия: вредоносная страница может попытаться создать пользователя, изменить группу, оценку, attendance или загрузить файл с пользовательской авторизацией.

**Исправление:** оставить только явный allowlist frontend-доменов, убрать regex `.*`, ограничить methods и headers, добавить CORS integration tests.

## P0-2. Фиксированный admin bootstrap и fallback-секреты

Файлы: [bak/app/db/init_db.py](bak/app/db/init_db.py), [bak/app/core/config.py](bak/app/core/config.py#L25-L34)

Нужно проверить текущий bootstrap: автоматическое создание admin с известным паролем и fallback-значения для JWT/MinIO недопустимы для production. На чистой БД фиксированный admin превращается в готовый административный вход.

**Исправление:** создавать admin отдельной одноразовой командой, убрать фиксированный пароль, сделать production secrets обязательными и ротировать уже раскрытые credentials.

## P1-1. JWT доверяет устаревшим claims

Файлы: [bak/app/shared/access/access_service.py](bak/app/shared/access/access_service.py#L8-L24), [bak/app/core/permissions.py](bak/app/core/permissions.py#L41-L58)

`AccessContext` строится из token claims, а существование и актуальность пользователя в БД не проверяются. После удаления пользователя или снятия роли старый токен продолжит работать до истечения срока.

**Исправление:** короткий access token, refresh/revocation, token version или проверка active user в БД; для admin actions проверять актуальные права.

## P1-2. Student task dashboard может раскрывать чужие данные

Файлы: [bak/app/education/api/students.py](bak/app/education/api/students.py#L116-L120), [bak/app/education/facade.py](bak/app/education/facade.py#L206-L208), [bak/app/education/services/student_service.py](bak/app/education/services/student_service.py#L206-L210)

Endpoint получает широкое `VIEW_STUDENTS`, а service формирует задания всех студентов. Нужно проверить, что teacher видит только разрешенные группы, а student только себя. Сейчас `ctx` в этом пути может теряться.

**Исправление:** передать context до service, применить group policy и разделить student/teacher/admin DTO.

## P1-3. MIME загрузки доверяется клиенту

Файл: [bak/app/infrastructure/storage/file_service.py](bak/app/infrastructure/storage/file_service.py#L119-L124)

Проверяется только `UploadFile.content_type`. Клиент может назвать любой файл изображением или видео.

**Исправление:** проверять magic bytes, декодировать изображения безопасной библиотекой, ограничивать dimensions/duration видео, сканировать документы и хранить uploads вне executable paths.

## P1-4. Orphan objects в MinIO после ошибки БД

Файлы: [bak/app/education/api/students.py](bak/app/education/api/students.py#L38-L48), [bak/app/infrastructure/storage/file_service.py](bak/app/infrastructure/storage/file_service.py#L137-L151)

Object сначала загружается в MinIO, затем создается запись БД. Ошибка БД оставляет файл без ссылки.

**Исправление:** cleanup object key при rollback, pending upload state, retry/reconciliation job и тест отказа БД после успешного upload.

## P1-5. Public leaderboard раскрывает больше данных, чем необходимо

Файл: [bak/app/public/services/public_service.py](bak/app/public/services/public_service.py#L31-L40)

Гостям возвращаются имя, рейтинг, фото, роль и description. `getattr(profile, ...)` может случайно выдать внутреннее поле, если модель изменится.

**Исправление:** минимальный whitelist public DTO, отдельный consent/public flag и явные поля вместо `getattr`.

## P1-6. Нет rate limit входа

Файл: [bak/app/accounts/api/auth.py](bak/app/accounts/api/auth.py#L22)

`/login` не ограничивает число попыток. Rate limit по IP будет добавлен на NGINX, но нужен также лимит по email, потому что распределенная атака может идти с разных IP.

**Исправление:** NGINX limit по IP, application-level backoff по email, одинаковый ответ для неизвестного email и неверного пароля, MFA для admin.

# 2. Надежность и данные

## P1-7. MinIO startup errors всё еще могут скрываться

Файлы: [bak/app/infrastructure/storage/file_service.py](bak/app/infrastructure/storage/file_service.py#L14-L20), [bak/app/infrastructure/storage/file_service.py](bak/app/infrastructure/storage/file_service.py#L42-L61), [bak/app/core/minio_init.py](bak/app/core/minio_init.py#L4-L15)

Если bucket не создался или policy не установилась, storage service пишет warning и может продолжить. Нужно убедиться, что новый `backend-init` трактует такую ошибку как failure и не запускает backend.

**Исправление:** исключения provisioning не проглатывать, init job должен иметь ненулевой exit code, readiness должен отдельно проверять MinIO.

## P1-8. Конкурентное создание пересекающихся consultation slots

Файлы: [bak/app/consultations/services/slot_service.py](bak/app/consultations/services/slot_service.py#L29-L36), [bak/app/consultations/repositories/slot_repository.py](bak/app/consultations/repositories/slot_repository.py#L20-L29)

Сервис сначала читает существующие слоты, потом вставляет новый. Два параллельных запроса могут оба пройти проверку и создать overlap.

**Исправление:** PostgreSQL exclusion constraint или блокировка календарного ресурса и concurrency test.

## P1-9. Два SQLAlchemy engine/session factory

Файлы: [bak/app/db/database.py](bak/app/db/database.py#L7-L15), [bak/app/db/session.py](bak/app/db/session.py#L7-L15)

Два модуля создают свои engine. Сейчас используется один путь, но второй легко будет использован новым кодом с другими pool settings.

**Исправление:** оставить один engine/session factory, настроить `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`, `pool_pre_ping`.

## P1-10. News/achievement/storage операции неатомарны между БД и MinIO

Файлы: [bak/app/news/services.py](bak/app/news/services.py#L38-L80), [bak/app/achievements/services/achievement_service.py](bak/app/achievements/services/achievement_service.py#L129-L230)

Транзакция PostgreSQL не может откатить уже выполненную операцию MinIO. При ошибке commit или следующем шаге появится orphan object.

**Исправление:** compensation cleanup, object lifecycle table или reconciliation job; старый файл удалять только после успешного commit.

# 3. Эффективность и скорость ответа

## P2-1. Consultation availability выполняет N+1 и не ограничивает диапазон

Файл: [bak/app/consultations/services/availability_service.py](bak/app/consultations/services/availability_service.py#L16-L26)

Сначала выбираются все дни, затем отдельным запросом слоты для каждого дня. API может принять широкий диапазон дат.

Для пользователя это означает непредсказуемую задержку: чем больше диапазон, тем больше SQL-запросов и размер ответа.

**Исправление:** один query с join по дням и слотам, максимальный диапазон дат, limit/offset и индексы `day_id/start_at/status`.

## P2-2. Student list делает N+1/N+M

Файлы: [bak/app/education/services/student_service.py](bak/app/education/services/student_service.py#L120-L160), [bak/app/attendance/facade.py](bak/app/attendance/facade.py#L13-L19)

Для каждой страницы студентов отдельно запрашиваются группы, родитель, subscription и attendance.

При 200 студентах один HTTP-запрос может породить сотни SQL-запросов. Это напрямую увеличивает p95/p99 времени ответа.

**Исправление:** batch queries по student IDs, `selectinload`, агрегированные subscription/attendance запросы и один проход построения DTO.

## P2-3. Некоторые коллекции всё еще не ограничены

Открытые `.all()` остаются в achievements, participants, invitations, notifications, education repositories и dashboard repositories.

Даже если сегодня данных мало, response и RAM будут расти вместе с количеством пользователей и истории.

**Исправление:** для каждого внешнего списка обязательные limit/offset или cursor pagination с максимальным limit; внутренние unlimited queries оставить только для доказанно маленьких справочников.

## P2-4. Student task dashboard тяжелый

Файлы: [bak/app/education/services/student_service.py](bak/app/education/services/student_service.py#L206-L300), [bak/app/education/repositories/student_repository.py](bak/app/education/repositories/student_repository.py#L20-L30)

Даже если список ограничен, в ответе на каждого ученика могут попасть категории, задания, видео, фотографии и другие поля. Сериализация большого JSON добавляет время после завершения SQL.

**Исправление:** отдельные endpoints list/detail, минимальный list DTO, lazy загрузка task media по запросу и лимит media на task.

# 4. Масштабируемость

## M1. Один worker и bind mount остаются development-конфигурацией

Файлы: [bak/Dockerfile](bak/Dockerfile#L1-L11), [bak/docker-compose.yml](bak/docker-compose.yml#L20-L40)

Один worker ограничивает параллельность, а `./app:/app` позволяет менять код вне immutable image.

**Исправление:** production image без bind mount, non-root user, reverse proxy/TLS, несколько workers/replicas, graceful shutdown и resource limits.

## M2. MinIO/PostgreSQL используют одиночные локальные volumes

Повреждение host или volume делает данные недоступными.

**Исправление:** backup/restore drills, snapshots, replica/managed storage и регулярная проверка восстановления.

## M3. Зависимости не закреплены

Файл: [bak/requirements.txt](bak/requirements.txt#L1-L12)

Большинство пакетов устанавливается без версий. Повторная сборка может получить другое поведение или уязвимую транзитивную зависимость.

**Исправление:** constraints/lock file, CI build, SBOM и `pip-audit`.

## M4. Наблюдаемость недостаточна

Нет стабильного request ID, structured logs, p50/p95/p99 latency, DB pool metrics, tracing и alerts.

**Исправление:** request ID, metrics по endpoint, безопасный SQL timing, error tracking и dashboards.

# 5. Скорость ответа: контрольные цели

Для основных endpoint’ов нужно измерять:

- `p50`: обычный ответ;
- `p95`: ответ для 95% запросов;
- `p99`: редкие тяжелые ответы;
- число SQL-запросов на request;
- размер JSON;
- время ожидания DB pool;
- время генерации presigned URL;
- время upload и ожидания threadpool.

Минимальные сценарии нагрузки:

1. student list: 100 и 200 студентов;
2. consultation availability: 7, 30 и 90 дней;
3. attendance summary: 1 000, 10 000 и 100 000 записей;
4. dashboard: студент с 10, 100 и 500 задачами/media;
5. public leaderboard: 1 000 и 100 000 профилей.

Пока такие замеры не проведены, нельзя честно утверждать фактическое время ответа в миллисекундах. Статический аудит показывает места, где latency будет расти с данными.

# 6. Тесты

Не хватает:

1. API authorization matrix по ролям и группам.
2. PostgreSQL integration tests для актуальной схемы.
3. Concurrency test пересекающихся slots.
4. MinIO policy and cleanup tests.
5. Performance tests с подсчетом SQL-запросов.
6. Readiness tests при недоступной БД/MinIO.
7. Проверки размера response и pagination.
8. Обновления устаревшего [test_student_management.py](bak/app/accounts/specs/test_student_management.py), который ожидает старое поле `plain_password` и старый tuple-контракт.

## Итог

Главные нерешенные задачи: CORS, fixed secrets/admin bootstrap, актуальность JWT, scope student dashboard, MinIO error handling, consultation overlap race, N+1 в student list/availability, остаточные unlimited collections, production container и измерение p95/p99.
