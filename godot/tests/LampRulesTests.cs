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
}
