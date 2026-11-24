using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/// <summary>(P3, docs/design/DEN_ROSTER.md section 3; the owner, 22 Nov: "I approve den roster".) The den's own cut of the
/// ordinary foes: each has one move, and its packs are built from five recipes. Only the den ("hollow"): arena nights,
/// story fights, Wayfinder maps and the roost read the table's rows (Enemies.cs), which this never edits.</summary>
public static class DenRoster
{
    public static bool For(string dungeon) => dungeon == "hollow";

    /// <summary>One part of a recipe: a kind, how many, and whether it is a telegraphed move (a charge, a lob, a slam, a howl).</summary>
    public sealed record Part(string Def, int Count, bool Telegraphed);
    public sealed record Recipe(string Id, Part[] Parts);

    /// <summary>The den's kinds that differ from the table's, as fresh copies (Battle.Roster).</summary>
    public static Dictionary<string, EnemyDef> Cuts()
    {
        double bite = DungeonFights.Of("hollow").Bite;
        var runner = Enemies.Get("wolf_runner").Clone();   // fodder swarm, dies to one cut
        runner.Behavior = Behavior.Chase; runner.Health = 14; runner.Lunge = null; runner.Damage *= bite;

        var wolf = Enemies.Get("wolf").Clone();            // the pack's weight: its bite is the den's threat
        wolf.Damage *= bite;

        var sick = Enemies.Get("wolf_blighted").Clone();   // coughs slurry, no ground left
        sick.Behavior = Behavior.Ranged;
        sick.Ranged = new RangedSpec { Range = 7, Cooldown = 3.5, Speed = 8.5, School = School.Nature, Lob = true, Aim = 0.6, Zone = null, Art = "slurry" };

        var ironback = Enemies.Get("boar_ironback").Clone();
        ironback.Slam = new SlamSpec(3, 5, 1.3, 2.8, 1.5);
        ironback.Health = 100; ironback.Speed = 3.0;       // (session 2) 300 held a tusker pack past 25 s; (session 3) 180 still 15 s, it walked in last

        var alpha = Enemies.Get("wolf_alpha").Clone();     // magic pack leader, no line
        alpha.Lunge = null;
        alpha.Health = 300;                                // (session 2) 520 held a magic pack past 20 s

        // (re-tune, session 3) The howler hangs back and calls, but one she can reach: at the table's 4.0 it backed off at 3.6 m/s
        // from 4.4 m, so a called pack's last 12 s were a chase after it alone (measured: last to die in 113 of 124 called packs).
        var howler = Enemies.Get("wolf_howler").Clone();
        howler.Speed = 2.8; howler.Health = 36; howler.KeepOff = 5;   // backs off only inside 2.75 m: in reach of a Leap on its pack

        var sow = Enemies.Get("boar_slurry").Clone();      // slow area-denial, walks in last; not a second wall
        sow.Health = 55;

        var cuts = new Dictionary<string, EnemyDef>
        {
            ["wolf"] = wolf, ["wolf_runner"] = runner, ["wolf_blighted"] = sick, ["boar_ironback"] = ironback, ["wolf_alpha"] = alpha,
            ["wolf_howler"] = howler, ["boar_slurry"] = sow,
        };
        // (first blow) How wide a den pack mills at rest (dungeon_fights.json "roam"; 0, as shipped: a map's 14.4 m box): on
        // every recipe kind, so the kinds the den leaves as the table has them get a den copy too, and the next den-only
        // number reaches the whole pack. (A signed champion's def is Signs.Wear's, made once per process: not reached.)
        var row = DungeonFights.Of("hollow");
        foreach (var id in Recipes.SelectMany(r => r.Parts.Select(p => p.Def)).Distinct())
            if (!cuts.ContainsKey(id)) cuts[id] = Enemies.Get(id).Clone();
        foreach (var d in cuts.Values) d.Roam = row.Roam;
        return cuts;
    }

    public static readonly Recipe[] Recipes =
    [
        new("hunting", [new("wolf", 4, false), new("wolf_runner", 2, false), new("boar", 1, true)]),
        new("sick", [new("wolf", 3, false), new("wolf_blighted", 1, true), new("boar_slurry", 1, true), new("wolf_runner", 1, false)]),
        new("called", [new("wolf_howler", 1, true), new("wolf_runner", 4, false), new("wolf", 2, false)]),
        new("tusker", [new("boar_ironback", 1, true), new("boar", 1, true), new("wolf", 4, false)]),
    ];

    public static readonly string[] Guardians = ["mb_old_tusk", "mb_whitethroat", "mb_blight_mother"];

    /// <summary>Every kind the den fields, so their visuals load (MapRun.Creatures).</summary>
    public static IEnumerable<string> Kinds =>
        Recipes.SelectMany(r => r.Parts.Select(p => p.Def))
            .Concat(["wolf_alpha", "boar_ironback", "wolf_blighted"]).Concat(Guardians).Distinct();
}
