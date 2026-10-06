p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\src\Fx\BattleFx.Dig.cs"
s = open(p, encoding="utf-8").read()
start = s.index("    /// <summary>The Dig's iron tubs: a few, reused, built in code (an iron box on four wheels).</summary>")
end = s.rindex("}")
s = s[:start] + '''    /// <summary>The Dig's iron tubs: a few, reused (MineTub).</summary>
    void MakeTubs()
    {
        tubPool = new Node3D[4];
        for (int i = 0; i < tubPool.Length; i++)
        {
            var tub = MineTub.Make(17 + i * 7);
            tub.Visible = false;
            AddChild(tub);
            tubPool[i] = tub;
        }
    }
''' + s[end:]
reps = [
    ("    MeshInstance3D[]? tubPool;", "    Node3D[]? tubPool;"),
    ("tub.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, Mathf.Atan2(dir.X, dir.Z)), at + Vector3.Up * (0.57f + 0.03f * Mathf.Sin(t * 60)));",
     "tub.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, Mathf.Atan2(dir.X, dir.Z)), at + Vector3.Up * (0.1f + 0.025f * Mathf.Sin(t * 60)));"),
    # Pictures of the Dig's moments (--on boss): the tub on its rail, the ground going, the crack.
    ("                pending.Add((time + life, () => CaveIn(x, z, (float)e.Radius)));",
     "                pending.Add((time + life, () => CaveIn(x, z, (float)e.Radius)));\n                if (Shots.On(\"boss\")) Shots.Want(\"cavein\", life + 0.3);"),
    ("                pending.Add((time + life, () => Fissure(x, z, x1, z1, (float)(e.Width ?? 4))));",
     "                pending.Add((time + life, () => Fissure(x, z, x1, z1, (float)(e.Width ?? 4))));\n                if (Shots.On(\"boss\")) Shots.Want(\"fissure\", life + 0.35);"),
    ("                pending.Add((time + life, () => tubRuns.Add((V(x, Y(x, z), z), V(tx1, Y(tx1, tz1), tz1), 0))));",
     "                pending.Add((time + life, () => tubRuns.Add((V(x, Y(x, z), z), V(tx1, Y(tx1, tz1), tz1), 0))));\n                if (Shots.On(\"boss\")) { Shots.Want(\"tubrun\", life + 0.12); Shots.Want(\"tubrun\", life + 0.3); }"),
    ("                fuses.Add((V(x, Y(x, z) + 0.95, z), (float)life));",
     "                fuses.Add((V(x, Y(x, z) + 0.95, z), (float)life));\n                if (Shots.On(\"boss\")) Shots.Want(\"fuse\", life * 0.5);"),
]
for a, b in reps:
    assert a in s, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
