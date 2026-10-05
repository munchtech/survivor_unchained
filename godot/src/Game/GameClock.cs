using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The day's clock on screen (docs/design/STORY_NIGHTS_AND_TIME.md §2): free play moves it
 * (Journey.PassTime), and each turn is staged here. The light is read off the clock itself, each
 * time of day's air crossed into the next over its edges (the dark comes in before the word
 * "night", not after it); dusk is the town's evening call and the night's fight named; nightfall calls it, and
 * "Answer the night" (held) lets the ember pull her straight there; a night left alone passes in a
 * fade. Free play is the world with nothing over it: no page, no conversation, no draft or chest,
 * no cinematic, no travel, no pause. */
public partial class Game
{
    /// <summary>The light as the clock last set it: whether it was mid-crossing, and when the colour
    /// grade (a lookup table rebuilt) may next be redone.</summary>
    bool airMoving, airDirty = true;
    double airGradeT;
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
        // The dial by the place's name: where the clock runs, dimmed while it stands still.
        hud.Clock(zone?.ClockRuns == true ? World.Clock : null, free && Journey.ClockStarted);
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
                Shots.Want("day", 20);
                break;
            case ClockTurn.Dusk:
            {
                Turn(TimeOfDay.Dusk, 60);
                Shots.Want("dusk", 1.5); Shots.Want("dusk", 6.5); Shots.Want("dusk", 30); Shots.Want("dusk", 59);
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
                Shots.Want("night", 1.0); Shots.Want("night", 25); Shots.Want("night", 52);
                var tonight = Journey.Tonight;
                Announce(new Announcement("Night", tonight?.Place ?? "The ember is coming up", "zone", 3.6));
                Save("night");
                break;
            }
            case ClockTurn.Nudge:
                Say(Journey.DayLines.Nudge, null, 4);
                Shots.Want("nudge", 1.0);
                break;
            case ClockTurn.NightOver:
                NightPasses();
                break;
        }
    }

    /// <summary>The time of day turns: the lamps and the place follow, the corner of the screen says
    /// so (the light is the clock's, BlendAir).</summary>
    void Turn(TimeOfDay to, double seconds)
    {
        if (zone == null || scene == null) return;
        scene.View.SetNight(to == TimeOfDay.Night);
        scene.View.SetDusk(to == TimeOfDay.Dusk);
        hud.ZoneInfo(zone.Name, zone.Region, World.Day, to);
        zone.TimeTurned(to);
        RefreshObjectives();
    }

    /// <summary>The air at a point on the clock: dawn warms into day over its first minute and a
    /// half, day goes gold over the first minute of dusk, and the dark comes in over the last half
    /// minute of dusk and the first of night, so the word "night" lands in the dark. True while
    /// crossing.</summary>
    (AtmospherePreset Air, bool Moving) AirAt(ZoneRuntime z, double s)
    {
        static double K(double s, double a, double b) { double k = Math.Clamp((s - a) / (b - a), 0, 1); return k * k * (3 - 2 * k); }
        AtmospherePreset A(TimeOfDay t) => z.AtmosphereFor(t);
        const double DawnEnds = 30, DayFull = 90, GoldFull = DayClock.DuskAt + 60, DarkFrom = DayClock.NightAt - 30, DarkFull = DayClock.NightAt + 30;
        if (s < DawnEnds) return (A(TimeOfDay.Dawn), false);
        if (s < DayFull) return (Atmospheres.Blend(A(TimeOfDay.Dawn), A(TimeOfDay.Day), K(s, DawnEnds, DayFull)), true);
        if (s < DayClock.DuskAt) return (A(TimeOfDay.Day), false);
        if (s < GoldFull) return (Atmospheres.Blend(A(TimeOfDay.Day), A(TimeOfDay.Dusk), K(s, DayClock.DuskAt, GoldFull)), true);
        if (s < DarkFrom) return (A(TimeOfDay.Dusk), false);
        if (s < DarkFull) return (Atmospheres.Blend(A(TimeOfDay.Dusk), A(TimeOfDay.Night), K(s, DarkFrom, DarkFull)), true);
        return (A(TimeOfDay.Night), false);
    }

    /// <summary>The light, a frame: read off the clock wherever the clock runs; the sky and the air
    /// every frame while it crosses, the colour grade twice a second, nothing while it holds.</summary>
    void BlendAir(double dt)
    {
        if (zone is not { ClockRuns: true } || !Journey.ClockStarted) return;
        DayClock.Sync(World);
        var (a, moving) = AirAt(zone, World.Clock);
        if (!moving && !airMoving && !airDirty) return;
        airGradeT -= dt;
        bool grade = airGradeT <= 0 || !moving || airDirty;
        if (grade) airGradeT = 0.5;
        air.Set(a, grade);
        airMoving = moving;
        airDirty = false;
    }

    /// <summary>The light set outright (a skip, a new place): the clock's air is put back at once.</summary>
    void StopBlend() => airDirty = true;

    /// <summary>A night left alone passes: a fade, the world a day on, the morning's news.</summary>
    void NightPasses()
    {
        if (zone == null || scene == null || dawnBreaking) return;
        dawnBreaking = true;
        controls.Captured = true;
        hud.Prompt(promptShown = null);
        hud.Fade(1, 1.2, "Dawn", $"Day {World.Day + 1}", new Godot.Color(1f, 0.62f, 0.3f, 0.32f));
        Shots.Want("dawnfade", 1.25);
        Wait(1.3, () =>
        {
            dawnBreaking = false;
            if (zone == null || scene == null) return;
            var lines = Journey.SeeNightOut(Rng.NextDouble);
            SetTimeOutright(TimeOfDay.Dawn);
            Save("dawn");
            hud.Fade(0, 1.4);
            Shots.Want("dawn", 1.6); Shots.Want("dawn", 6);
            controls.Captured = false;
            controls.ClearLatches();
            Morning(lines);
        });
    }

    /// <summary>The time of day set at once (a skip, the night's end): light, lamps, place, corner.</summary>
    void SetTimeOutright(TimeOfDay to)
    {
        if (zone == null || scene == null) return;
        // Where the clock runs, the light is the clock's (on the next frame); elsewhere, the time's own.
        if (zone.ClockRuns && Journey.ClockStarted) StopBlend();
        else air.Set(zone.AtmosphereFor(to));
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
        // (the tracker draws [[answer]] as the key itself, a keycap or the pad's button)
        steps.Add(new($"{Journey.DayLines.Answer}: hold [[answer]]", Optional: true));
        return new List<Tracked> { new("tonight", "Tonight", TrackTone.Main, steps) }.Concat(list).ToList();
    }

    void RefreshObjectives() => hud.Objectives(WithTonight(objectivesBase));
}
