import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"logic\Play\Zones\Prologue.cs", [
('''using SurvivorUnchained.Content;
''', '''using SurvivorUnchained.Cinema;
using SurvivorUnchained.Content;
'''),
('''        var p = B.Player;
        // Where the cinematic leaves him (its mark warden_end), facing her.
        double wx = 3.0, wz = -33.6;
        warden = B.SpawnEnemy''',
'''        var p = B.Player;
        // Where the cinematic leaves him (its mark warden_end), facing her.
        var (wx, _, wz, _) = CineFile.Load("c02").Mark("warden_end");
        warden = B.SpawnEnemy'''),
])

edit(r"tests\FakeHost.cs", [
('''    public void Capture(bool on) => Captured = on;''',
'''    public void Capture(bool on) => Captured = on;
    /// <summary>The cinematics this host plays (none unless set): each started is
    /// kept with its hand-back and its marks, for the test to play out.</summary>
    public Func<string, bool>? Plays;
    public readonly List<(string Id, Action? Done, IReadOnlyDictionary<string, double[]>? Marks)> Cines = new();
    public bool Cinematic(string id, Action? done = null, IReadOnlyDictionary<string, double[]>? marks = null)
    {
        if (Plays?.Invoke(id) != true) return false;
        Cines.Add((id, done, marks));
        return true;
    }
    public bool CanCinematic(string id) => Plays?.Invoke(id) == true;'''),
])

edit(r"logic\Play\Zone.cs", [
('''    bool Cinematic(string id, Action? done = null, IReadOnlyDictionary<string, double[]>? marks = null) => false;''',
'''    bool Cinematic(string id, Action? done = null, IReadOnlyDictionary<string, double[]>? marks = null) => false;
    /// <summary>Whether that cinematic would play here now (a zone waits for its moment only if so).</summary>
    bool CanCinematic(string id) => false;'''),
])

edit(r"src\Game\GameCinema.cs", [
('''    /// <summary>Each frame, after the world is drawn: the camera, the cast, the cues.</summary>''',
'''    public bool CanCinematic(string id) =>
        scene?.Battle != null && cine == null && !Args.Has("nocine") && !(quick && Args.Get("cine") != id)
        && FileAccess.FileExists($"res://data/cinematics/{id}.json");

    /// <summary>Each frame, after the world is drawn: the camera, the cast, the cues.</summary>'''),
])
print("ok")
