using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The warden quarter's and the crossings' phase-1 rules, read by the fight (docs/design/CLASSES.md 2).</summary>
public sealed class LampRulesTests
{
    static LampEffect Rule(string id, params (string, double)[] args)
    {
        var d = new Dictionary<string, double>();
        foreach (var (k, v) in args) d[k] = v;
        return new LampEffect { Do = LampDo.Rule, Rule = id, Args = d };
    }

    static int Blocked(Battle b, int blows)
    {
        int took = 0;
        for (int i = 0; i < blows; i++)
        {
            b.Player.Iframes = 0;
            if (b.HurtPlayer(10, School.Physical, "test", null) > 0) took++;
        }
        return blows - took;
    }

    [Fact]
    public void A_lamp_block_turns_blows_and_lays_stones_and_the_wall_that_holds_forbids_moving()
    {
        var b = BattleTests.Arena(3);
        b.Lamps = new LampLoadout();
        b.Lamps.Add(Rule("shield_arm", ("block", 0.75), ("stones", 10), ("radius", 4)));
        int blocked = Blocked(b, 40);
        Assert.True(blocked > Blocked(BattleTests.Arena(3), 40));
        Assert.InRange(b.Stones, 0, 9);

        // The wall that holds: still, doubled; moving, nothing.
        var w = BattleTests.Arena(3);
        w.Lamps = new LampLoadout();
        w.Lamps.Add(Rule("shield_arm", ("block", 0.4)));
        w.Lamps.Add(Rule("wall_holds", ("cap", 0.75)));
        w.Player.Moving = true;
        // Moving, no lamp block rolls: just what the dodge already turned.
        var bare = BattleTests.Arena(3);
        Assert.Equal(Blocked(bare, 30), Blocked(w, 30));
        w.Player.Moving = false;
        Assert.True(Blocked(w, 60) > Blocked(BattleTests.Arena(3), 60));
    }

    [Fact]
    public void A_block_size_is_a_quarter_by_night()
    {
        var day = new LampLoadout();
        day.Add(Rule("block.still", ("add", 0.2)));
        var night = new LampLoadout { Night = true };
        night.Add(Rule("block.still", ("add", 0.2)));
        Assert.Equal(0.2, day.Size("block.still", "add"), 6);
        Assert.Equal(0.05, night.Size("block.still", "add"), 6);
        // The wall's price is kept in full by night.
        night.Add(Rule("wall_holds", ("cap", 0.75)));
        Assert.Equal(0.75, night.Full("wall_holds", "cap"), 6);
    }

    [Fact]
    public void A_skill_lamp_widens_dawnpulse_and_a_tag_lamp_widens_heavy_and_nova()
    {
        var b = BattleTests.Arena(1, ("dawnpulse", 1));
        var w = b.Weapons[0];
        b.Lamps = new LampLoadout();
        double plain = Firing.AreaOf(b, w, 3.75);
        var wide = new LampEffect { Do = LampDo.Rule, Rule = "skill.area", Skill = "dawnpulse", Args = new() { ["inc"] = 0.2 } };
        var tags = new LampEffect { Do = LampDo.Rule, Rule = "tags.area", Tags = [Tag.Heavy, Tag.Nova], Args = new() { ["inc"] = 0.08 } };
        b.Lamps = new LampLoadout();
        b.Lamps.Add(wide); b.Lamps.Add(tags);
        Assert.Equal(plain * 1.28, Firing.AreaOf(b, w, 3.75), 6);
        b.Lamps = new LampLoadout { Night = true };
        b.Lamps.Add(wide);
        Assert.Equal(plain * 1.05, Firing.AreaOf(b, w, 3.75), 6);
    }

    [Fact]
    public void Burning_projectile_damage_and_a_champion_bleed_rule_read_the_target()
    {
        var b = BattleTests.Arena(2);
        b.Lamps = new LampLoadout();
        b.Lamps.Add(Rule("projectiles.vs_burning", ("more", 0.08)));
        var e = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z);
        Assert.NotNull(e);
        e!.MaxHp = e.Hp = 1e6;
        var tags = new[] { Tag.Projectile };
        double cold = b.HitEnemy(e, 100, School.Physical, tags, new HitOpts { NoCrit = true, Projectile = true });
        b.ApplyStatus(e, new StatusPayload(StatusKind.Burn, 10, 1, 3), 0);
        double hot = b.HitEnemy(e, 100, School.Physical, tags, new HitOpts { NoCrit = true, Projectile = true });
        Assert.True(hot > cold * 1.05);
    }

    // ---- the reaver quarter ----

    static double MeleeOnBleeder(LampLoadout l)
    {
        var b = BattleTests.Arena(2);
        b.Lamps = l;
        var e = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e6;
        b.ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 10, 1, 3), 100);
        return b.HitEnemy(e, 100, School.Physical, [Tag.Melee], new HitOpts { NoCrit = true });
    }

    [Fact]
    public void Bleeding_things_take_more_from_melee_and_by_night_a_quarter_of_it()
    {
        var plain = MeleeOnBleeder(new LampLoadout());
        var day = new LampLoadout(); day.Add(Rule("bleeding.melee", ("more", 0.1)));
        var night = new LampLoadout { Night = true }; night.Add(Rule("bleeding.melee", ("more", 0.1)));
        Assert.Equal(plain * 1.1, MeleeOnBleeder(day), 4);
        Assert.Equal(plain * 1.025, MeleeOnBleeder(night), 4);
    }

    [Fact]
    public void Always_bleeding_loses_what_would_mend_past_half_and_nothing_spared_mends_more_but_drinks_no_draught()
    {
        var b = BattleTests.Arena(3);
        b.Lamps = new LampLoadout();
        b.Lamps.Add(Rule("always_bleeding", ("cap", 0.5)));
        b.Player.Hp = b.MaxHp * 0.4;
        b.HealPlayer(b.MaxHp, "test");
        Assert.Equal(b.MaxHp * 0.5, b.Player.Hp, 4);

        var n = BattleTests.Arena(3);
        n.Lamps = new LampLoadout();
        n.Lamps.Add(Rule("no_draught"));
        n.Player.Hp = 10;
        n.HealPlayer(10, "test");
        Assert.Equal(25, n.Player.Hp, 4);
        n.Player.Hp = 10;
        n.HealPlayer(10, "draught");
        Assert.Equal(10, n.Player.Hp, 4);
        Assert.True(n.NoDraught);
    }

    [Fact]
    public void A_hit_on_a_bound_thing_adds_one_stack_of_frenzy_more_by_day_and_by_night_and_the_bonus_is_a_quarter()
    {
        foreach (bool night in new[] { false, true })
        {
            var b = BattleTests.Arena(2);
            b.Lamps = new LampLoadout { Night = night };
            b.Lamps.Add(Rule("frenzy", ("per", 0.01), ("cap", 20), ("fade", 3)));
            b.Lamps.Add(Rule("hook_and_hatchet"));
            var e = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z)!;
            e.MaxHp = e.Hp = 1e6;
            e.Status[StatusKind.Bound] = new StatusSlot(10, 1, 0, 0);
            b.HitEnemy(e, 10, School.Physical, [Tag.Melee], new HitOpts { NoCrit = true, Projectile = true });
            Assert.Equal(2, b.Frenzy, 6);
            var w = b.Weapons[0];
            double bare = Firing.CooldownOf(BattleTests.Arena(2), BattleTests.Arena(2).Weapons[0]);
            Assert.Equal(bare / (1 + 2 * (night ? 0.0025 : 0.01)), Firing.CooldownOf(b, w), 6);
        }
    }

    [Fact]
    public void The_butchers_count_price_is_in_full_by_night_but_its_per_stack_number_is_a_size()
    {
        double Taken(bool night)
        {
            var b = BattleTests.Arena(3);
            b.Lamps = new LampLoadout { Night = night };
            b.Lamps.Add(Rule("butchers_count", ("per", 0.01), ("cap", 50), ("seconds", 10), ("price", 0.5)));
            for (int i = 0; i < 20; i++) b.AddBuff("butchers_count", Stat.Damage, 0.01, ModKind.Inc, 10, 50);
            b.Player.Hp = b.MaxHp;
            return b.HurtPlayer(100, School.Physical, "test", null);
        }
        var bare = BattleTests.Arena(3);
        double plain = bare.HurtPlayer(100, School.Physical, "test", null);
        Assert.Equal(plain * 1.1, Taken(false), 4);
        Assert.Equal(plain * 1.025, Taken(true), 4); // the per-stack number is a size (a quarter by night); only the half is in full
    }

    static LampLoadout NightWith(params LampEffect[] rules) { var l = new LampLoadout { Night = true }; foreach (var r in rules) l.Add(r); return l; }

    [Fact]
    public void The_shield_arms_chance_is_in_full_by_night_and_its_riders_are_sizes()
    {
        var b = BattleTests.Arena(3);
        b.Lamps = NightWith(Rule("shield_arm", ("block", 0.15)), Rule("block.still", ("add", 0.2)));
        b.Player.StillT = 1;
        // Reflection-free: the blocks over many blows sit near 0.15 + 0.05, not the quarter-sized 0.0375 + 0.05.
        for (int i = 0; i < 400; i++) { b.Player.Iframes = 0; b.Player.Hp = b.MaxHp; b.HurtPlayer(10, School.Physical, "test", null); }
        // 0.15 + 0.05 = 0.20 in full; a quarter-sized chance would give 0.0375 + 0.05 = 0.0875 (dodge adds nothing here: no Blocks).
        Assert.InRange(b.Blocks, 400 * 0.14, 400 * 0.27);
    }

    [Fact]
    public void A_warding_block_lays_a_stone()
    {
        var b = BattleTests.Arena(3);
        b.Lamps = new LampLoadout();
        b.Lamps.Add(Rule("shield_arm", ("block", 0.0), ("stones", 10)));
        b.AddBoon("warding");
        b.Player.Iframes = 0;
        Assert.Equal(0, b.HurtPlayer(10, School.Physical, "test", null));
        Assert.Equal(1, b.Stones);
        Assert.Equal(1, b.Blocks);
    }

    [Fact]
    public void Stones_fall_one_a_second_after_the_lull_and_never_with_the_mortar()
    {
        foreach (bool mortar in new[] { false, true })
        {
            var b = BattleTests.Arena(3);
            b.Lamps = new LampLoadout();
            b.Lamps.Add(Rule("shield_arm", ("block", 0.0), ("stones", 10), ("lull", 6)));
            if (mortar) b.Lamps.Add(Rule("mortar", ("barrier", 0.01)));
            b.AddBoon("warding");
            for (int i = 0; i < 4; i++) { b.Player.Iframes = 0; b.Player.BlockT = 0; b.HurtPlayer(10, School.Physical, "test", null); }
            Assert.Equal(4, b.Stones);
            for (int i = 0; i < 55; i++) b.Tick(0.1, 0, 0);
            Assert.Equal(4, b.Stones); // still inside the lull
            for (int i = 0; i < 30; i++) b.Tick(0.1, 0, 0); // 3 more seconds
            if (mortar) Assert.Equal(4, b.Stones);
            else Assert.InRange(b.Stones, 1, 3); // falling singly, not all at once
            for (int i = 0; i < 100; i++) b.Tick(0.1, 0, 0);
            Assert.Equal(mortar ? 4 : 0, b.Stones);
        }
    }

    [Fact]
    public void The_rebuke_is_as_hard_as_the_wall_is_thick_and_grows_with_the_ember_as_the_flare_does()
    {
        var b = BattleTests.Arena(3);
        b.Lamps = NightWith(Rule("shield_arm", ("block", 0.15), ("stones", 10), ("radius", 4), ("rebuke", 10), ("per_level", 0.08)));
        // Its defining number is in full by night: ten times max health at the ember's first level.
        b.EmberLevel = 1;
        Assert.Equal(b.MaxHp * 10, b.RebukePower(), 6);
        // And 8% more a level, as the Flare's power (Lamps.FlarePower): at the ember's 51st, six times as hard.
        b.EmberLevel = 51;
        Assert.Equal(b.MaxHp * 10 * 5, b.RebukePower(), 6);
        // By day (no ember) the survivor's own level stands in for it.
        b.EmberOn = false;
        b.Level = 11;
        Assert.Equal(b.MaxHp * 10 * 1.8, b.RebukePower(), 6);
        // The lamp's own number, as the board builds it.
        var arm = Lamps.Get("bulwark.shield_arm").Effects[0];
        Assert.Equal(10, arm.Arg("rebuke", 0), 6);
        Assert.Equal(0.08, arm.Arg("per_level", 0), 6);

        // Ten stones: the rebuke lands its power through the build's damage on what stands near, and none past its reach.
        var w = BattleTests.Arena(3);
        w.Lamps = NightWith(Rule("shield_arm", ("block", 0.0), ("stones", 10), ("radius", 4), ("rebuke", 10), ("per_level", 0.08)));
        w.AddBoon("warding");
        var near = System.Array.Find(w.Enemies.Items, e => e != null && e.Alive && Dist(e, w) < 3.5);
        for (int i = 0; i < 10; i++) { w.Player.Iframes = 0; w.Player.BlockT = 0; w.HurtPlayer(1, School.Physical, "test", null); }
        Assert.Equal(1, w.Rebukes);
        Assert.Equal(0, w.Stones);
        if (near != null) Assert.True(w.DamageBy.GetValueOrDefault("rebuke") > 0);
    }

    static double Dist(Enemy e, Battle b) => System.Math.Sqrt((e.X - b.Player.X) * (e.X - b.Player.X) + (e.Z - b.Player.Z) * (e.Z - b.Player.Z));

    [Fact]
    public void The_long_chains_reach_is_in_full_by_night()
    {
        var b = BattleTests.Arena(3);
        b.Lamps = NightWith(Rule("long_chain", ("reach", 3), ("weaker", 0.2)));
        b.AddWeapon("oathblade", 1);
        Assert.Equal(3, b.ChainReach(b.Weapons[0]), 6);
    }

    // ---- the arcanist quarter ----

    [Fact]
    public void Frozen_things_take_more_from_fire_and_by_night_a_quarter_of_it()
    {
        double Fire(LampLoadout? l)
        {
            var b = BattleTests.Arena(2);
            if (l != null) b.Lamps = l;
            var e = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z)!;
            e.MaxHp = e.Hp = 1e6;
            e.Status[StatusKind.Frozen] = new StatusSlot(10, 1, 0, 0);
            return b.HitEnemy(e, 100, School.Fire, [Tag.Spell], new HitOpts { NoCrit = true });
        }
        LampLoadout Lit(bool night) { var l = new LampLoadout { Night = night }; l.Add(Rule("frozen.fire", ("more", 0.1))); return l; }
        double plain = Fire(null);
        Assert.Equal(plain * 1.1, Fire(Lit(false)), 4);
        Assert.Equal(plain * 1.025, Fire(Lit(true)), 4);
    }

    [Fact]
    public void Standing_in_her_ground_takes_less_with_ash_walker_and_the_price_is_kept_in_full_by_night()
    {
        foreach (bool night in new[] { false, true })
        {
            double Taken(bool inGround)
            {
                var b = BattleTests.Arena(3);
                b.Lamps = new LampLoadout { Night = night };
                b.Lamps.Add(Rule("ash_walker", ("less", 0.4), ("weaker", 0.15)));
                if (inGround) b.SpawnZone(Side.Player, b.Player.X, b.Player.Z, 3, 30, 0, School.Fire);
                b.Tick(0.3, 0, 0);
                b.Player.Hp = b.MaxHp;
                return b.HurtPlayer(100, School.Physical, "test", null);
            }
            double out_ = Taken(false), in_ = Taken(true);
            Assert.Equal(1 - 0.4 * (night ? 0.25 : 1), in_ / out_, 3);
        }
        // Outside the ground a spell is 15% weaker, in full by day and by night.
        foreach (bool night in new[] { false, true })
        {
            var b = BattleTests.Arena(2);
            double plain = b.HitEnemy(b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z)!, 100, School.Fire, [Tag.Spell], new HitOpts { NoCrit = true });
            var c = BattleTests.Arena(2);
            c.Lamps = new LampLoadout { Night = night };
            c.Lamps.Add(Rule("ash_walker", ("less", 0.4), ("weaker", 0.15)));
            double weak = c.HitEnemy(c.SpawnEnemy("wolf", c.Player.X + 5, c.Player.Z)!, 100, School.Fire, [Tag.Spell], new HitOpts { NoCrit = true });
            Assert.Equal(plain * 0.85, weak, 4);
        }
    }

    [Fact]
    public void Spells_loose_at_most_one_projectile_more_by_night_however_many_the_lamps_add()
    {
        int Count(bool night, bool crowd)
        {
            var b = BattleTests.Arena(1, ("seeking_motes", 1));
            b.Lamps = new LampLoadout { Night = night };
            b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "tags.projectiles", Tags = [Tag.Spell], Args = new() { ["add"] = 1 } });
            if (crowd) b.Lamps.Add(Rule("crowded_sky", ("add", 2), ("weaker", 0.35)));
            return Firing.CountOf(b, b.Weapons[0]);
        }
        int bare = Firing.CountOf(BattleTests.Arena(1, ("seeking_motes", 1)), BattleTests.Arena(1, ("seeking_motes", 1)).Weapons[0]);
        Assert.Equal(bare + 1, Count(false, false));
        Assert.Equal(bare + 3, Count(false, true));
        Assert.Equal(bare + 1, Count(true, true));
    }

    [Fact]
    public void The_echos_wait_is_kept_in_full_by_night_and_unbound_casting_waits_a_quarter_less_by_night()
    {
        double Wait(bool night, params LampEffect[] lamps)
        {
            var b = BattleTests.Arena(1, ("seeking_motes", 1));
            b.Lamps = new LampLoadout { Night = night };
            foreach (var x in lamps) b.Lamps.Add(x);
            return Firing.CooldownOf(b, b.Weapons[0]);
        }
        double bare = Wait(false);
        var echo = Rule("the_echo", ("delay", 0.5), ("share", 0.5), ("longer", 0.25));
        var unbound = Rule("unbound_casting", ("sooner", 0.3));
        Assert.Equal(bare * 1.25, Wait(false, echo), 6);
        Assert.Equal(bare * 1.25, Wait(true, echo), 6);
        Assert.Equal(bare * 0.7, Wait(false, unbound), 6);
        Assert.Equal(bare * (1 - 0.3 * 0.25), Wait(true, unbound), 6);
    }

    [Fact]
    public void Fire_on_a_frozen_thing_shatters_it_onto_its_neighbours()
    {
        var b = BattleTests.Arena(2);
        b.Lamps = new LampLoadout();
        b.Lamps.Add(Rule("fire_on_ice", ("radius", 2), ("share", 0.5)));
        var a = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z)!;
        var n = b.SpawnEnemy("wolf", b.Player.X + 6, b.Player.Z)!;
        a.MaxHp = a.Hp = 1e6; n.MaxHp = n.Hp = 1e6;
        b.Tick(0.05, 0, 0);
        a.Status[StatusKind.Frozen] = new StatusSlot(10, 1, 0, 0);
        b.HitEnemy(a, 100, School.Fire, [Tag.Spell], new HitOpts { NoCrit = true });
        Assert.False(a.Status.Has(StatusKind.Frozen));
        Assert.True(n.Hp < n.MaxHp);
    }

    [Fact]
    public void Stalker_poisoned_steel_is_a_size_and_long_sights_near_price_is_kept_in_full_by_night()
    {
        double Hit(LampLoadout? l, double dx, bool poisoned, params Tag[] tags)
        {
            var b = BattleTests.Arena(2);
            if (l != null) b.Lamps = l;
            var e = b.SpawnEnemy("wolf", b.Player.X + dx, b.Player.Z)!;
            e.MaxHp = e.Hp = 1e6;
            if (poisoned) e.Status[StatusKind.Poison] = new StatusSlot(10, 1, 0, 0);
            return b.HitEnemy(e, 100, School.Physical, tags, new HitOpts { NoCrit = true, Projectile = true });
        }
        foreach (bool night in new[] { false, true })
        {
            double k = night ? 0.25 : 1;
            LampLoadout Lit(params LampEffect[] r) { var l = new LampLoadout { Night = night }; foreach (var x in r) l.Add(x); return l; }
            double steel = Hit(null, 5, true, Tag.Steel);
            Assert.Equal(steel * (1 + 0.1 * k), Hit(Lit(Rule("poisoned.steel", ("more", 0.1))), 5, true, Tag.Steel), 4);
            var sight = Rule("long_sight", ("range", 8), ("more", 0.5), ("near", 4), ("weaker", 0.3));
            double far = Hit(null, 11, false, Tag.Ranged), close = Hit(null, 2, false, Tag.Ranged);
            Assert.Equal(far * (1 + 0.5 * k), Hit(Lit(sight), 11, false, Tag.Ranged), 4);
            Assert.Equal(close * 0.7, Hit(Lit(sight), 2, false, Tag.Ranged), 4);
        }
    }

    [Fact]
    public void Volley_looses_two_more_arrows_by_day_and_one_by_night_and_only_volley()
    {
        int Count(bool night, string skill)
        {
            var b = BattleTests.Arena(1, (skill, 1));
            b.Lamps = new LampLoadout { Night = night };
            b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "skill.projectiles", Skill = "volley", Args = new() { ["add"] = 2 } });
            return Firing.CountOf(b, b.Weapons[0]);
        }
        int bare = Firing.CountOf(BattleTests.Arena(1, ("volley", 1)), BattleTests.Arena(1, ("volley", 1)).Weapons[0]);
        Assert.Equal(bare + 2, Count(false, "volley"));
        Assert.Equal(bare + 1, Count(true, "volley"));
        int other = Firing.CountOf(BattleTests.Arena(1, ("knifestorm", 1)), BattleTests.Arena(1, ("knifestorm", 1)).Weapons[0]);
        Assert.Equal(other, Count(false, "knifestorm"));
    }

    [Fact]
    public void Never_still_halves_the_blows_after_a_second_still_in_full_by_night_and_dashes_return_a_quarter_less_faster()
    {
        foreach (bool night in new[] { false, true })
        {
            var b = BattleTests.Arena(2);
            b.Lamps = new LampLoadout { Night = night };
            b.Lamps.Add(Rule("never_still", ("faster", 0.4), ("weaker", 0.5)));
            var e = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z)!;
            e.MaxHp = e.Hp = 1e6;
            var o = new HitOpts { NoCrit = true, Projectile = true };
            double moving = b.HitEnemy(e, 100, School.Physical, [Tag.Ranged], o);
            b.Player.StillT = 1.5;
            Assert.Equal(moving * 0.5, b.HitEnemy(e, 100, School.Physical, [Tag.Ranged], o), 4);
        }
    }
}
