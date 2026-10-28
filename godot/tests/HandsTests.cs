using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The four Hands (docs/design/CLASS_IDENTITY_AND_TALENTS.md 2.2 item 1): each fires on its tags and only
/// its calling's, on an empty board, and the card says so.</summary>
public sealed class HandsTests
{
    static Battle Fight(string? calling, params (string Id, int Rank)[] weapons)
    {
        var b = BattleTests.Arena(3, weapons);
        b.Lamps = new LampLoadout();
        b.Calling = calling;
        return b;
    }

    /// <summary>A creature that stands and takes it, risen and next to her.</summary>
    static Enemy Dummy(Battle b, bool boss = false, bool elite = false, double dx = 1.5)
    {
        var e = b.SpawnEnemy("risen", b.Player.X + dx, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9;
        e.AttackT = e.RangedT = 99;
        // Her skills hold while it rises: the tests count their firings themselves.
        foreach (var w in b.Weapons) w.Timer = 1e9;
        for (int i = 0; i < 30; i++) b.Tick(0.1, 0, 0);
        b.Events.Drain();
        e.Boss = boss;
        e.Elite = elite || boss;
        e.MaxHp = e.Hp = 1e9;
        return e;
    }

    static void Reindex(Battle b)
    {
        b.Spatial.Clear();
        foreach (var e in b.Enemies.Items) if (e.Alive && e.State != EnemyState.Dying) b.Spatial.Insert(e.Id, e.X, e.Z);
    }

    /// <summary>The skill fires once, at whatever stands beside her.</summary>
    static void FireOnce(Battle b, WeaponInst w, Enemy e)
    {
        e.X = b.Player.X + 1.5; e.Z = b.Player.Z;
        Reindex(b);
        w.Timer = 0;
        int casts = w.Casts;
        Firing.Tick(b, w, 0.01);
        Assert.Equal(casts + 1, w.Casts);
    }

    [Fact]
    public void The_wardens_fourth_melee_blow_is_heavy_and_stuns_a_creature()
    {
        var b = Fight("warden", ("oathblade", 1));
        var w = b.Weapons[0];
        var e = Dummy(b);
        for (int i = 0; i < Content.Hands.Warden.Every - 1; i++) { FireOnce(b, w, e); e.Status.Remove(StatusKind.Stun); }
        Assert.Equal(0, b.HandHeavies);
        FireOnce(b, w, e);
        Assert.Equal(1, b.HandHeavies);
        Assert.True(e.Status.Has(StatusKind.Stun));
        Assert.Contains(b.Events.Drain(), x => x is Ev.Hand { Kind: HandKind.Heavy });
        // The count starts again: the next is plain (Every in hands.json).
        e.Status.Remove(StatusKind.Stun);
        FireOnce(b, w, e);
        Assert.Equal(1, b.HandHeavies);
        Assert.False(e.Status.Has(StatusKind.Stun));
    }

    [Fact]
    public void A_heavy_blow_on_a_boss_fills_its_stagger_bar()
    {
        var b = Fight("warden", ("oathblade", 1));
        var w = b.Weapons[0];
        var e = Dummy(b, boss: true);
        for (int i = 0; i < Content.Hands.Warden.Every - 1; i++) FireOnce(b, w, e);
        double before = e.Stagger;
        FireOnce(b, w, e);
        Assert.True(e.Stagger - before >= Content.Hands.Warden.Stagger * b.Rules.StaggerTaken * 0.99, $"{before} -> {e.Stagger}");
        Assert.False(e.Status.Has(StatusKind.Stun));
    }

    [Fact]
    public void A_heavy_throw_lands_heavy_when_it_arrives()
    {
        var b = Fight("warden", ("judgement_disc", 1));
        var w = b.Weapons[0];
        var e = Dummy(b, dx: 4);
        for (int i = 0; i < Content.Hands.Warden.Every; i++)
        {
            e.X = b.Player.X + 4; e.Z = b.Player.Z;
            w.Timer = 0;
            Firing.Tick(b, w, 0.01);
            for (int k = 0; k < 40; k++) { e.AttackT = 99; b.Tick(1 / 60.0, 0, 0); }
            w.Timer = 99;
        }
        Assert.True(b.HandHeavies >= 1);
    }

    [Fact]
    public void Spells_and_plain_projectiles_are_never_heavy_and_holy_skills_lay_a_stone_per_champion_per_firing()
    {
        var b = Fight("warden", ("dawnpulse", 1));
        var w = b.Weapons[0];
        var e = Dummy(b, elite: true);
        for (int i = 0; i < 4; i++) FireOnce(b, w, e);
        Assert.Equal(0, b.HandHeavies);
        Assert.Equal(4, b.HandStones);
        Assert.Equal(4, b.Stones);
        // On a creature that is no champion, no stone.
        var c = Fight("warden", ("dawnpulse", 1));
        var plain = Dummy(c);
        FireOnce(c, c.Weapons[0], plain);
        Assert.Equal(0, c.HandStones);
    }

    [Fact]
    public void The_hands_stones_answer_with_a_rebuke_on_an_empty_board()
    {
        var b = Fight("warden", ("dawnpulse", 1));
        var e = Dummy(b, elite: true);
        int need = Content.Hands.Warden.Stones;
        for (int i = 0; i < need; i++) FireOnce(b, b.Weapons[0], e);
        Assert.Equal(1, b.Rebukes);
        Assert.Equal(0, b.Stones);
    }

    [Fact]
    public void A_reavers_hit_on_a_bleeding_thing_adds_frenzy_and_her_areas_grow_when_hurt()
    {
        var b = Fight("reaver", ("cleaver", 1), ("volley", 1));
        var e = Dummy(b);
        var w = b.Weapons[0];
        b.HitEnemy(e, 1, School.Physical, w.Tags, new HitOpts { Weapon = w });
        Assert.Equal(0, b.Frenzy);
        e.Status.Ensure(StatusKind.Bleed, 5, 1, 1, 0.5);
        b.HitEnemy(e, 1, School.Physical, w.Tags, new HitOpts { Weapon = w });
        Assert.Equal(1, b.Frenzy);
        // At most one a gate.
        b.HitEnemy(e, 1, School.Physical, w.Tags, new HitOpts { Weapon = w });
        Assert.Equal(1, b.Frenzy);
        Assert.True(Firing.CooldownOf(b, w) < Firing.CooldownOf(Fight("reaver", ("cleaver", 1)), Fight("reaver", ("cleaver", 1)).Weapons[0]) + 1e-9);

        Assert.Equal(1, b.HandAreaMul(w));
        b.Player.Hp = b.MaxHp * 0.4;
        Assert.Equal(1 + Content.Hands.Reaver.Area, b.HandAreaMul(w), 6);
        Assert.Equal(1, b.HandAreaMul(b.Weapons[1])); // Volley has no Area
    }

    [Fact]
    public void An_arcanists_spell_kill_leaves_ground_and_passes_its_mark()
    {
        var b = Fight("arcanist", ("cinderfall", 1), ("oathblade", 1));
        var e = Dummy(b);
        var next = b.SpawnEnemy("risen", e.X + 2, e.Z)!;
        next.Hp = next.MaxHp = 1e9;
        Reindex(b);
        e.Hp = 1;
        e.Status[StatusKind.Mark] = new StatusSlot(4, 1, 1, 0.5);
        var spell = b.Weapons[0];
        b.HitEnemy(e, 100, spell.School, spell.Tags, new HitOpts { Weapon = spell, NoCrit = true });
        Assert.Equal(1, b.HandGrounds);
        Assert.Contains(b.Zones.Items, z => z.Alive && z.Credit == "hand" && z.School == School.Fire);
        Assert.Equal(1, b.HandMarks);
        Assert.True(next.Status.Has(StatusKind.Mark));

        // A blade's kill leaves nothing.
        var c = Fight("arcanist", ("oathblade", 1));
        var f = Dummy(c);
        f.Hp = 1;
        c.HitEnemy(f, 100, School.Physical, c.Weapons[0].Tags, new HitOpts { Weapon = c.Weapons[0], NoCrit = true });
        Assert.Equal(0, c.HandGrounds);
    }

    [Fact]
    public void After_a_dash_a_stalkers_projectiles_pierce_once_more_and_champions_are_struck_true()
    {
        var b = Fight("stalker", ("volley", 1), ("oathblade", 1));
        var bow = b.Weapons[0];
        var champ = Dummy(b, elite: true);
        Assert.Equal(0, b.HandPierce(bow));
        Assert.True(b.Dash(1, 0));
        Assert.Equal(Content.Hands.Stalker.Pierce, b.HandPierce(bow));
        Assert.Equal(0, b.HandPierce(b.Weapons[1])); // a blade has no pierce to gain
        for (int i = 0; i < 10; i++) b.HitEnemy(champ, 1, School.Physical, bow.Tags, new HitOpts { Weapon = bow, Projectile = true });
        Assert.Equal(10, b.HandTrues);
        // A creature that is no champion is not struck true by the Hand.
        var c = Fight("stalker", ("volley", 1));
        var mob = Dummy(c);
        c.Dash(1, 0);
        for (int i = 0; i < 10; i++) c.HitEnemy(mob, 1, School.Physical, c.Weapons[0].Tags, new HitOpts { Weapon = c.Weapons[0], Projectile = true });
        Assert.Equal(0, c.HandTrues);
        // The window closes.
        b.Time += Abilities.Dash.Time + Content.Hands.Stalker.Seconds + 0.1;
        Assert.Equal(0, b.HandPierce(bow));
    }

    [Fact]
    public void Off_calling_or_switched_off_no_hand_bends_anything()
    {
        foreach (var calling in new string?[] { null, "reaver", "arcanist", "stalker" })
        {
            var b = Fight(calling, ("oathblade", 1));
            var e = Dummy(b);
            for (int i = 0; i < 8; i++) FireOnce(b, b.Weapons[0], e);
            Assert.Equal(0, b.HandHeavies);
        }
        var off = Fight("warden", ("oathblade", 1));
        off.HandsOn = false;
        var d = Dummy(off);
        for (int i = 0; i < 8; i++) FireOnce(off, off.Weapons[0], d);
        Assert.Equal(0, off.HandHeavies);

        var r = Fight("reaver", ("cleaver", 1));
        r.HandsOn = false;
        var bleeding = Dummy(r);
        bleeding.Status.Ensure(StatusKind.Bleed, 5, 1, 1, 0.5);
        r.HitEnemy(bleeding, 1, School.Physical, r.Weapons[0].Tags, new HitOpts { Weapon = r.Weapons[0] });
        Assert.Equal(0, r.Frenzy);
        r.Player.Hp = 1;
        Assert.Equal(1, r.HandAreaMul(r.Weapons[0]));

        var s = Fight("stalker", ("volley", 1));
        s.HandsOn = false;
        s.Dash(1, 0);
        Assert.Equal(0, s.HandPierce(s.Weapons[0]));
        // A fight's switch starts from the harness's.
        Assert.Equal(Battle.Hands, new Battle(new BattleSetup { Seed = 1, Collision = new CollisionWorld(40), Combat = true, Stats = new StatBlock(), Weapons = [] }).HandsOn);
    }

    [Fact]
    public void The_card_says_what_her_hand_does_and_nothing_where_it_does_nothing()
    {
        var W = Weapons.All;
        Assert.StartsWith($"In a warden's hand: every {Content.Hands.Warden.Every}th blow is heavy", Hands.Line("warden", W["oathblade"]));
        Assert.Contains("lays a Stone", Hands.Line("warden", W["judgement_disc"]));
        Assert.Contains("heavy", Hands.Line("warden", W["judgement_disc"]));
        Assert.Null(Hands.Line("warden", W["volley"]));
        Assert.Null(Hands.Line("warden", W["seeking_motes"]));
        Assert.Contains("bleeding thing add Frenzy", Hands.Line("reaver", W["cleaver"]));
        Assert.Contains("larger", Hands.Line("reaver", W["cleaver"]));
        Assert.DoesNotContain("larger", Hands.Line("reaver", W["volley"]));
        Assert.StartsWith("In an arcanist's hand: what it kills leaves 1 m of burning ground for 2 s", Hands.Line("arcanist", W["cinderfall"]));
        Assert.Contains("chilling", Hands.Line("arcanist", W["rimeshard"]));
        Assert.Contains("moonlit", Hands.Line("arcanist", W["seeking_motes"]));
        Assert.DoesNotContain("ground", Hands.Line("arcanist", W["arcweb"]));
        Assert.Null(Hands.Line("arcanist", W["oathblade"]));
        Assert.Contains("pierces once more", Hands.Line("stalker", W["volley"]));
        Assert.DoesNotContain("pierces", Hands.Line("stalker", W["oathblade"]));
        Assert.Null(Hands.Line(null, W["oathblade"]));

        // The draft's card carries it, for her calling only.
        var b = Fight("warden");
        Assert.EndsWith(Hands.Line("warden", W["oathblade"])!, LevelUp.WithHand(b, W["oathblade"]));
        b.Calling = "stalker";
        Assert.DoesNotContain("warden", LevelUp.WithHand(b, W["oathblade"]));
        Assert.Equal(W["seeking_motes"].Description, LevelUp.WithHand(Fight("warden"), W["seeking_motes"]));
    }
}
