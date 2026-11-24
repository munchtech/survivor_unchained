using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* How hard each dungeon fights (dungeon-fights lane, 15 Nov; data/content/dungeon_fights.json). A dungeon's rooms and halls
 * are DungeonGen's; this is what stands in them: its creatures' levels over hers, its packs' size, how many are led by a
 * champion, and its ruler's health. Measured by the harness's `dungeon` command (godot/balance) against the targets in the
 * json's "about". A dungeon the file does not name: all ones (a map's numbers). */
public static class DungeonFights
{
    public sealed class Row
    {
        /// <summary>Levels its creatures (and its ruler) stand above max(its floor, her level).</summary>
        public int FoeUp;
        /// <summary>Pack size, over the map's (MapRun.Place).</summary>
        public double PackSize = 1;
        /// <summary>Chance a pack is led by a champion, over the map's.</summary>
        public double Elites = 1;
        /// <summary>The ruler's health, over MapRun.BossHealth.</summary>
        public double BossHealth = 1;
        /// <summary>(P3) The ruler's blows (its bites and its marked moves, all off its Damage; not the Drive's kit charge, a share of her
        /// life), over its people's champion's: MapRun.Ruler.</summary>
        public double BossDamage = 1;
        /// <summary>(P3) The ruler's kit tells (the Pack-Mother's Drive: a share of her life), over the table's: IBossArena.KitMul.</summary>
        public double BossKit = 1;
        /// <summary>(P3) Its biters' bite (the den's wolves and runners, Content/DenRoster.cs Biters), over the table's: the threat
        /// that is not a mark (DEN_ROSTER.md: "add foe damage before adding any tells").</summary>
        public double Bite = 1;
        /// <summary>(den first blow) The side of the box a resting pack mills in round its spot, in metres (EnemyDef.Roam, Ai.Idle); 0: the
        /// leash's 0.6 (14.4 m), as a map's packs.</summary>
        public double Roam;
    }

    sealed class File { public Dictionary<string, Row> Dungeons = new(); }
    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("dungeon_fights.json"));

    public static readonly Row Plain = new();

    /// <summary>The dungeon's row (the map's own numbers for one the file does not name).</summary>
    public static Row Of(string dungeon) => dungeon != "" && F.Dungeons.TryGetValue(dungeon, out var r) ? r : Plain;
}
