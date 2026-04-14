You are helping the user configure the prompt-language-coach plugin.

Ask these four questions one at a time:
1. "What is your native language? (e.g. Chinese, Japanese, Spanish)"
2. "What language are you learning? (e.g. English, French, German)"
3. "Which coaching style would you like?
   - teaching: show error reasons + corrected version + natural version
   - concise: corrected version + natural version only
   - translate: just give the target language version"
4. "When I answer your actual questions, which language should I use?
   - native (default): I respond in your native language
   - target: I respond in your target language (recommended for advanced learners)"

After collecting all four answers, write the config file by running:
python3 -c "import json,os; path=os.path.expanduser('~/.claude/language-coach.json'); json.dump({'native':'<native>','target':'<target>','style':'<style>','responseLanguage':'<responseLanguage>','enabled':True}, open(path,'w'), indent=2)"

Then confirm: "✓ Language coach configured. Native: <native> → Target: <target> (style: <style>, responses in: <responseLanguage>)"
