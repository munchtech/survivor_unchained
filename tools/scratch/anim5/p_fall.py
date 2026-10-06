from pathlib import Path
src = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\godot\src")
pv = src / "Actors" / "PlayerView.cs"
t = pv.read_text(encoding="utf-8")
E = [
    ('''    /// <summary>Up again after a fall (the prologue's second chances).</summary>
    public void Revive()
    {
        dead = false;''',
     '''    /// <summary>A story fall: down as at a death and held there, though the
    /// fight keeps her at a breath of life while the fall is staged
    /// (StoryNight.OnFall); up again with Revive. (Without it she stood
    /// through her own fall.)</summary>
    public void Fall() => fallen = true;
    bool fallen;

    /// <summary>Up again after a fall (the prologue's second chances, a story fall's rise).</summary>
    public void Revive()
    {
        dead = fallen = false;'''),
    ('''        if (!p.Alive)
        {''', '''        if (!p.Alive || fallen)
        {'''),
]
for a, b in E:
    assert t.count(a) == 1, a[:40]
    t = t.replace(a, b)
pv.write_text(t, encoding="utf-8")
gf = src / "Game" / "GameFall.cs"
t = gf.read_text(encoding="utf-8")
E = [
    ('''        hud.Prompt(promptShown = null);
        ShadeWorld(1, 0.9);
        if (risesLeft <= 0)''',
     '''        hud.Prompt(promptShown = null);
        ShadeWorld(1, 0.9);
        // She goes down where she stands (the fight only holds her at a breath of life).
        scene.Player?.Fall();
        if (risesLeft <= 0)'''),
    ('''            ShadeWorld(0, 0.01);
            rise();
            hud.Fade(0, 1.0);''',
     '''            ShadeWorld(0, 0.01);
            rise();
            scene?.Player?.Revive();
            hud.Fade(0, 1.0);'''),
]
for a, b in E:
    assert t.count(a) == 1, a[:40]
    t = t.replace(a, b)
gf.write_text(t, encoding="utf-8")
print("ok")
