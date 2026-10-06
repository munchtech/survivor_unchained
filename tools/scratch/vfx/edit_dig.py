G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"


def edit(path, pairs):
    p = G + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b, 1)
    open(p, "w", encoding="utf-8").write(s)


edit(r"src\Fx\BattleFx.Dig.cs", [
    ('''                tub.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, Mathf.Atan2(dir.X, dir.Z)), at + Vector3.Up * (0.05f + 0.03f * Mathf.Sin(t * 60)));''',
     '''                tub.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, Mathf.Atan2(dir.X, dir.Z)), at + Vector3.Up * (0.57f + 0.03f * Mathf.Sin(t * 60)));'''),
])

edit(r"src\Fx\BattleFx.cs", [
    ('''                case Ev.Telegraph e:
                {
''', '''                case Ev.Telegraph e:
                {
                    if (DigMark(e)) break;
'''),
    ('''        StepRise(b, fdt);''', '''        StepRise(b, fdt);
        StepDig(fdt);'''),
])

edit(r"src\Actors\CrowdView.cs", [
    ('''        float sc = (float)(e.Def.Scale ?? 1) * Beasts.Size(e.Def.Visual);''',
     '''        // Gone along under the ground by its script (Grimtunnel's Under): drawn burrowing, as the
        // burrowed are (its back, hat and lamp above the earth), while the effects heave the mound.
        if (e.State == EnemyState.Active && Under?.Invoke(e) == true) { role = "burrow"; y -= 0.25; t = time + e.Seed * 3; }
        float sc = (float)(e.Def.Scale ?? 1) * Beasts.Size(e.Def.Visual);'''),
    ('''    public CrowdView() { Name = "Crowd"; }''',
     '''    public CrowdView() { Name = "Crowd"; }

    /// <summary>Whether a creature is under the ground by its script's say (set by the view; null: none is).</summary>
    public static Func<Enemy, bool>? Under;'''),
])
print("ok")
