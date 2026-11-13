using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* Boards (H1 combat teeth, docs/team/hook/H1_combat_teeth.md item 6): a table arena as a board, as data
 * (data/content/boards.json). The owner, 3 November, after the tier-1 Deep Shaw: "the arena survivor area is just
 * too big and theres no strategy to it at all". So: the walkable ground cut to what its crowd fills, a fold to hold
 * (a clearing round a lamp, walled with three chokepoints), lanes from its gaps out to the edge, fewer cover islands.
 *
 * By place id (ArenaPlaces.IdFor: hollow, barrow, ruts, dig), each with the table-night tiers it applies at. A place
 * or tier with no board is made exactly as it was; story nights never take one. The generation is Maps/ArenaBoard.cs
 * (the common shape) and the place's own ArenaShape (its kit on the wall). SU_BOARDS=<path>: a variant file. */
public static class Boards
{
    public sealed class Def
    {
        /// <summary>The table-night tiers the board applies at.</summary>
        public int[] Tiers = [];
        /// <summary>The walkable ground's radius in metres (the edge wanders about it as before: ArenaGen.R is 84).</summary>
        public double Radius = 52;
        public FoldDef Fold = new();
        public LampDef Lamp = new();
        public LanesDef Lanes = new();
        public CoverDef Cover = new();
    }

    /// <summary>The place to hold: a clearing round the lamp, ringed by a broken wall.</summary>
    public sealed class FoldDef
    {
        /// <summary>Metres from the start point (0, 0) to the fold's middle, a seeded pick between the two.</summary>
        public double[] Offset = [18, 24];
        /// <summary>The wall's middle line, metres from the fold's middle (a seeded pick between the two).</summary>
        public double[] Wall = [17, 20];
        /// <summary>The wall's thickness in metres (impassable).</summary>
        public double Thick = 3;
        /// <summary>How many chokepoints break the wall (one always faces the start point).</summary>
        public int Gaps = 3;
        /// <summary>A gap's clear width in metres, collider to collider at its narrowest (a seeded pick between the two).</summary>
        public double[] GapWidth = [5, 6];
        /// <summary>Radians a gap's bearing wanders off the even spacing.</summary>
        public double Jitter = 0.3;
        /// <summary>Metres kept between the wall's outside and the board's edge (a way round behind it).</summary>
        public double ClearEdge = 6;
        /// <summary>Metres between two of the wall's dressing spots along its middle line (the place's own pieces).</summary>
        public double Dress = 4;
        /// <summary>The small warm lights at both sides of each gap, so the gaps read as doors (none if Energy is 0).</summary>
        public DoorDef Door = new();
        /// <summary>The wild kit's boulders on the wall (none: the place's own pieces only): this share of its spots
        /// (gap posts too) is one big rock, so the fight at the lamp is framed by them (L1 Stage C wave 2).</summary>
        public RocksDef? Rocks;
    }
    /// <summary>The fold wall's kit boulders: the flora kind, the share of wall spots, the scale range and the sink in
    /// metres; From says what the numbers are from (the pipeline's derivation rule).</summary>
    public sealed class RocksDef
    {
        public string Kind = "boulder";
        public double Share = 0;
        public double[] Scale = [1.2, 1.6];
        public double Sink = 0.2;
        public string From = "";
    }
    /// <summary>A gap's door lights: their colour, energy, reach in metres, and height over the ground.</summary>
    public sealed class DoorDef
    {
        public string Color = "#ffb060";
        public double Energy = 0, Range = 4.5, Height = 1.2;
        /// <summary>Metres in from the wall's middle line toward the fold's middle (a light on the inside of the post).</summary>
        public double In = 0.6;
    }

    /// <summary>The lamp at the fold's middle: a reason to stand somewhere (Play/Zones/ArenaRun.Lamp.cs). Cold till LitAt;
    /// lit, it pays her while she stands in its pool; from SnuffFrom the people send some of each wave to put it out,
    /// and she lights it again by standing at it. Its light index is ArenaBoard.Lamps[k].Light.</summary>
    public sealed class LampDef
    {
        public string Piece = "halloween/post_lantern";
        public double Scale = 1.3;
        public string Color = "#ffd07a";
        public double Energy = 7, Height = 2.7, Flicker = 0.04;
        /// <summary>Metres the lamp's light reaches past the wall's middle line (its range is the wall's radius and this;
        /// 0: as many metres as its energy, as any other lamp).</summary>
        public double Reach = 0;
        /// <summary>Where the light hangs in the lantern piece's own frame at scale 1 (x, up, z: the flame in its glass;
        /// none: Height over its foot), and the radius at scale 1 of the bright core drawn there (LightDef.Core).</summary>
        public double[] Head = [];
        public double Core = 0;
        /// <summary>Metres of the lamp's pool, where her reward is (while it is lit).</summary>
        public double Pool = 8;
        /// <summary>The night's minute it catches (cold and dark before).</summary>
        public double LitAt = 4.5;
        /// <summary>While she stands in its lit pool: the Flare fills this many times as fast (Rules.FlareFill), and the
        /// ember of what she kills there is this many times as much (Rules.KillEmber).</summary>
        public double FlareFill = 2, Ember = 1.25;
        /// <summary>From this minute, this share of each wave's rank and file (no champions, no throwers, casters,
        /// burrowers or rallying voices, none once the boss is up) come for the lamp, not for her.</summary>
        public double SnuffFrom = 5.0, SnuffShare = 0.2;
        /// <summary>Metres: a snuffer turns on her for good once she is this close to it.</summary>
        public double SnuffAggro = 5;
        /// <summary>Metres from the lamp a snuffer douses it from.</summary>
        public double AtLamp = 1.6;
        /// <summary>The lamp's life, and what each snuffer at it takes off it a second. At none it goes out.</summary>
        public double Life = 100, Douse = 8;
        /// <summary>Out, she lights it again by standing within RelightR metres of it for Relight seconds, no snuffer at it.</summary>
        public double RelightR = 2.5, Relight = 2;
        /// <summary>Seconds at least between two "They are at the lamp!" warnings, said when the first snuffer comes within
        /// WarnR metres of it (wherever she is).</summary>
        public double WarnEvery = 15, WarnR = 12;
        /// <summary>The harness's bots (balance/Harness/LampHold.cs): the chance a night's hands hold the lamp, by bot.</summary>
        public Dictionary<string, double> Hold = new();
    }

    /// <summary>The worn runs from each gap out to the edge, kept free of cover.</summary>
    public sealed class LanesDef
    {
        /// <summary>A lane's width in metres (a seeded pick between the two).</summary>
        public double[] Width = [3, 4];
    }

    /// <summary>The cover islands outside the fold, off the lanes.</summary>
    public sealed class CoverDef
    {
        /// <summary>How many (a seeded pick between the two, inclusive).</summary>
        public int[] Count = [6, 8];
        /// <summary>Metres at least between two islands.</summary>
        public double Spacing = 13;
        /// <summary>Metres from the start point an island keeps, and from the edge.</summary>
        public double From = 10, Edge = 9;
    }

    sealed class File
    {
        public Dictionary<string, Def> Places = new();
    }

    static File? file;
    static File F => file ??= Json.Parse<File>(DevOverrides.Env("SU_BOARDS") is { } alt ? System.IO.File.ReadAllText(alt) : Json.ReadContent("boards.json"));

    /// <summary>A place's board at a table-night tier, or null (made as it was).</summary>
    public static Def? For(string place, int tier) =>
        F.Places.TryGetValue(place, out var d) && System.Array.IndexOf(d.Tiers, tier) >= 0 ? d : null;

    /// <summary>Read the file again (a test or a variant that changed it).</summary>
    public static void Reload() => file = null;
}
