# Production Runbook

## Pre-deploy checklist

- Ensure migrations are up-to-date:
  - `alembic upgrade head`
- Confirm service checks on target environment:
  - `GET /health/live`
  - `GET /health/ready`
  - `GET /health/deep`
- Confirm required environment variables:
  - `APP_ENV=production`
  - `CORS_ORIGINS=https://your-frontend.example.com`
  - `DB_REVISION_GUARD=true`
  - `ENABLE_METRICS=true`
  - `ERROR_BUDGET_PERCENT=1.0`
  - `ERROR_BUDGET_MIN_REQUESTS=100`
  - `ALERT_WEBHOOK_URL=https://...` (optional)

## Canary rollout

1. Deploy to 10% traffic.
2. Observe `/metrics` for 10-15 minutes:
   - `error_rate_percent <= 1.0`
   - stable `avg_latency_ms` on key routes.
3. If healthy, increase to 50%, then 100%.

## Rollback plan

1. Route traffic to previous stable release.
2. Validate with:
   - `GET /health/ready`
   - `GET /health/deep`
3. If rollback required due to migration mismatch, restore DB snapshot and re-run:
   - `alembic upgrade head` on fixed artifact.

## Backup and restore drill

- Backup:
  - PostgreSQL: `pg_dump -Fc <db_name> > backup.dump`
- Restore (staging drill):
  - `pg_restore -d <target_db> backup.dump`
- Validate restored environment with health endpoints and smoke tests.

## Load smoke validation

Run against deployed environment:

```bash
python scripts/load_smoke.py --base-url https://your-api.example.com --concurrency 20 --requests-per-worker 25
```

Expected:
- Failure count near zero.
- Stable RPS and no readiness degradation.

## Changelog Notes

### 2026-02-14 - Signals APIs migrated into AI module

- Canonical signal endpoints are now served from AI:
  - `GET /ai/signals`
  - `GET /ai/signals/rush-hour`
  - `GET /ai/signals/slot-suggestions`
  - `GET /ai/signals/reorder-prompts`
- Legacy `GET /signals/*` routes were removed and should return `404`.
- Post-deploy verification:
  - Confirm all `/ai/signals*` endpoints return `200` with a `signals` payload.
  - Confirm `/signals` and `/signals/*` return `404`.
