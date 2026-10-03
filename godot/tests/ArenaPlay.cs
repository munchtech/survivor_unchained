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
    /// <summary>One arena to play: who, against whom, how hard, and for how long
    /// (an hour unless the sweep cuts it short). Level is the survivor's
    /// character level, points spent on the calling's own attribute. A deft
    /// survivor also reads the fight as a player who has learned it does:
    /// off the line of a lunge (a dash through it if it is late), out from
    /// under a lobbed pot and off burning ground, and in on the throwers when
    /// nothing else presses.</summary>
    internal sealed record Case(int Seed, string Calling, int Tier, string People, string[] Oaths,
        int Level = 1, int Weapon = 0, int Ability = 0, double MaxMinutes = 60, bool Deft = false);

    /// <summary>A card taken: what, when, and of what kind.</summary>
    internal sealed record Pick(string Id, string Kind, double Minute);

    internal sealed record Result(double? WonAt, bool Died, double Minutes, int Kills, int Ember, int Cards, double LowHp, int[] EmberAt, string Build, string Note)
    {
        public string Killer = "", Weapon = "", Ability = "";
        public int KillerLevel;
        /// <summary>Lowest health before the win (or the death, if it never came).</summary>
        public double LowHpBefore = 1;
        public int[] AliveAt = [], KillsAt = [], LevelAt = [];
        public double[] HpAt = [];
        public List<Pick> Picks = new();
        public List<string> Greats = new();
        public List<string> Offered = new();
        public Dictionary<string, double> Hurt = new();
        /// <summary>The boss: how strong it came, how long it lasted, and how much was left of it if the survivor fell to it.</summary>
        public double BossMaxHp, BossSeconds, BossLeft = -1;
        public int Quaffs, Heralds;
    }

    static int Primary(string calling) => calling switch { "arcanist" => 2, "stalker" => 1, _ => 0 };

    internal static Result Play(int seed, string calling, int tier, string people, string[] oaths, ITestOutputHelper? trace = null) =>
        Play(new Case(seed, calling, tier, people, oaths), trace);

    internal static Result Play(Case c, ITestOutputHelper? trace = null)
    {
        var (seed, calling, tier, people, oaths) = (c.Seed, c.Calling, c.Tier, c.People, c.Oaths);
        var a = Callings.Archetype(calling);
        var j = global::SurvivorUnchained.Play.Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[Math.Min(c.Weapon, a.Weapons.Count - 1)], Ability = a.Abilities[Math.Min(c.Ability, a.Abilities.Count - 1)],
        }, (uint)seed);
        // A survivor further on: the levels, and the points put into the calling's own.
        while (j.Ch.Level < c.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        switch (Primary(calling)) { case 2: j.Ch.Attributes.Wits += j.Ch.Points; break; case 1: j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
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
        double t = 0, low = 1, lowBefore = 1, ang = 0, bossFrom = -1, bossMax = 0, bossLeft = -1;
        int cards = 0, quaffs = 0, heralds = 0;
        var emberAt = new List<int>();
        var aliveAt = new List<int>();
        var killsAt = new List<int>();
        var levelAt = new List<int>();
        var hpAt = new List<double>();
        var picks = new List<Pick>();
        var greats = new List<string>();
        var offered = new List<string>();
        var hurt = new Dictionary<string, double>();
        var p = b.Player;
        double? wonAt = null;
        string? lastBar = null;
        string bossName = MapOffers.People(people).BossName;
        while (t < c.MaxMinutes * 60 && p.Alive && host.ArenaResult == null)
        {
            // Give ground when pressed; otherwise go to the fight (or to the ember
            // lying about when it is quiet), and keep away from the arena's edge.
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
            Pickup? stone = null;
            double sd = 12;
            foreach (var k in b.Pickups.Living())
            {
                if (k.Kind != PickupKind.Ember) continue;
                double d = Dist(k.X, k.Z, p.X, p.Z);
                if (d < sd) { sd = d; stone = k; }
            }
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
            if (c.Deft) SurvivorUnchained.Balance.Pilot.Deft(b, press.Count >= 2 || stone != null, ref mx, ref mz);
            double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
            if (far > 60) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }
            if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) { (mx, mz) = (-mz, mx); }
            double ml = Math.Sqrt(mx * mx + mz * mz);
            if (ml > 1e-6) { mx /= ml; mz /= ml; }
            var crush = b.HostilesInRadius(p.X, p.Z, 2.2);
            if (crush.Count >= 3 && p.DashCharges > 0) b.Dash(mx, mz);
            if (b.HostilesInRadius(p.X, p.Z, 6).Count >= 5) b.UseAbility(mx, mz);
            if (p.Hp < b.MaxHp * 0.33) { double before = p.Hp; j.Quaff(b); if (p.Hp > before) quaffs++; }
            zone.Step(dt);
            zone.Frame(dt);
            b.Tick(dt, mx, mz);
            foreach (var ev in b.Events.Drain())
                if (ev is Ev.PlayerHit ph && ph.Amount > 0) hurt[ph.Source] = hurt.GetValueOrDefault(ph.Source) + ph.Amount;
            host.Pass(dt);
            j.BankArt(b);
            while (b.DraftOwed)
            {
                bool great = LevelUp.GreatNext(b);
                var offers = LevelUp.Draft(b, 3);
                if (offers.Count == 0) break;
                foreach (var o in offers) offered.Add(o.Kind == OfferKind.Evolve ? $"evolve:{o.Branch}" : o.Id);
                LevelUp.Choose(b, offers[0]);
                var o0 = offers[0];
                picks.Add(new Pick(o0.Kind == OfferKind.Evolve ? o0.Branch! : o0.Id,
                    great ? "great" : o0.Blessing ? "blessing" : o0.Kind.ToString().ToLowerInvariant(), t / 60));
                if (great) greats.Add(o0.Id);
                cards++;
            }
            low = Math.Min(low, p.Hp / b.MaxHp);
            if (wonAt == null) lowBefore = low;
            t += dt;
            // The boss's bar (a herald's says otherwise): when it came, how strong, what is left of it.
            if (host.Boss is { } bar && bar.Name == bossName && wonAt == null && t >= 30 * 60)
            {
                if (bossFrom < 0) { bossFrom = t; bossMax = bar.MaxHp; }
                bossLeft = bar.Hp / bar.MaxHp;
            }
            string? barName = host.Boss?.Name;
            if (lastBar != null && lastBar.StartsWith("Herald") && barName != lastBar) heralds++;
            lastBar = barName;
            if (wonAt == null && zone.Won) wonAt = t / 60;
            if ((int)(t / 60) != (int)((t - dt) / 60))
            {
                emberAt.Add(b.EmberLevel);
                aliveAt.Add(b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile));
                killsAt.Add(b.KillCount);
                levelAt.Add(zone.Debug()["level"] is int lv ? lv : 0);
                hpAt.Add(Math.Round(p.Hp / b.MaxHp, 3));
                trace?.WriteLine($"  {t / 60:0} min: ember {b.EmberLevel}, {b.Enemies.Living().Count()} alive, hp {p.Hp:0}/{b.MaxHp:0}, " +
                    $"{string.Join("+", b.Weapons.Select(w => $"{w.Id}{w.Rank}"))}");
            }
        }
        string build = string.Join(" ", b.Weapons.Select(w => $"{w.Evolution?.Id ?? w.Id}{w.Rank}")) + " | " + string.Join(" ", b.Boons.Select(kv => $"{kv.Key}{kv.Value}"));
        string bossNote = host.Boss is { } bb ? $"boss at {bb.Hp / bb.MaxHp:P0} of {bb.MaxHp:0}; " : "";
        string note = bossNote + (!p.Alive ? $"killed by {p.LastKiller?.Def.Id ?? "?"} (lv {p.LastKiller?.Level}); hurt most by " +
            string.Join(", ", hurt.OrderByDescending(h => h.Value).Take(4).Select(h => $"{h.Key} {h.Value:0}")) : "");
        return new Result(wonAt, !p.Alive, t / 60, b.KillCount, b.EmberLevel, cards, low, emberAt.ToArray(), build, note)
        {
            Killer = !p.Alive ? p.LastKiller?.Def.Id ?? "?" : "", KillerLevel = !p.Alive ? p.LastKiller?.Level ?? 0 : 0,
            Weapon = a.Weapons[Math.Min(c.Weapon, a.Weapons.Count - 1)], Ability = a.Abilities[Math.Min(c.Ability, a.Abilities.Count - 1)],
            LowHpBefore = lowBefore, AliveAt = aliveAt.ToArray(), KillsAt = killsAt.ToArray(), LevelAt = levelAt.ToArray(), HpAt = hpAt.ToArray(),
            Picks = picks, Greats = greats, Offered = offered, Hurt = hurt,
            BossMaxHp = bossMax, BossSeconds = bossFrom < 0 ? 0 : (wonAt is double w ? w * 60 : t) - bossFrom, BossLeft = wonAt != null ? 0 : bossLeft,
            Quaffs = quaffs, Heralds = heralds,
        };
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
