G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"


def edit(path, pairs):
    p = G + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)


edit(r"src\Fx\BattleFx.Rise.cs", [
    ('''        // The cold: ice standing at her feet, frost glinting on her. Brief: the fire is coming.
        float cold = e.Ember ? (float)Math.Max(0.06, e.Delay) : 0.11f;
        Erupt(e.X, e.Z, 0.4f, 1.0f, 10, SpikeKind.Ice, 0.45f, cold + 0.12f, IceDeep);''',
     '''        // The cold: ice standing up round her feet and frost running out over the ground from her,
        // frost glinting on her, a cold light on her alone. Combat holds it a beat (Battle.RiseCold,
        // about a second in the slowed world) before the ember catches, so it must be seen: a few
        // small spikes under the crowd read as nothing happening.
        float cold = e.Ember ? (float)Math.Max(0.06, e.Delay) : 0.11f;
        Erupt(e.X, e.Z, 0.3f, 1.0f, 12, SpikeKind.Ice, 0.75f, cold + 0.15f, IceDeep);
        Erupt(e.X, e.Z, 0.9f, 1.8f, 14, SpikeKind.Ice, 0.5f, cold + 0.12f, IceDeep);
        AddFront(ground, 2.4f, cold + 0.15f, 0.1f, Rime, 1.3f, Ribbons.Style.Frost, 0.1f);
        Scars.Add("frost", ground, 2.2f, cold + 1.2f, 0);
        Flash(ground + Vector3.Up * 1.3f, new Color("#8fc4ff"), 4, cold + 0.15f, 3.5f);'''),
])

edit(r"src\Game\Game.cs", [
    ('''                    foreach (var s in new[] { 0.08, 0.3, 0.45, 0.6, 0.75, 0.9, 1.1, 1.5, 2.2, 3.2 }) Shots.Want("rise", s);''',
     '''                    foreach (var s in new[] { 0.1, 0.5, 0.9, 1.08, 1.16, 1.24, 1.32, 1.45, 2.0, 3.0 }) Shots.Want("rise", s);'''),
])
print("ok")
