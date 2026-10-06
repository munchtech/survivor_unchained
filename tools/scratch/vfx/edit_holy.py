p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.cs"
s = open(p, encoding="utf-8").read()
reps = [
    ("""        bool fire = school == School.Fire;
        if (On('f')) Sparks.Spawn(ground + Vector3.Up * 0.9f, Vector3.Zero, 0.07f, r * (fire ? 0.3f : 0.4f), fire ? new Color(1.9f, 0.95f, 0.22f) : new Color(1.8f, 1.7f, 1.6f), pal.Glow * 0.4f, r * (fire ? 0.6f : 0.8f), alpha: fire ? 0.7f : 0.8f);""",
     """        bool fire = school == School.Fire, holy = school == School.Holy;
        // Holy's is gold: white, it and its burst left cream discs under Hallowed Ground's crowd.
        if (On('f')) Sparks.Spawn(ground + Vector3.Up * 0.9f, Vector3.Zero, 0.07f, r * (fire ? 0.3f : 0.4f), fire ? new Color(1.9f, 0.95f, 0.22f) : holy ? new Color(1.5f, 1.15f, 0.55f) : new Color(1.8f, 1.7f, 1.6f), pal.Glow * 0.4f, r * (fire ? 0.6f : 0.8f), alpha: fire || holy ? 0.7f : 0.8f);"""),
    ("""            : fire ? new Color(glow * 1.0f, glow * 0.6f, glow * 0.3f, 1) : new Color(glow, glow, glow, 1);""",
     """            : fire ? new Color(glow * 1.0f, glow * 0.6f, glow * 0.3f, 1)
            : holy ? new Color(glow * 0.95f, glow * 0.7f, glow * 0.32f, 0.85f) : new Color(glow, glow, glow, 1);"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
