using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Lamps v2 in the fight (docs/design/LAMPS_V2_RULES.md; Sim/BoardRules.cs): rites, links, Hand lamps, the small
/// rules and the blues on small synthetic boards, and the flag (v2 off is v1 unchanged).</summary>
[Collection("Balance")]
public sealed class LampsV2Tests
{
    static Battle Fight(string? calling, params (string Id, int Rank)[] weapons)
    {
        var b = BattleTests.Arena(3, weapons);
        b.Lamps = new LampLoadout();
        b.Calling = calling;
        return b;
    }

    static LampEffect Rule(string rule, string? tags = null, Dictionary<string, double>? args = null, Dictionary<string, string>? words = null, string lamp = "") =>
        new()
        {
            Do = LampDo.Rule, Rule = rule, Args = args ?? new(), Words = words, Lamp = lamp,
            Tags = tags?.Split(',').Select(t => Enum.Parse<Tag>(t, true)).ToArray(),
        };

    static LampEffect Rite(string mech, string tags, Dictionary<string, double>? args = null) =>
        Rule("rite", tags, args, new() { ["mech"] = mech });

    /// <summary>A creature that stands and takes it, risen and next to her.</summary>
    static Enemy Dummy(Battle b, bool elite = false, double dx = 1.5, double hp = 1e9)
    {
        var e = b.SpawnEnemy("risen", b.Player.X + dx, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9;
        e.AttackT = e.RangedT = 99;
        foreach (var w in b.Weapons) w.Timer = 1e9;
        for (int i = 0; i < 30; i++) b.Tick(0.1, 0, 0);
        b.Events.Drain();
        e.Elite = elite;
        e.MaxHp = e.Hp = hp;
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

    /* ----------------------------------------------------------- the flag -- */

    [Fact]
    public void No_v1_rule_wakes_the_v2_board()
    {
        // v1's board never lights a v2 rule, so with v2 off every BoardRules path is a no-op (the Act 1 gate).
        Lamps.UseV2(false);
        try { OnV1(); }
        finally { Lamps.UseV2(true); }
    }

    static void OnV1()
    {
        Assert.False(Lamps.V2);
        var v1 = Lamps.All.Values.SelectMany(l => l.Effects).Where(e => e.Rule != null).Select(e => e.Rule!).Distinct().ToList();
        Assert.True(v1.Count > 100);
        Assert.Empty(v1.Where(LampLoadout.IsBoardRule));
        Assert.Contains(Lamps.All.Values, l => l.Kind == LampKind.Skill);
        var lit = new LampLoadout();
        foreach (var e in Lamps.All.Values.SelectMany(l => l.Effects).Where(e => e.Do == LampDo.Rule)) lit.Add(e);
        Assert.False(lit.Board);
        Assert.False(lit.Unhoused);
    }

    [Fact]
    public void Lamp_args_split_numbers_from_words()
    {
        var e = Json.Parse<LampEffect>("""{"do":"rule","rule":"rite","tags":["spell"],"args":{"mech":"bleed","share":0.3,"wait":"6"}}""");
        Assert.Equal("bleed", e.Word("mech"));
        Assert.Equal(0.3, e.Arg("share"));
        Assert.Equal(6, e.Arg("wait"));
        Assert.Equal([Tag.Spell], e.Tags);
    }

    /* -------------------------------------------------------------- rites -- */

    [Fact]
    public void A_heavy_rite_makes_another_tags_skill_heavy_for_whoever_lights_it()
    {
        var b = Fight("arcanist", ("hoarfrost", 1));
        b.Lamps.Add(Rite("heavy", "nova", new() { ["every"] = 2 }));
        var w = b.Weapons[0];
        var e = Dummy(b);
        FireOnce(b, w, e);
        Assert.Equal(0, b.HandHeavies);
        FireOnce(b, w, e);
        Assert.Equal(1, b.HandHeavies);
    }

    [Fact]
    public void A_stone_rite_lays_a_stone_on_a_champion_once_a_firing()
    {
        var b = Fight("stalker", ("reaving_arc", 1));
        b.Lamps.Add(Rite("stone", "nova"));
        var e = Dummy(b, elite: true);
        FireOnce(b, b.Weapons[0], e);
        Assert.Equal(1, b.HandStones);
        Assert.Equal(1, b.Stones);
    }

    [Fact]
    public void Bleed_bind_and_mark_rites_ride_the_blow()
    {
        foreach (var (mech, kind) in new[] { ("bleed", StatusKind.Bleed), ("bind", StatusKind.Bound), ("mark", StatusKind.Mark) })
        {
            var b = Fight(null, ("hoarfrost", 1));
            b.Lamps.Add(Rite(mech, "frost", new() { ["share"] = 0.3, ["seconds"] = 2 }));
            var e = Dummy(b);
            Assert.False(e.Status.Has(kind));
            FireOnce(b, b.Weapons[0], e);
            Assert.True(e.Status.Has(kind), mech);
        }
    }

    [Fact]
    public void A_bind_rite_binds_only_the_first_thing_struck_each_firing()
    {
        var b = Fight(null, ("hoarfrost", 1));
        b.Lamps.Add(Rite("bind", "frost", new() { ["seconds"] = 2 }));
        var e1 = Dummy(b);
        var e2 = b.SpawnEnemy("risen", b.Player.X - 1.5, b.Player.Z)!;
        e2.MaxHp = e2.Hp = 1e9;
        e2.AttackT = e2.RangedT = 99;
        e2.State = e1.State;
        FireOnce(b, b.Weapons[0], e1);
        Assert.Equal(1, new[] { e1, e2 }.Count(x => x.Status.Has(StatusKind.Bound)));
    }

    [Fact]
    public void A_ground_rite_leaves_the_arcanist_hands_ground_on_a_kill()
    {
        var b = Fight("warden", ("reaving_arc", 1));
        b.Lamps.Add(Rite("ground", "nova"));
        var e = Dummy(b, hp: 1);
        FireOnce(b, b.Weapons[0], e);
        Assert.False(e.Alive && e.State != EnemyState.Dying);
        Assert.Equal(1, b.HandGrounds);
    }

    [Fact]
    public void Opening_and_far_rites_make_blows_strike_true()
    {
        var b = Fight(null, ("hoarfrost", 1));
        b.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -0.05, "test"));
        b.Lamps.Add(Rite("far", "frost", new() { ["range"] = 1, ["chance"] = 1 }));
        var e = Dummy(b);
        FireOnce(b, b.Weapons[0], e);
        Assert.True(e.LastCrit);

        var c = Fight(null, ("hoarfrost", 1));
        c.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -0.05, "test"));
        c.Lamps.Add(Rite("opening", "frost", new() { ["seconds"] = 2 }));
        var f = Dummy(c);
        FireOnce(c, c.Weapons[0], f);
        Assert.False(f.LastCrit);
        c.Player.DashCharges = 2;
        Assert.True(c.Dash(1, 0));
        FireOnce(c, c.Weapons[0], f);
        Assert.True(f.LastCrit);
    }

    [Fact]
    public void An_old_road_rite_takes_her_callings_mechanic()
    {
        var b = Fight("reaver", ("hoarfrost", 1));
        b.Lamps.Add(Rite("hand", "frost"));
        var e = Dummy(b);
        FireOnce(b, b.Weapons[0], e);
        Assert.True(e.Status.Has(StatusKind.Bleed));
    }

    /* -------------------------------------------------------------- links -- */

    [Fact]
    public void A_link_fires_her_pick_or_light_my_ways_once_then_waits()
    {
        var b = Fight(null, ("reaving_arc", 1), ("hoarfrost", 1));
        b.Lamps.Add(Rule("link", "frost", new() { ["wait"] = 5 }, new() { ["trigger"] = "dash" }, lamp: "x.link1"));
        Dummy(b);
        // No pick: the carried skill sharing the most tags with the link's (frost: Hoarfrost).
        Assert.Equal("hoarfrost", b.LinkSkill("x.link1")!.Id);
        // Her pick, carried, wins.
        b.Lamps.Links["x.link1"] = "reaving_arc";
        var w = b.LinkSkill("x.link1")!;
        Assert.Equal("reaving_arc", w.Id);
        double timer = w.Timer;
        Assert.Equal(0, b.LinkWait("x.link1"));
        b.Player.DashCharges = 3;
        Assert.True(b.Dash(1, 0));
        var ev = b.Events.Drain();
        Assert.Contains(ev, x => x is Ev.Link { Lamp: "x.link1", Skill: "reaving_arc" });
        Assert.Equal(timer, w.Timer); // Weapons.Echo: its own timer untouched
        Assert.Equal(1, b.LinkWait("x.link1"), 6);
        // Within the wait a second dash fires nothing.
        for (int i = 0; i < 30; i++) b.Tick(1 / 60.0, 0, 0);
        b.Events.Drain();
        Assert.True(b.Dash(1, 0));
        Assert.DoesNotContain(b.Events.Drain(), x => x is Ev.Link);
        for (int i = 0; i < 6 * 60; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(0, b.LinkWait("x.link1"));
        // A pick she doesn't carry: Light my way's again.
        b.Lamps.Links["x.link1"] = "volley";
        Assert.Equal("hoarfrost", b.LinkSkill("x.link1")!.Id);
    }

    [Fact]
    public void A_kills_link_fires_on_every_countth_kill()
    {
        var b = Fight(null, ("hoarfrost", 1));
        b.Lamps.Add(Rule("link", "frost", new() { ["wait"] = 4, ["count"] = 3 }, new() { ["trigger"] = "kills" }, lamp: "x.link2"));
        var e = Dummy(b);
        int fired = 0;
        for (int i = 0; i < 3; i++)
        {
            var k = b.SpawnEnemy("risen", b.Player.X + 2, b.Player.Z)!;
            b.KillEnemy(k, true, null);
            fired += b.Events.Drain().Count(x => x is Ev.Link);
            if (i < 2) Assert.Equal(0, fired);
        }
        Assert.Equal(1, fired);
    }

    /* --------------------------------------------------------- Hand lamps -- */

    [Fact]
    public void A_hand_lamp_adds_its_delta_to_hands_json_and_unhoused_turns_the_hand_off()
    {
        int every = Content.Hands.Warden.Every;
        var b = Fight("warden", ("oathblade", 1));
        b.Lamps.Add(Rule("hand", args: new() { ["every"] = -(every - 2) }));
        var w = b.Weapons[0];
        var e = Dummy(b);
        FireOnce(b, w, e);
        Assert.Equal(0, b.HandHeavies);
        FireOnce(b, w, e);
        Assert.Equal(1, b.HandHeavies);
        Assert.Equal(every, Content.Hands.Warden.Every); // the file's own number is untouched

        var u = Fight("warden", ("oathblade", 1));
        u.Lamps.Add(Rule("hand", args: new() { ["every"] = -(every - 2) }));
        u.Lamps.Add(Rule("blue.unhoused"));
        var uw = u.Weapons[0];
        var ue = Dummy(u);
        for (int i = 0; i < every + 1; i++) FireOnce(u, uw, ue);
        Assert.Equal(0, u.HandHeavies);
    }

    /* ---------------------------------------------------------- tags.more -- */

    [Fact]
    public void Tags_more_reads_its_when_and_its_vs_and_runs_at_a_quarter_by_night()
    {
        double Hit(bool chilled, bool moving, bool night)
        {
            var b = Fight(null, ("hoarfrost", 1));
            b.Lamps.Add(Rule("tags.more", "frost", new() { ["more"] = 0.4 }, new() { ["when"] = "still", ["vs"] = "chill" }));
            b.Lamps.Night = night;
            var e = Dummy(b);
            if (chilled) e.Status.Ensure(StatusKind.Chill, 5, 1, 0, 0);
            b.Tick(1 / 60.0, moving ? 1 : 0, 0);
            return b.HitEnemy(e, 100, School.Frost, [Tag.Frost, Tag.Spell], new HitOpts { NoCrit = true, Weapon = b.Weapons[0] });
        }
        double plain = Hit(false, false, false);
        Assert.Equal(plain * 1.4, Hit(true, false, false), 6);
        Assert.Equal(plain, Hit(true, true, false), 6);
        Assert.Equal(plain * 1.1, Hit(true, false, true), 6);
    }

    /* -------------------------------------------------------------- blues -- */

    [Fact]
    public void Mourners_debt_mends_on_shadow_kills_and_nothing_else_mends()
    {
        var b = Fight(null, ("reaving_arc", 1));
        b.Lamps.Add(Rule("blue.mourners_debt"));
        var e = Dummy(b, hp: 1);
        b.Player.Hp = 50;
        b.HealPlayer(30, "draught");
        Assert.Equal(50, b.Player.Hp);
        FireOnce(b, b.Weapons[0], e);
        Assert.True(b.Player.Hp > 50);
    }

    [Fact]
    public void Butchers_block_bursts_the_bleed_on_a_heavy_blow()
    {
        var b = Fight("warden", ("oathblade", 1));
        b.Lamps.Add(Rule("blue.butchers_block"));
        var w = b.Weapons[0];
        var e = Dummy(b);
        for (int i = 0; i < Content.Hands.Warden.Every - 1; i++) FireOnce(b, w, e);
        b.ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 1, 5, 3), 1000);
        Assert.True(e.Status.Has(StatusKind.Bleed));
        FireOnce(b, w, e);
        Assert.Equal(1, b.HandHeavies);
        Assert.False(e.Status.Has(StatusKind.Bleed));
        Assert.True(b.DamageBy.GetValueOrDefault("butchers_block") > 0);
    }
}

/// <summary>Lamps v2's data (godot/data/content/lamps_v2.json) under the flag. Runs alone (the Balance collection never
/// runs beside another), since it switches the board for the whole process.</summary>
[Collection("Balance")]
public sealed class LampsV2DataTests
{
    static bool HasData => System.IO.File.Exists(System.IO.Path.Combine(Core.DataFiles.Dir, "content", "lamps_v2.json"));

    static T OnV2<T>(Func<T> f)
    {
        Lamps.UseV2(true);
        try { return f(); }
        finally { Lamps.UseV2(true); }
    }

    /// <summary>Every phase-1 rule a v2 lamp lights is read by the fight (as LampsTests' for v1).</summary>
    [Fact]
    public void Every_phase_one_v2_rule_is_read_by_the_fight()
    {
        if (!HasData) return;
        var sim = System.IO.Path.GetFullPath(System.IO.Path.Combine(AppContext.BaseDirectory, "../../../../logic/Sim"));
        var code = string.Concat(System.IO.Directory.GetFiles(sim, "*.cs").Select(System.IO.File.ReadAllText));
        var rules = OnV2(() => Lamps.All.Values.SelectMany(l => l.Effects).Where(e => e.Do == LampDo.Rule && e.Phase == 1 && e.Rule != null)
            .Select(e => e.Rule!).Distinct().ToList());
        Assert.True(rules.Count >= 100, $"only {rules.Count} phase-1 rules");
        var unread = rules.Where(r => !code.Contains($"\"{r}\"")).OrderBy(r => r).ToList();
        Assert.True(unread.Count == 0, "unread: " + string.Join(", ", unread));
        // Every rite's mech and every link's trigger is one the fight knows.
        var mechs = new HashSet<string> { "heavy", "stone", "bleed", "bind", "ground", "mark", "opening", "far", "hand" };
        var triggers = new HashSet<string> { "block", "dash", "heavy", "champion_kill", "hurt", "low", "flare", "crowd", "still", "kills", "status_kill" };
        var bad = OnV2(() => Lamps.All.Values.SelectMany(l => l.Effects).Where(e => e.Phase == 1 &&
            (e.Rule == "rite" && !mechs.Contains(e.Word("mech") ?? "") || e.Rule == "link" && !triggers.Contains(e.Word("trigger") ?? e.Trigger ?? "")))
            .Select(e => e.Lamp).ToList());
        Assert.True(bad.Count == 0, "unknown mech or trigger: " + string.Join(", ", bad));
    }

    [Fact]
    public void Unhoused_opens_other_callings_lamps_with_no_depth()
    {
        if (!HasData) return;
        OnV2(() =>
        {
            var a = Callings.Archetype("warden");
            var ch = Character.Create(new CreationChoice
            {
                Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
            }, seed: 7);
            ch.Level = 200;
            LampBook.Begin(ch, null);
            var gated = Lamps.All.Values.First(l => l.Calling != null && l.Calling != "warden" && l.Gate > 0 && !l.Home && Lamps.Next(l.Id).Any(n => Lamps.Find(n) is { Gate: 0 }));
            var lit = LampBook.Now(ch).Lit;
            lit.Add(Lamps.Next(gated.Id).First(n => Lamps.Find(n) is { Gate: 0 }));
            Assert.Equal(LampNo.Gate, LampBook.CanLight(ch, null, gated.Id));
            lit.Add("ford.unhoused");
            Assert.Equal(LampNo.None, LampBook.CanLight(ch, null, gated.Id));
            var night = LampBook.Loadout(ch, night: true);
            Assert.True(night.Unhoused);
            return 0;
        });
    }

    [Fact]
    public void On_v2_a_save_drops_the_lit_ids_v2_lacks()
    {
        if (!HasData) return;
        OnV2(() =>
        {
            var a = Callings.Archetype("reaver");
            var ch = Character.Create(new CreationChoice
            {
                Name = "Ashe", Archetype = "reaver", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
            }, seed: 7);
            LampBook.Begin(ch, null);
            LampBook.Now(ch).Lit.Add("no.such.lamp");
            LampBook.Now(ch).Links["no.such.link"] = "volley";
            LampBook.DropUnknown(ch);
            Assert.DoesNotContain("no.such.lamp", LampBook.Now(ch).Lit);
            Assert.Empty(LampBook.Now(ch).Links);
            Assert.All(LampBook.Free(ch), f => Assert.Contains(f, LampBook.Now(ch).Lit));
            return 0;
        });
    }
}
