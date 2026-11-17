using Godot;

namespace SurvivorUnchained.Play;

/// <summary>(aim-move) Whom she faces. Always: the cursor, standing or moving (her legs run the directional set under her turned
/// pelvis). Skill: her travel, and the cursor's side only while a skill's strike holds her aim.</summary>
public enum FacingMode { Always, Skill }

/// <summary>The current facing mode: --facing-mode always|skill, else the setting (Settings.FacingMode); F7 toggles it live.</summary>
public static class Facing
{
    public static FacingMode Current = Parse(Args.Get("facing-mode") ?? Settings.Current.FacingMode);

    static FacingMode Parse(string? s) => s != null && s.Equals("skill", System.StringComparison.OrdinalIgnoreCase) ? FacingMode.Skill : FacingMode.Always;

    public static string Name => Current == FacingMode.Always ? "always" : "skill";

    /// <summary>Flips the mode, keeps it in the settings, prints it. Returns the new name.</summary>
    public static string Toggle()
    {
        Current = Current == FacingMode.Always ? FacingMode.Skill : FacingMode.Always;
        Settings.Current.FacingMode = Name;
        Settings.Current.Save();
        GD.Print("FACING MODE " + Name);
        return Name;
    }
}
