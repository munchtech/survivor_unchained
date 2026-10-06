"""Resolve the UI lead's merge: one --clock switch (theirs, same effect), their dawn glow with my frame (run from godot/)."""
import re

def resolve(path, pick):
    s = open(path, encoding="utf-8").read()
    pat = re.compile(r"<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> origin/worktree-agent-aab47bfdab5955dac\n", re.S)
    s, n = pat.subn(lambda m: pick(m.group(1), m.group(2)), s)
    open(path, "w", encoding="utf-8", newline="").write(s)
    print(path, n)

resolve("src/Game/Game.cs", lambda mine, theirs: theirs)
resolve("src/Game/GameClock.cs", lambda mine, theirs:
        '        hud.Fade(1, 1.2, "Dawn", $"Day {World.Day + 1}", new Godot.Color(1f, 0.62f, 0.3f, 0.32f));\n        Shots.Want("dawnfade", 1.25);\n')
