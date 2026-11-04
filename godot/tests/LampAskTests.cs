using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Lamps screen's asks (docs/design/LAMPS_SCREEN_BRIEF.md §14) on the v2 board: PathTo and LightPath keep
/// CanLight's rules, Suggested lights nothing and agrees with Light my way, Sleeps and LinkPick agree with the fight's
/// links and rules, and WickBook.Sum's total is the fight's own number for the skill.</summary>
[Collection("Balance")]
public sealed class LampAskTests
{
    static bool HasData => System.IO.File.Exists(System.IO.Path.Combine(Core.DataFiles.Dir, "content", "lamps_v2.json"));

    static CharacterData Hero(string calling, int level)
    {
        Lamps.UseV2(true);
        var a = Callings.Archetype(calling);
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = level;
        LampBook.Begin(ch, null);
        return ch;
    }

    [Fact]
    public void PathTo_lights_step_by_step_by_CanLights_rules()
    {
        if (!HasData) return;
        foreach (var calling in new[] { "warden", "reaver" })
        {
            var ch = Hero(calling, 400);
            var keep = LampBook.Now(ch).Lit.ToList();
            int found = 0, gated = 0;
            var miss = new List<string>();
            // What can be lit at all: light anything CanLight allows until nothing more is (the ground truth).
            var reach = new HashSet<string>();
            for (bool more = true; more;)
            {
                more = false;
                foreach (var d in Lamps.All.Values) if (LampBook.Light(ch, null, d.Id)) { reach.Add(d.Id); more = true; }
            }
            LampBook.Now(ch).Lit.Clear();
            LampBook.Now(ch).Lit.AddRange(keep);
            foreach (var d in Lamps.All.Values.Where((_, i) => i % 3 == 0))
            {
                var p = LampBook.PathTo(ch, null, d.Id);
                if (keep.Contains(d.Id) || (d.Home && d.Calling != ch.Archetype)) { Assert.Empty(p); continue; }
                if (p.Count == 0) { if (reach.Contains(d.Id)) miss.Add(d.Id + ":" + d.Gate + ":" + d.Road); continue; }
                Assert.Contains(d.Id, reach);
                found++;
                if (d.Gate > 0) gated++;
                Assert.Equal(d.Id, p[^1]);
                Assert.Equal(p.Count, p.Distinct().Count());
                foreach (var x in p) Assert.True(LampBook.Light(ch, null, x), $"{d.Id}: {x} {LampBook.CanLight(ch, null, x)}");
                LampBook.Now(ch).Lit.Clear();
                LampBook.Now(ch).Lit.AddRange(keep);
            }
            Assert.True(miss.Count == 0, $"{calling}: {found} reached; missed {miss.Count} reachable: {string.Join(" ", miss.Take(15))}");
            Assert.True(found > 30, $"{calling}: {found} reached");
            Assert.True(gated > 10, $"{calling}: {gated} gated reached");
        }
    }

    [Fact]
    public void PathTo_reaches_a_deep_gate_with_the_fewest_road_lamps_it_needs()
    {
        if (!HasData) return;
        var ch = Hero("warden", 400);
        var keep = LampBook.Now(ch).Lit.ToList();
        var deep = Lamps.All.Values.Where(d => d.Calling == "warden" && !d.Home && d.Gate >= 8 && d.Road != null).ToList();
        Assert.NotEmpty(deep);
        foreach (var d in deep)
        {
            var p = LampBook.PathTo(ch, null, d.Id);
            Assert.NotEmpty(p);
            // Its gate is met when it lights, so at least gate lamps (less those lit) stand on its road before it.
            int onRoad = keep.Count(x => Lamps.Find(x)?.Road == d.Road) + p.Take(p.Count - 1).Count(x => Lamps.Find(x)?.Road == d.Road);
            Assert.True(onRoad >= d.Gate, d.Id);
        }
        Assert.Equal(keep, LampBook.Now(ch).Lit);
    }

    [Fact]
    public void LightPath_is_all_or_nothing()
    {
        if (!HasData) return;
        var ch = Hero("warden", 3);
        var l = LampBook.Now(ch);
        var before = l.Lit.ToList();
        var flare = l.Flare;
        var far = Lamps.All.Values.First(d => d.Calling == "warden" && !d.Home && LampBook.PathTo(ch, null, d.Id).Count > LampBook.Spare(ch, null));
        Assert.False(LampBook.LightPath(ch, null, far.Id));
        Assert.Equal(before, l.Lit);
        Assert.Equal(flare, l.Flare);
        ch.Level = 400;
        var p = LampBook.PathTo(ch, null, far.Id);
        Assert.True(LampBook.LightPath(ch, null, far.Id));
        Assert.Equal(before.Concat(p), l.Lit);
        Assert.Empty(LampBook.PathTo(ch, null, far.Id));
        Assert.False(LampBook.LightPath(ch, null, far.Id));
    }

    [Fact]
    public void Suggested_lights_nothing_and_is_what_Light_my_way_lights()
    {
        if (!HasData) return;
        foreach (var calling in new[] { "warden", "arcanist", "stalker" })
        {
            var ch = Hero(calling, 30);
            var before = LampBook.Now(ch).Lit.ToList();
            var s = LampBook.Suggested(ch, null, 100);
            var five = LampBook.Suggested(ch, null, 5);
            Assert.Equal(before, LampBook.Now(ch).Lit);
            Assert.Equal(s.Take(5), five);
            Assert.Equal(LampBook.Spare(ch, null), s.Count);
            LampBook.LightSuggested(ch, null);
            Assert.Equal(before.Concat(s), LampBook.Now(ch).Lit);
        }
    }

    /// <summary>A day fight with what she carries and the lit lamps' rules, as the game sets one up.</summary>
    static Battle Day(CharacterData ch)
    {
        var day = Character.DaySkills(ch);
        var b = BattleTests.Arena(3, day.ToArray());
        if (day.Count == 0) b.Weapons.Clear();
        b.Lamps = LampBook.Loadout(ch, night: false);
        b.Calling = ch.Archetype;
        return b;
    }

    [Fact]
    public void Sleeps_and_LinkPick_agree_with_the_fight()
    {
        if (!HasData) return;
        var ch = Hero("reaver", 400);
        var links = Lamps.All.Values.Where(d => d.Calling == "reaver" && d.Effects.Any(e => e.Rule == "link" && e.Phase <= Lamps.LivePhase)).ToList();
        Assert.NotEmpty(links);
        var link = links[0];
        Assert.True(LampBook.LightPath(ch, null, link.Id));
        var carries = new List<Action>
        {
            () => { },
            () => { ch.Equipment = new Equipment(); ch.Slotted.Clear(); },
        };
        int asleep = 0;
        foreach (var carry in carries)
        {
            carry();
            var b = Day(ch);
            var fires = b.LinkSkill(link.Id);
            Assert.Equal(fires == null, LampBook.Sleeps(ch, link.Id) != null);
            Assert.Equal(fires?.Id, LampBook.LinkPick(ch, link.Id));
            Assert.Equal(b.Weapons.Select(w => w.Id), LampBook.LinkChoices(ch, link.Id));
            if (fires == null) asleep++;
        }
        Assert.Equal(1, asleep);

        // A tag or rite lamp: awake exactly when the fight's rule is on one of her skills (LampLoadout.HasOn).
        ch = Hero("reaver", 400);
        var scoped = Lamps.All.Values.Where(d => d.Effects.Length > 0 && d.Effects.All(e => e.Do == LampDo.Rule && e.Rule != "link" && e.Tags != null && e.Phase <= Lamps.LivePhase)).ToList();
        Assert.NotEmpty(scoped);
        int awake = 0, slept = 0;
        foreach (var d in scoped)
        {
            var b = Day(ch);
            var lo = new LampLoadout();
            foreach (var e in d.Effects) lo.Add(e);
            bool on = d.Effects.Any(e => b.Weapons.Any(w => lo.HasOn(e.Rule!, w.Def.Id, w.Tags)));
            var sl = LampBook.Sleeps(ch, d.Id);
            Assert.True(on == (sl == null), d.Id);
            if (sl != null) { slept++; Assert.NotEmpty(sl.Tags); } else awake++;
        }
        Assert.True(awake > 0 && slept > 0, $"awake {awake}, asleep {slept}");

        // Pick a carried skill and it fires; a skill not carried is no choice.
        var c2 = Hero("reaver", 400);
        Assert.True(LampBook.LightPath(c2, null, link.Id));
        var choices = LampBook.LinkChoices(c2, link.Id);
        Assert.NotEmpty(choices);
        Assert.True(LampBook.SetLinkPick(c2, link.Id, choices[^1]));
        Assert.Equal(choices[^1], LampBook.LinkPick(c2, link.Id));
        Assert.Equal(choices[^1], Day(c2).LinkSkill(link.Id)?.Id);
        Assert.False(LampBook.SetLinkPick(c2, link.Id, "no_such_skill"));
    }

    [Fact]
    public void Sum_is_the_fights_number_by_day_and_night()
    {
        if (!HasData) return;
        int checkedN = 0;
        foreach (var calling in new[] { "warden", "reaver", "arcanist", "stalker" })
        {
            var ch = Hero(calling, 13);
            foreach (var skill in Wicks.Skills.Where(s => Weapons.CanCarry(calling, s) && (Weapons.All[s].Base.Damage ?? 0) > 0).Take(2))
                foreach (var night in new[] { false, true })
                {
                    var sum = WickBook.Sum(ch, skill, night);
                    Assert.NotNull(sum);
                    int rank = WickBook.RankIn(ch, skill, night);
                    var b = BattleTests.Arena(3, (skill, rank));
                    b.SetWickPath(skill, WickBook.Path(ch, skill));
                    var w = b.Weapons.Single(x => x.Id == skill);
                    Assert.Equal(w.Damage, sum!.Total, 9);
                    Assert.Equal("base", sum.Parts[0].What);
                    if (w.Wick is { TurnLit: true }) Assert.StartsWith("Turn", sum.Parts[^1].What);
                    checkedN++;
                }
        }
        Assert.True(checkedN >= 8);
        // Day and night differ by the rank the skill comes in at (13th level: day rank 5, the ember's 3).
        var h = Hero("warden", 13);
        var sk = Wicks.Skills.First(s => Weapons.CanCarry("warden", s) && (Weapons.All[s].Base.Damage ?? 0) > 0 && !Character.DaySkills(h, gearOnly: true).Any(g => g.Id == s));
        Assert.NotEqual(WickBook.Sum(h, sk, false)!.Total, WickBook.Sum(h, sk, true)!.Total);
        Assert.Null(WickBook.Sum(h, "no_such_skill", false));
    }
}
