using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Champions and carriers (M5-B, docs/design/ARPG.md 5 lessons 5, 6 and 8, 7.1): named elites with affixes from
/// the telegraph kit (data/content/champions.json, Content/Champions.cs), crowned by Encounters, and a pack's captain
/// as its carrier (Encounters.Carried).</summary>
public class ChampionsTests
{
    const double Dt = 1 / 60.0;

    static Battle Road(uint seed) => new(new BattleSetup
    {
        Seed = seed, Collision = new CollisionWorld(260), Combat = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
    });

    /// <summary>One pack of risen at (0, 30) with the champion given (a JSON object).</summary>
    static Encounters.Spec One(string champion, string captain = "null") => Json.Parse<Encounters.Spec>($$"""
        { "beats": [ { "id": "p", "kind": "pack", "x": 0, "z": 30, "foes": [ { "def": "risen", "n": 3 } ], "captain": {{captain}}, "champion": {{champion}} } ] }
        """);

    [Fact]
    public void The_affixes_load_and_each_kit_affix_is_a_telegraph_kind()
    {
        Assert.Equal(4, Champions.PerTier.Count);
        Assert.True(Champions.PerTier.Zip(Champions.PerTier.Skip(1)).All(p => p.Second >= p.First), "the count never falls with the tier");
        Assert.True(Champions.Names.Count >= 12 && Champions.Epithets.Count >= 12);
        var kinds = Champions.All.Values.Where(a => a.Kind != null).Select(a => a.Kind!).ToHashSet();
        Assert.Equal(new HashSet<string> { "ring", "charge", "pull", "closing" }, kinds);
        foreach (var a in Champions.All.Values)
        {
            Assert.Matches("^[A-Z][a-z]+$", a.Label);
            if (a.Kind != null) Assert.NotNull(Telegraphs.Get(a.Kind));
            else Assert.True(a.Health != 1 || a.Damage != 1 || a.Speed != 1, a.Id + " is no number on the foe");
            Assert.True(a.Every[1] >= a.Every[0] && a.Every[0] > 0);
        }
        // Every champion the Low Ford names has affixes the kit has, and a def that exists.
        var s = Encounters.For("lowford")!;
        var specs = s.Beats.Where(b => b.Champion != null).Select(b => b.Champion!).Concat(s.Placed.Values).ToList();
        Assert.InRange(specs.Count, 4, 6);
        foreach (var c in specs)
        {
            Assert.False(string.IsNullOrEmpty(c.Name));
            if (c.Def != null) Assert.NotNull(Content.Enemies.Get(c.Def));
            foreach (var id in c.Affixes.EnumerateArray()) Assert.NotNull(Champions.Get(id.GetString()!));
        }
        Assert.Equal("rare", s.Get("n_first")!.Loot);
    }

    [Fact]
    public void A_champion_beat_spawns_a_named_elite_with_its_affix_numbers()
    {
        var b = Road(3);
        var d = new Encounters(One("""{ "def": "risen", "name": "Hob Marrow the Drowned", "affixes": ["ironhide", "swift"] }"""), b, new Dictionary<string, Fact>(), 2, 1);
        d.Place();
        var (e, _) = d.Champions["p"];
        Assert.True(e.Elite);
        Assert.Equal("Hob Marrow the Drowned", e.Named!.Title);
        Assert.Equal(["Ironhide", "Swift"], e.Named.Affixes);
        Assert.Equal(["ironhide", "swift"], d.AffixesOn(e));
        // (an elite on a non-elite def is x3, and Ironhide's x1.4 on that; the beat's level and the champion's step)
        var def = Content.Enemies.Get("risen");
        int lv = Encounters.Level(2, 1, d.S.Get("p")!) + 1;
        Assert.Equal(lv, e.Level);
        Assert.Equal(def.Health * Content.Enemies.ScaleFor(lv).Health * 3 * 1.4, e.MaxHp, 6);
        Assert.Equal(e.MaxHp, e.Hp, 6);
        // With no captain it is the pack's carrier, and one of the pack.
        Assert.Same(e, d.Captain("p"));
        Assert.Equal(4, d.Packs["p"].Count);

        // The Low Ford's: its captain crowned in place (no extra foe), the howler crowned when it comes.
        var lf = new Encounters(Encounters.For("lowford")!, Road(4), new Dictionary<string, Fact>(), 2, 1);
        lf.Place();
        var tolly = lf.Champions["kerchiefs"].E;
        Assert.Same(tolly, lf.Captain("kerchiefs"));
        Assert.Equal("kerchief_captain", tolly.Def.Id);
        Assert.Equal(["Grasping"], tolly.Named!.Affixes);
        Assert.Equal(["Charging"], lf.Champions["wallow"].E.Named!.Affixes);
        Assert.Equal(lf.S.Get("kerchiefs")!.Foes.Sum(f => f.N) + 1, lf.Packs["kerchiefs"].Count);
        // A zone's own (the Barrow Knight): crowned by its key, its one affix the armor it stands in.
        var kb = Road(5);
        var night = new Encounters(Encounters.For("lowford")!, kb, new Dictionary<string, Fact>(), 1, 0, "night");
        var knight = kb.SpawnEnemy("barrow_knight", 0, 20, new Battle.SpawnOpts { Level = 1, Tag = "knight" })!;
        double hp = knight.MaxHp;
        night.Crown(knight, "knight");
        Assert.Equal(["Ironhide"], knight.Named!.Affixes);
        Assert.Equal(hp * 1.4, knight.MaxHp, 6);
        Assert.Same(knight, night.Champions["knight"].E);
    }

    [Fact]
    public void A_rolled_count_is_the_fights_dice_and_rises_at_world_tier_four()
    {
        List<string> Roll(uint seed, int tier)
        {
            var d = new Encounters(One("""{ "def": "risen", "affixes": 1 }"""), Road(seed), new Dictionary<string, Fact>(), 2, 1) { Tier = tier };
            d.Place();
            var e = d.Champions["p"].E;
            Assert.False(string.IsNullOrEmpty(e.Named!.Title));
            return d.AffixesOn(e).ToList();
        }
        Assert.Equal(Roll(21, 2), Roll(21, 2));
        Assert.Single(Roll(21, 1));
        Assert.Single(Roll(21, 2));
        Assert.Equal(2, Roll(21, 3).Count);
        var four = Roll(21, 4);
        Assert.Equal(3, four.Count);
        Assert.Equal(3, four.Distinct().Count());
        // Different fights roll different champions (somewhere in twenty seeds).
        Assert.True(Enumerable.Range(0, 20).Select(i => string.Join(",", Roll((uint)(100 + i), 2))).Distinct().Count() > 2);
        // A fixed list never grows with the tier.
        var fixedOne = new Encounters(One("""{ "def": "risen", "affixes": ["quaking"] }"""), Road(2), new Dictionary<string, Fact>(), 2, 1) { Tier = 4 };
        fixedOne.Place();
        Assert.Equal(["quaking"], fixedOne.AffixesOn(fixedOne.Champions["p"].E));
    }

    [Fact]
    public void A_kit_affix_is_cast_by_the_champion_on_its_cadence()
    {
        var b = Road(8);
        var d = new Encounters(One("""{ "def": "risen", "affixes": ["quaking"] }"""), b, new Dictionary<string, Fact>(), 2, 1);
        d.Place();
        var e = d.Champions["p"].E;
        var told = new List<double>();
        d.Told = (_, from, blow) => { if (from == e && blow.Tell == "ring") told.Add(b.Time); };
        b.Player.X = 0; b.Player.Z = 24;
        for (int i = 0; i < 60 * 30; i++)
        {
            // (she stands off its reach's edge and lives: the cadence is what is measured)
            b.Player.X = e.X; b.Player.Z = e.Z - 6; b.Player.Hp = b.MaxHp;
            b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain();
        }
        Assert.True(told.Count >= 2, $"{told.Count} rings in 30 s");
        var a = Champions.Get("quaking")!;
        for (int i = 1; i < told.Count; i++) Assert.True(told[i] - told[i - 1] >= a.Every[0] - 0.01);
    }

    static CreationChoice Choice() => new()
    {
        Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id,
        WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = Callings.Archetype("warden").Abilities[0],
    };

    [Fact]
    public void A_captain_carries_gear_on_its_kill_and_a_champion_carries_more()
    {
        var b = Road(6);
        var d = new Encounters(Encounters.For("lowford")!, b, new Dictionary<string, Fact>(), 2, 1);
        d.Place();
        var asked = new List<DropCtx>();
        List<Loot> Drops(DropCtx x) { asked.Add(x); return [new Loot(PickupKind.Gold, null, 1)]; }
        // The boars' captain: the loot "champion" source (0.45 a roll); the kerchiefs' crowned captain: "elite" (0.7).
        var boar = d.Captain("boars")!;
        Assert.Single(d.Carried(boar, Drops));
        Assert.Equal(DropSource.Champion, asked[^1].Source);
        Assert.Equal(0, asked[^1].Floor);
        Assert.Equal(boar.Level, asked[^1].Level);
        Assert.Equal("pack", asked[^1].People);
        // (once: a second call for the same carrier is nothing)
        Assert.Empty(d.Carried(boar, Drops));
        Assert.Single(asked);
        d.Carried(d.Captain("kerchiefs")!, Drops);
        Assert.Equal(DropSource.Elite, asked[^1].Source);
        // Nothing for the crowd.
        Assert.Empty(d.Carried(d.Standing("kerchiefs").First(f => f.Def.Id == "footpad"), Drops));
        Assert.Equal(2, asked.Count);

        // Through the zone's OnLoot hook: what it carried lies where it died.
        var j = Journey.Begin(Choice(), 42);
        int gear = 0;
        for (uint s = 0; s < 40; s++)
        {
            var bb = Road(200 + s);
            var dd = new Encounters(Encounters.For("lowford")!, bb, new Dictionary<string, Fact>(), 2, 1);
            dd.Place();
            var cap = dd.Captain("boars")!;
            gear += dd.Carried(cap, j.Drops).Count(l => l.Payload is ItemInstance);
        }
        // (about 45% a kill, the filter's verdict aside: well clear of none and of always)
        Assert.InRange(gear, 8, 32);
        for (int t = 0; t < 30; t++)
        {
            // (a fresh carrier each try: a roll may be no gear and no material)
            var bb = Road(300 + (uint)t);
            var dd = new Encounters(Encounters.For("lowford")!, bb, new Dictionary<string, Fact>(), 2, 1);
            dd.Place();
            bb.Hooks.OnLoot = e => dd.Carried(e, j.Drops);
            var cap = dd.Captain("wallow")!;
            double x = cap.X, z = cap.Z;
            bb.KillEnemy(cap, true, null);
            var lying = bb.Pickups.Items.Where(p => p.Alive && p.Persistent).ToList();
            if (lying.Count == 0) continue;
            Assert.All(lying, p => Assert.True(MathX.Dist(p.X, p.Z, x, z) < 3, "it fell where the captain died"));
            return;
        }
        Assert.Fail("thirty champions carried nothing");
    }

    [Fact]
    public void The_first_captains_floor_gives_a_rare_or_better()
    {
        var j = Journey.Begin(Choice(), 42);
        for (uint s = 0; s < 25; s++)
        {
            var b = Road(400 + s);
            var n = new Encounters(Encounters.For("lowford")!, b, new Dictionary<string, Fact>(), 1, 0, "night");
            n.Place();
            var cap = n.Captain("n_first")!;
            List<Dropped>? rolled = null;
            n.Carried(cap, x => { x.Ch = j.Ch; x.World = j.World; rolled = Rpg.Drops.Roll(x); return Rpg.Drops.AsLoot(rolled); });
            Assert.NotNull(rolled);
            Assert.True(rolled![0].Item != null, "the first roll is gear");
            Assert.True(rolled[0].Tier is >= LootTier.Rare and <= LootTier.Storied, $"seed {s}: {rolled[0].Tier}");
        }
        // Another night captain has no floor.
        var b2 = Road(9);
        var n2 = new Encounters(Encounters.For("lowford")!, b2, new Dictionary<string, Fact>(), 1, 0, "night");
        n2.Place();
        DropCtx? got = null;
        n2.Carried(n2.Captain("n_road2")!, x => { got = x; return []; });
        Assert.Equal(0, got!.Floor);
    }
}
