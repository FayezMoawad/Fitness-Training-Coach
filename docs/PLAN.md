# Fitness Training Coach — Implementation Plan

This plan implements the MVP workflow defined in `CLAUDE.md`:

> Coach assigns workout → Client completes workout → Client logs results → Coach reviews progress

It follows the tech stack (Next.js/TypeScript frontend, FastAPI/Python backend, PostgreSQL, JWT auth, REST API, Tailwind CSS) and conventions (thin routes, service-layer business logic, Pydantic schemas, backend-only DB access, pytest, feature branches, security rules) mandated by `CLAUDE.md`. **No feature outside this workflow should be built.** Explicitly out of scope for the MVP unless requested later: notifications/emails, social features, exercise libraries with media, payment/billing, analytics dashboards/charts beyond a simple list, mobile apps, multi-coach rosters, workout templates/programs beyond a single assignment, real-time messaging.

Each step below is self-contained, must be completed on its own feature branch (see `CLAUDE.md` branch naming: `feature/<name>`, `fix/<name>`, etc.), and must pass its listed tests before moving to the next step.

---

## Step 0 — Repository & Tooling Setup

**Branch:** `feature/project-scaffolding`

### Objective
Stand up the two-application skeleton (`frontend/`, `backend/`) with working dev servers, linting, and a health-check endpoint, so every later step has a place to add code.

### Scope
Scaffolding only — no business features, no auth, no DB models yet.

### Tasks
- **Backend** (`backend/`):
  - Initialize FastAPI project with `requirements.txt` (fastapi, uvicorn, pydantic, python-dotenv, pytest, httpx for test client).
  - Folder layout:
    ```
    backend/
      app/
        api/            # thin route handlers, grouped by resource
        services/        # business logic
        models/          # SQLAlchemy models (added Step 1)
        schemas/          # Pydantic request/response schemas
        core/             # config, security utils, db session
        main.py           # FastAPI app instantiation, router registration
      tests/
        test_health.py
      .env.example
      pyproject.toml or setup.cfg (pytest config)
    ```
  - Add `GET /health` route returning `{"status": "ok"}`.
  - Add `app/core/config.py` reading settings (e.g., `DATABASE_URL`, `JWT_SECRET`) from environment variables via `pydantic-settings`; never hardcode secrets.
  - Add `.env.example` listing required env vars with placeholder values (no real secrets).
- **Frontend** (`frontend/`):
  - `npx create-next-app@latest` with TypeScript + Tailwind CSS + App Router.
  - Folder layout: `app/`, `components/`, `lib/` (API client helpers), `types/`.
  - Add `lib/apiClient.ts` — a thin fetch wrapper pointing at `NEXT_PUBLIC_API_URL` (env var), used for all backend calls.
  - Add `.env.example` with `NEXT_PUBLIC_API_URL`.
- **Repo root:**
  - `.gitignore` covering `node_modules/`, `.next/`, `__pycache__/`, `.venv/`, `.env`, `*.pyc`.
  - Confirm no `.env` files are ever committed.

### Dependencies
None — first step.

### Tests
| Test | Expected Result |
|---|---|
| `cd backend && pytest` | `test_health.py` passes; `GET /health` returns 200 and `{"status": "ok"}` |
| `cd backend && uvicorn app.main:app --reload` | Server starts without error on default port |
| `cd frontend && npm run lint` | No lint errors |
| `cd frontend && npm run build` | Production build succeeds |
| `cd frontend && npm run dev` | Dev server starts; default page loads at `localhost:3000` |

### Done Criteria
Both apps run independently, health check passes, lint/build are clean, `.env.example` files exist with no real secrets, `.gitignore` in place.

---

## Step 1 — Database Schema & Models

**Branch:** `feature/db-schema`

### Objective
Define the persistent data model for users, workouts, assignments, and logs, with migrations, so all subsequent features have a schema to build on.

### Scope
Schema, ORM models, and migrations only. No API endpoints yet.

### Tasks
- Add SQLAlchemy + Alembic to `backend/requirements.txt`; add `psycopg2-binary` (or `psycopg`) as the PostgreSQL driver.
- `app/core/db.py`: SQLAlchemy engine/session factory reading `DATABASE_URL` from env.
- Define models in `app/models/`:
  - `User`: `id`, `email` (unique), `hashed_password`, `role` (enum: `coach` | `client`), `full_name`, `created_at`.
  - `Workout`: `id`, `coach_id` (FK → User), `name`, `description`, `created_at`.
  - `WorkoutAssignment`: `id`, `workout_id` (FK → Workout), `client_id` (FK → User), `assigned_at`, `status` (enum: `assigned` | `completed`).
  - `WorkoutLog`: `id`, `assignment_id` (FK → WorkoutAssignment), `notes`, `logged_at`, plus structured result fields (e.g., `exercises` as JSON array of `{name, sets, reps, weight}` — keep simple, no separate exercise table for MVP).
- Set up Alembic (`alembic init`), configure `env.py` to read `DATABASE_URL` from settings, generate initial migration from models.
- Add a `tests/conftest.py` fixture that spins up/tears down a test database (or uses a transactional rollback per test) for model-level tests.

### Dependencies
Step 0 (project scaffolding, config loading).

### Tests
| Test | Expected Result |
|---|---|
| `alembic upgrade head` against a fresh local Postgres DB | All tables created without error |
| `alembic downgrade base` | All tables dropped cleanly (reversible migration) |
| Unit test: create `User` with invalid `role` value | Raises validation/DB constraint error |
| Unit test: create `WorkoutAssignment` with non-existent `client_id` | Raises FK constraint error |
| Unit test: `User.email` uniqueness | Second insert with same email fails |

### Done Criteria
Migrations apply and roll back cleanly; constraint tests pass; models importable from `app/models`.

---

## Step 2 — Authentication (JWT)

**Branch:** `feature/jwt-auth`

### Objective
Allow users to sign up and log in as either a coach or client, issuing JWTs for subsequent authenticated requests. Centralize all auth logic per `CLAUDE.md`.

### Scope
Signup, login, token issuance/validation, password hashing. No role-guarded business endpoints yet (that's Step 3).

### Tasks
- Add `passlib[bcrypt]` and `python-jose` (or `pyjwt`) to requirements.
- `app/core/security.py` (centralized): `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`. `JWT_SECRET` and `JWT_EXPIRE_MINUTES` from env via settings — never hardcoded.
- `app/schemas/auth.py`: `SignupRequest`, `LoginRequest`, `TokenResponse` Pydantic models (email format validation, password min length).
- `app/services/auth_service.py`: business logic for signup (check duplicate email, hash password, persist user) and login (verify credentials, issue JWT with `sub`=user id and `role` claim).
- `app/api/auth.py`: thin routes — `POST /auth/signup`, `POST /auth/login` — delegate to `auth_service`.
- `app/core/deps.py`: `get_current_user` FastAPI dependency that decodes the JWT from the `Authorization: Bearer` header and loads the user; raises 401 on missing/invalid/expired token.
- Ensure passwords and tokens are never logged (check no `print`/`logger` calls include them).
- Register `auth` router in `main.py`.

### Dependencies
Step 1 (User model).

### Tests
| Test | Expected Result |
|---|---|
| `POST /auth/signup` with valid coach payload | 201, user created, password not returned in response |
| `POST /auth/signup` with duplicate email | 400/409, no duplicate row created |
| `POST /auth/signup` with weak/malformed input (bad email, short password) | 422 validation error |
| `POST /auth/login` with correct credentials | 200, returns valid JWT; decoding it yields correct `sub`/`role` |
| `POST /auth/login` with wrong password | 401 |
| Protected test route using `get_current_user` with no token | 401 |
| Protected test route with expired/tampered token | 401 |
| DB check: stored password is a bcrypt hash, never plaintext | Confirmed via direct query in test |

### Done Criteria
Full signup/login flow tested via integration tests hitting real endpoints (using `httpx.AsyncClient` or `TestClient`); `pytest` green; no secrets hardcoded; centralized in `core/security.py` and `core/deps.py`.

---

## Step 3 — Authorization & Role-Based Access

**Branch:** `feature/role-authorization`

### Objective
Enforce that coaches and clients can only perform actions appropriate to their role, and only on their own data — on the backend, never trusting the frontend.

### Scope
Reusable authorization dependencies/guards. No new business endpoints (applied to endpoints built in Steps 4–6).

### Tasks
- `app/core/deps.py`: add `require_role(role: str)` dependency factory (e.g., `require_role("coach")`, `require_role("client")`) built on top of `get_current_user`.
- Add ownership-check helpers in relevant services (e.g., `assert_client_owns_assignment(assignment, user)`, `assert_coach_owns_workout(workout, user)`) — used by every endpoint that touches a specific resource.
- Document the authorization pattern in code comments so Steps 4–6 reuse it consistently instead of re-implementing checks.

### Dependencies
Step 2 (JWT auth, `get_current_user`).

### Tests
| Test | Expected Result |
|---|---|
| Call a `require_role("coach")`-guarded test route as a client | 403 |
| Call a `require_role("client")`-guarded test route as a coach | 403 |
| Ownership helper: client A attempts to act on client B's assignment | Raises 403/404 (do not leak existence via inconsistent status codes — pick one convention and document it) |
| Coach attempts to act on another coach's workout | 403/404 per same convention |

### Done Criteria
Reusable role/ownership guards exist and are unit-tested in isolation before being wired into real endpoints.

---

## Step 4 — Core Backend Feature: Coach Assigns Workout

**Branch:** `feature/backend-assign-workout`

### Objective
Enable a coach to create a workout and assign it to a client.

### Scope
`Workout` and `WorkoutAssignment` CRUD (create + list); no update/delete beyond MVP needs.

### Tasks
- `app/schemas/workout.py`: `WorkoutCreate`, `WorkoutResponse`, `AssignmentCreate`, `AssignmentResponse` — validate exercise fields (non-empty name, positive sets/reps, non-negative weight).
- `app/services/workout_service.py`: `create_workout(coach, data)`, `assign_workout(coach, workout_id, client_id)`, `list_assignments_for_client(client)`, `list_workouts_for_coach(coach)`.
- `app/api/workouts.py` (thin routes, all guarded with `require_role("coach")` where appropriate):
  - `POST /workouts` — create a workout.
  - `POST /workouts/{workout_id}/assign` — assign to a client (`AssignmentCreate` body with `client_id`).
  - `GET /workouts` — list coach's own workouts.
  - `GET /assignments` — list assignments (coach: their assigned-out list; used by client route in Step 5/6 as well, filtered by role).
- Validate `client_id` refers to an existing user with `role == "client"` before assigning.

### Dependencies
Steps 1–3 (models, auth, authorization guards).

### Tests
| Test | Expected Result |
|---|---|
| Coach creates a workout | 201, workout persisted with correct `coach_id` |
| Coach assigns workout to valid client | 201, assignment created with `status=assigned` |
| Coach assigns workout to a non-existent/non-client user id | 400/404 |
| Client attempts `POST /workouts` | 403 (role guard) |
| Coach lists their workouts | Only their own workouts returned, not other coaches' |
| Invalid workout payload (missing name, negative reps) | 422 |
| Unit tests for `workout_service` functions in isolation (mock DB session) | Correct behavior without hitting a real DB |

### Done Criteria
Integration tests cover the full create → assign → list flow; unit tests cover service-layer validation; role guard confirmed.

---

## Step 5 — Core Backend Feature: Client Logs Results

**Branch:** `feature/backend-log-results`

### Objective
Enable a client to log results against their assigned workout and mark it completed.

### Scope
`WorkoutLog` create + read, `WorkoutAssignment.status` transition to `completed`.

### Tasks
- `app/schemas/log.py`: `WorkoutLogCreate` (exercises array with sets/reps/weight, optional notes), `WorkoutLogResponse`.
- `app/services/log_service.py`: `log_workout_result(client, assignment_id, data)` — verifies via `assert_client_owns_assignment`, persists `WorkoutLog`, updates assignment `status="completed"`. `get_logs_for_assignment(user, assignment_id)`.
- `app/api/logs.py`:
  - `POST /assignments/{assignment_id}/logs` — guarded `require_role("client")` + ownership check.
  - `GET /assignments/{assignment_id}/logs` — accessible by the owning client or the assigning coach (ownership check covers both cases).
- Ensure no internal DB error detail leaks to the client on failure — return a generic error message and log details server-side only (per `CLAUDE.md` security rule).

### Dependencies
Steps 1–4 (assignments must exist to log against).

### Tests
| Test | Expected Result |
|---|---|
| Client logs results for their own assignment | 201, log persisted, assignment `status` becomes `completed` |
| Client attempts to log results for another client's assignment | 403/404 |
| Client submits malformed log payload (negative reps, missing exercises) | 422 |
| Coach attempts `POST` to logs endpoint | 403 (only clients log results) |
| Coach fetches logs for their own assigned client | 200, correct data |
| Simulated DB failure during log creation | Client receives generic 500 message, no stack trace/SQL text in response body |

### Done Criteria
Full log flow integration-tested; ownership + role checks verified; error responses audited for leakage.

---

## Step 6 — Core Backend Feature: Coach Reviews Progress

**Branch:** `feature/backend-review-progress`

### Objective
Let a coach view a client's logged history/progress across assignments.

### Scope
Read-only aggregation endpoint. No analytics/charting logic in the backend — return structured data only.

### Tasks
- `app/services/progress_service.py`: `get_client_progress(coach, client_id)` — verifies the requesting coach has at least one assignment relationship with that client (ownership-style check), returns assignments + their logs ordered by date.
- `app/schemas/progress.py`: `ClientProgressResponse` (list of assignments, each with nested workout name, status, logs).
- `app/api/progress.py`: `GET /clients/{client_id}/progress`, guarded `require_role("coach")`.

### Dependencies
Steps 1–5 (need assignments and logs to exist).

### Tests
| Test | Expected Result |
|---|---|
| Coach requests progress for their own client | 200, returns all assignments + logs for that client in chronological order |
| Coach requests progress for a client they never assigned anything to | 403/404 (no relationship) |
| Client calls this endpoint | 403 |
| Client with zero completed logs | 200, empty logs array, no error |

### Done Criteria
Integration test confirms correct data shape and scoping; empty-state handled without error.

---

## Step 7 — Frontend: Auth & Layout Shell

**Branch:** `feature/frontend-auth-shell`

### Objective
Build the login/signup UI and a role-aware app shell that all later frontend features plug into.

### Scope
Auth pages, token storage, route protection, base layout/nav. No workout features yet.

### Tasks
- `app/(auth)/login/page.tsx`, `app/(auth)/signup/page.tsx` — forms calling `POST /auth/login` / `POST /auth/signup` via `lib/apiClient.ts`.
- Token storage: prefer httpOnly cookie set by a Next.js route handler (`app/api/auth/*`) that proxies to the backend, so the JWT is never exposed to client-side JS. (If time-constrained for MVP, document the simpler alternative of storing in memory/localStorage with the tradeoff noted — but httpOnly cookie is the recommended default.)
- `middleware.ts` — redirects unauthenticated users away from protected routes (`/coach/*`, `/client/*`) to `/login`.
- Base layout components in `components/` (PascalCase): `AppShell.tsx`, `NavBar.tsx` — nav items conditional on role read from the decoded token/session.
- Client-side auth context/hook: `lib/useAuth.ts` (custom hook, `useAuth` naming convention) exposing current user/role and logout.
- All actual authorization decisions remain server-enforced (Steps 3–6); frontend guards are UX-only, never trusted as the source of truth.

### Dependencies
Step 2 (backend auth endpoints must exist to call).

### Tests
| Test | Expected Result |
|---|---|
| Manual/E2E: submit valid signup form | Redirects to appropriate role dashboard, session established |
| Manual/E2E: submit login with wrong password | Inline error message shown, no redirect |
| Manual/E2E: visit `/coach/dashboard` while logged out | Redirected to `/login` |
| Manual/E2E: log in as client, visit a coach-only page | Nav does not show coach links; direct navigation is still blocked server-side (confirmed via Step 3/4 backend tests, not re-trusted here) |
| `npm run lint` / `npm run build` | Pass |

### Done Criteria
Login/signup work end-to-end against the real backend in local dev; unauthenticated access is redirected; nav reflects role.

---

## Step 8 — Frontend: Coach — Assign Workout UI

**Branch:** `feature/frontend-assign-workout`

### Objective
Give coaches a UI to create a workout and assign it to a client.

### Scope
`/coach/workouts` — create form + list; assignment action.

### Tasks
- `components/WorkoutForm.tsx` — controlled form (name, description, exercises with sets/reps/weight), client-side field validation mirroring backend constraints (non-empty, positive numbers), submits to `POST /workouts`.
- `components/AssignWorkoutForm.tsx` — client picker (fetched from a simple backend endpoint listing the coach's clients, or a minimal client list if roster management is out of scope — reuse existing data, don't invent a new roster feature) + submit to `POST /workouts/{id}/assign`.
- `app/coach/workouts/page.tsx` — Server Component fetching and listing the coach's workouts/assignments; form components as Client Components where interactivity is required.
- Backend validation errors (422/400) surfaced as inline form errors, not silent failures.

### Dependencies
Steps 4, 7.

### Tests
| Test | Expected Result |
|---|---|
| Manual/E2E: coach creates a workout with valid data | Appears in workout list immediately |
| Manual/E2E: coach submits invalid data (negative reps) | Inline validation error, no request sent, or backend 422 surfaced clearly |
| Manual/E2E: coach assigns workout to a client | Assignment appears in assignments list |
| `npm run build` | Succeeds with no type errors |

### Done Criteria
Coach can create and assign a workout entirely through the UI, using only REST calls to the backend (no direct DB access from frontend, per `CLAUDE.md`).

---

## Step 9 — Frontend: Client — Complete & Log Workout UI

**Branch:** `feature/frontend-log-workout`

### Objective
Give clients a UI to view assigned workouts and log their results.

### Scope
`/client/workouts` — list of assignments; log-results form.

### Tasks
- `app/client/workouts/page.tsx` — Server Component listing the logged-in client's assignments via `GET /assignments`.
- `components/LogResultForm.tsx` — per-assignment form (sets/reps/weight/notes per exercise) submitting to `POST /assignments/{id}/logs`; disabled/hidden once `status === "completed"` (or shows the already-logged result read-only).
- Client-side validation mirroring backend constraints; server errors surfaced inline.

### Dependencies
Steps 5, 7.

### Tests
| Test | Expected Result |
|---|---|
| Manual/E2E: client sees only their own assigned workouts | Confirmed against a second seeded client with different assignments |
| Manual/E2E: client logs a result | Assignment status updates to completed in UI after refresh/revalidation |
| Manual/E2E: invalid log submission | Inline error shown |
| `npm run build` | Succeeds |

### Done Criteria
Client can view and log against real assigned workouts end-to-end via the UI.

---

## Step 10 — Frontend: Coach — Review Progress UI

**Branch:** `feature/frontend-review-progress`

### Objective
Give coaches a simple view of a client's logged progress.

### Scope
`/coach/clients/[clientId]/progress` — simple list/table of assignments and logs. No charting library, no over-engineered visualizations (per "keep MVP simple").

### Tasks
- `app/coach/clients/[clientId]/progress/page.tsx` — Server Component calling `GET /clients/{client_id}/progress`.
- Render as a straightforward table/list grouped by assignment: workout name, status, date, logged sets/reps/weight/notes.
- Empty state: "No logged workouts yet" message when the array is empty.

### Dependencies
Steps 6, 7.

### Tests
| Test | Expected Result |
|---|---|
| Manual/E2E: coach views a client with completed logs | Data renders accurately, matching backend response |
| Manual/E2E: coach views a client with no logs | Empty-state message shown, no crash |
| Manual/E2E: coach attempts to view a client not theirs (via direct URL) | Backend 403 surfaces as an error/empty page, not a crash |
| `npm run build` | Succeeds |

### Done Criteria
Coach can review a client's progress end-to-end through the UI, completing the full MVP workflow loop.

---

## Step 11 — Error Handling & Input Validation Hardening

**Branch:** `feature/error-handling-hardening`

### Objective
Audit and standardize error handling across the whole stack so failures are safe, consistent, and non-leaky.

### Scope
Cross-cutting hardening pass over all endpoints and pages built in Steps 2–10. No new features.

### Tasks
- Backend: add a global FastAPI exception handler that catches unhandled exceptions, logs full details server-side, and returns a generic `{"detail": "Internal server error"}` (500) to the client — never raw exception text or SQL errors.
- Backend: audit every endpoint from Steps 2–6 to confirm Pydantic schemas validate all inputs (no endpoint accepts unvalidated raw dicts).
- Frontend: add a shared API error-handling helper in `lib/apiClient.ts` that normalizes error responses and a simple toast/inline-error UI pattern reused across the three forms built in Steps 8–9.
- Confirm consistent HTTP status code conventions across all endpoints (document the chosen convention, e.g., 403 vs 404 for cross-user access, in `docs/PLAN.md` addendum or a short `docs/ERROR_CONVENTIONS.md` if useful).

### Dependencies
Steps 2–10 must exist to audit.

### Tests
| Test | Expected Result |
|---|---|
| Force an unhandled backend exception (e.g., temporarily break DB connection in a test) | Client receives generic 500 message, no internal detail leaked; full detail present in server logs |
| Fuzz each POST endpoint with missing/wrong-typed fields | All return 422 with field-level errors, none return 500 |
| Frontend: simulate a 500 response | User sees a generic friendly error, app does not crash |

### Done Criteria
No endpoint leaks internal error detail; all input is validated; frontend degrades gracefully on API errors.

---

## Step 12 — Security Review Pass

**Branch:** `feature/security-review`

### Objective
Verify the full auth/authz surface and secret handling against `CLAUDE.md`'s security rules before considering the MVP feature-complete.

### Scope
Review and close gaps only — should not require new features if Steps 2–11 were done correctly.

### Tasks
- Confirm `JWT_SECRET`, `DATABASE_URL`, and any other secret are sourced from environment variables in every environment (dev/test/prod), never hardcoded, and `.env` is git-ignored (re-check `git log` for accidental commits).
- Confirm passwords are hashed (bcrypt via passlib) and never logged, returned in API responses, or included in error messages.
- Confirm all DB access uses the ORM (SQLAlchemy) with parameterized queries — grep for any raw string-interpolated SQL and eliminate it.
- Confirm every business endpoint (Steps 4–6) enforces both authentication (`get_current_user`) and authorization (`require_role` / ownership checks) — produce a checklist mapping each endpoint to its guards.
- Confirm JWT expiry is enforced and reasonable (e.g., 30–60 min access token; document the chosen value).
- Run the full backend test suite and specifically re-verify all auth/authz tests from Steps 2–6 pass together (no regressions from later steps).

### Dependencies
Steps 2–11.

### Tests
| Test | Expected Result |
|---|---|
| `pytest` full suite | 100% pass, including all auth/authz tests |
| `grep -R "SECRET\|PASSWORD" backend/ frontend/ --include=*.py --include=*.ts` (excluding `.env.example`) | No hardcoded values found |
| Manual: attempt SQL injection payload in a text field (e.g., workout name `'; DROP TABLE users;--`) | Rejected/stored safely as literal string, no DB error, table intact |
| Manual: inspect a login response and server logs | No plaintext password or raw JWT secret ever appears in logs |
| Endpoint-to-guard checklist review | Every business endpoint has both an auth and an authorization check documented |

### Done Criteria
Checklist complete, no findings outstanding, full test suite green.

---

## Step 13 — Testing & CI

**Branch:** `feature/ci-pipeline`

### Objective
Automate test execution so regressions are caught on every PR, matching the git workflow in `CLAUDE.md`.

### Scope
CI configuration only.

### Tasks
- Add `.github/workflows/ci.yml`:
  - Backend job: spin up a Postgres service container, install deps, run `alembic upgrade head`, run `pytest`.
  - Frontend job: install deps, run `npm run lint`, `npm run build`.
  - Trigger on pull requests targeting `main`.
- Document how to run the same checks locally in a `docs/DEVELOPMENT.md` (or root README section): `pytest` for backend, `npm run lint && npm run build` for frontend.

### Dependencies
Steps 0–12 (needs a working test suite to run).

### Tests
| Test | Expected Result |
|---|---|
| Open a PR against `main` from a feature branch | CI workflow triggers automatically |
| CI run on a clean checkout | Backend and frontend jobs both pass |
| Intentionally break a test locally and push | CI job fails, clearly reporting which test failed |

### Done Criteria
CI is green on the current state of `main`-bound branches; failing tests block merge (document as a branch protection recommendation if repo settings are configurable).

---

## Step 14 — Deployment Readiness (MVP Scope)

**Branch:** `feature/deployment-readiness`

### Objective
Document and verify the minimal steps to build and run the app in a production-like environment, without introducing infrastructure complexity beyond MVP needs.

### Scope
Build/deploy documentation and a production build smoke test. No actual cloud infra provisioning unless the user requests a specific target.

### Tasks
- Document required environment variables for both apps in `docs/DEPLOYMENT.md` (referencing `.env.example` files from Step 0): `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `NEXT_PUBLIC_API_URL`.
- Document backend production run command (e.g., `uvicorn app.main:app --host 0.0.0.0 --port 8000` behind a process manager, or `gunicorn -k uvicorn.workers.UvicornWorker`).
- Document frontend production build/run: `npm run build && npm run start`.
- Document the required deploy-time migration step: `alembic upgrade head` runs before the new backend version serves traffic.
- Keep this minimal — no Docker/Kubernetes/IaC unless explicitly requested later.

### Dependencies
Steps 0–13.

### Tests
| Test | Expected Result |
|---|---|
| `cd backend && uvicorn app.main:app` against a freshly migrated production-config DB | Boots and serves `/health` successfully |
| `cd frontend && npm run build && npm run start` | Boots and serves the app, successfully calling the backend via `NEXT_PUBLIC_API_URL` |
| Fresh clone + follow `docs/DEPLOYMENT.md` verbatim | A developer unfamiliar with the project can get both apps running |

### Done Criteria
A developer can follow `docs/DEPLOYMENT.md` from a clean checkout to a running full-stack app, completing the MVP loop end-to-end (coach signs up → assigns workout → client logs in → completes/logs it → coach reviews progress).

---

## Summary of Step Order & Dependency Chain

```
0. Project Scaffolding
   └─ 1. DB Schema & Models
       └─ 2. JWT Auth
           └─ 3. Role/Ownership Authorization
               ├─ 4. Backend: Assign Workout
               │    └─ 5. Backend: Log Results
               │         └─ 6. Backend: Review Progress
               └─ 7. Frontend: Auth & Layout Shell
                    ├─ 8. Frontend: Assign Workout UI      (needs 4 + 7)
                    ├─ 9. Frontend: Log Workout UI          (needs 5 + 7)
                    └─ 10. Frontend: Review Progress UI     (needs 6 + 7)
                         └─ 11. Error Handling Hardening (needs 2-10)
                              └─ 12. Security Review (needs 2-11)
                                   └─ 13. CI Pipeline (needs 0-12)
                                        └─ 14. Deployment Readiness (needs 0-13)
```

Each step must have its tests passing (`pytest` for backend, `npm run lint`/`npm run build` plus manual/E2E checks for frontend) and be merged via its feature branch before the next dependent step begins.
