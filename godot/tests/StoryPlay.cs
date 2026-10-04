using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>
/// The Verge walked by day without a screen, by a plain-minded survivor with
/// nothing but what they carry (the ember sleeps by day): from the gate to
/// each of the wood's packs in turn (not the quest camps), fighting what
/// wakes, backing off when pressed, drinking when low. It reports what it put down, what it learned
/// (character experience, levels), whether it fell and to what (for tuning
/// the wood's packs against a survivor fresh from the prologue).
/// Only with STORY_PLAY=1: dotnet test --filter StoryPlay.
/// </summary>
public class StoryPlay(ITestOutputHelper log)
{
    internal sealed record Result(bool Died, double Minutes, int Kills, int Levels, double Xp, double LowHp, int Places, string Note)
    {
        public string Killer = "";
        public int KillerLevel, Packs, Quaffs;
        public Dictionary<string, double> Hurt = new();
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    internal static Result Walk(int seed, string calling, int level, int day, ITestOutputHelper? trace = null)
    {
        var a = Callings.Archetype(calling);
        var j = global::SurvivorUnchained.Play.Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        j.World.Facts["prologue.done"] = true;
        j.World.Day = day;
        // Where the prologue leaves a survivor: a level or two, points spent on the calling's own.
        while (j.Ch.Level < level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        switch (calling) { case "arcanist": j.Ch.Attributes.Wits += j.Ch.Points; break; case "stalker": j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
        var meta = ZoneMeta.Load("verge");
        var host = new FakeHost(j, meta);
        var zone = new Verge(host, meta);
        var ground = Heightfield.Load(meta);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed);
        var kill = zone.Hooks.OnKill;
        b.Hooks = zone.Hooks;
        b.Hooks.OnKill = (e, by) => { kill?.Invoke(e, by); j.Killed(e, by); };
        host.Battle = b;
        zone.Begin(b);

        // The packs laid out in the wood (not the quest camps: those have their own ways in).
        var camps = new[] { "roost", "dig", "hollow" }.Select(c => meta.Place("V", c)).ToList();
        var route = b.Enemies.Living().Where(e => e.Wake > 0).Select(e => (X: e.HomeX, Z: e.HomeZ)).Distinct()
            .Where(h => camps.All(c => Dist(c.X, c.Z, h.X, h.Z) > 30)).ToList();
        int packs = route.Count;
        // Nearest first, then the nearest to that, and home.
        var order = new List<(double X, double Z)>();
        (double X, double Z) from = (b.Player.X, b.Player.Z);
        while (route.Count > 0) { var n = route.OrderBy(h => Dist(h.X, h.Z, from.X, from.Z)).First(); order.Add(n); route.Remove(n); from = n; }
        var entry = meta.Place("V", "entry");
        order.Add((entry.X + 4, entry.Z));
        var flow = new FlowField(b.Collision, 150);
        const double dt = 1 / 60.0;
        double t = 0, low = 1, xp0 = j.Ch.Xp, since = 0;
        int level0 = j.Ch.Level, k = 0, quaffs = 0;
        var hurt = new Dictionary<string, double>();
        var p = b.Player;
        while (t < 30 * 60 && p.Alive && k < order.Count)
        {
            var goal = order[k];
            // There, or given up on (a pack it cannot reach in a minute and a half).
            if (Dist(goal.X, goal.Z, p.X, p.Z) < 7 || t - since > 90) { k++; since = t; continue; }
            var awake = b.Enemies.Living().Where(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && (e.Wake <= 0 || e.Roused) && Dist(e.X, e.Z, p.X, p.Z) < 16).ToList();
            var press = b.HostilesInRadius(p.X, p.Z, 3.2);
            double mx, mz;
            if (press.Count >= 2)
            {
                double cx = press.Average(e => e.X) - p.X, cz = press.Average(e => e.Z) - p.Z;
                double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
                mx = -cx / cl * 0.7 - cz / cl * 0.7; mz = -cz / cl * 0.7 + cx / cl * 0.7;
            }
            else if (awake.Count > 0)
            {
                // Stand and fight: the throwers first (close on them), else circle the nearest at a blade's reach.
                var n = awake.Where(e => e.Def.Ranged != null).OrderBy(e => Dist(e.X, e.Z, p.X, p.Z)).FirstOrDefault()
                    ?? awake.OrderBy(e => Dist(e.X, e.Z, p.X, p.Z)).First();
                double d = Dist(n.X, n.Z, p.X, p.Z);
                double reach = n.Def.Ranged != null ? 1.8 : 3.5;
                if (d > reach) { mx = n.X - p.X; mz = n.Z - p.Z; }
                else { mx = -(n.Z - p.Z); mz = n.X - p.X; }
            }
            else
            {
                flow.Update(goal.X, goal.Z);
                mx = goal.X - p.X; mz = goal.Z - p.Z;
                if (flow.Dir(p.X, p.Z, out var fx, out var fz)) { mx = fx; mz = fz; }
            }
            if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) (mx, mz) = (-mz, mx);
            double ml = Math.Sqrt(mx * mx + mz * mz);
            if (ml > 1e-6) { mx /= ml; mz /= ml; }
            if (b.HostilesInRadius(p.X, p.Z, 2.2).Count >= 3 && p.DashCharges > 0) b.Dash(mx, mz);
            if (b.HostilesInRadius(p.X, p.Z, 6).Count >= 3) b.UseAbility(mx, mz);
            if (p.Hp < b.MaxHp * 0.35) { double before = p.Hp; j.Quaff(b); if (p.Hp > before) quaffs++; }
            zone.Step(dt);
            zone.Frame(dt);
            b.Tick(dt, mx, mz);
            foreach (var ev in b.Events.Drain())
                if (ev is Ev.PlayerHit ph && ph.Amount > 0) hurt[ph.Source] = hurt.GetValueOrDefault(ph.Source) + ph.Amount;
            host.Pass(dt);
            j.BankArt(b);
            low = Math.Min(low, p.Hp / b.MaxHp);
            t += dt;
            if (trace != null && (int)(t / 20) != (int)((t - dt) / 20))
                trace.WriteLine($"  {t:0}s to {k} at {p.X:0},{p.Z:0} hp {p.Hp:0}/{b.MaxHp:0} lv {j.Ch.Level} kills {b.KillCount} awake {awake.Count}");
        }
        string note = !p.Alive ? $"killed by {p.LastKiller?.Def.Id ?? "?"} (lv {p.LastKiller?.Level}) at pack {k} of {packs}; hurt by " +
            string.Join(", ", hurt.OrderByDescending(h => h.Value).Take(4).Select(h => $"{h.Key} {h.Value:0}")) : "";
        return new Result(!p.Alive, t / 60, b.KillCount, j.Ch.Level - level0, Enumerable.Range(level0, j.Ch.Level - level0).Sum(l => Character.XpForLevel(l)) + j.Ch.Xp - xp0, low, Math.Min(k, packs), $"of {packs} packs; " + note)
        {
            Killer = !p.Alive ? p.LastKiller?.Def.Id ?? "?" : "", KillerLevel = !p.Alive ? p.LastKiller?.Level ?? 0 : 0, Packs = packs, Quaffs = quaffs, Hurt = hurt,
        };
    }

    [Theory]
    [InlineData(42, "warden", 2, 1)]
    [InlineData(7, "stalker", 2, 1)]
    [InlineData(99, "arcanist", 3, 2)]
    [InlineData(1234, "reaver", 4, 3)]
    public void The_verge_walked_by_day(int seed, string calling, int level, int day)
    {
        if (Environment.GetEnvironmentVariable("STORY_PLAY") != "1") return;
        var r = Walk(seed, calling, level, day, Environment.GetEnvironmentVariable("STORY_TRACE") == "1" ? log : null);
        log.WriteLine($"seed {seed} {calling} level {level} day {day}: {(r.Died ? "FELL" : "came back")} after {r.Minutes:0.0} min,  {r.Places} packs " +
            $"{r.Kills} kills, +{r.Xp:0} xp (+{r.Levels} levels), lowest health {r.LowHp:P0} {r.Note}");
    }
}
