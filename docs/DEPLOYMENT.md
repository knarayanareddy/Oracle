# 🚀 ORACLE — Deployment Guide

> **Navigation:** [← Back to README](../README.md) | [Development](DEVELOPMENT.md) | [Database](DATABASE.md)

Production deployment guide for Supabase (EU), Railway (FastAPI), and Vercel (frontend).

---

## Table of Contents

1. [Deployment Overview](#1-deployment-overview)
2. [Supabase Setup (EU Frankfurt)](#2-supabase-setup-eu-frankfurt)
3. [Railway Setup (FastAPI)](#3-railway-setup-fastapi)
4. [Vercel Setup (Frontend)](#4-vercel-setup-frontend)
5. [Edge Function Deployment](#5-edge-function-deployment)
6. [CI/CD Pipeline](#6-cicd-pipeline)
7. [Post-Deployment Checklist](#7-post-deployment-checklist)
8. [Rollback](#8-rollback)

---

## 1. Deployment Overview

```
┌──────────────────────────────────────────────────────┐
│  PRODUCTION DEPLOYMENT                                │
│                                                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Vercel  │  │   Railway    │  │   Supabase    │  │
│  │          │  │              │  │   (Frankfurt) │  │
│  │ Frontend │  │  FastAPI     │  │               │  │
│  │ React    │  │  Python 3.12 │  │  PostgreSQL   │  │
│  │          │  │  2 workers   │  │  Edge Funcs   │  │
│  │ Auto-dep │  │  Auto-dep    │  │  Realtime     │  │
│  │ on push  │  │  on push     │  │  Storage      │  │
│  └────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
│       │               │                  │           │
│       └───────────────┴──────────────────┘           │
│                       │                               │
│              CI/CD on GitHub Actions                  │
│              (security → typecheck → tests → deploy)  │
└──────────────────────────────────────────────────────┘
```

**Order of deployment:** Supabase → Railway → Vercel (each depends on the previous).

---

## 2. Supabase Setup (EU Frankfurt)

### Create Project

1. Go to [supabase.com](https://supabase.com) → New Project
2. **Region:** `Frankfurt (eu-central-1)` — required for GDPR/AVG compliance
3. **PostgreSQL version:** 15.x
4. **Plan:** Free tier sufficient for hackathon

### Get Credentials

From **Project Settings → API**:

| Value | Env Var |
|-------|---------|
| Project URL | `SUPABASE_URL` |
| anon public key | `SUPABASE_ANON_KEY` |
| service_role key | `SUPABASE_SERVICE_ROLE_KEY` |
| JWT secret | `SUPABASE_JWT_SECRET` |

### Apply Migrations

```bash
# Link to remote project
supabase link --project-ref your-project-ref

# Push migrations
supabase db push

# Or reset with seed data (for fresh setup)
supabase db reset --linked
```

### Configure Database Settings

```sql
-- Set the custom GUCs for pg_cron jobs
ALTER ROLE postgres SET app.supabase_functions_url = 'https://your-project.functions.supabase.co';
ALTER ROLE postgres SET app.fastapi_url = 'https://oracle-api.railway.app';
ALTER ROLE postgres SET app.service_role_key = 'your-service-role-key';
ALTER ROLE postgres SET app.demo_user_id = '00000000-0000-0000-0000-000000000001';
```

### Enable Realtime on Tables

Supabase Dashboard → Database → Replication → enable for:
- `oracle_feed.transparency_feed_events`
- `oracle_simulation.simulation_rounds`
- `oracle_simulation.simulations`
- `oracle_portfolio.trades`

### Create Storage Buckets

The `20260613_storage_buckets.sql` migration creates them automatically. Verify in
Dashboard → Storage that all 5 buckets are **private** (public = false).

---

## 3. Railway Setup (FastAPI)

### Create Service

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select the `Oracle` repository
3. **Root directory:** `apps/api`
4. **Builder:** Dockerfile (auto-detected from `apps/api/Dockerfile`)

### Configure Environment Variables

Railway → Variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-...
POLYGON_API_KEY=...
ALPHA_VANTAGE_API_KEY=...
NEWS_API_KEY=...
FRED_API_KEY=...
FASTAPI_SECRET_KEY=your-strong-secret
MARKET_DATA_PROVIDER=auto
CORS_ORIGINS=https://oracle.vercel.app
RATE_LIMIT_PER_MINUTE=100
ORACLE_MAX_AGENTS=1000
ORACLE_MAX_ROUNDS=40
ORACLE_SIGNAL_REFRESH_MINUTES=15
```

### Health Check

Railway will use the Dockerfile `HEALTHCHECK` command hitting `GET /health`.
Verify it returns 200 after deployment:

```bash
curl https://oracle-api.railway.app/health
# → {"status": "healthy", ...}
```

### Custom Domain (Optional)

Railway → Settings → Networking → Generate Domain → `oracle-api.railway.app`

---

## 4. Vercel Setup (Frontend)

### Import Project

1. Go to [vercel.com](https://vercel.com) → New Project → Import from GitHub
2. Select the `Oracle` repository
3. **Root directory:** `apps/web`
4. **Build command:** `pnpm build` (auto-detected from `vercel.json`)
5. **Output directory:** `dist`

### Configure Environment Variables

Vercel → Project Settings → Environment Variables:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_DEMO_USER_ID=00000000-0000-0000-0000-000000000001
VITE_DEMO_MODE=true
VITE_FASTAPI_URL=https://oracle-api.railway.app
```

> ⚠️ **NEVER** add `VITE_SUPABASE_SERVICE_ROLE_KEY` — any `VITE_` prefix is exposed to the browser.

### Deploy

Push to `main` branch triggers auto-deploy. First deploy will build and serve at
`https://oracle.vercel.app`.

---

## 5. Edge Function Deployment

```bash
# Deploy all functions
supabase functions deploy swarm-trigger --no-verify-jwt
supabase functions deploy autopilot-loop --no-verify-jwt
supabase functions deploy signal-ingest --no-verify-jwt
supabase functions deploy memory-update --no-verify-jwt
supabase functions deploy trade-execute --no-verify-jwt

# Set function secrets (shared via Supabase env)
supabase secrets set FASTAPI_URL_LOCAL=https://oracle-api.railway.app
supabase secrets set FASTAPI_SECRET_KEY=your-strong-secret
supabase secrets set DEMO_USER_ID=00000000-0000-0000-0000-000000000001
```

---

## 6. CI/CD Pipeline

The pipeline (`.github/workflows/ci.yml`) runs on every push/PR:

```
push/PR to main
    │
    ▼
┌──────────────────┐     FAIL → block merge
│ Security Scan    │     (check_no_service_key.sh)
└────────┬─────────┘
         │ PASS
         ▼
┌──────────────────┐     FAIL → block merge
│ TypeScript Check │
└────────┬─────────┘
         │ PASS
         ▼
┌──────────────────┐     FAIL → block merge
│ Python Tests     │     (pytest, 40 tests)
└────────┬─────────┘
         │ PASS (main only)
         ▼
┌──────────────────────────────────────┐
│ Deploy Frontend (Vercel)             │
│ Deploy API (Railway)                  │
└──────────────────────────────────────┘
```

### Required GitHub Secrets

| Secret | Used By |
|--------|---------|
| `VERCEL_TOKEN` | Frontend deploy |
| `VERCEL_ORG_ID` | Frontend deploy |
| `VERCEL_PROJECT_ID` | Frontend deploy |
| `RAILWAY_TOKEN` | API deploy |
| `RAILWAY_PROJECT_ID` | API deploy |

---

## 7. Post-Deployment Checklist

After all three services are deployed, verify:

```bash
# 1. API health
curl https://oracle-api.railway.app/health
# Expected: {"status": "healthy", ...}

# 2. Frontend loads
curl -I https://oracle.vercel.app
# Expected: 200 OK

# 3. Edge Functions respond
curl -X POST https://your-project.functions.supabase.co/swarm-trigger \
  -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"seed_text": "test deployment trigger"}'
# Expected: {"simulation_id": "...", "status": "running"}

# 4. Supabase Realtime works
# Open the frontend → Transparency Feed should show live events

# 5. pg_cron jobs scheduled
# Supabase Dashboard → SQL Editor:
SELECT jobid, schedule, command FROM cron.jobs;
# Expected: 6 jobs

# 6. Storage buckets are private
# Supabase Dashboard → Storage → all 5 buckets show 🔒 Private

# 7. Security scan passes
bash .github/scripts/check_no_service_key.sh
```

---

## 8. Rollback

### Railway (FastAPI)
Railway → Deployments → select previous deployment → **Rollback**

### Vercel (Frontend)
Vercel → Deployments → select previous → **Promote to Production**

### Supabase (Database)
```bash
# Database migrations are not auto-rollbackable.
# To revert schema: create a new migration with the reverse operations.
# For data: use the daily backups in Supabase Dashboard → Database → Backups.
```

---

> **Next:** [Demo Guide →](DEMO_GUIDE.md) | [← Back to README](../README.md)
