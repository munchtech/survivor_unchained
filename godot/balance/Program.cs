using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;

/* The balance harness's command line.
 *
 *   arena   whole arenas, played by the Pilot, drafted by a policy
 *   probe   builds drafted to an ember level and put through the standard test
 *   report  a summary of runs saved before (arena's .jsonl)
 *   map     the Wayfinder's maps, played by the Pilot's hands with a day build
 *           (--tiers 1,2,3 --people all --seeds N --level L|tier --gear R --mods a+b --cap MIN)
 *   story   the story's nights, stage by stage and their bosses (docs/design/STORY_BOSSES.md 0.6)
 *           (--fight hollow|all --tiers 1,2,3,4 --seeds N --policies greedy,random --bot plain,deft
 *           --act2 --choice spare|finish --level N|tier --out PATH)
 *
 * Options: --callings warden,reaver|all  --policies greedy,random,path:steel|paths
 *          --seeds N  --seed0 S  --tier T (or --tiers 1,2,3)  --people pack,dead|all
 *          --oaths none|all|a,b+c  --level N|tier  --bot plain|deft  --cap MIN
 *          --beyond MIN  --weapons all  --levels 20,40  --par N  --out PATH  --csv DIR
 *          --bossread 0 (the hands as they were before they read the bosses)
 *          --charges 0 (every charger on its own clock, as before the charge director)
 *          --minutes 20 (a story's night: twenty minutes, ending on its boss)
 *
 * This is the one balance tool: the balance lab's sweep (godot/tests/BalanceLab.cs,
 * BALANCE_LAB=arena) runs these same arenas through these same hands. */

var opt = Opts.Parse(args);
Pilot.ReadsBosses = opt.Get("bossread", "1") != "0";
ArenaSim.Director = opt.Get("charges", "1") != "0";
string cmd = args.Length > 0 && !args[0].StartsWith("--") ? args[0] : "help";
// The content is read once, before the runs share it.
_ = Callings.Archetypes; _ = Items.All; _ = Weapons.All; _ = Boons.All;

switch (cmd)
{
    case "arena": Arena(); break;
    case "probe": ProbeAll(); break;
    case "weapons": WeaponsAll(); break;
    case "report": Console.WriteLine(Report.Arena(Load(opt.Get("in", "balance.jsonl")))); break;
    case "map": Maps(); break;
    case "story": Story(); break;
    case "place": Place(); break;
    case "landmarks": Landmarks(); break;
    default:
        Console.WriteLine("dotnet run -c Release --project godot/balance -- arena|probe|report [options]  (see Program.cs)");
        break;
}

List<RunResult> Load(string path) =>
    File.ReadAllLines(path).Where(l => l.Length > 0).Select(l => JsonSerializer.Deserialize<RunResult>(l, Opts.Json)!).ToList();

string[] Callers() => opt.List("callings", "all") is ["all"] ? ["warden", "reaver", "arcanist", "stalker"] : opt.List("callings", "all");

string[] Policies() =>
    opt.List("policies", "greedy").SelectMany(p => p == "paths" ? Paths.All.Select(x => $"path:{x.Id}") : [p]).ToArray();

void Arena()
{
    var peoples = opt.List("people", "all") is ["all"] ? MapOffers.Peoples.Select(p => p.Id).ToArray() : opt.List("people", "all");
    int seeds = opt.Int("seeds", 4), seed0 = opt.Int("seed0", 1);
    var tiers = opt.Has("tiers") ? opt.List("tiers", "1").Select(int.Parse).ToArray() : [opt.Int("tier", 1)];
    // --oaths none|all|table|a,b+c: unsworn, each oath alone, as the Wayfinder's table swears
    // them (none or one at tier 1, two at tiers 2 and 3, three from 4), or the ones named ('+' swears two at once).
    var oaths = opt.Get("oaths", "none") == "table" ? ["table"] : opt.List("oaths", "none") is ["all"] ? new[] { "none" }.Concat(MapOffers.Oaths.Select(o => o.Id)).ToArray() : opt.List("oaths", "none");
    string[]? Sworn(string oath, int tier, int seed)
    {
        if (oath == "none") return null;
        if (oath != "table") return oath.Split('+');
        var rng = new SurvivorUnchained.Core.Rng((uint)(seed * 104729 + tier * 7919 + 3));
        int n = tier <= 1 ? (seed % 3 == 0 ? 0 : 1) : Math.Min(3, 1 + tier / 2);
        return n == 0 ? null : rng.Shuffle(MapOffers.Oaths.Select(o => o.Id).ToList()).Take(n).ToArray();
    }
    // --level N|tier: the survivor's character level (tier: 1, 4, 7 by tier, as the story's pace has it).
    string level = opt.Get("level", "1");
    bool deft = opt.Get("bot", "plain") == "deft";
    bool allWeapons = opt.Get("weapons", "") == "all";
    var specs = new List<RunSpec>();
    foreach (var c in Callers())
        foreach (var pol in Policies())
            foreach (int tier in tiers)
                foreach (var oath in oaths)
                    for (int s = 0; s < seeds; s++)
                    {
                        int nw = allWeapons ? Callings.Archetype(c).Weapons.Count : 1;
                        for (int w = 0; w < nw; w++)
                            specs.Add(new RunSpec(seed0 + s, c, pol, tier, peoples[(s + w) % peoples.Length], Sworn(oath, tier, seed0 + s),
                                opt.Double("cap", 40), opt.Double("beyond", 0), allWeapons ? w : s % Callings.Archetype(c).Weapons.Count,
                                Level: level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), Deft: deft, Minutes: opt.Double("minutes", 30)));
                    }
    string outPath = opt.Get("out", "balance.jsonl");
    Console.WriteLine($"{specs.Count} arenas, {opt.Int("par", 16)} at a time -> {outPath}");
    var results = new ConcurrentBag<RunResult>();
    var sw = Stopwatch.StartNew();
    int done = 0;
    using var file = new StreamWriter(outPath, append: opt.Has("append"));
    var gate = new object();
    Parallel.ForEach(specs, new ParallelOptions { MaxDegreeOfParallelism = opt.Int("par", 16) }, spec =>
    {
        RunResult r;
        try { r = ArenaSim.Play(spec); }
        catch (Exception e) { Console.Error.WriteLine($"{spec.Key}: {e}"); return; }
        results.Add(r);
        lock (gate)
        {
            file.WriteLine(JsonSerializer.Serialize(r, Opts.Json));
            file.Flush();
            done++;
            Console.WriteLine($"[{done}/{specs.Count} {sw.Elapsed:mm\\:ss}] {spec.Key}: {(r.Won ? $"won {r.WonAt:0.0}" : r.Died ? $"fell {r.Minutes:0.0}" : $"standing {r.Minutes:0.0}")} ember {r.Ember}  {r.Build}");
        }
    });
    var md = Report.Arena(results.OrderBy(r => r.Spec.Key).ToList());
    File.WriteAllText(Path.ChangeExtension(outPath, ".md"), md);
    if (opt.Has("csv")) Report.Csv(results.OrderBy(r => r.Spec.Key).ToList(), opt.Get("csv", "out/csv"));
    Console.WriteLine(md);
}

/* A story fight's place drawn in text, a metre a character (north up): its spaces (a letter each),
 * its walls (#), its shut gates (=) and its named points (digits, with a legend). For checking an
 * outline before arena art builds to it. */
/// <summary>Where an arena's landmarks lie, for pointing the camera at them (arena art's
/// shots, `--at X,Z`): `landmarks --people pack --seed 311`. Its streams' and rails' points
/// nearest the middle, and the first of each of its own pieces.</summary>
void Landmarks()
{
    var m = MapGen.Generate(new MapSpec { Seed = opt.Int("seed", 311), Arena = true, People = opt.Get("people", "pack") });
    foreach (var (name, lines) in new[] { ("stream", m.Streams), ("rails", m.Rails) })
        foreach (var l in lines)
        {
            var p = l.Where(q => Math.Abs(q.X) < 60 && Math.Abs(q.Z) < 60).OrderBy(q => q.X * q.X + q.Z * q.Z).FirstOrDefault();
            Console.WriteLine($"{name} nearest the middle ({p.X:0}, {p.Z:0})");
        }
    foreach (var v in m.Vents) Console.WriteLine($"vent ({v.X:0}, {v.Z:0}) r {v.R:0.0}");
    // (And anything there are only a few of: a place's landmarks, the howe's door, its standard.)
    foreach (var g in m.Pieces.GroupBy(p => p.Id).Where(g => g.Key.StartsWith("arena/") || g.Count() <= 3))
        Console.WriteLine($"{g.Key} x{g.Count()}: " + string.Join(" ", g.Take(4).Select(p => $"({p.X:0}, {p.Z:0})")));
}

void Place()
{
    var ids = new Dictionary<string, string> { ["hollow"] = "hollow_by_night", ["roost"] = "roost_raid", ["dig"] = "dig_boils", ["vault"] = "vault_opened" };
    var fight = SurvivorUnchained.Play.Story.StoryScripts.For(ids[opt.Get("fight", "hollow")]) ?? throw new ArgumentException("no such fight");
    var pl = fight.Place;
    var (x0, z0, x1, z1) = pl.Bounds(3);
    var c = new SurvivorUnchained.Sim.CollisionWorld(400);
    pl.Build(c);
    var pts = pl.Points.ToList();
    const string marks = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    for (double z = Math.Ceiling(z1); z >= Math.Floor(z0); z -= 1)
    {
        var row = new System.Text.StringBuilder();
        for (double x = Math.Floor(x0); x <= Math.Ceiling(x1); x += 1)
        {
            int pi = pts.FindIndex(p => Math.Abs(p.Value.X - x) < 0.5 && Math.Abs(p.Value.Z - z) < 0.5);
            if (pi >= 0) { row.Append(marks[pi % marks.Length]); continue; }
            string? space = pl.SpaceAt(x, z);
            bool gate = c.Within(x, z, 0.5).Any(k => k.Tag?.StartsWith("gate:") == true);
            row.Append(gate ? '=' : space != null ? char.ToLower(space[0]) == 'f' ? ',' : '.' : c.Blocked(x, z, 0.3) ? '#' : ' ');
        }
        Console.WriteLine($"{z,5} {row}");
    }
    for (int i = 0; i < pts.Count; i++) Console.WriteLine($"  {marks[i % marks.Length]} {pts[i].Key} ({pts[i].Value.X}, {pts[i].Value.Z})");
}

/* The story's nights: each fight with its stages and boss, by each pair of hands and draft. */
void Story()
{
    // (Only the fights whose nights are written; the rest still run as a table's night.)
    var written = new Dictionary<string, string> { ["hollow"] = "hollow_by_night", ["roost"] = "roost_raid", ["dig"] = "dig_boils", ["vault"] = "vault_opened" };
    var fights = (opt.List("fight", "all") is ["all"] ? written.Keys.ToArray() : opt.List("fight", "hollow")).Where(f => SurvivorUnchained.Play.Story.StoryScripts.Has(written[f])).ToArray();
    int seeds = opt.Int("seeds", 4), seed0 = opt.Int("seed0", 1);
    var tiers = opt.List("tiers", "1").Select(int.Parse).ToArray();
    var hands = opt.List("bot", "plain");
    string level = opt.Get("level", "tier");
    var specs = new List<StoryRunSpec>();
    foreach (var f in fights)
        foreach (var c in Callers())
            foreach (var pol in opt.List("policies", "greedy,random"))
                foreach (int tier in tiers)
                    foreach (var h in hands)
                        for (int s = 0; s < seeds; s++)
                            specs.Add(new StoryRunSpec(seed0 + s, c, pol, f, tier, level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), h == "deft",
                                opt.Has("act2"), opt.Get("choice", "spare"), opt.Double("cap", 25), opt.Has("crates"), h == "naive", opt.Has("learned")));
    Console.WriteLine($"{specs.Count} story nights, {opt.Int("par", 16)} at a time");
    var results = new ConcurrentBag<StoryRunResult>();
    var sw = Stopwatch.StartNew();
    int done = 0;
    var gate = new object();
    using var file = opt.Has("out") ? new StreamWriter(opt.Get("out", "story.jsonl")) : null;
    Parallel.ForEach(specs, new ParallelOptions { MaxDegreeOfParallelism = opt.Int("par", 16) }, spec =>
    {
        StoryRunResult r;
        try { r = StorySim.Play(spec); }
        catch (Exception e) { Console.Error.WriteLine($"{spec.Key}: {e}"); return; }
        results.Add(r);
        lock (gate)
        {
            done++;
            file?.WriteLine(JsonSerializer.Serialize(r, Opts.Json));
            Console.WriteLine($"[{done}/{specs.Count} {sw.Elapsed:mm\\:ss}] {spec.Key}: {(r.Won ? $"won {r.Minutes:0.0}" : $"lost {r.Minutes:0.0} ({r.KilledBy}) [{r.Where}]")} falls {r.Falls} way in {r.WayIn:0.0} boss {(r.BossSeconds is double bs ? $"{bs:0}s" : $"phase {r.BossPhase}")} low {r.LowWayIn:0.00}  {r.Build}");
        }
    });
    var md = StorySim.Report(results.OrderBy(r => r.Spec.Key).ToList());
    if (opt.Has("out")) File.WriteAllText(Path.ChangeExtension(opt.Get("out", "story.jsonl"), ".md"), md);
    Console.WriteLine(md);
}

/* The Wayfinder's maps: each calling with its own path's day skills at the level's rank and plain
 * gear at a rarity, walking the way to the ruler. --level tier puts the survivor at the map's
 * creature level (8 + 2 x tier), capped at the character's 30. */
void Maps()
{
    var peoples = opt.List("people", "all") is ["all"] ? MapOffers.Peoples.Select(p => p.Id).ToArray() : opt.List("people", "all");
    int seeds = opt.Int("seeds", 2), seed0 = opt.Int("seed0", 1);
    var tiers = opt.List("tiers", "1").Select(int.Parse).ToArray();
    var mods = opt.Get("mods", "") is { Length: > 0 } m ? m.Split('+') : Array.Empty<string>();
    var specs = new List<MapRunSpec>();
    foreach (var c in Callers())
        foreach (int tier in tiers)
            foreach (var people in peoples)
                for (int s = 0; s < seeds; s++)
                {
                    int level = opt.Get("level", "tier") == "tier" ? Math.Min(30, 8 + 2 * tier) : opt.Int("level", 10);
                    specs.Add(new MapRunSpec(seed0 + s, c, tier, people, level, opt.Int("gear", 2), mods, opt.Get("bot", "deft") == "deft", opt.Double("cap", 25)));
                }
    Console.WriteLine($"{specs.Count} maps, {opt.Int("par", 16)} at a time");
    var results = new ConcurrentBag<MapRunResult>();
    var sw = Stopwatch.StartNew();
    int done = 0;
    var gate = new object();
    Parallel.ForEach(specs, new ParallelOptions { MaxDegreeOfParallelism = opt.Int("par", 16) }, spec =>
    {
        MapRunResult r;
        try { r = MapSim.Play(spec); }
        catch (Exception e) { Console.Error.WriteLine($"{spec.Key}: {e}"); return; }
        results.Add(r);
        lock (gate)
        {
            done++;
            Console.WriteLine($"[{done}/{specs.Count} {sw.Elapsed:mm\\:ss}] {spec.Key}: {(r.Cleared ? $"cleared {r.Minutes:0.0}" : r.Closed ? $"closed {r.Minutes:0.0} ({r.KilledBy})" : $"walking {r.Minutes:0.0}")} falls {r.Falls} packs {r.PacksCleared}/{r.Packs} boss {(r.BossTtk is double bt ? $"{bt:0}s" : $"phase {r.BossPhase} left {r.BossLeft:0.00}")} low {r.LowHp:0.00}  {r.Build}");
        }
    });
    var md = MapSim.Report(results.OrderBy(r => r.Spec.Key).ToList());
    if (opt.Has("out")) File.WriteAllText(opt.Get("out", "maps.md"), md);
    Console.WriteLine(md);
}

void ProbeAll()
{
    var levels = opt.List("levels", "20,40,55").Select(int.Parse).ToArray();
    int seeds = opt.Int("seeds", 8), seed0 = opt.Int("seed0", 1);
    var specs = new List<ProbeSpec>();
    foreach (var c in Callers())
        foreach (var pol in Policies())
            foreach (var l in levels)
                for (int s = 0; s < seeds; s++)
                    specs.Add(new ProbeSpec(seed0 + s, c, pol, l, s % Callings.Archetype(c).Weapons.Count, 0, opt.Get("people", "dead")));
    var results = new ConcurrentBag<ProbeResult>();
    var sw = Stopwatch.StartNew();
    Parallel.ForEach(specs, new ParallelOptions { MaxDegreeOfParallelism = opt.Int("par", 16) }, spec =>
    {
        try { results.Add(Probe.Run(spec)); }
        catch (Exception e) { Console.Error.WriteLine($"{spec.Key}: {e}"); }
    });
    Console.Error.WriteLine($"{specs.Count} probes in {sw.Elapsed:mm\\:ss}");
    if (opt.Has("builds"))
        foreach (var r in results.OrderBy(r => r.Spec.Key))
            Console.WriteLine($"{r.Spec.Key}: power {r.Power:0} crowd {r.CrowdDps:0} champion {r.BossDps:0} ehp {r.Ehp:0}  {r.Build}\n    " +
                string.Join(", ", r.DamageBy.OrderByDescending(x => x.Value).Take(6).Select(x => $"{x.Key} {x.Value:0}")));
    var md = Report.Probes(results.ToList());
    if (opt.Has("out")) File.WriteAllText(opt.Get("out", "probe.md"), md);
    Console.WriteLine(md);
}

/* Every combat skill alone at the stages a run passes through: rank 1 at
 * the second minute, rank 4 at the eighth, rank 8 at the fifteenth, each
 * evolution at the twenty-second; each as the median of a few seeds, and
 * against the median of all skills at that stage. */
void WeaponsAll()
{
    var stages = new (string Name, int Rank, bool Evolved, int Foe)[] { ("r1", 1, false, 1), ("r4", 4, false, 4), ("r8", 8, false, 7), ("evo", 8, true, 9) };
    int seeds = opt.Int("seeds", 3);
    var only = opt.Has("only") ? opt.List("only", "").ToHashSet() : null;
    var jobs = new List<(string Weapon, string? Evo, string Stage, int Rank, int Foe, int Seed)>();
    foreach (var w in Weapons.All.Values.Where(w => w.Findable && (only == null || only.Contains(w.Id))))
        foreach (var st in stages)
            foreach (var evo in st.Evolved ? w.Evolutions.Select(e => (string?)e.Id) : [null])
                for (int s = 0; s < seeds; s++) jobs.Add((w.Id, evo, st.Name, st.Rank, st.Foe, 1 + s));
    var results = new ConcurrentBag<(string Weapon, string? Evo, string Stage, ProbeResult R)>();
    Parallel.ForEach(jobs, new ParallelOptions { MaxDegreeOfParallelism = opt.Int("par", 16) }, job =>
    {
        try { results.Add((job.Weapon, job.Evo, job.Stage, SurvivorUnchained.Balance.Probe.Weapon(job.Weapon, job.Rank, job.Evo, job.Foe, job.Seed, opt.Get("people", "dead")))); }
        catch (Exception e) { Console.Error.WriteLine($"{job.Weapon} {job.Evo}: {e.Message}"); }
    });
    var sb = new StringBuilder();
    sb.AppendLine("## Every combat skill alone\n");
    sb.AppendLine("Index: 0.6 × crowd damage + 0.4 × champion damage, each against the median of all skills at that stage (1.00 is the median). In brackets: crowd / champion damage a second, and the damage the survivor took a second (the price of the range it fights at).\n");
    sb.AppendLine("| skill | r1 | r4 | r8 | evolutions |");
    sb.AppendLine("|---|---|---|---|---|");
    var per = results.GroupBy(r => (r.Weapon, r.Evo, r.Stage)).ToDictionary(g => g.Key, g => (Crowd: Report.Median(g.Select(x => x.R.CrowdDps)), Boss: Report.Median(g.Select(x => x.R.BossDps)), Hurt: Report.Median(g.Select(x => x.R.Intake))));
    var medC = per.GroupBy(x => x.Key.Stage).ToDictionary(g => g.Key, g => Report.Median(g.Select(x => x.Value.Crowd)));
    var medB = per.GroupBy(x => x.Key.Stage).ToDictionary(g => g.Key, g => Report.Median(g.Select(x => x.Value.Boss)));
    string Cell(string w, string? evo, string stage)
    {
        if (!per.TryGetValue((w, evo, stage), out var v)) return "–";
        double idx = 0.6 * v.Crowd / medC[stage] + 0.4 * v.Boss / Math.Max(1, medB[stage]);
        return $"{idx:0.00} ({v.Crowd:0}/{v.Boss:0}, {v.Hurt:0})";
    }
    foreach (var w in Weapons.All.Values.Where(w => w.Findable && (only == null || only.Contains(w.Id))).OrderBy(w => w.Id))
        sb.AppendLine($"| {w.Id} | {Cell(w.Id, null, "r1")} | {Cell(w.Id, null, "r4")} | {Cell(w.Id, null, "r8")} | " +
            string.Join("; ", w.Evolutions.Select(e => $"{e.Id} {Cell(w.Id, e.Id, "evo")}")) + " |");
    sb.AppendLine($"\nStage medians (crowd/champion): {string.Join(", ", medC.OrderBy(x => x.Key).Select(x => $"{x.Key} {x.Value:0}/{medB[x.Key]:0}"))}");
    // Unions, at the twenty-fifth minute's strength, against their two halves evolved (each alone).
    if (only == null)
    {
        var uj = new List<(string Id, string W, string? Evo, int Seed)>();
        foreach (var u in Unions.All)
            for (int s = 0; s < seeds; s++)
            {
                uj.Add((u.Id, u.Into, null, 1 + s));
                uj.Add((u.Id, u.A, Weapons.All[u.A].Evolutions[0].Id, 1 + s));
                uj.Add((u.Id, u.B, Weapons.All[u.B].Evolutions[0].Id, 1 + s));
            }
        var ur = new ConcurrentBag<(string Id, string W, ProbeResult R)>();
        Parallel.ForEach(uj, new ParallelOptions { MaxDegreeOfParallelism = opt.Int("par", 16) }, j =>
            ur.Add((j.Id, j.W, SurvivorUnchained.Balance.Probe.Weapon(j.W, Weapons.MaxRank, j.Evo, 11, j.Seed, opt.Get("people", "dead")))));
        sb.AppendLine("\n### Unions against their halves (crowd / champion damage a second; the union should be worth a little less than both, for the slot it frees)\n");
        sb.AppendLine("| union | union | halves together | ratio |");
        sb.AppendLine("|---|---|---|---|");
        foreach (var u in Unions.All)
        {
            double C(string w) => Report.Median(ur.Where(x => x.Id == u.Id && x.W == w).Select(x => x.R.CrowdDps));
            double B(string w) => Report.Median(ur.Where(x => x.Id == u.Id && x.W == w).Select(x => x.R.BossDps));
            double ratio = 0.6 * C(u.Into) / Math.Max(1, C(u.A) + C(u.B)) + 0.4 * B(u.Into) / Math.Max(1, B(u.A) + B(u.B));
            sb.AppendLine($"| {u.Id} | {C(u.Into):0}/{B(u.Into):0} | {C(u.A) + C(u.B):0}/{B(u.A) + B(u.B):0} | {ratio:0.00} |");
        }
    }
    if (opt.Has("out")) File.WriteAllText(opt.Get("out", "weapons.md"), sb.ToString());
    if (opt.Has("json"))
        File.WriteAllText(opt.Get("json", "weapons.json"), JsonSerializer.Serialize(per.Select(kv => new
        {
            weapon = kv.Key.Weapon, evo = kv.Key.Evo, stage = kv.Key.Stage, crowd = kv.Value.Crowd, boss = kv.Value.Boss, hurt = kv.Value.Hurt,
            index = 0.6 * kv.Value.Crowd / medC[kv.Key.Stage] + 0.4 * kv.Value.Boss / Math.Max(1, medB[kv.Key.Stage]),
        }).ToList(), Opts.Json));
    Console.WriteLine(sb.ToString());
}

sealed class Opts
{
    readonly Dictionary<string, string> v = new();
    public static readonly JsonSerializerOptions Json = new() { IncludeFields = true, NumberHandling = System.Text.Json.Serialization.JsonNumberHandling.AllowNamedFloatingPointLiterals };

    public static Opts Parse(string[] args)
    {
        var o = new Opts();
        for (int i = 0; i < args.Length; i++)
            if (args[i].StartsWith("--"))
                o.v[args[i][2..]] = i + 1 < args.Length && !args[i + 1].StartsWith("--") ? args[++i] : "true";
        return o;
    }

    public bool Has(string k) => v.ContainsKey(k);
    public string Get(string k, string d) => v.TryGetValue(k, out var s) ? s : d;
    public int Int(string k, int d) => v.TryGetValue(k, out var s) ? int.Parse(s) : d;
    public double Double(string k, double d) => v.TryGetValue(k, out var s) ? double.Parse(s, System.Globalization.CultureInfo.InvariantCulture) : d;
    public string[] List(string k, string d) => Get(k, d).Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
}
