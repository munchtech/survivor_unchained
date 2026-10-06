"""Where frames from play are: this worktree's own first, then the previous skills lead's (the 'before' frames)."""
import glob
import os

MINE = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a560452c597415545\godot\.shots"
AD05 = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad059388f00c19f9f\godot\.shots"
A191 = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\.shots"
ABC = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\.shots"
A94 = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a94ac6b67f1279213\godot\.shots"
PREV = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a63cd93fc73d5ed79\godot\.shots"
DIRS = [MINE, AD05, A191, ABC, A94, PREV, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8bafe3cd8a229639\godot\.shots"]


def shot(name):
    for d in DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def run(run_name):
    """The frames of one run, in order."""
    for d in DIRS:
        f = sorted(glob.glob(os.path.join(d, f"{run_name}_[0-9][0-9].png")))
        if f:
            return f
    return []
