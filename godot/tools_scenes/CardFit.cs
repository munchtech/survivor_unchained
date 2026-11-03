using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;
using Paths = SurvivorUnchained.Content.Paths;
using Weapons = SurvivorUnchained.Content.Weapons;

namespace SurvivorUnchained.Tools;

/// <summary>
/// Every offer a calling can be dealt (all four callings), laid out three to a row in a real DraftPanel at
/// 1920x1080, twice: as dealt, and with the worst-case footer that kind can carry (its two longest why lines,
/// tags, a path name; the recipe is the detail strip's, checked to fit its two lines), so no future combination exceeds what was checked. Per card: the body's last
/// line against the footer's top, the footer inside the card, the medallion, title and footer level across the
/// row, and no line hidden. A JSON report; exit 1 on any failure, printed. tools_scenes/card_fit.gd runs it:
///   Godot --headless --path godot -s res://tools_scenes/card_fit.gd -- OUT.json [--calling ID]
///   Godot --path godot -s res://tools_scenes/card_fit.gd -- OUT.json --sheet   (also shoots the rows of the six
///   least-slack cards at 1:1, as the game shows them, to godot/.shots/card_fit_N.png)
/// tests/DraftCardFitTests.cs runs it headless.
/// </summary>
public partial class CardFit : Node
{
    const int Batch = 12, Settle = 10;
    static readonly string[] AllCallings = ["warden", "arcanist", "reaver", "stalker"];

    sealed class Job
    {
        public string Calling = "", State = "", Pass = "";
        public Battle B = null!;
        public List<Offer> Offers = new();
        public HashSet<Tag> Build = new();
        public bool Blessing;
        public string? Great;
    }

    sealed class Row
    {
        public string Calling = "", State = "", Pass = "", Kind = "", Id = "", Title = "";
        public int Font, Lines, Visible, Job, Card;
        public string Text = "";
        public float Slack, Overlap, Short, BodyH, FootH, Above;
        public List<string> Fails = new();
    }

    readonly List<Job> jobs = new();
    readonly List<Row> rows = new();
    readonly List<string> fails = new();
    readonly List<(Job J, DraftPanel P)> live = new();
    string outPath = "";
    bool sheet;
    int next, wait, stripCards;
    SubViewport vp = null!;
    // The sheet: the rows to shoot, the one up now, its clock.
    List<(int Job, int Card)> shots = new();
    int shot = -1;
    double clock;
    DraftPanel? shotPanel;

    public override void _Ready()
    {
        var a = OS.GetCmdlineUserArgs();
        outPath = a.Length > 0 && !a[0].StartsWith("--") ? a[0] : ProjectSettings.GlobalizePath("res://.shots/card_fit.json");
        sheet = a.Contains("--sheet");
        int ci = Array.IndexOf(a, "--calling");
        string[] callings = ci >= 0 && ci + 1 < a.Length ? [a[ci + 1]] : AllCallings;
        AddChild(new Controls());
        vp = new SubViewport { Size = new Vector2I(1920, 1080), RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled, TransparentBg = false, GuiDisableInput = true };
        AddChild(vp);
        foreach (var c in callings) Gather(c);
        GD.Print($"card_fit: {jobs.Count} rows of up to three ({jobs.Sum(j => j.Offers.Count)} cards) over {string.Join(", ", callings)}");
    }

    public override void _Process(double delta)
    {
        if (shot >= 0) { Shoot(delta); return; }
        if (wait > 0) { wait--; return; }
        foreach (var (j, p) in live) { Measure(jobs.IndexOf(j), j, p); p.GetParent().QueueFree(); }
        live.Clear();
        if (next >= jobs.Count) { Finish(); return; }
        for (int k = 0; k < Batch && next < jobs.Count; k++, next++) live.Add((jobs[next], Lay(vp, jobs[next])));
        wait = Settle;
    }

    static DraftPanel Lay(Node into, Job j)
    {
        var host = new Control { Size = new Vector2(1920, 1080), MouseFilter = Control.MouseFilterEnum.Ignore };
        into.AddChild(host);
        var view = new DraftView(LevelUp.DraftLevel(j.B), j.Blessing, j.Offers, 3, 2, 0, null, j.Build, _ => { }, () => { }, _ => { }, j.Great, j.B);
        var p = new DraftPanel(view);
        host.AddChild(p);
        // The detail strip's text for each card with a recipe, laid out off screen at the strip's width (Measure counts its lines).
        for (int i = 0; i < j.Offers.Count; i++)
        {
            if (DraftPanel.DetailText(j.Offers[i]) is not { Length: > 0 } t) continue;
            var strip = DraftPanel.DetailLabel();
            strip.Name = $"Strip{i}";
            strip.Text = t;
            strip.MaxLinesVisible = -1;
            strip.Position = new Vector2(-5000, 0);
            strip.Size = new Vector2(DraftPanel.DetailW, 400);
            host.AddChild(strip);
        }
        return p;
    }

    // ---- the offers -------------------------------------------------------------------------------------------

    static StatBlock Stats()
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 140, [Stat.Regen] = 0, [Stat.Armor] = 2, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4,
            [Stat.CritChance] = 0.05, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        return s;
    }

    static Battle Make(string calling, IEnumerable<(string, int)> weapons, RoadDef? road = null)
    {
        var b = new Battle(new BattleSetup { Seed = 7, Collision = new CollisionWorld(120), Combat = true, Stats = Stats(), Weapons = weapons.ToList(), Ability = AbilityKind.ShieldBash });
        b.Calling = calling;
        b.Favours.UnionWith(Callings.Archetype(calling).Favours);
        b.CallingPaths.UnionWith(Paths.All.Where(p => p.Callings.Contains(calling)).Select(p => p.Id));
        b.EmberOn = true;
        b.Night = true;
        road ??= Lamps.Roads.Values.FirstOrDefault(r => r.Calling == calling);
        if (road != null) b.Lamps = new LampLoadout { Lean = road.Id };
        return b;
    }

    readonly HashSet<string> seen = new();

    /// <summary>The whole pool for a state (Draft takes from every pool until empty), kept where not seen before.</summary>
    void Deal(string calling, string state, Battle b, bool blessing = false, string? great = null, List<Offer>? given = null)
    {
        List<Offer> got;
        try { got = given ?? LevelUp.Draft(b, 99); }
        catch (Exception e) { fails.Add($"{calling} {state}: Draft threw {e.GetType().Name}: {e.Message}"); return; }
        var fresh = new List<Offer>();
        foreach (var o in got)
        {
            // (the badge a held skill's catalyst wears sits in the upper words: part of what the card is)
            var ev = o.Kind == OfferKind.Boon ? b.Weapons.FirstOrDefault(w => w.Evolution == null && LevelUp.EvolvesWith(w.Id).Any(e => e.Passives.Contains(o.Id)))?.Def.Name : null;
            var key = string.Join("|", o.Kind, o.Id, o.Branch, o.From, o.To, o.Title, o.Text, string.Join("/", o.Why), o.Recipe, o.Path, ev, o.Great, o.Blessing);
            if (seen.Add(key)) fresh.Add(o);
        }
        var build = LevelUp.BuildTags(b);
        var all = Enum.GetValues<Tag>().ToHashSet();
        for (int i = 0; i < fresh.Count; i += 3)
        {
            var three = fresh.Skip(i).Take(3).ToList();
            jobs.Add(new Job { Calling = calling, State = state, Pass = "dealt", B = b, Offers = three, Build = build, Blessing = blessing, Great = great });
            jobs.Add(new Job { Calling = calling, State = state, Pass = "worst", B = b, Offers = three.Select(Worst).ToList(), Build = all, Blessing = blessing, Great = great });
        }
    }

    static readonly string LongRoad = "Your road: " + Lamps.Roads.Values.OrderByDescending(r => r.Name.Length).First().Name;
    static readonly string LongPath = Paths.All.OrderByDescending(p => p.Name.Length).First().Id;
    static readonly string LongPathName = Paths.All.OrderByDescending(p => p.Name.Length).First().Name;
    static readonly string LongWeapon = Weapons.All.Values.OrderByDescending(w => w.Name.Length).First().Name;
    static string Longest(params string[] s) => s.OrderByDescending(x => x.Length).First();

    /// <summary>The card with the fullest footer its kind can carry (LevelUp's why lines, at their longest).</summary>
    static Offer Worst(Offer o)
    {
        var w = new Offer
        {
            Kind = o.Kind, Blessing = o.Blessing, Great = o.Great, Id = o.Id, Branch = o.Branch, Rarity = o.Rarity, Title = o.Title, Text = o.Text,
            Icon = o.Icon, From = o.From, To = o.To, Tags = o.Tags, Surge = o.Surge, Attuned = o.Attuned, Recipe = o.Recipe, Path = o.Path,
        };
        string[] why = o.Kind switch
        {
            // (Banked and Familiar never meet; Banked, then a road, a surge or the calling's lean)
            OfferKind.Weapon => ["Banked: it wakes at rank 8", Longest("Surge: it comes a rank higher", "Suits your calling", LongRoad)],
            OfferKind.Rank => ["Surge: two ranks at once", LongRoad],
            OfferKind.Boon when o.Great => ["Suits your calling"],
            OfferKind.Boon when o.Blessing => [$"For {LongPathName}", "A duo: two of your families at once"],
            // (a trap and a catalyst never meet: little use is said only when it evolves nothing)
            OfferKind.Boon => ["Surge: two ranks at once", Longest("Little use to what you carry now", $"Evolves {LongWeapon} now")],
            _ => [],
        };
        w.Why.AddRange(why);
        if (o.Kind is OfferKind.Weapon or OfferKind.Evolve or OfferKind.Union || o.Kind == OfferKind.Boon && !o.Blessing) w.Path = LongPath;
        return w;
    }

    void Gather(string calling)
    {
        var pool = Weapons.Pool.Where(id => Weapons.CanCarry(calling, id)).ToList();
        // Her own first: the skills her paths list, then the rest.
        var mine = Paths.All.Where(p => p.Callings.Contains(calling)).SelectMany(p => p.Weapons).Where(pool.Contains).Distinct().ToList();
        var w0 = mine.FirstOrDefault() ?? pool[0];
        var chunks = new List<List<string>>();
        for (int i = 0; i < pool.Count; i += Weapons.MaxWeapons) chunks.Add(pool.Skip(i).Take(Weapons.MaxWeapons).ToList());
        var passives = Boons.Order.Where(id => Boons.All[id].Kind == BoonKind.Passive).ToList();
        var blessings = Boons.Order.Where(id => Boons.All[id].Kind == BoonKind.Blessing).ToList();

        // A fresh night, by each road: the new combat skills with her Hand, the passives; banked and familiar.
        foreach (var road in Lamps.Roads.Values.Where(r => r.Calling == calling).DefaultIfEmpty(null))
        {
            var b = Make(calling, [(w0, 1)], road);
            for (int i = 0; i < pool.Count; i++) if (i % 2 == 0) b.Attuned[pool[i]] = 3; else b.Familiar.Add(pool[i]);
            Deal(calling, $"fresh{(road != null ? ":" + road.Id : "")}", b);
            var plain = Make(calling, [(w0, 1)], road);
            Deal(calling, "fresh:plain", plain);
        }
        // The great blessings: fresh (with her Flare, its own greats too), then each deeper rank.
        {
            var b = Make(calling, [(w0, 1)]);
            b.Flare = Lamps.Flares.Values.FirstOrDefault(f => f.Calling == calling) ?? Lamps.Flares.Values.First();
            b.GreatOwed = 1;
            Deal(calling, "great", b, great: "Dusk: the ember wakes, and any of them is yours");
            int deepest = Boons.Great.Concat(Boons.FlareGreat).Max(id => Boons.All[id].Max);
            for (int r = 1; r < deepest; r++)
            {
                var d = Make(calling, [(w0, 1)]);
                d.Flare = b.Flare;
                d.GreatOwed = 1;
                foreach (var id in Boons.Great.Concat(Boons.FlareGreat)) if (Boons.All[id].Max > r) d.Boons[id] = r;
                Deal(calling, $"great:r{r + 1}", d, great: "Midnight: a second, or the first deepened");
            }
        }
        foreach (var (chunk, ci) in chunks.Select((c, i) => (c, i)))
        {
            // Ranks 1-7 held: the rank cards and their rank-7/8 hints (the catalyst wanted, held, stood in for,
            // or the passives full), the passives' "Evolves X at rank 8" notes.
            for (int r = 1; r < Weapons.MaxRank; r++)
            {
                Deal(calling, $"c{ci}:r{r}", Make(calling, chunk.Select(id => (id, r))));
                if (r < Weapons.MaxRank - 2) continue;
                var cats = chunk.SelectMany(id => LevelUp.EvolvesWith(id).SelectMany(e => e.Passives)).Distinct().ToHashSet();
                var held = Make(calling, chunk.Select(id => (id, r)));
                foreach (var c in cats) held.Boons[c] = 1;
                Deal(calling, $"c{ci}:r{r}:catalysts", held);
                var stands = Make(calling, chunk.Select(id => (id, r)));
                stands.Stands.UnionWith(cats);
                Deal(calling, $"c{ci}:r{r}:stands", stands);
                var full = Make(calling, chunk.Select(id => (id, r)));
                foreach (var p in passives.Where(p => !cats.Contains(p)).Take(Boons.MaxPassives)) full.Boons[p] = 1;
                Deal(calling, $"c{ci}:r{r}:full", full);
            }
            // A milestone's blessings, with every passive held (what some of them ask), and each deeper rank.
            var m = Make(calling, chunk.Select(id => (id, 4)));
            foreach (var p in passives) m.Boons[p] = 1;
            m.PendingBlessings.Add(10);
            Deal(calling, $"c{ci}:blessing", m, blessing: true);
            int deep = blessings.Max(id => Boons.All[id].Max);
            for (int r = 1; r < deep; r++)
            {
                var d = Make(calling, chunk.Select(id => (id, 4)));
                foreach (var p in passives) d.Boons[p] = 1;
                foreach (var id in blessings) if (Boons.All[id].Max > r) d.Boons[id] = r;
                d.PendingBlessings.Add(10);
                Deal(calling, $"c{ci}:blessing:r{r + 1}", d, blessing: true);
            }
        }
        // The passives deeper: every rank of every passive held.
        int pdeep = passives.Max(id => Boons.All[id].Max);
        for (int r = 1; r < pdeep; r++)
        {
            var d = Make(calling, [(w0, 1)]);
            foreach (var p in passives) if (Boons.All[p].Max > r) d.Boons[p] = r;
            Deal(calling, $"passives:r{r}", d);
        }
        // Evolution, one skill at a time, every branch it has earned; then honing it, by each branch.
        foreach (var id in pool.Where(id => Weapons.All[id].Evolutions.Length > 0))
        {
            var b = Make(calling, [(id, Weapons.MaxRank)]);
            foreach (var c in LevelUp.EvolvesWith(id).SelectMany(e => e.Passives)) b.Boons[c] = 1;
            Deal(calling, $"evolve:{id}", b);
            foreach (var evo in Weapons.All[id].Evolutions)
            {
                var h = Make(calling, [(id, Weapons.MaxRank)]);
                h.Evolve(id, evo.Id);
                Deal(calling, $"hone:{evo.Id}", h);
            }
        }
        // Finished and never evolving: honing too.
        Deal(calling, "hone:plain", Make(calling, pool.Where(id => Weapons.All[id].Evolutions.Length == 0).Take(Weapons.MaxWeapons).Select(id => (id, Weapons.MaxRank))));
        // The unions, both halves evolved.
        foreach (var u in Unions.All.Where(u => Weapons.CanCarry(calling, u.Id) && pool.Contains(u.A) && pool.Contains(u.B)))
        {
            var b = Make(calling, [(u.A, Weapons.MaxRank), (u.B, Weapons.MaxRank)]);
            b.Evolve(u.A, Weapons.All[u.A].Evolutions[0].Id);
            b.Evolve(u.B, Weapons.All[u.B].Evolutions[0].Id);
            Deal(calling, $"union:{u.Id}", b);
        }
        // The Respite, when nothing is left.
        var respite = (List<Offer>)typeof(LevelUp).GetMethod("Respite", BindingFlags.NonPublic | BindingFlags.Static)!.Invoke(null, [false, false])!;
        Deal(calling, "respite", Make(calling, [(w0, 1)]), given: respite);
    }

    // ---- the measure ------------------------------------------------------------------------------------------

    void Measure(int ji, Job j, DraftPanel p)
    {
        var laid = p.Laid.ToList();
        var level = new List<(float Medal, float Title, float FootBottom)>();
        for (int i = 0; i < laid.Count; i++)
        {
            var (card, top, foot, body) = laid[i];
            var o = j.Offers[i];
            var words = card.GetChild<Control>(1);
            var at = words.GetGlobalRect().Position;
            float Y(Control c) => c.GetGlobalRect().Position.Y - at.Y;
            float Bottom(Control c) => c.GetGlobalRect().End.Y - at.Y;
            float footTop = Y(foot), bodyTop = Y(body), bodyH = body.Size.Y;
            int lines = body.GetLineCount(), vis = Math.Min(lines, body.GetVisibleLineCount());
            float textH = 0;
            for (int k = 0; k < vis; k++) textH += body.GetLineHeight(k);
            textH += Math.Max(0, vis - 1) * body.GetThemeConstant("line_spacing");
            float textBottom = textH < bodyH ? bodyTop + (bodyH + textH) / 2 : bodyTop + textH;
            var row = new Row
            {
                Calling = j.Calling, State = j.State, Pass = j.Pass, Kind = o.Kind.ToString(), Id = o.Id + (o.Branch != null ? ":" + o.Branch : ""), Title = o.Title,
                Font = body.GetThemeFontSize("font_size"), Lines = lines, Visible = vis, Job = ji, Card = i, Text = o.Text,
                Overlap = textBottom - footTop, Slack = footTop - Style.Gap2 - bodyTop - textH,
                Short = (lines - vis) * (body.GetLineHeight() + body.GetThemeConstant("line_spacing")), BodyH = bodyH, FootH = foot.Size.Y,
            };
            // (slack counts what is hidden: a trimmed card is as far short as its missing lines)
            row.Slack -= row.Short;
            if (row.Overlap > 0.5f) row.Fails.Add($"body overlaps the footer by {row.Overlap:0} px");
            if (vis < lines) row.Fails.Add($"body truncated: {vis} of {lines} lines shown");
            // Nothing above the body reaches the footer (the title, the badge, the pips).
            float above = top.GetChildren().OfType<Control>().Where(c => c != body && c.Visible).Select(Bottom).DefaultIfEmpty(0).Max();
            row.Above = above;
            if (above > footTop + 0.5f) row.Fails.Add($"upper words reach {above - footTop:0} px into the footer");
            var cr = card.GetGlobalRect();
            // (the words still rising in: the footer where it comes to rest)
            var fr = foot.GetGlobalRect();
            fr.Position -= words.Position - (Vector2)words.GetMeta("home");
            if (fr.Position.Y < cr.Position.Y - 0.5f || fr.End.Y > cr.End.Y + 0.5f || fr.Position.X < cr.Position.X - 0.5f || fr.End.X > cr.End.X + 0.5f)
                row.Fails.Add($"footer outside the card (footer {fr.Position.X - cr.Position.X:0},{fr.Position.Y - cr.Position.Y:0} {fr.Size.X:0}x{fr.Size.Y:0} in a {cr.Size.X:0}x{cr.Size.Y:0} card)");
            // The detail strip: this card's recipe fits its two lines.
            if (p.GetParent().GetNodeOrNull<Label>($"Strip{i}") is { } strip)
            {
                stripCards++;
                if (strip.GetLineCount() > 2) row.Fails.Add($"detail strip needs {strip.GetLineCount()} lines (2 shown): \"{strip.Text}\"");
            }
            level.Add((Y(top.GetChild<Control>(1)), Y(top.GetChild<Control>(2)), Bottom(foot)));
            rows.Add(row);
        }
        // Across the row: the medallions, the titles and the footers' baseline level.
        if (level.Count > 1)
        {
            var mine = rows.Skip(rows.Count - level.Count).ToList();
            void Level(Func<(float Medal, float Title, float FootBottom), float> of, string what)
            {
                float lo = level.Min(of), hi = level.Max(of);
                if (hi - lo > 0.5f) foreach (var r in mine) r.Fails.Add($"{what} not level across the row ({hi - lo:0} px)");
            }
            Level(x => x.Medal, "medallions");
            Level(x => x.Title, "titles");
            Level(x => x.FootBottom, "footer baselines");
        }
    }

    void Finish()
    {
        foreach (var r in rows) foreach (var f in r.Fails) fails.Add($"{r.Calling} {r.State} {r.Pass} {r.Kind} {r.Id} \"{r.Title}\" (font {r.Font}): {f}");
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath))!);
        var report = new
        {
            cards = rows.Count,
            stripsChecked = stripCards,
            failed = rows.Count(r => r.Fails.Count > 0),
            worstOverlap = rows.Count > 0 ? rows.Max(r => r.Overlap) : 0,
            leastSlack = rows.Count > 0 ? rows.Min(r => r.Slack) : 0,
            atFloor = rows.Count(r => r.Font <= DraftPanel.BodyFloor),
            fonts = rows.GroupBy(r => r.Font).OrderByDescending(g => g.Key).ToDictionary(g => g.Key.ToString(), g => g.Count()),
            failures = fails,
            rows = rows.Select(r => new { r.Calling, r.State, r.Pass, r.Kind, r.Id, r.Title, r.Text, r.Font, r.Lines, r.Visible, Slack = MathF.Round(r.Slack, 1), Overlap = MathF.Round(r.Overlap, 1), Short = MathF.Round(r.Short, 1), BodyH = MathF.Round(r.BodyH, 1), FootH = MathF.Round(r.FootH, 1), Above = MathF.Round(r.Above, 1), r.Fails }),
        };
        File.WriteAllText(outPath, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
        GD.Print($"card_fit: {rows.Count} cards, {report.failed} failed, worst overlap {report.worstOverlap:0.0} px, least slack {report.leastSlack:0.0} px, {report.atFloor} at the floor font -> {outPath}");
        foreach (var f in fails.Take(60)) GD.Print("  FAIL " + f);
        if (fails.Count > 60) GD.Print($"  ... {fails.Count - 60} more in the report");
        if (sheet)
        {
            // The rows of the six least-slack cards, each shot as the game shows it.
            var worst = rows.OrderBy(r => r.Slack).DistinctBy(r => (r.Kind, r.Id)).Take(6).ToList();
            // (the card lifted: the first in the row with a recipe, so the strip shows one, else the least-slack card)
            shots = worst.Select(r => (r.Job, Card: jobs[r.Job].Offers.FindIndex(o => o.Recipe is { Length: > 0 }) is int k and >= 0 ? k : r.Card)).DistinctBy(x => x.Job).ToList();
            foreach (var r in worst) GD.Print($"  sheet: {r.Calling} {r.State} {r.Pass} {r.Kind} {r.Id} \"{r.Title}\" slack {r.Slack:0.0} font {r.Font}");
            shot = 0;
            clock = -1;
            return;
        }
        GetTree().Quit(fails.Count > 0 ? 1 : 0);
    }

    void Shoot(double delta)
    {
        if (shot >= shots.Count) { GetTree().Quit(fails.Count > 0 ? 1 : 0); return; }
        if (clock < 0)
        {
            foreach (var c in vp.GetChildren()) c.QueueFree();
            vp.RenderTargetUpdateMode = SubViewport.UpdateMode.Always;
            shotPanel = Lay(vp, jobs[shots[shot].Job]);
            shotPanel.FocusCard(shots[shot].Card);
            clock = 0;
            return;
        }
        clock += delta;
        // (the cards rise in over half a second, the last a quarter second late)
        if (clock < 1.4) return;
        var dir = ProjectSettings.GlobalizePath("res://.shots");
        Directory.CreateDirectory(dir);
        var file = Path.Combine(dir, $"card_fit_{shot + 1}.png");
        vp.GetTexture().GetImage().SavePng(file);
        var j = jobs[shots[shot].Job];
        GD.Print($"card_fit: shot {file} ({j.Calling} {j.State} {j.Pass}: {string.Join(", ", j.Offers.Select(o => o.Title))})");
        shot++;
        clock = -1;
    }
}
