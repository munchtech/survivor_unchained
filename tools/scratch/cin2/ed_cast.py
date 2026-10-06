import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert old in s, (rel, old[:60])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"logic\Cinema\CineFile.cs", [(
'''/// <summary>Someone in it: the survivor, a person, one of the dead (spawned
/// into the fight, so they are still there when play begins), a boss.</summary>
public sealed class CineCast
{
    /// <summary>survivor, npc, enemy, boss.</summary>
    public string Kind = "npc";
    /// <summary>The enemy's def, the npc's id.</summary>
    public string? Def;
    /// <summary>Where they are when it begins.</summary>
    public string? Mark;
}''',
'''/// <summary>Someone in it: the survivor, a person, one of the dead (spawned
/// into the fight, so they are still there when play begins), a boss, a
/// crowd of extras, or a light that is a thing (the Warden's heart).</summary>
public sealed class CineCast
{
    /// <summary>survivor, npc, enemy, boss (the Ford-Warden's body, the
    /// cinematic's own), extras (a crowd seen only here, one at each of At,
    /// cued together by the cast's name), orb (a bright stone with its light).</summary>
    public string Kind = "npc";
    /// <summary>The enemy's def, the npc's id.</summary>
    public string? Def;
    /// <summary>Where they are when it begins.</summary>
    public string? Mark;
    /// <summary>Extras: how each is dressed (an enemy visual, in turn), where
    /// each stands (places), which way they all face, and the loop they hold.</summary>
    public List<string>? Visual;
    public List<JsonElement>? At;
    public double Heading;
    public string? Idle;
    /// <summary>An orb's colour and size; a boss's or an orb's glow to begin with.</summary>
    public string? Color;
    public double Size = 0.42, Glow = 1;
}'''),
(
'''        "atmosphere", "vfx", "spawn", "world", "bars", "title", "event", "fade", "hide", "wet", "hold", "prop", "prints", "glow", "frost",
    ];''',
'''        "atmosphere", "vfx", "spawn", "world", "bars", "title", "event", "fade", "hide", "wet", "hold", "prop", "prints", "glow", "frost",
        "lamp",
    ];'''),
])

edit(r"logic\Play\Zone.cs", [(
'''    /// <summary>A cinematic (godot/data/cinematics/ID.json) played now, `done`
    /// when it hands back or is skipped. False where none can play (no
    /// screen, the tests): the zone then says its lines as captions.</summary>
    bool Cinematic(string id, Action? done = null) => false;''',
'''    /// <summary>A cinematic (godot/data/cinematics/ID.json) played now, `done`
    /// when it hands back or is skipped. False where none can play (no
    /// screen, the tests): the zone then says its lines as captions. `marks`
    /// moves the file's marks to where things really are (where a boss fell).</summary>
    bool Cinematic(string id, Action? done = null, IReadOnlyDictionary<string, double[]>? marks = null) => false;'''),
])
print("ok")
