# Project Overview

This project is a fitness coaching platform.
The core workflow is:
Coach assigns workout
→ Client completes workout
→ Client logs results
→ Coach reviews progress
The MVP should remain simple.
Do not add features that are not explicitly requested.

# Tech Stack & Architecture Overview
## Tech Stack
- Frontend: Next.js with TypeScript
- Backend: Python FastAPI
- Database: PostgreSQL
- Authentication: JWT
- API: REST
- Styling: Tailwind CSS

## Architecture

The project is divided into two main applications:

- `frontend/` — Next.js application
- `backend/` — FastAPI application

The frontend communicates with the backend exclusively through REST APIs.

The backend is responsible for:
- Authentication
- Authorization
- Business logic
- Database access

The frontend is responsible for:
- UI
- Client-side state
- Form handling
- API communication

Do not move business logic into the frontend.

# Project Conventions & Style Guide

## Code Conventions

### General

- Keep implementations simple.
- Do not over-engineer.
- Prefer existing patterns over introducing new abstractions.
- Do not add dependencies unless necessary.
- Do not create features that are not explicitly requested.

### Frontend

- Use TypeScript.
- Use functional React components.
- Component files use PascalCase.
- Custom hooks use the `useXxx` naming convention.
- Prefer Server Components unless client-side behavior is required.
- Keep reusable UI components in `components/`.

### Backend

- Use Python type hints.
- Follow PEP 8.
- Use `snake_case` for Python variables and functions.
- Keep API routes thin.
- Put business logic in the service layer.
- Use Pydantic schemas for request/response validation.

### Database

- Database access must remain inside the backend.
- Do not access PostgreSQL directly from the frontend.

# Testing Requirements & Patterns

## Testing

All new functionality must include appropriate tests.

### Backend

- Use pytest.
- API endpoints should have integration tests.
- Business logic should have unit tests.
- Authentication and authorization behavior must be tested.

Run backend tests with:

```bash
pytest
```

# Git Workflow & Branch Strategy

## Git Workflow

- `main` is the stable branch.
- Do not make feature changes directly on `main`.
- Create a feature branch for new functionality.
- Use descriptive branch names.

Branch naming:

- `feature/<name>` for new features
- `fix/<name>` for bug fixes
- `refactor/<name>` for refactoring
- `docs/<name>` for documentation

Examples:

- `feature/client-dashboard`
- `feature/jwt-auth`
- `fix/login-validation`

### Commits

Use clear, focused commits.

Prefer:

- `feat: add client dashboard`
- `fix: validate workout input`
- `refactor: simplify auth service`
- `test: add workout completion tests`

Do not mix unrelated changes in the same commit.

Never commit secrets, API keys, passwords, `.env` files, or credentials.

# Security & Compliance Rules

## Security

- Never hardcode secrets, API keys, passwords, or tokens.
- Store secrets in environment variables.
- Never commit `.env` files.
- Validate all user input on the backend.
- Never trust authorization checks performed only on the frontend.
- Backend endpoints must enforce authentication and authorization.
- Passwords must never be stored in plaintext.
- Never log passwords, access tokens, refresh tokens, or sensitive user data.
- Do not expose internal database errors to API clients.
- Use parameterized queries / ORM methods to prevent SQL injection.
- Keep authentication logic centralized.
- Do not weaken security checks just to make tests pass.

Before completing security-sensitive changes, review the affected authentication and authorization paths.