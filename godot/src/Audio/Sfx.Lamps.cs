using Godot;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The Lamps screen's sound cues (docs/design/LAMPS_SCREEN_BRIEF.md §11, the Sound column), raised by name at each
/// moment. With a recording "lamps_&lt;cue&gt;" (art/sound) it plays; until the audio lead adds one, a cue that had a sound
/// keeps its stand-in (the interface's tick, pick, deny, close, page) and the rest are silent. --lamps-sfx prints each.
/// Cues: open, close, focus_small, focus_notable, focus_blue, light, light_notable, path_tick, blue_lit, gate_open,
/// put_out, denied, layout, wick_plan, wick_turn.
/// </summary>
public static partial class Sfx
{
    public static void Lamps(string cue)
    {
        if (SurvivorUnchained.Args.Has("lamps-sfx")) GD.Print($"LAMPSFX {cue}");
        // (the focus ticks: at most 12 a second, §11)
        if (cue.StartsWith("focus_") && A is { } g && !g.Gate("lamps_focus", 1, 83)) return;
        if (Recordings.Has("lamps_" + cue))
        {
            if (A is { } a) a.Play(new Clip { Of = "lamps_" + cue, G = 0.2, Pitch = R(0.97, 1.03), Bus = Bus.Ui });
            return;
        }
        switch (cue)
        {
            case "focus_small" or "focus_notable" or "focus_blue" or "path_tick": Hover(); break;
            case "light" or "light_notable" or "wick_plan" or "wick_turn": Pick(); break;
            case "denied": Deny(); break;
            case "put_out": Close(); break;
            case "layout": Page(); break;
        }
    }
}
