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

    static CharacterData Joined()
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, seed: 7);
        ch.Level = UnionJoin.Level;
        foreach (var s in new[] { "dawnpulse", "judgement_disc" })
        {
            ch.Skills.Add(s); ch.Slotted.Add(s);
            var st = Wicks.StrandsOf(s).First();
            for (int n = 1; n <= Wicks.PerStrand; n++) Assert.Equal(WickNo.None, WickBook.Plan(ch, s, $"{st.Id}.{n}"));
        }
        for (int i = 0; i < 2; i++)
        {
            var it = Inventory.Make(ch, a.Weapons[0], rarity: 2, seed: (uint)(ch.NextUid + 11));
            it.Rarity = 2;
            ch.Pack[ch.Pack.IndexOf(null)] = it;
        }
        Assert.Equal(UnionNo.None, UnionJoin.Join(ch, "dawns_judgement"));
        return ch;
    }

    static Battle Fight(Journey j) => j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7);

    [Fact]
    public void A_joined_union_is_in_the_campaign_fight_and_kept_by_the_kit_refresh()
    {
        var ch = Joined();
        var j = Journey.Begin(new CreationChoice { Name = "A", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id, WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = Callings.Archetype("warden").Abilities[0] }, 42);
        j.Ch.Level = ch.Level; j.Ch.Skills.Clear(); j.Ch.Skills.AddRange(ch.Skills);
        j.Ch.Slotted.Clear(); j.Ch.Slotted.AddRange(ch.Slotted);
        j.Ch.Lamps = ch.Lamps; j.Ch.Pack = ch.Pack;
        var u = Unions.Find("dawns_judgement")!;
        var b = Fight(j);
        Assert.Equal(1, b.Weapons.Count(w => w.Id == u.Into));
        Assert.DoesNotContain(b.Weapons, w => w.Id == u.A || w.Id == u.B);
        for (int i = 0; i < 3; i++) j.RefreshKit(b);
        Assert.Equal(1, b.Weapons.Count(w => w.Id == u.Into));
        Assert.DoesNotContain(b.Weapons, w => w.Id == u.A || w.Id == u.B);
        Assert.Equal(UnionNo.None, UnionJoin.Unjoin(j.Ch, "dawns_judgement"));
        j.RefreshKit(b);
        Assert.DoesNotContain(b.Weapons, w => w.Id == u.Into);
        Assert.Contains(b.Weapons, w => w.Id == u.A);
        Assert.Contains(b.Weapons, w => w.Id == u.B);
    }
}
