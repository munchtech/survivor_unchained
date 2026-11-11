namespace SurvivorUnchained.Sound;

public static partial class Sfx
{
    /// <summary>A sound by its id (data/content/sounds.json): plays the bank's event, and does nothing if it has no takes yet.
    /// For anything that has no recipe of its own to fall back on (SoundHooks.Play reaches it from the game's code).</summary>
    public static void Cue(string id, Where w = default) => SoundBank.Play(id, w.Near == 0 && w.Pan == 0 ? Center : w);

    /// <summary>Where for a sound with no place: heard in full, centered.</summary>
    static readonly Where Center = new(0, 1);

    /// <summary>Ask the bank for a sound: true if it played and the made recipe is to be skipped (the event's "synth": "replace").
    /// `gated: false` where the recipe has gated already. No place given: heard in full, centered.</summary>
    static bool Bank(string id, Where? w = null, double gain = 1, double? at = null, double pitch = 1, bool gated = true) =>
        SoundBank.Play(id, w ?? Center, gain, at, pitch, gated) == Banked.Replace;

    /// <summary>The first of a chain of ids that the bank can play (a fallback: art.moon.swing, then swing).</summary>
    static bool BankFirst(Where? w, bool gated, params string[] ids) => SoundBank.PlayFirst(w ?? Center, 1, 1, gated, ids) == Banked.Replace;

    /// <summary>A boss's or elite's tell as it winds up or lands (telegraph.charge.windup.boss, then telegraph.charge.windup):
    /// recorded only, no synth fallback. The Pack's howl, the dead's horn and the rest still go through Tell.</summary>
    public static void Telegraph(string tell, bool land, bool boss, Where w = default, double? windup = null)
    {
        using var _lead = Synth.LeadFor(true);
        string phase = land ? "land" : "windup";
        double? len = land ? null : windup; // the windup ends as the blow lands, whatever the take's length or pitch
        if (boss) SoundBank.PlayFirstFor(len, w, $"telegraph.{tell}.{phase}.boss", $"telegraph.{tell}.{phase}");
        else SoundBank.PlayFirstFor(len, w, $"telegraph.{tell}.{phase}");
    }
}
