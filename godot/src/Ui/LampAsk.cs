using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>What the Lamps screen asks of the board (docs/design/LAMPS_SCREEN_BRIEF.md §14), in one place: each a call
/// into Classes' LampBook and WickBook (Rpg), CopyLayout aside. Session undo needs nothing from Classes: the screen
/// keeps the lamps lit since it opened and puts them out with LampBook.Unlight, skipping only the place check.</summary>
public static class LampAsk
{
    /// <summary>§14.3: the unlit lamps to light, in lighting order (LampBook.PathTo).</summary>
    public static IReadOnlyList<string> PathTo(CharacterData ch, WorldState? w, string id) => LampBook.PathTo(ch, w, id);

    /// <summary>§14.3: light the whole path or nothing (LampBook.LightPath).</summary>
    public static bool LightPath(CharacterData ch, WorldState? w, string id) => LampBook.LightPath(ch, w, id);

    /// <summary>"Copy to II / III" (§9): the active layout, the whole build (type, lamps, Flare, wicks, links, the skills
    /// carried), copied over another. Only where layouts change (LampBook.LayoutsOpen). Stand-in until Classes has one.</summary>
    public static bool CopyLayout(CharacterData ch, int to, WorldState? w, string? zone)
    {
        var s = LampBook.State(ch);
        if (to < 0 || to >= s.Layouts.Count || to == s.Active || !LampBook.LayoutsOpen(w, zone)) return false;
        LampBook.Keep(ch);
        var a = s.Now;
        s.Layouts[to] = new LampLayout
        {
            Type = a.Type, Lit = a.Lit.ToList(), Flare = a.Flare,
            Wicks = a.Wicks.ToDictionary(kv => kv.Key, kv => kv.Value.ToList()),
            Links = new Dictionary<string, string>(a.Links), Carried = a.Carried.ToList(), Held = new Dictionary<string, int>(a.Held),
        };
        return true;
    }

    /// <summary>§14.4: why a lamp is dim (LampBook.Sleeps).</summary>
    public static LampSleep? Sleeps(CharacterData ch, string id) => LampBook.Sleeps(ch, id);

    /// <summary>§14.5: the skill a link fires (her pick, else Light my way's), the skills she may bind, and the pick.</summary>
    public static string? LinkPick(CharacterData ch, string link) => LampBook.LinkPick(ch, link);
    public static IReadOnlyList<string> LinkChoices(CharacterData ch, string link) => LampBook.LinkChoices(ch, link);
    public static bool SetLinkPick(CharacterData ch, string link, string skill) => LampBook.SetLinkPick(ch, link, skill);

    /// <summary>§14.6: the next n lamps Light my way would light, in order, without lighting them.</summary>
    public static IReadOnlyList<string> Suggested(CharacterData ch, WorldState? w, int n) => LampBook.Suggested(ch, w, n);

    /// <summary>§14.8: the wick's whole sum for one skill, from the sim (WickBook.Sum).</summary>
    public static WickSumView? Sum(CharacterData ch, string skill, bool night) => WickBook.Sum(ch, skill, night);
}
