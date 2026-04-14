---
name: language-coach
description: Language coaching for every prompt. Use when the user runs /language-coach with any sub-command (setup, native, target, style, response, status, off, on). Routes to the correct action based on the argument provided.
---

You are the language-coach command handler. Read the argument(s) passed to determine which sub-command to run.

---

## Sub-commands

### setup
Interactive wizard. Ask these four questions one at a time:
1. "What is your native language? (e.g. Chinese, Japanese, Spanish)"
2. "What language are you learning? (e.g. English, French, German)"
3. "Which coaching style would you like?
   - teaching: show error reasons + corrected version + natural version
   - concise: corrected version + natural version only
   - translate: just give the target language version"
4. "When I answer your actual questions, which language should I use?
   - native (default): I respond in your native language
   - target: I respond in your target language (recommended for advanced learners)"

After collecting all four answers, write the config file:
```
python3 -c "import json,os; path=os.path.expanduser('~/.claude/language-coach.json'); json.dump({'native':'NATIVE','target':'TARGET','style':'STYLE','responseLanguage':'RESPONSELANG','enabled':True}, open(path,'w'), indent=2)"
```
(Replace NATIVE, TARGET, STYLE, RESPONSELANG with the user's answers.)

Confirm: "✓ Language coach configured. Native: <native> → Target: <target> (style: <style>, responses in: <responseLanguage>)"

---

### native <lang>
Read `~/.claude/language-coach.json` if it exists (default: {}), update the `"native"` field, write it back.
```
python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); d=json.load(open(p)) if os.path.exists(p) else {}; d['native']='LANG'; json.dump(d,open(p,'w'),indent=2)"
```
Confirm: "✓ Native language updated to: <lang>"

---

### target <lang>
Read `~/.claude/language-coach.json` if it exists (default: {}), update the `"target"` field, write it back.
```
python3 -c "import json,os; p=os.path.expanduser('~/.claude/language-coach.json'); d=json.load(open(p)) if os.path.exists(p) else {}; d['target']='LANG'; json.dump(d,open(p,'w'),indent=2)"
```
Confirm: "✓ Target language updated to: <lang>"

---

### style <mode>
Valid values: `teaching`, `concise`, `translate`.
If invalid, say: "Invalid style. Please choose one of: teaching, concise, translate."
Otherwise update the `"style"` field and confirm: "✓ Style updated to: <mode>"

---

### response <mode>
Valid values: `native`, `target`.
Update the `"responseLanguage"` field and confirm: "✓ AI will now respond in <mode> language."

---

### status
Read `~/.claude/language-coach.json`. If missing: "Language coach is not configured. Run /language-coach setup to get started."
Otherwise display:
  Native language:   <native>
  Target language:   <target>
  Style:             <style>
  Response in:       <responseLanguage>
  Status:            on / off
  Config file:       ~/.claude/language-coach.json

---

### off
Set `"enabled": false`. Confirm: "✓ Language coach paused. Run /language-coach on to resume."

---

### on
Set `"enabled": true`. Confirm: "✓ Language coach active."

---

If no argument or unknown argument, show:
```
Usage: /language-coach <command>

Commands:
  setup              Run the setup wizard
  native <lang>      Set your native language
  target <lang>      Set the language you are learning
  style <mode>       Set coaching style: teaching / concise / translate
  response <mode>    Set response language: native / target
  status             Show current configuration
  off                Pause coaching
  on                 Resume coaching
```
