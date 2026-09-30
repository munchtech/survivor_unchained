using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>
/// A map played through without a screen, by a plain-minded survivor: walk
/// the way from the start to the boss, wake each altar and hold its clearing,
/// dash out of a crush, use the art on a crowd, take the first card offered.
/// It reports how long the map took, what died and whether the survivor did
/// (for tuning a map's density and length against 8 to 12 minutes).
/// Only with MAP_PLAY=1 (it takes a while): dotnet test --filter MapPlay.
/// </summary>
public class MapPlay(ITestOutputHelper log)
{
    sealed record Result(bool Cleared, bool Died, double Minutes, int Kills, int Ember, double LowHp, int Packs, double[] Phases, string Note);

    static Result Play(int seed, string calling, int tier, string people, string[] oaths, ITestOutputHelper? log = null)
    {
        var a = Callings.Archetype(calling);
        var j = global::SurvivorUnchained.Play.Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0], StartBoon = Boons.StartBlessings[0],
        }, (uint)seed);
        var offer = new MapOffer(new MapSpec { Seed = seed, Tier = tier, Name = "The Test Wood", Oaths = oaths.ToList() }, people);
        MapOffers.Remember(j.World, offer);
        var map = MapGen.Generate(offer.Spec);
        var host = new FakeHost(j, map.Meta, map.Ground);
        var zone = new global::SurvivorUnchained.Play.Zones.MapRun(host, map, people);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed);
        b.Hooks = zone.Hooks;
        var kill = b.Hooks.OnKill;
        b.Hooks.OnKill = (e, by) => { kill?.Invoke(e, by); j.Killed(e, by); };
        host.Battle = b;
        zone.Begin(b);

        var way = map.Meta.Paths["WAY"];
        var flow = new FlowField(b.Collision, 44);
        int k = 0;
        const double dt = 1 / 60.0;
        double t = 0, low = 1;
        var phases = new List<double>();
        int spent = 0;
        var hurt = new Dictionary<string, double>();
        (double X, double Z, double R)? holding = null;
        var p = b.Player;
        while (t < 25 * 60 && p.Alive)
        {
            // An altar in reach is woken, and its clearing held until it is spent.
            var waking = zone.Interactables.FirstOrDefault(i => i.Id.StartsWith("altar") && i.When!() && Dist(i.X, i.Z, p.X, p.Z) < 6);
            if (waking != null && holding == null)
            {
                waking.Act();
                var al = map.Altars.First(x => $"altar{x.Index}" == waking.Id);
                holding = (al.X, al.Z, al.R);
            }
            double tx, tz;
            bool bossTime = Dist(map.Boss.X, map.Boss.Z, p.X, p.Z) < map.Boss.R + 6;
            if (holding is { } h)
            {
                double ang = t * 0.5;
                tx = h.X + Math.Cos(ang) * h.R * 0.5; tz = h.Z + Math.Sin(ang) * h.R * 0.5;
            }
            else if (bossTime)
            {
                // Circle the last clearing.
                double ang = t * 0.35;
                tx = map.Boss.X + Math.Cos(ang) * map.Boss.R * 0.6; tz = map.Boss.Z + Math.Sin(ang) * map.Boss.R * 0.6;
            }
            else
            {
                while (k < way.Length - 1 && Dist(way[k][0], way[k][1], p.X, p.Z) < 4) k++;
                tx = way[k][0]; tz = way[k][1];
            }
            flow.Update(tx, tz);
            double mx = tx - p.X, mz = tz - p.Z;
            if (flow.Dir(p.X, p.Z, out var fx, out var fz)) { mx = fx; mz = fz; }
            // With a crowd on you, kite: circle away from the thick of them and let
            // the weapons work; go on along the way when it thins.
            var chasing = b.HostilesInRadius(p.X, p.Z, 9).Where(e => e.Target == -1).ToList();
            if (chasing.Count >= 4)
            {
                double cx = chasing.Average(e => e.X) - p.X, cz = chasing.Average(e => e.Z) - p.Z;
                double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
                double ax = -cx / cl, az = -cz / cl;
                // Away and round (a quarter turn), with a pull back toward the way.
                double rx = ax * 0.6 - az * 0.8, rz = az * 0.6 + ax * 0.8;
                double ml0 = Math.Max(0.01, Math.Sqrt(mx * mx + mz * mz));
                mx = rx + mx / ml0 * 0.35; mz = rz + mz / ml0 * 0.35;
                if (b.Collision.Blocked(p.X + mx * 1.2, p.Z + mz * 1.2, p.Radius)) { mx = -mx * 0.2 + ax; mz = -mz * 0.2 + az; }
            }
            var crush = b.HostilesInRadius(p.X, p.Z, 2.2);
            if (crush.Count >= 3 && p.DashCharges > 0)
            {
                double cx = crush.Average(e => e.X) - p.X, cz = crush.Average(e => e.Z) - p.Z;
                b.Dash(-cx - cz * 0.5, -cz + cx * 0.5);
            }
            if (log != null && (int)(t / 10) != (int)((t - dt) / 10))
                log.WriteLine($"  t {t:0} at {p.X:0.0},{p.Z:0.0} way {k}/{way.Length} to {tx:0},{tz:0} ({Dist(tx, tz, p.X, p.Z):0.0} m) flow {flow.Dir(p.X, p.Z, out _, out _)} move {mx:0.00},{mz:0.00} hunting {b.Enemies.Living().Count(e => e.Target == -1)}");
            double ml = Math.Sqrt(mx * mx + mz * mz);
            if (ml > 1e-6) { mx /= ml; mz /= ml; }
            if (b.HostilesInRadius(p.X, p.Z, 6).Count >= 4) b.UseAbility(mx, mz);
            if (p.Hp < b.MaxHp * 0.33) j.Quaff(b);
            zone.Step(dt);
            zone.Frame(dt);
            b.Tick(dt, mx, mz);
            foreach (var ev in b.Events.Drain())
                if (ev is Ev.PlayerHit ph && ph.Amount > 0) hurt[ph.Source] = hurt.GetValueOrDefault(ph.Source) + ph.Amount;
            host.Pass(dt);
            j.BankArt(b);
            while (b.DraftOwed)
            {
                var offers = LevelUp.Draft(b, 3);
                if (offers.Count == 0) break;
                LevelUp.Choose(b, offers[0]);
            }
            low = Math.Min(low, p.Hp / b.MaxHp);
            t += dt;
            if (host.Announced.Any(an => an.Kicker == "Map complete")) break;
            if (host.Announced.Count(an => an.Title == "The altar is spent") > spent)
            {
                spent++;
                holding = null;
                phases.Add(t / 60);
            }
        }
        bool cleared = host.Announced.Any(an => an.Kicker == "Map complete");
        string note = !p.Alive ? $"killed by {p.LastKiller?.Def.Id ?? "?"} (lv {p.LastKiller?.Level}) with {b.Enemies.Living().Count(e => e.Target == -1)} on you, " +
            $"{string.Join("+", b.Weapons.Select(w => $"{w.Id}{w.Rank}"))}, hp max {b.MaxHp:0}, at {Dist(p.X, p.Z, map.Start.X, map.Start.Z):0} m from the start; hurt by " +
            string.Join(", ", hurt.OrderByDescending(h => h.Value).Take(4).Select(h => $"{h.Key} {h.Value:0}")) : "";
        return new Result(cleared, !p.Alive, t / 60, b.KillCount, b.EmberLevel, low, map.Packs.Count, phases.ToArray(), note);
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    [Theory]
    [InlineData(42, "warden", 1, "pack")]
    [InlineData(7, "stalker", 1, "dead")]
    [InlineData(99, "arcanist", 1, "kerchiefs")]
    [InlineData(1234, "reaver", 2, "lamplings")]
    public void A_map_played_through(int seed, string calling, int tier, string people)
    {
        if (Environment.GetEnvironmentVariable("MAP_PLAY") != "1") return;
        var r = Play(seed, calling, tier, people, [], Environment.GetEnvironmentVariable("MAP_TRACE") == "1" ? log : null);
        log.WriteLine($"seed {seed} {calling} tier {tier} {people}: {(r.Cleared ? "cleared" : r.Died ? "DIED" : "timed out")} in {r.Minutes:0.0} min, " +
            $"{r.Kills} kills, ember {r.Ember}, lowest health {r.LowHp:P0}, {r.Packs} packs, altars spent at [{string.Join(", ", r.Phases.Select(x => x.ToString("0.0")))}] min {r.Note}");
    }
}
