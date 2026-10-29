using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Drowned Girl's experience light (logic/Play/XpLight.cs, UI 18 pick (c)): nothing at rest; a gain runs
/// to the fraction, holds and fades; gains batch (one run a second, the held front sliding on); a level-up lights all;
/// the fraction maps onto the run; the numbers' card and its hold key.</summary>
public class XpLightTests
{
    static XpLight Fresh(double f = 0.2, int lv = 3, bool ember = true)
    {
        var x = new XpLight();
        x.Feed(f, lv, ember);
        x.Step(5);
        return x;
    }

    static void Run(XpLight x, double sec) { for (double t = 0; t < sec - 1e-9; t += 1 / 60.0) x.Step(Math.Min(1 / 60.0, sec - t)); }

    static readonly XpLight.XpRest Knobs = new(0.3, 0.5, 90, 0.8, 2.0);

    [Fact]
    public void AtRestTheGlowIsStatic()
    {
        var x = Fresh();
        Assert.True(x.Lit);
        Assert.True(x.Resting);
        double tail = x.Tail, peak = x.Peak, front = x.Front;
        x.Feed(0.2, 3, true);
        Run(x, 3);
        Assert.Equal(0, x.Strength);
        Assert.Equal(0.2, x.Front, 6);
        Assert.Equal(x.K.RestTail, x.Tail, 6);
        Assert.Equal(x.K.RestFront, x.Peak, 6);
        Assert.Equal((tail, peak, front), (x.Tail, x.Peak, x.Front));   // nothing moves at rest
    }

    [Fact]
    public void LoadingShowsTheRestingGlow()
    {
        var x = new XpLight(Knobs);
        x.Feed(0.7, 9, false);
        Run(x, 0.3);
        Assert.True(x.Resting);                        // no run: the glow at the fraction
        Assert.Equal(0, x.Strength);
        Assert.Equal(0.7, x.Front, 6);
        Assert.False(x.Rose);
        Run(x, 89);
        Assert.True(x.Resting);                        // the quiet clock started at the load
        Run(x, 3);
        Assert.True(x.Dark);
    }

    [Fact]
    public void AGainRunsHoldsAndFades()
    {
        var x = Fresh();
        x.Feed(0.5, 3, true);
        Run(x, 0.3);
        Assert.True(x.Lit);
        Assert.InRange(x.Front, 0.05, 0.49);           // on its way from her hair
        Run(x, 0.35);
        Assert.Equal(0.5, x.Front, 3);                 // at the fraction by 0.6 s
        Run(x, 1.3);
        Assert.Equal(1, x.Strength, 3);                // held ~1.5 s
        Run(x, 0.4);
        Assert.InRange(x.Strength, 0.01, 0.99);        // settling
        Assert.InRange(x.Tail, x.K.RestTail + 0.01, 0.99);
        Run(x, 0.6);
        Assert.True(x.Resting);                        // at rest by ~2.9 s: dim, not dark
        Assert.Equal(0.5, x.Front, 6);
        Assert.Equal(x.K.RestTail, x.Tail, 6);
        Assert.Equal(x.K.RestFront, x.Peak, 6);
    }

    [Fact]
    public void DarkAfterTheLongQuietThenStraightBack()
    {
        var x = new XpLight(Knobs);
        x.Feed(0.2, 3, true);
        Run(x, 5);
        x.Feed(0.4, 3, true);
        Run(x, 3);
        Assert.True(x.Resting);
        Run(x, 86.5);                                  // 89.5 s since the gain
        Assert.True(x.Resting);
        Run(x, 1.0);                                   // 90.5 s: fading, slowly
        Assert.InRange(x.RestLevel, 0.6, 0.9);
        Run(x, 1.6);                                   // 92.1 s: dark
        Assert.True(x.Dark);
        Assert.False(x.Lit);
        Assert.Equal(0, x.Tail);
        Assert.Equal(0, x.Peak);
        x.Feed(0.45, 3, true);                         // the next gain: the run plays as ever, from her hair
        Run(x, 0.2);
        Assert.True(x.Lit);
        Assert.InRange(x.Front, 0.01, 0.44);
        Assert.True(x.Strength > 0.9);
        Run(x, 3);
        Assert.True(x.Resting);                        // and settles back to the glow
        Assert.Equal(0.45, x.Front, 6);
    }

    [Fact]
    public void ZoneEntryRestsAndRestartsTheQuiet()
    {
        var x = new XpLight(Knobs);
        x.Feed(0.3, 3, true);
        Run(x, 100);
        Assert.True(x.Dark);
        x.Wake();                                      // into a zone
        Assert.True(x.Resting);
        Assert.Equal(0.3, x.Front, 6);
        Run(x, 89);
        Assert.True(x.Resting);
        Run(x, 3.1);
        Assert.True(x.Dark);
        var y = new XpLight(Knobs);
        y.Wake();                                      // before the first reading: nothing to show yet, no throw
        y.Feed(0.6, 2, false);
        Assert.True(y.Resting);
    }

    [Fact]
    public void TheKnobsAreData()
    {
        var file = XpLight.XpRest.Parse(SurvivorUnchained.Core.Json.ReadContent("hud.json"));
        Assert.Equal(XpLight.XpRest.Game, file);       // the game reads hud.json
        Assert.InRange(file.RestTail, 0.05, 0.6);
        Assert.InRange(file.RestFront, 0.05, 0.8);
        Assert.InRange(file.Quiet, 10, 600);
        var k = XpLight.XpRest.Parse("{\"xpLight\":{\"restTail\":0.2,\"restFront\":0.4,\"quiet\":30,\"settle\":1.5,\"darkFade\":3}}");
        Assert.Equal(new XpLight.XpRest(0.2, 0.4, 30, 1.5, 3), k);
        var x = new XpLight(k);
        x.Feed(0.5, 1, true);
        Assert.Equal(0.2, x.Tail, 6);
        Assert.Equal(0.4, x.Peak, 6);
        Run(x, 31.6);
        Assert.InRange(x.RestLevel, 0.3, 0.7);
        // missing knobs, a bad value, bad JSON: the defaults
        var d = new XpLight.XpRest();
        Assert.Equal(d with { Quiet = 45 }, XpLight.XpRest.Parse("{\"xpLight\":{\"quiet\":45}}"));
        Assert.Equal(d, XpLight.XpRest.Parse("{\"xpLight\":{\"restTail\":7}}"));
        Assert.Equal(d, XpLight.XpRest.Parse("{}"));
        Assert.Equal(d, XpLight.XpRest.Parse("not json"));
    }

    [Fact]
    public void GainsBatchAndTheFrontSlides()
    {
        var x = Fresh(0.1);
        x.Feed(0.2, 3, true);
        Run(x, 0.8);
        Assert.Equal(0.2, x.Front, 3);
        // gains every 0.25 s for 4 s: one light that stays up, its front sliding forward as a meter
        double f = 0.2, last = x.Front;
        for (int i = 0; i < 16; i++)
        {
            f += 0.03;
            x.Feed(f, 3, true);
            Run(x, 0.25);
            Assert.True(x.Lit);
            Assert.Equal(1, x.Strength, 3);
            Assert.True(x.Front >= last - 1e-9, "the front never runs back to her hair while gains keep coming");
            last = x.Front;
        }
        Assert.InRange(x.Front, f - 0.04, f + 1e-9);
    }

    [Fact]
    public void AtMostOneRunASecond()
    {
        var x = Fresh(0.1);
        x.Feed(0.3, 4, true);   // a level-up (the whole lights; the run waits)
        Assert.True(x.Rose);
        Run(x, 0.2);
        x.Feed(0.35, 4, true);  // a gain 0.2 s later: no run yet
        Run(x, 0.1);
        Assert.Equal(0, x.Strength);
        Run(x, 1.0);            // the gap is past and the whole is done: the waiting run starts from her hair
        Assert.True(x.Strength > 0);
        Assert.True(x.Front < 0.35);
    }

    [Fact]
    public void ACaughtFadeComesBackUpWhereItIs()
    {
        var x = Fresh(0.1);
        x.Feed(0.4, 3, true);
        Run(x, 2.2);                                   // fading
        double front = x.Front;
        Assert.True(x.Strength < 1);
        x.Feed(0.45, 3, true);
        Run(x, 0.2);
        Assert.Equal(1, x.Strength, 3);
        Assert.True(x.Front >= front, "no new run from her hair");
    }

    [Fact]
    public void ALevelUpIsNamedOverTheRiverForAboutTwoSeconds()
    {
        var x = Fresh(0.9, 4);
        Assert.Equal(0, x.Title);
        x.Feed(0.05, 5, true);
        Run(x, 0.3);
        Assert.Equal(1, x.Title, 3);                   // in quickly
        Run(x, 1.8);
        Assert.Equal(1, x.Title, 3);                   // held past the light's own moment (2.1 s)
        Run(x, 0.4);
        Assert.InRange(x.Title, 0.01, 0.99);           // fading
        Run(x, 0.4);
        Assert.Equal(0, x.Title);                      // gone by 2.9 s
        x.Feed(0.05, 6, true);
        x.Wake();
        Assert.Equal(0, x.Title);                      // a zone change clears it
        Assert.Equal(1, XpLight.Posed(0.1, 0.3, rise: true).Title, 3);
    }

    [Fact]
    public void ALevelUpLightsAllForItsMoment()
    {
        var x = Fresh(0.9, 4);
        x.Feed(0.05, 5, true);
        Assert.True(x.Rose);
        Run(x, 0.2);
        Assert.Equal(1, x.Whole, 3);
        Assert.Equal(0, x.Strength);
        Run(x, 1.2);
        Assert.Equal(0, x.Whole);
        Assert.True(x.Resting);                        // then the glow at what carried over
        Assert.Equal(0.05, x.Front, 6);
        x.Feed(0.05, 5, true);
        Assert.False(x.Rose);                          // named once
    }

    [Fact]
    public void DayToNightOrALossSettlesWithoutARun()
    {
        var x = Fresh(0.2);
        x.Feed(0.5, 3, true);
        Run(x, 0.3);
        x.Feed(0.6, 7, false);                         // the ember out: her own experience, by day
        Assert.True(x.Resting);
        Assert.Equal(0.6, x.Front, 6);
        Assert.False(x.Rose);
        var y = Fresh(0.2, 3);
        y.Feed(0.5, 3, true);
        Run(y, 0.3);
        y.Feed(0.1, 1, true);                          // a new night: the ember from 1
        Assert.True(y.Resting);
        Assert.Equal(0.1, y.Front, 6);
    }

    [Fact]
    public void PosedPinsMatchTheClock()
    {
        var a = XpLight.Posed(0.7, 1.0);
        Assert.Equal(0.7, a.Front, 3);
        Assert.Equal(1, a.Strength, 3);
        Assert.Equal(0, XpLight.Posed(0.7, 3.0).Strength);
        var r = XpLight.PosedRest(0.3, Knobs);
        Assert.True(r.Resting);
        Assert.Equal(0.3, r.Front, 6);
        Assert.True(XpLight.PosedDark(0.3, Knobs).Dark);
        Assert.Equal(1, XpLight.Posed(0.2, 0.3, rise: true).Whole, 3);
    }

    [Fact]
    public void ARunSweepsTheRingFromWhereItStood()
    {
        // UI 23: the coin's ring never empties to refill: a gain sweeps it on from the fraction it showed
        var x = Fresh(0.2);
        Run(x, 0.1);
        Assert.Equal(0.2, x.Front, 6);
        x.Feed(0.5, 3, true);
        double last = x.Front;
        for (int i = 0; i < 40; i++)
        {
            Run(x, 1 / 60.0);
            Assert.InRange(x.Front, 0.2 - 1e-9, 0.5 + 1e-9);
            Assert.True(x.Front >= last - 1e-9);
            last = x.Front;
        }
        Assert.Equal(0.5, x.Front, 3);
        var k = XpLight.RingLook.Parse("{\"xpRing\":{\"titleGap\":12,\"shineTravel\":4,\"shinePeriod\":2}}");
        Assert.Equal(12, k.TitleGap);
        Assert.Equal(4, k.ShinePeriod);                 // never shorter than its travel
        Assert.Equal(new XpLight.RingLook(), XpLight.RingLook.Parse("not json"));
        Assert.Equal(XpLight.RingLook.Game, XpLight.RingLook.Parse(SurvivorUnchained.Core.Json.ReadContent("hud.json")));
    }

    [Fact]
    public void TheCardsWords()
    {
        var d = XpLight.Lines(false, 12, 4210, 6000, false);
        Assert.Equal(("Level 12", "70%", "4,210 / 6,000 experience", "1,790 to level 13"), d);
        var n = XpLight.Lines(true, 4, 42, 60, false);
        Assert.Equal(("Ember 4", "70%", "42 / 60 ember tonight", "18 to ember 5"), n);
        Assert.Equal("the last level", XpLight.Lines(false, 30, 0, 1, true).Count);
    }

    [Fact]
    public void TheHoldKey()
    {
        Assert.True(XpLight.TipShown(hover: false, held: true, captured: false));
        Assert.True(XpLight.TipShown(hover: true, held: false, captured: false));
        Assert.False(XpLight.TipShown(hover: true, held: true, captured: true));
        Assert.False(XpLight.TipShown(false, false, false));
        // the key is bound to the hold alone, and the pad's LB only means the book's pages in a menu
        string src = File.ReadAllText(Path.Combine(Root(), "src", "Game", "Controls.cs"));
        int start = src.IndexOf("Defaults = new()", StringComparison.Ordinal), end = src.IndexOf("};", start, StringComparison.Ordinal);
        string defaults = src[start..end];
        Assert.Contains("[Act.Experience] = [XpLight.HoldKey]", defaults);
        Assert.DoesNotContain($"\"{XpLight.HoldKey}\"", defaults);
        Assert.Matches(new Regex(@"\[Act\.Experience\] = \[JoyButton\.LeftShoulder\]"), src);
        Assert.Equal("LB", XpLight.HoldPad);
    }

    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? throw new DirectoryNotFoundException("godot/");
    }
}
