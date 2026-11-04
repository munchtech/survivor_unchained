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
    }

    /// <summary>The Ford-Warden (H8, N20, numbers H6's; the owner on demo-rc2: "the warden was easy. died in like 8
    /// seconds didn't have to crash a lamp"): the least of his life he can be brought to (a share of it) by lamps still
    /// unbroken this fight, 0-3, and the share of a blow he takes by lamps lit; his life's multiplier; a backstop, a
    /// last floor held until he has fought this long; and how long one floor holds before it cracks a step.</summary>
    public sealed class FordWarden
    {
        public double[] Floors = [0, 0, 0, 0];
        public double[] Ward = [1, 0.7, 0.55, 0.4];
        public double HpMul = 1;
        public double MinSeconds;
        public double Backstop = 0.05;
        /// <summary>Seconds held at one floor before it cracks a step (a player who can't bring a lamp down is never
        /// held for good: H8's runs had the autopilot's lamps relit by his channel over and over).</summary>
        public double CrackAfter = 45;
    }

    public sealed class PrologueTeeth
    {
        public FordWarden? FordWarden;
    }

    sealed class File
    {
        public Dictionary<string, Tier> Tiers = new();
        public PrologueTeeth? Prologue;
    }

    static File? file;
    static File F => file ??= Json.Parse<File>((System.Environment.GetEnvironmentVariable("SU_TEETH") is { Length: > 0 } alt ? System.IO.File.ReadAllText(alt) : Json.ReadContent("teeth.json")));

    /// <summary>A tier's teeth, or null (as it was).</summary>
    public static Tier? For(int tier) => F.Tiers.TryGetValue(tier.ToString(), out var t) ? t : null;

    /// <summary>The Ford-Warden's teeth, or null (as it was: the ward alone).</summary>
    public static FordWarden? Ford => F.Prologue?.FordWarden;

    // SU_TEETH=<path>: a variant of the file for a measuring run (the harness tunes several at once).
    /// <summary>Read the file again (a test or a variant that changed it).</summary>
    public static void Reload() => file = null;
}
