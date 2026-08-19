# Deployment

The minimal steps to build and run this app in a production-like environment. Kept deliberately simple, per `CLAUDE.md` — no Docker/Kubernetes/IaC here unless that's explicitly requested later. For local development instead, see `docs/DEVELOPMENT.md`.

## Environment variables

### Backend (`backend/.env.example`)

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Yes | Must use the `+psycopg` driver suffix (`postgresql+psycopg://user:password@host:5432/dbname`) — the installed driver is `psycopg` (v3), and plain `postgresql://` defaults to `psycopg2`, which isn't installed. |
| `JWT_SECRET` | Yes | A long random value, unique per environment, never reused between dev/staging/prod. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`. Never commit this. |
| `JWT_EXPIRE_MINUTES` | No | Defaults to `30` if unset. |

### Frontend (`frontend/.env.example`)

| Variable | Required | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | No | Defaults to `http://localhost:8000` if unset. In production, point this at the backend's public URL. It's inlined into the browser bundle at build time (the `NEXT_PUBLIC_` prefix), so it must be set *before* `npm run build`, not just at runtime. |

Both apps read these from the real environment — set them however your platform does that (systemd unit, process manager config, PaaS dashboard, etc.). `.env`/`.env.local` are for local development only and are git-ignored; nothing reads them in production unless you choose to deploy them as files, which isn't required.

## Backend: build & run

```bash
cd backend
pip install -r requirements.txt

# Deploy-time migration step -- run before the new version starts serving
# traffic, so the schema is always compatible with the code that's about
# to run.
alembic upgrade head

# Development / simple deployments:
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Behind a process manager, with multiple workers:
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

`gunicorn` isn't in `requirements.txt` (the MVP doesn't need it for local dev or CI) — add it if your deployment target needs a process manager in front of `uvicorn`.

## Frontend: build & run

```bash
cd frontend
npm install
npm run build
npm run start
```

`npm run start` serves the production build on port 3000 by default (`-p <port>` to change it).

## Order of operations for a deploy

1. Run backend migrations (`alembic upgrade head`) against the target database, **before** the new backend version starts serving traffic.
2. Start (or roll) the backend.
3. Build and start (or roll) the frontend, pointed at the backend via `NEXT_PUBLIC_API_URL`.

The frontend has no database of its own and no migration step — it only ever talks to the backend over REST (`lib/apiClient.ts`), never the database directly, per `CLAUDE.md`'s architecture rules.

## Verifying a deploy

- `GET /health` on the backend should return `{"status": "ok"}`.
- Visiting the frontend's root URL should render the landing page, and the full MVP loop should work end-to-end: sign up as a coach, sign up as a second account as a client, coach assigns a workout, client logs in and logs a result, coach reviews the client's progress.
