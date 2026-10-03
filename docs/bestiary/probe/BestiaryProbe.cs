using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using WeaponDefs = SurvivorUnchained.Content.Weapons;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

// Bestiary probe (docs/bestiary/probe/README.md): one kind of creature, or one
// mix, kept at a steady number round the survivor on an arena's ground, against
// one loadout, for a fixed time. The survivor cannot die (their health is made
// enormous) so every run lasts as long as every other and damage taken is a
// rate; what killing takes is measured from the first blow on a creature to its
// death. The movement is the balance lab's arena bot (origin/claude/cloud-balance-lab,
// godot/tests/ArenaPlay.cs), plain or deft, copied here so the probe stands alone.
static class Probe
{
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    static string F(double v, string f = "0.0") => double.IsNaN(v) ? "" : v.ToString(f, Inv);

    /// <summary>A group: who is kept alive, how many of each, and as champions or not.</summary>
    sealed record Group(string Id, string People, (string Def, int Count)[] Kinds, bool Elite = false);

    /// <summary>A loadout: the weapons at a rank, extra stat mods (gear), boons, and the art (none: the bot never uses one).</summary>
    sealed record Setup(string Id, (string Weapon, int Rank)[] Weapons, StatMod[]? Mods = null, string[]? Boons = null, string? Art = null);

    sealed record Case(Group G, Setup S, bool Deft, int Seed, int Level, string[] Oaths, double Seconds);

    sealed record Result(Case C, int Kills, double KillsPerMin, double Ttk, double TtkElite, double Taken, double TakenPerMin, double HitsTakenPerMin,
        double BlockedShare, int Perfects, int Interrupts, string TopSource, double TopShare, int Raised, int Splits);

    static readonly Group[] Groups =
    {
        // Alone: the rank and file, a steady crowd.
        new("risen", "dead", [("risen", 14)]),
        new("risen_warrior", "dead", [("risen_warrior", 8)]),
        new("risen_archer", "dead", [("risen_archer", 8)]),
        new("grave_caller+risen", "dead", [("grave_caller", 2), ("risen", 10)]),
        new("wolf", "pack", [("wolf", 14)]),
        new("wolf_blighted", "pack", [("wolf_blighted", 8)]),
        new("boar", "pack", [("boar", 6)]),
        new("lampling", "lamplings", [("lampling", 14)]),
        new("lampling_sapper", "lamplings", [("lampling_sapper", 8)]),
        new("footpad", "kerchiefs", [("footpad", 14)]),
        new("pillager", "kerchiefs", [("pillager", 8)]),
        new("bruiser", "kerchiefs", [("bruiser", 8)]),
        // Elites, one at a time.
        new("barrow_knight", "dead", [("barrow_knight", 1)]),
        new("wolf_alpha", "pack", [("wolf_alpha", 1)]),
        new("enforcer", "kerchiefs", [("enforcer", 1)]),
        new("grimtunnel_roused", "lamplings", [("grimtunnel_roused", 1)]),
        // Champions of the rank and file (the arena's champion flag: three times the health, a level up).
        new("champion:bruiser", "kerchiefs", [("bruiser", 2)], Elite: true),
        new("champion:wolf", "pack", [("wolf", 3)], Elite: true),
        // Mixes: where two kinds together ask something neither asks alone.
        new("mix:shieldwall", "kerchiefs", [("bruiser", 4), ("pillager", 4)]),
        new("mix:raised_ranks", "dead", [("grave_caller", 2), ("risen", 8), ("risen_warrior", 3)]),
        new("mix:dig", "lamplings", [("lampling", 10), ("lampling_sapper", 4)]),
        new("mix:hunt", "pack", [("wolf", 10), ("boar", 3)]),
        new("mix:ford", "dead", [("risen_warrior", 4), ("risen_archer", 4)]),
    };

    static StatMod M(string stat, ModKind k, double v) => new(stat, k, v, "probe");

    static readonly Setup[] Setups =
    {
        new("blade", [("oathblade", 4)]),
        new("cleaver", [("cleaver", 4)]),
        new("volley", [("volley", 4)]),
        new("knives", [("knifestorm", 4)]),
        new("motes", [("seeking_motes", 4)]),
        new("rime", [("rimeshard", 4)]),
        new("cinder", [("cinderfall", 4)]),
        new("arcweb", [("arcweb", 4)]),
        new("dawn", [("dawnpulse", 4)]),
        new("hallowed", [("hallowed_ring", 4)]),
        new("gyre", [("axe_gyre", 4)]),
        new("blight", [("blightfield", 4)]),
        new("lance", [("verdant_lance", 4)]),
        new("herd", [("spirit_herd", 4)]),
        // Gear on the volley: a slayer of grade III against every family (the people's own slayer), and a defensive kit.
        new("volley+slayer", [("volley", 4)], [M(Stat.VsOf(Family.Undead), ModKind.Flat, 0.32), M(Stat.VsOf(Family.Wolf), ModKind.Flat, 0.32),
            M(Stat.VsOf(Family.Boar), ModKind.Flat, 0.32), M(Stat.VsOf(Family.Lampling), ModKind.Flat, 0.32), M(Stat.VsOf(Family.Kerchief), ModKind.Flat, 0.32)]),
        new("volley+armour", [("volley", 4)], [M(Stat.Armor, ModKind.Flat, 10), M(Stat.ResistOf(School.Fire), ModKind.Flat, 0.15)]),
        // Two weapons, a generalist's pair: a crowd-clearer and a single-target one.
        new("pair:dawn+volley", [("dawnpulse", 4), ("volley", 4)]),
        // The arts, on the volley: each used by the bot's simple rule (a crowd near, or a champion or caster in reach).
        new("art:shield_bash", [("volley", 4)], Art: "shield_bash"),
        new("art:time_slip", [("volley", 4)], Art: "time_slip"),
        new("art:mark_prey", [("volley", 4)], Art: "mark_prey"),
        new("art:warcry", [("volley", 4)], Art: "warcry"),
        new("art:bulwark", [("volley", 4)], Art: "bulwark"),
        new("art:blink", [("volley", 4)], Art: "blink"),
        new("art:grapple", [("volley", 4)], Art: "grapple"),
        new("art:wraith_walk", [("volley", 4)], Art: "wraith_walk"),
        new("art:mirror_step", [("volley", 4)], Art: "mirror_step"),
    };

    static void Main(string[] args)
    {
        string dir = args.Length > 0 ? args[0] : Path.Combine(".lab", "bestiary");
        int seeds = args.Length > 1 ? int.Parse(args[1]) : 3;
        double seconds = args.Length > 2 ? double.Parse(args[2], Inv) : 150;
        Directory.CreateDirectory(dir);
        var cases = new List<Case>();
        foreach (var g in Groups)
            foreach (var s in Setups)
            {
                // The arts are measured only against the mixes and the elites, where an art has something to answer.
                if (s.Art != null && !(g.Id.StartsWith("mix:") || g.Kinds.Any(k => Enemies.Get(k.Def).Elite) || g.Id == "grave_caller+risen")) continue;
                foreach (bool deft in new[] { false, true })
                    for (int k = 0; k < seeds; k++) cases.Add(new Case(g, s, deft, 1000 + k * 7919, 5, [], seconds));
            }
        // The oaths, on two loadouts and three groups.
        foreach (var oath in new[] { "iron", "ruin", "embers", "winter", "hunt", "blight", "swarm" })
            foreach (var gid in new[] { "wolf", "risen", "mix:shieldwall" })
                foreach (var sid in new[] { "blade", "volley", "dawn" })
                    foreach (bool deft in new[] { false, true })
                        for (int k = 0; k < seeds; k++)
                            cases.Add(new Case(Groups.First(g => g.Id == gid), Setups.First(s => s.Id == sid), deft, 1000 + k * 7919, 5, [oath], seconds));
        // Read everything in once before the threads share it.
        Play(cases[0] with { Seconds = 2 });
        var bag = new ConcurrentBag<(int, Result)>();
        int done = 0;
        var clock = System.Diagnostics.Stopwatch.StartNew();
        Parallel.ForEach(Enumerable.Range(0, cases.Count), i =>
        {
            bag.Add((i, Play(cases[i])));
            int n = System.Threading.Interlocked.Increment(ref done);
            if (n % 100 == 0) Console.Error.WriteLine($"{n}/{cases.Count} after {clock.Elapsed.TotalMinutes:0.0} min");
        });
        var rows = bag.OrderBy(b => b.Item1).Select(b => b.Item2).ToList();
        WriteCsv(Path.Combine(dir, "runs.csv"), rows);
        var sum = Summary(rows);
        File.WriteAllText(Path.Combine(dir, "summary.md"), sum);
        Console.WriteLine(sum);
    }

    static Result Play(Case c)
    {
        // Every loadout on the same body (a warden's: 170 health, 5 armour), so the
        // weapon is what differs; character level 4, points in Might.
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Probe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)c.Seed);
        while (j.Ch.Level < 4) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        j.Ch.Attributes.Might += j.Ch.Points;
        j.Ch.Points = 0;
        var spec = new ArenaSpec { Id = "table:probe", Name = "Probe", Seed = c.Seed, Tier = 2, People = c.G.People, Oaths = c.Oaths.ToList() };
        var map = MapGen.Generate(spec.Map);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, 0, 0, 0, (uint)c.Seed, arena: true);
        b.EmberOn = false;
        b.Rules = MapOffers.Rules(spec.Map);
        b.InBounds = map.CanStand;
        foreach (var w in b.Weapons.Select(w => w.Id).ToList()) b.RemoveWeapon(w);
        foreach (var (w, r) in c.S.Weapons) b.AddWeapon(w, r);
        foreach (var boon in c.S.Boons ?? []) b.AddBoon(boon);
        if (c.S.Mods != null) b.Stats.AddAll(c.S.Mods);
        b.SetArt(c.S.Art != null ? Abilities.ById(c.S.Art).Kind : null, 1, []);
        // Cannot die: every run lasts the same time, and damage taken is a rate.
        double baseHp = b.MaxHp;
        b.Stats.Add(M(Stat.MaxHealth, ModKind.Flat, 1e7));
        var p = b.Player;
        p.Hp = b.MaxHp;
        var rng = new Random(c.Seed);
        double packSize = c.Oaths.Select(MapOffers.Oath).Aggregate(1.0, (x, o) => x * o.PackSize);

        var spawnedAt = new Dictionary<int, double>();
        var firstHit = new Dictionary<int, double>();
        var isElite = new Dictionary<int, bool>();
        var kindOf = new Dictionary<int, string>();
        var ttk = new List<double>();
        var ttkElite = new List<double>();
        var bySource = new Dictionary<string, double>();
        int kills = 0, hitsTaken = 0, hitsOn = 0, blocked = 0, perfects = 0, interrupts = 0, raised = 0, splits = 0;
        double taken = 0;
        const double dt = 1 / 60.0;
        double t = 0, keepT = 0;
        // Where the bot holds: a blade or a gyre must stand close to cut; everything else keeps a few steps off.
        double reach = c.S.Weapons.All(w => WeaponDefs.All[w.Weapon].Tags.Contains(Tag.Melee)) ? 2.2 : 6;

        void Keep()
        {
            // Top each kind up to its number (the oath of the swarm swells it), arriving from out of sight.
            var alive = new Dictionary<string, int>();
            foreach (var e in b.Enemies.Living())
                if (e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying)
                    alive[e.Def.Id] = alive.GetValueOrDefault(e.Def.Id) + 1;
            foreach (var (def, count) in c.G.Kinds)
            {
                int want = (int)Math.Round(count * (Enemies.Get(def).Elite || c.G.Elite ? 1 : packSize));
                // The raised dead are the caller's, not the director's: count risen raised as risen.
                for (int i = alive.GetValueOrDefault(def); i < want; i++)
                {
                    for (int tries = 0; tries < 12; tries++)
                    {
                        double ang = rng.NextDouble() * Math.PI * 2, d = 15 + rng.NextDouble() * 4;
                        double x = p.X + Math.Cos(ang) * d, z = p.Z + Math.Sin(ang) * d;
                        if (!map.CanStand(x, z) || b.Collision.Blocked(x, z, 0.7)) continue;
                        var dd = Enemies.Get(def);
                        var style = dd.Family == Family.Undead ? SpawnStyle.Rise : dd.Behavior == Behavior.Tunneler ? SpawnStyle.Burrow : SpawnStyle.Walk;
                        var e = b.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = c.Level + (c.G.Elite ? 1 : 0), Elite = c.G.Elite, Style = style });
                        if (e != null) { spawnedAt[e.Id] = t; isElite[e.Id] = e.Elite; kindOf[e.Id] = def; firstHit.Remove(e.Id); }
                        break;
                    }
                }
            }
        }

        while (t < c.Seconds)
        {
            if ((keepT -= dt) <= 0) { keepT = 0.5; Keep(); }
            var (mx, mz) = Steer(b, c.Deft, reach);
            var crush = b.HostilesInRadius(p.X, p.Z, 2.2);
            if (crush.Count >= 3 && p.DashCharges > 0) b.Dash(mx, mz);
            if (c.S.Art != null) UseArt(b, c.S.Art, mx, mz);
            b.Tick(dt, mx, mz);
            p.Hp = Math.Max(p.Hp, b.MaxHp * 0.5);
            foreach (var ev in b.Events.Drain())
            {
                switch (ev)
                {
                    case Ev.PlayerHit ph when ph.Amount > 0:
                        taken += ph.Amount; hitsTaken++;
                        bySource[ph.Source] = bySource.GetValueOrDefault(ph.Source) + ph.Amount;
                        break;
                    case Ev.Hit h when !h.Dot:
                        hitsOn++;
                        if (h.Blocked) blocked++;
                        if (!firstHit.ContainsKey(h.Target)) firstHit[h.Target] = t;
                        break;
                    case Ev.Hit h when h.Dot:
                        if (!firstHit.ContainsKey(h.Target)) firstHit[h.Target] = t;
                        break;
                    case Ev.Kill k when !k.Boss:
                        if (k.ByPlayer) kills++;
                        if (firstHit.TryGetValue(k.Enemy, out var fh))
                            (isElite.GetValueOrDefault(k.Enemy) ? ttkElite : ttk).Add(t - fh);
                        firstHit.Remove(k.Enemy);
                        break;
                    case Ev.Spawn s:
                        // Raised dead and split young: not the director's, but they count.
                        if (!spawnedAt.ContainsKey(s.Enemy) || spawnedAt[s.Enemy] < t - 0.01)
                        {
                            if (s.Style == SpawnStyle.Rise && s.Def == "risen" && t > 0.1) raised++;
                            spawnedAt[s.Enemy] = t; isElite[s.Enemy] = false; firstHit.Remove(s.Enemy);
                        }
                        break;
                    case Ev.PerfectDodge: perfects++; break;
                    case Ev.Bark bk when bk.Text == "Interrupted!": interrupts++; break;
                }
            }
            t += dt;
        }
        // The callers' raised: Spawn events from the director are told apart by the dictionary write in Keep.
        double min = c.Seconds / 60;
        var top = bySource.OrderByDescending(kv => kv.Value).FirstOrDefault();
        return new Result(c, kills, kills / min, Median(ttk), Median(ttkElite), taken, taken / min / baseHp * 100, hitsTaken / min,
            hitsOn > 0 ? (double)blocked / hitsOn : 0, perfects, interrupts, top.Key ?? "", taken > 0 ? top.Value / taken : 0, raised, splits);
    }

    static double Median(List<double> xs)
    {
        if (xs.Count == 0) return double.NaN;
        var s = xs.OrderBy(x => x).ToList();
        return s[s.Count / 2];
    }

    /// <summary>The art, by a simple rule: a crowd near, or a champion or a caster in reach.</summary>
    static void UseArt(Battle b, string art, double mx, double mz)
    {
        var p = b.Player;
        Enemy? key = null;
        double kd = 9;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            if (!(e.Elite || e.Def.Raise != null || e.State == EnemyState.Casting)) continue;
            double d = Dist(e.X, e.Z, p.X, p.Z);
            if (d < kd) { kd = d; key = e; }
        }
        bool crowd = b.HostilesInRadius(p.X, p.Z, 6).Count >= 5;
        if (key == null && !crowd) return;
        double ax = mx, az = mz;
        // Aimed arts that strike or close go at the key creature; ways out go where the bot is going.
        if (key != null && art is "shield_bash" or "grapple" or "leap" or "bull_rush")
        {
            double l = Math.Max(0.01, Dist(key.X, key.Z, p.X, p.Z));
            ax = (key.X - p.X) / l; az = (key.Z - p.Z) / l;
        }
        b.UseAbility(ax, az);
    }

    /// <summary>The balance lab's arena bot: give ground when pressed, go to the fight
    /// otherwise; deft, it also reads lunges, pots, burning ground and throwers.</summary>
    static (double, double) Steer(Battle b, bool deft, double reach)
    {
        var p = b.Player;
        double mx, mz;
        var press = b.HostilesInRadius(p.X, p.Z, 3.4);
        Enemy? nearest = null;
        double nd = double.MaxValue;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            double d2 = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d2 < nd) { nd = d2; nearest = e; }
        }
        if (press.Count >= 2)
        {
            double cx = press.Average(e => e.X) - p.X, cz = press.Average(e => e.Z) - p.Z;
            double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            mx = -cx / cl * 0.7 - cz / cl * 0.7; mz = -cz / cl * 0.7 + cx / cl * 0.7;
        }
        else if (nearest != null && Dist(nearest.X, nearest.Z, p.X, p.Z) > reach) { mx = nearest.X - p.X; mz = nearest.Z - p.Z; }
        else if (nearest != null) { mx = -(nearest.Z - p.Z); mz = nearest.X - p.X; }
        else { mx = -p.X; mz = -p.Z; }
        if (deft) Read(b, press.Count >= 2, ref mx, ref mz);
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
        if (far > 40) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }
        if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) { (mx, mz) = (-mz, mx); }
        double ml = Math.Sqrt(mx * mx + mz * mz);
        if (ml > 1e-6) { mx /= ml; mz /= ml; }
        return (mx, mz);
    }

    /// <summary>The deft bot's reading (ArenaPlay.Read): the worst danger first.</summary>
    static void Read(Battle b, bool busy, ref double mx, ref double mz)
    {
        var p = b.Player;
        foreach (var e in b.Enemies.Living())
        {
            if (e.State != EnemyState.Windup || e.Disposition != Disposition.Hostile) continue;
            var lunge = e.Def.Charge ?? e.Def.Lunge;
            if (lunge == null) continue;
            double reach = lunge.Speed * lunge.Time + e.Radius + 1;
            double rx = p.X - e.X, rz = p.Z - e.Z;
            double along = rx * e.LungeX + rz * e.LungeZ;
            double across = rx * -e.LungeZ + rz * e.LungeX;
            if (along < -1 || along > reach || Math.Abs(across) > e.Radius * 1.1 + p.Radius + 0.9) continue;
            double side = across >= 0 ? 1 : -1;
            mx = -e.LungeZ * side; mz = e.LungeX * side;
            if (e.StateT < 0.3 && p.DashCharges > 0) b.Dash(mx, mz);
            return;
        }
        foreach (var pr in b.Projectiles.Living())
        {
            if (!pr.Lob || pr.Owner != Side.Enemy) continue;
            double d = Dist(pr.LandX, pr.LandZ, p.X, p.Z);
            if (d < 2.2) { mx = (p.X - pr.LandX) / Math.Max(0.1, d); mz = (p.Z - pr.LandZ) / Math.Max(0.1, d); return; }
        }
        foreach (var z in b.Zones.Living())
        {
            if (z.Owner is not (Side.Enemy or Side.World)) continue;
            double d = Dist(z.X, z.Z, p.X, p.Z);
            if (d < z.Radius + p.Radius) { mx = (p.X - z.X) / Math.Max(0.1, d); mz = (p.Z - z.Z) / Math.Max(0.1, d); return; }
        }
        if (busy) return;
        Enemy? shooter = null;
        double sd = 11;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Def.Ranged == null || e.Elite || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            double d = Dist(e.X, e.Z, p.X, p.Z);
            if (d < sd) { sd = d; shooter = e; }
        }
        if (shooter != null && sd > 1.8 && b.HostilesInRadius(p.X, p.Z, 4.5).Count < 3) { mx = shooter.X - p.X; mz = shooter.Z - p.Z; }
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    static void WriteCsv(string path, List<Result> rows)
    {
        var o = new StringBuilder("group,setup,bot,oath,seed,kills,kills_per_min,ttk_s,ttk_elite_s,taken,taken_pct_hp_per_min,hits_taken_per_min,blocked_share,perfect_dodges,interrupts,top_source,top_share,raised\n");
        foreach (var r in rows)
            o.AppendLine(string.Join(",", r.C.G.Id, r.C.S.Id, r.C.Deft ? "deft" : "plain", r.C.Oaths.Length == 0 ? "none" : string.Join("+", r.C.Oaths), r.C.Seed,
                r.Kills, F(r.KillsPerMin), F(r.Ttk, "0.00"), F(r.TtkElite, "0.00"), F(r.Taken, "0"), F(r.TakenPerMin), F(r.HitsTakenPerMin),
                F(r.BlockedShare, "0.000"), r.Perfects, r.Interrupts, r.TopSource.Replace(",", ""), F(r.TopShare, "0.00"), r.Raised));
        File.WriteAllText(path, o.ToString());
    }

    static double Mean(IEnumerable<double> xs)
    {
        var l = xs.Where(x => !double.IsNaN(x)).ToList();
        return l.Count == 0 ? double.NaN : l.Average();
    }

    /// <summary>Tables: per group and loadout, kills a minute, time to kill and damage taken
    /// (as % of a warden's 170 health a minute), plain and deft side by side.</summary>
    static string Summary(List<Result> rows)
    {
        var s = new StringBuilder("# Bestiary probe\n\n");
        var plain = rows.Where(r => r.C.Oaths.Length == 0).ToList();
        string Cell(IEnumerable<Result> rs, Func<Result, double> f, string fmt = "0.0") => F(Mean(rs.Select(f)), fmt);
        var setups = plain.Select(r => r.C.S.Id).Distinct().Where(x => !x.StartsWith("art:")).ToList();
        foreach (var (title, f, fmt) in new (string, Func<Result, double>, string)[]
        {
            ("Kills a minute", r => r.KillsPerMin, "0"),
            ("Median seconds from first blow to death (rank and file; elites for elite groups)", r => double.IsNaN(r.Ttk) ? r.TtkElite : r.Ttk, "0.0"),
            ("Damage taken, % of 170 health a minute", r => r.TakenPerMin, "0"),
        })
            foreach (var bot in new[] { "plain", "deft" })
            {
                s.AppendLine($"## {title} ({bot} bot)\n");
                s.AppendLine("| group | " + string.Join(" | ", setups) + " |");
                s.AppendLine("|---|" + string.Concat(setups.Select(_ => "---:|")));
                foreach (var g in plain.Select(r => r.C.G.Id).Distinct())
                    s.AppendLine($"| {g} | " + string.Join(" | ", setups.Select(su => Cell(plain.Where(r => r.C.G.Id == g && r.C.S.Id == su && (r.C.Deft == (bot == "deft"))), f, fmt))) + " |");
                s.AppendLine();
            }
        var arts = plain.Where(r => r.C.S.Id.StartsWith("art:") || r.C.S.Id == "volley").ToList();
        s.AppendLine("## The arts (on the volley; deft bot): kills a minute / damage taken %/min / interrupts a run\n");
        var artIds = arts.Select(r => r.C.S.Id).Distinct().ToList();
        s.AppendLine("| group | " + string.Join(" | ", artIds) + " |");
        s.AppendLine("|---|" + string.Concat(artIds.Select(_ => "---:|")));
        foreach (var g in arts.Where(r => r.C.S.Id.StartsWith("art:")).Select(r => r.C.G.Id).Distinct())
            s.AppendLine($"| {g} | " + string.Join(" | ", artIds.Select(a =>
            {
                var rs = arts.Where(r => r.C.G.Id == g && r.C.S.Id == a && r.C.Deft).ToList();
                return $"{Cell(rs, r => r.KillsPerMin, "0")} / {Cell(rs, r => r.TakenPerMin, "0")} / {Cell(rs, r => r.Interrupts, "0")}";
            })) + " |");
        s.AppendLine();
        var oathRows = rows.Where(r => r.C.Oaths.Length > 0 || (new[] { "wolf", "risen", "mix:shieldwall" }.Contains(r.C.G.Id) && new[] { "blade", "volley", "dawn" }.Contains(r.C.S.Id))).ToList();
        s.AppendLine("## The oaths: kills a minute / damage taken %/min (plain bot | deft bot)\n");
        var oathIds = new[] { "none", "iron", "ruin", "embers", "winter", "hunt", "blight", "swarm" };
        s.AppendLine("| group · loadout | " + string.Join(" | ", oathIds) + " |");
        s.AppendLine("|---|" + string.Concat(oathIds.Select(_ => "---|")));
        foreach (var gid in new[] { "wolf", "risen", "mix:shieldwall" })
            foreach (var sid in new[] { "blade", "volley", "dawn" })
                s.AppendLine($"| {gid} · {sid} | " + string.Join(" | ", oathIds.Select(o =>
                {
                    var rs = oathRows.Where(r => r.C.G.Id == gid && r.C.S.Id == sid && (r.C.Oaths.Length == 0 ? "none" : r.C.Oaths[0]) == o).ToList();
                    var pl = rs.Where(r => !r.C.Deft); var de = rs.Where(r => r.C.Deft);
                    return $"{Cell(pl, r => r.KillsPerMin, "0")}/{Cell(pl, r => r.TakenPerMin, "0")} \\| {Cell(de, r => r.KillsPerMin, "0")}/{Cell(de, r => r.TakenPerMin, "0")}";
                })) + " |");
        s.AppendLine();
        s.AppendLine("## Where the damage came from (top source and its share, deft bot, all loadouts)\n");
        s.AppendLine("| group | top source | share | hits taken a minute | blows on them that glanced |");
        s.AppendLine("|---|---|---:|---:|---:|");
        foreach (var g in plain.Select(r => r.C.G.Id).Distinct())
        {
            var rs = plain.Where(r => r.C.G.Id == g && r.C.Deft && !r.C.S.Id.StartsWith("art:")).ToList();
            var src = rs.GroupBy(r => r.TopSource).OrderByDescending(x => x.Count()).First().Key;
            s.AppendLine($"| {g} | {src} | {Cell(rs, r => r.TopShare, "0.00")} | {Cell(rs, r => r.HitsTakenPerMin, "0")} | {Cell(rs, r => r.BlockedShare, "0.00")} |");
        }
        return s.ToString();
    }
}
