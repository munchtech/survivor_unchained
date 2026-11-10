namespace SurvivorUnchained.Look;

/// <summary>(L1 lead 22, mirror) A bone's left/right twin by its name, for a pose reflected across the body's
/// sagittal plane (PoseMirror, --hold-mirror): `hand_l` / `hand_r`, `upperarm.L` / `upperarm.R`, `thigh_L`,
/// `LeftHand` / `RightHand`, `index_01_l_end`-style infixes. A centre bone (pelvis, spine_02, head) is its own twin.</summary>
public static class MirrorPairs
{
    static readonly (string L, string R)[] Suffix = { ("_l", "_r"), ("_L", "_R"), (".l", ".r"), (".L", ".R") };
    static readonly (string L, string R)[] Infix = { ("_l_", "_r_"), ("_L_", "_R_"), (".l.", ".r."), (".L.", ".R.") };
    static readonly (string L, string R)[] Word = { ("Left", "Right"), ("left", "right"), ("LEFT", "RIGHT") };

    /// <summary>The twin's name, or the name itself for a centre bone.</summary>
    public static string Pair(string name)
    {
        foreach (var (l, r) in Suffix)
        {
            if (name.Length > l.Length && name.EndsWith(l, System.StringComparison.Ordinal)) return name[..^l.Length] + r;
            if (name.Length > r.Length && name.EndsWith(r, System.StringComparison.Ordinal)) return name[..^r.Length] + l;
        }
        foreach (var (l, r) in Infix)
        {
            int i = name.IndexOf(l, System.StringComparison.Ordinal);
            if (i > 0) return name[..i] + r + name[(i + l.Length)..];
            i = name.IndexOf(r, System.StringComparison.Ordinal);
            if (i > 0) return name[..i] + l + name[(i + r.Length)..];
        }
        foreach (var (l, r) in Word)
        {
            int i = name.IndexOf(l, System.StringComparison.Ordinal);
            if (i >= 0) return name[..i] + r + name[(i + l.Length)..];
            i = name.IndexOf(r, System.StringComparison.Ordinal);
            if (i >= 0) return name[..i] + l + name[(i + r.Length)..];
        }
        return name;
    }
}
