Valid values: native, target.
- native (default): AI answers the actual request in the user's native language.
- target: AI answers in the target language (for more advanced learners who want full immersion).

If invalid value provided, say: "Invalid option. Choose: native or target."

Update the "responseLanguage" field and confirm:
"✓ AI will now respond in <mode> language (<language name>)."

Use: python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); d=json.load(open(p)) if os.path.exists(p) else {}; d['responseLanguage']='<mode>'; json.dump(d,open(p,'w'),indent=2)"
