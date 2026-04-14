Read ~/.claude/language-coach.json if it exists (default: {}), update the "native" field to the value provided by the user, then write it back.

Use: python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); d=json.load(open(p)) if os.path.exists(p) else {}; d['native']='<lang>'; json.dump(d,open(p,'w'),indent=2)"

Confirm: "✓ Native language updated to: <lang>"
