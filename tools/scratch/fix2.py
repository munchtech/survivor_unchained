R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit('Overlay.cs', [
("""        var btn = CloseButton(closeKey, close ?? G.CloseOverlay);
        btn.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        head.AddChild(btn);""",
"""        // B and Escape close; the button is for the mouse, so focus never starts or sticks on it.
        var btn = Nav.Skip(CloseButton(closeKey, close ?? G.CloseOverlay));
        btn.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        head.AddChild(btn);"""),
("""            if (kind == Kind || a == Act.Inventory && Controls.Instance?.UsingPad == true) G.CloseOverlay();
            else G.Open(kind);
            return true;""",
"""            if (kind == Kind || a == Act.Inventory && Controls.Instance?.UsingPad == true) G.CloseOverlay();
            else { Sound.Sfx.Page(); G.Open(kind); }
            return true;"""),
("""            int i = Array.FindIndex(Book, b => b.Kind == Kind);
            G.Open(Book[(i + (a == Act.TabNext ? 1 : Book.Length - 1)) % Book.Length].Kind);
            return true;""",
"""            int i = Array.FindIndex(Book, b => b.Kind == Kind);
            Sound.Sfx.Page();
            G.Open(Book[(i + (a == Act.TabNext ? 1 : Book.Length - 1)) % Book.Length].Kind);
            return true;"""),
])
edit('Pack.cs', [
("""    public InventoryScreen(Game g) : base(g) { }""",
"""    public InventoryScreen(Game g) : base(g) { Nav.Prefer = "pack:0"; }"""),
("""    public ShopScreen(Game g, string shop) : base(g) { this.shop = shop; }""",
"""    public ShopScreen(Game g, string shop) : base(g) { this.shop = shop; Nav.Prefer = "shelf:0"; }"""),
("""    public StashScreen(Game g) : base(g) { }""",
"""    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }"""),
])
edit('Book.cs', [
("""        if (a == Act.SubNext) { tab = Sections[(i + 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Hover(); return true; }
        if (a == Act.SubPrev) { tab = Sections[(i + Sections.Length - 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Hover(); return true; }""",
"""        if (a == Act.SubNext) { tab = Sections[(i + 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }
        if (a == Act.SubPrev) { tab = Sections[(i + Sections.Length - 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }"""),
])
edit('ArtsScreen.cs', [
("""        skills = !skills;
        Sound.Sfx.Hover();""",
"""        skills = !skills;
        Sound.Sfx.Page();"""),
])
edit('Panels.cs', [
("""        chosen = i;
        Mark();
        Sound.Sfx.Click();""",
"""        chosen = i;
        Mark();
        Sound.Sfx.Pick();"""),
])
print('done')
