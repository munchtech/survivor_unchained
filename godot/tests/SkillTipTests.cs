using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>U1: the skill tooltips' model (Content/SkillTips.cs, Rpg/SkillTipModel.cs): every demo skill has its own card
/// whose numbers are the sim's, no placeholder is left, and a lamp reports what it changes.</summary>
public class SkillTipTests(ITestOutputHelper output)
{
    static Journey Warden(uint seed = 7)
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, seed);
    }

    static Battle Day(Journey j) => j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 1);

    static void LevelTo(Journey j, int level)
    {
        while (j.Ch.Level < level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 0.01);
    }

    /// <summary>The demo set with each skill's cast form: the taught slots, later, the union and its parts, rebuke.</summary>
    static List<(string Skill, string Cast)> Demo()
    {
        var t = TaughtBuilds.Of("warden")!;
        var set = new List<(string, string)>();
        void Add(string s, string cast) { if (set.All(x => x.Item1 != s)) set.Add((s, cast)); }
        foreach (var s in t.Slots) Add(s.Skill, s.Cast);
        foreach (var s in t.Later) Add(s, "kindle");
        if (t.Union != null)
        {
            Add(t.Union.Id, Cast(t.Union.Id));
            Add("cleaver", Cast("cleaver"));
            Add("sunder", Cast("sunder"));
        }
        Add("rebuke", "kindle");
        return set;
    }

    static string Cast(string id) => Weapons.All[id].Press?.Kind switch { PressKind.Hold => "hold", PressKind.Channel => "channel", PressKind.Kindle => "kindle", _ => "press" };

    /// <summary>The skill as the fight has it (carried, or put on in place of another so it can be compared).</summary>
    static WeaponInst InFight(CharacterData ch, Battle b, string skill, string cast)
    {
        var w = b.Weapons.Find(x => x.Id == skill);
        if (w == null)
        {
            for (int i = 0; i < 3 && (w = b.AddWeapon(skill, WickBook.RankIn(ch, skill, false))!) == null; i++)
                b.RemoveWeapon(b.Weapons.Last(x => x.Id != "sunder" && x.Id != skill).Id);
            Assert.NotNull(w);
        }
        w.SetForm(cast);
        return w;
    }

    static void NoBraces(SkillTipView v)
    {
        var all = new List<string> { v.Name, v.How, v.Line };
        all.AddRange(v.Rows.SelectMany(r => new[] { r.Label, r.Value }));
        if (v.Cost is { } c) { all.Add(c.Label); all.Add(c.Value); }
        foreach (var s in all) { Assert.DoesNotContain("{", s); Assert.DoesNotContain("}", s); Assert.DoesNotContain("?", s); }
    }

    [Fact]
    public void The_demo_set_has_its_own_cards_with_the_sims_numbers_at_levels_1_9_15()
    {
        var demo = Demo();
        Assert.True(demo.Count >= 9);
        foreach (int level in new[] { 1, 9, 15 })
        {
            var j = Warden();
            LevelTo(j, level);
            var b = Day(j);
            foreach (var (skill, cast) in demo)
            {
                var w = InFight(j.Ch, b, skill, cast);
                var v = SkillTipModel.Build(j.Ch, null, skill, cast);
                string at = $"{skill} L{level}";
                Assert.True(v.Own, at + " has no entry of its own");
                Assert.False(string.IsNullOrWhiteSpace(v.Name), at);
                Assert.False(string.IsNullOrWhiteSpace(v.Line), at);
                Assert.True(v.Line.Length <= 140, $"{at} line is {v.Line.Length} chars: {v.Line}");
                Assert.InRange(v.Rows.Count, 2, 4);
                Assert.All(v.Rows, r => Assert.False(string.IsNullOrWhiteSpace(r.Value), at));
                Assert.Empty(v.Unresolved);
                if (SkillTipModel.Build(j.Ch, null, skill, cast) is var vc && WickBook.Sum(j.Ch, skill, false)?.Cut is { } cut)
                {
                    // a chained skill: the cut is what lands (a normal Damage row, no cost row)
                    Assert.Null(v.Cost);
                    Assert.Equal($"{SkillTipModel.Damage(cut)} a cut, every {SkillTipModel.Seconds(WickBook.Sum(j.Ch, skill, false)!.Every!.Value)} s", v.Rows.First(r => r.Label == "Damage").Value);
                }
                else Assert.NotNull(v.Cost);
                NoBraces(v);
                Assert.True(v.Line.Length <= 112, $"{at} line is {v.Line.Length} chars: {v.Line}");

                // the numbers are the fight's
                var live = SkillTipModel.Build(j.Ch, b, skill, cast);
                Assert.Equal(v.Rows, live.Rows);
                Assert.Equal(v.Cost, live.Cost);
                Assert.Equal(v.Line, live.Line);
                Assert.Equal(SkillTipModel.Damage(w.Damage), SkillTipModel.Damage(SkillTipModelDamage(j.Ch, skill, cast)));
                double cd = Firing.CooldownOf(b, w);
                Assert.True(System.Math.Abs(cd - Firing.CampaignCooldownOf(Mirror(j.Ch, skill, cast, w), b.Resolve.On, SkillTipModel.StatMul(j.Ch))) < 1e-6, $"{at} cooldown sim {cd} twin {Firing.CampaignCooldownOf(Mirror(j.Ch, skill, cast, w), b.Resolve.On, SkillTipModel.StatMul(j.Ch))} stat {b.Stats.Get(Stat.Cooldown)} mods {w.Mods.Cooldown}");
                Assert.Equal(b.CostOf(w), b.Resolve.On ? w.Press?.Resolve ?? 0 : 0, 6);
            }
        }
    }

    /// <summary>The weapon as the card takes it up with no fight (what Build does), so its damage can be read.</summary>
    static WeaponInst Mirror(CharacterData ch, string skill, string cast, WeaponInst like)
    {
        var w = WickBook.Weapon(ch, skill, WickBook.RankIn(ch, skill, false), false);
        w.Press = Weapons.All[skill].Press;
        if (w.Press != null) w.SetForm(cast);
        return w;
    }

    static double SkillTipModelDamage(CharacterData ch, string skill, string cast) => Mirror(ch, skill, cast, null!).Damage;

    [Fact]
    public void Every_skill_builds_a_view_without_braces()
    {
        var j = Warden();
        LevelTo(j, 9);
        foreach (var id in Weapons.All.Keys)
        {
            foreach (var cast in new[] { "press", "hold", "channel", "kindle" })
            {
                var v = SkillTipModel.Build(j.Ch, null, id, cast, "Q");
                Assert.False(string.IsNullOrEmpty(v.Name));
                NoBraces(v);
            }
        }
        Assert.Equal("nothing_here", SkillTipModel.Build(j.Ch, null, "nothing_here", "press").Name);
    }

    [Fact]
    public void A_lamp_reports_the_first_stat_it_changes()
    {
        var j = Warden();
        // Sunder's strands: find a lamp that raises damage, one that widens, and a Turn
        string? dmg = null, reach = null, turn = null;
        foreach (var s in Wicks.StrandsOf("sunder"))
            for (int n = 1; n <= Wicks.PerStrand; n++)
            {
                string id = s.LampId(n);
                var d = WickBook.LampDelta(j.Ch, "sunder", id);
                if (d is { What: "Cut" } && dmg == null) dmg = id;
                if (d is { What: "Reach" or "Size" } && reach == null) reach = id;
                if (n == Wicks.PerStrand && turn == null) turn = id;
                output.WriteLine($"{id}: {d?.What} {d?.Before} -> {d?.After}");
            }
        Assert.NotNull(dmg);
        var dd = WickBook.LampDelta(j.Ch, "sunder", dmg!)!.Value;
        Assert.True(double.Parse(dd.After) > double.Parse(dd.Before));
        Assert.NotNull(reach);
        Assert.Null(WickBook.LampDelta(j.Ch, "sunder", "nope.9"));
        var before = Json.Write(j.Ch);
        WickBook.LampDelta(j.Ch, "sunder", turn!);
        Assert.Equal(before, Json.Write(j.Ch));
    }

    [Fact]
    public void A_damage_lamps_before_is_the_sum_lines_total_at_each_rank()
    {
        foreach (int lv in new[] { 3, 9 })
        {
            var j = Warden();
            LevelTo(j, lv);
            var sum = WickBook.Sum(j.Ch, "sunder", false)!;
            string? dmg = null;
            foreach (var s in Wicks.StrandsOf("sunder"))
                for (int n = 1; n < Wicks.PerStrand && dmg == null; n++)
                    if (WickBook.LampDelta(j.Ch, "sunder", s.LampId(n)) is { What: "Cut", Cond: "" }) dmg = s.LampId(n);
            Assert.NotNull(dmg);
            var d = WickBook.LampDelta(j.Ch, "sunder", dmg!)!.Value;
            output.WriteLine($"level {lv}: {d.Before} -> {d.After}, sum {sum.Total}");
            Assert.Equal(System.Math.Round(sum.Cut!.Value).ToString("0"), d.Before);
            Assert.True(double.Parse(d.After) > double.Parse(d.Before));
        }
    }

    [Fact]
    public void A_chained_skills_lamp_and_level_card_speak_in_cuts()
    {
        var j = Warden();
        var m = WickBook.LampMeasure(j.Ch, "sunder", WickBook.NextLamp(j.Ch, "sunder") ?? Wicks.StrandsOf("sunder").First().LampId(1));
        output.WriteLine($"{m}");
        if (m.Measure == "a cut") Assert.True(m.After > m.Before);
        var wide = WickBook.LampDelta(j.Ch, "sunder", Wicks.StrandsOf("sunder").SelectMany(s => Enumerable.Range(1, Wicks.PerStrand - 1).Select(s.LampId)).First(id => WickBook.LampDelta(j.Ch, "sunder", id) is { What: "Cut" }));
        Assert.True(double.Parse(wide!.Value.After) > double.Parse(wide.Value.Before));
    }

    [Fact]
    public void A_conditional_damage_lamp_reports_the_blow_against_its_condition()
    {
        var j = Warden();
        var st = WickBook.LampDelta(j.Ch, "sunder", "holy.2");
        Assert.NotNull(st);
        Assert.Equal("Cut", st!.Value.What); // Sunder is chained: its conditional lamps speak in cuts too
        Assert.True(double.Parse(st.Value.After, System.Globalization.CultureInfo.InvariantCulture) > double.Parse(st.Value.Before, System.Globalization.CultureInfo.InvariantCulture));
        Assert.Equal("on seared foes", st.Value.Cond);
        var ch = WickBook.LampDelta(j.Ch, "rebuke", "rebuke.morning.3");
        Assert.NotNull(ch);
        Assert.True(double.Parse(ch!.Value.After) > double.Parse(ch.Value.Before));
        Assert.Equal("on champions", ch.Value.Cond);
        // the statuses' chance and duration lamps stay without a delta
        Assert.Null(WickBook.LampDelta(j.Ch, "sunder", "holy.1"));
        Assert.Null(WickBook.LampDelta(j.Ch, "sunder", "holy.3"));
    }

    [Fact]
    public void The_level_9_cards_table()
    {
        var j = Warden();
        LevelTo(j, 9);
        var b = Day(j);
        foreach (var (skill, cast) in Demo())
        {
            InFight(j.Ch, b, skill, cast);
            var v = SkillTipModel.Build(j.Ch, null, skill, cast);
            output.WriteLine($"{v.Name} | {v.How} | {v.Line} | {string.Join("; ", v.Rows.Select(r => r.Label + ": " + r.Value))} | {v.Cost?.Label}: {v.Cost?.Value}");
            System.Console.WriteLine($"{v.Name} | {v.How} | {v.Line} | {string.Join("; ", v.Rows.Select(r => r.Label + ": " + r.Value))} | {v.Cost?.Label}: {v.Cost?.Value}");
        }
    }
}
