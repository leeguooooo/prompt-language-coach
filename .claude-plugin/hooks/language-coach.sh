#!/bin/bash
CONFIG="$HOME/.claude/language-coach.json"

# Silent exit if jq not installed
if ! command -v jq &>/dev/null; then exit 0; fi

# Silent exit if not configured
if [ ! -f "$CONFIG" ]; then exit 0; fi

# Silent exit if disabled
ENABLED=$(jq -r '.enabled // true' "$CONFIG")
if [ "$ENABLED" = "false" ]; then exit 0; fi

NATIVE=$(jq -r '.native // "zh"' "$CONFIG")
TARGET=$(jq -r '.target // "en"' "$CONFIG")
STYLE=$(jq -r '.style // "teaching"' "$CONFIG")
RESPONSE_LANG=$(jq -r '.responseLanguage // "native"' "$CONFIG")

# Resolve response language instruction
if [ "$RESPONSE_LANG" = "target" ]; then
  RESPONSE_INSTRUCTION="After coaching, answer the actual request in $TARGET."
else
  RESPONSE_INSTRUCTION="After coaching, answer the actual request in $NATIVE."
fi

PROMPT="Language coaching preference (native: $NATIVE → target: $TARGET):
- If user writes in $TARGET or mixes $NATIVE+$TARGET: quote original, point out key mistakes, give corrected version, give a more natural native-like version.
- If user writes fully in $NATIVE: provide one concise natural $TARGET version first.
- If mixed because user cannot express fully in $TARGET: give one complete natural $TARGET version of the whole meaning.
- Style: $STYLE (teaching = show error reasons; concise = corrections only; translate = target version only).
$RESPONSE_INSTRUCTION"

jq -nc --arg ctx "$PROMPT" \
  '{hookSpecificOutput:{hookEventName:"UserPromptSubmit",additionalContext:$ctx}}'
