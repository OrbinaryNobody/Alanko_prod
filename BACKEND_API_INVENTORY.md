# Backend API inventory

Дата проверки: 2026-08-26

Все маршруты ниже дополнительно получают префикс `/api` в `bak/app/main.py`.
Защищённые маршруты требуют `Authorization: Bearer <access_token>`.

## Общие маршруты

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/` | public | - | `{status, service}` |
| GET | `/health/live` | public | - | `{status}` |
| GET | `/api/accounts/health` | public | - | `{status, service}` |
| POST | `/api/accounts/login` | public | JSON `LoginSchema` | `{access_token, token_type}` |

Ошибки домена преобразуются в `{detail: string}` со статусами `400`, `403`,
`404`, `409` или `422`.

## Public

| Method | Path | Auth | Response |
| --- | --- | --- | --- |
| GET | `/api/public/leaderboard` | public | leaderboard payload |
| GET | `/api/public/achievements/videos?limit=20&offset=0` | public | `PublicAchievementVideosResponse` |
| GET | `/api/public/news?limit=20&offset=0` | public | `{items: [...]}` |
| GET | `/api/public/student/{student_id}/videos` | backend context | student video payload |

`/api/public/student/{student_id}/videos` нельзя считать публичным: маршрут
создаёт `AccessContext` через `get_access_context` и должен использоваться
только после проверки разрешённого сценария доступа.

## Profile and student

| Method | Path | Permission | Response |
| --- | --- | --- | --- |
| GET | `/api/profile/dashboard` | `VIEW_OWN_DASHBOARD` | dashboard payload |
| GET | `/api/education/students` | `VIEW_STUDENTS` или `VIEW_ATTENDANCE` | `{data: [...]}` |
| GET | `/api/education/students/tasks` | `VIEW_STUDENTS` | `{data: [...]}` |
| POST | `/api/education/students/upload-video` | upload-media permission | student task video payload |
| PUT | `/api/education/students/student-tasks/{student_task_id}` | grade-tasks permission | `{message, data}` |

Для списка студентов поддерживаются query-параметры `attendance_date`,
`search`, `group_id`, `payment_status`, `remaining_visits_lte`, `limit` и
`offset`.

## Education tasks

| Method | Path | Permission | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/api/education/tasks` | `VIEW_PROGRAMS` | - | `{data: [...]}` |
| POST | `/api/education/tasks` | create-tasks permission | JSON `TaskCreate` | `{message, task, students_count}` |
| GET | `/api/education/tasks/categories` | `VIEW_PROGRAMS` | - | `{data: [...]}` |
| POST | `/api/education/tasks/categories` | create-tasks permission | JSON `CategoryCreate` | `{message, data}` |
| GET | `/api/education/tasks/{task_id}` | `VIEW_PROGRAMS` | - | `{data: task}` |
| PUT | `/api/education/tasks/{task_id}` | edit-programs permission | JSON `TaskUpdate` | `{message, data}` |

## Attendance

| Method | Path | Permission | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/api/attendance/summary?date=YYYY-MM-DD` | `VIEW_ATTENDANCE` | - | summary payload |
| POST | `/api/attendance/check-in` | `MANAGE_ATTENDANCE` | JSON `AttendanceCheckInCreate` | attendance payload |
| POST | `/api/attendance/{attendance_id}/cancel` | `MANAGE_ATTENDANCE` | - | attendance payload |
| GET | `/api/attendance/students/{student_id}/attendance` | `VIEW_ATTENDANCE` | optional date/limit/offset | `{student_id, items}` |
| POST | `/api/attendance/students/{student_id}/subscriptions` | `MANAGE_ATTENDANCE` | JSON `SubscriptionCreate` | subscription payload |
| POST | `/api/attendance/groups/{group_id}/subscriptions` | `MANAGE_ATTENDANCE` | JSON `SubscriptionCreate` | `{group_id, count, subscriptions}` |
| POST | `/api/attendance/students/{student_id}/subscriptions/renew` | `MANAGE_ATTENDANCE` | JSON `SubscriptionCreate` | subscription payload |

Список студентов для attendance получается через
`GET /api/education/students` с permission `VIEW_ATTENDANCE`.

## Consultations

Подтверждённые student routes:

- `GET /api/consultations/availability`
- `GET /api/consultations/slots/{slot_id}/price`
- `GET /api/consultations/my`
- `GET /api/consultations/invitations`
- `GET /api/consultations/notifications`
- `POST /api/consultations/slots/{slot_id}/book`
- `POST /api/consultations/bookings/{participant_id}/cancel`
- `POST /api/consultations/invitations/{invitation_id}/accept`
- `POST /api/consultations/invitations/{invitation_id}/decline`

Все эти маршруты используют permissions домена consultations. Admin/teacher
routes находятся в `bak/app/consultations/api/admin.py` и должны быть добавлены
в следующую ревизию inventory вместе с их DTO.

## Accounts and media

Подтверждённые account mutations:

- `POST /api/accounts/users` - `MANAGE_USERS`, JSON `AdminAddUserSchema`;
- `POST /api/accounts/students` - `MANAGE_USERS`, multipart form + image;
- `PATCH /api/accounts/students/{student_id}` - `MANAGE_USERS`, JSON `StudentUpdateSchema`;
- `DELETE /api/accounts/students/{student_id}` - `MANAGE_USERS`.

Media upload routes и generated file URLs находятся в
`bak/app/media/api/routes.py`; frontend не должен собирать MinIO URL вручную.

## Programs, groups and achievements

Education routes используют permissions из соответствующих `require_*`
dependencies; frontend должен передавать JSON согласно указанным schema.

- `/api/education/programs`: `GET`, `POST` (`ProgramCreate`);
- `/api/education/programs/{program_id}`: `GET`, `PUT` (`ProgramCreate`);
- `/api/education/programs/{program_id}/structure`: `GET`;
- `/api/education/programs/{program_id}/blocks`: `POST` (`ProgramBlockCreate`);
- `/api/education/programs/blocks/{block_id}/topics`: `POST` (`ProgramTopicCreate`);
- `/api/education/programs/blocks/{block_id}/topics/{topic_id}/tasks`: `POST` (`ProgramTaskCreate`);
- `/api/education/groups`: `GET`, `POST` (`GroupCreate`);
- `/api/education/groups/{group_id}/members`: `POST` (`GroupMemberCreate`);
- `/api/education/groups/{group_id}/teachers`: `POST` (`GroupTeacherCreate`);
- `/api/education/groups/{group_id}/students`: `GET`;
- `/api/education/groups/{group_id}/enrollments`: `POST` (`EnrollmentCreate`);
- `/api/education/groups/{group_id}/schedule`: `GET`, `POST` (`GroupScheduleCreate`);
- `/api/education/groups/schedule/{schedule_id}`: `DELETE`;
- `/api/education/program-change-proposals/programs/{program_id}`: `POST` (`ProgramChangeProposalCreate`);
- `/api/education/program-change-proposals/my`: `GET`;
- `/api/education/program-change-proposals/{proposal_id}`: `GET`;
- `/api/education/admin/program-change-proposals`: `GET`;
- `/api/education/admin/program-change-proposals/{proposal_id}`: `GET`;
- `/api/education/admin/program-change-proposals/{proposal_id}/approve`: `POST` (`ProgramChangeDecision`);
- `/api/education/admin/program-change-proposals/{proposal_id}/reject`: `POST` (`ProgramChangeDecision`).

Achievements:

- `GET /api/achievements` - `VIEW_ACHIEVEMENTS`, response `{data: [...]}`;
- `GET /api/achievements/student/{student_id}` - `VIEW_ACHIEVEMENTS`, response `{data: [...]}`;
- `POST /api/achievements/create` - `MANAGE_ACHIEVEMENTS`, multipart form;
- `POST /api/achievements/assign` - `MANAGE_ACHIEVEMENTS`, JSON `AssignAchievement`;
- `POST /api/achievements/{achievement_id}/upload-media` - upload-media permission, multipart file;
- `POST /api/achievements/{achievement_id}/upload-video` - upload-media permission, multipart file.

## Calendar and consultation administration

- `GET /api/calendar/events` и `GET /api/calendar/days` - требуют
   `VIEW_CONSULTATIONS` или `MANAGE_CONSULTATIONS`; поддерживают `date_from`,
   `date_to`, а events также `teacher_id`, `type`, `status`.
- `GET /api/consultations/admin/days` и `POST /api/consultations/admin/days`
   (`ConsultationDayCreate`);
- `PATCH /api/consultations/admin/days/{day_id}/status`
   (`ConsultationDayStatusUpdate`);
- `GET /api/consultations/admin/slots` и `POST /api/consultations/admin/slots`
   (`ConsultationSlotCreate`);
- `POST /api/consultations/admin/slots/{slot_id}/invitations`
   (`ConsultationInvitationCreate`);
- `GET /api/consultations/admin/slots/{slot_id}/participants`;
- `PATCH /api/consultations/admin/participants/{participant_id}/attendance`
   (`ConsultationAttendanceUpdate`);
- `PATCH /api/consultations/admin/participants/{participant_id}/payment`
   (`ConsultationPaymentUpdate`);
- `GET /api/consultations/admin/slots/{slot_id}/settlement`.

Admin consultation routes требуют `MANAGE_CONSULTATIONS` или `MANAGE_USERS`.

## News administration

- `GET /api/admin/news` - `MANAGE_NEWS`, response `{items: [...]}`;
- `POST /api/admin/news` - `MANAGE_NEWS`, multipart `title`, `description`,
   `status`, `image`;
- `PATCH /api/admin/news/{news_id}` - `MANAGE_NEWS`, multipart optional fields;
- `DELETE /api/admin/news/{news_id}` - `MANAGE_NEWS`, status `204`.

Public news is read-only through `GET /api/public/news`.

## Deliberately unavailable

Payment router не подключён в `bak/app/main.py`. Следующие routes сейчас не
являются рабочим backend-контрактом и не должны вызываться frontend:

- `POST /api/payments/course`;
- `POST /api/payments/special-offer`;
- `GET /api/payments/{payment_id}`;
- `POST /api/payments/{payment_id}/confirm`;
- `POST /api/payments/webhook`.

## Integration blockers

1. OpenAPI отключён (`openapi_url=None`), поэтому этот inventory должен
   обновляться вместе с изменениями роутеров.
2. CORS сейчас разрешает любые origins и credentials одновременно; перед
   production нужно задать явный список frontend origins.
3. `web/js/auth.js` сохраняет token одновременно в `localStorage` и
   `sessionStorage`, что требует отдельного решения по token strategy.
4. `web/index.html` уже использует подтверждённые public leaderboard и videos,
   но login передаёт token ещё и через hash; после импорта hash token очищается,
   однако это нужно убрать из redirect-контракта при унификации auth-клиента.