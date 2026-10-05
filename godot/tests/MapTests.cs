using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Wayfinder's maps (docs/SKILLS_DESIGN.md §17): charts, placed packs that rest until
/// the survivor comes, kinds opening by tier, the ruler at the end on shorter floors, three falls,
/// and the atlas.</summary>
[Collection("Balance")]
public class MapTests
{
    sealed record Run(Journey J, HeadlessHost Host, MapRun Zone, Battle B, MapBuild Map);

    static Run Open(Chart chart, string calling = "warden", int level = 10)
    {
        var j = MapSim.Survivor(calling, level, 2, 3);
        var map = MapGen.Generate(chart.Map);
        var host = new HeadlessHost(j, 3);
        var zone = new MapRun(host, map, chart);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 3);
        b.Hooks = BattleHooks.Following(zone.Hooks);
        var zh = zone.Hooks;
        b.Hooks.OnPickup = p => (zh.OnPickup == null || zh.OnPickup(p)) && j.PickedUp(p);
        host.Battle = b;
        zone.Begin(b);
        return new Run(j, host, zone, b, map);
    }

    static void Step(Run r, double seconds, Action? each = null)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            r.Zone.Step(1 / 60.0);
            r.Zone.Frame(1 / 60.0);
            r.B.Tick(1 / 60.0, 0, 0);
            r.B.Events.Drain();
            r.Host.Pass(1 / 60.0);
            each?.Invoke();
            if (r.Zone.Over) return;
        }
    }

    static Chart Chart(string people = "pack", int tier = 1, params string[] mods) =>
        new() { Tier = tier, People = people, Seed = 1234, Mods = mods.ToList(), Name = "The Test Map" };

    [Fact]
    public void A_chart_carries_its_map_and_reads_back_whole()
    {
        var rng = new Rng(7);
        for (int i = 0; i < 40; i++)
        {
            var c = Charts.Roll(rng, 1 + i % 16, MapOffers.Peoples[i % 4].Id);
            var back = Charts.FromRef(Charts.Ref(c))!;
            Assert.Equal(c.Tier, back.Tier);
            Assert.Equal(c.People, back.People);
            Assert.Equal(c.Seed, back.Seed);
            Assert.Equal(c.Mods, back.Mods);
            Assert.Equal(c.Name, back.Name);
            // Plain charts have no mods, fine ones one or two, rare three to five; never two that clash.
            Assert.InRange(c.Mods.Count, c.Rarity switch { 2 => 3, 1 => 1, _ => 0 }, c.Rarity switch { 2 => 5, 1 => 2, _ => 0 });
            Assert.False(c.Has("blight") && c.Has("thin_blood"));
            Assert.False(c.Has("contested") && c.Tier < 8);
            // Each mod pays.
            Assert.True(c.Quantity >= 1 + 0.08 * c.Mods.Count - 1e-9);
        }
        // Into the pack as a chart, with its map.
        var j = MapSim.Survivor("warden", 10, 1, 1);
        var chart = Charts.Roll(new Rng(3), 2, "dead");
        Assert.True(j.PickedUp(new Pickup(0) { Kind = PickupKind.Item, Ref = Charts.Ref(chart), Value = 1 }));
        var it = j.Ch.Satchel.First(i => i.Chart != null);
        Assert.Equal(Charts.Item, it.Def);
        Assert.Equal(2, it.Chart!.Tier);
    }

    [Fact]
    public void Kinds_and_signs_open_by_tier_not_by_a_clock()
    {
        var pack = MapOffers.People("pack");
        var t1 = Charts.Kinds(pack, 1).Select(k => k.Def).ToHashSet();
        // The first two stretches' kinds at the first tier, never a later stretch's.
        Assert.Contains("boar", t1);
        Assert.Contains("wolf_runner", t1);
        Assert.DoesNotContain("wolf_blighted", t1);
        Assert.DoesNotContain("wolf_howler", t1);
        Assert.Equal(2, Charts.Guardians(pack, 1).Count);
        // The whole roster by the ninth.
        var t9 = Charts.Kinds(pack, 9).Select(k => k.Def).ToHashSet();
        foreach (var h in pack.Arena) Assert.Contains(h.Def, t9);
        Assert.Equal(5, Charts.Guardians(pack, 9).Count);
        Assert.Contains("bannered", Charts.Signs(pack, 9));
        Assert.DoesNotContain("bannered", Charts.Signs(pack, 1));
    }

    [Fact]
    public void Packs_rest_where_they_lie_until_she_comes_near()
    {
        var r = Open(Chart());
        Step(r, 1);
        // Only what is near the start is set down.
        Assert.True(r.Zone.PackCount >= 20);
        Assert.True(r.Zone.PacksPlaced < r.Zone.PackCount / 4, $"{r.Zone.PacksPlaced} of {r.Zone.PackCount} set down at the start");
        // Come within sight of one: it is set down, resting, at the map's level (its leader a level up).
        var (sx, sz) = r.Zone.Standing.OrderBy(s => (s.X - r.Map.Start.X) * (s.X - r.Map.Start.X) + (s.Z - r.Map.Start.Z) * (s.Z - r.Map.Start.Z)).First();
        r.B.Player.X = sx + 30; r.B.Player.Z = sz;
        Step(r, 0.2);
        Assert.NotEmpty(r.B.Enemies.Living());
        // (Nothing out of her reach is roused: another pack may lie nearer her than this one.)
        var p = r.B.Player;
        Assert.DoesNotContain(r.B.Enemies.Living(), e => e.Roused && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) > 16 * 16);
        Assert.Contains(r.B.Enemies.Living(), e => !e.Roused);
        Assert.All(r.B.Enemies.Living(), e => Assert.Equal(r.Zone.Chart.Level, e.Level - (e.Elite ? 1 : 0)));
        // Walked up to, it wakes, and its own with it.
        var near = r.B.Enemies.Living().OrderBy(e => (e.X - sx) * (e.X - sx) + (e.Z - sz) * (e.Z - sz)).First();
        r.B.Player.X = near.X + 6; r.B.Player.Z = near.Z;
        Step(r, 0.5);
        Assert.True(r.B.Enemies.Living().Count(x => x.Roused) >= 3);
    }

    [Fact]
    public void The_ruler_keeps_its_script_on_the_maps_shorter_floors()
    {
        var r = Open(Chart("kerchiefs"));
        var bc = r.Map.Boss;
        r.B.Player.X = bc.X; r.B.Player.Z = bc.Z;
        Step(r, 0.2);
        var boss = r.Zone.Boss!;
        Assert.NotNull(boss);
        Assert.IsType<RedHand>(r.Zone.BossScript);
        Assert.Equal(MapRun.BossFloors, r.Zone.BossScript!.FloorScale);
        double start = r.B.Time, took = -1;
        // An absurd build: the map's floors (10, 13 and 10 s, and the turns) still hold it.
        Step(r, 120, () =>
        {
            r.B.Player.Hp = r.B.MaxHp;
            if (boss.Alive && boss.Boss && boss.State != EnemyState.Dying) r.B.HitEnemy(boss, boss.MaxHp * 0.2, School.Storm, [Tag.Storm], new HitOpts { NoCrit = true });
            if (r.Zone.Cleared && took < 0) took = r.B.Time - start;
        });
        Assert.True(r.Zone.Cleared);
        Assert.InRange(took, 15 * 2 * MapRun.BossFloors + 5, 60);
        // The first clear of the Kerchiefs at the first tier: marked, a point, and the next tier's chart.
        Assert.True(Atlas.Done(r.J.World, "kerchiefs", 1));
        Assert.Equal(1, Atlas.Points(r.J.World));
        // (On the ground, or already in the pack if they fell within her reach.)
        var charts = r.B.Pickups.Living().Where(p => p.Ref != null && Charts.FromRef(p.Ref) != null).Select(p => Charts.FromRef(p.Ref!)!)
            .Concat(r.J.Ch.Satchel.Where(i => i.Chart != null).Select(i => i.Chart!)).ToList();
        Assert.NotEmpty(charts);
        Assert.Contains(charts, c => c.Tier == 2 && c.People == "kerchiefs");
    }

    /// <summary>The owner: getting up and fighting on is rare, "or it is a balancing nightmare". A fall
    /// closes the map and spills half of what was picked up there; only a trait that gets her up
    /// keeps her in it, and it catches her before the fall counts.</summary>
    [Fact]
    public void A_fall_closes_a_map_and_spills_half_of_what_was_picked_up_there()
    {
        var r = Open(Chart("dead"));
        // Something picked up here.
        r.B.Hooks.OnPickup!(new Pickup(0) { Kind = PickupKind.Material, Ref = "bone_dust", Value = 8 });
        Assert.Equal(8, r.J.Ch.Materials.GetValueOrDefault("bone_dust"));
        Assert.False(r.B.Hooks.OnPlayerDeath!(null));
        Assert.Equal(1, r.Zone.Falls);
        Assert.Equal(4, r.J.Ch.Materials.GetValueOrDefault("bone_dust"));
    }

    [Fact]
    public void Cold_Then_Not_gets_her_up_on_a_map_before_the_fall_counts()
    {
        var r = Open(Chart("dead"));
        var p = r.B.Player;
        p.Revives = 1;
        r.B.HurtPlayer(r.B.MaxHp * 5, School.Physical, "test", null);
        Assert.True(p.Alive);
        Assert.Equal(r.B.MaxHp * 0.5, p.Hp, 1);
        Assert.Equal(0, r.Zone.Falls);
    }

    /// <summary>The experience lead's shape: three clearings before the ruler's at tiers 1-2, four at
    /// 3-5, five from 6, the other turns of the way only bends; an altar in each clearing but the
    /// first, to three; and the last way to the ruler empty, a breath before it.</summary>
    [Theory]
    [InlineData(1, 3, 1)]
    [InlineData(3, 4, 2)]
    [InlineData(6, 5, 3)]
    public void A_map_has_its_tiers_clearings_and_a_breath_before_its_ruler(int tier, int clearings, int altars)
    {
        var r = Open(Chart("dead", tier));
        var areas = r.Map.Areas;
        Assert.Equal(clearings, areas.Count(a => a.Kind is AreaKind.Clearing or AreaKind.Altar));
        Assert.Equal(altars, areas.Count(a => a.Kind == AreaKind.Altar));
        Assert.NotEqual(AreaKind.Altar, areas.First(a => a.Kind is AreaKind.Clearing or AreaKind.Altar).Kind);
        // Walk the way to the ruler's clearing's edge: nothing set down on its last stretch.
        var last = areas[^2];
        var bc = r.Map.Boss;
        r.B.Player.Iframes = 1e9;
        for (double k = 0; k <= 1; k += 0.05)
        {
            r.B.Player.X = last.X + (bc.X - last.X) * k * 0.8; r.B.Player.Z = last.Z + (bc.Z - last.Z) * k * 0.8;
            Step(r, 0.05);
        }
        Assert.DoesNotContain(r.B.Enemies.Living(), e => (e.X - bc.X) * (e.X - bc.X) + (e.Z - bc.Z) * (e.Z - bc.Z) < 30 * 30
            && (e.X - last.X) * (e.X - last.X) + (e.Z - last.Z) * (e.Z - last.Z) > last.R * last.R && !e.Boss && e.Wake > 0);
    }

    /// <summary>The map's event: lit by the first altar's keeper falling, the people's question asked
    /// three times over about fifty seconds; then a strongbox at the altar, three to five things at
    /// the map's level, its opening shown.</summary>
    [Fact]
    public void The_first_altar_lit_asks_the_peoples_question_and_ends_in_a_strongbox()
    {
        var r = Open(Chart("pack"));
        var altar = r.Map.Altars.First();
        var p = r.B.Player;
        p.X = altar.X; p.Z = altar.Z;
        Step(r, 0.2);
        // The keepers down (an absurd build), the altar is lit and the question asked.
        int waves = 0;
        ChestOpened? chest = null;
        r.Host.Opened = c => chest = c;
        for (double t = 0; t < 75 && chest == null; t += 1 / 60.0)
        {
            p.Hp = r.B.MaxHp; p.Iframes = 1;
            foreach (var e in r.B.Enemies.Living().ToList())
                if (e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) < 30 * 30)
                    r.B.HitEnemy(e, e.MaxHp * 2, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            r.Zone.Step(1 / 60.0);
            r.B.Tick(1 / 60.0, 0, 0);
            foreach (var ev in r.B.Events.Drain()) if (ev is Ev.Telegraph { Kind: TelegraphKind.Ground }) waves++;
            r.Host.Pass(1 / 60.0);
            // The strongbox is walked to.
            foreach (var k in r.B.Pickups.Living()) if (k.Kind == PickupKind.Chest && k.Ref == "strongbox") { p.X = k.X; p.Z = k.Z; }
        }
        Assert.True(waves > 10);
        Assert.NotNull(chest);
        Assert.InRange(chest!.Items.Count, 3, 7);
        Assert.Contains(chest.Items, i => i.Kind == ChestItemKind.Gear);
    }

    [Fact]
    public void A_charts_suffixes_weaken_the_survivor()
    {
        var r = Open(Chart("pack", 1, "sleepless", "brittle", "sour"));
        Assert.Equal(0, r.B.Rules.RegenMul);
        Assert.Equal(0.6, r.B.Rules.ArmourMul, 3);
        var p = r.B.Player;
        p.Hp = r.B.MaxHp * 0.5;
        double before = p.Hp;
        Step(r, 2);
        Assert.Equal(before, p.Hp, 3);
        r.B.HealPlayer(100, "draught");
        Assert.Equal(before + 50 * r.B.Stats.Get(Stat.Healing), p.Hp, 1);
    }
}
