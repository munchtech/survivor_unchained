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
    }

    /// <summary>The lamp at the fold's middle (part B lights and douses it: its light index is ArenaBoard.Lamps).</summary>
    public sealed class LampDef
    {
        public string Piece = "halloween/post_lantern";
        public double Scale = 1.3;
        public string Color = "#ffd07a";
        public double Energy = 7, Height = 2.7, Flicker = 0.04;
        /// <summary>Metres of the lamp's pool (where her reward is, part B).</summary>
        public double Pool = 8;
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
    static File F => file ??= Json.Parse<File>(System.Environment.GetEnvironmentVariable("SU_BOARDS") is { Length: > 0 } alt ? System.IO.File.ReadAllText(alt) : Json.ReadContent("boards.json"));

    /// <summary>A place's board at a table-night tier, or null (made as it was).</summary>
    public static Def? For(string place, int tier) =>
        F.Places.TryGetValue(place, out var d) && System.Array.IndexOf(d.Tiers, tier) >= 0 ? d : null;

    /// <summary>Read the file again (a test or a variant that changed it).</summary>
    public static void Reload() => file = null;
}
