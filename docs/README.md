# 📚 ORACLE Documentation Index

> **[← Back to main README](../README.md)**

Complete documentation for the ORACLE Swarm Intelligence Broker.

---

## Start Here

| # | Document | Description | Audience |
|---|----------|-------------|----------|
| 1 | **[🏠 README](../README.md)** | Project overview, quick start, navigation hub | Everyone |
| 2 | **[🏗️ Architecture](ARCHITECTURE.md)** | System design, 10-layer stack, ADRs, resilience | Engineers |
| 3 | **[🔌 API Reference](API_REFERENCE.md)** | All endpoints with examples | Integrators |

---

## By Topic

### 🏗️ Architecture & Design
- [Architecture Deep Dive](ARCHITECTURE.md) — System diagram, 10-layer stack, ADRs, circuit breakers
- [Database Guide](DATABASE.md) — 25 tables, 8 schemas, RLS, pgvector, cron jobs

### 🔌 Integration
- [API Reference](API_REFERENCE.md) — 12 FastAPI endpoints + 5 Edge Functions
- [API Interactive Docs](http://localhost:8000/docs) — Swagger UI (when running locally)

### 🚀 Operations
- [Deployment Guide](DEPLOYMENT.md) — Supabase + Railway + Vercel production setup
- [Security Model](SECURITY.md) — RLS, key isolation, GDPR, threat model

### 💻 Development
- [Development Guide](DEVELOPMENT.md) — Local setup, testing, debugging, codebase tour
- [Contributing Guide](../CONTRIBUTING.md) — PR workflow, code standards, commit format
- [Changelog](../CHANGELOG.md) — Version history + roadmap

### 🎥 Presenting
- [Demo Guide](DEMO_GUIDE.md) — 5-minute script, checklist, fallbacks, Q&A prep

---

## Quick Links

| What | Link |
|------|------|
| Quick start | [README → Quick Start](../README.md#-quick-start) |
| Environment variables | [.env.example](../.env.example) |
| Database schema | [DATABASE.md](DATABASE.md) |
| API endpoints | [API_REFERENCE.md](API_REFERENCE.md) |
| Security model | [SECURITY.md](SECURITY.md) |
| Run tests | [DEVELOPMENT.md → Testing](DEVELOPMENT.md#5-testing) |
| Deploy to production | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Demo script | [DEMO_GUIDE.md](DEMO_GUIDE.md) |

---

## File Map

```
oracle/
├── README.md                 ← Start here
├── CHANGELOG.md              ← Version history
├── CONTRIBUTING.md           ← How to contribute
├── .env.example              ← Environment variables
│
├── docs/                     ← You are here
│   ├── README.md             ← This index
│   ├── ARCHITECTURE.md       ← System design
│   ├── API_REFERENCE.md      ← Endpoints
│   ├── DATABASE.md           ← Schema + RLS
│   ├── DEPLOYMENT.md         ← Production setup
│   ├── DEMO_GUIDE.md         ← Hackathon demo
│   ├── SECURITY.md           ← Security model
│   └── DEVELOPMENT.md        ← Dev guide
│
├── apps/
│   ├── web/                  ← React frontend
│   └── api/                  ← FastAPI backend
│
├── supabase/
│   ├── migrations/           ← SQL migrations
│   ├── functions/            ← Edge Functions
│   ├── tests/                ← RLS tests
│   └── seed.sql              ← Demo data
│
└── oracle-swarm/             ← Swarm engine fork
```
