using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>One map to play: who, how hard, with what character, under which mods.</summary>
public sealed record MapRunSpec(int Seed, string Calling, int Tier, string People, int Level, int GearRarity, string[] Mods, bool Deft, double Cap = 25)
{
    public string Key => $"{Calling}/t{Tier}/{People}/s{Seed}/L{Level}/g{GearRarity}{(Mods.Length > 0 ? "/" + string.Join("+", Mods) : "")}";
}

public sealed class MapRunResult
{
    public MapRunSpec Spec = null!;
    public bool Cleared, Closed;
    public double Minutes, LowHp = 1, DamageTaken;
    public int Falls, Kills, Packs, PacksCleared, Quaffs, Items, Charts, Gold;
    public double? BossTtk;
    public int BossPhase;
    /// <summary>What was left of the ruler when the map closed (-1: never met).</summary>
    public double BossLeft = -1;
    /// <summary>Seconds between kills, and between packs put down (the experience lead's rhythm:
    /// a kill or find every 10-20 s, a pack every 20-40 s).</summary>
    public double KillGap, PackGap;
    public string Build = "", KilledBy = "";
    public double MaxHp;
}

/// <summary>A Wayfinder's map played through headless (Play/Zones/MapRun.cs on MapGen's winding
/// way): the survivor's own build, kept for good, walked along the way by the Pilot's hands,
/// fighting what wakes, to the ruler at the end.</summary>
public static class MapSim
{
    const double Dt = 1 / 60.0;

    /// <summary>A survivor at a level, as a player would have dressed them by then: the calling's own
    /// path's three skills at the day's rank, the points in the calling's attribute, and plain gear
    /// at a rarity in every slot.</summary>
    public static Journey Survivor(string calling, int level, int gearRarity, int seed)
    {
        var a = Callings.Archetype(calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        var ch = j.Ch;
        while (ch.Level < level) Character.GainXp(ch, Character.XpForLevel(ch.Level) - ch.Xp + 1);
        switch (calling) { case "arcanist": ch.Attributes.Wits += ch.Points; break; case "stalker": ch.Attributes.Finesse += ch.Points; break; default: ch.Attributes.Might += ch.Points; break; }
        ch.Points = 0;
        var path = Content.Paths.All.Where(p => p.Callings.Contains(calling)).OrderBy(p => p.Id).ToList();
        var pick = path[seed % path.Count];
        foreach (var id in pick.Weapons.Concat(path.SelectMany(p => p.Weapons)).Distinct())
        {
            if (ch.Slotted.Count >= SkillBook.Slots(ch)) break;
            if (!Content.Weapons.All.ContainsKey(id) || !SkillBook.Meets(ch, id) || ch.Skills.Contains(id)) continue;
            ch.Skills.Add(id);
            ch.Slotted.Add(id);
        }
        var rng = new Rng((uint)seed * 31 + 5);
        (EquipSlot Slot, string Def)[] dress =
        [
            (EquipSlot.Head, rng.Chance(0.5) ? "iron_helm" : "leather_cap"), (EquipSlot.Body, rng.Chance(0.5) ? "chain_shirt" : "padded_jerkin"),
            (EquipSlot.Cloak, "travelers_cloak"), (EquipSlot.Amulet, "bone_amulet"), (EquipSlot.Ring1, "silver_ring"), (EquipSlot.Ring2, "copper_ring"),
        ];
        foreach (var (slot, def) in dress)
            ch.Equipment[slot] = Inventory.Make(ch, def, 1, gearRarity, (uint)rng.Int(1, 1 << 30));
        return j;
    }

    public static MapRunResult Play(MapRunSpec spec)
    {
        var j = Survivor(spec.Calling, spec.Level, spec.GearRarity, spec.Seed);
        for (int i = 0; i < 4; i++) Inventory.AddToPack(j.Ch, Inventory.Make(j.Ch, "health_draught", 1));
        var chart = new Chart { Tier = spec.Tier, People = spec.People, Seed = spec.Seed * 7919 + spec.Tier, Mods = spec.Mods.ToList(), Rarity = spec.Mods.Length == 0 ? 0 : spec.Mods.Length <= 2 ? 1 : 2, Name = "The Harness Map" };
        var map = MapGen.Generate(chart.Map);
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new MapRun(host, map, chart);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed);
        // As the game wires it: what is picked up goes into the pack (charts and materials); gear is
        // counted and stashed, so the pack never fills and leaves a piece lying under the hands.
        var zh = zone.Hooks;
        b.Hooks = BattleHooks.Following(zh);
        int gear = 0;
        b.Hooks.OnPickup = pk =>
        {
            if (zh.OnPickup != null && !zh.OnPickup(pk)) return false;
            if (pk.Kind == PickupKind.Item && pk.Ref != null && Charts.FromRef(pk.Ref) == null) { gear++; return true; }
            j.PickedUp(pk);
            return true;
        };
        host.Battle = b;
        zone.Begin(b);
        var r = new MapRunResult { Spec = spec, Packs = zone.PackCount, MaxHp = b.MaxHp, Build = string.Join(" ", b.Weapons.Select(w => $"{w.Id}{w.Rank}")) };
        var nav = new NavField(map, b, map.Boss.X, map.Boss.Z);
        double along = 0;
        var p = b.Player;
        double t = 0, lastKill = 0, lastPack = 0, stuck = 0, bestToGo = double.MaxValue;
        int holds = 0;
        int lastCleared = 0;
        var kills = new List<double>();
        bool trace = Environment.GetEnvironmentVariable("MAP_TRACE") == "1", blows = Environment.GetEnvironmentVariable("MAP_BLOWS") == "1";
        var packs = new List<double>();
        while (t < spec.Cap * 60 && !zone.Over)
        {
            // Onward: downhill on the way's distance to the ruler, a few metres ahead, by a line
            // that is clear of what stands on the ground.
            var onward = nav.Onward(p.X, p.Z);
            along = nav.ToGo(p.X, p.Z);
            var (mx, mz) = Pilot.Steer(b, spec.Deft, zone.BossScript, onward);
            // No nearer the ruler in twenty seconds with the ruler not up (a pickup out of reach, a
            // corner, a tunneller under the ground the hands wait on): walk on, longer each time.
            if ((int)(t / 20) != (int)((t + Dt) / 20))
            {
                if (zone.Boss == null && !double.IsNaN(along) && along > bestToGo - 3)
                {
                    holds++;
                    stuck = 4 * Math.Pow(2, Math.Min(3, holds - 1));
                }
                else holds = 0;
                if (!double.IsNaN(along)) bestToGo = Math.Min(bestToGo, along);
            }
            if (stuck > 0)
            {
                stuck -= Dt;
                (mx, mz) = (onward.X - p.X, onward.Z - p.Z);
                double ml = Math.Max(1e-6, Math.Sqrt(mx * mx + mz * mz));
                (mx, mz) = (mx / ml, mz / ml);
            }
            if (Pilot.Act(b, j, mx, mz)) r.Quaffs++;
            zone.Step(Dt);
            zone.Frame(Dt);
            b.Tick(Dt, mx, mz);
            foreach (var ev in b.Events.Drain())
                switch (ev)
                {
                    case Ev.Kill k when k.ByPlayer: kills.Add(t - lastKill); lastKill = t; break;
                    case Ev.PlayerDeath d: r.KilledBy = d.Killer; break;
                    // MAP_BLOWS=1: the blows that land in the ruler's fight (why its fight was lost).
                    case Ev.PlayerHit ph when blows && zone.Boss != null:
                        Console.Error.WriteLine($"{t / 60:0.000} {ph.Source,-22} {ph.Amount,6:0} {(ph.Dodged ? "dodged" : "")} hp {p.Hp:0}/{b.MaxHp:0} phase {zone.BossScript?.PhaseIx}");
                        break;
                }
            host.Pass(Dt);
            r.LowHp = Math.Min(r.LowHp, p.Hp / b.MaxHp);
            if (zone.PacksCleared > lastCleared) { packs.Add(t - lastPack); lastPack = t; lastCleared = zone.PacksCleared; }
            // Cleared: walk to the way out and take it.
            if (zone.Cleared && !zone.Over) zone.Leave();
            if (!p.Alive) break;
            // MAP_TRACE=1: where the hands are every ten seconds (why a map was not finished).
            if (trace && (int)(t / 10) != (int)((t + Dt) / 10))
                Console.Error.WriteLine($"{t / 60:0.00} at ({p.X:0.0},{p.Z:0.0}) m ({mx:0.00},{mz:0.00}) v ({p.Vx:0.0},{p.Vz:0.0}) blocked {b.Collision.Blocked(p.X, p.Z, p.Radius)} leap {p.Leap != null} dash {p.DashT:0.00} slow {p.SlowF:0.00} spd {b.Stats.Get(Stat.MoveSpeed):0.0} over {b.Over} stuck {stuck:0.0} to go {along:0} m onward ({onward.X:0},{onward.Z:0}) roused {b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && (e.Wake == 0 || e.Roused))} hp {p.Hp:0}/{b.MaxHp:0} packs {zone.PacksCleared}/{zone.PacksPlaced}");
            t += Dt;
        }
        r.Cleared = zone.Cleared;
        r.Closed = !zone.Cleared && (zone.Falls >= MapRun.FallsAllowed || !p.Alive);
        r.Minutes = t / 60;
        r.Falls = zone.Falls;
        r.Kills = zone.Kills;
        r.PacksCleared = zone.PacksCleared;
        r.BossTtk = zone.Result?.BossTtk;
        r.BossPhase = zone.BossScript?.PhaseIx ?? -1;
        if (zone.Boss is { } zb && zone.BossScript != null) r.BossLeft = zb.Hp / zone.BossScript.MaxHp;
        r.DamageTaken = b.DamageTaken;
        r.KillGap = Median(kills);
        r.PackGap = Median(packs);
        r.Items = gear;
        r.Charts = j.Ch.Pack.Count(i => i?.Chart != null);
        r.Gold = (int)j.Ch.Gold;
        return r;
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    static double Median(List<double> xs)
    {
        if (xs.Count == 0) return double.NaN;
        var s = xs.OrderBy(x => x).ToList();
        return s[s.Count / 2];
    }

    public static string Report(List<MapRunResult> rs)
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine("| group | runs | cleared | closed | falls/run | minutes | boss TTK (s) | kill gap (s) | pack gap (s) | lowest | items | charts | gold |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        void Row(string name, List<MapRunResult> l)
        {
            if (l.Count == 0) return;
            double M(IEnumerable<double> xs) { var a = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList(); return a.Count == 0 ? double.NaN : a[a.Count / 2]; }
            sb.AppendLine($"| {name} | {l.Count} | {100 * l.Count(x => x.Cleared) / l.Count}% | {100 * l.Count(x => x.Closed) / l.Count}% | {l.Average(x => x.Falls):0.00} | {M(l.Where(x => x.Cleared).Select(x => x.Minutes)):0.0} | {M(l.Where(x => x.BossTtk != null).Select(x => x.BossTtk!.Value)):0} | {M(l.Select(x => x.KillGap)):0.0} | {M(l.Select(x => x.PackGap)):0} | {M(l.Select(x => x.LowHp)):0.00} | {M(l.Select(x => (double)x.Items)):0} | {M(l.Select(x => (double)x.Charts)):0} | {M(l.Select(x => (double)x.Gold)):0} |");
        }
        Row("all", rs);
        foreach (var g in rs.GroupBy(x => $"tier {x.Spec.Tier}").OrderBy(g => g.Key)) Row(g.Key, g.ToList());
        foreach (var g in rs.GroupBy(x => x.Spec.Calling).OrderBy(g => g.Key)) Row(g.Key, g.ToList());
        foreach (var g in rs.GroupBy(x => x.Spec.People).OrderBy(g => g.Key)) Row(g.Key, g.ToList());
        return sb.ToString();
    }
}
