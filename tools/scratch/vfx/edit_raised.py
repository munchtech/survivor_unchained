G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"
p = G + r"\src\Fx\BattleFx.cs"
s = open(p, encoding="utf-8").read()
a = '''                    float gy = Y(e.X, e.Z);
                    if (e.Style == SpawnStyle.Rise)
                    {'''
b = '''                    float gy = Y(e.X, e.Z);
                    if (e.Style == SpawnStyle.Rise && e.Def.EndsWith("_ally", StringComparison.Ordinal)) { Raised(e); break; }
                    if (e.Style == SpawnStyle.Rise)
                    {'''
assert a in s
s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)

p = G + r"\src\Fx\BattleFx.Enemies.cs"
s = open(p, encoding="utf-8").read()
a = '''    int buffBudget;
'''
b = '''    /// <summary>Hers, got up out of the ground (Gravecall): a grave-sigil of soul-light burning in
    /// where it breaks open, soul-fire licking up off the one climbing out, the earth thrown.
    /// (A puff of dirt and a blue spark, it read as one of the enemy's dead rising.)</summary>
    void Raised(Ev.Spawn e)
    {
        float gy = Y(e.X, e.Z);
        var g = V(e.X, gy, e.Z);
        var m = Ground(e.X, e.Z, 1.1f, SummonTexture(), Soul * 0.8f, 1.1f, 2f);
        m.Decal.Rotation = new Vector3(0, R() * Mathf.Tau, 0);
        m.Grow = true;
        Scars.Add("crack", g, 0.9f, 3f, 0);
        for (int i = 0; i < 8; i++)
            Smoke.Spawn(g + Vector3.Up * 0.15f, new Vector3((R() - 0.5f) * 2.5f, 1.5f + R() * 2, (R() - 0.5f) * 2.5f), 0.6f, 0.09f + R() * 0.06f, new Color("#3a2e22"), gravity: 10, sprite: Sprites.Of("dirt"), spinV: 4);
        for (int i = 0; i < 7; i++)
            MoonTongue(g + new Vector3((R() - 0.5f) * 0.7f, 0.2f + R() * 0.5f, (R() - 0.5f) * 0.7f), Vector3.Up * (1.2f + R() * 1.2f), 0.35f + R() * 0.15f, Soul);
    }

    /// <summary>The soul-light of what is hers (Gravecall's risen): sea-green, never the enemy dead's grey.</summary>
    static readonly Color Soul = Hdr("#3affc8", 1.35f);

    int buffBudget;
'''
assert a in s
s = s.replace(a, b)
a2 = '''        foreach (var e in b.Enemies.Living())
        {
            if (buffBudget <= 0) break;'''
b2 = '''        foreach (var e in b.Enemies.Living())
        {
            // Hers among the dead: a small soul-flame at the breast, so the crowd tells them apart.
            if (e.Disposition == Disposition.Ally && e.Def.Family == Family.Undead)
                Body(V(e.X, Y(e.X, e.Z) + 1.25 * (e.Def.Scale ?? 1), e.Z), 0.42f, "wisp", Soul * 0.8f, (float)time * 2 + e.Id);
            if (buffBudget <= 0) continue;'''
assert a2 in s
s = s.replace(a2, b2)
open(p, "w", encoding="utf-8").write(s)
print("ok")
