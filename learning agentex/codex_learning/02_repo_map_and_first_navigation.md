# Repo Map and First Navigation

Workspace root relevant to you:

```text
ScaleAI/
├─ scale-agentex/            # Main Agentex repository
│  ├─ README.md              # Primary onboarding
│  ├─ dev.sh                 # One-command local orchestration (macOS-focused)
│  ├─ agentex/               # Backend server + infra logic
│  └─ agentex-ui/            # Frontend developer UI (Next.js)
└─ learning agentex/         # This learning pack
```

## `scale-agentex` top-level map

## `scale-agentex/agentex` (backend infra)

High-value directories:

- `src/`  
  Backend API/runtime code.

- `docs/docs/`  
  Best concept docs (architecture, tasks, state, streaming, agent types).

- `docker-compose.yml`  
  Local service topology:
  - Temporal + Temporal UI
  - Postgres
  - Redis
  - MongoDB
  - OpenTelemetry collector
  - Agentex API + Temporal worker

- `Makefile`  
  Useful commands (`make dev`, `make test`, docs commands).

## `scale-agentex/agentex-ui` (developer frontend)

High-value files:

- `README.md`  
  UI responsibilities and setup.

- `app/` and `components/agentex/`  
  Main UX surfaces for tasks/chat/traces.

- `hooks/`  
  Where data-fetching and subscriptions are implemented.

- `package.json`  
  Scripts and dependency stack.

## Read this first (in order)

1. `scale-agentex/README.md`
2. `scale-agentex/agentex/docs/docs/getting_started/agentex_overview.md`
3. `scale-agentex/agentex/docs/docs/getting_started/choose_your_agent_type.md`
4. `scale-agentex/agentex/docs/docs/concepts/agents.md`
5. `scale-agentex/agentex/docs/docs/concepts/task.md`
6. `scale-agentex/agentex-ui/README.md`

## Skip for now (until you need it)

- deep deployment docs
- CI/CD details
- migration scripts internals
- advanced Temporal troubleshooting

## First 30-minute navigation drill

Run these commands from repo root:

```bash
cd scale-agentex
rg --files | rg -i "readme|overview|agent_type|concepts/(agents|task|state|streaming)"
```

Then:

1. Open each file and write 1 sentence on its purpose.
2. Draw your own 3-box diagram:
   - Client/UI
   - Agentex server
   - Agent code
3. Trace one request path in words.

If you can do this clearly, the blob feeling drops fast.

## One-sentence architecture summary

The UI/client sends tasks/messages to Agentex Server, which routes them to agent code via ACP, persists runtime artifacts, and streams responses/traces back to clients.
