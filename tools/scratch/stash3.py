p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Pack.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

rep("""    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }
""", """    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }

    VBoxContainer inspect = null!;

    /// <summary>What is hovered or focused, read in the pack's pane rather than in a tip over the slots.</summary>
    void Read(ItemInstance? it)
    {
        if (!IsInstanceValid(inspect)) return;
        foreach (var c in inspect.GetChildren()) { inspect.RemoveChild(c); c.QueueFree(); }
        if (it == null)
        {
            inspect.AddChild(Style.Label(Controls.Instance.UsingPad ? "Move over a thing to read it." : "Hover a thing to read it; click or drag it to move it.", Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
            return;
        }
        inspect.AddChild(ItemViews.Card(it, G.Journey.Ch, false, null, 600));
    }
""")
rep("""        sc.AddChild(ItemViews.Grid(w.Stash, 10, 98, null, null, it => G.Journey.FromStash(it.Uid), it => G.Journey.FromStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "store", null,""",
    """        sc.AddChild(ItemViews.Grid(w.Stash, 8, 118, null, null, it => G.Journey.FromStash(it.Uid), it => G.Journey.FromStash(it.Uid), (it, over) => Read(it), "store", null,""")
rep("""        mc.AddChild(ItemViews.Grid(ch.Pack, 6, 92, null, null, it => G.Journey.ToStash(it.Uid), it => G.Journey.ToStash(it.Uid), (it, over) => Tip(it != null ? ItemViews.Card(it, ch, false) : null, over), "mine", null,""",
    """        mc.AddChild(ItemViews.Grid(ch.Pack, 6, 92, null, null, it => G.Journey.ToStash(it.Uid), it => G.Journey.ToStash(it.Uid), (it, over) => Read(it), "mine", null,""")
rep("""        mwell.AddChild(mc);
        mine.AddChild(mwell);
        PageFooter(Controls.Instance.UsingPad ? Footer((Act.Confirm, "Move between pack and store")""", """        mwell.AddChild(mc);
        mine.AddChild(mwell);
        mine.AddChild(new Section("Read closely"));
        inspect = Style.V(Style.Gap2);
        mine.AddChild(inspect);
        Read(null);
        PageFooter(Controls.Instance.UsingPad ? Footer((Act.Confirm, "Move between pack and store")""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
