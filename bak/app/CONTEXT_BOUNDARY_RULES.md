# Alanko architecture method book

## Current state
The project is now a context-based modular monolith with clear owner contexts and shared infrastructure.

Current top-level contexts:
- accounts
- education
- assessment
- profile
- achievements
- media
- admin
- catalog
- payments
- consultations

Current state of the implementation:
- the project remains a modular monolith, and the `consultations` bounded context has moved from pure scaffold to an operational vertical slice;
- the consultations context now includes model/service/repository code, student/admin API routes, schema DTOs, permission constants, and an init_db bootstrap;
- the consultations router is registered in the app startup layer; the current empty-database workflow uses `Base.metadata.create_all()` and `app/db/init_db.py`, not Alembic;
- payments and education remain separated by facades and service boundaries, as defined in the architecture rules.

The architecture is implemented around:
- thin API routers
- facades as public context contracts
- services owning business scenarios
- repositories owning persistence
- AccessContext-based authorization
- DTOs shaping API payloads

## Current implementation status
The project is currently in the middle of two parallel evolutions:
1. the existing temporary offer/payment flow still needs the final production-grade hardening;
2. a new private-consultations bounded context is being introduced to model teacher/student slots, participant history, invitations, and attendance.

This is the current target shape:
- offers are still treated as a temporary commercial/business domain for collaboration-style registration flows;
- payments remain a separate bounded context and should not own education registration logic directly;
- education remains the owner of learning/program enrollment logic;
- private consultations are a new bounded context, intentionally separated from payments and education;
- payments do not own the educational registration flow directly;
- consultation booking is modeled as slot-based resource allocation, not as direct teacher calendar logic.

### What is already implemented
- payments context exists with API, facade, service, repository, and provider abstraction;
- a special-offer-based payment flow exists for the current collaboration-style use case;
- payment DTOs and a frontend-facing payment endpoint exist;
- webhook handling and payment confirmation are implemented with signature verification and idempotency protections;
- database initialization uses `app/db/init_db.py` for fresh DB setup, including payment uniqueness constraints for pending payments;
- tests cover payment creation, duplicate pending payment reuse, duplicate webhook handling, and basic webhook status transitions;
- the consultations bounded context has moved beyond skeleton: it includes `facade.py`, models, repositories, services, routes, and a DTO schema layer under `bak/app/consultations`.

### What is implemented in the consultations context
- `ConsultationDay` model with date/status and working window (`available_from`, `available_to`);
- `ConsultationSlot` model with `start_at`, `end_at`, `capacity`, `access_mode`, `status` and teacher linkage;
- `ConsultationParticipant` model with booking + attendance state separated from deletion logic;
- `ConsultationInvitation` model with `PENDING/ACCEPTED/DECLINED` flow;
- repositories for day, slot, participant, and invitation persistence;
- initial `DayService`, `SlotService`, `AvailabilityService`, and `BookingService` skeletons;
- student route layer for availability, booking, and cancellation;
- admin route layer for day and slot creation;
- schema DTOs for consultation create/update payloads;
- `init_db.py`/`Base.metadata.create_all()` bootstrap for consultation days, slots, participants, invitations, notifications, pricing, and cash-payment status;
- permission constants and app registration hooks for consultation access.

### What is still missing for the target architecture
- runtime validation against a live PostgreSQL instance;
- end-to-end verification that the consultation flow works through the actual FastAPI app startup;
- deeper business logic validation for invitation flow, attendance flow, policy enforcement, and cancellation edge cases;
- full concurrency tests for multi-user booking under full capacity and overlapping time windows;
- production hardening for payments/offers and final integration between the temporary flow and registration logic.

### Current architecture position
The project is no longer at the "empty design" stage: the consultation context is intentionally taking shape as a proper bounded context in the same modular pattern as payments, education, and achievements.
The next priority is to complete the vertical slice for consultations:
- DB schema bootstrap via `init_db.py`
- API routes
- permissions
- booking transaction
- tests

Only after that should the module be considered production-ready for the first operational release.

## Immediate business goal
The next step is not to build a generic payment engine for all courses.
The next step is to build a narrow, temporary offer-based flow for one commercial scenario:
- one offer
- one course/program
- one price
- one payment path
- registration after successful payment

This keeps the feature scoped and avoids polluting education with temporary commercial rules.

## Implementation principle for the current step
The current goal is not to refactor the existing SpecialOffer into a full offers bounded context immediately.
The current goal is to preserve the working foundation that already exists and evaluate whether it is sufficient for the future offers domain.

In practice this means:
- keep the current payments context and Payment model intact
- keep SpecialOffer as the current commercial object for the temporary collaboration flow
- do not replace it with a new offers context just because it was planned earlier
- first audit the existing payments and education integration points before any larger architectural refactor
- only introduce a fuller offers domain if the same pattern is needed for more than one temporary scenario

This is preferable to a premature rewrite of SpecialOffer into Offer followed by a large payments refactor.

## Audit findings and point-by-point plan
### What I found in the current code
- SpecialOffer is currently a minimal commercial object with course_id, price, currency, validity dates, and lifecycle status. It is suitable as the current temporary offer foundation.
- Payment is already a clear bounded-context object and should remain the main payment aggregate.
- PaymentService now orchestrates payment creation while delegating registration to the education facade.
- PaymentRepository stays focused on payment and offer persistence and no longer owns enrollment creation.
- PaymentsFacade is still thin and acceptable.
- Payments routes are thin and can stay thin.
- The provider abstraction is useful and should remain; the YooKassa implementation is still a stub and should not be treated as production-ready.
- The current DTOs are fine for the prototype flow, but they should continue to be reviewed against the frontend contract.
- The course registration handoff is now going through the education facade, though the registration flow still needs end-to-end verification.

### What to leave as-is
- Keep Payment as the payment aggregate in the payments context.
- Keep the payments facade as the public contract of the payments context.
- Keep the API routes thin and DTO-driven.
- Keep the provider abstraction in place.
- Keep SpecialOffer as the current temporary commercial object for the collaboration flow.

### What to change
- Keep payment success separated from educational enrollment, using the education facade rather than direct repository enrollment writes.
- Keep PaymentRepository focused on payment/offer persistence.
- Keep the webhook and confirmation flow so that payment status transition and enrollment outcome remain coordinated but separate.
- Replace the current YooKassa stub with a real provider integration once the boundary and safety behavior are stable.
- Keep the DTO layer clean so the frontend receives only the contract it needs and backend owns the business data.

### What to remove or avoid for now
- Do not introduce a full offers bounded context immediately.
- Do not rename SpecialOffer to Offer or replace it with a new domain structure just for architectural symmetry.
- Do not keep the current direct payments -> education repository coupling in place.
- Do not treat the current YooKassa stub as production-ready.

### What to add next
- Add a clear handoff point from payments to education after payment success, ideally through the education facade or a dedicated registration service.
- Add a domain event or explicit confirmation step so that payment success and course registration become separate but coordinated steps.
- Add idempotency protection for duplicate webhooks and repeated confirmations.
- Add transaction-safe handling so payment status and registration outcome cannot diverge.
- Add structured logging for payment created, payment confirmed, webhook received, and registration completed.

### Recommended execution order
1. Fix the payments -> education boundary first.
2. Keep SpecialOffer as-is for the current temporary flow.
3. Harden webhook and confirmation behavior.
4. Only then move to real provider integration and production-grade reliability.

## Architecture rules
### Rule 1: contexts communicate only through facades
Allowed:
- other_context.facade

Forbidden:
- other_context.services.*
- other_context.repositories.*
- other_context.models.*
- other_context.policies.*
- other_context.schemas.*

### Rule 2: one owner for every domain object
Each domain object has exactly one owning context.
Other contexts must use the owner facade to access it.

### Rule 3: core remains infrastructural
The core layer contains shared infrastructure only:
- access abstractions
- permissions
- auth helpers
- config and security helpers

Not allowed in core:
- domain business rules
- context-specific policies
- product-specific payment logic

### Rule 4: business logic stays in the owning context
Business scenarios belong to the context that owns the domain.

### Rule 5: API is thin
Routers should only:
- receive a request
- resolve access context
- call a facade or service
- return a DTO or response

Routers should not:
- contain business logic
- contain SQL
- contain policy logic
- manipulate ORM entities directly

### Rule 6: services own business scenarios
Services implement business rules and orchestrate repositories, policies, and access checks.
They should not depend on FastAPI or JWT directly.

### Rule 7: repositories are persistence-only
Repositories should only access data.
They should not enforce authorization or business rules.

### Rule 8: policies decide access
Policies answer whether a user may perform an action on an object.
They should not contain persistence logic.

### Rule 9: unified access flow
The access chain must be:
- JWT
- AccessContext
- Permission
- Policy
- Service
- Repository

### Rule 10: do not skip layers
Allowed:
- API -> Facade -> Service -> Repository -> Database

Forbidden:
- API -> Repository
- API -> ORM
- Facade -> Database
- Policy -> Repository

## Project structure
Top-level areas:
- accounts — authentication, users, roles
- education — programs, groups, enrollments, tasks
- assessment — assessments and readiness logic
- profile — dashboard and personal views
- achievements — achievements and award logic
- media — upload and media handling
- admin — internal administration flows
- catalog — public listings and read-only catalog
- payments — payment flow, providers, webhooks, status handling
- core — shared access, security, config
- db — database wiring and persistence setup
- shared — common utilities

## How new features should be added
When adding a feature:
1. Add API route
2. Call the owning facade
3. Implement service logic
4. Use repository for persistence
5. Return DTOs, not ORM objects

## Access control flow
1. Add permission if needed
2. Add policy if object-level access is needed
3. Enforce it in the service

## Current target architecture for offers and payments
The target shape for the current feature is:

API
  |
  v
Facade
  |
  v
Service
  |
  v
Repository
  |
  v
Database

JWT
  |
  v
AccessContext
  |
  v
Permission
  |
  v
Policy
  |
  v
Service

### Target domain flow
- SpecialOffer currently acts as the local commercial object for the temporary flow
- Payments domain owns payment creation, provider communication, and webhook handling
- Education remains the owner of learning/program enrollment
- Payments and education communicate through facades, not direct imports
- If the temporary flow later grows into a broader offers pattern, a future offers domain can be introduced from this foundation rather than by a premature rewrite

## What must be done next
The next development steps should follow this priority order:

### P0 — foundation
1. Keep the current SpecialOffer as the working foundation for the temporary flow
2. Audit the current implementation before introducing any larger architectural change
   - SpecialOffer
   - Payment
   - payment_service.py
   - payment_repository.py
   - payments/facade.py
   - payments/api/routes.py
   - providers/base.py
   - providers/yookassa.py
   - DTOs
   - the existing enrollment/registration mechanism in education
3. Verify the boundary between payments and education
   - payments should not directly own the education registration logic
   - confirmation should flow through the existing education facade or current registration mechanism
4. Only after the audit, decide whether SpecialOffer needs to evolve into a fuller offers model
   - OfferRegistration
   - capacity control
   - lifecycle/status handling
   - future offers domain structure
5. Add database constraints only when the domain shape is clear and justified by real requirements
   - unique (offer_id, user_id)
   - foreign keys
   - indexes on offer_id, user_id, status

### P0 — payments
1. Keep payments as a separate bounded context
2. Keep Payment as a separate domain object
   - id
   - user_id
   - offer_id
   - provider
   - provider_payment_id
   - amount
   - currency
   - status
   - created_at
   - paid_at
3. Keep the API thin and DTO-driven
4. Keep provider abstraction in place

### P0 — YooKassa integration
1. Replace the current stub provider with a real provider integration
2. Move credentials to environment variables
   - YOOKASSA_SHOP_ID
   - YOOKASSA_SECRET_KEY
   - YOOKASSA_RETURN_URL
3. Trust price and offer_id only from backend logic, never from frontend

### P0 — payment creation flow
Implement the flow:
1. user authenticated via JWT
2. offer is resolved from backend
3. offer validity is checked
4. capacity is checked
5. existing registration is checked
6. payment is created
7. provider returns payment URL
8. frontend receives only the URL

### P0 — webhook flow
Complete the webhook flow for a real provider:
1. receive event from provider
2. verify signature/authenticity (already implemented for the current stub)
3. resolve provider_payment_id
4. validate amount/status
5. mark payment as paid
6. create or activate registration through the education facade
7. ensure idempotency

### P0 — idempotency and safety
The system must be safe against:
- duplicate webhooks
- repeated payment attempts
- parallel registration attempts

The current implementation already protects against duplicate webhook processing and pending-payment reuse.
Continue validating this behavior in integration tests and with real provider payloads.

The core protection is:
- unique registration constraint
- status checks before creating registration
- atomic update or transaction-safe handling

### P0 — transaction handling
Successful webhook processing must be atomic:
- payment becomes paid
- registration becomes active
- both happen as one consistent outcome

If registration cannot be created, the payment state must not be left inconsistent.

## P1 — lifecycle and capacity
1. Introduce offer statuses such as:
   - DRAFT
   - PUBLISHED
   - REGISTRATION_OPEN
   - REGISTRATION_CLOSED
   - COMPLETED
   - CANCELED
   - ARCHIVED
2. Enforce offer lifecycle centrally in the offer service
3. Enforce capacity atomically

## P1 — education integration
After successful payment and registration:
- the offer flow should trigger the existing education flow
- do not create a second parallel enrollment system unless there is no suitable existing mechanism

The target is:
- offers manage registration intent
- education owns learning enrollment

## P1 — frontend
The frontend should:
- show offer details
- show price and availability
- call the payment endpoint
- open the returned payment URL
- show a result page after return

## P1 — errors and observability
Minimum error set:
- OFFER_NOT_FOUND
- OFFER_NOT_PUBLISHED
- OFFER_REGISTRATION_CLOSED
- OFFER_FULL
- ALREADY_REGISTERED
- PAYMENT_NOT_FOUND
- PAYMENT_ALREADY_PAID
- PAYMENT_AMOUNT_MISMATCH
- PAYMENT_PROVIDER_ERROR
- INVALID_WEBHOOK

Minimum logging events:
- offer_payment_created
- payment_provider_created
- payment_webhook_received
- payment_paid
- offer_registration_created
- payment_failed
- payment_webhook_rejected

Logs must never contain secrets or payment details.

## P1 — testing strategy
Required tests:
- payment creation
- successful webhook
- duplicate webhook
- parallel registration attempts
- invalid amount
- closed offer
- full offer

Testing should follow the architecture layers:
- repositories: integration tests
- services: unit tests
- API: API tests

## MinIO security note
The current implementation makes student photos and videos public.
This is acceptable only as a temporary compromise during early development.
Long-term, student media must be moved to private storage and served through authenticated access.

## Review checklist
A PR should be checked for:
- facade-based cross-context access
- no forbidden imports
- thin API layer
- AccessContext usage in services
- policy and permission enforcement
- DTO-based responses where appropriate
- repository persistence only
- no HTTP logic inside services
- no business logic in routers
- no cross-context direct imports
- acknowledgement of the MinIO public media security risk

## Definition of done for the current feature
The current offer/payment feature is considered ready when:
- there is a real offers domain
- offer lifecycle and capacity are enforced
- payment creation uses backend-owned offer data
- webhook verifies provider authenticity
- successful payment creates registration safely
- duplicate events are harmless
- the flow works end to end in a test environment

## Sprint plan for the next step
### 1. Finish provider integration
- connect a real YooKassa SDK or HTTP client
- move shop id and secrets to environment variables
- configure return_url and basic payment parameters

### 2. Make webhook handling real
- accept and verify signatures
- parse payloads
- handle success, failed, and canceled events
- prevent duplicate processing

### 3. Add idempotency
- ensure a repeated webhook does not create a second enrollment
- protect confirm/payment flow from repeated calls

### 4. Ensure transaction safety
- combine payment creation and enrollment handling into one safe operation
- roll back state if something fails

### 5. Add logging
- emit structured logs for:
  - payment_created
  - webhook_received
  - payment_paid
  - payment_failed
  - enrollment_created

### 6. Add basic monitoring
- metrics for payment creation and confirmation
- logging for webhook failures and errors
- simple alerts for critical failures

### 7. Add tests
- unit tests for the service
- webhook tests
- tests for duplicate webhooks
- tests for already paid / already enrolled scenarios

### 8. Verify end-to-end
- test flow:
  - create payment
  - complete payment
  - receive webhook
  - gain access to the course

## Production readiness checklist for payments
### Business logic
- [ ] payment is created only for an active special offer
- [ ] price comes from the offer, not from the frontend
- [ ] the user is resolved from JWT/AccessContext
- [ ] successful payment grants access to the course
- [ ] other courses are not affected

### Security
- [ ] secrets are stored in environment variables or secrets manager
- [ ] webhook is verified by signature
- [ ] unknown or forged events are rejected
- [ ] no sensitive data is exposed in logs

### Reliability
- [ ] webhook handling is idempotent
- [ ] repeated webhook does not create duplicates
- [ ] repeated confirm does not break state
- [ ] payment and enrollment are processed atomically

### Errors and statuses
- [ ] clear errors exist for:
  - OFFER_NOT_FOUND
  - OFFER_NOT_ACTIVE
  - OFFER_EXPIRED
  - PAYMENT_ALREADY_PAID
  - INVALID_WEBHOOK
- [ ] payment and enrollment statuses are explicit and consistent

### Logging and observability
- [ ] structured logs are present
- [ ] exceptions include context
- [ ] success/error metrics are available
- [ ] it is easy to identify which payment is stuck

### Tests
- [ ] unit tests exist
- [ ] webhook tests exist
- [ ] duplicate webhook tests exist
- [ ] successful payment -> course enrollment flow is covered

### Infrastructure
- [ ] real provider is configured
- [ ] real webhook URL is reachable
- [ ] staging/test environment is verified
- [ ] production credentials are prepared

## Short conclusion
If the goal is only to show the flow working, the current implementation is already close to a demo.
If the goal is to run it in production without losing money or user trust, the checklist above is the minimum required path.

## Final target
The project should become a true modular monolith:
- predictable
- extensible
- secure
- easy to evolve
- suitable for gradual decomposition into microservices without a rewrite of core business logic.

## Private Consultations — подробная инструкция (коротко)

Кратко и технически — что должно появиться в проекте и каким образом реализовать.

1) Модели (SQLAlchemy)
  - `ConsultationDay`
    - `id: int`, `date: date` (UNIQUE), `status: enum(OPEN,CLOSED)`,
      `available_from: time`, `available_to: time`, `created_at`, `updated_at`.
  - `ConsultationSlot`
    - `id`, `day_id -> consultation_days.id`, `teacher_id -> users.id`,
      `start_at: timestamptz`, `end_at: timestamptz`,
      `capacity: int` (DB CHECK 1..4), `access_mode: enum(PUBLIC,INVITED)`,
      `status: enum(ACTIVE,CANCELLED,COMPLETED)`, `booking_open_at`, `booking_close_at`, `created_by`, timestamps.
  - `ConsultationInvitation`
    - `id`, `slot_id`, `student_id`, `invited_by`, `status: enum(PENDING,ACCEPTED,DECLINED)`, timestamps.
  - `ConsultationParticipant`
    - `id`, `slot_id`, `student_id`, `source: enum(SELF,INVITATION)`,
      `booking_status: enum(CONFIRMED,CANCELLED)`, `attendance_status: enum(NOT_MARKED,PRESENT,ABSENT)`, timestamps.

2) Бизнес-правила и проверки
  - `start_at < end_at` (CHECK).
  - `capacity` жёстко ограничен DB CHECK 1..4.
  - Пересечение слотов — проверка в `SlotService` (service-level):
    `existing.start_at < new.end_at AND existing.end_at > new.start_at`.
  - `ConsultationDay.available_from/available_to` задают рабочее окно; создание дня не генерирует слоты.
  - Отмена записи меняет `booking_status -> CANCELLED` (не удалять запись).
  - `PENDING` invitation не резервирует место; при `ACCEPTED` создаётся `ConsultationParticipant`.

3) Транзакция бронирования (псевдокод)
  - BEGIN
  - SELECT slot FOR UPDATE
  - проверить day OPEN, slot ACTIVE, booking window
  - проверить дубликат participant
  - посчитать confirmed participants
  - если >= capacity -> raise
  - создать participant (booking_status=CONFIRMED)
  - COMMIT

4) API контракт (минимум)
  - `GET /api/consultations/available?date_from&date_to` — backend возвращает доступные интервалы по дням.
  - `POST /api/consultations/slots/{slot_id}/book` — записаться (текущий user -> student_id).
  - `POST /api/consultations/participants/{id}/cancel` — отменить свою запись.
  - `GET /api/consultations/my`, `GET /api/consultations/invitations` и endpoints для accept/decline.
  - Admin: days/slots/invitations/attendance endpoints (см. TODO ниже).

5) Конфигурация
  - добавить в `core/config.py` ключи: `PRIVATE_CONSULTATION_DEFAULT_DURATION_MINUTES`, `PRIVATE_CONSULTATION_MAX_CAPACITY`, `PRIVATE_CONSULTATION_BOOKING_OPEN_DAYS`, `PRIVATE_CONSULTATION_CANCEL_CUTOFF_HOURS`, `PRIVATE_CONSULTATIONS_ALLOW_OVERLAPPING_SLOTS`.

6) Тесты (обязательные)
  - миграция upgrade/downgrade
  - модельные тесты constraints
  - сервисные тесты: создание слота, overlap rejection, capacity
  - concurrency test: 5 конкурентных booking при capacity=4 -> 4 success, 1 fail

7) Порядок работ (коротко)
  - создать `bak/app/consultations` (models/repos/services/api/facade/specs)
  - сделать SQLAlchemy-модели и bootstrap через `init_db.py`
  - реализовать `DayService`, `SlotService`, `BookingService` (транзакции)
  - реализовать `AvailabilityService` и базовые API-роуты
  - добавить permissions и тесты

TODO (коротко):
- [ ] scaffolding `bak/app/consultations`
- [x] models + `init_db.py` bootstrap
- [ ] repositories + services (day/slot/booking)
- [ ] availability + student/admin API
- [ ] tests (incl. concurrency)
- [ ] config keys + permissions

Не включать сейчас: онлайн-платежи, родительские аккаунты, глобальную проверку конфликтов с другими занятиями, брокеры/Redis, автоматическую генерацию часовых слотов.

---
