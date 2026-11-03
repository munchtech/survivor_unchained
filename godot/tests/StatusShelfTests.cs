using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>UI 28: the HUD's status shelf (Play/StatusShelf.cs): timer fraction from the max seen, priority,
/// overflow, the pin's syntax.</summary>
public class StatusShelfTests
{
    static StatusShelf.Entry E(string key, string glyph, bool good, double left, int stacks = 0) => new(key, glyph, good, left, stacks);

    [Fact]
    public void TimerDrainsFromTheMaxSeenAndResetsWhenRefreshed()
    {
        var s = new StatusShelf();
        s.Update([E("burn", "flame", false, 4)]);
        Assert.Equal(1f, s.Debuffs[0].Fraction);
        s.Update([E("burn", "flame", false, 1)]);
        Assert.Equal(0.25, (double)s.Debuffs[0].Fraction, 3);
        Assert.True(s.Debuffs[0].Pulse);
        s.Update([E("burn", "flame", false, 3)]);   // refreshed: its new start
        Assert.Equal(1f, s.Debuffs[0].Fraction);
        s.Update([E("aura", "arcane", true, 9e9)]);
        Assert.True(s.Buffs[0].Permanent);
        Assert.False(s.Buffs[0].Pulse);
        Assert.Empty(s.Debuffs);
    }

    [Fact]
    public void PriorityThenFirstSeen()
    {
        var s = new StatusShelf();
        s.Update([E("w", "hourglass", true, 5), E("a", "arcane", true, 5), E("h", "howl", true, 5)]);
        s.Update([E("w", "hourglass", true, 5), E("a", "arcane", true, 5), E("h", "howl", true, 5), E("bar", "aegis", true, 5), E("p", "plague", false, 5), E("s", "boot", false, 5)]);
        Assert.Equal(["bar", "a", "h", "w"], s.Buffs.Select(x => x.Key));
        Assert.Equal(["s", "p"], s.Debuffs.Select(x => x.Key));
    }

    [Fact]
    public void OverflowShowsSixAndAMore()
    {
        var s = new StatusShelf();
        var l = new List<StatusShelf.Entry>();
        for (int i = 0; i < 9; i++) l.Add(E("b" + i, "arcane", true, 5));
        for (int i = 0; i < 7; i++) l.Add(E("d" + i, "flame", false, 5));
        s.Update(l);
        Assert.Equal(7, s.Buffs.Count);
        Assert.Equal(3, s.Buffs[6].More);
        Assert.Equal(7, s.Debuffs.Count);
        Assert.Equal(0, s.Debuffs[6].More);
    }

    [Fact]
    public void PinParses()
    {
        var p = StatusShelf.Parse("b:aegis:6:8+d:flame:3:5:4");
        Assert.Equal(2, p.Count);
        Assert.True(p[0].Good);
        Assert.Equal(8, p[0].Max);
        Assert.Equal(4, p[1].Stacks);
        var s = new StatusShelf();
        s.Update(p);
        Assert.Equal(0.75, (double)s.Buffs[0].Fraction, 3);
        Assert.Equal(0.6, (double)s.Debuffs[0].Fraction, 3);
    }
}
