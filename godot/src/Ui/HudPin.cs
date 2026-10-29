using System;
using System.Globalization;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Debug only (Args reads nothing in a player's build): holds what the instrument DISPLAYS, every frame, for
/// pictures. Not gameplay: the fight runs on underneath.
///   --hud-pin "life=0.4,shield=0.3,ember=0.7,lockheat=0.5,draught=0,art=1,seats=f3:h:e"
///     life 0-1 (her life), shield 0-1 (a fraction of her max life), ember 0-1 (the chain's fill), lockheat 0-1,
///     draught (a count, 0 = empty), art 0-1 (the art glass's level), seats: one code per seat from the left,
///     f3 = filled at rank 3 of 8, h = filled and hot (can evolve), e = empty (night); missing = empty;
///     behind=1: the Drowned Girl's figure faded as if something were behind it; day=1|0: her XP thread
///     drawn as by day (her experience) or by night (the ember), whatever the fight is; dash=1.4: the dash's
///     charges held (1 held, the next 40% back).
///     UI 18, the experience light (the game's HUD): xp=run:F:T the light T seconds after a gain to F from rest,
///     xp=rise:F:T T seconds after a level-up (F carried over), xp=rest:F the resting glow at F after its
///     gain has settled, xp=dark (or dark:F) dark after the long quiet; xptip=hold (the hold key's card, at the run's front) or
///     xptip=X:Y (the pointer's card, the pointer at X, Y); xpnum=LEVEL:HAVE:NEED the card's numbers.
///   --hud-seq "state;state;..." [--hud-seq-every S]: Shots.cs steps through the states (each one applied over
///     --hud-pin) and saves SHOT_hud0.png, SHOT_hud1.png...
/// </summary>
public static class HudPin
{
    public static float? Life, Shield, Ember, LockHeat, Art, Dash;
    /// <summary>UI 23: her hair's shine held at this front (screen run px, the idle sheen off); the coin's level.</summary>
    public static float? Shine;
    public static int? Level;
    public static int? Draught;
    public static bool? Behind, Day;
    public static string[]? Seats;
    public static string? Xp, XpTip;
    public static int[]? XpNum;
    static readonly string baseSpec = Args.Get("hud-pin") ?? "";
    /// <summary>The sequence's states (empty: none).</summary>
    public static readonly string[] Seq = Args.Get("hud-seq") is string q ? q.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries) : [];

    public static bool Active { get; private set; } = Args.Has("hud-pin") || Args.Has("hud-seq");

    static HudPin() { if (Active) Parse(baseSpec); }

    /// <summary>Sequence state k: the pin over a clean slate.</summary>
    public static void Use(int k)
    {
        Life = Shield = Ember = LockHeat = Art = Dash = null; Draught = null; Seats = null; Behind = null; Day = null;
        Xp = XpTip = null; XpNum = null; Shine = null; Level = null;
        Parse(baseSpec);
        if (k >= 0 && k < Seq.Length) Parse(Seq[k]);
    }

    static void Parse(string spec)
    {
        foreach (var part in spec.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var kv = part.Split('=', 2);
            if (kv.Length < 2) continue;
            float F() => float.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? Math.Clamp(v, 0, 1) : 0;
            switch (kv[0].Trim().ToLowerInvariant())
            {
                case "life": Life = F(); break;
                case "shield": Shield = F(); break;
                case "ember": Ember = F(); break;
                case "lockheat": LockHeat = F(); break;
                case "art": Art = F(); break;
                case "draught": Draught = (int)Math.Round(float.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var d) ? d : 0); break;
                case "behind": Behind = F() > 0.5f; break;
                case "day": Day = F() > 0.5f; break;
                case "dash": Dash = float.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var ds) ? Math.Max(0, ds) : 0; break;
                case "xp": Xp = kv[1]; break;
                case "shine": Shine = float.TryParse(kv[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var sh) ? sh : null; break;
                case "level": Level = int.TryParse(kv[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out var lv) ? lv : null; break;
                case "xptip": XpTip = kv[1]; break;
                case "xpnum": XpNum = Array.ConvertAll(kv[1].Split(':'), v => int.TryParse(v, NumberStyles.Integer, CultureInfo.InvariantCulture, out var n) ? n : 0); break;
                case "seats": Seats = kv[1].Split(':', StringSplitOptions.TrimEntries); break;
            }
        }
    }
}
