# Error & Status Code Conventions

This documents the status-code and error-handling conventions used across the backend and frontend, established piecemeal in Steps 2–10 and consolidated here per Step 11. New endpoints and forms should follow these rather than inventing new patterns.

## Backend status codes

| Code | Meaning | Where |
|---|---|---|
| **401** | Not authenticated — missing, malformed, or expired token. | `get_current_user` (`app/core/deps.py`) |
| **403** | Authenticated, but the wrong *kind* of user entirely (e.g. a client calling a coach-only route). Nothing to leak — the caller already knows their own role. | `require_role` (`app/core/deps.py`) |
| **404** | The requested resource doesn't exist, *or* it exists but belongs to someone else. These two cases are deliberately indistinguishable: if a caller could tell "403 forbidden, this exists but isn't yours" apart from "404 not found", that distinction itself would leak which resource IDs belong to other users. | `assert_coach_owns_workout` / `assert_client_owns_assignment` (`app/services/authorization.py`); reused by `workout_service`, `log_service`, `progress_service` for both "doesn't exist" and "not yours" cases |
| **400** | The request is structurally valid but references something invalid in a way that isn't an ownership question — e.g. `client_id` doesn't refer to an existing user with `role=client`. | `workout_service.assign_workout` |
| **422** | Request body fails Pydantic schema validation (missing/wrong-typed/out-of-range fields). Handled automatically by FastAPI — every POST endpoint takes a Pydantic model, never a raw dict, so this is enforced uniformly. | All `POST` routes |
| **500** | Anything unhandled — a DB failure, a bug, whatever. Always the generic body below; never raw exception text, SQL, or a stack trace. Full detail goes to the server log only. | Global `Exception` handler in `app/main.py` |

```json
{ "detail": "Internal server error" }
```

## Frontend handling

- `lib/apiClient.ts` (server-side backend calls) and `lib/formSubmit.ts` (client-side calls to our own `/api/*` proxy routes) both surface the backend's `detail` field **only when it's a plain string**. FastAPI's 422 body carries `detail` as a structured array of field errors, not a string — that's intentionally *not* surfaced verbatim; forms fall back to a generic message ("Something went wrong. Please try again.") for that case rather than rendering `[object Object]` or similar.
- Every form (`LoginForm`, `SignupForm`, `WorkoutForm`, `AssignWorkoutForm`, `LogResultForm`) uses the shared `submitJson` helper and `FormError` component, so a network failure, a 4xx, or a 500 all resolve to the same inline, non-crashing error state — never an unhandled promise rejection or a blank page.
- Client-side field validation (required names, positive numbers, etc.) mirrors the backend's Pydantic constraints so most invalid input never reaches the network — but the backend remains the actual source of truth; nothing here is trusted as validation on its own.

## Why this split (400 vs 404 vs 403)

The guiding rule: **status codes must not leak more than the caller is entitled to know.**

- A role mismatch (403) leaks nothing — you already know your own role.
- An ownership mismatch (404) would leak "this ID exists and belongs to someone else" if it returned 403 instead — so both "doesn't exist" and "not yours" collapse into the same 404.
- An invalid `client_id` on assignment (400) isn't an ownership question at all — the coach is allowed to know a `client_id` doesn't resolve to a client, since they supplied it as part of a request they're authorized to make.
