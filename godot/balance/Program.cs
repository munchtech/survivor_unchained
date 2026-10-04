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
 *
 * Options: --callings warden,reaver|all  --policies greedy,random,path:steel|paths
 *          --seeds N  --seed0 S  --tier T (or --tiers 1,2,3)  --people pack,dead|all
 *          --oaths none|all|a,b+c  --level N|tier  --bot plain|deft  --cap MIN
 *          --beyond MIN  --weapons all  --levels 20,40  --par N  --out PATH  --csv DIR
 *          --bossread 0 (the hands as they were before they read the bosses)
 *
 * This is the one balance tool: the balance lab's sweep (godot/tests/BalanceLab.cs,
 * BALANCE_LAB=arena) runs these same arenas through these same hands. */

var opt = Opts.Parse(args);
Pilot.ReadsBosses = opt.Get("bossread", "1") != "0";
string cmd = args.Length > 0 && !args[0].StartsWith("--") ? args[0] : "help";
// The content is read once, before the runs share it.
_ = Callings.Archetypes; _ = Items.All; _ = Weapons.All; _ = Boons.All;

switch (cmd)
{
    case "arena": Arena(); break;
    case "probe": ProbeAll(); break;
    case "weapons": WeaponsAll(); break;
    case "report": Console.WriteLine(Report.Arena(Load(opt.Get("in", "balance.jsonl")))); break;
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
                                Level: level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), Deft: deft));
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
