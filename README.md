# My Fitness Coach Backend

A small, production-conscious foundation for a fitness application API, built with FastAPI and
async SQLAlchemy. It deliberately contains infrastructure and health checks only; authentication,
users, workouts, nutrition, and other product features can be added as independent modules.

## Technology stack

| Technology | Purpose |
| --- | --- |
| Python 3.12+ | Typed, modern application runtime. |
| FastAPI | Async HTTP framework with dependency injection and generated OpenAPI/Swagger docs. |
| Uvicorn | ASGI server that runs the FastAPI application. |
| PostgreSQL | Relational application database. |
| SQLAlchemy 2.0 async | ORM and async database access via `asyncpg`. It plays a role similar to Sequelize, with explicit typed query and session APIs. |
| Alembic | Versioned schema migrations and autogeneration, similar in purpose to Sequelize migrations. |
| Pydantic v2 / pydantic-settings | Data validation and environment-based application configuration. Pydantic schemas fill a role similar to Zod or Joi schemas. |
| pytest / httpx | Test runner and HTTP client used by FastAPI's `TestClient`. |
| Ruff | Fast Python linting and formatting. |
| Docker / Compose | Repeatable application and PostgreSQL development/runtime environment. |

Dependencies and tooling are declared in `pyproject.toml`; a lockfile is not committed in this
starter. Pin and lock dependencies in the deployment workflow when reproducible releases are
required.

## Project structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── health.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── exceptions.py
│   │   ├── exception_handlers.py
│   │   └── logging.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py
│   ├── repositories/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── health.py
│   └── utils/
│       └── __init__.py
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 20261109_0001_initial.py
├── tests/
│   ├── conftest.py
│   └── test_health.py
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

### Important directories and files

- `app/main.py` creates the FastAPI application, adds routers and error handlers, and owns the
  process lifespan. It never creates database tables.
- `app/api/` contains HTTP routing. `router.py` mounts versioned routes; `api/v1/` contains
  endpoint modules.
- `app/services/` contains business operations. The health service demonstrates mapping a
  database failure to a safe application exception.
- `app/repositories/` is where feature-specific database queries belong; it is intentionally empty
  until there is a feature to implement.
- `app/models/` contains SQLAlchemy table mappings. `base.py` provides shared metadata and
  deterministic constraint names.
- `app/schemas/` contains Pydantic request and response types; it is intentionally empty until an
  endpoint has domain input or output to validate.
- `app/core/config.py` loads typed settings from environment variables and `.env`.
- `app/core/database.py` creates the async SQLAlchemy engine, connection pool, and session
  dependency.
- `app/core/exceptions.py` and `exception_handlers.py` define and serialize API errors.
- `migrations/` is Alembic's async migration environment and revision history.
- `tests/` contains API contract tests. Database health tests use a fake session so they do not
  require a running PostgreSQL server.
- `Dockerfile` builds a non-root application image. `docker-compose.yml` runs it with PostgreSQL
  and a persistent volume.
- `.env.example` documents local configuration; copy it to `.env` and replace the example values.

## Architecture and request lifecycle

```text
Client
  |
  v
API Router (FastAPI APIRouter)
  |
  v
Service Layer (business rules and orchestration)
  |
  v
Repository Layer (SQLAlchemy queries)
  |
  v
SQLAlchemy Model (table mapping)
  |
  v
PostgreSQL
```

For a future feature request, the router validates HTTP input and invokes a service. The service
applies business rules and calls a repository. The repository translates the operation into
SQLAlchemy queries against mapped models. Results are returned up the layers and serialized with
Pydantic response schemas. The current health readiness route is intentionally small and calls a
service that runs `SELECT 1`.

### Familiar concepts for Express developers

- A FastAPI `APIRouter` is similar to an Express `Router`: it groups endpoints and is mounted with
  a prefix. FastAPI also inspects type annotations to generate validation and OpenAPI schemas.
- `Depends(...)` is dependency injection, not just middleware. Like Express middleware it can
  provide request-scoped resources, but FastAPI builds and cleans up a dependency graph and injects
  the result directly into route parameters. `get_db_session` yields a session and closes it after
  the request.
- Pydantic models validate and serialize data at the API boundary, much like Joi/Zod schemas. Put
  request and response types in `app/schemas/`; keep SQLAlchemy table classes in `app/models/`.
- SQLAlchemy is an ORM/query toolkit similar in role to Sequelize. An `AsyncSession` is the unit of
  work for database I/O; it is not itself a model instance.
- Alembic records schema changes as ordered migration scripts, similar to Sequelize migrations.
  Migrations—not application startup code—are the only mechanism for changing database schema.

## Database management

`app/core/database.py` creates one async engine and an `async_sessionmaker` for the process. The
pool uses `pool_pre_ping=True`, up to five persistent connections, ten overflow connections, and
a 30-second checkout timeout. FastAPI's `get_db_session` dependency opens one session per request
and closes it reliably. It does not commit automatically: a future service/repository operation
should explicitly define its transaction boundary and commit or roll back as appropriate.

The `/api/v1/health/db` endpoint executes `SELECT 1`. It does not require domain tables, and
returns HTTP 503 with a safe error if PostgreSQL cannot be reached. Tables are never created during
application startup; apply Alembic migrations explicitly.

## Authentication and workouts

Apply the migrations before using account or workout endpoints. Public registration always creates
the `user` role; the request schema does not accept a role. `admin` and `superadmin` are provisioned
only by the explicit development/test seeder. Passwords are stored as Argon2id hashes, and login
returns a short-lived JWT access token. Send it as `Authorization: Bearer <token>`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Register with `email` and `password` |
| `POST` | `/api/v1/auth/login` | Exchange JSON email/password for an access token |
| `GET` | `/api/v1/auth/me` | Return the authenticated account |
| `POST` | `/api/v1/workouts` | Save `workout_data` JSON for the authenticated user |
| `GET` | `/api/v1/workouts` | List the authenticated user's workouts (`limit`, `offset`) |

Workout records are stored separately from account data. Their JSON payload is intentionally
flexible; all list queries are scoped to the token's account.

Configure `AUTH_SECRET_KEY` with a unique secret of at least 32 characters in production and set
`ACCESS_TOKEN_EXPIRE_MINUTES` to the desired access-token lifetime. The development default is
not suitable for deployment. Migrations create the users and workouts tables; the API does not
create tables on startup.

The test-account seeder is explicit and never runs as part of application startup. In a
development/test environment, configure `SEED_SUPERADMIN_EMAIL`, `SEED_SUPERADMIN_PASSWORD`,
`SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `SEED_USER_EMAIL`, and `SEED_USER_PASSWORD`, then run
`python -m app.seed_test_accounts` from `backend/`. It creates missing accounts only and will not
reset existing credentials. Do not use sample seeder values outside local testing.

## Configuration

Settings are loaded by `pydantic-settings` from process environment variables and, for local use,
the `.env` file in the current working directory. Environment variables take precedence.

| Variable | Description |
| --- | --- |
| `APP_NAME` | API title displayed in the generated OpenAPI docs. |
| `APP_ENV` | `development`, `test`, or `production`. |
| `DEBUG` | FastAPI debug behavior; keep `false` in production. |
| `DATABASE_URL` | SQLAlchemy async URL, for example `postgresql+asyncpg://user:password@localhost:5432/fitness_db`. |
| `LOG_LEVEL` | Standard logging level, such as `INFO` or `DEBUG`. |
| `AUTH_SECRET_KEY` | JWT signing secret; use a unique secret of at least 32 characters in production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access-token lifetime in minutes; defaults to `30`. |
| `SEED_*_EMAIL` / `SEED_*_PASSWORD` | Optional per-role credentials required only for the explicit test-account seeder. |
| `POSTGRES_DB` | Compose PostgreSQL database name. |
| `POSTGRES_USER` | Compose PostgreSQL user. |
| `POSTGRES_PASSWORD` | Compose PostgreSQL password. |

`DATABASE_URL` has a no-credential local fallback so importing the application does not require a
secret. Configure a real URL before connecting to a database. URL-encode reserved characters in
credentials; for the Compose example, use a URL-safe password because Compose builds the URL from
`POSTGRES_PASSWORD`. Never commit `.env` or use example credentials in production.

## Error handling and logging

Known `AppException` subclasses carry an HTTP status and stable error code (`NotFoundException`,
`BadRequestException`, `UnauthorizedException`, `ForbiddenException`, and
`ServiceUnavailableException`). FastAPI/Starlette HTTP exceptions, request validation errors, and
unexpected exceptions are normalized to the same shape:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource not found",
    "details": null
  }
}
```

Validation responses include field locations and messages but omit submitted values. Unexpected
errors are logged with method and path, while clients receive only a generic 500 response. Do not
put secrets, tokens, passwords, or sensitive personal data into error messages or logs. In
production, keep `DEBUG=false` so framework debug pages are disabled.

Successful health responses use `{"success": true, "data": {"status": "healthy"}}`.

Logging uses a timestamped, consistently formatted Python logger. Call `configure_logging` from the
application lifespan; services can obtain named loggers with `logging.getLogger(__name__)`.

## Local development

From the `backend/` directory, create and activate a virtual environment and install the app with
its development tools:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
```

Edit `.env` with local values. Start PostgreSQL separately, or use Docker Compose below. Run the
API from this directory so `.env` is discovered:

```bash
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`; Swagger UI is at `http://localhost:8000/docs` and the
OpenAPI schema is at `http://localhost:8000/openapi.json`.

## Docker Compose

Copy and edit the example environment file, then start the services:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Compose waits for PostgreSQL's `pg_isready` check before starting the API. PostgreSQL data persists
in the named `postgres_data` volume. The API connects to the `db` service hostname over the Compose
network. PostgreSQL is published on `127.0.0.1:5432` for local host tools only; it is not bound to
external network interfaces. For Alembic commands run on your host, set `DATABASE_URL` to use
`localhost:5432`. For commands run inside the API container, use the Compose hostname `db:5432`.
The app container runs as a non-root user and has its own HTTP health check.

Run migrations, view logs, and stop the stack with:

```bash
docker compose exec api alembic upgrade head
docker compose logs -f api
docker compose down
```

To remove the database volume as well (this deletes local database data), use
`docker compose down --volumes`.

## Database migrations

The committed initial revision is an empty baseline because the skeleton has no domain tables.
Alembic creates and tracks its own version table when the migration is applied. Once model classes
are added, import their modules from `app/models/__init__.py` so Alembic autogenerate can discover
their metadata.

Run these commands from `backend/` with `DATABASE_URL` configured and PostgreSQL reachable:

```bash
# Create a revision by comparing imported SQLAlchemy metadata with the database.
alembic revision --autogenerate -m "initial migration"

# Apply every revision through the latest one.
alembic upgrade head

# Roll back one revision.
alembic downgrade -1
```

Review every autogenerated migration before applying it. Alembic autogeneration is a proposal, not
a substitute for understanding data migrations or destructive schema changes.

## Tests and code quality

Run the API tests and Ruff from `backend/`:

```bash
pytest
ruff check .
ruff format --check .
```

Tests use FastAPI's synchronous `TestClient` (backed by httpx) and override the database dependency
with a fake async session, so no database or test credentials are needed. To check against a real
PostgreSQL database, set a test-specific `DATABASE_URL`; do not reuse production data.

## Adding a feature endpoint

For example, a future workout feature can add `app/api/v1/workouts.py`, a Pydantic schema under
`app/schemas/`, a service under `app/services/`, and a repository under `app/repositories/`. Keep
the route focused on HTTP concerns and include its router from `app/api/router.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.get("/{workout_id}")
async def get_workout(workout_id: int) -> dict[str, int]:
    """Return a workout after the feature service loads it."""
    return {"workout_id": workout_id}
```

Replace the example return with a service call and a typed response schema when implementing the
feature. Routers are versioned by mounting them below `/api/v1`.

## Adding a database model

Create a SQLAlchemy 2 model that inherits from `app.models.base.Base`, using `Mapped[...]` and
`mapped_column(...)` annotations. Import the model module in `app/models/__init__.py`; then generate
and review a migration with Alembic. Implement feature-specific SQL in a repository and business
rules in a service. Do not call `Base.metadata.create_all()` from application startup.

## Current limitations

- Refresh tokens, password reset, email verification, OAuth, and role-management endpoints are not
  included. Public registration cannot create privileged roles.
- Workout payloads are flexible JSON; exercise-level validation and workout update/delete endpoints
  are not included.
- Tests use an in-memory database double for API contracts and do not replace running the Alembic
  migration against PostgreSQL in a disposable integration environment.
- Dependency ranges are declared but not locked; deployment should use a reviewed lock/build
  process and external secret management.
- Production deployment still needs environment-specific concerns such as TLS termination, secrets,
  observability integration, and a deployment strategy appropriate to the hosting platform.

## commands
From the backend directory, copy .env.example to .env, set local values, then 
start with docker compose up --build -d. 
Apply migrations with docker compose exec api alembic upgrade head; 
run local tests with pytest.# myFitnessCoach
