using System.Collections.Generic;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

public partial class Game
{
    readonly Dictionary<string, Cond> stateConds = new();
    double statesT;

    /// <summary>The zone's story states put on its look as the world's facts have them (data/zones/ZONE/states.json:
    /// each state's "when" tested, ZoneView.SetState): at the zone's start, then twice a second, so a fact that changes
    /// while she is there (the Verge's stream run clean) changes the look too. Films and play alike.</summary>
    void LookStates(double dt)
    {
        if ((statesT -= dt) > 0 || scene == null || Journey == null) return;
        statesT = 0.5;
        foreach (var (name, when) in scene.View.StateWhens())
        {
            if (!stateConds.TryGetValue(when, out var c)) stateConds[when] = c = Json.Parse<Cond>(when);
            scene.View.SetState(name, Rules.Test(c, Journey.Ctx));
        }
    }
}
