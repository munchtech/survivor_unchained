W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""    public static Journey Character(string calling, int level, int gearRarity, int seed)""",
         """    public static Journey Survivor(string calling, int level, int gearRarity, int seed)"""),
        ("""        var j = Character(spec.Calling, spec.Level, spec.GearRarity, spec.Seed);""",
         """        var j = Survivor(spec.Calling, spec.Level, spec.GearRarity, spec.Seed);"""),
    ],
    W + "balance/Program.cs": [
        (""" *   report  a summary of runs saved before (arena's .jsonl)
""", """ *   report  a summary of runs saved before (arena's .jsonl)
 *   map     the Wayfinder's maps, played by the Pilot's hands with a day build
 *           (--tiers 1,2,3 --people all --seeds N --level L|tier --gear R --mods a+b --cap MIN)
"""),
        ("""    case "report": Console.WriteLine(Report.Arena(Load(opt.Get("in", "balance.jsonl")))); break;""",
         """    case "report": Console.WriteLine(Report.Arena(Load(opt.Get("in", "balance.jsonl")))); break;
    case "map": Maps(); break;"""),
        ("""void ProbeAll()
{""", """/* The Wayfinder's maps: each calling with its own path's day skills at the level's rank and plain
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
            Console.WriteLine($"[{done}/{specs.Count} {sw.Elapsed:mm\\\\:ss}] {spec.Key}: {(r.Cleared ? $"cleared {r.Minutes:0.0}" : r.Closed ? $"closed {r.Minutes:0.0} ({r.KilledBy})" : $"walking {r.Minutes:0.0}")} falls {r.Falls} packs {r.PacksCleared}/{r.Packs} boss {(r.BossTtk is double bt ? $"{bt:0}s" : $"phase {r.BossPhase}")} low {r.LowHp:0.00}  {r.Build}");
        }
    });
    var md = MapSim.Report(results.OrderBy(r => r.Spec.Key).ToList());
    if (opt.Has("out")) File.WriteAllText(opt.Get("out", "maps.md"), md);
    Console.WriteLine(md);
}

void ProbeAll()
{"""),
    ],
}
