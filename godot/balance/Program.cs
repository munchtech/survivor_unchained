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
 *          --seeds N  --seed0 S  --tier T  --people pack,dead|all  --cap MIN
 *          --beyond MIN  --weapons all  --levels 20,40  --par N  --out PATH */

var opt = Opts.Parse(args);
string cmd = args.Length > 0 && !args[0].StartsWith("--") ? args[0] : "help";
// The content is read once, before the runs share it.
_ = Callings.Archetypes; _ = Items.All; _ = Weapons.All; _ = Boons.All;

switch (cmd)
{
    case "arena": Arena(); break;
    case "probe": ProbeAll(); break;
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
    int seeds = opt.Int("seeds", 4), seed0 = opt.Int("seed0", 1), tier = opt.Int("tier", 1);
    bool allWeapons = opt.Get("weapons", "") == "all";
    var specs = new List<RunSpec>();
    foreach (var c in Callers())
        foreach (var pol in Policies())
            for (int s = 0; s < seeds; s++)
            {
                int nw = allWeapons ? Callings.Archetype(c).Weapons.Count : 1;
                for (int w = 0; w < nw; w++)
                    specs.Add(new RunSpec(seed0 + s, c, pol, tier, peoples[(s + w) % peoples.Length], null, opt.Double("cap", 40), opt.Double("beyond", 0), allWeapons ? w : s % Callings.Archetype(c).Weapons.Count));
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
    var md = Report.Arena(results.ToList());
    File.WriteAllText(Path.ChangeExtension(outPath, ".md"), md);
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
