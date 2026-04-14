Read ~/.claude/language-coach.json, set "enabled": false, write it back.
Confirm: "✓ Language coach paused. Run /language-coach on to resume."
The hook script checks this field and exits silently when enabled is false.

Use: python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); d=json.load(open(p)) if os.path.exists(p) else {}; d['enabled']=False; json.dump(d,open(p,'w'),indent=2)"
