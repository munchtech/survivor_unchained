using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>
/// An ember arena played through without a screen, by a plain-minded
/// survivor: go to the fight and give ground when pressed, pick up the
/// ember, dash out of a crush, use the art on a crowd, drink when low, take
/// the first card offered. It stays past the win (the arena has no end) and
/// reports when it won, how long it lived, how often the cards came and what
/// killed it (for tuning the horde and the draft). It gives up at an hour.
/// Only with ARENA_PLAY=1 (it takes a while): dotnet test --filter ArenaPlay.
/// </summary>
public class ArenaPlay(ITestOutputHelper log)
{
    sealed record Result(double? WonAt, bool Died, double Minutes, int Kills, int Ember, int Cards, double LowHp, int[] EmberAt, string Build, string Note);

    static Result Play(int seed, string calling, int tier, string people, string[] oaths, ITestOutputHelper? trace = null)
    {
        var a = Callings.Archetype(calling);
        var j = global::SurvivorUnchained.Play.Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        var spec = new ArenaSpec { Id = "table:bot", Name = "The Test Arena", Seed = seed, Tier = tier, People = people, Oaths = oaths.ToList() };
        Arenas.Begin(j.World, spec);
        var map = MapGen.Generate(spec.Map);
        var host = new FakeHost(j, map.Meta, map.Ground);
        var zone = new global::SurvivorUnchained.Play.Zones.ArenaRun(host, map, spec);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed, arena: true);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);

        const double dt = 1 / 60.0;
        double t = 0, low = 1, ang = 0;
        int cards = 0;
        var emberAt = new List<int>();
        var hurt = new Dictionary<string, double>();
        var p = b.Player;
        double? wonAt = null;
        while (t < 60 * 60 && p.Alive && host.ArenaResult == null)
        {
            // Give ground when pressed; otherwise go to the fight (or to the ember
            // lying about when it is quiet), and keep away from the arena's edge.
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
                // Away and round: a quarter turn off straight back.
                mx = -cx / cl * 0.7 - cz / cl * 0.7; mz = -cz / cl * 0.7 + cx / cl * 0.7;
            }
            else if (stone != null && (nearest == null || Dist(nearest.X, nearest.Z, p.X, p.Z) > 5)) { mx = stone.X - p.X; mz = stone.Z - p.Z; }
            else if (nearest != null && Dist(nearest.X, nearest.Z, p.X, p.Z) > 6) { mx = nearest.X - p.X; mz = nearest.Z - p.Z; }
            else if (nearest != null) { ang += dt; mx = -(nearest.Z - p.Z); mz = nearest.X - p.X; }
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
                cards++;
            }
            low = Math.Min(low, p.Hp / b.MaxHp);
            t += dt;
            if (wonAt == null && zone.Won) wonAt = t / 60;
            if ((int)(t / 60) != (int)((t - dt) / 60))
            {
                emberAt.Add(b.EmberLevel);
                trace?.WriteLine($"  {t / 60:0} min: ember {b.EmberLevel}, {b.Enemies.Living().Count()} alive, hp {p.Hp:0}/{b.MaxHp:0}, " +
                    $"{string.Join("+", b.Weapons.Select(w => $"{w.Id}{w.Rank}"))}");
            }
        }
        string build = string.Join(" ", b.Weapons.Select(w => $"{w.Evolution?.Id ?? w.Id}{w.Rank}")) + " | " + string.Join(" ", b.Boons.Select(kv => $"{kv.Key}{kv.Value}"));
        string bossNote = host.Boss is { } bb ? $"boss at {bb.Hp / bb.MaxHp:P0} of {bb.MaxHp:0}; " : "";
        string note = bossNote + (!p.Alive ? $"killed by {p.LastKiller?.Def.Id ?? "?"} (lv {p.LastKiller?.Level}); hurt most by " +
            string.Join(", ", hurt.OrderByDescending(h => h.Value).Take(4).Select(h => $"{h.Key} {h.Value:0}")) : "");
        return new Result(wonAt, !p.Alive, t / 60, b.KillCount, b.EmberLevel, cards, low, emberAt.ToArray(), build, note);
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    [Theory]
    [InlineData(42, "warden", 1, "pack")]
    [InlineData(7, "stalker", 1, "dead")]
    [InlineData(99, "arcanist", 1, "kerchiefs")]
    [InlineData(1234, "reaver", 1, "lamplings")]
    [InlineData(5, "warden", 2, "pack")]
    public void An_arena_played_through(int seed, string calling, int tier, string people)
    {
        if (Environment.GetEnvironmentVariable("ARENA_PLAY") != "1") return;
        // ARENA_CASE=seed,calling,tier,people: that one instead (for tuning).
        if (Environment.GetEnvironmentVariable("ARENA_CASE") is string c)
        {
            if (seed != 42) return;
            var f = c.Split(',');
            (seed, calling, tier, people) = (int.Parse(f[0]), f[1], int.Parse(f[2]), f[3]);
        }
        var r = Play(seed, calling, tier, people, [], Environment.GetEnvironmentVariable("ARENA_TRACE") == "1" ? log : null);
        log.WriteLine($"seed {seed} {calling} tier {tier} {people}: {(r.WonAt is double w ? $"won at {w:0.0} min, " : "")}{(r.Died ? "fell" : "still standing")} at {r.Minutes:0.0} min, " +
            $"{r.Kills} kills, ember {r.Ember}, {r.Cards} cards ({r.Cards / Math.Max(1, r.Minutes):0.0}/min), lowest health {r.LowHp:P0}");
        log.WriteLine($"  ember by minute [{string.Join(" ", r.EmberAt)}]");
        log.WriteLine($"  {r.Build}");
        if (r.Note != "") log.WriteLine($"  {r.Note}");
    }
}
