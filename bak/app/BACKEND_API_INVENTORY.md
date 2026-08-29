# Backend API inventory

Дата проверки: 2026-08-26.

Источник истины: `bak/app/main.py` и подключенные FastAPI-роутеры. Все
router-маршруты получают дополнительный префикс `/api` в `main.py`. Маршруты
`/` и `/health/live` зарегистрированы напрямую и `/api` не имеют.

Зарегистрировано 92 API endpoints, не считая двух корневых health-маршрутов.
Еще 5 payment endpoints определены в коде, но не подключены.

## Общие правила

- `public` означает отсутствие auth dependency.
- Остальные маршруты требуют `Authorization: Bearer <access_token>`.
- Статус по умолчанию: `200`; явные `201` и `204` указаны ниже.
- Ошибки авторизации: `401/403`; ошибки валидации: `422`; доменные ошибки:
  `400/403/404/409/422`.
- Внешний frontend-контракт возвращает DTO/объекты, а не ORM-модели.

## Общие маршруты

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/` | public | — | `{status, service}`, `200` |
| GET | `/health/live` | public | — | `{status}`, `200` |

## Accounts

Роутер: `accounts/api/auth.py`.

| Method | Path | Auth / permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/accounts/health` | public | — | `{status, service}`, `200` |
| POST | `/api/accounts/login` | public | JSON `LoginSchema`: `email`, `password` | `{access_token, token_type}`, `200` |
| POST | `/api/accounts/users` | Bearer, `MANAGE_USERS` | JSON `AdminAddUserSchema` | `{message, data: {user_id, email, password}}`, `201` |
| POST | `/api/accounts/teachers` | Bearer, `MANAGE_USERS` | multipart: `email`, `first_name`, `middle_name`; optional image, last name | `{message, data: {user_id, email, password, avatar_url}}`, `201` |
| DELETE | `/api/accounts/teachers/{teacher_id}` | Bearer, `MANAGE_USERS` | Path `teacher_id: int` | empty, `204` |
| GET | `/api/accounts/users` | Bearer, `MANAGE_USERS` | Query `role` optional | `{data: [user DTO]}`, `200` |
| POST | `/api/accounts/students` | Bearer, `MANAGE_USERS` | multipart: `email`, `first_name`, `middle_name`; optional image, last name, birth year, parent fields | `{user_id, email, image_url}`, `201` |
| DELETE | `/api/accounts/students/{student_id}` | Bearer, `MANAGE_USERS` | Path `student_id: int` | `{message, student_id}`, `200` |
| PATCH | `/api/accounts/students/{student_id}` | Bearer, `MANAGE_USERS` | Path; JSON `StudentUpdateSchema` | `{message, data}`, `200` |

`GET /api/accounts/users?role=teacher` используется админской страницей для
списка преподавателей. Пароли и `password_hash` не возвращаются.

## Education

Роутеры подключены через `education/api/routes.py`. Общий префикс:
`/api/education`.

### Health

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/education/health` | public | — | `{status, service}`, `200` |

### Programs

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| POST | `/api/education/programs` | `CREATE_PROGRAMS` | JSON `ProgramCreate` | `{message, data}`, `201` |
| GET | `/api/education/programs` | `VIEW_PROGRAMS` | — | `{data}`, `200` |
| GET | `/api/education/programs/{program_id}` | `VIEW_PROGRAMS` | Path `program_id` | `{data}`, `200` |
| PUT | `/api/education/programs/{program_id}` | `EDIT_PROGRAMS` | Path; JSON `ProgramCreate` | `{message, data}`, `200` |
| GET | `/api/education/programs/{program_id}/structure` | `VIEW_PROGRAMS` | Path `program_id` | `{data}` with blocks/topics/tasks, `200` |
| POST | `/api/education/programs/{program_id}/blocks` | `CREATE_BLOCKS` | Path; JSON `ProgramBlockCreate` | `{message, data}`, `201` |
| POST | `/api/education/programs/blocks/{block_id}/topics` | `CREATE_BLOCKS` | Path; JSON `ProgramTopicCreate` | `{message, data}`, `201` |
| POST | `/api/education/programs/blocks/{block_id}/topics/{topic_id}/tasks` | `CREATE_BLOCKS` | Path; JSON `ProgramTaskCreate` | `{message, data}`, `201` |
| PUT | `/api/education/programs/{program_id}/blocks/{block_id}` | `EDIT_PROGRAMS` | Path; JSON `ProgramBlockUpdate` | `{message, data}`, `200` |
| DELETE | `/api/education/programs/{program_id}/blocks/{block_id}` | `EDIT_PROGRAMS` | Path `program_id`, `block_id` | empty, `204` |
| PUT | `/api/education/programs/{program_id}/blocks/{block_id}/topics/{topic_id}` | `EDIT_PROGRAMS` | Path; JSON `ProgramTopicUpdate` | `{message, data}`, `200` |
| DELETE | `/api/education/programs/{program_id}/blocks/{block_id}/topics/{topic_id}` | `EDIT_PROGRAMS` | Path `program_id`, `block_id`, `topic_id` | empty, `204` |
| PUT | `/api/education/programs/{program_id}/blocks/{block_id}/topics/{topic_id}/tasks/{task_id}` | `EDIT_PROGRAMS` | Path; JSON `ProgramTaskUpdate` | `{message, data}`, `200` |
| DELETE | `/api/education/programs/{program_id}/blocks/{block_id}/topics/{topic_id}/tasks/{task_id}` | `EDIT_PROGRAMS` | Path `program_id`, `block_id`, `topic_id`, `task_id` | empty, `204` |

### Groups

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| POST | `/api/education/groups` | `MANAGE_GROUPS` | JSON `GroupCreate` | `{message, data}`, `201` |
| GET | `/api/education/groups` | `VIEW_GROUPS` | — | `{data}`, `200` |
| POST | `/api/education/groups/{group_id}/members` | `MANAGE_GROUPS` | Path; JSON `GroupMemberCreate` | `{message, data}`, `201` |
| POST | `/api/education/groups/{group_id}/teachers` | `MANAGE_GROUPS` | Path; JSON `GroupTeacherCreate` | `{message, data}`, `201` |
| POST | `/api/education/groups/{group_id}/students` | `MANAGE_ENROLLMENTS` | Path; JSON `GroupStudentCreate` | `{message, data}`, `201` |
| GET | `/api/education/groups/{group_id}/students` | `VIEW_STUDENTS` | Path `group_id` | `{data}`, `200` |
| GET | `/api/education/groups/{group_id}/schedule` | `VIEW_GROUPS` | Path `group_id` | `{data}`, `200` |
| POST | `/api/education/groups/{group_id}/schedule` | `MANAGE_GROUPS` | Path; JSON `GroupScheduleCreate` | `{data}`, `201` |
| DELETE | `/api/education/groups/schedule/{schedule_id}` | `MANAGE_GROUPS` | Path `schedule_id` | empty, `204` |
| POST | `/api/education/groups/{group_id}/enrollments` | `MANAGE_ENROLLMENTS` | Path; JSON `EnrollmentCreate` | `{message, data}`, `201` |

### Students

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| POST | `/api/education/students/upload-video` | `UPLOAD_MEDIA` | multipart `file`, `student_task_id` | task/media payload, `200` |
| PUT | `/api/education/students/student-tasks/{student_task_id}` | `GRADE_TASKS` | Path; JSON `StudentTaskUpdate` | `{message, data}`, `200` |
| GET | `/api/education/students` | `VIEW_STUDENTS` or `VIEW_ATTENDANCE` | Query `attendance_date`, `search`, `group_id`, `payment_status`, `remaining_visits_lte`, `limit` (1-200, default 100), `offset` | `{data}`, `200` |
| GET | `/api/education/students/tasks` | `VIEW_STUDENTS` | — | `{data}`, `200` |

### Tasks

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| POST | `/api/education/tasks` | `CREATE_TASKS` | JSON `TaskCreate` | `{message, task, students_count}`, `201` |
| GET | `/api/education/tasks` | `VIEW_PROGRAMS` | — | `{data}`, `200` |
| GET | `/api/education/tasks/categories` | `VIEW_PROGRAMS` | — | `{data}`, `200` |
| POST | `/api/education/tasks/categories` | `CREATE_TASKS` | JSON `CategoryCreate` | `{message, data}`, `201` |
| GET | `/api/education/tasks/{task_id}` | `VIEW_PROGRAMS` | Path `task_id` | `{data}`, `200` |
| PUT | `/api/education/tasks/{task_id}` | `EDIT_PROGRAMS` | Path; JSON `TaskUpdate` | `{message, data}`, `200` |

### Program change proposals

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| POST | `/api/education/program-change-proposals/programs/{program_id}` | `VIEW_PROGRAMS` | Path; JSON `ProgramChangeProposalCreate` | `{message, data}`, `201` |
| GET | `/api/education/program-change-proposals/my` | `VIEW_PROGRAMS` | — | `{data}`, `200` |
| GET | `/api/education/program-change-proposals/{proposal_id}` | `VIEW_PROGRAMS` | Path `proposal_id` | `{data}`, `200` |
| GET | `/api/education/admin/program-change-proposals` | `VIEW_PROGRAMS` | — | `{data}`, `200` |
| GET | `/api/education/admin/program-change-proposals/{proposal_id}` | `VIEW_PROGRAMS` | Path `proposal_id` | `{data}`, `200` |
| POST | `/api/education/admin/program-change-proposals/{proposal_id}/approve` | `VIEW_PROGRAMS` | Path; JSON `ProgramChangeDecision` | `{message, data}`, `200` |
| POST | `/api/education/admin/program-change-proposals/{proposal_id}/reject` | `VIEW_PROGRAMS` | Path; JSON `ProgramChangeDecision` | `{message, data}`, `200` |

## Achievements

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/achievements` | `VIEW_ACHIEVEMENTS` | — | `{data}`, `200` |
| GET | `/api/achievements/student/{student_id}` | `VIEW_ACHIEVEMENTS` | Path `student_id` | `{data}`, `200` |
| POST | `/api/achievements/create` | `MANAGE_ACHIEVEMENTS` | multipart `title`, `assignment_type`; optional description, event date, place, student id, file | create payload, `200` |
| POST | `/api/achievements/assign` | `MANAGE_ACHIEVEMENTS` | JSON `AssignAchievement` | assignment payload, `200` |
| POST | `/api/achievements/{achievement_id}/upload-media` | `UPLOAD_MEDIA` | Path; multipart `file` | upload payload, `200` |
| POST | `/api/achievements/{achievement_id}/upload-video` | `UPLOAD_MEDIA` | Path; multipart `file` | upload payload, `200` |

## Assessment

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/assessment/student/{student_id}/task/{task_id}` | `VIEW_STUDENTS` | Path `student_id`, `task_id` | assessment payload, `200` |

## Attendance

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/attendance/summary` | `VIEW_ATTENDANCE` | Required query `date: YYYY-MM-DD` | summary payload, `200` |
| POST | `/api/attendance/check-in` | `MANAGE_ATTENDANCE` | JSON `AttendanceCheckInCreate` | attendance payload, `201` |
| POST | `/api/attendance/{attendance_id}/cancel` | `MANAGE_ATTENDANCE` | Path `attendance_id` | attendance payload, `200` |
| GET | `/api/attendance/students/{student_id}/attendance` | `VIEW_ATTENDANCE` | Path; query `date_from`, `date_to`, `limit` (default 50), `offset` | `AttendanceHistoryResponse`, `200` |
| POST | `/api/attendance/students/{student_id}/subscriptions` | `MANAGE_ATTENDANCE` | Path; JSON `SubscriptionCreate` | subscription payload, `201` |
| POST | `/api/attendance/groups/{group_id}/subscriptions` | `MANAGE_ATTENDANCE` | Path; JSON `SubscriptionCreate` | `{group_id, count, subscriptions}`, `201` |
| POST | `/api/attendance/students/{student_id}/subscriptions/renew` | `MANAGE_ATTENDANCE` | Path; JSON `SubscriptionCreate` | subscription payload, `201` |

## Catalog

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/catalog/health` | public | — | `{status, service}`, `200` |
| GET | `/api/catalog/programs` | `VIEW_PROGRAMS` | — | `{data}`, `200` |

## Profile

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/profile/dashboard` | `VIEW_OWN_DASHBOARD` | — | dashboard payload, `200` |
| GET | `/api/profile/tasks` | `VIEW_OWN_TASKS` | — | student tasks payload, `200` |

## Public

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/public/leaderboard` | public | — | leaderboard payload, `200` |
| GET | `/api/public/achievements/videos` | public | Query `limit` (1-100, default 20), `offset` (default 0) | `PublicAchievementVideosResponse`, `200` |
| GET | `/api/public/student/{student_id}/videos` | Bearer via `get_access_context` | Path `student_id` | student video payload, `200` |

Несмотря на префикс `/public`, последний endpoint не является анонимным.

## Media

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/media/health` | public | — | `{status, service}`, `200` |
| POST | `/api/media/upload` | `UPLOAD_MEDIA` | multipart `file` | `UploadMediaPayload`, `200` |

## Consultations

### Student

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/consultations/availability` | `VIEW_CONSULTATIONS` | Query `date_from`, `date_to` | `{items}`, `200` |
| GET | `/api/consultations/slots/{slot_id}/price` | `VIEW_CONSULTATIONS` | Path `slot_id` | price quote, `200` |
| GET | `/api/consultations/my` | `VIEW_CONSULTATIONS` | — | `{items}`, `200` |
| GET | `/api/consultations/invitations` | `VIEW_CONSULTATIONS` | — | `{items}`, `200` |
| GET | `/api/consultations/notifications` | `VIEW_CONSULTATIONS` | — | `{items}`, `200` |
| POST | `/api/consultations/slots/{slot_id}/book` | `BOOK_CONSULTATIONS` | Path `slot_id` | participant payload, `201` |
| POST | `/api/consultations/bookings/{participant_id}/cancel` | `BOOK_CONSULTATIONS` | Path `participant_id` | cancellation payload, `200` |
| POST | `/api/consultations/invitations/{invitation_id}/accept` | `BOOK_CONSULTATIONS` | Path `invitation_id` | participant payload, `200` |
| POST | `/api/consultations/invitations/{invitation_id}/decline` | `BOOK_CONSULTATIONS` | Path `invitation_id` | invitation payload, `200` |

### Admin

Все маршруты используют `MANAGE_CONSULTATIONS` или `MANAGE_USERS` через
`require_any_permission`.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/consultations/admin/days` | — | `{items}`, `200` |
| POST | `/api/consultations/admin/days` | JSON `ConsultationDayCreate` | day payload, `201` |
| PATCH | `/api/consultations/admin/days/{day_id}/status` | Path; JSON `ConsultationDayStatusUpdate` | `{id, status}`, `200` |
| GET | `/api/consultations/admin/slots` | Query `limit` (default 100), `offset` | `{items}`, `200` |
| POST | `/api/consultations/admin/slots` | JSON `ConsultationSlotCreate` | slot payload, `201` |
| POST | `/api/consultations/admin/slots/{slot_id}/invitations` | Path; JSON `ConsultationInvitationCreate` | `{items}`, `201` |
| GET | `/api/consultations/admin/slots/{slot_id}/participants` | Path `slot_id` | `{items}`, `200` |
| PATCH | `/api/consultations/admin/participants/{participant_id}/attendance` | Path; JSON `ConsultationAttendanceUpdate` | attendance payload, `200` |
| PATCH | `/api/consultations/admin/participants/{participant_id}/payment` | Path; JSON `ConsultationPaymentUpdate` | payment payload, `200` |
| GET | `/api/consultations/admin/slots/{slot_id}/settlement` | Path `slot_id` | settlement payload, `200` |

## Calendar

Роутер `schedule/api/routes.py` подключен с префиксом `/calendar`. Оба
маршрута требуют `VIEW_CONSULTATIONS` или `MANAGE_CONSULTATIONS`.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/calendar/events` | Query `date_from`, `date_to`, `teacher_id`, `type`, `status` | `{date_from, date_to, items}`, `200` |
| GET | `/api/calendar/days` | Query `date_from`, `date_to` | `{date_from, date_to, items}`, `200` |

Без дат используется диапазон от текущего дня до следующих 6 дней.

## News

### Public

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| GET | `/api/public/news` | public | Query `limit` (default 20), `offset` (default 0) | `NewsListResponse`, `200` |

### Admin

| Method | Path | Permission | Request | Response |
|---|---|---|---|---|
| GET | `/api/admin/news` | `MANAGE_NEWS` | — | `NewsListResponse`, `200` |
| POST | `/api/admin/news` | `MANAGE_NEWS` | multipart required `title`, `description`, `image`; optional `status` | news payload, `201` |
| PATCH | `/api/admin/news/{news_id}` | `MANAGE_NEWS` | Path; multipart optional `title`, `description`, `status`, `image` | news payload, `200` |
| DELETE | `/api/admin/news/{news_id}` | `MANAGE_NEWS` | Path `news_id` | empty, `204` |

Удаление новости является soft-delete: запись переводится в `archived` и
исключается из рабочего admin-списка. Публичный список возвращает только
`published` записи.

## Определены, но не подключены

`payments/api/routes.py` существует, но router отсутствует в `main.py`. Эти
маршруты не являются рабочим HTTP-контрактом и не должны вызываться frontend:

| Method | Path | Auth / dependency | Request | Response |
|---|---|---|---|---|
| POST | `/api/payments/course` | Bearer via `get_access_context` | JSON `CreateOfferPaymentRequest` | `CreateOfferPaymentResponse`, `200` |
| POST | `/api/payments/special-offer` | Bearer via `get_access_context` | JSON `CreateSpecialOfferPaymentRequest` | `CreateOfferPaymentResponse`, `200` |
| GET | `/api/payments/{payment_id}` | Bearer via `get_access_context` | Path `payment_id` | `PaymentStatusResponse`, `200` |
| POST | `/api/payments/{payment_id}/confirm` | Bearer via `get_access_context` | Path `payment_id` | `PaymentStatusResponse`, `200` |
| POST | `/api/payments/webhook` | public endpoint + `get_db` | JSON `PaymentWebhookRequest` | `PaymentStatusResponse`, `200` |

## Важные ограничения

- OpenAPI отключён в `main.py` (`openapi_url=None`), поэтому файл нужно
  обновлять вместе с изменениями роутеров.
- CORS сейчас разрешает любые origins и credentials одновременно; перед
  production нужен явный allowlist frontend origins.
- Frontend должен использовать generated media URLs backend и не собирать
  MinIO URLs самостоятельно.
