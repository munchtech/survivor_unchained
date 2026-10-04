using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>An ember arena, run without a screen (Arena/Arena.cs, Play/Zones/ArenaRun.cs).</summary>
public class ArenaTests
{
    sealed record Setup(Journey J, FakeHost Host, ArenaRun Zone, Battle B, MapBuild Map, ArenaSpec Spec)
    {
        /// <summary>What was called out over the fight.</summary>
        public readonly List<string> Barks = new();
    }

    internal static ArenaSpec Spec(string people = "pack", bool story = false, params string[] oaths) => new()
    {
        Id = story ? "hollow_teeth" : "table:1", Name = "The Test Arena", Seed = 9, Tier = 1, People = people, Oaths = oaths.ToList(),
        Story = story, ReturnZone = "verge", ReturnX = 10, ReturnZ = 20,
        OnWin = """[{ "set": { "test.won": true } }]""", OnLose = """[{ "set": { "test.lost": true } }]""",
    };

    static Setup Make(ArenaSpec spec, Journey? j = null)
    {
        var a = Callings.Archetype("warden");
        j ??= Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        Arenas.Begin(j.World, spec);
        var map = MapGen.Generate(spec.Map);
        var host = new FakeHost(j, map.Meta, map.Ground);
        var zone = new ArenaRun(host, map, spec);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 11, arena: true);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, map, spec);
    }

    static void Run(Setup s, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            s.Zone.Step(1 / 60.0);
            s.Zone.Frame(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            foreach (var ev in s.B.Events.Drain()) if (ev is Ev.Bark bk) s.Barks.Add(bk.Text);
            s.Host.Pass(1 / 60.0);
        }
    }

    /// <summary>What rules the people (the strongest of its kind on the field).</summary>
    static Enemy Boss(Setup s) => s.B.Enemies.Living().Where(e => e.Def.Id == MapOffers.People(s.Spec.People).Boss).MaxBy(e => e.MaxHp)!;

    /// <summary>The boss beaten by a crushing build: through its phases (each gated by
    /// its floor), as fast as the contract lets anything win.</summary>
    static void Defeat(Setup s)
    {
        var boss = Boss(s);
        for (int i = 0; i < 400 && !s.Zone.Won; i++)
        {
            if (boss.Alive && boss.State != EnemyState.Dying) s.B.HitEnemy(boss, boss.MaxHp * 0.25, School.Physical, [Tag.Physical]);
            Run(s, 0.5);
        }
    }

    static int Hostile(Battle b) => b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying);

    /* ------------------------------------------------- the long night -- */

    /// <summary>The owner: "endless is truly endless - just keep ramping up till its
    /// impossible". No ceiling and no cliff: every minute harder than the last, smooth for
    /// the first three quarters of an hour, compounding after, so nothing holds for ever;
    /// their pace rises only to what can still be read.</summary>
    [Fact]
    public void The_long_night_climbs_without_a_ceiling_or_a_cliff()
    {
        var last = ArenaRun.Hardening(0);
        Assert.Equal((1.0, 1.0, 1.0), last);
        for (double m = 0.5; m <= 300; m += 0.5)
        {
            var h = ArenaRun.Hardening(m);
            Assert.True(h.Health > last.Health && h.Damage > last.Damage, $"flat at {m}");
            // No cliff: no minute more than a tenth harder than the one before.
            Assert.True(h.Damage / last.Damage < 1.1 && h.Health / last.Health < 1.1, $"a cliff at {m}");
            Assert.True(h.Pace <= 1.15);
            last = h;
        }
        // Two hours past the half hour, blows land many times as hard as at the half hour:
        // past what any armour, dodge or mending answers.
        Assert.True(ArenaRun.Hardening(120).Damage > 20);
    }

    /// <summary>Every five minutes past the win the dark swears one more of the table's
    /// oaths (its rule from then on, announced, listed), never one already sworn and never
    /// the moonless (the night must stay readable); out of them, it deepens.</summary>
    [Fact]
    public void The_dark_swears_an_oath_every_five_minutes_and_never_the_moonless()
    {
        var s = Make(Spec("pack", false, "iron"));
        s.B.Player.Iframes = 1e9;
        s.B.Time = 1800;
        Run(s, 1);
        Defeat(s);
        Assert.True(s.Zone.Won);
        double light = s.B.Rules.Light;
        for (int k = 1; k <= 11; k++)
        {
            s.B.Time += 300;
            Run(s, 0.2);
            Assert.Equal(k, s.Zone.DarkSworn);
        }
        var sworn = s.Host.Announced.Where(a => a.Kicker == "The long night").Select(a => a.Title).ToList();
        Assert.Contains("The dark swears the Oath of Embers", sworn);
        Assert.DoesNotContain(sworn, t => t.Contains("Iron") || t.Contains("Moonless"));
        Assert.Contains("The dark deepens", sworn);
        // Their rules hold from then on, and what they pay is paid.
        Assert.Equal(1.2, s.B.Rules.FoeSpeed, 3);
        Assert.True(s.B.Rules.DeathFire && s.B.Rules.HitChill && s.B.Rules.HitPoison);
        Assert.Equal(light, s.B.Rules.Light);
        Assert.True(s.B.Rules.EmberGain > 2);
    }

    /// <summary>What rules the people comes again every quarter hour past the win, its sign a
    /// minute before: its own fight, a part stronger each time, its chest a card richer; the
    /// arena stays won and goes on.</summary>
    [Fact]
    public void What_rules_them_comes_again_each_quarter_hour_stronger()
    {
        var s = Make(Spec());
        s.B.Player.Iframes = 1e9;
        s.B.Time = 1800;
        Run(s, 1);
        double first = Boss(s).MaxHp;
        Defeat(s);
        Assert.True(s.Zone.Won);
        s.B.Time += 900 - 70;
        Run(s, 12);
        Assert.Contains(s.Host.Announced, a => a.Title.EndsWith("stirs again"));
        Run(s, 60);
        Assert.Equal(1, s.Zone.Returns);
        var again = Boss(s);
        Assert.True(again.Boss);
        Assert.Equal(first * (1 + ArenaRun.ReturnGrowth), again.MaxHp, 0);
        Assert.Contains(s.Host.Announced, a => a.Kicker == "Again");
        int chests = s.B.Pickups.Items.Count(p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss");
        for (int i = 0; i < 400 && again.Alive && again.State != EnemyState.Dying; i++)
        {
            s.B.HitEnemy(again, again.MaxHp * 0.25, School.Physical, [Tag.Physical]);
            Run(s, 0.5);
        }
        Assert.Contains(s.Host.Announced, a => a.Title.EndsWith("is down again"));
        Assert.Null(s.Host.ArenaResult);
        Assert.True(s.B.Pickups.Items.Count(p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss") > chests);
    }

    /// <summary>An oath's pay in ember ("half again the ember") was never paid: the dead left
    /// the same stones under any oath.</summary>
    [Fact]
    public void An_oath_that_pays_in_ember_pays()
    {
        double Dropped(params string[] oaths)
        {
            var s = Make(Spec("pack", false, oaths));
            var wolf = s.B.SpawnEnemy("wolf", s.B.Player.X + 6, s.B.Player.Z, new Battle.SpawnOpts { Level = 1 })!;
            s.B.KillEnemy(wolf, true, null);
            return s.B.Pickups.Items.Where(p => p.Alive && p.Kind == PickupKind.Ember).Sum(p => p.Value);
        }
        Assert.Equal(Dropped() * 1.5, Dropped("swarm"), 3);
    }

    [Fact]
    public void The_ember_starts_again_from_nothing_whatever_is_carried()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
        j.Expedition = new Expedition { Hp = 50 };
        var s = Make(Spec(), j);
        Assert.True(s.B.EmberOn);
        Assert.Equal(1, s.B.EmberLevel);
        Assert.DoesNotContain(s.B.Boons, kv => kv.Value > 0 && Boons.IsGreat(kv.Key));
        // Whole, whatever the road took out of the survivor.
        Assert.Equal(s.B.MaxHp, s.B.Player.Hp);
        // And what is built in it stays in it (the wounds taken outside are still waiting).
        s.B.AddWeapon("knifestorm", 3);
        s.B.Player.Hp = 10;
        j.Capture(s.B);
        Assert.Equal(50, j.Expedition!.Hp);
    }

    [Fact]
    public void A_great_blessing_is_chosen_as_it_begins_and_another_at_the_fifteenth_minute()
    {
        var s = Make(Spec());
        Assert.True(LevelUp.GreatNext(s.B));
        var first = LevelUp.Draft(s.B, 3);
        Assert.Equal(3, first.Count);
        Assert.All(first, o => { Assert.True(o.Great); Assert.True(Boons.IsGreat(o.Id)); Assert.Equal(0, o.From); });
        LevelUp.Choose(s.B, first[0]);
        Assert.Equal(0, s.B.GreatOwed);
        Assert.False(s.B.DraftOwed);
        Assert.Equal(1, s.B.Boons[first[0].Id]);
        // A milestone never gives a new one.
        s.B.PendingBlessings.Add(4);
        for (int k = 0; k < 20; k++) Assert.DoesNotContain(LevelUp.Draft(s.B, 3), o => Boons.IsGreat(o.Id) && o.From == 0);
        s.B.PendingBlessings.Clear();
        // The fifteenth minute: a second, which may be the first deepened (the Kindling's minute
        // passed with its core left standing).
        s.B.Player.Iframes = 1e9;
        s.B.Time = 14.5 * 60;
        Run(s, 61);
        Assert.Equal(1, s.B.GreatOwed);
        Assert.Contains(s.Host.Announced, a => a.Title == "Halfway through the dark");
        bool deeper = false;
        for (int k = 0; k < 30 && !deeper; k++) deeper = LevelUp.Draft(s.B, 3).Any(o => o.Id == first[0].Id && o.To == 2 && o.Text.StartsWith("Rank 2:"));
        Assert.True(deeper);
    }

    /// <summary>The Kindling (docs/bosses/SURVIVORS_BOSSES.md 9): in the breath before the fifteenth
    /// minute an ember-core comes up, and beside it the ruler's own creature with a verb of its
    /// ruler's. Broken within the minute, the great blessing comes a card richer; the keeper carries
    /// a chest; the blessing is owed either way.</summary>
    [Theory]
    [InlineData("pack", "lt_pack")]
    [InlineData("dead", "lt_dead")]
    [InlineData("lamplings", "lt_lamplings")]
    [InlineData("kerchiefs", "lt_kerchiefs")]
    public void The_kindling_puts_a_core_and_the_rulers_keeper_before_the_great_blessing(string people, string keeperDef)
    {
        var s = Make(Spec(people));
        s.B.GreatOwed = 0;
        s.B.Player.Iframes = 1e9;
        s.B.Time = 14.5 * 60;
        Run(s, 0.2);
        var core = s.B.Enemies.Living().Single(e => e.Def.Id == "ember_core");
        var keeper = s.B.Enemies.Living().Single(e => e.Def.Id == keeperDef);
        Assert.Equal(keeper.MaxHp / 2, core.MaxHp, 3);
        Assert.Equal(0, s.B.GreatOwed);
        Assert.Contains(keeperDef, s.Zone.Creatures);
        // Broken in time: the blessing is owed, and a card richer.
        s.B.HitEnemy(core, core.MaxHp * 2, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Run(s, 0.2);
        Assert.Equal(1, s.B.GreatOwed);
        Assert.True(s.Zone.CoreBroken);
        int cards = LevelUp.Count(s.B);
        Assert.Equal(4, cards);
        // Left standing, it cools after its minute, and the blessing is the night's as it was.
        var t = Make(Spec(people));
        t.B.GreatOwed = 0;
        t.B.Player.Iframes = 1e9;
        t.B.Time = 14.5 * 60;
        Run(t, 61);
        Assert.Equal(1, t.B.GreatOwed);
        Assert.False(t.Zone.CoreBroken);
        Assert.DoesNotContain(t.B.Enemies.Living(), e => e.Def.Id == "ember_core");
        Assert.Equal(3, LevelUp.Count(t.B));
    }

    /// <summary>The boss's fall is the night's peak: the view is told (it slows the world and
    /// turns to it) and the people break and run. A story night then gives up its spoils and
    /// ends on its beat; a table night goes on into the long night.</summary>
    [Fact]
    public void The_fall_is_the_peak_and_a_story_night_ends_on_its_beat()
    {
        foreach (bool story in new[] { true, false })
        {
            var s = Make(Spec(story: story));
            s.B.Player.Iframes = 1e9;
            s.B.Time = 1800;
            Run(s, 1);
            bool fell = false;
            var boss = Boss(s);
            for (int i = 0; i < 400 && !s.Zone.Won; i++)
            {
                if (boss.Alive && boss.State != EnemyState.Dying) s.B.HitEnemy(boss, boss.MaxHp * 0.25, School.Physical, [Tag.Physical]);
                for (double t = 0; t < 0.5; t += 1 / 60.0)
                {
                    s.Zone.Step(1 / 60.0);
                    s.Zone.Frame(1 / 60.0);
                    s.B.Tick(1 / 60.0, 0, 0);
                    foreach (var ev in s.B.Events.Drain()) fell |= ev is Ev.Victory;
                    s.Host.Pass(1 / 60.0);
                }
            }
            Assert.True(s.Zone.Won);
            Assert.True(fell, "the fall was not told");
            var p = s.B.Player;
            Assert.Contains(s.B.Enemies.Living(), e => !e.Elite && e.Status.Has(StatusKind.Fear) && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) < 32 * 32);
            // The way out waits until the fall has landed; a story's night needs none.
            var way = s.Zone.Interactables.FirstOrDefault(i => i.Id == "way_out");
            if (story) Assert.Null(way);
            else Assert.False(way!.When!(), "the way out's prompt stood over the fall");
            Run(s, 8);
            Assert.Equal(story, s.Zone.Over);
            if (!story) Assert.True(way!.When!());
            if (story) Assert.True(s.Host.ArenaResult!.Won);
        }
    }

    /// <summary>At about six minutes the people ask their own question, with a tell first:
    /// for the Risen, the ground marked in a ring round the survivor and the dead coming up
    /// out of every mark at once, and a captain with a chest leading them.</summary>
    [Fact]
    public void The_people_ask_their_own_question_with_a_tell_first()
    {
        var s = Make(Spec("dead"));
        s.B.Player.Iframes = 1e9;
        // (Nothing of hers to kill them: the count is of what rises, not of what she mows.)
        foreach (var w in s.B.Weapons.ToList()) s.B.RemoveWeapon(w.Id);
        s.B.Time = 5.4 * 60;
        int marks = 0;
        for (double t = 0; t < 140 && !s.Barks.Contains("The ground cracks in a ring round you."); t += 1 / 60.0)
        {
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            foreach (var ev in s.B.Events.Drain())
            {
                if (ev is Ev.Bark bk) s.Barks.Add(bk.Text);
                if (ev is Ev.Telegraph { Kind: TelegraphKind.Ground }) marks++;
            }
            s.Host.Pass(1 / 60.0);
        }
        Assert.Contains("The ground cracks in a ring round you.", s.Barks);
        Assert.True(marks >= 10, $"{marks} marks");
        var p = s.B.Player;
        int Near() => s.B.Enemies.Living().Count(e => e.Def.Id.StartsWith("risen") && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) < 12 * 12);
        int before = Near();
        Run(s, 1.6);
        Assert.True(Near() >= before + 8, $"{before} then {Near()} risen within twelve paces");
        Assert.Contains(s.B.Enemies.Living(), e => e.Elite);
    }

    [Fact]
    public void Under_the_oath_of_champions_they_come_two_at_a_time()
    {
        var s = Make(Spec("pack", false, "champions"));
        s.B.Player.Iframes = 1e9;
        s.B.Time = 240;
        // From the eighth minute a champion's turn comes in every three (ArenaPacing).
        for (int i = 0; i < 16 && !s.Barks.Contains("Champions of the Pack: they carry something."); i++) Run(s, 30);
        Assert.Contains("Champions of the Pack: they carry something.", s.Barks);
        Assert.True(s.B.Enemies.Living().Count(e => e.Elite) >= 2);
    }

    [Fact]
    public void The_horde_thickens_with_the_minutes()
    {
        var s = Make(Spec());
        s.B.Player.Iframes = 1e9;
        Run(s, 20);
        int early = Hostile(s.B);
        Assert.InRange(early, 10, 60);
        // Ten minutes on: more of them, stronger, the tuskers among them, and a herald.
        s.B.Time = 600;
        foreach (var e in s.B.Enemies.Living().ToList()) s.B.KillEnemy(e, false, null);
        Run(s, 25);
        Assert.True(Hostile(s.B) > early * 2, $"{early} then {Hostile(s.B)}");
        Assert.Contains(s.B.Enemies.Living(), e => e.Def.Id == "boar");
        Assert.Contains(s.Host.Announced, a => a.Title.StartsWith("Herald"));
        Assert.True(s.B.Enemies.Living().Max(e => e.Level) > 1);
    }

    [Fact]
    public void Events_come_in_turn_and_a_champion_carries_a_chest()
    {
        var s = Make(Spec());
        s.B.Player.Iframes = 1e9;
        // Nothing is drafted here, so only a chest can rank anything up.
        int Ranks() => s.B.Weapons.Sum(w => w.Rank) + s.B.Boons.Values.Sum();
        int ranks = Ranks();
        s.B.Time = 240;
        // From the eighth minute a champion's turn comes in every three (ArenaPacing).
        for (int i = 0; i < 18 && !s.Barks.Any(b => b.StartsWith("A champion of")); i++) Run(s, 30);
        Assert.Contains(s.Barks, b => b.StartsWith("A champion of"));
        // Every champion still standing falls, and every chest is walked to.
        foreach (var e in s.B.Enemies.Living().Where(e => e.Elite).ToList()) s.B.HitEnemy(e, 1e9, School.Physical, [Tag.Physical]);
        Run(s, 0.2);
        foreach (var c in s.B.Pickups.Living().Where(p => p.Kind == PickupKind.Chest).ToList()) { c.X = s.B.Player.X; c.Z = s.B.Player.Z; c.Pulled = true; }
        Run(s, 1);
        Assert.Contains(s.Host.Announced, a => a.Title == "A chest");
        Assert.True(Ranks() > ranks);
    }

    [Fact]
    public void At_the_half_hour_the_boss_comes_and_killing_it_wins_and_the_arena_goes_on()
    {
        var s = Make(Spec());
        s.B.Player.Iframes = 1e9;
        s.B.AddWeapon("seeking_motes", 2);
        s.B.AddBoon("might");
        s.B.Time = 1800;
        Run(s, 1);
        Assert.NotNull(s.Host.Boss);
        int level = s.J.Ch.Level;
        Defeat(s);
        Run(s, 4);
        // Won, and the story told so at once; but nothing is over.
        Assert.True(s.Zone.Won);
        Assert.True(s.J.World.Fact("test.won").Truthy);
        Assert.Equal("won", s.J.World.Fact($"arena.{s.Spec.Id}").Str);
        Assert.Null(s.Host.ArenaResult);
        Assert.NotNull(s.J.World.Arena);
        Assert.Contains(s.Host.Announced, a => a.Kicker == "Victory");
        // It goes on, and harder: more of them, and tougher than they were.
        s.B.Time = 1800 + 20 * 60;
        foreach (var e in s.B.Enemies.Living().ToList()) s.B.KillEnemy(e, false, null);
        Run(s, 15);
        Assert.True(Hostile(s.B) > 60);
        var wolf = s.B.Enemies.Living().First(e => e.Def.Id == "wolf" && !e.Elite);
        Assert.True(wolf.MaxHp > Enemies.Get("wolf").Health * 4, $"{wolf.MaxHp}");
        // The long night: the dark swears its oaths, and a herald or what rules them comes again.
        Assert.Contains(s.Host.Announced, a => a.Title.StartsWith("Herald") || a.Kicker?.StartsWith("Again") == true);
        Assert.Contains(s.Host.Announced, a => a.Kicker == "The long night");
        // Out by the way that opened where the boss fell.
        var way = s.Zone.Interactables.Single(i => i.Id == "way_out");
        way.Act();
        Run(s, 1);
        var r = s.Host.ArenaResult;
        Assert.NotNull(r);
        Assert.True(r!.Won);
        Assert.True(r.Seconds > 1800 + 20 * 60);
        Assert.Equal(Arenas.XpFor(s.Spec, r.Seconds, true), r.Xp);
        Assert.True(s.J.Ch.Level > level);
        Assert.Contains("seeking_motes", s.J.Ch.Discovered);
        // Only combat skills are discovered (only they can be learned by day).
        Assert.DoesNotContain("might", s.J.Ch.Discovered);
        Assert.Contains("seeking_motes", r.Discovered);
        Assert.Null(s.J.World.Arena);
        Assert.True(s.J.World.Fact("arena.longest").Number > 50);
    }

    /* -------------------------------------------- the night's stretches -- */

    /// <summary>The owner: mechanics "don't appear till certain mini bosses and minion types show
    /// up". The Pack's tuskers do not run in the horde until Old Tusk has come, named, his lesson
    /// said; then they do.</summary>
    [Fact]
    public void The_tuskers_come_only_after_Old_Tusk_has_shown_them()
    {
        var s = Make(Spec("pack"));
        s.B.Player.Iframes = 1e9;
        s.B.Time = 2.6 * 60;
        bool boarBefore = false;
        for (double t = 0; t < 90 && !s.Host.Announced.Any(a => a.Title == "Old Tusk"); t += 1)
        {
            Run(s, 1);
            // (He comes with a few of his own beside him: those count from his coming.)
            if (!s.Host.Announced.Any(a => a.Title == "Old Tusk")) boarBefore |= s.B.Enemies.Living().Any(e => e.Def.Id == "boar");
        }
        Assert.False(boarBefore);
        var came = s.Host.Announced.Single(a => a.Title == "Old Tusk");
        Assert.Equal(Enemies.Get("mb_old_tusk").Lesson, came.Sub);
        Assert.Contains(s.B.Enemies.Living(), e => e.Def.Id == "mb_old_tusk" && e.Elite);
        // Its bar, as a herald's, and then its kind in the crowd.
        Run(s, 1);
        Assert.Equal("Old Tusk", s.Host.Boss?.Name);
        Run(s, 40);
        Assert.Contains(s.B.Enemies.Living(), e => e.Def.Id == "boar" && !e.Elite);
    }

    /// <summary>Champions from the second tier wear their people's Signs: named for them,
    /// coloured, with the verb.</summary>
    [Fact]
    public void A_champions_turn_brings_a_signed_champion_from_the_second_tier()
    {
        var spec = Spec("dead");
        spec.Tier = 2;
        var s = Make(spec);
        s.B.Player.Iframes = 1e9;
        s.B.Time = 8 * 60;
        for (int i = 0; i < 16 && !s.B.Enemies.Living().Any(e => e.Elite && e.Def.Signs.Length > 0); i++) Run(s, 30);
        var champ = s.B.Enemies.Living().First(e => e.Elite && e.Def.Signs.Length > 0);
        Assert.Contains(Signs.Get(champ.Def.Signs[0]).Name, champ.Def.Name);
        Assert.NotNull(champ.Def.Tint);
    }

    /// <summary>Crafting's measure: the Kerchiefs' horde paid tens of thousands of gold a night and
    /// the crowd's champions hundreds of pieces of gear. Now the rank and file drop a three-hundredth
    /// of their gold and champions a tenth, and gear comes only from what carries a chest.</summary>
    [Fact]
    public void An_arenas_horde_pays_a_little_gold_and_its_crowd_champions_no_gear()
    {
        var s = Make(Spec("kerchiefs"));
        var b = s.B;
        int gold = 0, items = 0;
        for (int i = 0; i < 400; i++)
        {
            var e = b.SpawnEnemy("footpad", b.Player.X + 30, b.Player.Z, new Battle.SpawnOpts { Elite = i % 20 == 0 })!;
            b.KillEnemy(e, true, null);
        }
        foreach (var k in b.Pickups.Living()) { if (k.Kind == PickupKind.Gold) gold++; if (k.Kind == PickupKind.Item) items++; }
        // 380 footpads and 20 champions at the day's rate would drop about 220 purses: now a
        // three-hundredth of the crowd's and a tenth of the champions', one or two.
        Assert.InRange(gold, 0, 8);
        Assert.Equal(0, items);
    }

    /// <summary>The story's nights are twenty minutes: the same night told quicker. Its boss comes at
    /// the twentieth minute, the ember comes half again as fast, and when the boss falls the night
    /// is over: no long night after it, its people drawing back.</summary>
    [Fact]
    public void A_story_night_is_twenty_minutes_and_ends_on_its_boss()
    {
        var spec = Spec(story: true);
        spec.Minutes = 20;
        var s = Make(spec);
        s.B.Player.Iframes = 1e9;
        s.B.AddWeapon("seeking_motes", 2);
        s.B.AddBoon("might");
        Assert.Equal(1.5, s.B.Rules.EmberGain, 6);
        s.B.Time = 19.99 * 60;
        Run(s, 1);
        Assert.NotNull(s.Host.Boss);
        Assert.Contains(s.Host.Announced, a => a.Kicker == "The dead of night");
        Defeat(s);
        Assert.True(s.Zone.Won);
        Assert.Equal(1.0, s.B.Rules.EmberGain, 6);
        Run(s, 6 * 60 + 30);
        Assert.DoesNotContain(s.Host.Announced, a => a.Kicker == "The long night");
        Assert.True(Hostile(s.B) < 20, $"{Hostile(s.B)} still in the field");
    }

    [Fact]
    public void Fallen_after_the_win_it_is_still_won()
    {
        var s = Make(Spec(story: true));
        s.B.Player.Iframes = 1e9;
        s.B.Time = 1800;
        Run(s, 1);
        Defeat(s);
        Run(s, 1);
        Assert.True(s.Zone.OnDeath("a wolf"));
        Run(s, 3);
        var r = s.Host.ArenaResult!;
        Assert.True(r.Won);
        Assert.False(s.J.World.Fact("test.lost").Truthy);
        Assert.Empty(s.J.World.Rematches);
        Assert.Equal("won", s.J.World.Fact($"arena.{s.Spec.Id}").Str);
    }

    [Fact]
    public void What_brought_her_down_is_named_as_a_sentence_names_it()
    {
        // "Brought down by a Kerchief Footpad at 12:30": one of a kind takes an article, a name does not.
        Assert.Equal("a Kerchief Footpad", Enemies.Called(null, "Kerchief Footpad"));
        Assert.Equal("an Ironbound Risen", Enemies.Called(null, "Ironbound Risen"));
        Assert.Equal("Whitethroat", Enemies.Called("Whitethroat", "Whitethroat"));
        Assert.Equal("the Pack-Mother", Enemies.Called("The Pack-Mother", "The Pack-Mother"));
        Assert.Equal("the Herald of the Pack", Enemies.Called("Herald of the Pack", "Longtooth Wolf"));
        Assert.Equal("a babbling lampling", Enemies.Called("A babbling lampling", "Lampling Tunneler"));
        Assert.Equal("the Pack-Mother", MapOffers.InSentence("The Pack-Mother"));
    }

    [Fact]
    public void The_town_can_talk_about_the_last_night()
    {
        var s = Make(Spec("kerchiefs"));
        s.B.Time = 12.5 * 60;
        s.B.Player.Alive = false;
        s.Zone.OnDeath("a Kerchief Bruiser");
        Run(s, 3);
        var w = s.J.World;
        Assert.Equal("kerchiefs", w.Fact("arena.last.people").Str);
        Assert.False(w.Fact("arena.last.won").Truthy);
        Assert.True(w.Fact("arena.last.fell").Truthy);
        Assert.Equal("a Kerchief Bruiser", w.Fact("arena.last.killer").Str);
        Assert.Equal(12.5, w.Fact("arena.last.minutes").Number, 1);
        Assert.Equal(1, w.Fact("arena.nights").Number);
        Assert.Equal(1, w.Fact("arena.fell").Number);
    }

    [Fact]
    public void Falling_keeps_what_was_earned_and_a_story_fight_waits_to_be_taken_again()
    {
        var s = Make(Spec(story: true));
        s.B.Time = 540;
        s.B.GoldGained = 40;
        double gold = s.J.Ch.Gold;
        // There is no way out before the win.
        s.Zone.Leave();
        Assert.False(s.Zone.Over);
        Assert.True(s.Zone.OnDeath("a wolf"));
        Run(s, 3);
        var r = s.Host.ArenaResult!;
        Assert.False(r.Won);
        Assert.InRange(r.Xp, 200, 400);
        Assert.Equal(gold + 40, s.J.Ch.Gold);
        Assert.True(s.J.World.Fact("test.lost").Truthy);
        Assert.Single(s.J.World.Rematches, x => x.Id == "hollow_teeth");
        // Taken again from the table and won, it is gone from it (and a second loss would tell the story nothing).
        var again = Arenas.Again(s.J.World.Rematches[0], "waystation", 1, 2, 0);
        Assert.Null(again.OnLose);
        Assert.NotNull(again.OnWin);
        // Its lost line says where she comes to, and a rematch sends her back to the table instead.
        Assert.Null(again.EndLost);
        var next = Make(again, s.J);
        next.B.Player.Iframes = 1e9;
        next.B.Time = 1800;
        Run(next, 1);
        Defeat(next);
        Run(next, 1);
        Assert.Empty(s.J.World.Rematches);
        Assert.True(s.J.World.Fact("test.won").Truthy);
    }

    [Fact]
    public void Kills_in_an_arena_teach_nothing_until_it_is_over()
    {
        var s = Make(Spec());
        double xp = s.J.Ch.Xp;
        int level = s.J.Ch.Level;
        var w = s.B.SpawnEnemy("wolf", 5, 5)!;
        s.J.Killed(w, true);
        Assert.Equal(xp, s.J.Ch.Xp);
        Assert.Equal(level, s.J.Ch.Level);
    }

    /// <summary>A night opens close on the survivor, so she is seen, and the camera stands back
    /// as the horde grows, so the fight is; the boss is framed from further still.</summary>
    [Fact]
    public void The_camera_opens_close_and_stands_back_as_the_horde_grows()
    {
        var s = Make(Spec());
        s.B.Player.Iframes = 1e9;
        Run(s, 10);
        Assert.InRange(s.Zone.CameraDistance, 22, 24);
        s.B.Time = 22 * 60;
        Run(s, 40);
        Assert.True(Hostile(s.B) > 90, $"{Hostile(s.B)} alive");
        Assert.InRange(s.Zone.CameraDistance, 24.5, 31);
    }

    [Fact]
    public void Nothing_carries_the_survivor_out_of_the_arena()
    {
        var s = Make(Spec());
        Assert.NotNull(s.B.InBounds);
        Assert.False(s.B.InBounds!(140, 0));
        // It opens close on the survivor; the camera pulls back as the horde grows (CameraDistance).
        Assert.Equal((64.0, 22.0), s.Zone.Camera);
    }
}
