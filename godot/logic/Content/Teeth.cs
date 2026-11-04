using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* Teeth (H1 combat teeth, docs/team/hook/H1_combat_teeth.md items 1 and 7): what a table night's tier asks of a
 * human, as data (data/content/teeth.json). The owner, 3 November, after demo-rc1: "enemies all get 1 shot", "zero
 * danger". The balance harness's late hands (balance/Harness/Human.cs) measure it: tools/balance/danger.py.
 *
 * A tier with no entry is as it was (every number 1, a thirty-minute night). Story nights never read it: their
 * stages are their own. */
public static class Teeth
{
    public sealed class Tier
    {
        /// <summary>Health and blows of the crowd (not champions, not the boss), on top of the night's own curve.</summary>
        public double FodderHp = 1, FodderDamage = 1;
        /// <summary>Health and blows of champions, heralds and minibosses (not the boss).</summary>
        public double EliteHp = 1, EliteDamage = 1;
        /// <summary>The horde's size (ArenaRun.Target).</summary>
        public double Crowd = 1;
        /// <summary>The boss's health and blows (on its script's own).</summary>
        public double BossHp = 1, BossDamage = 1;
        /// <summary>The table night's length to the boss, in real minutes (0: thirty, the table's own).</summary>
        public double Minutes;
        /// <summary>The crowd's director (H6, Play/Zones/ArenaRun.Director.cs): what makes standing itself dangerous.
        /// None: as it was.</summary>
        public Director? Director;
    }

    /// <summary>The crowd's director (H6: "i'm never really surrounded. i'm never really kiting"). Each mechanic has its
    /// switch (false: off), so a measuring run can take each away; distances in metres, times in seconds of the night.</summary>
    public sealed class Director
    {
        /// <summary>The pincer: from FlankFrom until the boss, every FlankEvery [min, max] s, two groups of the people's
        /// fastest kind (FlankBase + minute / FlankPerMinutes each) at FlankDist [min, max] on bearings her heading
        /// +-FlankBearing degrees (heading: her velocity, else her facing), so they come on from behind on both sides.</summary>
        public bool Flank = true;
        public double FlankFrom = 60;
        public double[] FlankEvery = { 60, 90 };
        public double[] FlankDist = { 15, 18 };
        public double FlankBearing = 140, FlankBase = 4, FlankPerMinutes = 3;
        /// <summary>The cut-off: each new group's first foe steers to Lead metres ahead of her along her velocity until it
        /// is within LeadUntil of her, then hunts her as the rest do.</summary>
        public bool CutOff = true;
        public double Lead = 5, LeadUntil = 6;
        /// <summary>A surround closes: foes within SurroundNear of her in SurroundSectors of six sectors for SurroundFor s
        /// (the harness's Surround measure), and the kit's closing is cast round her (the kit on), using the foes already
        /// round her and CloseBase + minute x ClosePerMinute of its own on its ring, at most once each SurroundCooldown.</summary>
        public bool Surround = true;
        public double SurroundNear = 4, SurroundSectors = 3, SurroundFor = 1.5, SurroundCooldown = 20, CloseBase = 18, ClosePerMinute = 1.2;
        /// <summary>Packs close when she stands: moved less than StandMoved in StandFor s with a hostile within StandNear,
        /// the nearest fodder (not held) casts the kit's charge at her at StandScale, at most once each StandCooldown.</summary>
        public bool Stand = true;
        public double StandMoved = 1.2, StandFor = 3, StandNear = 7, StandScale = 0.6, StandCooldown = 3.5;
        /// <summary>The lamp's holder draws a flank: PoolFor s in the lit pool without leaving it brings the next flank
        /// now, and again each PoolEvery s while she stays.</summary>
        public bool Pool = true;
        public double PoolFor = 60, PoolEvery = 45;
        /// <summary>Stuck foes recalled (N34): a hostile non-boss that moved less than StuckMoved in StuckFor s while more
        /// than StuckNear from her goes back to a lane RecallDist out if it is more than RecallFar from her (off the
        /// camera), else follows the flow field to her wholly for FlowFor s.</summary>
        public bool Recall = true;
        public double StuckMoved = 0.6, StuckFor = 6, StuckNear = 3, RecallFar = 14, RecallDist = 24, FlowFor = 4;
        /// <summary>The snuffer explained once: the first snuffer within SnufferNear of the lamp in a night, a bark (once a
        /// night) and a callout (once a profile).</summary>
        public bool Explain = true;
        public double SnufferNear = 12;
    }

    sealed class File
    {
        public Dictionary<string, Tier> Tiers = new();
    }

    static File? file;
    static File F => file ??= Json.Parse<File>((System.Environment.GetEnvironmentVariable("SU_TEETH") is { Length: > 0 } alt ? System.IO.File.ReadAllText(alt) : Json.ReadContent("teeth.json")));

    /// <summary>A tier's teeth, or null (as it was).</summary>
    public static Tier? For(int tier) => F.Tiers.TryGetValue(tier.ToString(), out var t) ? t : null;

    // SU_TEETH=<path>: a variant of the file for a measuring run (the harness tunes several at once).
    /// <summary>Read the file again (a test or a variant that changed it).</summary>
    public static void Reload() => file = null;
}
