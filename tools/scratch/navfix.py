p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Nav.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""    readonly List<(Control C, string Id, NavItem? Info)> items = new();
    Panel? ring;
    double t;""",
"""    readonly List<(Control C, string Id, NavItem? Info)> items = new();
    Panel? ring;
    double t;
    // A screen built this frame has not been laid out: a direction waits a frame for it.
    ulong builtFrame;
    readonly List<Act> waiting = new();"""),
("""        Walk(Scope ?? host);
        if (FocusId == null || items.All(i => i.Id != FocusId))""",
"""        Walk(Scope ?? host);
        builtFrame = Engine.GetProcessFrames();
        if (FocusId == null || items.All(i => i.Id != FocusId))"""),
("""        if (Args.Has("navlog")) GD.Print($"nav {a}: {items.Count} items, focus {FocusId}, current {Current?.Id}, keymode {KeyMode}");
        if (!Enabled || items.Count == 0) return false;
        switch (a)
        {
            case Act.Up or Act.Down or Act.Left or Act.Right:""",
"""        if (!Enabled || items.Count == 0) return false;
        switch (a)
        {
            case Act.Up or Act.Down or Act.Left or Act.Right when Engine.GetProcessFrames() == builtFrame:
                // Built this very frame (the press that switched to the pad redrew it): move once it has its places.
                waiting.Add(a);
                return true;
            case Act.Up or Act.Down or Act.Left or Act.Right:"""),
("""        if (Args.Has("navlog")) GD.Print($"move {a} from {cur.Id} {from}: to {best?.Id} ({string.Join("; ", items.Select(i => $"{i.Id} {i.C.GetGlobalRect()}"))})");
        if (best is not { } next) { Sound.Sfx.Deny(); return; }""",
"""        if (best is not { } next) { Sound.Sfx.Deny(); return; }"""),
("""    public void Update(double delta)
    {
        if (ring == null || !GodotObject.IsInstanceValid(ring)) return;""",
"""    public void Update(double delta)
    {
        if (waiting.Count > 0 && Engine.GetProcessFrames() > builtFrame)
        {
            var now = waiting.ToList();
            waiting.Clear();
            foreach (var a in now) Key(a);
        }
        if (ring == null || !GodotObject.IsInstanceValid(ring)) return;"""),
]
for old, new in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
