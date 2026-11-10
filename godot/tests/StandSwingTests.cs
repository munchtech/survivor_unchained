using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 lead 5) The story stand clock knows a fighter's plant (PackKit.Stand, Teeth.Director.StandSwing): a cut of
/// her held swing that lands on a foe holds the clock off for its own length, up to StandSwing s at one spot; a step of
/// StandMoved gives the allowance back; a swing at the air earns nothing; with StandSwing 0 the clock is what it was.
/// The route: a campaign Battle stepped here with its own `new PackKit(b)` (as Encounters.Standing and MapRun call
/// `Stand(dt, held, awake)`), no zone; the clock's numbers are set here (tier I's row of 9 Nov), not read from the data.</summary>
public sealed class StandSwingTests
{
    const double Dt = 1 / 60.0;
    const double StandFor = 1.0, StandMoved = 0.6, Swing = 2.4;
    /// <summary>One clock sample (PackKit samples her trail each quarter second) and a step of slack.</summary>
    const double Sample = 0.3;

    /// <summary>A campaign fight under the stand clock: the warden with her held swing (Sunder) ready, a foe pinned in
    /// her reach (what her cuts land on) and one pinned past StandFrom (the clock's charger), both the woken pack.</summary>
    sealed class Fight
    {
        public readonly Battle B;
        public readonly PackKit Kit;
        public readonly WeaponInst W;
        public readonly Enemy Near, Far;
        readonly HashSet<Enemy> pack;
        /// <summary>When the clock first charged her, when her first cut landed, the longest the clock counted before its
        /// first charge.</summary>
        public double? ChargedAt, LandedAt;
        public double Counted;

        public Fight(double standSwing)
        {
            B = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [("sunder", 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Calling = "warden";
            W = B.Weapons.Single();
            W.Timer = 0;
            B.StoryStand = new Teeth.Director
            {
                Stand = true, StandMoved = StandMoved, StandFor = StandFor, StandNear = 16, StandScale = 2.2, StandPair = 1,
                StandFrom = 7, StandCooldown = 1.0, StandDamage = 1.4, StandSwing = standSwing,
            };
            Kit = new PackKit(B);
            Near = Foe(2, 0);
            Far = Foe(9, 0);
            pack = [Near, Far];
            Pin();
        }

        Enemy Foe(double x, double z)
        {
            var e = B.SpawnEnemy("footpad", x, z)!;
            e.Hp = e.MaxHp = 1e7;
            e.AttackT = e.RangedT = 999;
            return e;
        }

        /// <summary>The foes where they were put (the swing's knockback and their own feet aside).</summary>
        void Pin()
        {
            (Near.X, Near.Z, Near.Vx, Near.Vz) = (2, 0, 0, 0);
            (Far.X, Far.Z, Far.Vx, Far.Vz) = (9, 0, 0, 0);
            B.Spatial.Clear();
            foreach (var e in B.Enemies.Items) if (e.Alive && e.State != EnemyState.Dying) B.Spatial.Insert(e.Id, e.X, e.Z);
        }

        /// <summary>Seconds of the fight: her swing held at (aimX, 0) or let go, her feet as (mx, mz); the clock stepped
        /// after the battle, as the zones step it. Stops at the first charge when asked.</summary>
        public void Run(double seconds, double? aimX, double mx = 0, double mz = 0, bool untilCharged = false)
        {
            for (double t = 0; t < seconds - 1e-9; t += Dt)
            {
                Pin();
                if (aimX is { } ax) B.HoldSkill(W.Slot, true, B.Player.X + ax, B.Player.Z); else B.HoldSkill(W.Slot, false);
                B.Tick(Dt, mx, mz);
                B.Events.Drain();
                B.Player.Hp = B.MaxHp;
                Kit.Stand(Dt, null, () => pack);
                if (LandedAt == null && B.SwingLanded > 0) LandedAt = B.Time;
                if (ChargedAt == null && Kit.StandCharges > 0) ChargedAt = B.Time;
                if (ChargedAt == null) Counted = Math.Max(Counted, B.StoodFor);
                if (untilCharged && ChargedAt != null) return;
            }
        }
    }

    /// <summary>When the old clock (StandSwing 0) charges a stander who never swings: the yardstick for the rest.</summary>
    static double OldClockCharge()
    {
        var f = new Fight(0);
        f.Run(4, null, untilCharged: true);
        Assert.True(f.ChargedAt != null, "the old clock never charged a stander in 4 s");
        return f.ChargedAt!.Value;
    }

    [Fact]
    public void With_no_swing_allowance_a_stander_is_charged_once_she_has_stood_the_clocks_time()
    {
        var f = new Fight(0);
        Assert.True(f.B.Campaign);
        f.Run(StandFor - 2 * Dt, null);
        Assert.Equal(0, f.Kit.StandCharges);
        f.Run(3, null, untilCharged: true);
        Assert.Equal(1, f.Kit.StandCharges);
        Assert.InRange(f.ChargedAt!.Value, StandFor, StandFor + Sample);
        // Swinging changes nothing for the old clock: her cuts land and it charges her at the same time.
        var s = new Fight(0);
        s.Run(4, 2, untilCharged: true);
        Assert.True(s.B.SwingLanded > 0, "her swing never landed");
        Assert.Equal(f.ChargedAt!.Value, s.ChargedAt!.Value, 9);
    }

    [Fact]
    public void With_the_allowance_a_stander_who_lands_nothing_is_charged_when_she_was_before()
    {
        double old = OldClockCharge();
        // Her feet still, her swing never held.
        var idle = new Fight(Swing);
        idle.Run(4, null, untilCharged: true);
        Assert.True(idle.ChargedAt != null, "never charged");
        Assert.InRange(idle.ChargedAt!.Value, old - Sample, old + Sample);
        // Her swing held at the air behind her: cuts made, none landed, nothing earned.
        var air = new Fight(Swing);
        air.Run(4, -2, untilCharged: true);
        Assert.True(air.W.Casts > 0, "she never swung");
        Assert.Equal(0, air.B.SwingLanded);
        Assert.True(air.ChargedAt != null, "never charged");
        Assert.InRange(air.ChargedAt!.Value, old - Sample, old + Sample);
    }

    [Fact]
    public void Landed_cuts_hold_the_clock_off_for_the_allowance_and_no_longer()
    {
        var f = new Fight(Swing);
        f.Run(Swing + StandFor + 3, 2, untilCharged: true);
        Assert.True(f.LandedAt != null, "her swing never landed");
        Assert.True(f.LandedAt < 0.3, $"her first cut landed at {f.LandedAt:0.00} s");
        // The cap holds: standing and swinging on, the charge comes once the allowance is spent and she has stood StandFor.
        Assert.True(f.ChargedAt != null, $"no charge in {f.B.Time:0.0} s of standing and swinging (the allowance has no end)");
        double due = f.LandedAt!.Value + Swing + StandFor;
        Assert.True(f.ChargedAt >= f.LandedAt + Swing, $"charged at {f.ChargedAt:0.00} s, inside the first {Swing} s of landed cuts (first at {f.LandedAt:0.00})");
        Assert.InRange(f.ChargedAt!.Value, due - Sample, due + 2 * Sample);
        // Inside the allowance the clock has not counted a stand.
        var g = new Fight(Swing);
        g.Run(0.3, 2);
        g.Run(g.LandedAt!.Value + Swing - g.B.Time, 2);
        Assert.Equal(0, g.Kit.StandCharges);
        Assert.True(g.Counted < StandFor, $"the clock counted {g.Counted:0.00} s of standing while her cuts landed");
    }

    [Fact]
    public void A_step_gives_the_allowance_back()
    {
        var f = new Fight(Swing);
        // Most of the allowance spent at the first spot.
        f.Run(2.0, 2);
        Assert.Equal(0, f.Kit.StandCharges);
        // One step aside (the foe still in her reach), then planted again.
        double z0 = f.B.Player.Z;
        while (Math.Abs(f.B.Player.Z - z0) < StandMoved + 0.1) f.Run(Dt, 2, 0, 1);
        double stepped = f.B.Time, landed0 = f.B.SwingLanded;
        Assert.True(stepped < 2.5, $"the step took until {stepped:0.00} s");
        // Her cuts land on as they did: no charge for another allowance, then one (it is one allowance, not more).
        double? next = null;
        while (f.B.Time < stepped + 8 && f.ChargedAt == null)
        {
            f.Run(Dt, 2);
            if (next == null && f.B.SwingLanded > landed0) next = f.B.Time;
        }
        // The same fight with no step: charged when the first spot's allowance and StandFor are over.
        var still = new Fight(Swing);
        still.Run(12, 2, untilCharged: true);
        string saw = $"stepped at {stepped:0.00} s, her next cut landed at {(next == null ? "never" : $"{next:0.00} s")}, charged at {(f.ChargedAt == null ? "never" : $"{f.ChargedAt:0.00} s")} "
            + $"(the clock had counted {f.Counted:0.00} s; her swing's wait {Firing.CooldownOf(f.B, f.W):0.00} s); with no step, charged at {still.ChargedAt:0.00} s";
        Assert.True(f.ChargedAt != null, "no charge in 8 s after the step (the allowance has no end): " + saw);
        Assert.True(f.ChargedAt >= stepped + Swing, $"charged inside {Swing} s of her step with her cuts landing: " + saw);
        Assert.True(f.ChargedAt <= stepped + Firing.CooldownOf(f.B, f.W) + Swing + StandFor + 2 * Sample, "the allowance after a step is more than one: " + saw);
        Assert.True(f.ChargedAt > still.ChargedAt + 1.5, "the step bought her nothing: " + saw);
    }

    [Fact]
    public void Only_a_held_cut_that_struck_a_foe_counts_and_by_its_own_wait()
    {
        var f = new Fight(0);
        // At the air: cuts, nothing landed.
        f.Run(2, -2);
        Assert.True(f.W.Casts >= 1, "she never swung");
        Assert.Equal(0, f.B.SwingLanded);
        // At the foe: each cut that strikes adds its wait.
        f.B.HoldSkill(f.W.Slot, false);
        f.W.Timer = 0;
        int casts0 = f.W.Casts;
        double wait = Firing.CooldownOf(f.B, f.W), was = 0;
        Assert.True(wait > 0.08);
        for (int i = 0; i < 400 && f.W.Casts < casts0 + 3; i++)
        {
            f.Run(Dt, 2);
            // (never between cuts)
            if (f.W.Casts == casts0 + (int)Math.Round(was / wait)) Assert.Equal(was, f.B.SwingLanded, 9);
            was = f.B.SwingLanded;
        }
        Assert.Equal(casts0 + 3, f.W.Casts);
        Assert.Equal(3 * wait, f.B.SwingLanded, 9);
        // Let go: nothing more.
        f.Run(wait + 0.2, null);
        Assert.Equal(3 * wait, f.B.SwingLanded, 9);
        // The arena's fights never count it (the same skill firing itself at the same foe).
        var a = BattleTests.Arena(5, ("sunder", 1));
        Assert.False(a.Campaign);
        var e = a.SpawnEnemy("footpad", 2, 0)!;
        e.Hp = e.MaxHp = 1e7;
        for (int i = 0; i < 240; i++) { e.X = a.Player.X + 2; e.Z = a.Player.Z; a.Tick(Dt, 0, 0); a.Events.Drain(); a.Player.Hp = a.MaxHp; }
        Assert.True(e.Hp < e.MaxHp, "the arena's swing never struck");
        Assert.Equal(0, a.SwingLanded);
    }
}
