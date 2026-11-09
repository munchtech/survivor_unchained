using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* The dash's growth as named, visible steps (data/content/dash_steps.json). The owner, 8 Nov: "dashes ... its
 * decent fundamentally - its improvements behind the scenes are awkward - just pushing the button leveling it up is
 * weird". So the dash no longer ranks by use: a movement art stays rank 1 (ArtBook.Rank) and grows only by these,
 * each one a card the player reads when it is granted (Journey.GrantDashStep, Ev.DashStep). The steps chosen live on
 * the survivor (CharacterData.DashSteps) and enter every fight at its start (BattleSetup.DashSteps,
 * Sim/DashGrowth.cs). In play (ARPG.md 3.3) Hard Landing is a board hearth lamp and the rest come from story beats and gear, never a
 * level-up card or the ember's cards; console grants (--dash-step) until then. */

public enum DashStepKind { Charge, Length, Recharge, Landing }

public sealed class DashStepDef
{
    public string Id = "", Name = "", Card = "";
    public DashStepKind Kind;
    /// <summary>Charge: pips added; Length: the share farther; Recharge: the share sooner.</summary>
    public double Amount;
    /// <summary>Landing: the shove's reach (m), its knockback and its damage.</summary>
    public double Radius, Knockback, Damage;
    /// <summary>The lamp the board lights for this step ("dash.&lt;id&gt;"): Hard Landing's only, a Warden hearth lamp
    /// (ARPG.md 3.3); the rest have none.</summary>
    public string Lamp = "";
    /// <summary>Where a step with no lamp is earned (story, gear): never a level-up card or the ember's cards.</summary>
    public string[] From = System.Array.Empty<string>();
    /// <summary>Times it may be taken (1 if unset).</summary>
    public int Most = 1;
}

public sealed class DashStepsFile
{
    public List<DashStepDef> Steps = new();
}

public static class DashSteps
{
    /// <summary>Pips the steps may add, at most (Another Breath twice).</summary>
    public const int MaxPips = 2;

    static DashStepsFile? file;
    static Dictionary<string, DashStepDef>? byId;

    public static DashStepsFile File => file ??= Parse(Json.ReadContent("dash_steps.json"));
    public static DashStepsFile Parse(string json) => Json.Parse<DashStepsFile>(json);

    public static IReadOnlyList<DashStepDef> All => File.Steps;
    public static DashStepDef? Find(string id) => (byId ??= File.Steps.ToDictionary(s => s.Id)).TryGetValue(id, out var d) ? d : null;

    /// <summary>May one more of this step be taken, with these taken already?</summary>
    public static bool CanTake(IEnumerable<string> taken, string id) =>
        Find(id) is { } d && taken.Count(t => t == id) < System.Math.Max(1, d.Most);
}
