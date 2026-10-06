p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\src\Fx\BattleFx.Enemies.cs"
s = open(p, encoding="utf-8").read()
a = '''            if (e.WardT > 0 && R() < 0.06f)
            {
                Sparks.Spawn(feet + Vector3.Up * 1.0f, Vector3.Zero, 0.35f, 0.9f, Hdr("#c8dcff", 1.2f) * 0.6f, null, 1.1f, sprite: Sprites.Range("ward_disc").First + 1, spinV: 0.5f);
                buffBudget--;
            }'''
b = '''            // A ward winks on one of them now and then, told by a few at a time: a wink a frame per
            // warded body piled a hundred pale discs over a warded crowd (the Dig, a white mass).
            if (e.WardT > 0 && time - lastWard > 0.06 && R() < 0.08f)
            {
                lastWard = time;
                Sparks.Spawn(feet + Vector3.Up * 0.9f, Vector3.Zero, 0.3f, 0.6f, Hdr("#8ab0ff", 1f) * 0.45f, null, 0.8f, sprite: Sprites.Range("ward_disc").First + 1, spinV: 0.5f);
                buffBudget--;
            }'''
assert a in s
s = s.replace(a, b)
a2 = '''    int buffBudget;
'''
b2 = '''    int buffBudget;
    double lastWard = -1;
'''
assert a2 in s
s = s.replace(a2, b2)
open(p, "w", encoding="utf-8").write(s)
print("ok")
