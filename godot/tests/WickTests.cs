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

/// <summary>The Wicks (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.3): the plan's rules, rank to lit lamps, Light my
/// way, each built Turn on the skill's numbers, evolutions and unions, the save, and a skill without one untouched.</summary>
public sealed class WickTests
{
    static CharacterData Warden(int level = 1)
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = level;
        return ch;
    }

    static StatBlock Stats()
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 140, [Stat.Regen] = 0, [Stat.Armor] = 2, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4,
            [Stat.CritChance] = 0.05, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        return s;
    }

    /// <summary>A fight with one skill whose wick lights along a plan (null: no wick in the fight).</summary>
    static Battle Fight(string skill, int rank, string[]? plan, uint seed = 1, string? wickFor = null)
    {
        var col = new CollisionWorld(120);
        return new Battle(new BattleSetup
        {
            Seed = seed, Collision = col, Combat = true, Stats = Stats(), Weapons = [(skill, rank)], Ability = AbilityKind.ShieldBash,
            Wicks = plan == null ? null : new Dictionary<string, string[]> { [wickFor ?? skill] = WickBook.Path(plan, wickFor ?? skill) },
        });
    }

    static (Battle B, WeaponInst W) One(string skill, int rank, params string[] plan)
    {
        var b = Fight(skill, rank, plan);
        return (b, b.Weapons[0]);
    }

    static string[] Strand(string id, int upTo = 4) => Enumerable.Range(1, upTo).Select(n => $"{id}.{n}").ToArray();

    [Fact]
    public void The_starting_skills_have_their_strands()
    {
        Assert.Equal(["wide", "linger", "holy"], Wicks.Of("oathblade")!.Strands);
        Assert.Equal("wide", Wicks.Of("oathblade")!.Suggested);
        Assert.Equal(["chain", "split", "fire"], Wicks.Of("judgement_disc")!.Strands);
        Assert.Equal("chain", Wicks.Of("judgement_disc")!.Suggested);
        Assert.Null(Wicks.Of("seeking_motes"));
        // Every strand a skill lists suits it as it is.
        foreach (var id in Wicks.Skills)
        {
            var w = Weapons.Get(id);
            foreach (var s in Wicks.StrandsOf(id))
                Assert.True(Wicks.Suits(s, w.Behavior, w.Tags, w.School, (w.Base.Splash ?? 0) > 0), $"{id}: {s.Id}");
        }
        Assert.Equal("15% chance to sear", Wicks.Text("oathblade", "holy.1"));
        Assert.Equal("+10% damage to seared enemies", Wicks.Text("oathblade", "holy.2"));
        Assert.StartsWith("Wide:", Wicks.Text("oathblade", "wide.4"));
    }

    [Fact]
    public void A_plan_lights_in_order_with_one_turn()
    {
        var ch = Warden();
        Assert.Equal(WickNo.Order, WickBook.Plan(ch, "oathblade", "wide.2"));
        Assert.Equal(WickNo.Unknown, WickBook.Plan(ch, "oathblade", "split.1"));
        Assert.Equal(WickNo.NoWick, WickBook.Plan(ch, "seeking_motes", "split.1"));
        foreach (var l in Strand("wide")) Assert.Equal(WickNo.None, WickBook.Plan(ch, "oathblade", l));
        Assert.Equal(WickNo.Planned, WickBook.Plan(ch, "oathblade", "wide.1"));
        foreach (var l in Strand("holy", 3)) Assert.Equal(WickNo.None, WickBook.Plan(ch, "oathblade", l));
        // One Turn a skill.
        Assert.Equal(WickNo.Turn, WickBook.Plan(ch, "oathblade", "holy.4"));
        foreach (var l in Strand("linger", 3)) Assert.Equal(WickNo.None, WickBook.Plan(ch, "oathblade", l));
        Assert.Equal(WickNo.Turn, WickBook.Plan(ch, "oathblade", "linger.4"));
        Assert.Equal(10, WickBook.PlanOf(ch, "oathblade").Count);
        // A lamp holding a later one stays; the last of a strand comes out.
        Assert.Equal(WickNo.Holds, WickBook.Unplan(ch, "oathblade", "holy.2"));
        Assert.Equal(WickNo.None, WickBook.Unplan(ch, "oathblade", "holy.3"));
        Assert.Equal(WickNo.Unplanned, WickBook.Unplan(ch, "oathblade", "holy.3"));
        // The Turn out, another may go in.
        Assert.Equal(WickNo.None, WickBook.Unplan(ch, "oathblade", "wide.4"));
        Assert.Equal(WickNo.None, WickBook.Plan(ch, "oathblade", "linger.4"));
        WickBook.Reset(ch, "oathblade");
        Assert.Empty(WickBook.PlanOf(ch, "oathblade"));
    }

    [Fact]
    public void Twelve_is_the_most_a_plan_holds()
    {
        // Twelve lamps with one Turn is ten at most: the rules stop it before twelve, and the path never passes it.
        var path = WickBook.Path(Strand("holy").Concat(Strand("wide")).Concat(Strand("linger")).ToArray(), "oathblade");
        Assert.True(path.Length <= Wicks.LampCount);
        Assert.Single(path, l => Wicks.IsTurn("oathblade", l));
    }

    [Fact]
    public void Light_my_way_follows_the_suggested_strand_then_the_lead_ins()
    {
        var ch = Warden();
        Assert.Equal(["wide.1", "wide.2", "wide.3", "wide.4", "linger.1", "linger.2", "linger.3", "holy.1", "holy.2", "holy.3"], WickBook.Path(ch, "oathblade"));
        Assert.Equal(["wide.1", "wide.2", "wide.3"], WickBook.Lit(ch, "oathblade", 3));
        Assert.Equal(["wide.1", "wide.2", "wide.3", "wide.4", "linger.1"], WickBook.Lit(ch, "oathblade", 5));
        // A plan comes first; Light my way finishes it and never lights a second Turn.
        WickBook.Plan(ch, "oathblade", "holy.1");
        WickBook.Plan(ch, "oathblade", "holy.2");
        Assert.Equal(["holy.1", "holy.2", "wide.1", "wide.2", "wide.3", "wide.4", "linger.1", "linger.2"], WickBook.Lit(ch, "oathblade", 8));
        foreach (var l in new[] { "holy.3", "holy.4" }) WickBook.Plan(ch, "oathblade", l);
        var p = WickBook.Path(ch, "oathblade");
        Assert.Equal(["holy.1", "holy.2", "holy.3", "holy.4", "wide.1", "wide.2", "wide.3", "linger.1", "linger.2", "linger.3"], p);
        // The harness's --turn puts a strand first.
        Assert.Equal(Strand("linger"), WickBook.Path(System.Array.Empty<string>(), "oathblade", force: "linger").Take(4));
        // Forced over a plan: its Turn wins, the plan's lead-ins follow.
        Assert.Equal(["linger.1", "linger.2", "linger.3", "linger.4", "holy.1", "holy.2", "holy.3", "wide.1"], WickBook.Path(p, "oathblade", force: "linger").Take(8));
        Assert.Empty(WickBook.Path(ch, "seeking_motes"));
    }

    [Fact]
    public void The_plan_saves_with_her_and_an_old_save_has_none()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 7);
        foreach (var l in Strand("linger")) WickBook.Plan(j.Ch, "oathblade", l);
        WickBook.Plan(j.Ch, "judgement_disc", "fire.1");
        var text = Json.Write(j.ToSave(new SaveLocation { Zone = "waystation" }));
        var back = Saves.Migrate(Json.Parse<SaveData>(text));
        Assert.Equal(Strand("linger"), WickBook.PlanOf(back.Character, "oathblade"));
        Assert.Equal(["fire.1"], WickBook.PlanOf(back.Character, "judgement_disc"));
        // A save from before the Wicks: no "wicks" on its layouts.
        var bare = Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 7);
        var old = Json.Write(bare.ToSave(new SaveLocation { Zone = "waystation" }));
        Assert.Contains("\"wicks\":{}", old);
        var o = Saves.Migrate(Json.Parse<SaveData>(old.Replace(",\"wicks\":{}", "").Replace("\"wicks\":{},", "")));
        Assert.Empty(WickBook.PlanOf(o.Character, "oathblade"));
        Assert.Equal(WickNo.None, WickBook.Plan(o.Character, "oathblade", "wide.1"));
    }

    [Fact]
    public void By_day_her_skills_fight_with_their_wick_at_her_rank()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 7);
        j.Ch.Level = 10;
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7);
        Assert.False(b.EmberOn);
        foreach (var w in b.Weapons.Where(w => Wicks.Of(w.Id) != null))
        {
            Assert.Equal(w.Rank, w.Wick!.Lit.Length);
            Assert.Equal(WickBook.Lit(j.Ch, w.Id, w.Rank), w.Wick.Lit);
        }
        Assert.Contains(b.Weapons, w => w.Wick != null);
    }

    [Fact]
    public void By_night_each_rank_lights_the_next_lamp_and_shows_it()
    {
        var b = Fight("judgement_disc", 2, []);
        b.EmberOn = true;
        b.Events.Drain();
        var w = b.Weapons[0];
        Assert.Equal(["chain.1", "chain.2"], w.Wick!.Lit);
        b.RankWeapon("judgement_disc");
        b.RankWeapon("judgement_disc");
        Assert.Equal(Strand("chain"), w.Wick!.Lit);
        var ev = b.Events.Drain().OfType<Ev.Wick>().ToList();
        Assert.Equal(["chain.3", "chain.4"], ev.Select(e => e.Lamp));
        Assert.Equal([false, true], ev.Select(e => e.Turn));
        Assert.Equal(2, b.WickLit);
        Assert.Equal(["chain"], w.Wick.Turns);
    }

    static double Ratio(System.Func<Battle, WeaponInst, double> f, string skill, int rank, string[] plan)
    {
        var (b0, w0) = (Fight(skill, rank, null), (WeaponInst?)null);
        w0 = b0.Weapons[0];
        var (b1, w1) = One(skill, rank, plan);
        return f(b1, w1) / f(b0, w0);
    }

    [Fact]
    public void Split_throws_three_smaller()
    {
        var plan = Strand("split");
        Assert.Equal(1.1 * 0.28, Ratio((_, w) => w.Damage, "judgement_disc", 4, plan), 6);
        Assert.Equal(0.75, Ratio((b, w) => Firing.AreaOf(b, w, 1), "judgement_disc", 4, plan), 6);
        Assert.Equal(3, Ratio((b, w) => Firing.CountOf(b, w), "judgement_disc", 4, plan), 6);
        // Its second lamp on a projectile is speed, not area; its third, the cooldown.
        Assert.Equal(1.15, Ratio((b, w) => Firing.SpeedOf(b, w), "judgement_disc", 4, plan), 6);
        Assert.Equal(0.92, Ratio((b, w) => Firing.CooldownOf(b, w), "judgement_disc", 4, plan), 6);
    }

    [Fact]
    public void Chain_bounces_twice_more()
    {
        var (b, w) = One("judgement_disc", 4, Strand("chain"));
        Assert.Equal(1.1 * 0.85, Ratio((_, x) => x.Damage, "judgement_disc", 4, Strand("chain")), 6);
        var e = b.SpawnEnemy("risen", b.Player.X + 4, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9;
        for (int i = 0; i < 60 && !b.Projectiles.Items.Any(p => p.Alive && p.Weapon == "judgement_disc"); i++) b.Tick(0.05, 0, 0);
        var pr = b.Projectiles.Items.First(p => p.Alive && p.Weapon == "judgement_disc");
        Assert.Equal((int)Weapons.Get("judgement_disc").Base.Bounces! + 2, pr.Bounces);
    }

    [Fact]
    public void Wide_is_bigger_and_slower()
    {
        var plan = Strand("wide");
        Assert.Equal(1.2 * 1.1, Ratio((b, w) => Firing.AreaOf(b, w, 1), "oathblade", 4, plan), 6);
        Assert.Equal(1.3 * 0.92, Ratio((b, w) => Firing.CooldownOf(b, w), "oathblade", 4, plan), 6);
        Assert.Equal(1.1 * 0.85, Ratio((_, w) => w.Damage, "oathblade", 4, plan), 6);
    }

    [Fact]
    public void Linger_leaves_its_ground()
    {
        var (b, w) = One("oathblade", 4, Strand("linger"));
        Assert.Equal(new GroundSpec(1.5, 2, 0.25), w.GroundOf);
        var e = b.SpawnEnemy("risen", b.Player.X + 1.5, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9;
        for (int i = 0; i < 80 && !b.Zones.Items.Any(z => z.Alive && z.Weapon == "oathblade"); i++) b.Tick(0.05, 0, 0);
        var zn = b.Zones.Items.First(z => z.Alive && z.Weapon == "oathblade");
        Assert.Equal(School.Physical, zn.School);
        Assert.Null(Fight("oathblade", 4, null).Weapons[0].GroundOf);
    }

    [Fact]
    public void A_school_turn_changes_the_school_its_tag_and_its_status()
    {
        var (_, w) = One("oathblade", 4, Strand("holy"));
        Assert.Equal(School.Holy, w.School);
        Assert.Contains(Tag.Holy, w.Tags);
        Assert.Contains(Tag.Physical, w.Tags);
        Assert.Contains(Tag.Steel, w.Tags);
        var st = Assert.Single(w.Wick!.Statuses);
        Assert.Equal(StatusKind.Sear, st.Pay.Kind);
        Assert.Equal(0.15, st.Pay.Chance, 6);
        Assert.Equal(0.10, st.VsStatus, 6);
        Assert.Equal(0.15, st.Duration, 6);
        // A holy disc turned fire loses holy, and its lead-ins burn.
        var (_, d) = One("judgement_disc", 4, Strand("fire"));
        Assert.Equal(School.Fire, d.School);
        Assert.DoesNotContain(Tag.Holy, d.Tags);
        Assert.Contains(Tag.Fire, d.Tags);
        Assert.Equal(StatusKind.Burn, d.Wick!.Statuses[0].Pay.Kind);
        // The lead-ins alone (no Turn) keep the school and still give the new one's status a chance.
        var (_, h) = One("oathblade", 3, Strand("holy", 3));
        Assert.Equal(School.Physical, h.School);
        Assert.Equal(StatusKind.Sear, h.Wick!.Statuses[0].Pay.Kind);
    }

    [Fact]
    public void An_evolution_keeps_its_turn_where_it_suits_and_dims_it_where_it_replaced_the_shape()
    {
        var (b, w) = One("oathblade", 8, Strand("wide"));
        b.Evolve("oathblade", "oathkeeper", chest: true);
        Assert.Equal(["wide"], w.Wick!.Turns);
        // An evolution with a shape of its own (a behavior, a count or an arc it sets) leaves a shape Turn nothing.
        var (_, d) = One("judgement_disc", 8, Strand("split"));
        d.Evolution = new Evolution { Id = "test_shape", Set = new WeaponStats { Projectiles = 2 } };
        var lit = d.Wick!.Lit.Select(id => Wicks.Lamp("judgement_disc", id)!.Value);
        var fx = Turns.Build(d, lit, d.Wick.Lit);
        Assert.Empty(fx.Turns);
        Assert.Equal(["split"], fx.Dark);
        Assert.Equal(1.0, fx.Projectiles);
        d.Evolution = new Evolution { Id = "test_behavior", Behavior = WeaponBehavior.Nova };
        Assert.Equal(["split"], Turns.Build(d, lit, d.Wick.Lit).Dark);
        // A school Turn holds through an evolution that sets no school, and dims for one that does.
        var (_, o) = One("oathblade", 8, Strand("holy"));
        var olit = o.Wick!.Lit.Select(id => Wicks.Lamp("oathblade", id)!.Value).ToList();
        o.Evolution = Weapons.Get("oathblade").Evolutions.First(e => e.Id == "graveedge");
        Assert.Equal(["holy"], Turns.Build(o, olit).Turns);
        o.Evolution = new Evolution { Id = "test_school", School = School.Frost };
        Assert.Equal(["holy"], Turns.Build(o, olit).Dark);
    }

    [Fact]
    public void A_union_carries_each_parts_turn_that_still_suits()
    {
        var col = new CollisionWorld(120);
        var b = new Battle(new BattleSetup
        {
            Seed = 1, Collision = col, Combat = true, Stats = Stats(), Weapons = [("judgement_disc", 8), ("dawnpulse", 8)], Ability = AbilityKind.ShieldBash,
            Wicks = new() { ["judgement_disc"] = WickBook.Path(Strand("chain"), "judgement_disc") },
        });
        b.Evolve("judgement_disc", "reckoning", chest: true);
        b.Evolve("dawnpulse", Weapons.Get("dawnpulse").Evolutions[0].Id, chest: true);
        var u = b.Unite("dawns_judgement")!;
        Assert.Equal(["chain"], u.Wick!.Turns);
        Assert.Equal(2, u.Wick.Bounces);
    }

    /// <summary>A library Turn (no lead-ins) lit on a fight's one skill.</summary>
    static (Battle B, WeaponInst W) Turned(string skill, int rank, string strand)
    {
        var b = Fight(skill, rank, null);
        var w = b.Weapons[0];
        w.Wick = Turns.Build(w, [(Wicks.Strand(skill, strand)!, Wicks.PerStrand)]);
        Assert.Equal([strand], w.Wick.Turns);
        return (b, w);
    }

    [Fact]
    public void Pulse_goes_off_three_times_smaller()
    {
        var (b, w) = Turned("dawnpulse", 4, "pulse");
        var t = Wicks.Turn("pulse");
        Assert.Equal(3, w.Wick!.Pulses);
        Assert.Equal(t.Damage, w.Wick.Damage, 6);
        Assert.Equal(t.Area, w.Wick.Area, 6);
        var plain = Fight("dawnpulse", 4, null).Weapons[0];
        Assert.Equal(t.Damage, w.Damage / plain.Damage, 6);
        var e = b.SpawnEnemy("risen", b.Player.X + 1, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9;
        var novas = new List<double>();
        for (int i = 0; i < 400 && novas.Count == 0; i++) { b.Tick(0.01, 0, 0); foreach (var ev in b.Events.Drain()) if (ev is Ev.Nova) novas.Add(b.Time); }
        Assert.Single(novas);
        // The cast's two follow-ups, PulseGap apart, before its cooldown brings the next cast; one cast, one blow.
        for (int i = 0; i < 70; i++) { b.Tick(0.01, 0, 0); foreach (var ev in b.Events.Drain()) if (ev is Ev.Nova) novas.Add(b.Time); }
        Assert.True(Firing.CooldownOf(b, w) > 0.7);
        Assert.Equal(3, novas.Count);
        Assert.Equal(t.PulseGap, novas[1] - novas[0], 1);
        Assert.Equal(t.PulseGap, novas[2] - novas[1], 1);
        Assert.Equal(1, w.Casts);
    }

    [Fact]
    public void On_kill_fires_once_from_the_corpse_with_no_cascade_and_its_gap()
    {
        // (gap 0: only the no-cascade rule can stop an echo's kill from echoing)
        static (Battle B, WeaponInst W, List<(double X, double Z)> Mine, List<(double X, double Z)> Echoes, System.Func<double, double, double, Enemy> At) Setup(double? gap)
        {
            var (b, w) = Turned("oathblade", 4, "onkill");
            if (gap is { } g) w.Wick!.OnKillGap = g;
            double x = b.Player.X, z = b.Player.Z;
            Enemy At(double dx, double dz, double hp) { var e = b.SpawnEnemy("risen", x + dx, z + dz)!; e.MaxHp = e.Hp = hp; e.Speed = 0; return e; }
            return (b, w, new(), new(), At);
        }
        static void Run(Battle b, List<(double X, double Z)> mine, List<(double X, double Z)> echoes)
        {
            double x = b.Player.X, z = b.Player.Z;
            // (until her first swing, then a little past it: the echo comes on the next tick)
            for (int i = 0, after = 0; i < 400 && after < 15; i++)
            {
                if (mine.Count > 0) after++;
                b.Tick(0.02, 0, 0);
                foreach (var ev in b.Events.Drain())
                    if (ev is Ev.Slash s) (System.Math.Abs(s.X - x) + System.Math.Abs(s.Z - z) < 0.3 ? mine : echoes).Add((s.X, s.Z));
            }
        }
        static bool Down(Enemy e) => !e.Alive || e.State == EnemyState.Dying;

        // One in her reach that her swing kills; past it, one only an echo from its corpse reaches (and kills), and one
        // only an echo from that one's corpse could reach.
        var (b, w, mine, echoes, at) = Setup(0);
        double r = Firing.AreaOf(b, w, Weapons.Get("oathblade").Base.Reach ?? 2.6);
        var a = at(1, 0, 1);
        var next = at(1 + r - 0.4, 0, 1);
        var far = at(1 + 2 * r - 0.8, 0, 1e9);
        Run(b, mine, echoes);
        Assert.True(Down(a) && Down(next));
        // (one firing: each of its swings, CountOf of them, from the one corpse)
        var echo = Assert.Single(echoes.Distinct());
        Assert.Equal(Firing.CountOf(b, w, 1), echoes.Count);
        Assert.Equal(b.Player.X + 1, echo.X, 0);
        Assert.Equal(far.MaxHp, far.Hp);
        // Not a cast: no blow counted, no pose (her firings are her swings alone).
        Assert.Equal(mine.Count, w.Casts * Firing.CountOf(b, w, 1));

        // Two kills in one swing: one echo, the gap holding the second.
        (b, w, mine, echoes, at) = Setup(null);
        Assert.Equal(Wicks.Turn("onkill").OnKillGap, w.Wick!.OnKillGap);
        var a1 = at(1, 0, 1);
        var a2 = at(1, 0.5, 1);
        at(1 + r - 0.4, 0, 1e9); // (something for the echoes to swing at)
        Run(b, mine, echoes);
        Assert.True(Down(a1) && Down(a2));
        Assert.Single(echoes.Distinct());
    }

    [Fact]
    public void A_union_carries_both_parts_lead_ins()
    {
        var col = new CollisionWorld(120);
        var b = new Battle(new BattleSetup
        {
            Seed = 1, Collision = col, Combat = true, Stats = Stats(), Weapons = [("judgement_disc", 8), ("dawnpulse", 8)], Ability = AbilityKind.ShieldBash,
            Wicks = new() { ["judgement_disc"] = WickBook.Path(Strand("chain"), "judgement_disc") },
        });
        var disc = b.Weapons[0];
        // Its path: the chain strand (+10% damage, +15% speed, 8% shorter cooldown, the Turn), then four more lead-ins.
        var lit = disc.Wick!.Lit.Select(id => Wicks.Lamp("judgement_disc", id)!.Value).ToList();
        Assert.Equal(8, lit.Count);
        double dmg = 1 + lit.Where(l => l.N < Wicks.PerStrand).Sum(l => l.Strand.LeadIns[l.N - 1].Damage);
        double cd = 1 + lit.Where(l => l.N < Wicks.PerStrand).Sum(l => l.Strand.LeadIns[l.N - 1].Cooldown);
        b.Evolve("judgement_disc", "reckoning", chest: true);
        b.Evolve("dawnpulse", Weapons.Get("dawnpulse").Evolutions[0].Id, chest: true);
        var u = b.Unite("dawns_judgement")!;
        Assert.Equal(["chain"], u.Wick!.Turns);
        Assert.True(dmg > 1.05 && cd < 0.95);
        Assert.Equal(0.85 * dmg, u.Wick.Damage, 6);
        Assert.Equal(cd, u.Wick.Cooldown, 6);
    }

    [Fact]
    public void A_skill_with_no_wick_fights_exactly_as_before()
    {
        static string Digest(Battle b) =>
            $"{b.Time:R}|{b.Player.Hp:R}|{string.Join(",", b.Weapons.Select(w => $"{w.Id}:{w.DamageDealt:R}:{w.Kills}"))}|{b.Enemies.Items.Count(e => e.Alive)}";
        // No drafts (the ember out), so the fight is hers alone; the wicked one carries every wick's path.
        var plain = Fight("seeking_motes", 3, null, seed: 5);
        var wicked = Fight("seeking_motes", 3, [], seed: 5, wickFor: "judgement_disc");
        foreach (var id in Wicks.Skills) wicked.WickPaths[id] = WickBook.Path(System.Array.Empty<string>(), id);
        plain.EmberOn = wicked.EmberOn = false;
        BattleTests.Simulate(plain, 40);
        BattleTests.Simulate(wicked, 40);
        Assert.Null(wicked.Weapons.Find(w => w.Id == "seeking_motes")!.Wick);
        Assert.Equal(Digest(plain), Digest(wicked));
    }
}
