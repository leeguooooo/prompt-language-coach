#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG="$HOME/.claude/language-coach.json"

if ! command -v python3 >/dev/null 2>&1; then
  exit 0
fi

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

python3 "$REPO_ROOT/scripts/render_coaching_context.py" \
  --platform claude \
  --config "$CONFIG"
