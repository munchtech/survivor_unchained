using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>CODEX_audit.md installment 8 (SU-046..SU-049): the Lamps screen's wick panel, Light my way, a link's pick and
/// the carried Flare, each decided in logic and taken into the running fight by the one reconcile (Journey.RefreshKit).</summary>
[Collection("Balance")]
public class LampChoicesTests : System.IDisposable
{
    // (the live board, v2: other tests in the collection leave the v1 board up)
    readonly bool v2 = Lamps.V2;
    public LampChoicesTests() => Lamps.UseV2(true);
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

    static Battle Campaign(Journey j) => j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 3);

    /// <summary>A carried skill with a wick whose path runs past her rank's first lamps (room for held points to show).</summary>
    static string WickSkill(Journey j) =>
        SkillBook.Carried(j.Ch).Select(c => c.Id).First(id => Wicks.Of(id) != null && WickBook.Path(j.Ch, id).Length >= 4 && SkillBook.Rank(j.Ch) >= 3);

    /// <summary>SU-046: with points held, the panel lights what the day fight lights (before: path.Take(SkillBook.Rank),
    /// the held lamps shown lit) and names the held lamps apart; in an arena it reads the night build, read-only.</summary>
    [Fact]
    public void The_wick_panel_lights_what_the_day_fight_lights_and_shows_held_points_apart()
    {
        var j = New();
        var skill = WickSkill(j);
        var b = Campaign(j);
        WickBook.Hold(j.Ch, skill, 2);
        j.RefreshKit(b);
        int held = WickBook.Held(j.Ch, skill);
        var v = WickBook.Panel(j.Ch, skill, night: false);
        var w = Assert.Single(b.Weapons, x => x.Id == skill);
        Assert.Equal(w.Wick!.Lit, v.Lit);
        Assert.Equal(WickBook.DayRank(j.Ch, skill), v.Rank);
        Assert.NotEqual(WickBook.Path(j.Ch, skill).Take(SkillBook.Rank(j.Ch)).ToArray(), v.Lit);
        Assert.True(held >= 2);
        Assert.Equal(System.Math.Min(held, WickBook.Path(j.Ch, skill).Length - v.Lit.Length), v.Held.Length);
        Assert.Empty(v.Held.Intersect(v.Lit));
        Assert.Equal(WickBook.Path(j.Ch, skill).Skip(v.Lit.Length).Take(held), v.Held);
        Assert.False(v.ReadOnly);

        var n = WickBook.Panel(j.Ch, skill, night: true);
        Assert.True(n.ReadOnly);
        Assert.Empty(n.Held);
        Assert.Equal(WickBook.Path(j.Ch, skill).Take(WickBook.RankIn(j.Ch, skill, true)), n.Lit);
    }

    /// <summary>SU-047: Light my way is one command (LampBook.LightMyWay): with no board lamp left to light it still
    /// burns the held wick points (before: the board's own loop refused, held points stayed held), and the fight takes
    /// the rank up by the reconcile.</summary>
    [Fact]
    public void Light_my_way_burns_held_wick_points_with_no_lamp_left_to_light()
    {
        var j = New();
        var skill = WickSkill(j);
        var b = Campaign(j);
        LampBook.LightSuggested(j.Ch, null);
        Assert.Null(LampBook.Suggest(j.Ch, null));
        WickBook.Hold(j.Ch, skill, 2);
        j.RefreshKit(b);
        int all = LampBook.Now(j.Ch).Held!.Values.Sum();
        int heldRank = Assert.Single(b.Weapons, x => x.Id == skill).Rank;
        Assert.True(LampBook.LightMyWayWaits(j.Ch, null));
        var (lit, burned) = LampBook.LightMyWay(j.Ch, null);
        Assert.Empty(lit);
        Assert.Equal(all, burned);
        Assert.Equal(0, WickBook.Held(j.Ch, skill));
        Assert.False(LampBook.LightMyWayWaits(j.Ch, null));
        j.RefreshKit(b);
        var w = Assert.Single(b.Weapons, x => x.Id == skill);
        Assert.Equal(WickBook.DayRank(j.Ch, skill), w.Rank);
        Assert.True(w.Rank > heldRank, $"rank {w.Rank} after, {heldRank} held");
        Assert.Equal(WickBook.Panel(j.Ch, skill, false).Lit, w.Wick!.Lit);
    }

    /// <summary>SU-048: a lit link's chooser steps through every skill it may fire (LinkChoices), binds each (SetLinkPick:
    /// kept on her layout), and the running fight's lamps carry the pick after the reconcile. Before: no caller.</summary>
    [Fact]
    public void A_lit_links_chooser_binds_each_skill_it_may_fire_and_the_fight_takes_it()
    {
        var j = New();
        var link = Lamps.All.Values.Where(d => d.Effects.Any(e => e.Rule == "link"))
            .Select(d => d.Id).OrderBy(id => id).First(id => LampBook.LightPath(j.Ch, null, id));
        var b = Campaign(j);
        var choices = LampBook.LinkChoices(j.Ch, link);
        Assert.True(choices.Count >= 2, $"{link}: {choices.Count} choices");
        var seen = new System.Collections.Generic.List<string>();
        for (int i = 0; i < choices.Count; i++)
        {
            var pick = LampBook.NextLinkPick(j.Ch, link)!;
            seen.Add(pick);
            Assert.Equal(pick, LampBook.LinkPick(j.Ch, link));
            Assert.Equal(pick, LampBook.Now(j.Ch).Links[link]);
            j.RefreshKit(b);
            Assert.Equal(pick, b.Lamps.Links[link]);
        }
        Assert.Equal(choices.OrderBy(x => x), seen.OrderBy(x => x));
    }

    /// <summary>SU-049: a learned second Flare (sunderer.dawn_in_the_steel) is carried from its lit lamp (FlareOf, Carry)
    /// and the running fight takes it up at once; before, only the dev --flare switch called Carry.</summary>
    [Fact]
    public void A_learned_flare_is_carried_from_its_lamp_and_the_running_fight_takes_it_up()
    {
        var j = New(level: 60);
        const string lamp = "sunderer.dawn_in_the_steel";
        string was = LampBook.Carried(j.Ch);
        Assert.True(LampBook.LightPath(j.Ch, null, lamp), "the path to " + lamp);
        var fl = LampBook.FlareOf(j.Ch, lamp);
        Assert.NotNull(fl);
        Assert.Contains(fl, LampBook.Learned(j.Ch));
        Assert.NotEqual(fl, LampBook.Carried(j.Ch));
        var b = Campaign(j);
        Assert.Equal(was, b.Flare?.Id);
        Assert.True(LampBook.Carry(j.Ch, fl!));
        j.RefreshKit(b);
        Assert.Equal(fl, b.Flare?.Id);
        Assert.Equal(fl, Campaign(j).Flare?.Id);
        Assert.Null(LampBook.FlareOf(j.Ch, "sunderer.s1"));
    }
}
