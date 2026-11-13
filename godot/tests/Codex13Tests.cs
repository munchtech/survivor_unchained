using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-087) A reward is never lost: pack, Rook's shelves, else held by her door.</summary>
public sealed class RewardDeliveryTests
{
    [Fact]
    public void A_gift_with_pack_and_storeroom_full_is_held_by_rooks_door_and_said_so()
    {
        // old: no free shelf place, and the item was dropped (the notice still said "sent to the inn")
        var s = H.Make();
        for (int i = 0; i < s.Ch.Pack.Count; i++) s.Ch.Pack[i] = Inventory.Make(s.Ch, "moonsilver_circlet", 1);
        for (int i = 0; i < s.World.Stash.Count; i++) s.World.Stash[i] = Inventory.Make(s.Ch, "moonsilver_circlet", 1);
        s.World.Held.Clear();
        Rules.Apply(H.Es("[{ set: { 'grove.circlet': true } }, { give: 'moonsilver_circlet' }]"), s.C);
        Assert.Single(s.World.Held, it => it.Def == "moonsilver_circlet");
        Assert.Contains(s.Notices, n => n.Text.Contains("holding it by the door"));
    }

    [Fact]
    public void A_gift_that_misses_the_pack_goes_to_a_free_shelf_place()
    {
        var s = H.Make();
        for (int i = 0; i < s.Ch.Pack.Count; i++) s.Ch.Pack[i] = Inventory.Make(s.Ch, "moonsilver_circlet", 1);
        s.World.Held.Clear();
        Rules.Apply(H.Es("[{ give: 'moonsilver_circlet' }]"), s.C);
        Assert.Contains(s.World.Stash, it => it?.Def == "moonsilver_circlet");
        Assert.Empty(s.World.Held);
        Assert.Contains(s.Notices, n => n.Text.Contains("Rook's storeroom"));
    }
}

/// <summary>(Codex audit SU-089) Every damage to a creature passes the defender's rules, a rival's too.</summary>
public sealed class RivalStrikeTests
{
    static (Battle B, Enemy Ruler, Enemy Rival) Setup()
    {
        var b = BattleTests.Arena(4);
        var ruler = b.SpawnEnemy("risen", b.Player.X + 8, b.Player.Z)!;
        ruler.Boss = true;
        ruler.MaxHp = ruler.Hp = 1000;
        var rival = b.SpawnEnemy("risen", b.Player.X + 9, b.Player.Z)!;
        return (b, ruler, rival);
    }

    [Fact]
    public void A_rivals_blow_stops_at_a_rulers_phase_floor()
    {
        // old: o.Hp -= dmg and KillEnemy: the rival killed it through its floor and ended the encounter
        var (b, ruler, rival) = Setup();
        ruler.HpFloor = 500;
        ruler.Hp = 520;
        b.CreatureStrike(ruler, 5000, School.Physical, Allegiance.Of(rival), rival, 1, 0);
        Assert.True(ruler.Alive);
        Assert.NotEqual(EnemyState.Dying, ruler.State);
        Assert.Equal(500, ruler.Hp, 6);
    }

    [Fact]
    public void A_ruler_turning_takes_nothing_from_a_rival()
    {
        var (b, ruler, rival) = Setup();
        ruler.TakenMul = 0;
        b.CreatureStrike(ruler, 200, School.Physical, Allegiance.Of(rival), rival, 1, 0);
        Assert.Equal(1000, ruler.Hp, 6);
    }

    [Fact]
    public void A_rivals_blow_takes_the_defenders_protection_share()
    {
        var (b, ruler, rival) = Setup();
        ruler.TakenMul = 0.5;
        double want = 100 * b.DefenderMul(ruler, School.Physical, false, 1, 0, out _);
        b.CreatureStrike(ruler, 100, School.Physical, Allegiance.Of(rival), rival, 1, 0);
        Assert.Equal(1000 - want, ruler.Hp, 6);
        Assert.True(want <= 50 + 1e-9);
    }
}

/// <summary>(Codex audit SU-092) The ground a missile leaves lasts by the one duration calculation.</summary>
public sealed class MissileGroundDurationTests
{
    [Fact]
    public void A_firepots_ground_is_lengthened_by_duration()
    {
        // old: SpawnZone took the raw 2.5 s (g.Duration); Evergreen and every duration source were ignored
        var b = BattleTests.Arena(4, ("firepot", 1));
        b.Stats.Add(new StatMod(Stat.Duration, ModKind.Flat, 1, "test"));
        var w = b.Weapons.Single(x => x.Id == "firepot");
        double want = Firing.DurationOf(b, w, w.GroundOf!.Duration);
        Assert.True(want > w.GroundOf.Duration * 1.5);
        var e = b.SpawnEnemy("risen", b.Player.X + 4, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e6;
        GroundZone? zn = null;
        for (int i = 0; i < 600 && zn == null; i++)
        {
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            zn = b.Zones.Living().FirstOrDefault(z => z.Weapon == "firepot");
        }
        Assert.NotNull(zn);
        Assert.Equal(want, zn!.Life, 6);
    }
}

/// <summary>(Codex audit SU-091) A missile's struck-thing memory is by lifetime: a newcomer in a struck slot is fresh.</summary>
public sealed class MissileHitMemoryTests
{
    [Fact]
    public void A_piercing_missile_strikes_a_newcomer_in_a_struck_things_slot()
    {
        // old: pr.Hits held e.Id, so the newcomer in that slot was skipped as already struck
        var b = BattleTests.Arena(4);
        var e = b.SpawnEnemy("risen", b.Player.X + 6, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e6;
        var pr = b.SpawnProjectile(Side.Player, e.X, e.Z, 10, School.Physical)!;
        pr.Pierce = 9; pr.Radius = 0.8; pr.Life = 5;
        b.Tick(1 / 60.0, 0, 0);
        Assert.Contains(Lifetime.Of(e), pr.Hits);
        int slot = e.Id;
        b.Enemies.Release(e);
        var n = b.SpawnEnemy("risen", pr.X, pr.Z)!;
        Assert.Equal(slot, n.Id);
        n.MaxHp = n.Hp = 1e6;
        b.Tick(1 / 60.0, 0, 0);
        Assert.True(n.Hp < n.MaxHp);
    }
}

/// <summary>(Codex audit SU-085/086) A chart's oaths do what they say on the map, and a carrier is known by lifetime.</summary>
[Collection("Balance")]
public sealed class ChartOathRuntimeTests
{
    static (MapRun Zone, Battle B) Open(params string[] mods)
    {
        var j = MapSim.Survivor("warden", 16, 2, 3);
        var chart = new Chart { Tier = 4, People = "pack", Seed = 1234, Name = "The Test Map" };
        chart.Mods.AddRange(mods);
        var map = MapGen.Generate(chart.Map);
        var host = new HeadlessHost(j, 3);
        var zone = new MapRun(host, map, chart);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 3);
        b.Hooks = BattleHooks.Following(zone.Hooks);
        host.Battle = b;
        zone.Begin(b);
        zone.PlaceAll();
        return (zone, b);
    }

    static List<Enemy> Foes(Battle b) => b.Enemies.Living().Where(e => e.Disposition == Disposition.Hostile).ToList();

    [Fact]
    public void The_deep_dark_sets_its_foes_two_levels_up()
    {
        // old: Levels 2 was dropped by the chart adapter; only the text said so
        var (plain, pb) = Open();
        var (deep, db) = Open("deep");
        Assert.Equal(2, deep.Chart.FoeLevels);
        int Low(Battle b) => Foes(b).Where(e => !e.Elite).Min(e => e.Level);
        Assert.Equal(Low(pb) + 2, Low(db));
        Assert.Equal(plain.Chart.ItemLevel, deep.Chart.ItemLevel);
    }

    [Fact]
    public void The_swarm_fields_packs_half_again_as_large()
    {
        // old: the Swarm's chart mod added 0 pack size (its 1.5 was dropped)
        var (_, pb) = Open();
        var (swarm, sb) = Open("swarm");
        Assert.Equal(1.5, swarm.Chart.PackSize, 6);
        Assert.True(Foes(sb).Count > Foes(pb).Count * 1.25, $"{Foes(sb).Count} vs {Foes(pb).Count}");
    }

    [Fact]
    public void Champions_lead_twice_the_packs()
    {
        // old: Elites 2 was dropped: the same share of packs had a champion leading them
        var (plain, _) = Open();
        var (champ, _) = Open("champions");
        Assert.Equal(2, champ.Chart.Elites, 6);
        int Led(MapRun z) => z.PackGrades.Count(g => g > 0);
        Assert.True(Led(champ) > Led(plain), $"{Led(champ)} vs {Led(plain)}");
    }

    [Fact]
    public void A_carriers_entry_goes_with_any_death_and_not_to_the_newcomer_in_its_slot()
    {
        // old: carriers keyed by e.Id, removed only on a credited kill: a rival's kill left it for the slot's newcomer
        var (zone, b) = Open();
        var c = b.Enemies.Living().First(zone.Carries);
        b.KillEnemy(c, false, null);
        b.Enemies.Release(c);
        var n = b.SpawnEnemy(c.Def.Id, c.X, c.Z)!;
        Assert.Equal(c.Id, n.Id);
        Assert.False(zone.Carries(n));
    }
}

/// <summary>(Codex audit SU-084) The atlas reaches every carried chart.</summary>
public sealed class AtlasPagingTests
{
    [Fact]
    public void Every_carried_chart_but_the_chosen_is_on_some_page()
    {
        // old: carried.Where(o => o != chosen).Take(6): the eighth chart on could never be chosen
        var items = Enumerable.Range(1, 15).Select(i => new ItemInstance { Uid = $"c{i}", Def = Charts.Item }).ToList();
        var seen = new HashSet<string>();
        var (_, _, pages) = Charts.OthersPage(items, "c3", 0);
        Assert.Equal(3, pages);
        for (int p = 0; p < pages; p++) foreach (var it in Charts.OthersPage(items, "c3", p).Shown) seen.Add(it.Uid);
        Assert.Equal(14, seen.Count);
        Assert.DoesNotContain("c3", seen);
        Assert.Equal(2, Charts.OthersPage(items, "c3", 99).Page);
    }
}

/// <summary>(Codex audit SU-088/090) The Verge: its crews by lifetime, its scars by stable id.</summary>
public sealed class VergeIdentityTests
{
    sealed record Setup(Journey J, FakeHost Host, Verge Zone, Battle B, ZoneMeta Meta);

    static Setup Make(TimeOfDay time = TimeOfDay.Day, Journey? j = null)
    {
        var a = Callings.Archetype("warden");
        j ??= Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        j.World.Time = time;
        var meta = ZoneMeta.Load("verge");
        var host = new FakeHost(j, meta);
        var zone = new Verge(host, meta);
        var ground = Heightfield.Load(meta);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), ground.HeightAt, at.X, at.Z, at.Facing, 11);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, meta);
    }

    [Fact]
    public void A_won_scar_stays_won_when_another_scar_stops_opening()
    {
        // old: completion keyed scar.{day}.{position}: with the Pack's scar gone, the won one reopened and the next was suppressed
        var s = Make(TimeOfDay.Night);
        var names = s.Zone.Interactables.Where(i => i.Id.StartsWith("scar:")).Select(i => i.Name).ToList();
        Assert.Contains("The Scar by the Stream", names);
        var dead = s.Zone.Interactables.Single(i => i.Name == "The Scar at the Sealed Door");
        s.B.Player.X = dead.X; s.B.Player.Z = dead.Z;
        dead.Act();
        s.J.Apply(s.Host.Entered!.OnWin!);
        s.J.World.Facts["beasts.population"] = 5;   // the Pack's scar no longer opens
        var again = Make(TimeOfDay.Night, s.J);
        var now = again.Zone.Interactables.Where(i => i.Id.StartsWith("scar:")).Select(i => i.Name).ToList();
        Assert.Equal(names.Where(n => n is not ("The Scar at the Sealed Door" or "The Scar by the Stream")).OrderBy(n => n), now.OrderBy(n => n));
        Assert.Contains(again.Zone.Interactables, i => i.Id == "scar:kerchiefs" || i.Id == "scar:lamplings");
    }

    [Fact]
    public void A_newcomer_in_a_fallen_crewmans_slot_does_not_keep_the_roost()
    {
        // old: roostCrew held Enemy refs; Up(newcomer) passed, so the camp was never cleared
        var s = Make();
        s.J.World.Facts["redcowl"] = "dead";
        var roost = s.Meta.Place("V", "roost");
        s.B.Player.X = roost.X; s.B.Player.Z = roost.Z - 30;
        s.Zone.Step(1 / 60.0);
        var crew = s.B.Enemies.Living().Where(e => e.Tag == "roost").ToList();
        Assert.True(crew.Count >= 4);
        var first = crew[0];
        s.B.KillEnemy(first, false, null);
        s.B.Enemies.Release(first);
        var n = s.B.SpawnEnemy("risen", first.X, first.Z)!;
        Assert.Equal(first.Id, n.Id);
        foreach (var e in crew.Skip(1)) s.B.KillEnemy(e, true, null);
        Assert.True(s.J.World.Fact("roost.cleared").Truthy);
    }
}
