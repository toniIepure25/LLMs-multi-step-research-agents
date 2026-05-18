#!/usr/bin/env bash
# Start both the ASAR FastAPI backend (port 8000) and the Next.js frontend
# (port 3000) in one shell, with shared output and clean shutdown on Ctrl-C.
#
# Run from anywhere:    ./webapp/run-dev.sh
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$( cd -- "${SCRIPT_DIR}/.." &> /dev/null && pwd )"
cd "${REPO_ROOT}"

# ----- env vars for the v3 adapter ------------------------------------------
export ASAR_MODEL_PROVIDER="${ASAR_MODEL_PROVIDER:-local}"
export ASAR_LOCAL_BASE_MODEL="${ASAR_LOCAL_BASE_MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
export ASAR_LOCAL_ADAPTER_PATH="${ASAR_LOCAL_ADAPTER_PATH:-models/asar-qwen-0.5b-scifact-dpo-v3}"
export ASAR_LOCAL_DEVICE="${ASAR_LOCAL_DEVICE:-cpu}"
export ASAR_SEARCH_PROVIDER="${ASAR_SEARCH_PROVIDER:-corpus}"
export ASAR_SAFETY_ENABLED="${ASAR_SAFETY_ENABLED:-1}"

if [[ ! -d "${ASAR_LOCAL_ADAPTER_PATH}" ]]; then
  echo "warning: adapter directory not found at ${ASAR_LOCAL_ADAPTER_PATH}" >&2
fi

# ----- frontend node_modules check ------------------------------------------
if [[ ! -d "webapp/frontend/node_modules" ]]; then
  echo "[run-dev] installing frontend deps..."
  (cd webapp/frontend && npm install --no-audit --no-fund)
fi

# ----- free our ports if a stale dev server is still bound ------------------
log() { printf "\033[36m[run-dev]\033[0m %s\n" "$*"; }

free_port() {
  local port="$1"
  local pids
  pids=$(lsof -ti tcp:"${port}" -sTCP:LISTEN 2>/dev/null || true)
  if [[ -n "${pids}" ]]; then
    log "port ${port} busy (pid: ${pids//$'\n'/, }) — killing"
    # shellcheck disable=SC2086
    kill ${pids} 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti tcp:"${port}" -sTCP:LISTEN 2>/dev/null || true)
    if [[ -n "${pids}" ]]; then
      # shellcheck disable=SC2086
      kill -9 ${pids} 2>/dev/null || true
    fi
  fi
}

free_port 8000
free_port 3000

# ----- launch both processes ------------------------------------------------
# Kill children on Ctrl-C / exit.
BACK_PID=""
FRONT_PID=""
cleanup() {
  log "shutting down"
  [[ -n "${BACK_PID}"  ]] && kill "${BACK_PID}"  2>/dev/null || true
  [[ -n "${FRONT_PID}" ]] && kill "${FRONT_PID}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

log "starting backend on http://127.0.0.1:8000"
log "  adapter: ${ASAR_LOCAL_ADAPTER_PATH}"
log "  search:  ${ASAR_SEARCH_PROVIDER}"
log "  safety:  ${ASAR_SAFETY_ENABLED}"

# Prefix each line with [back] / [front] so the merged output is readable.
( uv run --extra webapp --extra local-llm --extra rag --extra safety \
    uvicorn webapp.api.server:app --host 127.0.0.1 --port 8000 \
    2>&1 | sed -u 's/^/[back ] /' ) &
BACK_PID=$!

log "starting frontend on http://localhost:3000"
( cd webapp/frontend && npm run dev -- --port 3000 \
    2>&1 | sed -u 's/^/[front] /' ) &
FRONT_PID=$!

log "open http://localhost:3000  (Ctrl-C to stop both)"
wait
