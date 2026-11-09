using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>One night on the Low Ford road, without a screen (Play/Zones/Prologue.cs).</summary>
public class PrologueTests
{
    sealed record Setup(Journey J, FakeHost Host, Prologue Zone, Battle B, ZoneMeta Meta);

    static Setup Make(bool draft = false)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta) { Draft = draft };
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5, ember: zone.Ember);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, meta);
    }

    [Fact]
    public void The_shut_gate_drops_its_portcullis_and_raises_it_once_the_ring_is_down()
    {
        // (H8 N22, the judge on the N22 frames: "the arch looks open ... the player walks into an invisible wall")
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta) { DayStart = true };
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5, ember: zone.Ember);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        var s = new Setup(j, host, zone, b, meta);
        Run(s, 0.1);
        // The day starts shut: the portcullis down at once (never seen up), the bar on its line, a watchman behind it.
        Assert.Equal(1, host.FakeLook.Moved["portcullis"]);
        var spec = Play.Zones.Encounters.For("lowford")!;
        var bar = Assert.Single(b.Collision.All(), c => c.Tag == "gate_shut");
        Assert.InRange(bar.Z, spec.PortcullisZ, spec.PortcullisZ + 0.6);
        Run(s, 12);
        Assert.Equal(Prologue.Stage.Exit, zone.Now);
        // Up to the bars, past the exit line: held, told why, and the tracker names the task in one line.
        var gate = meta.Place("LOWFORD", "gate");
        // (by the wall's side of the apron, off the ring's line: the ring is not sprung, still owed)
        double exitZ = meta.Places["LOWFORD"].GetProperty("exitZ").GetDouble();
        Stand(s, gate.X + 8.7, exitZ - 1);
        Run(s, 0.2);
        Assert.False(j.World.Fact("prologue.done").Truthy);
        var steps = host.Tracked.Single(t => t.Id == "pro").Steps;
        Assert.Equal(Prologue.GateTask, steps[0].Text);
        Assert.DoesNotContain(steps, x => x.Text.StartsWith("Walk up the road"));
        Assert.Equal(1, host.FakeLook.Moved["portcullis"]);
        // (near the gate the goal's line takes the first line's place, in the same words: one line, not two)
        var ring = Goals.All.Single(g => g.Id == "day_ring");
        var merged = Goals.Merge(host.Tracked, [new ActiveGoal(ring, 0, 0, 0, true)], _ => null).Single(t => t.Id == "pro").Steps;
        Assert.Equal(steps.Count, merged.Count);
        Assert.Equal(Prologue.GateTask, merged[0].Text);
        // The ring down: the portcullis rises over a few seconds, eased; she goes through once it is most of the way up.
        j.World.Zone("lowford")[Play.Zones.Encounters.DoneKey("wolves")] = true;
        Stand(s, gate.X, exitZ - 1);
        Run(s, 1.0);
        Assert.InRange(host.FakeLook.Moved["portcullis"], 0.3, 0.95);
        Assert.False(j.World.Fact("prologue.done").Truthy);
        Run(s, 2.0);
        Assert.Equal(0, host.FakeLook.Moved["portcullis"]);
        Assert.DoesNotContain(b.Collision.All(), c => c.Tag == "gate_shut");
        Assert.True(j.World.Fact("prologue.done").Truthy);
    }

    static void Run(Setup s, double seconds, bool safe = true)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            if (safe) { s.B.Player.Hp = s.B.MaxHp; }
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            s.B.Events.Drain();
            s.Zone.Frame(1 / 60.0);
            s.Host.Pass(1 / 60.0);
        }
    }

    static void Stand(Setup s, double x, double z) { s.B.Player.X = x; s.B.Player.Z = z; }

    [Fact]
    public void The_night_starts_by_the_fire_and_the_dead_rise()
    {
        // (the draft on: encounters.json's lowford "draft": true plays the night's cards as before M5)
        var s = Make(draft: true);
        Assert.Same(Atmospheres.LowFordNight, s.Host.Air);
        Assert.Equal("Survive the night", s.Host.Tracked.Single().Steps[0].Text);
        // The night's: the ember burns here.
        Assert.True(s.B.EmberOn);
        Run(s, 12);
        Assert.Equal(Prologue.Stage.Rising, s.Zone.Now);
        Assert.True(s.B.Enemies.Living().Count() > 3);
        Assert.Equal("move", s.Host.CurrentHint?.Id ?? "move");
        // The first rise of the ember brings its first card alone; the great blessing comes on its own
        // panel later (au1 item 2).
        s.B.GainEmber(s.B.EmberNext);
        Run(s, 0.1);
        Assert.False(LevelUp.GreatNext(s.B));
        Assert.True(s.B.DraftOwed);
        Assert.NotNull(s.Host.DraftTip);
    }

    /// <summary>Puts a night beat's foes down (as she would), and lets the night see it.</summary>
    static void KillPack(Setup s, string id)
    {
        // (a gated pack rises when the beat it waits on has been down its breather, After: let the clock run it)
        for (int i = 0; i < 60 && s.Zone.Night!.Pending(id); i++) Run(s, 0.5);
        foreach (var e in s.Zone.Night!.Standing(id)) s.B.KillEnemy(e, true, null);
        Run(s, 0.1);
        Assert.True(s.Zone.Night.Done(id));
    }

    /// <summary>The Rising's beats down, the first pack at the wagon's approach down, and her at the wagon.</summary>
    static void ToTheCart(Setup s)
    {
        Run(s, 4);
        Assert.Equal(Prologue.Stage.Rising, s.Zone.Now);
        KillPack(s, "n_lone");
        KillPack(s, "n_three");
        Assert.Equal(Prologue.Stage.Road, s.Zone.Now);
        KillPack(s, "n_first");
        var cart = s.Meta.Place("LOWFORD", "cart");
        Stand(s, cart.X, cart.Z + 5);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Ambush, s.Zone.Now);
    }

    [Fact]
    public void The_Rising_ends_when_its_beats_are_down_not_on_a_clock()
    {
        var s = Make();
        Run(s, 4);
        Assert.Equal(Prologue.Stage.Rising, s.Zone.Now);
        // (no top-up: standing by the fire, the clearing does not fill, and the Rising waits on its beats)
        int placed = s.B.Enemies.Living().Count();
        Run(s, 120);
        Assert.Equal(Prologue.Stage.Rising, s.Zone.Now);
        Assert.True(s.B.Enemies.Living().Count() <= placed + 3);  // (+ the three, laid once the lone one is down)
        KillPack(s, "n_lone");
        Assert.Equal(Prologue.Stage.Rising, s.Zone.Now);
        KillPack(s, "n_three");
        Assert.Equal(Prologue.Stage.Road, s.Zone.Now);
        // (or she walks 20 m up the road)
        var t = Make();
        Run(t, 4);
        var camp = t.Meta.Place("LOWFORD", "camp");
        Stand(t, 0, camp.Z - 1.5 - 20.2);
        Run(t, 0.1);
        Assert.Equal(Prologue.Stage.Road, t.Zone.Now);
    }

    [Fact]
    public void With_the_draft_off_the_night_teaches_experience_and_the_dawn_takes_nothing()
    {
        var s = Make();
        Assert.False(s.Zone.Draft);
        Assert.False(s.Zone.Ember);
        Assert.False(s.B.EmberOn);
        Assert.Null(s.Host.DraftTip);
        // (the Flare at half, as the night started it, for the Warden's lamps)
        Assert.NotNull(s.B.Flare);
        Assert.True(s.B.FlareMeter >= Battle.FlareFull / 2 - 1e-6);
        Run(s, 4);
        double xp = s.J.Ch.Xp; int level = s.J.Ch.Level;
        foreach (var id in new[] { "n_lone", "n_three", "n_first" })
        {
            for (int i = 0; i < 60 && s.Zone.Night!.Pending(id); i++) Run(s, 0.5);
            foreach (var e in s.Zone.Night!.Standing(id)) { s.B.KillEnemy(e, true, null); s.J.Killed(e, true); }
            Run(s, 0.1);
        }
        Run(s, 1);
        Assert.False(s.B.DraftOwed);
        Assert.Equal(0, s.B.GreatOwed);
        Assert.Equal(0, s.J.World.NightLessons);
        Assert.True(s.J.Ch.Xp > xp || s.J.Ch.Level > level);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id is "ember_bar" or "first_draft" or "first_skill" or "great_blessing");
        // The dawn's douse takes and pays nothing the night did not lend: her skills and her level stay, no card.
        var weapons = s.B.Weapons.Select(w => (w.Id, w.Rank)).ToList();
        level = s.J.Ch.Level;
        typeof(Prologue).GetMethod("Douse", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(s.Zone, [true]);
        Run(s, 2);
        Assert.Equal(weapons, s.B.Weapons.Select(w => (w.Id, w.Rank)).ToList());
        Assert.Equal(level, s.J.Ch.Level);
        Assert.Empty(s.Host.Dawns);
    }

    [Fact]
    public void With_the_draft_on_the_nights_kills_rise_the_ember_and_wait_for_dawn()
    {
        var s = Make(draft: true);
        Assert.True(s.B.EmberOn);
        Assert.NotNull(s.Host.DraftTip);
        Run(s, 4);
        double xp = s.J.Ch.Xp;
        s.B.GainEmber(s.B.EmberNext);
        // (her own fire takes the lone one in the first seconds; the three rise out of the road 4 s after it)
        for (int i = 0; i < 60 && (s.Zone.Night!.Pending("n_three") || s.Zone.Night.Standing("n_three").Count == 0); i++) Run(s, 0.5);
        Assert.NotEmpty(s.Zone.Night!.Standing("n_three"));
        foreach (var e in s.Zone.Night.Standing("n_three")) { s.B.KillEnemy(e, true, null); s.J.Killed(e, true); }
        Run(s, 0.1);
        Assert.True(s.B.DraftOwed);
        Assert.Equal(xp, s.J.Ch.Xp);
        Assert.True(s.J.World.NightLessons > 0);
    }

    [Fact]
    public void The_wagon_is_quiet_until_its_line_is_read_then_a_volley_asks_for_the_dash()
    {
        var s = Make();
        ToTheCart(s);
        // The Road's beat (au i15): coins spilled from the wagon, and the ditch still quiet.
        Assert.True(s.B.Pickups.Living().Count(k => k.Kind == PickupKind.Gold) >= 3);
        // (its line after the road's and the night's opening captions, M5: the Rising is short now)
        for (int i = 0; i < 300 && !s.Host.Said.Any(l => l.StartsWith("A wagon on its side")); i++) Run(s, 0.1);
        Assert.Contains(s.Host.Said, l => l.StartsWith("A wagon on its side"));
        Assert.False(s.Zone.Sprung);
        // The ditch rises once its line is read.
        Run(s, 6);
        Assert.True(s.Zone.Sprung);
        Assert.True(s.B.Enemies.Living().Count(e => e.Def.Id == "risen_archer") >= 3);
        // Their first volley in the air at her asks for the dash, briefly (never late, after it lands).
        Run(s, 4);
        var dash = s.Host.Asked.FirstOrDefault(c => c.Id == "dash");
        Assert.NotNull(dash);
        Assert.True(dash!.Patience < 1);
    }

    [Fact]
    public void Two_bowmen_who_keep_their_range_do_not_hold_the_wagon_for_good()
    {
        // (m5 clip r1: the game's autopilot circled the wagon, two of its bowmen kept off her, and the night stood at
        // the Ambush for nine minutes; a player who will not chase them is not held there either)
        var s = Make();
        ToTheCart(s);
        for (int i = 0; i < 400 && !s.Zone.Sprung; i++) Run(s, 0.1);
        Assert.True(s.Zone.Sprung);
        var left = s.Zone.Night!.Standing("n_cart").Where(e => e.Def.Id == "risen_archer").Take(2).ToList();
        Assert.Equal(2, left.Count);
        foreach (var e in s.Zone.Night.Standing("n_cart").Except(left)) s.B.KillEnemy(e, true, null);
        foreach (var e in left) e.Hp = e.MaxHp = 1e9;
        var leftSeeds = left.Select(e => e.Seed).ToList();
        Run(s, 10);
        Assert.Equal(Prologue.Stage.Ambush, s.Zone.Now);
        Run(s, 25);
        Assert.Equal(Prologue.Stage.Road2, s.Zone.Now);
        Assert.True(s.Zone.Night.Done("n_cart"));
        // (the pool hands a fallen foe's slot to the next pack that rises, n_road1: a slot is the same foe only while its Seed holds)
        Assert.All(left.Zip(leftSeeds), x => Assert.False(x.First.Seed == x.Second && x.First.Alive && x.First.State != EnemyState.Dying));
    }

    [Fact]
    public void The_road_runs_from_the_clearing_to_the_ford()
    {
        var s = Make();
        ToTheCart(s);
        // (the wagon's line read, the ditch risen; over when its dead are down, n_cart)
        for (int i = 0; i < 400 && !s.Zone.Sprung; i++) Run(s, 0.1);
        Assert.True(s.Zone.Sprung);
        Assert.Equal(Prologue.Stage.Ambush, s.Zone.Now);
        KillPack(s, "n_cart");
        Assert.Equal(Prologue.Stage.Road2, s.Zone.Now);
        var post = s.Meta.Place("LOWFORD", "post");
        Stand(s, post.X - 6, post.Z + 4);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Post, s.Zone.Now);
        var knight = s.B.Enemies.Living().Single(e => e.Tag == "knight");
        Assert.NotNull(s.Zone.Interactables.Single(i => i.Id == "chest").Locked!());
        s.B.KillEnemy(knight, true, null);
        var chest = s.Zone.Interactables.Single(i => i.Id == "chest");
        Assert.Null(chest.Locked!());
        chest.Act();
        Assert.Contains(s.J.Ch.Pack, p => p?.Def == "padded_jerkin");
        Stand(s, 0, 18);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Barrow, s.Zone.Now);
        s.B.KillEnemy(s.B.Enemies.Living().Single(e => e.Tag == "caller"), true, null);
        Run(s, 1.2);
        Assert.Equal(Prologue.Stage.ToFord, s.Zone.Now);
    }

    [Fact]
    public void The_Ford_Warden_holds_at_his_floor_until_two_lamps_are_broken()
    {
        // (H8, N20, the owner on demo-rc2: "the warden was easy. died in like 8 seconds didn't have to crash a lamp")
        var s = Make();
        var ford = s.Meta.Place("LOWFORD", "ford");
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(s.Zone, [Prologue.Stage.ToFord]);
        Stand(s, ford.X, ford.Z + 12);
        Run(s, 0.1);
        Run(s, 7);
        Assert.Equal(Prologue.Stage.Boss, s.Zone.Now);
        var warden = s.B.Enemies.Living().Single(e => e.Tag == "warden");
        var fw = Teeth.Ford!;
        Assert.Equal(2600 * fw.HpMul, warden.MaxHp, 0);
        void Pound() { for (int i = 0; i < 40; i++) { s.B.HitEnemy(warden, 5000, School.Physical, []); Run(s, 0.02); } }
        Pound();
        Assert.True(warden.Alive);
        Assert.InRange(warden.Hp / warden.MaxHp, fw.Floors[3] - 0.01, fw.Floors[3] + 0.05);
        // One lamp broken: down to the next floor, no further.
        var p0 = s.Meta.Colliders.First(c => c.Tag == "pylon:0");
        s.Zone.Hooks.OnHitProp!("pylon:0", p0.Id, School.Physical, 300, p0.X, p0.Z);
        Pound();
        Assert.True(warden.Alive);
        Assert.InRange(warden.Hp / warden.MaxHp, fw.Floors[2] - 0.01, fw.Floors[2] + 0.05);
        // Two broken: he can fall (after the backstop's minute).
        var p1 = s.Meta.Colliders.First(c => c.Tag == "pylon:1");
        s.Zone.Hooks.OnHitProp!("pylon:1", p1.Id, School.Physical, 300, p1.X, p1.Z);
        Run(s, fw.MinSeconds);
        if (warden.Alive) Pound();
        Assert.False(warden.Alive);
    }

    [Fact]
    public void The_first_Ford_Warden_kill_leaves_one_certain_Legendary_and_sets_the_world_fact()
    {
        // (ARPG 7.1: "1, certain, from the Ford-Warden"; the early pool has Legendaries from level 1-3)
        int Legends(Setup s) => s.B.Pickups.Living().Count(k => k.Kind == PickupKind.Item && k.Loot == (int)LootTier.Legendary);
        foreach (int level in new[] { 3, 4 })
        {
            var s = Make();
            Assert.False(s.J.World.Fact(Prologue.WardenLegendaryFact).Truthy);
            var e = s.B.SpawnEnemy("wolf", s.B.Player.X + 3, s.B.Player.Z + 3, new Battle.SpawnOpts { Level = level })!;
            s.Zone.WardenLegendary(e);
            Assert.True(s.J.World.Fact(Prologue.WardenLegendaryFact).Truthy);
            Assert.True(Legends(s) >= 1, $"no Legendary at level {level}");
            // (a second kill rolls the plain Boss source: the fact stays, the certainty is spent)
            int before = Legends(s);
            s.Zone.WardenLegendary(e);
            Assert.True(s.J.World.Fact(Prologue.WardenLegendaryFact).Truthy);
            Assert.True(Legends(s) - before <= 1);
        }
    }

    [Fact]
    public void The_warden_wakes_behind_its_lamps_falls_and_the_gate_opens_at_dawn()
    {
        // (the draft on: the dawn takes what the ember lent)
        var s = Make(draft: true);
        var ford = s.Meta.Place("LOWFORD", "ford");
        // Straight to the ford.
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(s.Zone, [Prologue.Stage.ToFord]);
        Stand(s, ford.X, ford.Z + 12);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Intro, s.Zone.Now);
        Assert.True(s.Host.Captured);
        Assert.NotNull(s.Host.Held);
        Run(s, 7);
        Assert.Equal(Prologue.Stage.Boss, s.Zone.Now);
        Assert.False(s.Host.Captured);
        var warden = s.B.Enemies.Living().Single(e => e.Tag == "warden");
        // What the night built: a card or two, a blessing.
        s.B.AddWeapon("knifestorm", 4);
        s.B.AddBoon("stormborn");
        s.B.GainEmber(s.B.EmberNext * 2);
        Run(s, 0.5);
        // Three lamps: most of every blow goes to them.
        Assert.Equal(0.4, warden.TakenMul, 3);
        Assert.True(s.Host.Boss!.Shielded);
        // Break a lamp.
        var pylon = s.Meta.Colliders.First(c => c.Tag == "pylon:0");
        s.Zone.Hooks.OnHitProp!("pylon:0", pylon.Id, School.Physical, 300, pylon.X, pylon.Z);
        Assert.Equal(2, s.Zone.LitCount);
        s.B.KillEnemy(warden, true, null);
        Assert.Equal(Prologue.Stage.Victory, s.Zone.Now);
        Assert.Equal(0, s.Zone.LitCount);
        // (M5 r2: the first Legendary's beat holds the narration about 5.7 s; M5 r4: the heart's beat waits for her to take
        // the Legendary, up to LegendWaitMax)
        Run(s, 12);
        Assert.Equal(Prologue.Stage.Victory, s.Zone.Now);
        var legends = s.B.Pickups.Living().Where(k => k.Loot is (int)LootTier.Legendary or (int)LootTier.Storied).ToList();
        Assert.NotEmpty(legends);
        Assert.DoesNotContain(s.B.Pickups.Living(), k => k.Ref == "wardens_lampiron");
        foreach (var l in legends) s.B.Pickups.Release(l);
        Run(s, 13.5);
        Assert.Equal(Prologue.Stage.Dawn, s.Zone.Now);
        Assert.Equal(TimeOfDay.Dawn, s.J.World.Time);
        Assert.Contains(s.J.World.History, h => h.Id == "ford_warden_slain");
        Assert.DoesNotContain(s.B.Collision.All(), c => c.Tag == "gate");
        // The sun comes up and the ember goes out, and all it built: the survivor
        // has what they carry.
        Assert.True(s.B.EmberOn);
        Run(s, 4);
        Assert.False(s.B.EmberOn);
        Assert.Equal(1, s.B.EmberLevel);
        Assert.Empty(s.B.Boons);
        Assert.Equal(Character.Kit(s.J.Ch).Weapons.Select(w => w.Id), s.B.Weapons.Select(w => w.Id));
        // (said on the dawn's card, held until a click: N24; no banner and no caption say it again)
        var dawn = Assert.Single(s.Host.Dawns);
        Assert.Equal("The ember goes out", dawn.Title);
        Assert.Contains("The Lamps' light", dawn.Takes);
        Assert.DoesNotContain(s.Host.Announced, a => a.Title == "The ember goes out");
        Assert.DoesNotContain(s.Host.Said, l => l.Contains("the ember goes out of you"));
        Run(s, 7);
        Assert.Equal(Prologue.Stage.Exit, s.Zone.Now);
        var gate = s.Meta.Place("LOWFORD", "gate");
        // (the day's wolf ring at the gate put down today: H4 item 10 r3's ring holds the gate till its second wave is down)
        s.J.World.Zone("lowford")[Play.Zones.Encounters.DoneKey("wolves")] = true;
        Stand(s, gate.X, gate.Z + 6);
        // (H8 N22: the portcullis, down while the ring was owed, rises first: she goes through once it is most of the way up)
        Run(s, 2.6);
        Assert.True(s.J.World.Fact("prologue.done").Truthy);
        Assert.Equal("waystation", s.Host.Travelled?.Zone);
    }

    [Fact]
    public void At_the_ford_C02_plays_and_leaves_the_warden_an_arms_length_off_facing_her()
    {
        // With a screen, the cinematic replaces the captions and the barks: the zone
        // waits, hides its own Warden while the cinematic's is on, and its last cue
        // starts the fight with him where it left him.
        var s = Make();
        s.Host.Plays = id => id == "c02";
        var ford = s.Meta.Place("LOWFORD", "ford");
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(s.Zone, [Prologue.Stage.ToFord]);
        Stand(s, 2.5, -31);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Intro, s.Zone.Now);
        var (id, done, _) = Assert.Single(s.Host.Cines);
        Assert.Equal("c02", id);
        Assert.Null(s.Host.Held);
        Run(s, 10);
        Assert.Equal(Prologue.Stage.Intro, s.Zone.Now);
        Assert.DoesNotContain(s.B.Enemies.Living(), e => e.Tag == "warden");
        s.Zone.CineEvent("warden_cine");
        s.Zone.CineEvent("warden_up");
        done!();
        Assert.Equal(Prologue.Stage.Boss, s.Zone.Now);
        var w = s.B.Enemies.Living().Single(e => e.Tag == "warden");
        var (x, _, z, _) = SurvivorUnchained.Cinema.CineFile.Load("c02").Mark("warden_end");
        Assert.Equal((x, z), (w.X, w.Z));
        Assert.True(Math.Cos(w.Facing - Math.Atan2(-31 - z, 2.5 - x)) > 0.99);
        Assert.Equal("Put out the lamps", s.Host.Tracked.Single().Steps[1].Text);
    }

    [Fact]
    public void Falling_here_is_forgiven()
    {
        var s = Make();
        Run(s, 5);
        Assert.True(s.Zone.OnDeath("the dead"));
        s.B.Player.Alive = false;
        Run(s, 3, safe: false);
        Assert.True(s.B.Player.Alive);
        Assert.Equal(s.B.MaxHp, s.B.Player.Hp);
        Assert.NotNull(s.Host.Revival);
    }

    [Fact]
    public void After_the_prologue_the_road_is_quiet_at_dawn()
    {
        var a = Callings.Archetype("warden");
        var s = Make();
        s.J.World.Facts["prologue.done"] = true;
        var z2 = new Prologue(s.Host, s.Meta);
        var b = s.J.StartBattle(true, s.Meta.Collision(), (_, _) => 0, 0, -100, 0, 9);
        z2.Begin(b);
        Assert.Equal(Prologue.Stage.Exit, z2.Now);
        Assert.Same(Atmospheres.LowFordMorning, s.Host.Air);   // (the morning's sun, climbed: Prologue.MorningClimbs)
        Assert.DoesNotContain(b.Collision.All(), c => c.Tag == "gate");
    }

    [Fact]
    public void The_dead_watchmans_book_opens_the_lamps()
    {
        // L1: the first line of the lamps is read on the night you rise.
        var s = Make();
        s.Zone.Interactables.Single(i => i.Id == "watchman").Act();
        Assert.Contains("lore.warden", s.J.Ch.Knowledge);
        Assert.Equal(QuestStatus.Active, s.J.World.Quests["lamps"].Status);
        Assert.Contains("book", s.J.World.Quests["lamps"].Entries);
    }
}
