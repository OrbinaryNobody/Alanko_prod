# Alanko architecture method book

## Current state
The project has moved from a scattered structure to a context-based modular monolith.
The main bounded contexts are already visible in the codebase:
- education
- accounts
- assessment
- profile
- achievements
- media
- admin
- catalog

The first iteration established the basic architectural boundary, and the second iteration completed the access-model standardization work.
The main results of the work are:
- contexts are treated as independent modules;
- cross-context calls are routed through facades;
- the core layer is reserved for shared infrastructure;
- access checks are now enforced in services via AccessContext -> Policy -> Service;
- domain-specific policies were introduced for education, profile, achievements, assessment, and media.

## Project status
Current iteration: Iteration 3 (Business layer maturity) — nearing completion; the core business-layer structure is already implemented and partially validated.

Completed:
- context separation;
- facade boundaries;
- modular structure;
- shared infrastructure extraction;
- AccessContext adoption in the main services;
- explicit policy-driven access checks for education, profile, achievements, assessment, and media;
- scenario-oriented service split in the education domain;
- DTO-based response shaping for education, profile, achievements, admin, and assessment;
- shared domain-error translation helper for API routes;
- transaction-boundary support through UnitOfWork in the key education flows;
- regression tests covering the main DTO, policy, and transaction flows.

In progress:
- full error-handling unification across the remaining modules;
- broader adoption of domain exceptions in the remaining services;
- final pass on DTO coverage for the remaining endpoints;
- first internal domain events for the main business milestones;
- end-to-end verification of the business-layer flow;
- review remaining facade contracts and argument shapes to avoid forwarding request DTOs through the facade layer;
- ensure media upload flows propagate AccessContext cleanly through facade and service layers;
- close DTO gaps in achievement upload responses and public-facing payload services.

### What should be done to finish Iteration 3
To complete the third iteration, the project should focus on the last consolidation steps:
1. Finish migrating the remaining services and routes to the same domain-exception pattern.
2. Apply DTO-based response shaping consistently to the remaining API endpoints.
3. Extend UnitOfWork usage to the remaining multi-step flows, especially in student-task, admin, and media-related operations.
4. Add a small set of internal domain events for the main successful scenarios, such as program publication, group enrollment, or task completion.
5. Run the relevant regression and API tests, then review the codebase against the architecture rules from this document.

### Definition of done for Iteration 3
Iteration 3 can be considered complete when:
- API routes stay thin and transport-oriented;
- services own the business scenarios and use AccessContext consistently;
- repositories are persistence-only and do not contain business rules;
- domain exceptions replace the remaining service-level HTTP handling;
- DTOs are used for API-facing payloads;
- the main multi-step operations use a transaction boundary;
- the architecture is documented and verified by tests.

## Iteration 2 implementation report
The second iteration focused on making authorization consistent and explicit.
The implemented approach follows the intended architecture chain:
- API receives the request;
- AccessContext is built from auth data;
- Permission dependencies validate the basic capability;
- domain Policy decides whether the user may act on the given object;
- the owning Service contains the business logic and enforces the policy.

The main practical changes were:
- education services now enforce access through context-owned policies for programs, groups, and student tasks;
- profile dashboard access is now checked through a dedicated profile policy;
- achievements, assessment, and media flows now use service-layer policy enforcement as well;
- facades became the stable public contract for cross-context use;
- tests were added to capture the expected policy behavior.

This means the project has reached a stable baseline for access handling and has also started strengthening the business layer through scenario services and DTOs. The next step is to complete the unification of the remaining modules and lock in the business-layer conventions across the whole application.

## Project structure
The project is organized around bounded contexts and shared infrastructure.

Main top-level areas:
- accounts/ — authentication, users, roles, account-related business logic
- education/ — programs, groups, enrollments, tasks, study-related domain logic
- assessment/ — assessment and readiness-related logic
- profile/ — dashboards, student profile views, personal area logic
- achievements/ — achievements and awarded results
- media/ — upload and media handling
- admin/ — internal administrative operations
- catalog/ — public/read-oriented listing over the education domain
- core/ — shared infrastructure and access abstractions
- db/ — database connection and persistence setup
- shared/ — common cross-cutting utilities if needed later

## Project structure template for a new context
A new context should follow this template:

context_name/
    api/
    services/
    repositories/
    models/
    schemas/
    policies/
    exceptions/
    facade.py

This ensures consistency when new domains are introduced.

## Direction of movement
The project is moving toward a modular monolith that can later be evolved into microservices without rewriting business logic.
The target architecture is:
- clear domain ownership;
- explicit context boundaries;
- stable public contracts;
- business logic in services;
- thin API layer;
- consistent access model;
- ability to evolve by extension rather than by breaking existing structure.

## End goal of the architecture
The final target is a system where:
- each business domain is isolated in its own context;
- access is handled through AccessContext -> Permission -> Policy -> Service;
- APIs stay thin and transport-oriented;
- services contain business logic and scenarios;
- repositories only work with data storage;
- contexts communicate only through public facades;
- DTOs separate API from ORM and persistence details;
- complex operations are handled as atomic business operations;
- domain events can be introduced later without major restructuring.

## Context ownership
Every domain object has exactly one owner context.

Examples:
- Education owns:
  - Program
  - Block
  - Task
  - Group
  - Enrollment
- Accounts owns:
  - User
  - Role
  - Authentication
- Media owns:
  - File upload flows
  - Storage-related logic
- Profile owns:
  - Dashboard payloads
  - Personal profile views
- Achievements owns:
  - Achievement entities
  - Achievement assignment logic

If another context needs that object, it must communicate through the owning context facade.

## Core architectural rules

### Rule 1: contexts communicate only through facades
Other contexts must not import services, repositories, models, policies, or schemas from another context directly.

Allowed:
- other_context.facade

Forbidden:
- other_context.services.*
- other_context.repositories.*
- other_context.models.*
- other_context.policies.*
- other_context.schemas.*

### Rule 2: one owner for every domain object
Every business object has exactly one owning context.
If another context needs it, it must interact through the owner facade.
This prevents hidden coupling and context drift.

### Rule 3: core remains infrastructural
The core package must contain shared infrastructure only.
Allowed in core:
- AccessContext
- Permission
- security helpers
- shared access utilities
- common auth/access infrastructure

Not allowed in core:
- specific education rules
- specific assessment rules
- specific profile rules
- domain business logic
- context-specific policies

### Rule 4: business logic stays in the owning context
Domain rules and business scenarios belong to the context that owns the domain.
Example:
- Program rules belong to education
- Achievement rules belong to achievements
- Dashboard logic belongs to profile
- Media logic belongs to media

### Rule 5: API is thin
Routers must only:
- receive the request;
- create or resolve access context;
- call a service or facade;
- return a DTO or response.

Routers must not:
- contain business logic;
- contain SQL;
- contain policy checks;
- contain direct data transformation logic beyond formatting the response.

### Rule 6: services are the center of business logic
Services contain business scenarios.
Examples:
- CreateProgram
- PublishProgram
- TransferStudent
- EnrollStudent
- UploadAchievementMedia

Services must not depend on HTTP, FastAPI, or JWT directly.
They operate on AccessContext and domain objects.

### Rule 7: repositories are simple data access components
Repositories must only work with persistence.
They may provide methods such as:
- create
- update
- delete
- find
- find_by_id
- list

They must not decide whether an action is allowed or whether a business rule is satisfied.

### Rule 8: policies decide whether an action is allowed
Policies answer the question:
- can this user act on this object in this situation?

Examples:
- can this teacher edit this program;
- can this student view this group;
- can this user upload media.

Policies must not contain persistence logic.

### Rule 9: access flow is unified
The access chain must be:
- JWT
- AccessContext
- Permission
- Policy
- Service
- Repository

No business layer should depend directly on raw JWT data.

### Rule 10: do not skip layers
The allowed flow is:
- API -> Facade -> Service -> Repository -> Database

Forbidden flows:
- API -> Repository
- API -> ORM
- Facade -> Database
- Policy -> Repository

### Rule 11: facades are the public API of a context
Everything except the facade is considered internal implementation.
Internal implementation may change.
The facade contract must remain stable.

### Rule 12: new functionality must extend the system, not break it
When adding a feature, the development path should be:
- business requirement
- domain model
- policy
- service
- facade
- API

This preserves architecture and avoids ad hoc coupling.

### Rule 13: contexts should evolve by growth, not by centralization
If a domain becomes large, it should be split into a new context rather than overloaded into an existing one.
Example:
- certificates may become a separate context later;
- exams may become a separate context later.

### Rule 14: architecture matters more than convenience
Even if a direct import is shorter, the correct path is the architectural one.
The project should prefer:
- facade-based access
- explicit ownership
- clear boundaries
- stable contracts

over short-term convenience that weakens the structure.

## Naming conventions
Use consistent names so the structure is easy to follow.

- Service: ProgramCreationService, ProgramPublishService, StudentTransferService
- Policy: ProgramPolicy, GroupPolicy, CanTransferStudent
- Repository: ProgramRepository, GroupRepository, DashboardRepository
- Facade: EducationFacade, AccountsFacade, ProfileFacade
- DTO: ProgramResponse, StudentTaskResponse, DashboardResponse
- Exception: ProgramNotFound, PermissionDenied, StudentAlreadyEnrolled

## Dependency rules
Allowed imports:
- API -> Facade
- Facade -> Service
- Service -> Repository
- Repository -> ORM / DB client
- Service -> Policy
- Service -> Exception

Forbidden imports:
- API -> Repository
- API -> Model
- API -> Policy
- Service -> API
- Repository -> Policy
- Repository -> Service
- Context A -> Context B repository
- Context A -> Context B service
- Context A -> Context B model

## Where new code goes
When adding a new feature, follow this flow.

### If you need a new endpoint
1. Add API route
2. Call facade
3. Implement service logic
4. Use repository if persistence is needed

### If you need access control
1. Add Permission if necessary
2. Add Policy if object-level access is needed
3. Apply it in the service

### If you need persistence
1. Add or extend repository
2. Keep repository data-only
3. Do not put business rules there

## Architecture anti-patterns
Never do the following:
- call repositories from API;
- use HTTPException inside services;
- check JWT inside business logic;
- import another context's repository;
- bypass facade;
- expose ORM outside service;
- duplicate business rules;
- place business logic in routers.

## Iteration goals

### Iteration 1: establish context boundaries
Completed goals:
- identify the main bounded contexts;
- establish facade-based interaction between contexts;
- document the boundary rules;
- prevent direct cross-context service/repository coupling.

### Iteration 2: complete the access model
Target:
- fully standardize access flow through AccessContext -> Permission -> Policy -> Service;
- ensure services receive AccessContext instead of relying on raw auth data;
- make policies explicit and context-owned where needed;
- remove direct dependency on JWT from business services.

### Iteration 3: strengthen the business layer
Target:
- move from large CRUD-style services to scenario-based services;
- introduce domain exceptions instead of HTTPException in services;
- introduce DTOs where service output is exposed to API;
- begin introducing Unit of Work patterns for multi-entity operations;
- prepare the system for domain events later.

## Practical plan for iteration 2

### Goal
Make the access layer consistent across the project.

### Actions
1. Review all services and ensure they receive AccessContext.
2. Make sure each protected action is checked by Permission and Policy.
3. Remove direct dependence on JWT or current_user from services.
4. Keep business rules in the owning context, not in core.
5. Ensure repositories never perform access checks.
6. Keep router logic as thin as possible.

### Completion criteria
- no service depends on raw JWT data;
- all protected operations go through the same access chain;
- authorization is explicit and consistent.

## Practical plan for iteration 3

### Goal
Make the business layer more mature and scenario-oriented, but do it in a way that fits the current modules already present in the workspace.

### Concrete action plan for the current project
1. Start with the education domain as the main focus.
   - Refactor [bak/app/education/services/program_service.py](bak/app/education/services/program_service.py) so it stops acting as a generic catch-all service and is split into scenario-oriented services such as ProgramCreationService, ProgramPublishService, and ProgramArchiveService.
   - Refactor [bak/app/education/services/group_service.py](bak/app/education/services/group_service.py) into a group-management flow focused on enrollment and membership operations.
   - Refactor [bak/app/education/services/student_task_service.py](bak/app/education/services/student_task_service.py) so grading and manual task creation become explicit business scenarios.

2. Introduce domain exceptions in the owning contexts.
   - Add an exceptions package under [bak/app/education](bak/app/education), [bak/app/profile](bak/app/profile), [bak/app/achievements](bak/app/achievements), and [bak/app/media](bak/app/media).
   - Replace service-level HTTPException usage with domain exceptions such as PermissionDenied, ProgramNotFound, StudentAlreadyEnrolled, and GroupIsArchived.
   - Keep API routes responsible only for translating domain failures into HTTP responses.

3. Introduce DTOs for API-facing payloads.
   - Start with the main payloads currently produced in [bak/app/education/api/programs.py](bak/app/education/api/programs.py), [bak/app/education/api/groups.py](bak/app/education/api/groups.py), [bak/app/profile/api/dashboard.py](bak/app/profile/api/dashboard.py), and [bak/app/achievements/api/routes.py](bak/app/achievements/api/routes.py).
   - Move response shaping from routers into service or facade layers.
   - Keep schemas in the owning context, for example under [bak/app/education/schemas](bak/app/education/schemas) or [bak/app/profile/schemas](bak/app/profile/schemas) if they exist.
   - Validate remaining manual response dictionaries in admin, achievements upload flows, and public services to bring them under DTO coverage.

4. Make services independent from HTTP and auth transport.
   - Ensure services accept AccessContext and domain objects rather than relying on FastAPI request objects, JWT payloads, or current-user helpers.
   - Keep [bak/app/core/permissions.py](bak/app/core/permissions.py) and [bak/app/shared/access/access_service.py](bak/app/shared/access/access_service.py) as infrastructure only.

5. Apply Unit of Work for multi-step operations.
   - Start with the education flows that modify several objects at once, such as creating a group, adding a member, and creating enrollments.
   - Add a simple transaction boundary in the education layer first, for example through a dedicated unit-of-work helper under [bak/app/education](bak/app/education).
   - Ensure one business operation becomes one atomic transaction.
   - Validate the new `education.events` module as a first-class context package and keep event imports aligned with package boundaries.

6. Introduce the first internal domain events.
   - Add an initial event bus under [bak/app/core](bak/app/core) or [bak/app/shared](bak/app/shared).
   - Start with simple events such as ProgramPublished, StudentEnrolled, and StudentTransferred.
   - Keep the first implementation internal and synchronous so it does not force a broker dependency yet.

7. Tighten the API boundary.
   - Keep routers in [bak/app/education/api](bak/app/education/api), [bak/app/profile/api](bak/app/profile/api), [bak/app/achievements/api](bak/app/achievements/api), and [bak/app/admin/api](bak/app/admin/api) short and thin.
   - Route all business decisions through facades and services.
   - If a route grows beyond roughly 20 lines or starts containing branching business logic, move that logic into a service.

### Completion criteria
- services are focused on one business scenario each;
- API no longer depends on ORM objects directly;
- domain exceptions replace service-level HTTPException usage;
- DTOs are used for API-facing data;
- complex operations are executed through a transaction boundary;
- the system is prepared for future domain events and later service extraction.

## Architecture Decision Records
To preserve the reasoning behind the architecture, new decisions should be documented in docs/adr/.
Recommended ADRs:
- ADR-001: Why modular monolith
- ADR-002: Why AccessContext
- ADR-003: Why facades
- ADR-004: Why scenario services

## Future roadmap
Possible next steps after the current iterations:
- Iteration 4: optional CQRS for read-heavy flows
- Iteration 5: domain event bus
- Iteration 6: outbox pattern
- Iteration 7: extraction of some contexts into separate services
- Iteration 8: distributed messaging and asynchronous integration

## Definition of Done
A feature is complete only if:
- API is thin;
- AccessContext is used;
- Permission is checked;
- Policy is checked;
- service contains business logic;
- repository contains persistence only;
- DTO is returned if needed;
- architecture rules are respected;
- tests are updated.

## How to review a Pull Request
A PR should be checked against the following:
- context ownership preserved;
- no forbidden imports;
- thin API;
- AccessContext used;
- Permission checked;
- Policy checked;
- no HTTPException in services;
- DTO returned;
- repository contains no business logic;
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
