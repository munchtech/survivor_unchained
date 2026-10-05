using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The day moving on by itself (docs/design/STORY_NIGHTS_AND_TIME.md §2, the owner's decisions):
 * free play runs the clock, dusk warns, night calls the night's fight, and a night left alone
 * passes. The inn's bed and "wait for nightfall" are shortcuts through it. A story fight lost
 * costs her the night: she wakes in town a day on. The host decides what is free play and
 * stages each turn; this is what the turns do to the world. */
public sealed partial class Journey
{
    /// <summary>The story's words for the clock's moments (the story lead's drafts).</summary>
    public static class DayLines
    {
        /// <summary>The town's own evening call, at dusk (the gate guard's).</summary>
        public const string Dusk = "Lamps are lit. Stay where they reach.";
        /// <summary>At dusk, after the call: the night's fight named, by StoryFights id ("" when none is open).</summary>
        public static readonly Dictionary<string, string> Tonight = new()
        {
            ["hollow"] = "Out past the lamps, the Pack has stopped howling.",
            ["roost"] = "Up the Old Road, the Kerchiefs' fires are lit all along the ravine.",
            ["dig"] = "On the hill over the Dig, the lamps are all moving the same way.",
            ["vault"] = "Out in the Verge, the sealed door has woken. Its light is violet.",
            [""] = "Out on the Verge, the ember is coming up.",
        };
        /// <summary>Getting up in a story fight (the prologue's own words; one rise, Act 1 only).</summary>
        public const string Rise = "You get up.";
        /// <summary>Half the night gone (a placeholder until story writes it).</summary>
        public const string Nudge = "Half the night is gone.";
        /// <summary>A night left alone, passing.</summary>
        public const string NightOut = "You see the night out on your feet. At first light the warmth comes back into your hands.";
        /// <summary>A story fight lost: Chid carries her home, and she wakes a day on (a placeholder
        /// until story writes it).</summary>
        public const string Carried = "You wake in your bed at the Last Lamp, a day gone. Chid carried you home.";
    }

    /// <summary>The clock has started: on the first day it waits until the arrival is over (the
    /// first of the two troubles in her journal), when she has somewhere to be; after that it runs.</summary>
    public bool ClockStarted
    {
        get
        {
            if (World.Fact("clock.started").Truthy) return true;
            bool begun = World.Day > 1 || World.Quests.Any(q => q.Key is "beasts" or "caravan" && q.Value.Status != QuestStatus.Unknown);
            if (begun) World.Facts["clock.started"] = true;
            return begun;
        }
    }

    /// <summary>Free play passes: the clock moves on and says what it crossed. The night holds at
    /// its end until the host lets it pass (SeeNightOut).</summary>
    public List<ClockTurn> PassTime(double dt)
    {
        var turns = new List<ClockTurn>();
        if (dt <= 0 || !ClockStarted) return turns;
        DayClock.Sync(World);
        double s0 = World.Clock, s1 = Math.Min(s0 + dt, DayClock.NightEnds);
        World.Clock = s1;
        void Cross(double at, ClockTurn t) { if (s0 < at && s1 >= at) turns.Add(t); }
        Cross(DayClock.DayAt, ClockTurn.Day);
        Cross(DayClock.DuskAt, ClockTurn.Dusk);
        Cross(DayClock.NightAt, ClockTurn.Night);
        Cross(DayClock.NudgeAt, ClockTurn.Nudge);
        Cross(DayClock.NightEnds, ClockTurn.NightOver);
        World.Time = DayClock.At(s1);
        return turns;
    }

    /// <summary>The story's fight the night calls (null when the story has pointed her at none: the
    /// scars and the table are the night's then).</summary>
    public StoryFights.Fight? Tonight => StoryFights.Called(Ctx).FirstOrDefault();

    /// <summary>A night left alone passes: the world moves on a day, as it does when she sleeps,
    /// but without the inn's rest (her wounds come with her). What the night brought, as lines.</summary>
    public List<string> SeeNightOut(Func<double> rng)
    {
        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Dawn;
        World.Clock = 0;
        var lines = new List<string> { DayLines.NightOut };
        lines.AddRange(Overnight(report, atInn: false));
        OnTouch();
        return lines;
    }

    /// <summary>A story fight lost (the owner: "having to die for a time"): the night is lost, and
    /// she wakes in town the next morning, carried home, healed by the bed she was put in, with a
    /// day to make ready before she tries again. What the night brought, as lines.</summary>
    public List<string> WakeAfterLoss(Battle? b, Func<double> rng)
    {
        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Dawn;
        World.Clock = 0;
        Expedition = null;
        if (b != null) b.Player.Hp = b.MaxHp;
        var lines = new List<string> { DayLines.Carried };
        lines.AddRange(Overnight(report, atInn: true));
        OnTouch();
        return lines;
    }

    /// <summary>Back from a fight into the same night (the owner: several fights a night, by going
    /// straight from one to the next): the night keeps at least a few minutes, to hear the town
    /// or to go on to another.</summary>
    public void BackFromFight()
    {
        if (World.Time != TimeOfDay.Night) return;
        DayClock.Sync(World);
        World.Clock = Math.Min(World.Clock, DayClock.NightEnds - DayClock.AfterFight);
    }
}
