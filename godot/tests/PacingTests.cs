using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Zones;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The shape of a night before its boss (Play/Zones/ArenaPacing.cs): a sawtooth that
/// rises into each landmark and lets go after it, breathers after turns, a herald's duel and
/// its flood, the hush, and turns that never repeat.</summary>
public class PacingTests
{
    static double S(double minute) => minute * 60;

    [Fact]
    public void The_night_rises_into_each_landmark_and_lets_go_after_it()
    {
        var p = new ArenaPacing(S(30));
        // Into the first herald, and down after it.
        Assert.True(p.Shape(S(9.9)) > p.Shape(S(7)) + 0.2);
        Assert.True(p.Shape(S(10.5)) < p.Shape(S(9.9)) - 0.2);
        // A breath before midnight's great blessing.
        Assert.True(p.Shape(S(14.5)) < p.Shape(S(13)));
        // Into the second herald.
        Assert.True(p.Shape(S(19.9)) > p.Shape(S(17)) + 0.2);
        // The long push is the fullest the field is kept before the boss...
        double push = p.Shape(S(28.4));
        for (double m = 0; m < 28.4; m += 0.25) Assert.True(p.Shape(S(m)) <= push, $"{m}");
        // ...and the hush after it the thinnest.
        Assert.True(p.Hush(S(29)));
        Assert.True(p.Shape(S(29)) < 0.5);
        Assert.False(p.Hush(S(30)));
        Assert.Equal(1, p.Shape(S(31)));
    }

    [Fact]
    public void The_danger_builds_into_each_landmark_and_never_in_the_hush()
    {
        var p = new ArenaPacing(S(30));
        Assert.True(p.Building(S(9)));
        Assert.True(p.Building(S(19)));
        Assert.True(p.Building(S(27)));
        Assert.False(p.Building(S(12)));
        Assert.False(p.Building(S(29)));
        p.HeraldCame();
        Assert.False(p.Building(S(19)));
    }

    [Fact]
    public void The_shape_reshapes_the_night_and_does_not_make_it_harder_or_easier()
    {
        var p = new ArenaPacing(S(30));
        double sum = 0;
        int n = 0;
        for (double s = 0; s < S(30); s += 1) { sum += p.Shape(s); n++; }
        Assert.InRange(sum / n, 0.95, 1.08);
    }

    [Fact]
    public void A_shorter_night_keeps_the_same_shape()
    {
        var full = new ArenaPacing(S(30));
        var half = new ArenaPacing(S(15));
        foreach (double m in new[] { 1, 5, 9.9, 10.5, 14.5, 19.9, 27, 29 })
            Assert.Equal(full.Shape(S(m)), half.Shape(S(m / 2)), 6);
    }

    [Fact]
    public void A_heralds_duel_thins_the_field_and_its_fall_floods_it()
    {
        var p = new ArenaPacing(S(30));
        double before = p.TargetShare(S(10));
        p.HeraldCame();
        Assert.True(p.TargetShare(S(10.1)) <= 0.55);
        Assert.Null(p.Next(S(10.1), () => 0.5));
        p.HeraldFell(S(10.5));
        Assert.True(p.Flooding(S(10.6)));
        Assert.True(p.TargetShare(S(10.6)) > before);
        Assert.False(p.Flooding(S(11.2)));
    }

    [Fact]
    public void A_turn_is_followed_by_a_breather()
    {
        var p = new ArenaPacing(S(30));
        p.Played(S(4));
        Assert.False(p.Breather(S(4) + 5));
        Assert.True(p.Breather(S(4) + 20));
        Assert.True(p.TargetShare(S(4) + 20) < 0.5);
        Assert.False(p.Breather(S(4) + 40));
    }

    [Fact]
    public void Turns_never_repeat_the_people_ask_their_question_and_champions_come_often()
    {
        var rng = new Random(7);
        for (int run = 0; run < 50; run++)
        {
            var p = new ArenaPacing(S(30));
            var turns = new List<(double Minute, Turn Turn)>();
            for (double s = 55; s < S(30); s += 60 + rng.NextDouble() * 25)
                if (p.Next(s, rng.NextDouble) is Turn t) { turns.Add((s / 60, t)); p.Played(s); }
            for (int i = 1; i < turns.Count; i++) Assert.NotEqual(turns[i - 1].Turn, turns[i].Turn);
            // The people's own question at about six minutes, their second at about seventeen,
            // the first again in the long push; none in the hush.
            string said = string.Join(", ", turns.Select(x => $"{x.Minute:0.0} {x.Turn}"));
            Assert.True(turns.Any(x => x.Turn == Turn.Signature && x.Minute is >= 5.5 and < 8), said);
            Assert.True(turns.Any(x => x.Turn == Turn.SecondSignature && x.Minute is >= 16.5 and < 19), said);
            Assert.True(turns.Any(x => x.Turn == Turn.Signature && x.Minute is >= 25.5 and < 28.5), said);
            Assert.DoesNotContain(turns, x => x.Minute >= 28.5);
            // From the eighth minute a chest in every three turns: a champion's, or the captain's
            // who leads the people's own turn.
            var late = turns.Where(x => x.Minute >= 8).Select(x => x.Turn).ToList();
            for (int i = 0; i + 3 <= late.Count; i++)
                Assert.True(late.Skip(i).Take(3).Any(t => t is Turn.Champion or Turn.Signature or Turn.SecondSignature), said);
        }
    }

    [Fact]
    public void Moving_the_clock_on_does_not_ask_every_question_at_once()
    {
        var p = new ArenaPacing(S(30));
        p.SkipTo(S(20));
        Assert.NotEqual(Turn.Signature, p.Next(S(20), () => 0.0));
        Assert.NotEqual(Turn.SecondSignature, p.Next(S(21.5), () => 0.0));
    }
}
