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

The architecture is implemented around:
- thin API routers
- facades as public context contracts
- services owning business scenarios
- repositories owning persistence
- AccessContext-based authorization
- DTOs shaping API payloads

## MinIO access model
The current code splits MinIO storage into public and private buckets:
- public:
  - `alanko-videos`
  - `alanko-student-photos`
- private:
  - `alanko-certificates`
  - `alanko-documents`

This split is implemented in:
- `bak/app/db/minio_client.py`
- `bak/app/services/file_service.py`
- `bak/app/core/minio_init.py`

Important security note:
- student photos and videos are currently stored in public buckets and served by direct public URLs.
- that is a security hole for student media and must be fixed in a future iteration.
- the safer design is to keep student media private and serve it through authenticated access or a secure proxy.

## Current architecture rules
### Rule 1: contexts communicate only through facades
Allowed:
- `other_context.facade`

Forbidden:
- `other_context.services.*`
- `other_context.repositories.*`
- `other_context.models.*`
- `other_context.policies.*`
- `other_context.schemas.*`

### Rule 2: one owner for every domain object
A domain object has exactly one owning context.
Other contexts must use the owner facade to access it.

### Rule 3: core remains infrastructural
`core/` contains shared infrastructure only:
- access abstractions
- permissions
- security helpers
- auth helpers

Not allowed in `core/`:
- domain business rules
- context-specific policies

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
- `API -> Facade -> Service -> Repository -> Database`

Forbidden:
- `API -> Repository`
- `API -> ORM`
- `Facade -> Database`
- `Policy -> Repository`

## Project structure
Top-level areas:
- `accounts/` — authentication, users, roles
- `education/` — programs, groups, enrollments, tasks
- `assessment/` — assessments and readiness logic
- `profile/` — dashboard and personal views
- `achievements/` — achievements and award logic
- `media/` — upload and media handling
- `admin/` — internal administration flows
- `catalog/` — public listings and read-only catalog
- `core/` — shared access, security, config
- `db/` — database wiring and persistence setup
- `shared/` — common utilities

## New code flow
When adding a feature:
1. Add API route
2. Call the owning facade
3. Implement service logic
4. Use repository for persistence

## Access control flow
1. Add permission if needed
2. Add policy if object-level access is needed
3. Enforce it in the service

## MinIO security note
The current implementation makes student photos and videos public.
This is acceptable only as a temporary compromise during early development.
Long-term, student media must be moved to private storage and served through authenticated access.

## Practical project status
The current project is centered on completing the business-layer consolidation:
- context boundaries are in place
- access flow is standardized
- services and facades are established
- DTOs are used in many payloads
- MinIO public/private bucket split exists, but media security needs refinement

## What remains
To finish the current iteration:
- unify error handling across modules
- extend domain exceptions to remaining services
- complete DTO coverage for public and achievement payloads
- enforce UnitOfWork for multi-step operations in education and media
- fix the student media public-bucket security gap
- run end-to-end regression and API tests

## Review checklist
A PR should be checked for:
- facade-based cross-context access
- no forbidden imports
- thin API layer
- AccessContext usage in services
- permission and policy enforcement
- DTO-based responses where appropriate
- repository persistence only
- no HTTP logic inside services
- acknowledgement of the MinIO public media security risk

- cross-context call uses facade.

## Architecture diagram

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

## How to add a new bounded context
When creating a new context:
1. Create the context folder and subfolders: api, services, repositories, models, schemas, policies, exceptions
2. Add facade.py
3. Register the router in the main app
4. Expose the public contract through the facade
5. Keep internal implementation private

## Testing strategy
A simple testing strategy should follow the architecture layers:
- Repositories: integration tests
- Services: unit tests
- API: API tests

## Final target
The project should become a true modular monolith:
- predictable;
- extensible;
- secure;
- easy to evolve;
- suitable for gradual decomposition into microservices without a rewrite of core business logic.
