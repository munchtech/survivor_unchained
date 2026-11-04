namespace SurvivorUnchained.Sound;

/// <summary>Named sound moments other areas raise without owning the sound (H4 with H3, 3 Nov):
/// the audio lead wires <see cref="Cue"/> once at startup (SoundHooks.Cue = id => Sfx.Cue(id)).
/// Ids: "ui.way_out" (a night's way out opens: its banner), "ui.skill_ready" (a skill seat ready again),
/// "cine.to_play" (a cinematic's camera has landed in play and control is back).</summary>
public static class SoundHooks
{
    public static System.Action<string>? Cue;
    public static void Play(string id) => Cue?.Invoke(id);
}
