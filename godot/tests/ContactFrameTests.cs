using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her blows land on the clip's contact frame (M3, ONE_BUILD 5.14; Sim/Contact.cs): a campaign press of a Slash
/// or a Crack strikes `contact` frames of its clip (data/anim/her_events.json, at 60 fps, over the clip's rate) after
/// the press, the heavy on its heavy clip's; the arena's auto swings still strike as they fire.</summary>
public sealed class ContactFrameTests
{
    const double Dt = 1 / 60.0;

    static Battle Fight(bool campaign, params (string Id, int Rank)[] skills)
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = campaign, Stats = BattleTests.BaseStats(),
            Weapons = skills.ToList(), Ability = AbilityKind.ShieldBash,
        });
        if (campaign) b.Calling = "warden";
        foreach (var w in b.Weapons) w.Timer = 0;
        return b;
    }

    static Enemy Dummy(Battle b, double x, double z)
    {
        var e = b.SpawnEnemy("footpad", x, z)!;
        e.Hp = e.MaxHp = 1e7;
        e.AttackT = e.RangedT = 999;
        b.Spatial.Clear();
        foreach (var o in b.Enemies.Items) if (o.Alive && o.State != EnemyState.Dying) b.Spatial.Insert(o.Id, o.X, o.Z);
        return e;
    }

    /// <summary>The clip's contact delay in game seconds for this press. An unchained record: the clip's contact over its
    /// rate from the press record (clipRate, clipHeavyRate). A chained record (press `chain`; Sim/SwingChain.cs): the cut's
    /// contact beat less its start, from the chain's own beats: the clip fills the cut's period (the skill's wait,
    /// Firing.CooldownOf; a heavy on its heavy clip a period longer by its clip's length over the cut's), so the rate is
    /// the clip's length over the period and the blow lands contact / rate after the cut starts.</summary>
    static double Delay(Battle b, WeaponInst w, string clip)
    {
        var r = w.Press!;
        bool heavy = clip == r.ClipHeavy && !(r.Clip?.Contains(clip) ?? false);
        if (r.Chain == null)
        {
            double rate = heavy ? r.ClipHeavyRate ?? 1.5 : r.ClipRate ?? 1.6;
            return HerEvents.ContactFrame(clip)!.Value / HerEvents.Fps / rate;
        }
        var beats = HerEvents.ChainBeats(clip, heavy);
        double scale = heavy && r.Clip is { Length: > 0 } cs ? beats.Len / HerEvents.ChainBeats(cs[0], false).Len : 1;
        return beats.Contact / (beats.Len / (Firing.CooldownOf(b, w) * scale));
    }

    /// <summary>Press the skill at the dummy and step until its first hit: (the clip she swung, seconds from the press to the hit).</summary>
    static (string Clip, double After) PressAndLand(Battle b, WeaponInst w, Enemy e)
    {
        b.Events.Drain();
        double t0 = b.Time;
        Assert.True(b.PressSkill(w.Slot, e.X, e.Z));
        var a = b.Player.AttackAnim;
        Assert.NotNull(a);
        Assert.NotNull(a!.Clip);
        Assert.Equal(t0, a.T, 9);
        Assert.Empty(b.Events.Drain().OfType<Ev.Hit>());
        for (int i = 0; i < 120; i++)
        {
            e.X = 2; e.Z = 0; e.Vx = e.Vz = 0;
            b.Tick(Dt, 0, 0);
            if (b.Events.Drain().OfType<Ev.Hit>().Any()) return (a.Clip!, b.Time - t0);
        }
        throw new Exception("the blow never landed");
    }

    /// <summary>(sw2) Both contracts on the same two records: as shipped (chained since the switch: the blow lands on the
    /// chain's contact beat) and with the chain stripped off the weapon's own copy (`WithChain(null)`: the old contract,
    /// the clip's contact over the press record's clip rate). The expected delay is worked from the record each time, with
    /// one step of slack: the blow lands on the first step at or after its beat.</summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void A_campaign_press_strikes_on_its_clips_contact(bool shipped)
    {
        var b = Fight(true, ("sunder", 1), ("oathblade", 1));
        var e = Dummy(b, 2, 0);
        foreach (var id in new[] { "oathblade", "sunder" })
        {
            var w = b.Weapons.First(x => x.Id == id);
            // (the switch: the shipped record carries a chain; the old contract is tested on the same record without it)
            Assert.NotNull(w.Press!.Chain);
            if (!shipped) w.Press = w.Press.WithChain(null);
            Assert.Equal(shipped, w.Chained);
            var (clip, after) = PressAndLand(b, w, e);
            Assert.Contains(clip, w.Press!.Clip!);
            double d = Delay(b, w, clip);
            Assert.True(d > Dt, $"{id}: a contact of {d:0.000} s");
            // (a chained cut: the chain's own clock says the same beat)
            if (shipped) Assert.Equal(d, w.Chain!.ContactAt - w.Chain.StartAt, 9);
            else Assert.Null(w.Chain);
            Assert.InRange(after, d - 1e-9, d + Dt + 1e-9);
            Assert.Equal(0, b.PendingBlows);
            // (ready again for the next)
            for (int i = 0; i < 200 && w.Timer > 0; i++) b.Tick(Dt, 0, 0);
        }
    }

    [Fact]
    public void A_heavy_strikes_on_its_heavy_clips_frame()
    {
        var b = Fight(true, ("oathblade", 1), ("sunder", 1));
        var e = Dummy(b, 2, 0);
        var w = b.Weapons.First(x => x.Id == "sunder");
        int every = Firing.HeavyEveryOf(b, w);
        Assert.True(every > 0);
        // the next is its own heavy. (sw1) Sunder is chained: a cut counts its share of a blow (0.70 / 1.6 = 0.4375), so
        // the count stands one cut short of the every-th blow, not one blow short.
        (w.OwnBlows, w.OwnPart) = (every - 1, 1 - w.BlowWeight);
        Assert.Equal(0.70 / 1.6, w.BlowWeight, 12);
        var (clip, after) = PressAndLand(b, w, e);
        Assert.Equal(w.Def.Press!.ClipHeavy, clip);
        // (sw2) a chained record's heavy lands on the chain's beat too: the same reading as the press above
        double d = Delay(b, w, clip);
        Assert.Equal(d, w.Chain!.ContactAt - w.Chain.StartAt, 9);
        Assert.InRange(after, d - 1e-9, d + Dt + 1e-9);
        Assert.True(w.WasOwnHeavy);
        Assert.Equal(every, w.OwnBlows);
        // The oathblade's light swings alternate their clips, swing to swing.
        var o = b.Weapons.First(x => x.Id == "oathblade");
        var seen = new System.Collections.Generic.HashSet<string>();
        for (int k = 0; k < 2; k++)
        {
            for (int i = 0; i < 200 && (o.Timer > 0 || b.PendingBlows > 0); i++) b.Tick(Dt, 0, 0);
            seen.Add(PressAndLand(b, o, e).Clip);
        }
        Assert.Equal(2, seen.Count);
    }

    [Fact]
    public void A_blow_pending_when_she_is_knocked_down_is_dropped()
    {
        var b = Fight(true, ("sunder", 1));
        var e = Dummy(b, 2, 0);
        var w = b.Weapons.First(x => x.Id == "sunder");
        Assert.True(b.PressSkill(w.Slot, e.X, e.Z));
        Assert.Equal(1, b.PendingBlows);
        b.KnockPlayer(0.6);
        Assert.Equal(0, b.PendingBlows);
        b.Events.Drain();
        for (int i = 0; i < 30; i++) b.Tick(Dt, 0, 0);
        Assert.Empty(b.Events.Drain().OfType<Ev.Hit>());
        Assert.Equal(0, w.Swing);
    }

    [Fact]
    public void The_arenas_auto_sunder_strikes_as_it_fires()
    {
        var b = Fight(false, ("sunder", 1));
        Dummy(b, 2, 0);
        for (int i = 0; i < 240; i++)
        {
            b.Tick(Dt, 0, 0);
            Assert.Equal(0, b.PendingBlows);
            if (b.Events.Drain().OfType<Ev.Hit>().Any())
            {
                Assert.NotNull(b.Player.AttackAnim);
                Assert.Equal(b.Time, b.Player.AttackAnim!.T, 9);
                Assert.Null(b.Player.AttackAnim.Clip);
                return;
            }
        }
        throw new Exception("the arena's sunder never struck");
    }

    [Fact]
    public void Her_events_parse_and_every_skill_clip_has_a_contact()
    {
        HerEvents.Reload();
        Assert.Equal(60, HerEvents.Fps);
        int named = 0;
        foreach (var d in SurvivorUnchained.Content.Weapons.All.Values)
        {
            if (d.Press is not { } r) continue;
            foreach (var c in (r.Clip ?? []).Append(r.ClipHeavy).OfType<string>())
            {
                named++;
                Assert.True(HerEvents.ContactFrame(c) is > 0, $"{d.Id}: clip {c} has no contact in her_events.json");
            }
        }
        Assert.True(named >= 8, "the warden's blows name their clips");
    }
}
