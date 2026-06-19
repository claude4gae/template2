# AGENTS.md

## Scope
These rules apply to `apps/api/**`.

## Domain App Boundary
- Domain app path: `apps/api/api/<feature>` (`api.<feature>`)
- Data movement table apps are the only nested domain app exception:
  - Namespace path: `apps/api/api/data_movement/<table_name>` (`api.data_movement.<table_name>`)
  - `<table_name>` must match the physical target table name.
  - Each table app owns only its table models, migrations, loader services, tests, and management commands.
  - Shared ingestion helpers for these apps live under `apps/api/api/data_movement/common`.
- Allowed files/folders only:
  - `apps.py`, `models.py`, `urls.py`, `callback_urls.py` (auth only)
  - `views.py`, `serializers.py`, `selectors.py`, `permissions.py`, `admin.py`, `tests.py`
  - `services/`, `migrations/`, `management/commands/`
- No new backend folders outside approved paths.
- Max depth 2, except `services/`, `migrations/`, `management/commands/`.
- Shared/infrastructure packages only:
  - `apps/api/api/common`
  - `apps/api/api/data_movement/common`
  - `apps/api/api/auth`
  - `apps/api/api/rag`
  - `apps/api/api/management`

## Cross-Feature and Responsibilities
- Cross-feature imports allowed only through other feature's `services/__init__.py` facade or `selectors.py`.
- `views.py`: HTTP only.
- `serializers.py`: schema + validation only.
- `permissions.py`: DRF permissions only.
- `services/*`: business logic, writes, transactions, external calls.
- `selectors.py`: read-only ORM queries only.
- `models.py`: schema + pure domain rules only.
- Views/services must not execute direct read ORM queries; use selectors.

## Routing and API Shape
- Use versioned API prefix `/api/v1/<route-scope>/...`.
- Exception: auth callbacks under `/auth/` (`api.auth.callback_urls`).
- Global routing only in `apps/api/api/urls.py` as include registry.
- Feature `urls.py` must define relative paths only.
- Routes contain no business logic.

## Model and DB Rules
- Fields: snake_case.
- Models: singular PascalCase.
- Every model sets `db_table = "<feature>_<entity>"`.
- Data movement table apps set the primary imported table model `db_table` exactly to `<table_name>`.
  Supporting tables may append a clear suffix, for example `<table_name>_load_job`.
- Primary key: `id` (BigAutoField), UUID only when externally required.
- Timestamps timezone-aware UTC (`created_at` required; `updated_at`, `deleted_at` optional).
- Index/constraint naming:
  - `idx_<table>_<cols>`
  - `uniq_<table>_<cols>`
  - max length <= 30
  - apply deterministic abbreviation/suffix rule
- Full naming map/playbook is maintained in `create-django-feature` skill.

## Safety and Readability
- Wrap multi-step writes in `transaction.atomic()`.
- No writes in selectors/models.
- Prefer explicit, linear, small single-purpose code.
- Keep functions/classes small and single-purpose where practical (about 30–50 lines).
- Add type hints and Korean docstrings to public services/selectors.

## Testing and Migrations
- Update/add tests when business logic changes.
- Prefer service/selector tests; keep view tests minimal.
- Never edit applied migrations.
- Tests must not directly import other domain internal modules.
- Domain-specific commands stay in each feature app.
- Shared commands use service/selector facade only.
- Backend tests/commands must run in Docker Compose `api` container.
- Static agent audit scripts may run on the host because they do not execute Django runtime code.
- After backend domain boundary/import/view/selector changes, run or recommend `npm run agent:audit:api-boundary`.
- Detailed execution sequence and commands are in `django-test-migration-flow` skill.

## Offsite Development
- Assume offsite/local development may not have corporate network access.
- Never hardcode intranet URLs.
- External dependency URLs must remain env-driven.
- If auth/RAG/assistant/mail contract changes, local mock/dev wiring must stay runnable.
- Detailed offsite sync steps are in `offsite-dev-contract-sync` skill.
