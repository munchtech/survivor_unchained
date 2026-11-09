using System.Collections.Generic;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M5 r3) One story text channel at a time (Play/StoryText.cs): the narrator's band and a speaker's named card
/// never open over one another, in the order they were asked for.</summary>
public class StoryTextTests
{
    double now;
    double narrUntil = -1, speakUntil = -1;
    readonly List<string> shown = new();

    StoryText New() => new(() => now, () => now < narrUntil, () => now < speakUntil);

    void Narrate(StoryText s, string id, double secs) => s.Ask(StoryText.Kind.Narration, () => { shown.Add(id); narrUntil = now + secs; });
    void Speak(StoryText s, string id, double secs, string who = "Grimtunnel") => s.Ask(StoryText.Kind.Speaker, () => { shown.Add(id); speakUntil = now + secs; }, who);

    void Run(StoryText s, double to) { for (; now < to; now += 0.05) s.Tick(); }

    [Fact]
    public void A_narration_waits_for_a_speakers_card_to_close()
    {
        var s = New();
        Speak(s, "grim", 3.9);
        now = 3.0;
        Narrate(s, "reeds", 4);
        Assert.Equal(new[] { "grim" }, shown);
        Run(s, 3.8);
        Assert.Equal(new[] { "grim" }, shown);
        Run(s, 4.0);
        Assert.Equal(new[] { "grim", "reeds" }, shown);
    }

    [Fact]
    public void A_speakers_card_does_not_open_over_narration_nor_overtake_it()
    {
        var s = New();
        Narrate(s, "heart", 5);
        now = 1;
        Speak(s, "grim1", 2);
        Assert.Equal(new[] { "heart" }, shown);
        Run(s, 5.1);
        Assert.Equal(new[] { "heart", "grim1" }, shown);
        // asked in order: a narration, then a speaker; the speaker never overtakes the narration waiting on another card
        Narrate(s, "reeds", 4);
        Speak(s, "grim2", 2);
        Assert.Equal(new[] { "heart", "grim1" }, shown);
        Run(s, 7.2);
        Assert.Equal(new[] { "heart", "grim1", "reeds" }, shown);
        Run(s, 11.2);
        Assert.Equal(new[] { "heart", "grim1", "reeds", "grim2" }, shown);
    }

    [Fact]
    public void A_held_narration_keeps_its_spacing_from_the_line_after_it()
    {
        var s = New();
        Speak(s, "grim", 3);
        Narrate(s, "reeds", 4);
        // its zone times the next line 4.4 s after the first was asked
        now = 2.5;
        Run(s, 4.4);
        Assert.Equal(new[] { "grim", "reeds" }, shown);
        double reedsAt = 3.0;
        Narrate(s, "gray", 6);
        Run(s, reedsAt + 4.3);
        Assert.Equal(new[] { "grim", "reeds" }, shown);
        Run(s, reedsAt + 4.7);
        Assert.Equal(new[] { "grim", "reeds", "gray" }, shown);
    }

    [Fact]
    public void Narrations_unheld_replace_one_another_as_their_zone_timed_them()
    {
        var s = New();
        Narrate(s, "a", 3);
        now = 1;
        Narrate(s, "b", 3);
        Assert.Equal(new[] { "a", "b" }, shown);
    }

    [Fact]
    public void A_champions_wake_holds_the_narration_band()
    {
        var s = New();
        s.HoldNarration(StoryText.WakeHold);
        Narrate(s, "knight", 5);
        Run(s, StoryText.WakeHold - 0.1);
        Assert.Empty(shown);
        Run(s, StoryText.WakeHold + 0.1);
        Assert.Equal(new[] { "knight" }, shown);
    }

    [Fact]
    public void A_hush_drops_the_speakers_waiting_lines_and_a_narration_is_never_lost()
    {
        var s = New();
        Narrate(s, "n", 3);
        Speak(s, "lie", 2, "chid");
        Speak(s, "grim", 2);
        s.Drop("chid");
        Run(s, 3.1);
        Assert.Equal(new[] { "n", "grim" }, shown);
        // a speaker who never stops: the narration shows after MostWait
        speakUntil = 1e9;
        Narrate(s, "late", 3);
        Run(s, now + StoryText.MostWait + 0.1);
        Assert.Equal("late", shown[^1]);
    }
    [Fact]
    public void A_champion_about_to_wake_holds_the_band_and_a_line_up_is_taken_down_and_asked_again()
    {
        // (M5 r4: Ser Aldric's intro line opened 1.7 s before his wake and ran through his body)
        var s = New();
        bool soon = false; int downs = 0;
        s.WakeSoon = () => soon;
        s.TakeDown = () => { downs++; narrUntil = now; };
        Narrate(s, "armor", 5);
        Run(s, 1.0);
        soon = true;                       // her walk will wake him within 2 s
        Run(s, 1.2);
        Assert.Equal(1, downs);
        Assert.False(now < narrUntil);
        Narrate(s, "next", 4);
        Run(s, 3.0);                       // he wakes: the game's hold after it
        soon = false; s.HoldNarration(StoryText.WakeHold);
        Run(s, 5.9);
        Assert.Equal(new[] { "armor" }, shown);
        Run(s, 6.2);
        Assert.Equal(new[] { "armor", "armor" }, shown);
        soon = true; Run(s, 6.5);          // asked again, it is not taken down a second time
        Assert.Equal(1, downs);
    }

    [Fact]
    public void Without_a_wake_coming_nothing_is_taken_down()
    {
        var s = New(); int downs = 0;
        s.WakeSoon = () => false; s.TakeDown = () => downs++;
        Narrate(s, "a", 3); Run(s, 2);
        Assert.Equal(0, downs);
        Assert.Equal(new[] { "a" }, shown);
    }
}
