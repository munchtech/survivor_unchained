namespace SurvivorUnchained.Rpg;

/// <summary>Plain words for why a lamp or a wick lamp was refused (the functional Lamps board and Wick screen).</summary>
public static class BoardWords
{
    public static string Why(LampNo n) => n switch
    {
        LampNo.None => "",
        LampNo.Unknown => "There is no such lamp.",
        LampNo.Lit => "It is already lit.",
        LampNo.Unlit => "It is not lit.",
        LampNo.NoLamps => "No spare lamps. Earn more by levels, story fights and the atlas.",
        LampNo.NotHome => "Only that calling may light this one.",
        LampNo.Dark => "Light a lamp beside it first.",
        LampNo.Gate => "Light more lamps on this road first.",
        LampNo.Free => "This lamp is free and stays lit.",
        LampNo.Holds => "Other lit lamps hang from this one. Put those out first.",
        _ => "",
    };

    public static string Why(WickNo n) => n switch
    {
        WickNo.None => "",
        WickNo.NoWick => "This skill has no wick yet.",
        WickNo.Unknown => "That lamp is not on this skill's wick.",
        WickNo.Planned => "It is already in the plan.",
        WickNo.Unplanned => "It is not in the plan.",
        WickNo.Order => "Plan the lamp before it in this strand first.",
        WickNo.Turn => "Only one Turn can be planned.",
        WickNo.Full => "The plan is full (twelve lamps).",
        WickNo.Holds => "A later lamp of this strand stands on it. Unplan that first.",
        _ => "",
    };
}
