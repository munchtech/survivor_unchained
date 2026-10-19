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
        Assert.Equal("b", t.Update(0.7, 0.7, Busy.None, Here)?.Id);
    }

    [Fact]
    public void WaitsWhileTheScreenIsBusy()
    {
        var t = new Teacher(new TeachMemory());
        t.Offer(Freeze("a"), 0);
        foreach (var b in new[] { Busy.Cinematic, Busy.Transit, Busy.Fall, Busy.Overlay, Busy.Draft, Busy.Banner, Busy.Say, Busy.Prompt, Busy.Hint })
            Assert.Null(t.Update(1, 1, b, Here));
        Assert.Equal("a", t.Update(2, 2, Busy.None, Here)?.Id);
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
}
