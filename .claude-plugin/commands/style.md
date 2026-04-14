Valid values: teaching, concise, translate.
If the user provides an invalid value, say: "Invalid style. Please choose one of: teaching, concise, translate."
Otherwise update the "style" field and confirm: "✓ Style updated to: <mode>"

Use: python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); d=json.load(open(p)) if os.path.exists(p) else {}; d['style']='<mode>'; json.dump(d,open(p,'w'),indent=2)"
