using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-sockets) Support gems worn in the fight (Battle.WearSupports) and a joined Union carried by Journey's fights.</summary>
[Collection("Balance")]
public class SupportsFightTests
{
    static (Battle B, WeaponInst W, CharacterData Ch) Rig(string skill, int rank, params string[] gems)
    {
        var ch = Character.Create(new CreationChoice { Name = "A", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id, WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = Callings.Archetype("warden").Abilities[0] }, seed: 7);
        for (int i = 0; i < gems.Length; i++)
        {
            ch.Gems.Owned[gems[i]] = 1;
            Assert.True(Supports.Socket(ch.Gems, skill, 6, i, gems[i]), gems[i]);
        }
        var b = BattleTests.Arena(1, (skill, rank));
        b.WearSupports(Supports.SourceFor(ch));
        return (b, b.Weapons[0], ch);
    }

    [Fact]
    public void Brutality_raises_damage_and_cuts_area_and_wearing_again_does_not_compound()
    {
        var (b, w, ch) = Rig("sunder", 3, "brutality");
        Assert.Equal(1.25, w.Mods.Damage, 9);
        Assert.Equal(0.85, w.Mods.Area, 9);
        var one = (w.Mods.Damage, w.Mods.Area, w.Mods.Cooldown);
        b.WearSupports(Supports.SourceFor(ch)); b.WearSupports(Supports.SourceFor(ch));
        Assert.Equal(one, (w.Mods.Damage, w.Mods.Area, w.Mods.Cooldown));
    }

    [Fact]
    public void A_socket_closed_by_rank_adds_nothing()
    {
        var (b, w, _) = Rig("sunder", 6, "brutality");
        Assert.Equal(1.25, w.Mods.Damage, 9);
        b.SetRank("sunder", 2);
        Assert.Equal(1.0, w.Mods.Damage, 9);
        Assert.Null(w.Support);
        b.SetRank("sunder", 6);
        Assert.Equal(1.25, w.Mods.Damage, 9);
    }

    [Fact]
    public void Haste_lowers_the_cooldown()
    {
        var plain = BattleTests.Arena(1, ("sunder", 3)).Weapons[0];
        var (b, w, _) = Rig("sunder", 3, "haste");
        double was = Firing.CooldownOf(BattleTests.Arena(1, ("sunder", 3)), plain);
        Assert.True(Firing.CooldownOf(b, w) < was);
    }

    [Fact]
    public void Bloodletting_puts_a_bleed_on_what_it_strikes()
    {
        var (b, w, _) = Rig("sunder", 3, "bloodletting");
        var e = b.SpawnEnemy("wolf", 3, 0)!;
        e.AttackT = 99; e.RangedT = 99;
        b.HitEnemy(e, 5, School.Physical, w.Def.Tags, new HitOpts { Weapon = w });
        Assert.NotNull(e.Status[StatusKind.Bleed]);
        var (b2, w2, _) = Rig("sunder", 3);
        var e2 = b2.SpawnEnemy("wolf", 3, 0)!;
        b2.HitEnemy(e2, 5, School.Physical, w2.Def.Tags, new HitOpts { Weapon = w2 });
        Assert.Null(e2.Status[StatusKind.Bleed]);
    }

    [Fact]
    public void Echo_makes_a_firing_pulse_once_more()
    {
        var (b, w, _) = Rig("sunder", 3, "echo");
        Assert.Equal(1, w.Support!.Echo);
        var e = b.SpawnEnemy("wolf", 2, 0)!;
        e.AttackT = 99; e.RangedT = 99;
        int most = 0;
        for (int i = 0; i < 600 && w.Cuts == 0 && w.Casts == 0; i++) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); most = Math.Max(most, w.PulseLeft); }
        for (int i = 0; i < 30; i++) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); most = Math.Max(most, w.PulseLeft); }
        Assert.True(most >= 1, "pulse left " + most);
    }

    [Fact]
    public void A_union_weapon_takes_both_halves_gems()
    {
        var u = Unions.Find("dawns_judgement")!;
        var ch = Character.Create(new CreationChoice { Name = "A", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id, WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = Callings.Archetype("warden").Abilities[0] }, seed: 7);
        ch.Gems.Owned["haste"] = 1; ch.Gems.Owned["echo"] = 1;
        Assert.True(Supports.Socket(ch.Gems, u.A, 6, 0, "haste"));
        Assert.True(Supports.Socket(ch.Gems, u.B, 6, 0, "echo"));
        var fx = Supports.SourceFor(ch)(u.Into, 6);
        Assert.Equal(0.15, fx["speed"], 9);
        Assert.Equal(1, fx["echo"], 9);
        Assert.Equal(0.15, Supports.SourceFor(ch)(u.A, 6)["speed"], 9);
    }

    // ---- Journey ----

    const string Wall = "falling_wall";

    /// <summary>A campaign Warden levelled to 15 the way play does, her taught build granted and her points lit (Light my
    /// way), two rare items in her pack.</summary>
    static Journey AtFifteen()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "A", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 42);
        while (j.Ch.Level < UnionJoin.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 0.01);
        j.Teach(null);
        WickBook.LightAll(j.Ch);
        for (int i = 0; i < 2; i++)
        {
            var it = Inventory.Make(j.Ch, a.Weapons[0], rarity: 2, seed: (uint)(j.Ch.NextUid + 11));
            it.Rarity = 2;
            j.Ch.Pack[j.Ch.Pack.IndexOf(null)] = it;
        }
        return j;
    }

    static Battle Fight(Journey j) => j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7);

    /// <summary>BUILD_UNLOCKS.md level 15: the Warden's first Union is reachable on her taught build. Its two halves are
    /// keys she is taught (Heroic Leap, key 2; Shield Charge, key 4), both carried at 15 and both burning a Turn, so she
    /// joins it at a lamp-post for its price (two rare items), and not a level before.</summary>
    [Fact]
    public void A_campaign_warden_at_15_on_her_taught_build_can_join_her_first_union()
    {
        var t = TaughtBuilds.Of("warden")!;
        Assert.Equal(Wall, t.Union?.Id);
        var u = Unions.Find(Wall)!;
        Assert.Contains(t.Keys, k => k.Skill == u.A && k.Level < UnionJoin.Level);
        Assert.Contains(t.Keys, k => k.Skill == u.B && k.Level < UnionJoin.Level);
        Assert.True(Weapons.CanCarry("warden", u.Id));
        Assert.Equal(2, u.Price);
        var j = AtFifteen();
        Assert.Contains(u.A, j.Ch.Slotted);
        Assert.Contains(u.B, j.Ch.Slotted);
        Assert.False(SkillBook.IsAuto(j.Ch, u.A));
        Assert.False(SkillBook.IsAuto(j.Ch, u.B));
        Assert.True(UnionJoin.TurnBurning(j.Ch, u.A), u.A);
        Assert.True(UnionJoin.TurnBurning(j.Ch, u.B), u.B);
        Assert.Contains(UnionJoin.Offered(j.Ch), o => o.Id == Wall);
        // A level short, it waits.
        j.Ch.Level = UnionJoin.Level - 1;
        Assert.Equal(UnionNo.Level, UnionJoin.CanJoin(j.Ch, Wall));
        j.Ch.Level = UnionJoin.Level;
        int had = j.Ch.Pack.Count(x => x != null);
        Assert.Equal(UnionNo.None, UnionJoin.Join(j.Ch, Wall));
        Assert.Equal(had - 2, j.Ch.Pack.Count(x => x != null));
        Assert.True(UnionJoin.Known(j.Ch, Wall));
        Assert.Single(UnionJoin.Live(j.Ch));
    }

    [Fact]
    public void A_joined_union_is_in_the_campaign_fight_and_kept_by_the_kit_refresh()
    {
        var j = AtFifteen();
        Assert.Equal(UnionNo.None, UnionJoin.Join(j.Ch, Wall));
        var u = Unions.Find(Wall)!;
        var b = Fight(j);
        Assert.Equal(1, b.Weapons.Count(w => w.Id == u.Into));
        Assert.DoesNotContain(b.Weapons, w => w.Id == u.A || w.Id == u.B);
        // It holds both halves' keys.
        var joined = b.Weapons.Single(x => x.Id == u.Into);
        Assert.True(joined.Slot >= 0 && joined.Slot2 >= 0 && joined.Slot != joined.Slot2);
        for (int i = 0; i < 3; i++) j.RefreshKit(b);
        Assert.Equal(1, b.Weapons.Count(w => w.Id == u.Into));
        Assert.DoesNotContain(b.Weapons, w => w.Id == u.A || w.Id == u.B);
        Assert.Equal(UnionNo.None, UnionJoin.Unjoin(j.Ch, Wall));
        j.RefreshKit(b);
        Assert.DoesNotContain(b.Weapons, w => w.Id == u.Into);
        Assert.Contains(b.Weapons, w => w.Id == u.A);
        Assert.Contains(b.Weapons, w => w.Id == u.B);
    }
}
