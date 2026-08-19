# Security Review — Step 12

A review pass over the full auth/authz surface and secret handling, per `CLAUDE.md`'s security rules, before considering the MVP feature-complete. This found no gaps requiring code changes — Steps 2–11 already built the things this step checks for. What follows is the verification record, plus the endpoint checklist the plan asked for.

## Secrets

- `JWT_SECRET`, `DATABASE_URL`, and `JWT_EXPIRE_MINUTES` are sourced exclusively from environment variables (`app/core/config.py`'s `Settings`, a `pydantic-settings` `BaseSettings`) — no hardcoded values anywhere in `app/`.
- `git log --all --diff-filter=A --name-only | grep -iE "^\.env$|/\.env$"` returns nothing — no `.env` file has ever been committed, in this branch or any other. Only `backend/.env.example` and `frontend/.env.example` (placeholder values only, e.g. `JWT_SECRET=change-me`) are tracked.
- `.gitignore` (root, `backend/.gitignore`, `frontend/.gitignore`) all exclude `.env`/`.env.*` while explicitly re-including `.env.example`.
- `grep -rniE "SECRET|PASSWORD" backend/ frontend/ --include=*.py --include=*.ts --include=*.tsx` (excluding `.env.example`, `node_modules/`, `.venv/`) turns up only: config field names (`jwt_secret`, `database_url`), the `hashed_password` column/field name, test-only literal credentials (e.g. `"supersecret1"`, scoped to disposable local test databases), and UI strings like `"Incorrect email or password"`. No real secret value appears anywhere in source.

## Passwords

- Hashed via bcrypt (`passlib.context.CryptContext(schemes=["bcrypt"])`, `app/core/security.py`) before ever touching the database — confirmed by `test_password_stored_as_bcrypt_hash_not_plaintext`, which asserts the stored value `!= "supersecret1"` and starts with `$2b$`.
- Never returned in a response: `UserResponse` (`app/schemas/auth.py`) explicitly whitelists `id`/`email`/`full_name`/`role`/`created_at` — `hashed_password` isn't a field on it, so it physically cannot leak through that schema. Confirmed by `test_signup_valid_coach_returns_201_without_password`.
- Never logged: the only `logger.*` call in the entire backend is the catch-all exception handler in `app/main.py`, which logs `request.method` and `request.url.path` only — never the request body, so a password in a signup/login payload never reaches a log line. The frontend has zero `console.*` calls in application code.

## SQL injection / raw SQL audit

- `grep -rn "execute(\|text(\|f\"SELECT\|f\"INSERT\|..." app/` (excluding tests/migrations) returns nothing — no raw or string-interpolated SQL in application code.
- Every DB read goes through SQLAlchemy's query builder: `db.get(Model, id)` or `db.query(Model).filter(Column == value)` — every one of the ~15 call sites across `auth_service.py`, `workout_service.py`, `log_service.py`, `progress_service.py`, `deps.py` (checked by hand). All parameterized by SQLAlchemy; none build a WHERE clause via string formatting.
- Raw `INSERT`/`text()` calls in `tests/test_models.py` exist only to exercise DB-level constraints directly (e.g. proving a bad `role` value gets rejected by the enum at the DB layer) — they take hardcoded test literals, never user input, and aren't part of the request-handling path.
- **Manual test performed**: signed up, logged in, then created a workout with `name` set to `'; DROP TABLE users;--`. Backend stored and returned it as a literal string (`"name":"'; DROP TABLE users;--"`); a subsequent login with the same credentials still succeeded (200), confirming the `users` table was untouched.

## JWT expiry

- Enforced by `pyjwt`'s standard `exp` claim check on decode (`jwt.decode` in `app/core/security.py` — `verify_exp` is on by default, never disabled) — confirmed by `test_protected_route_with_expired_token_returns_401`, which mints a token with `expires_delta=timedelta(minutes=-5)` and asserts 401.
- Default lifetime: **30 minutes** (`Settings.jwt_expire_minutes`, `.env.example`), within the plan's suggested 30–60 minute range for an access token. Configurable via `JWT_EXPIRE_MINUTES` without a code change.

## Endpoint → guard checklist (Steps 4–6 business endpoints)

| Endpoint | Authentication | Authorization |
|---|---|---|
| `POST /auth/signup` | — (public, by design) | — |
| `POST /auth/login` | — (public, by design) | — |
| `GET /auth/me` | `get_current_user` | — (returns only the caller's own data; nothing to authorize) |
| `POST /workouts` | `get_current_user` (via `require_role`) | `require_role(coach)` |
| `POST /workouts/{workout_id}/assign` | `get_current_user` (via `require_role`) | `require_role(coach)` **+** `assert_coach_owns_workout` (404 if not this coach's workout) **+** client-must-be-a-client check (400 otherwise) |
| `GET /workouts` | `get_current_user` (via `require_role`) | `require_role(coach)` **+** service-layer scoping (`WHERE coach_id = current_user.id`) |
| `GET /assignments` | `get_current_user` | No role guard by design — shared by both roles; authorization is enforced by service-layer scoping instead (`list_assignments_for_coach` filters by `Workout.coach_id`, `list_assignments_for_client` filters by `client_id`, dispatched on `current_user.role`) |
| `POST /assignments/{assignment_id}/logs` | `get_current_user` (via `require_role`) | `require_role(client)` **+** `assert_client_owns_assignment` (404 if not this client's assignment) |
| `GET /assignments/{assignment_id}/logs` | `get_current_user` | No role guard by design — shared by the owning client and the assigning coach; `assert_client_owns_assignment` or `assert_coach_owns_workout` is applied depending on `current_user.role` |
| `GET /clients/{client_id}/progress` | `get_current_user` (via `require_role`) | `require_role(coach)` **+** relationship check (404 if this coach has never assigned this client anything) |

Every business endpoint has at least `get_current_user` (directly, or transitively via `require_role`) plus one of: a role guard, an ownership assertion, or service-layer query scoping — never trusting a client-supplied ID without checking it against `current_user`.

## Full suite re-run

`pytest -v` against a disposable Postgres container: **77/77 passing**, including every auth/authz test from Steps 2–6 run together with everything from Steps 4–11 — no regressions.

## Result

No findings. No code changes were required by this review — it's a paper trail confirming what Steps 2–11 already built correctly, plus the checklist and manual injection test the plan asked for explicitly.
