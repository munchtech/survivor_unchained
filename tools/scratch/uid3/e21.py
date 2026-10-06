import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/ArenaResult.cs', [
    ('''/// <summary>An arena over (Arena/Arena.cs): how long, how many, and what
/// comes out of it (experience, gold, skills discovered) set against what
/// stays behind (the build the ember made). Then back to the story. The
/// end of half an hour is what the player remembers of it (the peak-end
/// rule), so the tally counts up rather than appearing, one after another.</summary>
public partial class ArenaResultScreen : Overlay
{
    readonly ArenaResult r;
    public override string Kind => "arena";
    public override bool Dismissable => false;

    public ArenaResultScreen(Game g, ArenaResult result) : base(g) => r = result;

    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    // The numbers counting up: each label, its final value, how it is written, when it starts.
    readonly System.Collections.Generic.List<(Medallion M, double To, System.Func<double, string> Fmt, double At)> counts = new();
    double shownFor;

    public override void _Process(double delta)
    {
        base._Process(delta);
        shownFor += delta;
        foreach (var (m, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(m)) continue;
            double k = System.Math.Clamp((shownFor - at) / 0.9, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            var t = fmt(to * k);
            if (t != m.Text) { m.Text = t; m.Arc = (float)k; m.QueueRedraw(); }
        }
    }''', '''/// <summary>An arena over (Arena/Arena.cs), told as the night's story in
/// beats (the experience director's brief; the end of half an hour is what
/// the player remembers of it, the peak-end rule): the verdict; the night's
/// numbers counting up, each landing with a blow; what comes out, a line at a
/// time with its own sound, the best last; what stays (the build the ember
/// made) going to ash; then how it went, in a line, and back to the road.
/// A press tells it all at once; the next leaves.</summary>
public partial class ArenaResultScreen : Overlay
{
    readonly ArenaResult r;
    public override string Kind => "arena";
    public override bool Dismissable => false;

    public ArenaResultScreen(Game g, ArenaResult result) : base(g) => r = result;

    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    // The numbers counting up: each label, its final value, how it is written, when it starts.
    readonly System.Collections.Generic.List<(Medallion M, double To, System.Func<double, string> Fmt, double At)> counts = new();
    // What is shown in turn: each thing, when, and its sound; and what goes to ash, and when.
    readonly System.Collections.Generic.List<(Control C, double At, System.Action? Sound)> beats = new();
    readonly System.Collections.Generic.HashSet<Control> shown = new();
    readonly System.Collections.Generic.HashSet<Medallion> landed = new();
    Control? ash;
    double ashAt, endAt, shownFor;
    /// <summary>Kept through a rebuild (a tome written), so the story is not told twice.</summary>
    bool told;
    double tick;
    const double Count = 0.9;

    /// <summary>Everything told (a press skipped the telling, or it ran its course).</summary>
    bool Told => told || shownFor >= endAt;

    public override void _Process(double delta)
    {
        base._Process(delta);
        shownFor += delta;
        tick -= delta;
        foreach (var (m, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(m)) continue;
            double k = Told ? 1 : Math.Clamp((shownFor - at) / Count, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            var t = fmt(to * k);
            if (t != m.Text) { m.Text = t; m.Arc = (float)k; m.QueueRedraw(); if (!Told && tick <= 0) { tick = 0.07; Sound.Sfx.Hover(); } }
            // (each number lands with a blow)
            if (k >= 1 && landed.Add(m) && !told) Sound.Sfx.Bash();
        }
        foreach (var (c, at, sound) in beats)
        {
            if (!IsInstanceValid(c)) continue;
            if (!shown.Contains(c) && (Told || shownFor >= at))
            {
                shown.Add(c);
                if (!told) sound?.Invoke();
            }
            // In from a little to the left, as a line is set down.
            float k = Told ? 1 : (float)Math.Clamp((shownFor - at) / 0.35, 0, 1);
            k = 1 - (1 - k) * (1 - k);
            c.Modulate = new Color(1, 1, 1, k);
            if (c.GetParent() is not BoxContainer) c.Position = c.Position with { X = (1 - k) * -18 };
        }
        // What stays goes grey, as the ember goes out.
        if (ash != null && IsInstanceValid(ash))
        {
            float k = Told ? 1 : (float)Math.Clamp((shownFor - ashAt) / 1.1, 0, 1);
            ash.Modulate = new Color(1, 1, 1, 1).Lerp(new Color(0.5f, 0.48f, 0.52f, 0.8f), k);
        }
    }

    /// <summary>Shown in its turn, with its sound.</summary>
    T Beat<T>(T c, double at, System.Action? sound = null) where T : Control
    {
        c.Modulate = new Color(1, 1, 1, 0);
        beats.Add((c, at, sound));
        endAt = Math.Max(endAt, at + 0.35);
        return c;
    }'''),
    ('''    protected override void Build()
    {
        HideHud();
        AddChild(new Backdrop(null, r.Won ? 0.82f : 0.9f));''', '''    protected override void Build()
    {
        HideHud();
        beats.Clear();
        shown.Clear();
        landed.Clear();
        if (shownFor > 0) told = true;
        AddChild(new Backdrop(null, r.Won ? 0.82f : 0.9f));'''),
    ('''        var tally = Style.H(48,
            Stat("hourglass", r.Seconds, Clock, r.Won ? "survived" : "held out", 0.2),
            Stat("skull", r.Kills, x => $"{x:N0}", "slain", 0.45),
            Stat("flame", r.EmberLevel, x => $"{x:0}", "ember", 0.7));
        if (r.Won && beyond >= 1) tally.AddChild(Stat("moon", beyond, Clock, "past the dead of night", 0.95));
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(tally);
        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center));
        // How it ended, and how near it came (docs/feel S-16: the end tells the run's story).
        var story = Story();
        if (story != "") wrap.AddChild(Style.Label(story, Style.TextItalic, Style.Body, r.Won ? Style.Ink : Style.BloodHi, true, HorizontalAlignment.Center));
''', '''        // Beat one: the night's numbers, counting up one after another.
        var tally = Style.H(48,
            Stat("hourglass", r.Seconds, Clock, r.Won ? "survived" : "held out", 0.5),
            Stat("skull", r.Kills, x => $"{x:N0}", "slain", 0.85),
            Stat("flame", r.EmberLevel, x => $"{x:0}", "ember", 1.2));
        double cue = 1.2 + Count;
        if (r.Won && beyond >= 1) { tally.AddChild(Stat("moon", beyond, Clock, "past the dead of night", 1.55)); cue = 1.55 + Count; }
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(tally);
        if (r.Longest && r.Seconds > 120)
            wrap.AddChild(Beat(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center), cue, Sound.Sfx.Discovery));
        cue += 0.4;
        // (how it ended, in a line, comes last: below)
        var story = Story();
'''),
    ('''        // What comes out, on a forged plate; what stays, on a slab gone to ash.
        var outv = Style.V(8, new Section("What you take out"));
        outv.AddChild(Line("book", $"{r.Xp:N0} experience" + (r.LevelsGained > 0 ? $"  ·  you are level {G.Journey.Ch.Level} now" : ""), r.LevelsGained > 0 ? Style.Good : Style.Ink));
        if (r.Gold > 0) outv.AddChild(Line("coin", $"{r.Gold:N0} gold", Style.GoldHi));
        // What the night left in the fist, for the Waystation's hands; on a fall, what spilled.
        if (r.Carried.Count > 0 || r.Spilled.Count > 0) outv.AddChild(Haul(r));
        // A tome won is the survivor's to write: one of what burned here.
        if (r.Inscribed is { } tome) outv.AddChild(Line("book", $"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")));
        else if (r.TomeChoices.Count > 0)
        {
            outv.AddChild(Line("book", "A blank tome: write it with one of what burned", new Color("#b8a8d8")));
            var pick = Style.H(8);
            foreach (var id in r.TomeChoices)
            {
                var w = Weapons.All[id];
                var btn = Style.Button(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) Refresh(); }, false, true);
                btn.TooltipText = $"{w.Description} By day it asks {SkillBook.Need} {SkillBook.Attribute(id)}.";
                pick.AddChild(btn);
            }
            outv.AddChild(pick);
        }
        foreach (var made in r.Recorded)
            outv.AddChild(Line("scroll", made.StartsWith("evo:") ? $"In the codex: {EvolutionName(made[4..])}" : $"In the codex: the union {Unions.Find(made[6..])?.Name}", Style.GoldHi));
        if (r.Taught is { } taught) outv.AddChild(Line("book", $"Your calling taught you {Weapons.All[taught].Name}", Style.Good));
        outv.AddChild(Style.Rule());
        outv.AddChild(Style.SubLabel(r.Discovered.Count > 0 ? "Discovered" : "Nothing new discovered"));
        foreach (var id in r.Discovered) outv.AddChild(Skill(id, true));
        if (r.Discovered.Count > 0)
            outv.AddChild(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        two.AddChild(Card(outv));''', '''        // Beat two: what comes out, on a forged plate, a line at a time with its sound, the best
        // last (what is counted, then what is carried, then what is learned, then what is new to
        // you: a level, a tome).
        var outv = Style.V(8, new Section("What you take out"));
        void Next(Control c, System.Action? sound, double gap = 0.42) { outv.AddChild(Beat(c, cue, sound)); cue += gap; }
        Next(Line("book", $"{r.Xp:N0} experience", Style.Ink), () => Sound.Sfx.Xp(6));
        if (r.Gold > 0) Next(Line("coin", $"{r.Gold:N0} gold", Style.GoldHi), Sound.Sfx.Gold);
        // What the night left in the fist, for the Waystation's hands; on a fall, what spilled.
        if (r.Carried.Count > 0 || r.Spilled.Count > 0) Next(Haul(r), () => Sound.Sfx.Loot(), 0.55);
        foreach (var made in r.Recorded)
            Next(Line("scroll", made.StartsWith("evo:") ? $"In the codex: {EvolutionName(made[4..])}" : $"In the codex: the union {Unions.Find(made[6..])?.Name}", Style.GoldHi), Sound.Sfx.Page);
        if (r.Discovered.Count > 0)
        {
            Next(Style.SubLabel("Discovered"), null, 0.2);
            foreach (var id in r.Discovered) Next(Skill(id, true), Sound.Sfx.Discovery, 0.38);
            Next(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, Style.Caption, Style.InkDim, true), null, 0.3);
        }
        if (r.Taught is { } taught) Next(Line("book", $"Your calling taught you {Weapons.All[taught].Name}", Style.Good), Sound.Sfx.Discovery);
        if (r.LevelsGained > 0) Next(Line("star", $"Level {G.Journey.Ch.Level}" + (r.LevelsGained > 1 ? $": {r.LevelsGained} levels in one night" : ""), Style.Good), Sound.Sfx.LevelUp, 0.6);
        // A tome won is the survivor's to write: one of what burned here (the best of a night, last).
        if (r.Inscribed is { } tome) Next(Line("book", $"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")), () => Sound.Sfx.Loot(true), 0.6);
        else if (r.TomeChoices.Count > 0)
        {
            Next(Line("book", "A blank tome: write it with one of what burned", new Color("#b8a8d8")), () => Sound.Sfx.Loot(true), 0.3);
            var pick = Style.H(8);
            foreach (var id in r.TomeChoices)
            {
                var w = Weapons.All[id];
                var btn = Style.Button(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) Refresh(); }, false, true);
                btn.TooltipText = $"{w.Description} By day it asks {SkillBook.Need} {SkillBook.Attribute(id)}.";
                pick.AddChild(btn);
            }
            Next(pick, null, 0.5);
        }
        if (r.Discovered.Count == 0) Next(Style.Label("Nothing new discovered.", Style.TextItalic, Style.Caption, Style.InkDim), null, 0.3);
        two.AddChild(Card(outv));'''),
    ('''        // What stays.
        var stay = Style.V(8, new Section("What stays in the arena"));
        if (G.Battle is { } b)
        {
            // The build the ember made, as grey medallions: it does not leave with you.
            var ash = new GridContainer { Columns = 5, MouseFilter = MouseFilterEnum.Ignore };
            ash.AddThemeConstantOverride("h_separation", 10);
            ash.AddThemeConstantOverride("v_separation", 10);
            Control Faded(string glyph, string name)
            {
                var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
                mc.AddChild(new Medallion(64, "", glyph) { Ring = Style.InkFaint, Ink = Style.InkDim, Core = new Color("#16131a") });
                var v = Style.V(2, mc, Style.Label(name, Style.Ui, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
                v.CustomMinimumSize = new Vector2(100, 0);
                return v;
            }
            foreach (var w in b.Weapons) ash.AddChild(Faded(w.Evolution?.Art ?? w.Def.Art, $"{w.Evolution?.Name ?? w.Def.Name} {Numeral(w.Rank)}"));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd) ash.AddChild(Faded(bd.Icon, bd.Max > 1 ? $"{bd.Name} {Numeral(rank)}" : bd.Name));
            stay.AddChild(ash);
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true));
        var stayCard = Card(stay, Style.Slab(18));
        stayCard.Modulate = new Color(1, 1, 1, 0.85f);
        two.AddChild(stayCard);

        string after = r.Spec.Story
            ? r.Won ? "The story goes on." : "The story goes on without the win. The Wayfinder will let you take this fight again."
            : r.Won ? "The Wayfinder will want to hear of it." : "The Wayfinder's table will have other maps.";
        wrap.AddChild(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center));''', '''        // Beat three: what stays, the build the ember made, lit as it was, then going to ash.
        var stay = Style.V(8, new Section("What stays in the arena"));
        if (G.Battle is { } b)
        {
            var grid = new GridContainer { Columns = 5, MouseFilter = MouseFilterEnum.Ignore };
            grid.AddThemeConstantOverride("h_separation", 10);
            grid.AddThemeConstantOverride("v_separation", 10);
            Control Kept(string glyph, string name)
            {
                var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
                mc.AddChild(new Medallion(64, "", glyph) { Ring = Style.Gold, Ink = Style.GoldHi, Core = new Color("#2a1a10") });
                var v = Style.V(2, mc, Style.Label(name, Style.Ui, Style.Caption, Style.Ink, true, HorizontalAlignment.Center));
                v.CustomMinimumSize = new Vector2(100, 0);
                return v;
            }
            foreach (var w in b.Weapons) grid.AddChild(Kept(w.Evolution?.Art ?? w.Def.Art, $"{w.Evolution?.Name ?? w.Def.Name} {Numeral(w.Rank)}"));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd) grid.AddChild(Kept(bd.Icon, bd.Max > 1 ? $"{bd.Name} {Numeral(rank)}" : bd.Name));
            stay.AddChild(grid);
            ash = grid;
        }
        cue += 0.3;
        ashAt = cue;
        stay.AddChild(Beat(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true), cue + 0.6, () => Sound.Sfx.Moment(0.1, 0.9f)));
        cue += 1.4;
        two.AddChild(Card(stay, Style.Slab(18)));

        // Beat four: how it went, in a line; what comes of it; and back to the road.
        string after = r.Spec.Story
            ? r.Won ? "The story goes on." : "The story goes on without the win. The Wayfinder will let you take this fight again."
            : r.Won ? "The Wayfinder will want to hear of it." : "The Wayfinder's table will have other maps.";
        if (story != "") wrap.AddChild(Beat(Style.Label(story, Style.TextItalic, Style.Body, r.Won ? Style.Ink : Style.BloodHi, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page));
        cue += 0.5;
        wrap.AddChild(Beat(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center), cue));
        cue += 0.3;'''),
    ('''        var acts = Style.H(12, go);
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(acts);
    }''', '''        var acts = Style.H(12, go);
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(Beat(acts, cue));
    }'''),
    ('''    public override bool Key(Act a)
    {
        if (a == Act.Confirm) { G.LeaveArena(r); return true; }''', '''    public override bool Key(Act a)
    {
        // The first press tells the rest at once; the next goes back to the road.
        if (a is Act.Confirm or Act.Cancel && !Told) { told = true; return true; }
        if (a == Act.Confirm) { G.LeaveArena(r); return true; }'''),
])
