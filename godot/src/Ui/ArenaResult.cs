using System;
using System.Linq;
using Godot;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>An arena over (Arena/Arena.cs), told as the night's story in
/// beats (the experience director's brief; the end of half an hour is what
/// the player remembers of it, the peak-end rule): the verdict; the night's
/// numbers counting up, each landing with a blow; what comes out, a line at a
/// time with its own sound, the best last; what stays (the build the ember
/// made) going to ash; then how it went, in a line, and back to the road.
/// A press tells it all at once; the next leaves.</summary>
public partial class ArenaResultScreen : TellingScreen
{
    readonly ArenaResult r;
    public override string Kind => "arena";
    Control? ash;
    double ashAt;
    public override bool Dismissable => false;

    public ArenaResultScreen(Game g, ArenaResult result) : base(g) => r = result;

    public override void _Process(double delta)
    {
        base._Process(delta);
        // What stays goes grey, as the ember goes out.
        if (ash == null || !IsInstanceValid(ash)) return;
        float k = Told ? 1 : (float)Math.Clamp((ShownFor - ashAt) / 1.1, 0, 1);
        ash.Modulate = new Color(1, 1, 1, 1).Lerp(new Color(0.5f, 0.48f, 0.52f, 0.8f), k);
    }

    protected override void Build()
    {
        HideHud();
        Retell();
        // (a click anywhere tells the rest at once)
        AddChild(new Backdrop(() => told = true, r.Won ? 0.82f : 0.9f));
        var wrap = Style.Centered(Style.V(14), new Vector2(1240, 900));
        AddChild(wrap);
        var tone = r.Won ? Style.EmberHi : Style.BloodHi;
        bool fell = G.Battle?.Player.Alive == false;
        // The verdict on a banner, the arena's name under it.
        var banner = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 30, r.Won ? Style.Gold : Style.BloodHi),
            Style.Label(!r.Won ? "THE EMBER GUTTERS" : fell ? "WON, AND HELD TO THE LAST" : "THE NIGHT IS HELD", Style.Display, 40, r.Won ? new Color("#ffe6b8") : Style.BloodHi, false, HorizontalAlignment.Center));
        banner.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        wrap.AddChild(banner);
        wrap.AddChild(Style.Label(r.Spec.Name, Style.TextItalic, Style.Lead, Style.GoldHi, false, HorizontalAlignment.Center));
        double beyond = r.Seconds - r.Spec.Minutes * 60;
        // Beat one: the night's numbers, counting up one after another.
        var tally = Style.H(48,
            Stat("hourglass", r.Seconds, Clock, r.Won ? "survived" : "held out", 0.5, r.Won),
            Stat("skull", r.Kills, x => $"{x:N0}", "slain", 0.85, r.Won),
            Stat("flame", r.EmberLevel, x => $"{x:0}", "ember", 1.2, r.Won));
        double cue = 1.2 + Count;
        if (r.Won && beyond >= 1) { tally.AddChild(Stat("moon", beyond, Clock, "past the dead of night", 1.55, r.Won)); cue = 1.55 + Count; }
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(tally);
        if (r.Longest && r.Seconds > 120)
            wrap.AddChild(Beat(Style.Label("Your longest night yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center), cue, Sound.Sfx.Discovery));
        cue += 0.4;
        // (how it ended and how near it came, in a line, comes last: below; docs/feel S-16)
        var story = Story();

        var two = Style.H(18);
        two.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(two);

        // Beat two: what comes out, on a forged plate, a line at a time with its sound, the best
        // last (what is counted, then what is carried, then what is learned, then what is new to
        // you: a level, a tome).
        var outv = Style.V(8, new Section("What you take out"));
        void Next(Control c, System.Action? sound, double gap = 0.42) { outv.AddChild(Beat(c, cue, sound)); cue += gap; }
        Next(Line("book", $"{r.Xp:N0} experience", Style.Ink), () => Sound.Sfx.Xp(6, 1, false, false));
        if (r.Gold > 0) Next(Line("coin", $"{r.Gold:N0} gold", Style.GoldHi), Sound.Sfx.Gold);
        // What the night left in the fist, for the Waystation's hands; on a fall, what spilled.
        if (r.Carried.Count > 0 || r.Spilled.Count > 0) Next(Haul(r.Carried, r.Spilled, "Carried out, for the Waystation's hands"), () => Sound.Sfx.Loot(), 0.55);
        foreach (var made in r.Recorded)
            Next(Line("scroll", made.StartsWith("evo:") ? $"In the codex: {EvolutionName(made[4..])}" : $"In the codex: the union {Unions.Find(made[6..])?.Name}", Style.GoldHi), Sound.Sfx.Page);
        if (r.Discovered.Count > 0)
        {
            Next(Style.SubLabel("Discovered"), null, 0.2);
            foreach (var id in r.Discovered) Next(Skill(id, true), Sound.Sfx.Discovery, 0.38);
            Next(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, Style.Caption, Style.InkDim, true), null, 0.3);
        }
        if (r.Taught is { } taught) Next(Line("book", $"Your calling taught you {Weapons.All[taught].Name}", Style.Good), Sound.Sfx.Discovery);
        if (r.LevelsGained > 0) Next(Line("star", $"Level {G.Journey.Ch.Level}" + (r.LevelsGained > 1 ? $": {r.LevelsGained} levels in one night" : ""), Style.Good), () => Sound.Sfx.LevelUp(), 0.6);
        // A tome won is the survivor's to write: one of what burned here (the best of a night, last).
        if (r.Inscribed is { } tome) Next(Line("book", $"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")), () => Sound.Sfx.Loot(true), 0.6);
        else if (r.TomeChoices.Count > 0)
        {
            Next(Line("book", "A blank tome: write it with one of what burned", new Color("#b8a8d8")), () => Sound.Sfx.Loot(true), 0.3);
            var pick = Style.H(8);
            foreach (var id in r.TomeChoices)
            {
                var w = Weapons.All[id];
                var btn = Style.Button(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) { told = true; Refresh(); } }, false, true);
                btn.TooltipText = $"{w.Description} By day it asks {SkillBook.Need} {SkillBook.Attribute(id)}.";
                pick.AddChild(btn);
            }
            Next(pick, null, 0.5);
        }
        if (r.Discovered.Count == 0) Next(Style.Label("Nothing new discovered.", Style.TextItalic, Style.Caption, Style.InkDim), null, 0.3);
        two.AddChild(Card(outv));

        // Beat three: what stays, the build the ember made, lit as it was, then going to ash.
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
        stay.AddChild(Beat(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true), cue + 0.6));
        cue += 1.4;
        two.AddChild(Card(stay, Style.Slab(18)));

        // Beat four: how it went, in a line; then a story night's narrator line for how it went
        // (docs/WRITING_PASS.md §20), a lost one saying where it waits; a table night ends with the
        // Wayfinder, who writes it down; and back to the road.
        string after = r.Spec.Story
            ? r.Won ? (r.Spec.Spared ? r.Spec.EndSpared : null) ?? r.Spec.EndWon ?? "The valley will hear of it." : r.Spec.EndLost ?? "The valley will hear of it."
            : r.Won ? "The Wayfinder will want it for her margins." : "The Wayfinder's table will have other maps.";
        if (story != "") wrap.AddChild(Beat(Style.Label(story, Style.TextItalic, Style.Body, r.Won ? Style.Ink : Style.BloodHi, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page));
        cue += 0.5;
        wrap.AddChild(Beat(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center), cue));
        cue += 0.3;
        if (r.Spec.Story && !r.Won)
        {
            wrap.AddChild(Beat(Style.Label("The fight waits on the Wayfinder's table, to be taken again.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center), cue));
            cue += 0.3;
        }
        // (the autopilot's Confirm, like a player's, first tells the rest, then leaves)
        wrap.AddChild(Beat(Onward("Back to the road", () => G.LeaveArena(r)), cue));
    }

    static string EvolutionName(string id) => Weapons.All.Values.SelectMany(w => w.Evolutions).FirstOrDefault(e => e.Id == id)?.Name ?? id;

    /// <summary>The run's ending in a line: who brought you down and when, and how near the end was.</summary>
    string Story()
    {
        string boss = r.Spec.BossName ?? SurvivorUnchained.Maps.MapOffers.People(r.Spec.People).BossName;
        double end = r.Spec.Minutes * 60;
        var parts = new System.Collections.Generic.List<string>();
        if (G.LastFall is var (killer, at) && G.Battle?.Player.Alive == false) parts.Add($"Brought down by {killer} at {Clock(at)}");
        if (!r.Won)
        {
            if (r.Seconds < end) { int m = (int)Math.Ceiling((end - r.Seconds) / 60); parts.Add($"{m} minute{(m == 1 ? "" : "s")} before {SurvivorUnchained.Maps.MapOffers.InSentence(boss)} would have come"); }
            else parts.Add($"{boss} still stands");
        }
        return string.Join(";  ", parts) + (parts.Count > 0 ? "." : "");
    }

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
    static string Numeral(int n) => n >= 0 && n < Numerals.Length ? Numerals[n] : n.ToString();

    static Control Skill(string id, bool fresh)
    {
        var (icon, name, what) = Weapons.All.TryGetValue(id, out var w) ? (w.Art, w.Name, "combat skill")
            : Boons.Find(id) is { } bd ? (bd.Icon, bd.Name, "passive skill") : ("scroll", id, "");
        var col = fresh ? new Color("#b8a8d8") : Style.InkDim;
        return Style.H(8, Glyphs.Icon(icon, 22, col), Style.V(0, Style.Label(name, Style.UiBold, Style.Small, col), Style.Label(what, Style.TextItalic, Style.Caption, Style.InkDim)));
    }

    public override bool Key(Act a)
    {
        // The first press tells the rest at once; the next goes back to the road.
        if (a is Act.Confirm or Act.Cancel && !Told) { told = true; return true; }
        if (a == Act.Confirm) { G.LeaveArena(r); return true; }
        // Nothing else leaves it: the arena's end is read, not skipped by a stray key.
        return a is not (Act.Up or Act.Down or Act.Left or Act.Right);
    }
}
