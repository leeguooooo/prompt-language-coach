#!/bin/bash
set -euo pipefail

# Resolve plugin root robustly regardless of how the hook is invoked
if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
  REPO_ROOT="$CURSOR_PLUGIN_ROOT"
else
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

python3 "$REPO_ROOT/scripts/render_coaching_context.py" \
  --platform cursor \
  --config "$HOME/.cursor/language-coach.json"
