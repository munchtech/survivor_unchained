using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(P3, docs/design/DEN_ROSTER.md section 3) The den's roster: its packs are recipes, its foes have one move each,
/// and nowhere else is the table's row changed.</summary>
[Collection("Balance")]
public class DenRosterTests
{
    sealed record Run(MapRun Zone, Battle B);

    static Run Open(Chart chart)
    {
        var j = MapSim.Survivor("warden", 6, 2, 3);
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
        return new Run(zone, b);
    }

    static Run Den(int seed)
    {
        var r = Open(Chart.ForDungeon(DungeonGen.Get("hollow")!, seed, 6));
        r.Zone.PlaceAll();
        return r;
    }

    static readonly string[] Telegraphed = ["boar", "wolf_blighted", "boar_slurry", "boar_ironback", "wolf_howler"];

    [Fact]
    public void The_dens_packs_are_all_recipes_and_at_most_one_foe_in_three_is_telegraphed()
    {
        var ids = DenRoster.Recipes.Select(x => x.Id).ToHashSet();
        int seen = 0;
        for (int seed = 1; seed <= 6; seed++)
            foreach (var (recipe, _, defs) in Den(seed).Zone.PackMakeup)
            {
                seen++;
                Assert.Contains(recipe, ids);
                int tele = defs.Count(d => Telegraphed.Contains(d));
                Assert.True(tele * 3 <= defs.Count, $"seed {seed} {recipe}: {tele} of {defs.Count} telegraphed");
            }
        Assert.True(seen > 0);
    }

    /// <summary>(P3 session 2) A recipe pack wakes as one: Battle.Rouse wakes only a foe's own people, and a recipe mixes the Pack's
    /// wolves with the wild boars (measured 22 Nov: its boars woke late and came in behind the wolves).</summary>
    [Fact]
    public void A_recipe_pack_wakes_as_one_though_its_boars_are_another_people()
    {
        int mixed = 0;
        for (int seed = 1; seed <= 4; seed++)
        {
            var r = Den(seed);
            foreach (var (recipe, _, members) in r.Zone.PackLives)
            {
                var live = members.Where(m => m.E.Alive && m.E.Seed == m.Seed).Select(m => m.E).ToList();
                if (live.Select(e => e.Faction).Distinct().Count() < 2 || live.Any(e => e.Roused)) continue;
                mixed++;
                r.B.Rouse(live.First(e => e.Faction == Faction.Pack));
                Assert.Contains(live, e => !e.Roused);   // the battle's own rouse leaves the other people asleep
                r.Zone.Step(1 / 60.0);
                Assert.All(live, e => Assert.True(e.Roused, $"seed {seed} {recipe}: {e.Def.Id} slept on"));
            }
        }
        Assert.True(mixed > 0, "no mixed recipe pack met");
    }

    [Fact]
    public void Over_six_dens_every_kind_of_the_roster_is_fielded()
    {
        var seen = new HashSet<string>();
        for (int seed = 1; seed <= 6; seed++)
            foreach (var (_, _, defs) in Den(seed).Zone.PackMakeup) foreach (var d in defs) seen.Add(d);
        foreach (var kind in new[] { "wolf", "wolf_runner", "wolf_blighted", "boar", "boar_slurry", "wolf_howler", "boar_ironback" })
            Assert.Contains(kind, seen);
    }

    [Fact]
    public void The_cut_changes_the_dens_kinds_and_never_the_table()
    {
        var wolfRunner = Enemies.Get("wolf_runner");
        Assert.Equal(Behavior.Orbit, wolfRunner.Behavior);
        Assert.Equal(26, wolfRunner.Health);
        Assert.NotNull(wolfRunner.Lunge);

        var live = new List<Enemy>();
        for (int seed = 1; seed <= 6; seed++) live.AddRange(Den(seed).B.Enemies.Living());
        var runner = live.First(e => e.Def.Id == "wolf_runner").Def;
        Assert.Equal(Behavior.Chase, runner.Behavior);
        Assert.Null(runner.Lunge);
        Assert.Equal(14, runner.Health);
        var sick = live.First(e => e.Def.Id == "wolf_blighted").Def;
        Assert.Equal(Behavior.Ranged, sick.Behavior);
        Assert.True(sick.Ranged!.Lob);
        Assert.Equal(0.6, sick.Ranged.Aim);
        Assert.NotNull(sick.Burst);
        Assert.NotNull(live.First(e => e.Def.Id == "boar").Def.Charge);
        Assert.Equal(2.8, live.First(e => e.Def.Id == "boar_ironback").Def.Slam!.Radius);
    }

    /// <summary>(den first blow, 22 Nov) The den row's `roam` (dungeon_fights.json) is the side of the box a resting pack mills in
    /// round its spot; 0, the shipped value, is the leash's 0.6 (14.4 m), as a map's packs. It rides the den's own copies of
    /// its kinds (every recipe kind has one), never the table's rows. Measured 22 Nov: at 4 a pack is 2.0 m from its middle at
    /// the wake against 5.8 m, and all of it reaches her inside 0.8 s against 2.2 s.</summary>
    [Fact]
    public void A_resting_den_pack_mills_in_the_rows_roam_box_and_the_table_carries_none()
    {
        var kinds = DenRoster.Recipes.SelectMany(x => x.Parts.Select(p => p.Def)).ToHashSet();
        foreach (var id in kinds) Assert.Equal(0, Enemies.Get(id).Roam);
        double Farthest(double roam)
        {
            var r = Den(2);
            var cuts = r.B.Roster!;
            // Every recipe kind has a den copy carrying the row's roam (so a den number reaches it), never the table's own row.
            foreach (var id in kinds)
            {
                Assert.NotSame(Enemies.Get(id), cuts[id]);
                Assert.Equal(DungeonFights.Of("hollow").Roam, cuts[id].Roam);
            }
            // (A signed champion's def is Signs.Wear's, made once for the whole process: not this battle's, so left alone here.)
            var rest = r.B.Enemies.Living().Where(e => e.Wake > 0 && !e.Roused && cuts.TryGetValue(e.Def.Id, out var c) && ReferenceEquals(c, e.Def)).ToList();
            Assert.NotEmpty(rest);
            foreach (var d in cuts.Values) d.Roam = roam;                         // this battle's own copies
            for (int k = 0; k < 40 * 30; k++) { r.Zone.Step(1 / 30.0); r.Zone.Frame(1 / 30.0); r.B.Tick(1 / 30.0, 0, 0); }
            var still = rest.Where(e => e.Alive && !e.Roused).ToList();
            Assert.NotEmpty(still);
            return still.Max(e => Math.Sqrt((e.X - e.HomeX) * (e.X - e.HomeX) + (e.Z - e.HomeZ) * (e.Z - e.HomeZ)));
        }
        double tight = Farthest(4), loose = Farthest(0);
        Assert.True(tight <= 3.8, $"a 4 m box: the farthest stands {tight:0.0} m from its spot");
        Assert.True(loose > 4.5, $"the leash's box: the farthest stands {loose:0.0} m from its spot");
    }

    /// <summary>(den first blow, 22 Nov) A champion's Sign is worn on the def it was given. The den's cut of a kind and the
    /// table's row share an id and are two kinds; Signs.Wear kept what it made by id for the whole process, so whichever was
    /// signed first won: after a den, an arena night's Ironbound runner was the den's (14 health, no lunge), or, the other way
    /// round, the den's champion was the table's. Both orders here: the den first, then the table first.</summary>
    [Fact]
    public void A_champions_sign_is_worn_on_the_def_it_was_given_den_first_or_table_first()
    {
        static void Carries(EnemyDef from, EnemyDef worn)
        {
            Assert.Equal(from.Id, worn.Id);
            Assert.Equal(from.Health, worn.Health);
            Assert.Equal(from.Behavior, worn.Behavior);
            Assert.Same(from.Lunge, worn.Lunge);
            Assert.Same(from.Slam, worn.Slam);
            Assert.Equal(0.4, worn.IronSkin);                                     // and it wears the Sign
            Assert.Equal(new[] { "ironbound" }, worn.Signs);
            Assert.Empty(from.Signs);                                             // the kind itself is untouched
        }
        string[] sign = ["ironbound"];
        var cuts = Den(1).B.Roster!;                                              // a den battle's own kinds
        Assert.Null(Open(new Chart { Tier = 1, People = "pack", Seed = 1234, Mods = new List<string>(), Name = "The Test Map" }).B.Roster);   // outside the den: the table's rows

        // The den first: a den champion, then the same kind signed the same way outside the den.
        EnemyDef cut = cuts["wolf_runner"], row = Enemies.Get("wolf_runner");
        Assert.NotEqual(row.Health, cut.Health);
        var den = Signs.Wear(cut, sign);
        var outside = Signs.Wear(row, sign);
        Assert.NotSame(den, outside);
        Carries(cut, den);
        Carries(row, outside);

        // The table first: a champion outside the den, then the den's.
        cut = cuts["boar_ironback"]; row = Enemies.Get("boar_ironback");
        Assert.NotEqual(row.Health, cut.Health);
        outside = Signs.Wear(row, sign);
        den = Signs.Wear(cut, sign);
        Assert.NotSame(den, outside);
        Carries(row, outside);
        Carries(cut, den);

        // Kept: the same kind signed the same way again is the same def, each side.
        Assert.Same(den, Signs.Wear(cut, sign));
        Assert.Same(outside, Signs.Wear(row, sign));
    }

    [Fact]
    public void Only_the_den_battle_carries_a_roster()
    {
        var den = Open(Chart.ForDungeon(DungeonGen.Get("hollow")!, 1, 6));
        Assert.NotNull(den.B.Roster);
        var map = Open(new Chart { Tier = 1, People = "pack", Seed = 1234, Mods = new List<string>(), Name = "The Test Map" });
        Assert.Null(map.B.Roster);
    }
}
