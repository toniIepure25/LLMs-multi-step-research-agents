#!/usr/bin/env bash
# Start the ASAR webapp FastAPI backend wired to the local v3 adapter.
#
# Run from the repo root:   ./webapp/run-backend.sh
set -euo pipefail

# Resolve repo root regardless of where this script is invoked from.
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$( cd -- "${SCRIPT_DIR}/.." &> /dev/null && pwd )"
cd "${REPO_ROOT}"

export ASAR_MODEL_PROVIDER="${ASAR_MODEL_PROVIDER:-local}"
export ASAR_LOCAL_BASE_MODEL="${ASAR_LOCAL_BASE_MODEL:-Qwen/Qwen2.5-0.5B-Instruct}"
export ASAR_LOCAL_ADAPTER_PATH="${ASAR_LOCAL_ADAPTER_PATH:-models/asar-qwen-0.5b-scifact-dpo-v3}"
export ASAR_LOCAL_DEVICE="${ASAR_LOCAL_DEVICE:-mps}"
export ASAR_SEARCH_PROVIDER="${ASAR_SEARCH_PROVIDER:-corpus}"
export ASAR_SAFETY_ENABLED="${ASAR_SAFETY_ENABLED:-1}"

if [[ ! -d "${ASAR_LOCAL_ADAPTER_PATH}" ]]; then
  echo "warning: adapter directory not found at ${ASAR_LOCAL_ADAPTER_PATH}" >&2
fi

exec uv run --extra webapp --extra local-llm --extra rag --extra safety \
  uvicorn webapp.api.server:app --host 127.0.0.1 --port 8000 --reload
