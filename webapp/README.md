# ASAR webapp — demo UI

A two-process demo of the ASAR v0 research pipeline backed by the local
fine-tuned **Qwen-0.5B + LoRA (SFT + DPO v3)** adapter.

```
┌─────────────────────────────┐        ┌──────────────────────────────────────┐
│ Next.js 14 + Tailwind +     │  fetch │ FastAPI /api/research, /api/info,    │
│ Framer Motion + Heroicons   ├───────►│ /api/health                          │
│ (port 3000)                 │        │ ► run_demo_pipeline(mode="live")     │
└─────────────────────────────┘        │ ► LocalSLMClient → adapter v3 (MPS)  │
                                       │ ► SafetyAwareRunner pre/post check   │
                                       │ (port 8000)                          │
                                       └──────────────────────────────────────┘
```

## Run (one command

(Skip this — `./webapp/run-dev.sh` does it for you on first run.)

From the repo root:

```bash
uv sync --extra webapp --extra local-llm --extra rag --extra safety
cd webapp/frontend && npm install && cd -
```)

From the repo root:

```bash
./webapp/run-dev.sh
```

That script:

1. exports all `ASAR_*` env vars (provider=local, adapter=v3, search=corpus, safety=on)
2. installs `webapp/frontend/node_modules` on first run
3. starts the FastAPI backend on `127.0.0.1:8000` (with prefix `[back ]`)
4. starts the Next.js dev server on `localhost:3000` (with prefix `[front]`)
5. cleans both up on Ctrl-C

Open <http://localhost:3000>.

## Run (two terminals)

If you prefer separate terminals:

```bash
# terminal 1 — backend
./webapp/run-backend.sh

# terminal 2 — frontend
cd webapp/frontend && npm run dev
```

## One-time install

## Backend environment

The backend reads its model wiring from environment variables. Defaults
(set by `run-backend.sh`):

| Variable                    | Value                                                |
|-----------------------------|------------------------------------------------------|
| `ASAR_MODEL_PROVIDER`       | `local`                                              |
| `ASAR_LOCAL_BASE_MODEL`     | `Qwen/Qwen2.5-0.5B-Instruct`                         |
| `ASAR_LOCAL_ADAPTER_PATH`   | `models/asar-qwen-0.5b-scifact-dpo-v3`               |
| `ASAR_LOCAL_DEVICE`         | `mps`                                                |
| `ASAR_SEARCH_PROVIDER`      | `corpus`                                             |
| `ASAR_SAFETY_ENABLED`       | `1`                                                  |

The Next.js `next.config.mjs` rewrites `/api/*` → `http://127.0.0.1:8000/api/*`,
so the frontend can call the backend with same-origin fetches and no CORS dance.

## Endpoints

- `POST /api/research` — body `{"goal": "...", "safety_enabled": true}` → full
  `ResearchOutput` plus a safety report.
- `GET  /api/info` — adapter metadata + base model + provider state.
- `GET  /api/health` — `{"status": "ok"}`.

## What the UI shows

For each run the page renders:

1. **Verdict bar** — verified / consistent / in-scope claim counts, safety
   status, wall-clock time.
2. **Plan** — every step the planner produced.
3. **Synthesis** — the synthesized answer plus each claim with its
   epistemic-status chip and supporting-evidence count.
4. **Evidence** — the retrieved SciFact passages with relevance bars.
5. **Raw JSON** — the full response, collapsible.
