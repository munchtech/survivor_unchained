"""Point the capture tools at this lead's worktree (abc6bbe0...); the last lead's frames stay readable as 'before'."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OLD, NEW = b"agent-a94ac6b67f1279213", b"agent-abc6bbe020c7fe287"
for f in ["shot.py", "sweep.py", "gpu_horn.sh", "install_fb.py", "import_like.py", "install_dial_fb.py", "install_marks.py"]:
    p = os.path.join(HERE, f)
    with open(p, "rb") as fh:
        b = fh.read()
    nb = b.replace(OLD, NEW)
    if nb != b:
        with open(p, "wb") as fh:
            fh.write(nb)
        print("repointed", f)
p = os.path.join(HERE, "shots.py")
s = open(p, encoding="utf-8").read()
if "A94 =" not in s:
    old_line = 'MINE = r"C:\\Users\\munch\\Desktop\\survivorsunchained\\.claude\\worktrees\\agent-a94ac6b67f1279213\\godot\\.shots"'
    new_lines = ('MINE = r"C:\\Users\\munch\\Desktop\\survivorsunchained\\.claude\\worktrees\\agent-abc6bbe020c7fe287\\godot\\.shots"\n'
                 'A94 = r"C:\\Users\\munch\\Desktop\\survivorsunchained\\.claude\\worktrees\\agent-a94ac6b67f1279213\\godot\\.shots"')
    assert old_line in s
    s = s.replace(old_line, new_lines).replace("DIRS = [MINE, PREV,", "DIRS = [MINE, A94, PREV,")
    open(p, "w", encoding="utf-8").write(s)
    print("repointed shots.py")
