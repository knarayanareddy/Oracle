# 🤝 Contributing to ORACLE

> **Navigation:** [← Back to README](README.md) | [Development Guide](docs/DEVELOPMENT.md)

Thank you for your interest in contributing! ORACLE is a hackathon project with a clear
path to production. This guide covers the contribution workflow.

---

## Quick PR Flow

```bash
# 1. Create a branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# ... code ...

# 3. Run all checks locally
pnpm typecheck                          # TypeScript
cd apps/api && pytest tests/ -v         # Python (40 tests)
bash .github/scripts/check_no_service_key.sh  # Security

# 4. Commit with conventional format
git commit -m "feat(swarm): add volatility detection to L5 signals"

# 5. Push and open a PR
git push origin feature/your-feature-name
# → GitHub opens PR
# → CI runs: security → typecheck → tests
# → Request review
```

---

## Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/short-description` | `feature/swarm-volatility` |
| Bug fix | `fix/short-description` | `fix/voice-tempfile` |
| Docs | `docs/short-description` | `docs/api-reference` |
| Refactor | `refactor/short-description` | `refactor/extract-resilience` |
| Chore | `chore/short-description` | `chore/update-deps` |

---

## Commit Convention

We use [Conventional Commits](https://conventionalcommits.org/):

```
type(scope): description

type:     feat | fix | docs | refactor | test | chore | perf
scope:    swarm | voice | strategy | signals | memory | api | web | db | security
```

**Examples:**
```
feat(swarm): add institutional trader persona with conviction logic
fix(voice): replace temp file with in-memory BytesIO streaming
docs(api): add request/response examples for all endpoints
refactor(resilience): extract circuit breaker to reusable module
test(graphrag): add entity extraction test cases
chore(deps): pin langchain-openai to 0.2.3
```

---

## Code Standards

### Python (Backend)

- **Python 3.12+** required
- **Type hints** on all function signatures
- **Pydantic models** for request/response validation
- **structlog** for all logging (JSON format, never log PII)
- **Dependency injection** via FastAPI `Depends()` where appropriate
- **Tests** required for new services

```python
# Good
async def run_swarm(self, config: SwarmConfig) -> SwarmResult:
    logger.info("swarm_run_start", simulation_id=config.simulation_id)
    ...

# Bad
async def run_swarm(self, config):
    print(f"Starting {config.simulation_id}")
    ...
```

### TypeScript (Frontend)

- **Strict mode** enabled (`tsconfig.json` → `strict: true`)
- **Named exports** preferred
- **Zustand** for global state, **TanStack Query** for server state
- **Canonical types** from `src/types/index.ts` — never duplicate types
- **Tailwind** for styling (use the `oracle-*` color tokens)

```typescript
// Good
import { type Position } from '@/types'
export function PositionRow({ position }: { position: Position }) { ... }

// Bad
function PositionRow({ position }: { position: any }) { ... }
```

### SQL (Database)

- **All tables need RLS** — no exceptions
- **Comments** on non-obvious columns
- **Index** on frequently queried columns (especially `user_id`, `created_at`)
- **Migration files** named `YYYYMMDD_description.sql`

---

## Review Checklist

Before requesting review, verify:

```
□ All tests pass (pytest + typecheck)
□ Security scan passes (check_no_service_key.sh)
□ No service role key in frontend code
□ New database tables have RLS enabled
□ New API endpoints have X-Oracle-Secret auth
□ External calls wrapped in circuit breaker
□ Structured logging (no print statements, no PII)
□ Commit message follows conventional format
```

---

## Architecture Constraints

These are **non-negotiable** design principles (from the design doc):

1. **Transparency First** — every recommendation shows its reasoning chain
2. **Paper Trading Only** — no real money execution (ADR-008)
3. **RLS on every table** — no exceptions
4. **Service role key never in frontend** — enforced by CI scan
5. **EU data residency** — Supabase Frankfurt only
6. **No PII in logs** — UUIDs only
7. **Circuit breakers** on all external calls

If your change conflicts with these principles, discuss in the PR description.

---

## Reporting Issues

```
Title: [Bug/Feature] Short description

Body:
- What happened / what you expected
- Steps to reproduce (for bugs)
- Environment (OS, Node, Python versions)
- Relevant logs (redact secrets)
- Screenshots (for UI issues)
```

---

> **← Back to README** | [Development Guide →](docs/DEVELOPMENT.md)
