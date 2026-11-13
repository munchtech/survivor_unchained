using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-keys) The second weapon set is a stance (data/content/stances.json; BUILD_DIRECTION.md round 8): it opens
/// at the taught build's level, flavors every one of her four keys and never turns one off; each stance has a price and
/// none is better than another on every count; a swap strike fires once per swap, each set's on its own cooldown.</summary>
public sealed class StanceTests
{
    const double Dt = 1.0 / 60;

    static void Tick(Battle b, double seconds)
    {
        for (double t = 0; t < seconds - 1e-9; t += Dt) { b.Tick(Dt, 0, 0); b.Events.Drain(); }
    }

    static Enemy Dummy(Battle b, double dx, double dz)
    {
        var e = b.SpawnEnemy("footpad", b.Player.X + dx, b.Player.Z + dz)!;
        e.Hp = e.MaxHp = 1e7;
        e.AttackT = 999;
        return e;
    }

    static Battle Fight(int level, string? stance = null)
    {
        var j = KeyBarTests.New(level);
        if (stance != null) { KeyBarTests.Fight(j); Assert.True(Rpg.SkillBook.SetStance(j.Ch, stance)); }
        return KeyBarTests.Fight(j);
    }

    [Fact]
    public void The_stance_opens_at_its_level()
    {
        var t = TaughtBuilds.Of("warden")!.Stance!;
        Assert.Equal(8, t.Level);
        Assert.Null(Fight(t.Level - 1).StanceB);
        var b = Fight(t.Level);
        Assert.Equal(t.Default, b.StanceB!.Id);
        Assert.False(b.OnB);
        Assert.All(t.Offers, id => Assert.NotNull(Stances.Find(id)));
        // Outside the campaign (the arena) there is no second set.
        Assert.False(BattleTests.Arena(3).Swap());
    }

    public static IEnumerable<object[]> Offered => TaughtBuilds.Of("warden")!.Stance!.Offers.Select(s => new object[] { s });

    [Theory]
    [MemberData(nameof(Offered))]
    public void Every_stance_flavors_all_four_keys_and_turns_none_off(string stance)
    {
        var b = Fight(12, stance);
        var keys = Enumerable.Range(0, Weapons.MaxKeys).Select(i => b.OnSlot(i)!).ToList();
        Assert.Equal(4, keys.Distinct().Count());
        var shape = keys.Select(w => (w.Id, w.Slot, w.Cast, w.Pressed, w.Hold)).ToList();
        var e = Dummy(b, 1.5, 0);
        // In set A nothing flavors.
        foreach (var w in keys) b.HitEnemy(e, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = w });
        Assert.Equal(0, b.StanceFlavored);
        Assert.True(b.Swap());
        Assert.Equal(stance, b.StanceNow!.Id);
        // Same four keys, same forms: nothing turned off.
        Assert.Equal(shape, Enumerable.Range(0, Weapons.MaxKeys).Select(i => b.OnSlot(i)!).Select(w => (w.Id, w.Slot, w.Cast, w.Pressed, w.Hold)).ToList());
        Assert.All(keys, w => Assert.True(w.Keyed, w.Id));
        // Each key's blow carries the stance; an auto's and a status tick's do not.
        foreach (var w in keys)
        {
            int n = b.StanceFlavored;
            b.HitEnemy(e, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = w });
            Assert.Equal(n + 1, b.StanceFlavored);
        }
        int k = b.StanceFlavored;
        var auto = b.Weapons.First(w => w.Slot >= Weapons.MaxKeys);
        b.HitEnemy(e, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = auto });
        b.HitEnemy(e, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = keys[0], Dot = true });
        Assert.Equal(k, b.StanceFlavored);
    }

    [Fact]
    public void Each_stance_flavors_its_own_way()
    {
        // Twin blades: every key blow bleeds.
        var tb = Fight(12, "twin_blades");
        tb.Swap();
        var e = Dummy(tb, 1.5, 0);
        tb.HitEnemy(e, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = tb.OnSlot(1) });
        Assert.True(e.Status.Has(StatusKind.Bleed));
        // Mace: every second blow stuns.
        var m = Fight(12, "mace");
        m.Swap();
        Tick(m, 2);
        var me = Dummy(m, 1.5, 0);
        m.HitEnemy(me, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = m.OnSlot(1) });
        Assert.False(me.Status.Has(StatusKind.Stun));
        m.HitEnemy(me, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = m.OnSlot(1) });
        Assert.True(me.Status.Has(StatusKind.Stun));
        // Shield: each blow brings her Warding light back sooner.
        var s = Fight(12, "shield");
        s.Swap();
        var se = Dummy(s, 1.5, 0);
        s.Player.BlockT = 5;
        s.HitEnemy(se, 5, School.Physical, [Tag.Melee], new HitOpts { Weapon = s.OnSlot(1) });
        Assert.True(s.Player.BlockT < 5);
    }

    [Fact]
    public void A_swap_strike_fires_once_per_swap_on_its_own_cooldown()
    {
        var b = Fight(12, "mace");
        var e = Dummy(b, 1.2, 0);
        Tick(b, 1);                                  // (it has come up and stands in reach)
        double hp = e.Hp;
        Assert.True(b.Swap());                       // into B: Crushing Blow
        Assert.Equal(1, b.SwapStrikes);
        Assert.True(e.Hp < hp);
        Assert.True(b.Swap());                       // back to A: the Greatsword Draw, its own cooldown
        Assert.Equal(2, b.SwapStrikes);
        Assert.True(b.Swap());                       // into B again at once: its strike is cooling
        Assert.True(b.Swap());
        Assert.Equal(2, b.SwapStrikes);
        Assert.Equal(4, b.Swaps);
        Assert.True(b.StrikeReadyIn(1) > 0);
        Tick(b, Stances.Find("mace")!.Strike.Cooldown + 0.1);
        Assert.Equal(0, b.StrikeReadyIn(1));
        Assert.True(b.Swap());
        Assert.Equal(3, b.SwapStrikes);
        var swaps = b.Events.Drain().OfType<Ev.Swap>().ToList();
        Assert.Equal("Crushing Blow", Assert.Single(swaps).Strike);
    }

    /// <summary>Each stance's counts against set A (0 there): what it gives (+) and costs (-).</summary>
    static Dictionary<string, double> Axes(StanceDef s)
    {
        double Mod(string stat, ModKind kind) => s.Mods.Where(m => m.Stat == stat && m.Kind == kind).Sum(m => m.Value);
        var b = s.Blow;
        return new()
        {
            ["damage"] = Mod(Stat.Damage, ModKind.More),
            ["pace"] = -Mod(Stat.Cooldown, ModKind.More),
            ["guard"] = Mod(Stat.Armor, ModKind.Inc) + Mod(Stat.Armor, ModKind.More) + Mod(Stat.MaxHealth, ModKind.More) + 0.25 * Mod(Stat.Block, ModKind.Flat),
            ["stride"] = Mod(Stat.MoveSpeed, ModKind.More),
            ["throw"] = Mod(Stat.Knockback, ModKind.Inc),
            ["control"] = (b.Stun + b.Stagger) / Math.Max(1, b.Every) + b.Ward,
            ["bleed"] = (b.Bleed?.Power ?? 0) / Math.Max(1, b.Every),
        };
    }

    [Fact]
    public void Every_stance_has_a_price_and_a_gift_and_none_is_better_on_every_count()
    {
        var all = Stances.All.ToDictionary(s => s.Id, Axes);
        Assert.True(all.Count >= 3);
        foreach (var (id, ax) in all)
        {
            Assert.True(ax.Values.Any(v => v < 0), $"{id} costs nothing");
            Assert.True(ax.Values.Any(v => v > 0), $"{id} gives nothing");
            Assert.NotEmpty(Stances.Find(id)!.Flavor);
            Assert.True(Stances.Find(id)!.Strike.Cooldown > 0, id);
        }
        foreach (var (a, x) in all)
            foreach (var (b, y) in all)
                if (a != b) Assert.False(x.Keys.All(k => x[k] >= y[k]), $"{a} is at least {b} on every count");
        // Set A's own strike for the warden.
        Assert.NotNull(Stances.SetA("warden"));
    }
}
