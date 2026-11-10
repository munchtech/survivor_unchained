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

    /// <summary>The clip's contact delay in game seconds for this press (its rate from the press record).</summary>
    static double Delay(WeaponDef d, string clip)
    {
        var r = d.Press!;
        bool heavy = clip == r.ClipHeavy && !(r.Clip?.Contains(clip) ?? false);
        double rate = heavy ? r.ClipHeavyRate ?? 1.5 : r.ClipRate ?? 1.6;
        return HerEvents.ContactFrame(clip)!.Value / HerEvents.Fps / rate;
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

    [Fact]
    public void A_campaign_press_strikes_on_its_clips_contact()
    {
        var b = Fight(true, ("sunder", 1), ("oathblade", 1));
        var e = Dummy(b, 2, 0);
        foreach (var id in new[] { "oathblade", "sunder" })
        {
            var w = b.Weapons.First(x => x.Id == id);
            var (clip, after) = PressAndLand(b, w, e);
            Assert.Contains(clip, w.Def.Press!.Clip!);
            double d = Delay(w.Def, clip);
            Assert.True(d > Dt, $"{id}: a contact of {d:0.000} s");
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
        w.OwnBlows = every - 1;   // the next is its own heavy
        var (clip, after) = PressAndLand(b, w, e);
        Assert.Equal(w.Def.Press!.ClipHeavy, clip);
        double d = HerEvents.ContactFrame(clip)!.Value / HerEvents.Fps / (w.Def.Press.ClipHeavyRate ?? 1.5);
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
    /// <summary>her_events.json "side" (HerEvents.Side): which way each clip's blade crosses, as measured in play
    /// (Ev.Slash.Side's contract: -1 toward the lesser sim angle, +1 toward the greater); null where none is written.</summary>
    [Fact]
    public void The_sword_clips_name_their_sides_and_a_clip_without_one_names_none()
    {
        Assert.Equal(1, HerEvents.Side("sword_back"));
        Assert.Equal(-1, HerEvents.Side("sword_fore"));
        Assert.Equal(-1, HerEvents.Side("sword_heavy"));
        Assert.Null(HerEvents.Side("no_such_clip"));
        Assert.Null(HerEvents.Side(""));
    }
}
