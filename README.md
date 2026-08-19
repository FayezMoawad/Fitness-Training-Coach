# Fitness-Training-Coach

[![CI](https://github.com/FayezMoawad/Fitness-Training-Coach/actions/workflows/ci.yml/badge.svg)](https://github.com/FayezMoawad/Fitness-Training-Coach/actions/workflows/ci.yml)

A fitness training coach application designed to help users plan workouts, track progress, and stay consistent with their fitness goals.

## Status
✅ MVP complete — all 15 steps of [`docs/PLAN.md`](docs/PLAN.md) are done. The full workflow (coach assigns workout → client completes it → client logs results → coach reviews progress) works end-to-end through the UI.

- Step 0 — Repository & tooling setup (Next.js + FastAPI scaffolding, health check)
- Step 1 — Database schema & models (PostgreSQL, SQLAlchemy, Alembic migrations)
- Step 2 — JWT authentication (signup, login, current user)
- Step 3 — Authorization & role-based access (role and ownership guards)
- Step 4 — Backend: coach assigns workout
- Step 5 — Backend: client logs results
- Step 6 — Backend: coach reviews progress
- Step 7 — Frontend: auth pages and role-aware app shell
- Step 8 — Frontend: coach assign-workout UI
- Step 9 — Frontend: client log-workout UI
- Step 10 — Frontend: coach review-progress UI
- Step 11 — Error handling & input validation hardening
- Step 12 — Security review pass
- Step 13 — CI pipeline ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
- Step 14 — Deployment readiness ([`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md))

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) to run the project locally.
