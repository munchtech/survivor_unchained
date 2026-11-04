using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* The telegraph kit (H1 combat teeth, docs/team/hook/H1_combat_teeth.md item 3): named blows that must be dashed, as
 * data (data/content/telegraphs.json). Any zone casts one on a foe with one call (Battle.Tell, logic/Sim/Tells.cs);
 * the arena's table nights cast them from their wave shapes (the "waves" block, ArenaRun). The kind names are H3's
 * sound bank's keys (telegraph.<kind>.windup / .land): ring, charge, pull, closing. They never change. */
public static class Telegraphs
{
    /// <summary>One named telegraph. Sizes in metres (a cast's scale multiplies them), times in seconds.</summary>
    public sealed class Kind
    {
        /// <summary>From its mark to its blow.</summary>
        public double Windup = 1.5;
        /// <summary>The blow's reach: a ring's circle, a pull's reach, a closing's outer edge.</summary>
        public double Radius;
        /// <summary>A closing's band starts here (a Ring mark from Inner to Radius).</summary>
        public double Inner;
        /// <summary>A charge's line, from the foe through the point.</summary>
        public double Length, Width = 1;
        /// <summary>The blow, as a fraction of her max life (before her armor): the same bite at every tier.</summary>
        public double Damage;
        /// <summary>A ring: inside its fill (growing from the center to the edge over the windup), she is slowed by this share.</summary>
        public double Slow;
        /// <summary>A ring: at this share of the windup, within RootRadius of the center, she is rooted for Root s (a dash ends it).</summary>
        public double RootAt, RootRadius, Root;
        /// <summary>A pull: within Radius she drifts toward the center at Pull m/s; the blow lands on its Core.</summary>
        public double Pull, Core;
        /// <summary>A closing: its foes, held for the windup, then rush in at x Rush pace for RushFor s.</summary>
        public double Rush = 1, RushFor;
    }

    /// <summary>Where a table night casts the kit (ArenaRun): its tiers, past its minute, how often, and which wave shape casts what.</summary>
    public sealed class WaveRules
    {
        /// <summary>The table tiers that carry the kit (none listed: the night is as it was, draw for draw).</summary>
        public int[] Tiers = [];
        /// <summary>The night's minute (ArenaRun.Minute) from which it does.</summary>
        public double From = 3;
        /// <summary>Seconds between ambient tells (uniform in [min, max]).</summary>
        public double[] Every = [16, 24];
        /// <summary>An ambient tell is cast by a champion, else a fodder, within this of her.</summary>
        public double Near = 14;
        /// <summary>An ambient tell's kind, by weight.</summary>
        public Dictionary<string, double> Weights = new();
        /// <summary>A champion's turn: it repeats its charge this often while it lives.</summary>
        public double ChampionEvery = 7;
        /// <summary>A swarm's pull is centered this far off her, toward the swarm.</summary>
        public double SwarmOffset = 3;
        /// <summary>Each wave shape's kind (ring, champion, stampede, swarm, signature).</summary>
        public Dictionary<string, string> Turns = new();
    }

    sealed class File
    {
        public Dictionary<string, Kind> Kinds = new();
        public WaveRules Waves = new();
    }

    static File? file;
    static File F => file ??= Json.Parse<File>((System.Environment.GetEnvironmentVariable("SU_TELLS") is { Length: > 0 } alt ? System.IO.File.ReadAllText(alt) : Json.ReadContent("telegraphs.json")));

    /// <summary>The named telegraph, or null for a name the kit does not have.</summary>
    public static Kind? Get(string kind) => F.Kinds.TryGetValue(kind, out var k) ? k : null;

    /// <summary>Where the arena's table nights cast the kit.</summary>
    public static WaveRules Waves => F.Waves;

    /// <summary>The kind a wave shape casts (ring, champion, stampede, swarm, signature), or null for none.</summary>
    public static string? Turn(string shape) => F.Waves.Turns.TryGetValue(shape, out var k) && Get(k) != null ? k : null;

    // SU_TELLS=<path>: a variant of the file for a measuring run (the harness tunes several at once).
    /// <summary>Read the file again (a test or a variant that changed it).</summary>
    public static void Reload() => file = null;
}
