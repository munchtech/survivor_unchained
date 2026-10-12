using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Lamps (docs/design/CLASSES.md §2): the board's shape, and how a survivor lights,
/// puts out and carries it (Content/Lamps.cs, Rpg/LampBook.cs).</summary>
public class LampsTests
{
    static readonly string[] Callings4 = ["warden", "reaver", "arcanist", "stalker"];

    static CharacterData Survivor(string calling, int level = 1)
    {
        var a = Callings.Archetype(calling);
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = level;
        return ch;
    }

    [Fact]
    public void TheBoardHasItsShape()
    {
        Assert.Equal(360, Lamps.All.Count);
        Assert.Equal(8, Lamps.Roads.Count);
        Assert.Equal(16, Lamps.Flares.Count);
        foreach (var c in Callings4)
        {
            Assert.Equal(84, Lamps.All.Values.Count(l => l.Calling == c));
            Assert.Equal(14, Lamps.All.Values.Count(l => l.Calling == c && l.Region == LampRegion.Hearth));
            Assert.Equal(6, Lamps.All.Values.Count(l => l.Calling == c && l.Region == LampRegion.Bridge));
            Assert.Equal(2, Lamps.RoadsOf(c).Count());
            Assert.Single(Lamps.All.Values, l => l.Calling == c && l.Kind == LampKind.Start);
        }
        foreach (var r in Lamps.Roads.Values)
        {
            var on = Lamps.All.Values.Where(l => l.Road == r.Id).ToList();
            Assert.Equal(32, on.Count);
            Assert.Single(on, l => l.Kind == LampKind.Entry);
            Assert.Equal(7, on.Count(l => l.Kind is LampKind.Small or LampKind.Attribute));
            Assert.Equal(9, on.Count(l => l.Kind == LampKind.Skill));
            Assert.Equal(5, on.Count(l => l.Kind == LampKind.Notable));
            Assert.Equal(2, on.Count(l => l.Kind == LampKind.Blue));
            Assert.Equal(2, on.Count(l => l.Kind == LampKind.Ultimate));
            Assert.Equal(6, on.Count(l => l.Kind == LampKind.UltimateMod));
            Assert.Equal(3, r.Skills.Length);
            Assert.Equal(FlareKind.Strike, Lamps.Flare(r.Strike)!.Kind);
            Assert.Equal(FlareKind.Stand, Lamps.Flare(r.Stand)!.Kind);
        }
        Assert.Equal(24, Lamps.All.Values.Count(l => l.Region == LampRegion.Crossing));
        // 28 blue lamps, each named (§2.3).
        Assert.Equal(28, Lamps.All.Values.Count(l => l.Kind == LampKind.Blue));
        Assert.All(Lamps.All.Values.Where(l => l.Kind is not (LampKind.Small or LampKind.Attribute)), l => Assert.False(string.IsNullOrWhiteSpace(l.Name), l.Id));
        Assert.All(Lamps.All.Values, l => Assert.False(string.IsNullOrWhiteSpace(l.Text), l.Id));
    }

    [Fact]
    public void EveryLampIsReachedFromEveryHearth()
    {
        foreach (var c in Callings4)
        {
            var seen = new HashSet<string> { Lamps.Start(c) };
            var q = new Queue<string>(seen);
            while (q.Count > 0) foreach (var n in Lamps.Next(q.Dequeue())) if (seen.Add(n)) q.Enqueue(n);
            Assert.Equal(360, seen.Count);
        }
    }

    [Fact]
    public void SmallLampsAreNeverABarePercent()
    {
        // A small lamp is a number tied to a condition or two tags, or +2 to an attribute (§2.3):
        // never an unconditional "+n%" on a stat.
        foreach (var l in Lamps.All.Values.Where(l => l.Kind == LampKind.Small))
            Assert.DoesNotContain(l.Effects, e => e.Do == LampDo.Mod && e.When == null && e.Skill == null);
        foreach (var l in Lamps.All.Values.Where(l => l.Kind == LampKind.Attribute))
            Assert.All(l.Effects, e => Assert.True(e.Do == LampDo.Attr && e.Value == 2, l.Id));
    }

    [Fact]
    public void ArtsNamedByLampsExistWithTheirFacets()
    {
        foreach (var l in Lamps.All.Values)
            foreach (var e in l.Effects)
            {
                if (e.Do is LampDo.Form or LampDo.Reflex or LampDo.Facet)
                    Assert.True(Abilities.Find(e.Art!) != null, $"{l.Id}: no art {e.Art}");
                if (e.Do == LampDo.Facet)
                    Assert.Contains(Abilities.Find(e.Art!)!.Facets, f => f.Id == e.Facet);
                if (e.Do is LampDo.Flare or LampDo.FlareMod)
                    Assert.NotNull(Lamps.Flare(e.Flare!));
                if (e.Skill != null && e.Phase == 1)
                    Assert.True(Weapons.All.ContainsKey(e.Skill), $"{l.Id}: no skill {e.Skill}");
            }
    }

    [Fact]
    public void ANewSurvivorHasTheirFreeLampsAndOneALevel()
    {
        var ch = Survivor("warden");
        var lit = LampBook.Now(ch).Lit;
        Assert.Equal(3, lit.Count);
        Assert.Contains(Lamps.Start("warden"), lit);
        Assert.Equal("sunderer", LampBook.Now(ch).Type);
        Assert.Equal("the_long_cut", LampBook.Carried(ch));
        Assert.Equal(0, LampBook.Spare(ch, null));
        ch.Level = 12;
        Assert.Equal(11, LampBook.Spare(ch, null));
        var w = new WorldState();
        w.Facts["arena.hollow_by_night"] = "won";
        w.Facts["arena.roost_raid"] = "won";
        w.Facts["arena.some_table_night"] = "won";
        w.Facts["lamps.atlas"] = 11;
        Assert.Equal(11 + 2 + 8, LampBook.Spare(ch, w));
    }

    [Fact]
    public void LampsAreLitNextToLitOnesPastTheirGates()
    {
        var ch = Survivor("warden", 30);
        Assert.Equal(LampNo.None, LampBook.CanLight(ch, null, "sunderer.s1"));
        Assert.Equal(LampNo.Dark, LampBook.CanLight(ch, null, "sunderer.s3"));
        // Another calling's hearth and Flares are theirs alone.
        Assert.Equal(LampNo.NotHome, LampBook.CanLight(ch, null, Lamps.Start("reaver")));
        Assert.True(LampBook.Light(ch, null, "sunderer.s1"));
        Assert.True(LampBook.Light(ch, null, "sunderer.s2"));
        // Notables open at six lamps on the road (entry, Strike, s1, s2 make four).
        Assert.Equal(LampNo.Gate, LampBook.CanLight(ch, null, "sunderer.breaking_point"));
        Assert.True(LampBook.Light(ch, null, "sunderer.s3"));
        Assert.True(LampBook.Light(ch, null, "sunderer.s4"));
        Assert.True(LampBook.Light(ch, null, "sunderer.breaking_point"));
        // Spending stops at what was earned.
        while (LampBook.Spare(ch, null) > 0) Assert.NotNull(LampBook.Suggest(ch, null) is { } id && LampBook.Light(ch, null, id) ? id : null);
        Assert.Null(LampBook.Suggest(ch, null));
        Assert.Equal(29 + 3, LampBook.Now(ch).Lit.Count);
    }

    [Fact]
    public void LampsGoOutOnlyWhileTheRestHangsTogether()
    {
        var ch = Survivor("warden", 10);
        LampBook.Light(ch, null, "sunderer.s1");
        LampBook.Light(ch, null, "sunderer.s2");
        LampBook.Light(ch, null, "sunderer.s3");
        Assert.Equal(LampNo.Holds, LampBook.CanUnlight(ch, "sunderer.s2"));
        Assert.Equal(LampNo.Free, LampBook.CanUnlight(ch, Lamps.Start("warden")));
        Assert.True(LampBook.Unlight(ch, "sunderer.s3"));
        Assert.True(LampBook.Unlight(ch, "sunderer.s2"));
        Assert.True(LampBook.Unlight(ch, "sunderer.s1"));
        LampBook.Light(ch, null, "sunderer.s1");
        LampBook.Clear(ch);
        Assert.Equal(3, LampBook.Now(ch).Lit.Count);
        Assert.Equal(9, LampBook.Spare(ch, null));
    }

    [Fact]
    public void TheTypeIsNeverALock()
    {
        var ch = Survivor("warden", 10);
        LampBook.Light(ch, null, "sunderer.s1");
        Assert.False(LampBook.SetType(ch, "butcher"));
        Assert.True(LampBook.SetType(ch, "bulwark"));
        var l = LampBook.Now(ch);
        Assert.Equal(3, l.Lit.Count);
        Assert.Contains(Lamps.Entry("bulwark"), l.Lit);
        Assert.Equal("bell_of_the_morning", LampBook.Carried(ch));
        // Two layouts: the other keeps its own.
        Assert.True(LampBook.Switch(ch, 1));
        Assert.Equal("sunderer", LampBook.Now(ch).Type);
        Assert.True(LampBook.Switch(ch, 0));
        Assert.Equal("bulwark", LampBook.Now(ch).Type);
    }

    [Fact]
    public void FlaresAreTheCallingsAndLearnedByTheirLamps()
    {
        var ch = Survivor("warden", 30);
        Assert.False(LampBook.Carry(ch, "dawn_in_the_steel"));
        Assert.False(LampBook.Carry(ch, "butchers_hour"));
        foreach (var id in new[] { "sunderer.s1", "sunderer.s2", "sunderer.s3", "sunderer.s4", "sunderer.s5", "sunderer.s6", "sunderer.s7" })
            Assert.True(LampBook.Light(ch, null, id));
        foreach (var id in new[] { "sunderer.sunder.wide_swing", "sunderer.sunder.third_blow", "sunderer.sunder.burning_edge" })
            Assert.True(LampBook.Light(ch, null, id));
        Assert.Equal(12, LampBook.Depth(ch, "sunderer"));
        Assert.True(LampBook.Light(ch, null, "sunderer.dawn_in_the_steel"));
        Assert.True(LampBook.Carry(ch, "dawn_in_the_steel"));
        Assert.Equal("dawn_in_the_steel", LampBook.Carried(ch));
        // Its lamp going out takes the Flare with it.
        Assert.True(LampBook.Unlight(ch, "sunderer.dawn_in_the_steel"));
        Assert.Equal("the_long_cut", LampBook.Carried(ch));
    }

    [Fact]
    public void ByNightSizesRunAtAQuarterAndSmallLampsOnlyLean()
    {
        var ch = Survivor("stalker", 30);
        // Light Step (the hearth's blue): +1 dash charge, a count; Nimble, a rule.
        foreach (var id in new[] { "stalker.mark_prey", "stalker.smoke_bomb", "stalker.choking_smoke", "stalker.two_prey", "stalker.executioner" })
            Assert.True(LampBook.Light(ch, null, id), id);
        Assert.True(LampBook.Light(ch, null, "stalker.light_step"));
        Assert.True(LampBook.Light(ch, null, "roadknife.s1"));
        Assert.True(LampBook.Light(ch, null, "roadknife.s2"));
        Assert.True(LampBook.Light(ch, null, "roadknife.s3"));
        Assert.True(LampBook.Light(ch, null, "roadknife.s4"));
        var day = LampBook.Loadout(ch, night: false);
        var night = LampBook.Loadout(ch, night: true);
        Assert.Equal(2, day.Attributes["finesse"]);
        Assert.Empty(night.Attributes);
        Assert.Contains(day.Mods, m => m.Stat == Stat.DashCharges && m.Value == 1);
        Assert.Contains(night.Mods, m => m.Stat == Stat.DashCharges && m.Value == 1);
        Assert.Equal(2, day.Reflexes.Count);
        Assert.Equal(2, night.Reflexes.Count);
        Assert.Contains("executioner", night.Facets);
        Assert.Equal("vault", night.Kin);
        Assert.Equal(6, night.KinWait);
        Assert.True(night.Has("opening"));
        Assert.Equal(2, night.Full("opening", "seconds"));
        // A small lamp's rule sleeps by night: its road leans the draft instead (CLASSES.md §2.10).
        Assert.Equal(0.08, day.Size("poison.dash_faster", "inc"), 6);
        Assert.Equal(0, night.Size("poison.dash_faster", "inc"));
        Assert.Equal("roadknife", night.Lean);
    }

    [Fact]
    public void ASaveFromBeforeTheLampsGetsEveryLampBack()
    {
        var ch = Survivor("reaver", 9);
        ch.Lamps = null;
        var w = new WorldState();
        w.Facts["arena.dig_boils"] = "won";
        var d = Saves.Migrate(new SaveData { Version = 4, Character = ch, World = w });
        Assert.Equal(Saves.Version, d.Version);
        Assert.NotNull(d.Character.Lamps);
        Assert.Equal("butcher", LampBook.Now(d.Character).Type);
        Assert.Equal(8 + 1, LampBook.Spare(d.Character, w));
    }

    /// <summary>Every phase-1 rule a lamp lights is read by the fight: its id appears, quoted, in the
    /// fight's code (godot/logic/Sim). A rule nobody reads would light a lamp that does nothing.</summary>
    [Fact]
    public void Every_phase_one_rule_is_read_by_the_fight()
    {
        var sim = System.IO.Path.GetFullPath(System.IO.Path.Combine(AppContext.BaseDirectory, "../../../../logic/Sim"));
        var code = string.Concat(System.IO.Directory.GetFiles(sim, "*.cs").Select(System.IO.File.ReadAllText));
        var rules = Lamps.All.Values.SelectMany(l => l.Effects).Where(e => e.Do == LampDo.Rule && e.Phase == 1 && e.Rule != null)
            .Select(e => e.Rule!).Distinct().ToList();
        Assert.True(rules.Count >= 130, $"only {rules.Count} phase-1 rules");
        var unread = rules.Where(r => !code.Contains($"\"{r}\"")).OrderBy(r => r).ToList();
        Assert.True(unread.Count == 0, "unread: " + string.Join(", ", unread));
        // The staged Flares' modifier lamps, live from phase 2 (Sim/FlareStaged.cs).
        var mods = Lamps.All.Values.SelectMany(l => l.Effects).Where(e => e.Do == LampDo.FlareMod && e.Phase <= Lamps.LivePhase && e.Rule != null)
            .Select(e => e.Rule!).Distinct().ToList();
        Assert.Equal(12, mods.Count);
        var dark = mods.Where(r => !code.Contains($"\"{r}\"")).OrderBy(r => r).ToList();
        Assert.True(dark.Count == 0, "unread flare mods: " + string.Join(", ", dark));
    }
}
