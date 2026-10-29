using System.Collections.Generic;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The tutorial's line of callouts (logic/Play/Teach.cs): once a profile, one at a time,
/// waiting while the screen is busy, let go unseen when its moment passes, nothing with tips off.</summary>
public class TeachTests
{
    static Callout Freeze(string id) => new(id, CalloutKind.Freeze, id, "A line.", Aim.At("dash"));
    static Callout Arrow(string id) => new(id, CalloutKind.Arrow, id, "A line.", Aim.At("chain"));
    static Callout Panel(string id) => new(id, CalloutKind.Panel, id, "A line.", Aim.At("cards"));
    static Presence Here(Callout _) => Presence.Here;

    [Fact]
    public void ShowsOncePerProfile()
    {
        var mem = new TeachMemory();
        var t = new Teacher(mem);
        Assert.True(t.Offer(Freeze("dash"), 0));
        Assert.Equal("dash", t.Update(0, 0, Busy.None, Here)?.Id);
        t.Close("key", 1);
        Assert.True(mem.Seen("dash"));
        Assert.False(t.Offer(Freeze("dash"), 2));
        Assert.Null(t.Update(2, 2, Busy.None, Here));
        // A new teacher on the same profile remembers.
        Assert.False(new Teacher(mem).Offer(Freeze("dash"), 0));
    }

    [Fact]
    public void NeverTwoAtOnceAndInOrder()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Freeze("a"), 0);
        t.Offer(Freeze("b"), 0);
        Assert.False(t.Offer(Freeze("a"), 0));
        Assert.Equal("a", t.Update(0, 0, Busy.None, Here)?.Id);
        Assert.Null(t.Update(0.1, 0.1, Busy.None, Here));
        Assert.Equal("a", t.Current?.Id);
        t.Close("key", 0.6);
        // (a breath of play after a freeze before the next)
        Assert.Null(t.Update(1, 1, Busy.None, Here));
        Assert.Equal("b", t.Update(1.6, 1.6, Busy.None, Here)?.Id);
    }

    [Fact]
    public void WaitsWhileTheScreenIsBusy()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Freeze("a"), 0);
        foreach (var b in new[] { Busy.Cinematic, Busy.Transit, Busy.Fall, Busy.Overlay, Busy.Draft, Busy.Banner, Busy.Say, Busy.Prompt, Busy.Hint })
            Assert.Null(t.Update(1, 1, b, Here));
        Assert.Equal("a", t.Update(2.6, 2.6, Busy.None, Here)?.Id);
    }

    [Fact]
    public void PanelBelongsOnTheDraft()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Panel("great"), 0);
        Assert.Null(t.Update(0.1, 0.1, Busy.None, Here));
        Assert.Null(t.Update(0.2, 0.2, Busy.Draft | Busy.Cinematic, Here));
        Assert.Equal("great", t.Update(0.3, 0.3, Busy.Draft | Busy.Say, Here)?.Id);
        // It ends with the panel.
        Assert.Null(t.Update(0.3, 5, Busy.Draft, Here));
        Assert.NotNull(t.Current);
        t.Update(0.4, 6, Busy.None, Here);
        Assert.Null(t.Current);
        Assert.True(t.Memory.Seen("great"));
    }

    [Fact]
    public void DroppedUnseenComesBackLater()
    {
        var mem = new TeachMemory();
        var t = new Teacher(mem);
        var log = new List<string>();
        t.Log = (what, c, _) => log.Add($"{c.Id} {what}");
        t.Offer(Freeze("a"), 0);
        // Waited past its patience behind a busy screen: let go, unseen.
        Assert.Null(t.Update(9, 9, Busy.Say, Here));
        Assert.Equal(0, t.Waiting);
        Assert.False(mem.Seen("a"));
        Assert.Contains("a dropped", log);
        // Not again at once, but later it is taken again and shows.
        Assert.False(t.Offer(Freeze("a"), 9.5));
        Assert.True(t.Offer(Freeze("a"), 12));
        Assert.Equal("a", t.Update(12, 12, Busy.None, Here)?.Id);
    }

    [Fact]
    public void TargetGoneIsDroppedAndNotYetWaits()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Freeze("gone"), 0);
        t.Offer(Freeze("later"), 0);
        var where = new Dictionary<string, Presence> { ["gone"] = Presence.Gone, ["later"] = Presence.NotYet };
        Assert.Null(t.Update(1, 1, Busy.None, c => where[c.Id]));
        Assert.False(t.Queued("gone"));
        Assert.True(t.Queued("later"));
        where["later"] = Presence.Here;
        Assert.Equal("later", t.Update(2, 2, Busy.None, c => where[c.Id])?.Id);
    }

    [Fact]
    public void ArrowEndsInTimeAndAnUnreadOneComesBack()
    {
        var mem = new TeachMemory();
        var t = new Teacher(mem);
        t.Offer(Arrow("bar"), 0);
        t.Update(0, 0, Busy.None, Here);
        // A draft cuts it off a second in: unread, so not seen.
        t.Update(1, 1, Busy.Draft, Here);
        Assert.Null(t.Current);
        Assert.False(mem.Seen("bar"));
        Assert.True(t.Offer(Arrow("bar"), 4));
        t.Update(4, 10, Busy.None, Here);
        t.Update(4, 14.1, Busy.None, Here);
        Assert.Null(t.Current);
        Assert.True(mem.Seen("bar"));
    }

    [Fact]
    public void FreezeHoldsBeforeItCanBeGoneOn()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Freeze("a"), 0);
        t.Update(0, 10, Busy.None, Here);
        Assert.False(t.CanContinue(10.2));
        Assert.True(t.CanContinue(10.6));
    }

    [Fact]
    public void TipsOffShowsNothing()
    {
        var mem = new TeachMemory { Tips = false };
        var t = new Teacher(mem);
        Assert.False(t.Offer(Freeze("a"), 0));
        Assert.Null(t.Update(0, 0, Busy.None, Here));
        // Turned off while one waits: it never shows.
        mem.Tips = true;
        t.Offer(Freeze("b"), 0);
        mem.Tips = false;
        Assert.Null(t.Update(0, 0, Busy.None, Here));
        Assert.Equal(0, t.Waiting);
    }

    static Callout OnGround(string id) => new(id, CalloutKind.Freeze, id, "A line.", Aim.In(() => [(1.0, 0.0, 2.0)]));

    [Fact]
    public void TransientFreezeGoesOverAHintButNotACaption()
    {
        var t = new Teacher(new TeachMemory());
        Assert.True(OnGround("red_line").Transient);
        Assert.False(Freeze("dash").Transient);
        Assert.False(new Callout("bar", CalloutKind.Arrow, "b", "l", Aim.In(() => [(0.0, 0.0, 0.0)])).Transient);
        t.Offer(Freeze("dash"), 0);
        t.Offer(OnGround("red_line"), 0);
        // A hint holds the dash's freeze; the red line's goes over it.
        Assert.Equal("red_line", t.Update(0, 0, Busy.Hint, Here)?.Id);
        t.Close("key", 1);
        // Captions, banners, prompts, cinematics still hold it.
        var u = new Teacher(new TeachMemory());
        u.Offer(OnGround("red_line"), 0);
        foreach (var b in new[] { Busy.Say, Busy.Banner, Busy.Cinematic, Busy.Say | Busy.Hint, Busy.Say | Busy.Prompt })
            Assert.Null(u.Update(1, 1, b, Here));
        Assert.Equal("red_line", u.Update(2, 2, Busy.Hint | Busy.Prompt, Here)?.Id);
    }

    [Fact]
    public void WaitsWhileADraftIsOwedUnlessAPanel()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Freeze("dash"), 0);
        t.Offer(Panel("great"), 0);
        Assert.Null(t.Update(0.1, 0.1, Busy.Owed, Here));
        Assert.Equal("great", t.Update(0.2, 0.2, Busy.Draft | Busy.Owed, Here)?.Id);
        t.Update(0.2, 3, Busy.None, Here);
        Assert.Null(t.Current);
        // The draft was a pause: the dash waits a breath of play after it.
        Assert.Null(t.Update(1.0, 4, Busy.None, Here));
        Assert.Equal("dash", t.Update(1.8, 5, Busy.None, Here)?.Id);
    }

    [Fact]
    public void GapAfterAFreezeHoldsTheNextFreezeAndArrow()
    {
        var t = new Teacher(new TeachMemory());
        var log = new List<string>();
        t.Log = (what, c, _) => log.Add($"{c.Id} {what} {t.LogWaited}");
        t.Offer(Freeze("a"), 0);
        t.Offer(Arrow("b"), 0);
        t.Update(0, 0, Busy.None, Here);
        t.Close("key", 1);
        Assert.Null(t.Update(0, 2, Busy.None, Here));
        Assert.Null(t.Update(1.4, 3, Busy.None, Here));
        Assert.Equal("b", t.Update(1.5, 4, Busy.None, Here)?.Id);
        Assert.Contains("b shown gap", log);
    }

    [Fact]
    public void PrerequisitesInOrder()
    {
        var t = new Teacher(new TeachMemory());
        var log = new List<string>();
        t.Log = (what, c, _) => log.Add($"{c.Id} {what} {t.LogWaited}");
        var bar = Arrow("ember_bar") with { After = "ember_ground" };
        t.Offer(bar, 0);
        // Its forerunner not yet offered: it waits.
        Assert.Null(t.Update(0, 0, Busy.None, Here));
        t.Offer(Freeze("ember_ground"), 0.5);
        Assert.Equal("ember_ground", t.Update(0.5, 0.5, Busy.None, Here)?.Id);
        t.Close("key", 2);
        Assert.Null(t.Update(1, 3, Busy.None, Here));
        Assert.Equal("ember_bar", t.Update(2.1, 4, Busy.None, Here)?.Id);
        Assert.Contains("ember_bar shown gap,prereq", log);
    }

    [Fact]
    public void APrerequisiteWhoseMomentLapsedNoLongerHolds()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Freeze("first"), 0);
        // Its target gone before it could show: dropped, and not asked for again.
        t.Update(0.1, 0.1, Busy.None, _ => Presence.Gone);
        t.Offer(Arrow("second") with { After = "first" }, 0.2);
        Assert.Null(t.Update(1, 1, Busy.None, Here));
        Assert.False(t.Lapsed("first", 2));
        Assert.True(t.Lapsed("first", 2.6));
        Assert.Equal("second", t.Update(2.6, 2.6, Busy.None, Here)?.Id);
    }

    [Fact]
    public void AnAimHoldsSeveralTargets()
    {
        // F8: the art's ring on the console and the Grave-Caller; F9: each lit lamp.
        var art = new Aim { Hud = "art", World = () => [(4.0, 1.4, 2.0)] };
        Assert.Equal("art", art.Hud);
        Assert.Single(art.World!());
        var lamps = Aim.In(() => [(0.0, 2.2, 0.0), (5.0, 2.2, 0.0), (10.0, 2.2, 0.0)]);
        Assert.Equal(3, lamps.World!().Count);
        Assert.True(new Callout("art", CalloutKind.Freeze, "Art", "l", art, "flare").Transient);
    }

    [Fact]
    public void LogSaysWhatItWaitedOn()
    {
        var t = new Teacher(new TeachMemory());
        var log = new List<string>();
        t.Log = (what, c, how) => log.Add($"{c.Id} {what} {t.LogWaited}");
        t.Offer(Freeze("a"), 0, Busy.Say | Busy.Hint);
        t.Update(0.5, 0.5, Busy.Say, Here);
        t.Update(1, 1, Busy.Banner, Here);
        t.Update(2, 2, Busy.None, Here);
        Assert.Equal(["a queued say,tip", "a shown banner,say"], log);
    }

    [Fact]
    public void ALessonKeepsItsQuiet()
    {
        // (au1 item 14) a lesson comes only once the screen has been clear its quiet: 4 s after a line ends.
        var t = new Teacher(new TeachMemory());
        var lesson = Arrow("tally") with { Quiet = 4, Patience = 30 };
        t.Offer(lesson, 0, Busy.Say);
        Assert.Null(t.Update(0, 0, Busy.Say, Here));
        Assert.Null(t.Update(3, 3, Busy.Say, Here));
        // (the line ended at 3: not at 5, at 7)
        Assert.Null(t.Update(5, 5, Busy.None, Here));
        Assert.Equal("tally", t.Update(7.1, 7.1, Busy.None, Here)?.Id);
        // (its 4 s up, the arrow ends on the step at 11.2)
        Assert.Null(t.Update(11.2, 11.2, Busy.None, Here));
        Assert.Null(t.Current);
        // (and from the end of another callout too)
        var next = Arrow("card") with { Quiet = 4, Patience = 30 };
        t.Offer(next, 11.1);
        Assert.Null(t.Update(13, 13, Busy.None, Here));
        Assert.Equal("card", t.Update(15.2, 15.2, Busy.None, Here)?.Id);
    }

    [Fact]
    public void ThePromptsLessonPointsAtThePrompt()
    {
        // (a callout on the interact prompt isn't held back by the prompt; any other is)
        var t = new Teacher(new TeachMemory());
        t.Offer(new Callout("talk", CalloutKind.Arrow, "Talk", "A line.", Aim.At("prompt")), 0);
        t.Offer(Arrow("other"), 0);
        Assert.Equal("talk", t.Update(0, 0, Busy.Prompt, Here)?.Id);
        t.Close("time", 4);
        Assert.Null(t.Update(5, 5, Busy.Prompt, Here));
    }

    [Fact]
    public void ALessonWhoseCalmEndsIsLetGo()
    {
        // (the tally's calm ends when the ditch rises: it is let go unseen, never shown in the fight)
        var t = new Teacher(new TeachMemory());
        bool calm = true;
        var log = new List<string>();
        t.Log = (what, c, how) => log.Add($"{what} {how}");
        t.Offer(Arrow("tally") with { Quiet = 4, Patience = 30, Still = () => calm }, 0, Busy.Say);
        Assert.Null(t.Update(1, 1, Busy.Say, Here));
        calm = false;
        Assert.Null(t.Update(6, 6, Busy.None, Here));
        Assert.False(t.Queued("tally"));
        Assert.Contains("dropped passed", log);
    }
}
