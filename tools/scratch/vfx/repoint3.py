"""Point the capture tools at this lead's worktree (ad059388...); the earlier leads' frames stay readable as 'before'."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OLD, NEW = b"agent-a191ed81e2df462cf", b"agent-ad059388f00c19f9f"
for f in ["shot.py", "sweep.py", "gpu_horn.sh", "install_fb.py", "import_like.py", "install_dial_fb.py", "install_marks.py"]:
    p = os.path.join(HERE, f)
    if not os.path.exists(p):
        continue
    with open(p, "rb") as fh:
        b = fh.read()
    nb = b.replace(OLD, NEW)
    if nb != b:
        with open(p, "wb") as fh:
            fh.write(nb)
        print("repointed", f)
p = os.path.join(HERE, "shots.py")
s = open(p, encoding="utf-8").read()
if "A191 =" not in s:
    old_line = 'MINE = r"C:\\Users\\munch\\Desktop\\survivorsunchained\\.claude\\worktrees\\agent-a191ed81e2df462cf\\godot\\.shots"'
    new_lines = ('MINE = r"C:\\Users\\munch\\Desktop\\survivorsunchained\\.claude\\worktrees\\agent-ad059388f00c19f9f\\godot\\.shots"\n'
                 'A191 = r"C:\\Users\\munch\\Desktop\\survivorsunchained\\.claude\\worktrees\\agent-a191ed81e2df462cf\\godot\\.shots"')
    assert old_line in s
    s = s.replace(old_line, new_lines).replace("DIRS = [MINE, ABC,", "DIRS = [MINE, A191, ABC,")
    open(p, "w", encoding="utf-8").write(s)
    print("repointed shots.py")
