Read ~/.claude/language-coach.json. If it does not exist, say: "Language coach is not configured. Run /language-coach setup to get started."
Otherwise display:
  Native language:   <native>
  Target language:   <target>
  Style:             <style>
  Response in:       <responseLanguage>
  Status:            <on/off>
  Config file:       ~/.claude/language-coach.json

Use: python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); print(json.dumps(json.load(open(p)),indent=2)) if os.path.exists(p) else print('not configured')"
