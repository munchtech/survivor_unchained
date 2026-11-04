using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.World;

/// <summary>
/// The app can now make a permanent zone reset like a Diablo zone, as data (data/content/zone_resets.json): its state
/// (WorldState.Zone(id): packs down, chests opened) is cleared on its rule's turn ("day": the day change) and kept
/// within it. One piece for every zone that wants it (the Low Ford Road by day now; the Wayfinder's later maps).
/// World facts (a relit lamp-post) are never zone state, so never reset.
/// </summary>
public static class ZoneReset
{
    public sealed class Rule
    {
        /// <summary>"day": cleared on the day change; "never": kept for good.</summary>
        public string Reset = "never";
        /// <summary>Key prefixes in the zone's state that are never cleared.</summary>
        public List<string> Keep = new();
    }

    sealed class File { public Dictionary<string, Rule> Zones = new(); }

    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("zone_resets.json"));

    /// <summary>The key in a zone's state that holds the turn it was last reset for (the day).</summary>
    public const string Stamp = "_reset";

    /// <summary>The zone's rule, or null for a zone without one (its state is as it always was).</summary>
    public static Rule? For(string zone) => F.Zones.TryGetValue(zone, out var r) ? r : null;

    /// <summary>The turn a rule counts in now: the day for "day", 0 for "never".</summary>
    public static int Turn(Rule r, WorldState w) => r.Reset == "day" ? w.Day : 0;

    /// <summary>Applies the zone's rule as it is entered (or as the clock turns while she is in it): a new turn clears its
    /// state but the kept keys, and stamps the turn. True when something was cleared.</summary>
    public static bool Apply(WorldState w, string zone) => For(zone) is { } r && Apply(w, zone, r);

    public static bool Apply(WorldState w, string zone, Rule r)
    {
        var st = w.Zone(zone);
        int now = Turn(r, w);
        if (st.TryGetValue(Stamp, out var f) && (int)f.Number == now) return false;
        bool cleared = false;
        foreach (var k in st.Keys.ToList())
        {
            if (k == Stamp || r.Keep.Any(k.StartsWith)) continue;
            st.Remove(k);
            cleared = true;
        }
        st[Stamp] = now;
        return cleared;
    }
}
