using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>CODEX_audit.md installment 7 (SU-042, SU-043, SU-045): a build committed mid-fight goes into the running fight
/// at once by the one reconcile (Journey.RefreshKit): the same build a fresh battle would build, never stacking; and the
/// Lamps' edits are open where the post menu opens the bench (PostMenu.EditsOpen).</summary>
[Collection("Balance")]
public class BuildReconcileTests : IDisposable
{
    // (the live board, v2: other tests in the collection leave the v1 board up)
    readonly bool v2 = Lamps.V2;
    public BuildReconcileTests() => Lamps.UseV2(true);
    public void Dispose() => Lamps.UseV2(v2);

    static Journey New(string calling = "warden", int level = 30)
    {
        var a = Callings.Archetype(calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
        j.Ch.Level = level;
        return j;
    }

    static Battle Campaign(Journey j, uint seed = 3) => j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, seed);

    static readonly string[] Keys = [Stat.MaxHealth, Stat.Damage, Stat.Armor, Stat.CritChance, Stat.MoveSpeed, Stat.Cooldown, Stat.AbilityCooldown, Stat.DashCharges, Stat.Area, Stat.Regen];

    /// <summary>What the fight's build is: its numbers, facets, reflexes (with ranks), Flare and skills (rank, form, wick).</summary>
    static string Build(Battle b) => string.Join("\n", new[]
    {
        string.Join(" ", Keys.Select(k => $"{k}={b.Stats.Get(k):F6}")),
        "facets " + string.Join(",", b.Facets.OrderBy(x => x)),
        "reflexes " + string.Join(",", b.Reflexes.Select(r => $"{r.Def.Art}:{r.Rank}:{r.Def.Trigger}").OrderBy(x => x)),
        "flare " + (b.Flare?.Id ?? "-"),
        "lamps " + string.Join(",", b.Lamps.Rules.Keys.OrderBy(x => x)),
        "skills " + string.Join(",", b.Weapons.Select(w => $"{w.Id}:{w.Rank}:{w.Cast}:{string.Join("/", w.Wick?.Lit ?? [])}").OrderBy(x => x)),
    });

    /// <summary>SU-042: a layout taken up at a field post mid-fight. Before: the fight kept the old lamps, reflexes,
    /// Flare and numbers (LampBook.Switch changed the character only). After RefreshKit the fight is what a fresh battle
    /// builds, a second refresh changes nothing, and the reflex the old layout lit no longer fires.</summary>
    [Fact]
    public void A_layout_switched_mid_fight_is_the_fresh_battles_build_and_its_old_reflex_stops()
    {
        var j = New();
        Assert.True(LampBook.LightPath(j.Ch, null, "warden.shield_bash"), "shield bash path");
        foreach (var id in new[] { "sunderer.s1", "sunderer.s2", "sunderer.s3" }) LampBook.Light(j.Ch, null, id);
        var b = Campaign(j);
        Assert.Contains(b.Reflexes, r => r.Def.Art == "shield_bash");

        // layout 2 (empty, its type's entry only), taken up where layouts are open
        Assert.True(LampBook.Switch(j.Ch, 1, new WorldState { Time = TimeOfDay.Day }, "waystation"));
        j.RefreshKit(b);
        string after = Build(b);
        Assert.DoesNotContain(b.Reflexes, r => r.Def.Art == "shield_bash");
        j.RefreshKit(b);
        j.RefreshKit(b);
        Assert.Equal(after, Build(b));

        // removed reflexes stop firing: a crowd and a champion on her, and no shield bash
        foreach (var dx in new[] { 1.0, -1.0, 0.0 })
        {
            var e = b.SpawnEnemy("enforcer", dx, dx == 0 ? 1 : 0)!;
            e.AttackT = e.RangedT = 99;
        }
        int bashes = 0;
        for (int i = 0; i < 180; i++)
        {
            b.Tick(1 / 60.0, 0, 0);
            bashes += b.Events.Drain().OfType<Ev.Reflex>().Count(r => r.Art == "shield_bash");
        }
        Assert.Equal(0, bashes);

        // the same build a fresh battle takes up
        var fresh = Campaign(j);
        Assert.Equal(Build(fresh), after);

        // and back: the first layout's reflex is in the fight again, once
        Assert.True(LampBook.Switch(j.Ch, 0, new WorldState { Time = TimeOfDay.Day }, "waystation"));
        j.RefreshKit(b);
        j.RefreshKit(b);
        Assert.Single(b.Reflexes, r => r.Def.Art == "shield_bash");
        Assert.Equal(Build(Campaign(j)), Build(b));
    }

    /// <summary>SU-042: putting a lamp out mid-fight takes its numbers out (no stacking either way); lighting it again
    /// brings them back once.</summary>
    [Fact]
    public void A_lamp_put_out_and_lit_again_mid_fight_neither_lingers_nor_stacks()
    {
        var j = New();
        foreach (var id in new[] { "sunderer.s1", "sunderer.s2", "sunderer.s3" }) LampBook.Light(j.Ch, null, id);
        var b = Campaign(j);
        string lit = Build(b);
        var last = LampBook.Now(j.Ch).Lit.Last();
        Assert.True(LampBook.Unlight(j.Ch, last));
        j.RefreshKit(b);
        string dark = Build(b);
        Assert.NotEqual(lit, dark);
        Assert.Equal(Build(Campaign(j)), dark);
        Assert.True(LampBook.Light(j.Ch, null, last));
        j.RefreshKit(b);
        j.RefreshKit(b);
        Assert.Equal(lit, Build(b));
    }

    static string LearnableSkill(Journey j) =>
        Weapons.All.Values.Where(w => w.Findable && SkillBook.Carries(j.Ch, w.Id) && !SkillBook.Knows(j.Ch, w.Id) && Items.Find(SkillBook.Tome(w.Id)) != null
            && j.Ch.Equipment.Weapon?.Def is { } wd && Items.Get(wd).Weapon?.Id != w.Id)
            .Select(w => w.Id).OrderBy(id => id).First();

    /// <summary>SU-045: a tome read mid-fight learns and carries the skill; before, the fight never had it (RefreshKit
    /// added the gear's skills only). Now it is in the campaign fight at its day rank and taught form, once.</summary>
    [Fact]
    public void A_tome_read_mid_fight_puts_the_skill_in_the_campaign_fight()
    {
        var j = New(level: 9);
        j.Ch.Attributes.Might = j.Ch.Attributes.Finesse = j.Ch.Attributes.Wits = j.Ch.Attributes.Resolve = 10;
        var b = Campaign(j);
        // room on her keys and in her day slots for one more
        while (j.Ch.Slotted.Count >= SkillBook.Slots(j.Ch) - 1) j.Ch.Slotted.RemoveAt(j.Ch.Slotted.Count - 1);
        j.RefreshKit(b);
        var skill = LearnableSkill(j);
        Assert.True(b.HasRoomFor(skill), "room for " + skill);
        j.Ch.Discovered.Add(skill);
        j.GiveItem(SkillBook.Tome(skill));
        var tome = j.Ch.Satchel.First(p => p?.Def == SkillBook.Tome(skill))!;
        Assert.DoesNotContain(b.Weapons, w => w.Id == skill);
        j.Use(tome.Uid, b);
        Assert.Contains(skill, SkillBook.Carried(j.Ch).Select(c => c.Id));
        var w = Assert.Single(b.Weapons, x => x.Id == skill);
        Assert.Equal(WickBook.DayRank(j.Ch, skill), w.Rank);
        j.RefreshKit(b);
        Assert.Single(b.Weapons, x => x.Id == skill);
        Assert.Equal(Build(Campaign(j)), Build(b));
    }

    /// <summary>SU-045: an attribute point that meets a carried skill's need (SkillBook.Need) brings it into the fight;
    /// before, SpendPoint's refresh never added a learned skill.</summary>
    [Fact]
    public void A_point_that_meets_a_carried_skills_need_brings_it_into_the_fight()
    {
        var j = New(level: 9);
        j.Ch.Attributes.Might = j.Ch.Attributes.Finesse = j.Ch.Attributes.Wits = j.Ch.Attributes.Resolve = 10;
        var b = Campaign(j);
        while (j.Ch.Slotted.Count >= SkillBook.Slots(j.Ch) - 1) j.Ch.Slotted.RemoveAt(j.Ch.Slotted.Count - 1);
        j.RefreshKit(b);
        var skill = LearnableSkill(j);
        j.Ch.Discovered.Add(skill);
        Assert.True(SkillBook.Learn(j.Ch, skill));
        string attr = SkillBook.Attribute(skill);
        void Set(int v) { switch (attr) { case "Might": j.Ch.Attributes.Might = v; break; case "Finesse": j.Ch.Attributes.Finesse = v; break; case "Wits": j.Ch.Attributes.Wits = v; break; default: j.Ch.Attributes.Resolve = v; break; } }
        Set(SkillBook.Need - 1);
        j.RefreshKit(b);
        Assert.DoesNotContain(b.Weapons, w => w.Id == skill);
        j.Ch.Points = 1;
        j.SpendPoint(attr.ToLowerInvariant(), b);
        Assert.True(SkillBook.Meets(j.Ch, skill));
        Assert.Single(b.Weapons, x => x.Id == skill);
        Assert.Equal(Build(Campaign(j)), Build(b));
    }

    /// <summary>SU-043: the Lamps' edits are open where the post menu opens the bench (a lit post, calm, in reach), asked
    /// as each act runs. Before: the screen refused every edit in any combat zone (Battle.Combat), so the field respec the
    /// menu offered could not be finished.</summary>
    [Fact]
    public void The_lamps_edits_are_open_at_a_calm_lit_post_in_a_fight_and_close_when_she_leaves_it()
    {
        var w = new WorldState();
        w.Facts[PostMenu.TravelFact] = true;
        var post = LampPosts.Get("lowford.watch")!;
        LampBook.LightPost(w, post.Id);
        var b = new Battle(new BattleSetup { Seed = 1, Collision = new CollisionWorld(400), Combat = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)] });
        b.Player.X = post.X + 1; b.Player.Z = post.Z;
        var was = LampBook.Bench;
        try
        {
            LampBook.Bench = null;
            Assert.True(PostMenu.EditsOpen(w, post.Zone, null));
            Assert.False(PostMenu.EditsOpen(w, post.Zone, b));
            LampBook.Bench = world => world == w && PostMenu.AtBench(world, b, post) ? post.Id : null;
            Assert.True(PostMenu.LampsOpen(w, b, post));
            Assert.True(PostMenu.EditsOpen(w, post.Zone, b));
            Assert.False(PostMenu.EditsOpen(w, "elsewhere", b));
            // a foe comes close: the menu and the edits close together
            var e = b.SpawnEnemy(Enemies.All.Values.First(d => d.Faction == Faction.Pack).Id, b.Player.X + 1, b.Player.Z)!;
            b.Tick(1 / 60.0, 0, 0);
            Assert.False(PostMenu.LampsOpen(w, b, post));
            Assert.False(PostMenu.EditsOpen(w, post.Zone, b));
            e.X = post.X + 150; e.Z = post.Z + 150;
            b.Tick(1 / 60.0, 0, 0);
            Assert.True(PostMenu.EditsOpen(w, post.Zone, b));
            // she walks off: closed again
            b.Player.X = post.X + 30;
            Assert.False(PostMenu.EditsOpen(w, post.Zone, b));
        }
        finally { LampBook.Bench = was; }
    }
}
