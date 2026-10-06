p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\src\Fx\BattleFx.Rise.cs"
s = open(p, encoding="utf-8").read()
pairs = [
    ('''        Flash(ground + Vector3.Up * 1.3f, new Color("#8fc4ff"), 4, cold + 0.15f, 3.5f);''',
     '''        Flash(ground + Vector3.Up * 1.3f, new Color("#8fc4ff"), 4, cold + 0.15f, 3.5f);
        // Over the crowd's heads, where a packed crowd lets it be seen (the ice at her feet is under
        // them): a ring of frost opening out at the height of their heads (StepRise), and snow
        // coming down over them.
        coldFrom = time;
        coldUntil = time + cold + 0.1;
        for (int i = 0; i < 46; i++)
        {
            float a = R() * Mathf.Tau, d = 0.4f + Mathf.Sqrt(R()) * 2.4f;
            Sparks.Spawn(ground + new Vector3(Mathf.Cos(a) * d, 2.1f + R() * 1.1f, Mathf.Sin(a) * d), new Vector3((R() - 0.5f) * 0.3f, -0.9f - R() * 0.6f, (R() - 0.5f) * 0.3f),
                cold + 0.35f + R() * 0.3f, 0.07f + R() * 0.06f, Hdr("#dff2ff", 1.4f), Hdr("#7ab8ff", 0.8f), 0.03f, 0, 0.6f,
                sprite: i % 3 == 0 ? Sprites.Of("frost_star") : Sprites.Of("star"), spinV: 1.5f);
        }'''),
    ('''    bool graceEmber;''',
     '''    bool graceEmber;
    double coldFrom, coldUntil = -1;'''),
    ('''        var p = b.Player;
        if (!p.Alive) { graceUntil = -1; handFrom = -1; return; }
        float gy = Y(p.X, p.Z);''',
     '''        var p = b.Player;
        if (!p.Alive) { graceUntil = -1; handFrom = -1; coldUntil = -1; return; }
        float gy = Y(p.X, p.Z);
        if (time < coldUntil)
        {
            // The frost ring over their heads, opening out and fading as the ember catches.
            float k = (float)((time - coldFrom) / Math.Max(0.05, coldUntil - coldFrom));
            float rr = 0.9f + 1.7f * (1 - (1 - k) * (1 - k));
            const int N = 44;
            var ring = new Vector3[N + 1];
            for (int j = 0; j <= N; j++)
            {
                float a = j / (float)N * Mathf.Tau;
                ring[j] = V(p.X + Mathf.Cos(a) * rr, gy + 2.0, p.Z + Mathf.Sin(a) * rr);
            }
            Ribbons.Now(ring, 0.16f, Rime, 2.2f * Mathf.Min(1, k * 6) * (1 - k * k), Ribbons.Style.Frost);
        }'''),
]
for a, b in pairs:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
