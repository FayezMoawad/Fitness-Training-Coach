# Development

How to run this project locally, and how to run the same checks CI runs on every PR against `main` (`.github/workflows/ci.yml`).

## Backend

From `backend/`, with a virtual environment activated:

```bash
pip install -r requirements.txt
```

Set the required environment variables (see `backend/.env.example` — copy it to `.env` and fill in real values; `.env` is git-ignored):

- `DATABASE_URL` — e.g. `postgresql+psycopg://postgres:postgres@localhost:5432/fitness_training_coach`
- `JWT_SECRET` — any long random value for local dev (`python -c "import secrets; print(secrets.token_hex(32))"`)
- `JWT_EXPIRE_MINUTES` — defaults to `30` if unset

Run migrations against a running Postgres instance:

```bash
python -m alembic upgrade head
```

Run the test suite (needs `DATABASE_URL`/`JWT_SECRET` set — tests that need a DB skip cleanly if it isn't):

```bash
pytest
```

Run the API locally:

```bash
uvicorn app.main:app --reload
```

### Spinning up a disposable local Postgres for testing

If you don't already have Postgres running locally, a throwaway Docker container works well and matches what CI uses:

```bash
docker run -d --name ftc_pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ftc_dev -p 5432:5432 postgres:16-alpine
```

Tear it down with `docker rm -f ftc_pg` when you're done — it holds no state you need to keep.

## Frontend

From `frontend/`:

```bash
npm install
```

Set `NEXT_PUBLIC_API_URL` (see `frontend/.env.example`, copy to `.env.local`) to point at the running backend — defaults to `http://localhost:8000` if unset.

```bash
npm run lint
npm run build
npm run dev
```

## What CI runs

Every PR against `main` runs `.github/workflows/ci.yml`, two independent jobs:

- **Backend**: spins up a `postgres:16-alpine` service container, installs `backend/requirements.txt`, runs `alembic upgrade head` against it, then `pytest`.
- **Frontend**: installs `frontend/` dependencies, then `npm run lint` and `npm run build`. No backend or database is needed for this job — every page that calls the backend is server-rendered on demand, not statically prerendered at build time.

Both jobs must pass before a PR should be merged. The `pull_request` trigger only runs on PRs targeting `main`, matching this repo's git workflow (feature branches, no direct pushes to `main`) documented in `CLAUDE.md`.

**Branch protection recommendation** (not something a workflow file can configure — set under the repo's Settings → Branches): require the `Backend (pytest)` and `Frontend (lint + build)` status checks to pass before merging into `main`, so a red CI run actually blocks the merge instead of just being visible after the fact.
