using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Tests;

// Feel probe (docs/feel/AUDIT.md §9): the ArenaPlay bot (godot/tests/ArenaPlay.cs),
// counting per minute what feel depends on. Columns: ember level, levels and cards
// taken this minute, hostiles alive, kills, ordinary (non-elite) kills, mean direct
// blows per ordinary kill, % of those killed by one blow, % of kills that burst
// the body, direct hits/s, crit %, DoT ticks, ember stones/s; then peaks in any
// one second: hits, kills, stones, and projectiles alive.
static class Probe
{
    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    static void Main(string[] args)
    {
        var cases = new (int, string, int, string)[] { (42, "warden", 1, "pack"), (7, "stalker", 1, "dead"), (99, "arcanist", 1, "kerchiefs"), (1234, "reaver", 1, "lamplings") };
        double limit = args.Length > 0 ? double.Parse(args[0]) : 36;
        foreach (var c in cases) Run(c.Item1, c.Item2, c.Item3, c.Item4, limit);
    }

    static void Run(int seed, string calling, int tier, string people, double limitMin)
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
        const double dt = 1 / 60.0;
        double t = 0, ang = 0;
        var p = b.Player;
        var hitsOn = new Dictionary<int, int>();
        var eliteIds = new HashSet<int>();
        // per-minute accumulators
        int mHits = 0, mCrits = 0, mDot = 0, mKills = 0, mPick = 0, mCards = 0, mBurst = 0, mLevels = 0, mOrdKills = 0, mOneHit = 0;
        double mHtk = 0; int peakHits1s = 0, peakKills1s = 0, peakPick1s = 0, peakProj = 0;
        var sHits = new Queue<double>(); var sKills = new Queue<double>(); var sPick = new Queue<double>();
        double? wonAt = null;
        Console.WriteLine($"=== seed {seed} {calling} tier {tier} {people}");
        Console.WriteLine("min ember lv+ cards alive kills  ordKills meanHTK oneHit% burst% hits/s crit% dotHits pick/s | peak1s hits kills picks proj");
        while (t < limitMin * 60 && p.Alive)
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
            {
                switch (ev)
                {
                    case Ev.Spawn s: hitsOn[s.Enemy] = 0; break;
                    case Ev.Hit h:
                        if (!h.Dot) hitsOn[h.Target] = hitsOn.GetValueOrDefault(h.Target) + 1;
                        if (h.Dot) mDot++; else { mHits++; sHits.Enqueue(t); if (h.Crit) mCrits++; }
                        break;
                    case Ev.Kill k when k.ByPlayer:
                        mKills++; sKills.Enqueue(t);
                        if (k.Burst) mBurst++;
                        if (!k.Elite && !k.Boss) { int n = hitsOn.GetValueOrDefault(k.Enemy); mOrdKills++; mHtk += n; if (n <= 1) mOneHit++; }
                        hitsOn.Remove(k.Enemy);
                        break;
                    case Ev.Pickup pk when pk.Kind == PickupKind.Ember: mPick++; sPick.Enqueue(t); break;
                    case Ev.LevelUp: mLevels++; break;
                }
            }
            while (sHits.Count > 0 && sHits.Peek() < t - 1) sHits.Dequeue();
            while (sKills.Count > 0 && sKills.Peek() < t - 1) sKills.Dequeue();
            while (sPick.Count > 0 && sPick.Peek() < t - 1) sPick.Dequeue();
            peakHits1s = Math.Max(peakHits1s, sHits.Count); peakKills1s = Math.Max(peakKills1s, sKills.Count); peakPick1s = Math.Max(peakPick1s, sPick.Count);
            peakProj = Math.Max(peakProj, b.Projectiles.Living().Count());
            host.Pass(dt);
            j.BankArt(b);
            while (b.DraftOwed)
            {
                var offers = LevelUp.Draft(b, 3);
                if (offers.Count == 0) break;
                LevelUp.Choose(b, offers[0]);
                mCards++;
            }
            t += dt;
            if (wonAt == null && zone.Won) wonAt = t / 60;
            if ((int)(t / 60) != (int)((t - dt) / 60))
            {
                int alive = b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying);
                Console.WriteLine($"{(int)(t / 60),3} {b.EmberLevel,5} {mLevels,3} {mCards,5} {alive,5} {mKills,6} {mOrdKills,8} {(mOrdKills > 0 ? mHtk / mOrdKills : 0),7:0.0} {(mOrdKills > 0 ? 100.0 * mOneHit / mOrdKills : 0),6:0} {(mKills > 0 ? 100.0 * mBurst / mKills : 0),6:0} {mHits / 60.0,6:0.0} {(mHits > 0 ? 100.0 * mCrits / mHits : 0),5:0} {mDot,7} {mPick / 60.0,6:0.0} | {peakHits1s,10} {peakKills1s,5} {peakPick1s,5} {peakProj,4}");
                mHits = mCrits = mDot = mKills = mPick = mCards = mBurst = mLevels = mOrdKills = mOneHit = 0; mHtk = 0;
                peakHits1s = peakKills1s = peakPick1s = peakProj = 0;
            }
        }
        string build = string.Join(" ", b.Weapons.Select(w => $"{w.Evolution?.Id ?? w.Id}{w.Rank}")) + " | " + string.Join(" ", b.Boons.Select(kv => $"{kv.Key}{kv.Value}"));
        Console.WriteLine($"won at {(wonAt is double w ? w.ToString("0.0") : "-")} min; {(p.Alive ? "alive" : "fell")} at {t / 60:0.0}; kills {b.KillCount}; build {build}");
    }
}
