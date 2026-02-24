# First Run Playbook

Goal: run the local platform and interact with one agent end-to-end.

## Important environment note (for your setup)

Your machine path indicates Windows.  
`scale-agentex/dev.sh` is explicitly macOS-oriented.

Recommended options:

1. Use **WSL2 + Docker Desktop integration** (recommended on Windows).
2. Or run manually in separate terminals without relying on `dev.sh`.

## Prerequisites checklist

- Python 3.12
- `uv`
- Docker Desktop running
- Node.js + npm
- `agentex` CLI (`uv tool install agentex-sdk`)

## Option A: quick start script (macOS/Linux users)

From `scale-agentex/`:

```bash
./dev.sh
```

Expected URLs after startup:

- UI: `http://localhost:3000`
- API: `http://localhost:5003`
- Swagger: `http://localhost:5003/swagger`
- Temporal UI: `http://localhost:8080`

## Option B: manual start (works well in WSL)

## Terminal 1: backend infra + API

```bash
cd scale-agentex/agentex
uv venv
source .venv/bin/activate
uv sync --group dev
make dev
```

## Terminal 2: frontend UI

```bash
cd scale-agentex/agentex-ui
npm install
npm run dev
```

## Terminal 3: your first agent project

```bash
uv tool install agentex-sdk
agentex init
cd <your-agent-folder>
uv venv
source .venv/bin/activate
uv sync
agentex agents run --manifest manifest.yaml
```

Then open `http://localhost:3000` and verify your agent appears.

## Sanity checkpoints

- Backend responds at `/swagger`
- UI loads agent list
- Sending a test message returns a response
- Task and message history visible
- Trace view shows execution spans

## Common failures

## Port conflicts

If `Address already in use`:

- stop conflicting process
- or change local ports in config/manifest

## Redis conflicts

If local Redis already occupies `6379`, Docker Redis may fail.

## CLI missing

If `agentex` command not found:

```bash
uv tool install agentex-sdk
agentex --help
```

## What to do right after first successful run

1. Switch a sync sample to a streaming response.
2. Read `choose_your_agent_type.md` and decide if you need async.
3. Add one external tool/API call in your agent logic.
