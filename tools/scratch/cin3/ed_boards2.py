p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\tools\cinematics\boards.py'
t = open(p, encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, a[:60]
    t = t.replace(a, b)


rep('''waits for ComfyUI's queue to be empty first, and frees the models after.
''', '''takes the GPU's turn first (tools/turn.py; --wait minutes for it), waits for
ComfyUI's queue to be empty, and gives the turn back (freeing the models) after.
''')
rep('''    ap.add_argument("--stage", default="",''', '''    ap.add_argument("--wait", default="0", help="minutes to wait for the GPU's turn")
    ap.add_argument("--stage", default="",''')
rep('''    made = []
    wait_idle()
    try:''', '''    made = []
    # Heavy work takes turns on this machine (docs/team/README.md).
    turn = os.path.join(ROOT, "tools", "turn.py")
    who = f"cinematics: boards {a.id}"
    if subprocess.run([sys.executable, turn, "take", "gpu", who, "--wait", a.wait]).returncode != 0:
        raise SystemExit(1)
    try:
        wait_idle()''')
rep('''    finally:
        free()''', '''    finally:
        subprocess.run([sys.executable, turn, "give", "gpu", who])''')
rep('''import json
import os
import sys''', '''import json
import os
import subprocess
import sys''')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')
