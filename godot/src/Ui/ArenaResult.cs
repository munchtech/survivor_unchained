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

    /// <summary>
    /// One panel over the world, fitted, as the map's end is: the verdict between the chains; the
    /// night's numbers as a ledger line; what comes out at the left, set close (its lines ran past
    /// the fold at 1080 and scrolled) and the best last; what stays at the right, going to ash; then
    /// how it ended, in a line, and the way back, there from the first moment.
    /// </summary>
    protected override void Build()
    {
        Retell();
        bool fell = G.Battle?.Player.Alive == false;
        var v = ResultPanel(!r.Won ? "The ember gutters" : fell ? "Won, and held to the last" : "The night is held", r.Won ? new Color("#ffe6b8") : Style.BloodHi, r.Spec.Name);
        double beyond = r.Seconds - r.Spec.Minutes * 60;
        // Beat one: the night's numbers, counting up one after another.
        var stats = new System.Collections.Generic.List<(double, Func<double, string>, string, double, bool)>
        {
            // (a written story night has no clock to survive: its time is how long the fight took)
            (r.Seconds, Clock, !r.Won ? "held out" : SurvivorUnchained.Play.Story.StoryScripts.Has(r.Spec.Id) ? "fought" : "survived", 0.3, r.Won),
            (r.Kills, x => $"{x:N0}", "slain", 0.55, r.Won), (r.EmberLevel, x => $"{x:0}", "ember", 0.8, r.Won),
        };
        double cue = 0.8 + Count;
        if (r.Won && beyond >= 1) { stats.Add((beyond, Clock, "past the dead of night", 1.05, r.Won)); cue = 1.05 + Count; }
        v.AddChild(Tally(stats.ToArray()));
        if (r.Longest && r.Seconds > 120)
        {
            v.AddChild(Beat(Style.Label("Your longest night yet", Style.TextItalic, 18, Style.EmberHi, false, HorizontalAlignment.Center), cue, Sound.Sfx.Discovery));
            cue += 0.3;
        }
        var story = Story();

        // Beat two: what comes out, told down the panel as centred ledger lines (it was a column
        // beside a near-empty one): what is counted and carried, what is learned, then what is new
        // to you (a level, a tome).
        Register(v, "What you take out");
        void Next(Control c, Action? sound, double gap = 0.32) { v.AddChild(Beat(c, cue, sound)); cue += gap; }
        Control Mid(string text, Color c, int size = 17, Font? font = null) => Style.Label(text, font ?? Style.UiBold, size, c, true, HorizontalAlignment.Center);
        // The experience and the gold on one line; under it what the night left in the fist, for the
        // Waystation's hands, and on a fall what spilled after it (on one line the two ran past the panel).
        var earned = new System.Collections.Generic.List<Control> { Sum(Glyphs.Icon("book", 22, Kit.Ink), $"{r.Xp:N0} experience", Kit.Ink) };
        if (r.Gold > 0) earned.Add(Sum(Glyphs.Icon("coin", 24, Style.GoldHi), $"{r.Gold:N0} gold", Style.GoldHi));
        Next(LedgerLine(earned), () => { Sound.Sfx.Xp(6, 1, false, false); if (r.Gold > 0) Sound.Sfx.Gold(); }, 0.3);
        if (r.Carried.Count > 0 || r.Spilled.Count > 0)
            Next(LedgerLine(r.Carried.Select(kv => Counted(kv.Key, kv.Value)), r.Spilled), () => Sound.Sfx.Loot(), 0.4);
        if (r.HaulSeen is { } seen) Next(Mid(seen, Kit.Dim, 15, Style.TextItalic), null, 0.3);
        foreach (var made in r.Recorded)
            Next(Mid(made.StartsWith("evo:") ? $"In the codex: {EvolutionName(made[4..])}" : $"In the codex: the union {Unions.Find(made[6..])?.Name}", Style.GoldHi), Sound.Sfx.Page);
        if (r.Discovered.Count > 0)
        {
            // The skills found, side by side under one line that says what they are for.
            var found = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = FlowContainer.AlignmentMode.Center };
            found.AddThemeConstantOverride("h_separation", 32);
            found.AddThemeConstantOverride("v_separation", 8);
            foreach (var id in r.Discovered) found.AddChild(Skill(id, true));
            Next(Style.V(8, Mid("DISCOVERED  ·  to be learned by day, from tomes and from your calling", Kit.HeadInk, 12, Style.UiHeavy), found), Sound.Sfx.Discovery, 0.45);
        }
        if (r.Taught is { } taught) Next(Mid($"Your calling taught you {Weapons.All[taught].Name}", Style.Good), Sound.Sfx.Discovery);
        if (r.LevelsGained > 0) Next(Mid($"Level {G.Journey.Ch.Level}" + (r.LevelsGained > 1 ? $": {r.LevelsGained} levels in one night" : ""), Style.Good, 20), () => Sound.Sfx.LevelUp(), 0.45);
        // A tome won is the survivor's to write: one of what burned here (the best of a night, last).
        if (r.Inscribed is { } tome) Next(Mid($"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")), () => Sound.Sfx.Loot(true), 0.45);
        else if (r.TomeChoices.Count > 0)
        {
            var pick = Style.H(18, Style.Label("A blank tome, to write with one of what burned:", Style.Ui, 16, new Color("#b8a8d8")));
            pick.Alignment = BoxContainer.AlignmentMode.Center;
            foreach (var id in r.TomeChoices)
            {
                var w = Weapons.All[id];
                var word = Kit.Word(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) { told = true; Refresh(); } }, new Color("#d8c8f0"), 16);
                word.TooltipText = $"{w.Description} By day it asks {SkillBook.Need} {SkillBook.Attribute(id)}.";
                pick.AddChild(word);
            }
            Next(pick, () => Sound.Sfx.Loot(true), 0.45);
        }

        // Beat three: what stays, the build the ember made, lit as it was across the panel, then going to ash.
        if (G.Battle is { } b)
        {
            Register(v, "What stays in the arena");
            var grid = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = FlowContainer.AlignmentMode.Center };
            grid.AddThemeConstantOverride("h_separation", 12);
            grid.AddThemeConstantOverride("v_separation", 10);
            Control Kept(string glyph, string name)
            {
                var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
                mc.AddChild(new Medallion(56, "", glyph) { Ring = Style.Gold, Ink = Style.GoldHi, Core = new Color("#2a1a10") });
                var kv = Style.V(4, mc, Style.Label(Kit.Balance(name, Style.Ui, 14, 104), Style.Ui, 14, Kit.Ink2, false, HorizontalAlignment.Center, true));
                kv.CustomMinimumSize = new Vector2(112, 0);
                return kv;
            }
            foreach (var w in b.Weapons) grid.AddChild(Kept(w.Evolution?.Art ?? w.Def.Art, $"{w.Evolution?.Name ?? w.Def.Name} {Numeral(w.Rank)}"));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd) grid.AddChild(Kept(bd.Icon, bd.Max > 1 ? $"{bd.Name} {Numeral(rank)}" : bd.Name));
            v.AddChild(grid);
            ash = grid;
            ashAt = cue + 0.2;
            v.AddChild(Beat(Mid("The ember goes out with the arena. The next one starts from nothing.", Kit.Dim, 15, Style.TextItalic), cue + 0.6));
            cue += 0.9;
        }

        // Beat four: how it ended, and the story's own line for it; the way back has been there all along.
        string after = r.Spec.Story
            ? r.Won ? (r.Spec.Spared ? r.Spec.EndSpared : null) ?? r.Spec.EndWon ?? "The valley will hear of it." : r.Spec.EndLost ?? "The valley will hear of it."
            : r.Won ? "The Wayfinder will want it for her margins." : "The Wayfinder's table will have other maps.";
        if (r.Spec.Story && !r.Won) after += " It will be there again tomorrow night.";
        v.AddChild(Kit.RuleH());
        if (story != "") { v.AddChild(Beat(Style.Label(story, Style.TextItalic, 18, r.Won ? Kit.Ink : Style.BloodHi, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page)); cue += 0.4; }
        v.AddChild(Beat(Style.Label(after, Style.TextItalic, 18, Kit.Ink2, true, HorizontalAlignment.Center), cue));
        // (the autopilot's Confirm, like a player's, first tells the rest, then leaves)
        v.AddChild(OnwardWord("Back to the road", () => G.LeaveArena(r)));
    }

    static string EvolutionName(string id) => Weapons.All.Values.SelectMany(w => w.Evolutions).FirstOrDefault(e => e.Id == id)?.Name ?? id;

    /// <summary>The run's ending in a line: who brought you down and when, and how near the end was.</summary>
    string Story()
    {
        string boss = r.Spec.BossName ?? SurvivorUnchained.Maps.MapOffers.People(r.Spec.People).BossName;
        double end = r.Spec.Minutes * 60;
        var parts = new System.Collections.Generic.List<string>();
        if (G.LastFall is var (killer, at) && G.Battle?.Player.Alive == false) parts.Add($"Brought down by {killer} at {Clock(at)}");
        // A written story night has no clock (its boss comes when its stages are done), so it says nothing
        // of minutes before the boss; its own last line says the rest.
        if (!r.Won && !SurvivorUnchained.Play.Story.StoryScripts.Has(r.Spec.Id))
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
