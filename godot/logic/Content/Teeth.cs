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

    sealed class File
    {
        public Dictionary<string, Tier> Tiers = new();
    }

    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("teeth.json"));

    /// <summary>A tier's teeth, or null (as it was).</summary>
    public static Tier? For(int tier) => F.Tiers.TryGetValue(tier.ToString(), out var t) ? t : null;

    /// <summary>Read the file again (a test or a variant that changed it).</summary>
    public static void Reload() => file = null;
}
