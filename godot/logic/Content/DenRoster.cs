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
        var runner = Enemies.Get("wolf_runner").Clone();   // fodder swarm, dies to one cut
        runner.Behavior = Behavior.Chase; runner.Health = 14; runner.Lunge = null;

        var sick = Enemies.Get("wolf_blighted").Clone();   // coughs slurry, no ground left
        sick.Behavior = Behavior.Ranged;
        sick.Ranged = new RangedSpec { Range = 7, Cooldown = 3.5, Speed = 8.5, School = School.Nature, Lob = true, Aim = 0.6, Zone = null, Art = "slurry" };

        var ironback = Enemies.Get("boar_ironback").Clone();
        ironback.Slam = new SlamSpec(3, 5, 1.3, 2.8, 1.5);

        var alpha = Enemies.Get("wolf_alpha").Clone();     // magic pack leader, no line
        alpha.Lunge = null;

        return new Dictionary<string, EnemyDef>
        {
            ["wolf_runner"] = runner, ["wolf_blighted"] = sick, ["boar_ironback"] = ironback, ["wolf_alpha"] = alpha,
        };
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
