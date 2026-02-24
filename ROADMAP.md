# Nao Medical Roadmap

This roadmap tracks the next implementation steps to improve reliability, quality, security, and product readiness.

## Current Baseline (as of 2026-02-24)

- Frontend live URL is reachable: `https://nao-medical-five.vercel.app` (`200`)
- Backend root URL returns `404`, but health/docs are reachable:
  - `https://nao-medical-t187.onrender.com/health` (`200`)
  - `https://nao-medical-t187.onrender.com/docs` (`200`)
- Most documentation links are healthy.
- Some endpoints are expected to be protected/private (`403`) or placeholder/local-only (`000`).

## Guiding Goals

1. Improve deployment reliability and operational clarity.
2. Build a solid quality gate with tests and CI checks.
3. Raise security posture for real-world usage.
4. Improve real-time UX and observability.

## Phase 1: Stability and Documentation Hygiene (Week 1)

### Deliverables

- [x] Add backend root route (`GET /`) returning basic API metadata and links.
- [x] Fix README live backend link to a working endpoint (`/health` or `/docs`).
- [x] Remove or correct unconfigured `www` domain usage in docs/env examples.
- [x] Add `backend/.env.example` and `frontend/.env.example`.
- [x] Add startup validation for required environment variables per mode.
- [x] Add automated link-check workflow in CI using `curl`.

### Exit Criteria

- [x] All documented production links return expected statuses.
- [x] New contributors can boot locally using only `.env.example` files.
- [x] CI fails on broken documentation links.

## Phase 2: Test Coverage and CI Quality Gates (Week 2)

### Deliverables

- [ ] Add backend tests for:
  - [ ] Conversation creation/retrieval
  - [ ] Text message flow
  - [ ] Audio finalize flow (with provider mocked)
  - [ ] Search endpoint
  - [ ] Summary endpoint
- [ ] Add frontend API integration tests for major user flows.
- [ ] Enforce lint + typecheck + tests in CI before merge.
- [ ] Add test data fixtures and deterministic mocks for AI provider responses.

### Exit Criteria

- [ ] Test suite runs reliably in CI.
- [ ] Critical flows have regression protection.
- [ ] Merge pipeline blocks on lint/type/test failures.

## Phase 3: Security and Production Hardening (Week 3)

### Deliverables

- [ ] Add authentication for doctor/patient access flows.
- [ ] Add authorization checks for conversation/message access.
- [ ] Add rate limiting for key API endpoints.
- [ ] Add stricter request validation and payload limits.
- [ ] Define production DB path (managed Postgres) and migrations strategy.
- [ ] Improve secret/config handling for deployment environments.

### Exit Criteria

- [ ] Unauthorized access to conversation data is blocked.
- [ ] Abuse controls in place for expensive endpoints.
- [ ] Production deployment path is documented and repeatable.

## Phase 4: Real-Time UX and Observability (Week 4)

### Deliverables

- [ ] Replace or augment polling with WebSocket/SSE for message updates.
- [ ] Add resilient retry/error handling for transient AI provider failures.
- [ ] Add structured logging and request IDs.
- [ ] Add basic monitoring metrics (latency, error rates, provider failures).
- [ ] Improve user-facing error states in frontend.

### Exit Criteria

- [ ] Perceived latency improves for live chat updates.
- [ ] Operational issues are visible through logs/metrics.
- [ ] Frontend degrades gracefully when dependencies fail.

## Backlog (Post-Phase 4)

- [ ] Role-based audit trail for medical/legal compliance requirements.
- [ ] Multi-format audio support beyond `audio/webm`.
- [ ] Background job queue for heavy summarization/transcription.
- [ ] Localization improvements and language quality evaluation loop.
- [ ] Usage analytics and product funnel instrumentation.

## Working Rules

- Keep changes small and shippable.
- Update this file in each PR by marking completed checkboxes.
- Include date-stamped notes for scope changes.

## Change Log

- 2026-02-24: Initial roadmap created from link audit + project improvement planning.
- 2026-02-24: Phase 1 implemented (root endpoint, docs/env cleanup, mode-aware config validation, CI link checks).
