#!/bin/sh
# Run the placeholder Whisper check by hand on the first two pending jobs.
S="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad"
PY=/c/Users/munch/vo-tools/analysis/Scripts/python.exe
cd "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a501b387a90d78b4e" || exit 1
"$PY" -c "
import json
j=json.load(open(r'C:/Users/munch/vo-tools/work/placeholders/check_jobs.json',encoding='utf-8'))
json.dump(j[:2],open(r'$S/check2.json','w',encoding='utf-8'))
print(len(j))
"
export PYTHONIOENCODING=utf-8 HF_TOKEN_PATH='C:\Users\munch\vo-tools\voicebox-data\no-token' HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export PATH="/c/Users/munch/vo-tools/ffmpeg/bin:$PATH"
rm -f "$S/check2.out"
"$PY" tools/vo/placeholders.py --check "$S/check2.json" "$S/check2.out" > "$S/check2.log" 2>&1
echo "exit $?"
tail -5 "$S/check2.log"
head -c 1200 "$S/check2.out"
