import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"logic\Play\Zones\Waystation.cs", [
('''        G.SetObjectives(Objectives.Of(C));
        G.AnnounceZone();
        if (!F("waystation.visited").Truthy)
        {
            W.Facts["waystation.visited"] = true;
            G.After(2.5, () => G.Say("The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.", null, 5));
        }
        else if (!F("maps.told").Truthy && F("prologue.done").Truthy)
        {''',
'''        G.SetObjectives(Objectives.Of(C));
        if (!F("waystation.visited").Truthy)
        {
            W.Facts["waystation.visited"] = true;
            // C04 B (docs/cinematics/shoot/c04b.md): the first arrival, at first light.
            // Its chapter card is the place's title, so there is no other.
            if (G.Cinematic("c04b", () => { rookByCine = false; Presence(); })) return;
            G.AnnounceZone();
            G.After(2.5, () => G.Say("The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.", null, 5));
            return;
        }
        G.AnnounceZone();
        if (!F("maps.told").Truthy && F("prologue.done").Truthy)
        {'''),
('''    public override void Frame(double dt)
    {
        if (B == null) return;''',
'''    /// <summary>C04 B plays Rook with its own: ours steps out of the picture until it hands back.</summary>
    bool rookByCine;

    public override void CineEvent(string name)
    {
        if (name == "rook_cine") rookByCine = true;
    }

    public override void Frame(double dt)
    {
        if (B == null) return;
        if (rookByCine && Actors.TryGetValue("rook", out var rook)) rook.Hidden = true;'''),
])
print("ok")
