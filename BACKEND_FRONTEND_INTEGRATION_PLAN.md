# План подключения backend ко всему frontend

## 1. Цель и границы

Подключить статический frontend из `web/` к FastAPI backend из `bak/app/` через единый HTTP-контракт, сохранив ролевую модель и бизнес-логику backend. В результате каждая пользовательская операция должна получать данные из API, показывать состояния загрузки/ошибки и обновлять UI после успешной мутации.

Целевые роли:

- публичный посетитель;
- ученик;
- преподаватель;
- администратор.
- секретарь.

Главное правило: frontend не воспроизводит бизнес-правила, не обращается к БД и не хранит рабочие данные в `localStorage`; он вызывает API и отображает DTO.

## 2. Что уже есть

### Backend

- FastAPI запускается из `bak/app/main.py`.
- Все доменные роутеры подключаются с префиксом `/api`.
- Авторизация: `POST /api/accounts/login`, затем JWT в `Authorization: Bearer <token>`.
- Доступ: JWT -> `AccessContext` -> permission/policy -> service.
- Основные домены: accounts, education, achievements, profile, attendance, consultations, calendar, catalog, media, payments, public, news.
- Файлы обслуживаются через MinIO; часть URL публичная, сертификаты и документы должны оставаться приватными.

### Frontend

- Страницы находятся в `web/`, общий auth-код в `web/js/auth.js`.
- `auth.js` уже содержит `API_URL`, хранение JWT и `fetchWithAuth`.
- `index.html` вызывает публичные leaderboard/video API и login.
- `student_page.html` содержит готовые рендереры dashboard/tasks, но вызов dashboard закомментирован.
- `test.html` содержит наиболее полный набор teacher/admin запросов.
- `panel_for_al.html`, `panel_for_taecher.html` и `admin_attendance.html` в значительной части состоят из mock/static UI и требуют привязки.

## 3. P0: зафиксировать контракт до подключения UI

1. Получить OpenAPI-схему или сделать backend endpoint inventory: метод, полный путь, auth, permission, request DTO, response DTO, ошибки.
2. Проверить фактические пути, особенно:
   - dashboard: backend показывает `/api/profile/dashboard`, а frontend ожидает `/api/user/dashboard`;
   - student tasks/students: проверить, соответствуют ли frontend-пути `/education/students`, `/education/students/tasks`, `/education/tasks` реальным роутерам;
   - consultation, calendar, payment и news prefix-ы;
   - формат `data`, `items`, вложенных объектов и nullable-полей.
3. Согласовать единую версию DTO. Не добавлять на frontend эвристику вида `data.x || data.y` после фиксации контракта.
4. Добавить или включить machine-readable OpenAPI для разработки либо хранить версионируемый `openapi.json`.
5. Зафиксировать базовые URL через `window.ALANKO_API_URL` и конфигурацию окружений: local/stage/prod.
6. Проверить CORS: убрать `allow_origins=["*"]` и `allow_credentials=True` вместе в production, задать список разрешённых frontend origin.

**Готово, когда:** любой endpoint можно найти в единой таблице, а frontend-разработчик знает точный request/response без чтения service-кода.

## 4. P0: общий frontend API и auth слой

Из `web/js/auth.js` выделить или расширить общий клиент:

- `apiFetch(path, options)` с JSON parsing, timeout и единым форматом `ApiError`;
- автоматическое добавление Bearer token;
- обработка `401` с очисткой сессии и возвратом на login;
- обработка `403`, `404`, `409`, `422`, `5xx` с понятным UI-сообщением;
- `requestJson`, `requestFormData`, `requestFile` без ручного дублирования заголовков;
- отмена устаревших запросов через `AbortController`;
- защита от повторной отправки формы и базовая retry-политика только для безопасных GET;
- единый logout и redirect по роли;
- проверка JWT payload только для навигации, а не для принятия решений о доступе.

JWT не хранить одновременно в localStorage и sessionStorage без явного решения по модели угроз. Минимум: выбрать один механизм, добавить logout на всех страницах и не выводить access token в URL/hash после миграции.

## 5. P1: подключение публичной части

### `web/index.html`

1. Login: оставить `POST /api/accounts/login`, обработать ошибочные ответы и redirect по роли.
2. Leaderboard: подключить `GET /api/public/leaderboard`.
3. Public videos: подключить `GET /api/public/student/{student_id}/videos` только если этот публичный сценарий разрешён продуктом; иначе заменить на authenticated endpoint.
4. Новости: добавить загрузку `GET /api/public/news` и состояние empty/loading/error.
5. Удалить demo-данные из участков, которые уже обслуживаются API.
6. Проверить XSS: не вставлять поля API через `innerHTML` без escaping; для пользовательского текста использовать `textContent`.

**Проверка:** неавторизованный посетитель видит только разрешённые публичные данные; при недоступном API страница остаётся usable и показывает fallback.

## 6. P1: кабинет ученика

### `web/student_page.html`

1. Включить `requireAuth()` и `loadStudentDashboard()` после проверки контракта.
2. Перевести dashboard на фактический backend path, вероятнее всего `/api/profile/dashboard`.
3. Подключить задачи, достижения, рейтинг, историю и видео к одному DTO.
4. Добавить консультации:
   - `GET /api/consultations/availability`;
   - `GET /api/consultations/my`;
   - `GET /api/consultations/invitations`;
   - `GET /api/consultations/notifications`;
   - booking/cancel/accept/decline по реальным route decorators.
5. Добавить оплату консультации/курса только по подтверждённым payment endpoint-ам и redirect URL провайдера.
6. Убрать локальную имитацию отмены занятия: отмена должна вызывать API, затем обновлять список.
7. Для видео и приватных файлов показывать backend-generated URL, не собирать MinIO URL на frontend.

**Проверка:** ученик видит только свои данные; прямой вызов чужого resource ID получает `403/404`, а UI корректно отображает ошибку.

## 7. P1: кабинет преподавателя

### `web/panel_for_taecher.html` и функционал из `web/test.html`

Разделить большой inline-script на доменные модули или минимум на файлы:

- `teacher/students.js`;
- `teacher/tasks.js`;
- `teacher/achievements.js`;
- `teacher/groups.js`;
- `teacher/consultations.js`;
- `teacher/attendance.js`.

Подключить в таком порядке:

1. список студентов и student options;
2. категории и задачи: list/create/update;
3. task details, upload student task video, grade/update status;
4. achievements: list/student/create/assign/upload media/upload video;
5. группы, участники и расписание;
6. consultations availability/admin slots/invitations/attendance/settlement;
7. teacher profile и logout.

Формы загрузки отправлять через `FormData` без ручного `Content-Type`. После mutation обновлять только затронутый ресурс либо инвалидировать соответствующий cache.

Важно: в `test.html` уже видны запросы к `/education/...`; сначала сверить их с реальными роутерами, потому что часть API может быть смонтирована иначе. Не переносить mock fallback в production как источник истины.

## 8. P1: кабинет администратора

### `web/panel_for_al.html`

Подключить реальные сценарии:

- пользователи: список, создание teacher/student, редактирование и удаление согласно accounts API;
- группы/programs: CRUD, структура программы, topics/tasks, proposals и review;
- consultations admin: days, slots, invitations, participants, attendance, payment status;
- attendance: summary, check-in, cancel, student history, subscriptions;
- news: `POST /api/admin/news/sync` и управление публикациями, если admin routes это поддерживают;
- payments: статусы и webhook оставить backend-only, в UI показывать только безопасные read/action endpoints;
- media: upload с прогрессом и отображением ошибок размера/type.

Заменить кнопки, которые сейчас только закрывают modal или вызывают `alert`, на submit handlers с `loading/success/error` состояниями. Mock names, counts, dates, students и teachers удалить после появления соответствующих API responses.

## 9. P1: attendance interface

### `web/admin_attendance.html`

1. Убрать `DEFAULT_STUDENTS` и `alanko_students_db` из рабочего режима.
2. Загружать студентов и контекст посещаемости из attendance/education API.
3. Фильтры search/group/payment/remaining visits передавать query-параметрами backend, если endpoint это поддерживает.
4. Check-in/cancel делать через API с idempotent UI.
5. Подписки создавать/обновлять через attendance endpoints.
6. После операции обновлять metrics и историю с сервера.
7. Разделить demo mode и production mode явным config flag, не смешивать их.

Доступ к этому кабинету получают `admin`, `teacher` и `secretary`. Роль `secretary`
является отдельным аккаунтом без управления пользователями, группами, заданиями,
достижениями и платежами: ей доступны только просмотр списка учеников и контекста
посещаемости/абонемента, отметка и отмена посещения, создание и продление абонемента.
Для этого backend использует отдельные permissions `VIEW_ATTENDANCE` и
`MANAGE_ATTENDANCE`; seed должен добавлять роль идемпотентно и в уже существующую БД.

## 10. P1: роли и маршрутизация

Сделать единый guard:

- public route без token;
- student route требует `VIEW_OWN_DASHBOARD`/доменные permissions;
- teacher route проверяет backend permissions, не только наличие JWT;
- admin route использует `is_admin`/permissions и показывает `403` state.
- secretary route открывает только кабинет посещаемости и проверяет backend permissions;
   роль не должна получать admin bypass или доступ к управлению пользователями.

После login redirect должен опираться на согласованный role claim. Если permissions не входят в JWT, добавить `/me` endpoint или другой безопасный источник текущего пользователя, вместо предположений frontend.

## 11. P2: надёжность и безопасность

- таймауты и offline state для каждого экрана;
- единая обработка validation errors `422`;
- escaping всех API-текстов, URL allowlist для ссылок и видео;
- CSP, HTTPS, secure cookie/token strategy и запрет токенов в URL;
- private MinIO objects выдавать через authenticated backend/signed URL;
- исправить публичность student photos/videos, если это не осознанное требование;
- не показывать generated passwords повторно в публичном DOM и не хранить их в frontend storage;
- добавить request correlation id и client-side error logging без персональных данных.

## 12. Тестовый контур

### Backend contract tests

Для каждого endpoint проверить status, auth, permission, DTO shape, validation и domain errors. Минимальные сценарии: login, expired token, forbidden role, empty lists, duplicate mutation, upload limits, payment callback.

### Frontend tests

- API client: token, 401, 403, 422, timeout, retry;
- login и role redirect;
- student dashboard loading/error/empty;
- teacher create task/student/achievement;
- admin check-in and subscription;
- consultation booking and invitation acceptance;
- file upload and generated URL display.

### E2E smoke

1. anonymous -> public page/news/leaderboard;
2. admin login -> create student -> create task -> assign achievement;
3. teacher login -> view students -> grade/upload;
4. student login -> dashboard -> task -> consultation booking;
5. admin -> attendance check-in -> history/subscription verification.

Запускать against disposable PostgreSQL/MinIO fixtures, не against production.

## 13. Рекомендуемый порядок работ

1. Контрактный inventory и исправление path/DTO mismatches.
2. Общий API/auth client и environment config.
3. Login, guards, logout и публичная index page.
4. Student dashboard and consultations.
5. Teacher tasks, students, achievements and uploads.
6. Admin users, education and consultations.
7. Attendance page migration from localStorage.
8. Payments, news sync and remaining catalog/profile screens.
9. Security hardening, OpenAPI/contract tests and E2E.
10. Удаление mock data, dead handlers и дублей inline JavaScript.

## 14. Definition of Done

- Нет рабочих экранов, которые используют mock/localStorage вместо backend.
- Все запросы идут через общий API client.
- Каждая mutation имеет loading, success и error state.
- Все защищённые операции проверяются backend permissions.
- Контракты frontend/backend покрыты тестами.
- Публичные и приватные файлы разделены корректно.
- CORS, token strategy, CSP и production environment проверены.
- Пройдены smoke-сценарии для anonymous, student, teacher и admin.
