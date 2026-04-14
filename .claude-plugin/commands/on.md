Read ~/.claude/language-coach.json, set "enabled": true (or remove the field), write it back.
Confirm: "✓ Language coach active."

Use: python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); d=json.load(open(p)) if os.path.exists(p) else {}; d['enabled']=True; json.dump(d,open(p,'w'),indent=2)"
