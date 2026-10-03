using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Tests;

// Boss probe (docs/bosses/AUDIT.md §4): the feel probe's arena bot
// (docs/feel/probe, after godot/tests/ArenaPlay.cs) played to the half hour
// and through the boss, with the survivor's damage scaled by a "power" factor
// from the first second, to stand in for builds from weak to absurd. For each
// run it reports how long the heralds and the boss lived, how hard the boss
// hit, how much of the survivor's health the fight cost, and whether the
// survivor lived. Nothing in the game is changed.
//
// Arguments: power factors (comma list), tiers (comma list), optional calling.
//   dotnet run --project docs/bosses/probe -c Release -- 0.5,1,3,10 1,3
static class Probe
{
    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    static void Main(string[] args)
    {
        var powers = (args.Length > 0 ? args[0] : "0.5,1,3,10").Split(',').Select(double.Parse).ToArray();
        var tiers = (args.Length > 1 ? args[1] : "1").Split(',').Select(int.Parse).ToArray();
        var cases = new (int Seed, string Calling, string People)[] { (42, "warden", "pack"), (7, "stalker", "dead"), (99, "arcanist", "kerchiefs"), (1234, "reaver", "lamplings") };
        if (args.Length > 2) cases = cases.Where(c => c.Calling == args[2]).ToArray();
        Console.WriteLine("calling  people     tier power | h10 ttk  h20 ttk | bossHP   ttk(s)  bossDPS  hitsOnBoss  hpLost%  minHp%  boss blows | end");
        foreach (var t in tiers)
            foreach (var pw in powers)
                foreach (var c in cases) Run(c.Seed, c.Calling, t, c.People, pw);
    }

    static void Run(int seed, string calling, int tier, string people, double power)
    {
        var a = Callings.Archetype(calling);
        var j = global::SurvivorUnchained.Play.Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        var spec = new ArenaSpec { Id = "table:bot", Name = "Probe", Seed = seed, Tier = tier, People = people, Oaths = new() };
        Arenas.Begin(j.World, spec);
        var map = MapGen.Generate(spec.Map);
        var host = new FakeHost(j, map.Meta, map.Ground);
        var zone = new global::SurvivorUnchained.Play.Zones.ArenaRun(host, map, spec);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed, arena: true);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        // The build's strength, as one multiplier on everything the survivor deals.
        if (power != 1) b.Stats.Add(new StatMod(Stat.Damage, ModKind.More, power - 1, "probe"));
        const double dt = 1 / 60.0;
        double t = 0;
        var p = b.Player;
        // Named fights: the heralds (10, 20) and the boss (30), tracked by id.
        var champs = new Dictionary<int, (double Born, string Kind, double MaxHp)>();
        var lived = new List<(string Kind, double Secs)>();
        int? bossId = null;
        double bossBorn = 0, bossHp = 0, bossDealt = 0, hpAtBoss = 0, minHp = 1, lostInFight = 0, bossBlows = 0, worstBlow = 0;
        int hitsOnBoss = 0;
        string bossDef = MapOffers.People(people).Boss, bossName = "?";
        var seen = new HashSet<int>();
        double? bossTtk = null;
        double stopAt = 40 * 60;
        while (t < stopAt && p.Alive)
        {
            double mx, mz;
            var press = b.HostilesInRadius(p.X, p.Z, 3.4);
            var nearest = b.Enemies.Living().Where(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying)
                .OrderBy(e => (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)).FirstOrDefault();
            var stone = b.Pickups.Living().Where(k => k.Kind == PickupKind.Ember && Dist(k.X, k.Z, p.X, p.Z) < 12)
                .OrderBy(k => Dist(k.X, k.Z, p.X, p.Z)).FirstOrDefault();
            if (press.Count >= 2)
            {
                double cx = press.Average(e => e.X) - p.X, cz = press.Average(e => e.Z) - p.Z;
                double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
                mx = -cx / cl * 0.7 - cz / cl * 0.7; mz = -cz / cl * 0.7 + cx / cl * 0.7;
            }
            else if (stone != null && (nearest == null || Dist(nearest.X, nearest.Z, p.X, p.Z) > 5)) { mx = stone.X - p.X; mz = stone.Z - p.Z; }
            else if (nearest != null && Dist(nearest.X, nearest.Z, p.X, p.Z) > 6) { mx = nearest.X - p.X; mz = nearest.Z - p.Z; }
            else if (nearest != null) { mx = -(nearest.Z - p.Z); mz = nearest.X - p.X; }
            else { mx = -p.X; mz = -p.Z; }
            double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
            if (far > 60) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }
            if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) { (mx, mz) = (-mz, mx); }
            double ml = Math.Sqrt(mx * mx + mz * mz);
            if (ml > 1e-6) { mx /= ml; mz /= ml; }
            var crush = b.HostilesInRadius(p.X, p.Z, 2.2);
            if (crush.Count >= 3 && p.DashCharges > 0) b.Dash(mx, mz);
            if (b.HostilesInRadius(p.X, p.Z, 6).Count >= 5) b.UseAbility(mx, mz);
            if (p.Hp < b.MaxHp * 0.33) j.Quaff(b);
            double hpBefore = p.Hp;
            zone.Step(dt);
            zone.Frame(dt);
            b.Tick(dt, mx, mz);
            foreach (var ev in b.Events.Drain())
            {
                switch (ev)
                {
                    case Ev.Spawn sp when bossId == null && t >= 30 * 60 - 0.1 && sp.Def == bossDef:
                    {
                        var e = b.Enemies.Living().FirstOrDefault(x => x.Id == sp.Enemy);
                        if (e == null) break;
                        bossId = e.Id; bossBorn = t; bossHp = e.MaxHp; bossName = e.Def.Name; hpAtBoss = p.Hp / b.MaxHp; minHp = hpAtBoss;
                        champs[e.Id] = (t, "boss", e.MaxHp);
                        break;
                    }
                    case Ev.Hit h when bossId == h.Target:
                        if (!h.Dot) hitsOnBoss++;
                        bossDealt += h.Amount;
                        break;
                    case Ev.PlayerHit ph when bossId != null && !ph.Dodged:
                        if (ph.Source == bossName) { bossBlows++; worstBlow = Math.Max(worstBlow, ph.Amount / b.MaxHp); }
                        break;
                    case Ev.Kill k:
                        if (champs.TryGetValue(k.Enemy, out var c))
                        {
                            lived.Add((c.Kind, t - c.Born));
                            champs.Remove(k.Enemy);
                            if (k.Enemy == bossId) bossTtk = t - bossBorn;
                        }
                        break;
                }
            }
            // Heralds get their title a moment after they spawn.
            foreach (var e in b.Enemies.Living())
                if (e.Elite && e.Named?.Title.StartsWith("Herald") == true && !champs.ContainsKey(e.Id) && !seen.Contains(e.Id))
                {
                    seen.Add(e.Id);
                    champs[e.Id] = (t, $"herald@{(int)Math.Round(t / 60)}", e.MaxHp);
                }
            if (bossId != null && bossTtk == null)
            {
                minHp = Math.Min(minHp, p.Hp / b.MaxHp);
                if (p.Hp < hpBefore) lostInFight += (hpBefore - p.Hp) / b.MaxHp;
            }
            host.Pass(dt);
            j.BankArt(b);
            while (b.DraftOwed)
            {
                var offers = LevelUp.Draft(b, 3);
                if (offers.Count == 0) break;
                LevelUp.Choose(b, offers[0]);
            }
            t += dt;
            if (bossTtk != null && stopAt > t + 5) stopAt = t + 5;
        }
        var h10 = lived.FirstOrDefault(l => l.Kind is "herald@10");
        var h20 = lived.FirstOrDefault(l => l.Kind is "herald@20");
        string ttk = bossTtk is double s ? $"{s,6:0.0}" : "     -";
        string dps = bossTtk is double s2 && s2 > 0 ? $"{bossHp / s2,7:0}" : bossId != null ? $"{bossDealt / Math.Max(1, t - bossBorn),7:0}" : "      -";
        string end = bossTtk != null ? "won" : p.Alive ? (bossId != null ? "boss alive" : "no boss") : $"fell {t / 60:0.0}";
        Console.WriteLine($"{calling,-8} {people,-10} {tier,4} {power,5} | {(h10.Kind != null ? $"{h10.Secs,4:0}" : "   -")} {"",3} {(h20.Kind != null ? $"{h20.Secs,4:0}" : "   -")} {"",3} | {bossHp,7:0} {ttk} {dps} {hitsOnBoss,10} {100 * lostInFight,8:0} {100 * minHp,7:0} {bossBlows,5:0} (worst {100 * worstBlow:0}%) | {end}; ember {b.EmberLevel}");
    }
}
