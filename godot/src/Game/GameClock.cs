using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The day's clock on screen (docs/design/STORY_NIGHTS_AND_TIME.md §2): free play moves it
 * (Journey.PassTime), and each turn is staged here. The light crosses to the next time of day over
 * a minute; dusk is the town's evening call and the night's fight named; nightfall calls it, and
 * "Answer the night" (held) lets the ember pull her straight there; a night left alone passes in a
 * fade. Free play is the world with nothing over it: no page, no conversation, no draft or chest,
 * no cinematic, no travel, no pause. */
public partial class Game
{
    /// <summary>The light between two times of day, crossed over a minute or so.</summary>
    AtmospherePreset? airFrom, airTo;
    double airT, airLen, airGradeT;
    /// <summary>How long "Answer the night" has been held.</summary>
    double answerHeld;
    /// <summary>A night passing by itself, in its fade.</summary>
    bool dawnBreaking;
    /// <summary>The zone's own objectives, before the night's call is put above them.</summary>
    List<Tracked> objectivesBase = new();

    /// <summary>Held this long, the night is answered (a tap is never a fight).</summary>
    const double AnswerHold = 0.8;

    bool FreePlay => zone != null && scene != null && zone.ClockRuns && Overlay == null && !inTransit && cine == null
        && !scene.SimPaused && !controls.Captured && !dawnBreaking && Battle?.Player.Alive != false;

    /// <summary>The clock's frame: free play moves it, the light blends, the night can be answered.</summary>
    void TickDay(double dt)
    {
        bool free = FreePlay;
        if (free)
            foreach (var t in Journey.PassTime(dt)) OnClock(t);
        BlendAir(dt);
        Answering(dt, free);
    }

    void OnClock(ClockTurn t)
    {
        if (zone == null) return;
        switch (t)
        {
            case ClockTurn.Day:
                Turn(TimeOfDay.Day, 40);
                break;
            case ClockTurn.Dusk:
            {
                Turn(TimeOfDay.Dusk, 60);
                // The town's own evening call, heard in the town; then, anywhere, what the night holds.
                var tonight = Journey.Tonight;
                double gap = 0;
                if (zone is Waystation) { Say(Journey.DayLines.Dusk, "Gate guard", 4.5); gap = 5; }
                After(gap, () => Say(Journey.DayLines.Tonight[tonight?.Id ?? ""], null, 5.5));
                break;
            }
            case ClockTurn.Night:
            {
                Turn(TimeOfDay.Night, 50);
                var tonight = Journey.Tonight;
                Announce(new Announcement("Night", tonight?.Place ?? "The ember is coming up", "zone", 3.6));
                Save("night");
                break;
            }
            case ClockTurn.Nudge:
                Say(Journey.DayLines.Nudge, null, 4);
                break;
            case ClockTurn.NightOver:
                NightPasses();
                break;
        }
    }

    /// <summary>The time of day turns: the light crosses over `seconds`, the lamps and the place
    /// follow, the corner of the screen says so.</summary>
    void Turn(TimeOfDay to, double seconds)
    {
        if (zone == null || scene == null) return;
        airFrom = air.Current;
        airTo = zone.AtmosphereFor(to);
        airT = 0;
        airLen = seconds;
        airGradeT = 0;
        scene.View.SetNight(to == TimeOfDay.Night);
        scene.View.SetDusk(to == TimeOfDay.Dusk);
        hud.ZoneInfo(zone.Name, zone.Region, World.Day, to);
        zone.TimeTurned(to);
        RefreshObjectives();
    }

    /// <summary>A turn of the light, a frame: the sky and the air every frame, the colour grade
    /// (a lookup table rebuilt) twice a second.</summary>
    void BlendAir(double dt)
    {
        if (airTo == null || airFrom == null) return;
        airT += dt;
        double k = Math.Clamp(airT / Math.Max(0.01, airLen), 0, 1);
        k = k * k * (3 - 2 * k);
        airGradeT -= dt;
        bool grade = airGradeT <= 0 || k >= 1;
        if (grade) airGradeT = 0.5;
        air.Set(Atmospheres.Blend(airFrom, airTo, k), grade);
        if (k >= 1) airTo = null;
    }

    /// <summary>The light set outright (a skip, a new place): any turn under way is dropped.</summary>
    void StopBlend() => airTo = null;

    /// <summary>A night left alone passes: a fade, the world a day on, the morning's news.</summary>
    void NightPasses()
    {
        if (zone == null || scene == null || dawnBreaking) return;
        dawnBreaking = true;
        controls.Captured = true;
        hud.Prompt(promptShown = null);
        hud.Fade(1, 1.2, "Dawn", $"Day {World.Day + 1}");
        Wait(1.3, () =>
        {
            dawnBreaking = false;
            if (zone == null || scene == null) return;
            var lines = Journey.SeeNightOut(Rng.NextDouble);
            SetTimeOutright(TimeOfDay.Dawn);
            Save("dawn");
            hud.Fade(0, 1.4);
            controls.Captured = false;
            controls.ClearLatches();
            Morning(lines);
        });
    }

    /// <summary>The time of day set at once (a skip, the night's end): light, lamps, place, corner.</summary>
    void SetTimeOutright(TimeOfDay to)
    {
        if (zone == null || scene == null) return;
        StopBlend();
        air.Set(zone.AtmosphereFor(to));
        scene.View.SetNight(to == TimeOfDay.Night);
        scene.View.SetDusk(to == TimeOfDay.Dusk);
        hud.ZoneInfo(zone.Name, zone.Region, World.Day, to);
        zone.TimeTurned(to);
        RefreshObjectives();
    }

    /// <summary>What the night brought, said as the morning comes up: the first line under the
    /// picture, the news after it as notices.</summary>
    void Morning(List<string> lines)
    {
        if (lines.Count == 0) return;
        Say(lines[0], null, 6);
        for (int i = 1; i < lines.Count; i++)
        {
            var line = lines[i];
            After(2.5 + i * 1.6, () => Toast(new Toast(ToastKind.World, line)));
        }
    }

    /* ------------------------------------------------------- answer the night -- */

    void Answering(double dt, bool free)
    {
        bool can = free && World.Time == TimeOfDay.Night && auto == null;
        if (!can || !controls.Held(Act.Answer)) { answerHeld = 0; return; }
        if (answerHeld < 0) return;
        answerHeld += dt;
        if (answerHeld >= AnswerHold) { answerHeld = -1; AnswerNight(); }
    }

    /// <summary>The night answered: the ember pulls her to the story's fight if one is open, else to
    /// the nearest ember scar in the wood, else to the Wayfinder's table.</summary>
    void AnswerNight()
    {
        if (zone == null || Battle is not { } b) return;
        var p = b.Player;
        // A second fight the same night: she does not go back to the lamps.
        if (Journey.FoughtTonight) Say(Journey.DayLines.StraightOn, null, 3.5);
        if (Journey.Tonight is { } f) { EnterArena(StoryFights.Spec(f.Id, Journey.Ctx, zone.Id, p.X, p.Z, p.Facing)); return; }
        if (zone is Verge v && v.NearestScar(p.X, p.Z) is { } scar) { EnterArena(scar); return; }
        Open("maps");
    }

    /// <summary>What the night offers, above the zone's own objectives while it is night.</summary>
    List<Tracked> WithTonight(List<Tracked> list)
    {
        if (zone is not { ClockRuns: true } || World.Time != TimeOfDay.Night) return list;
        // The night's fight first, then what else is out tonight, then how to answer it.
        var called = StoryFights.Called(Journey.Ctx);
        bool scars = zone is Verge { HasScars: true };
        string what = called.FirstOrDefault() is { } f ? $"{f.Verb}: {f.Place}" : scars ? "Step into an ember scar" : "The Wayfinder's table";
        var others = called.Skip(1).Select(o => o.Place).ToList();
        if (scars && called.Count > 0) others.Add("the ember scars");
        var steps = new List<Step> { new(what) };
        if (others.Count > 0) steps.Add(new($"{Journey.DayLines.AlsoOut} {string.Join(", ", others)}", Optional: true));
        steps.Add(new($"{Journey.DayLines.Answer}: hold {KeyLabel("answer")}", Optional: true));
        return new List<Tracked> { new("tonight", "Tonight", TrackTone.Main, steps) }.Concat(list).ToList();
    }

    void RefreshObjectives() => hud.Objectives(WithTonight(objectivesBase));
}
