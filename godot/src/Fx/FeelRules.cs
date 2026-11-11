using System;
using System.Collections.Generic;

namespace SurvivorUnchained.View;

/// <summary>
/// F1 lead 27 (round 5): the combat-readability rules with no Godot in them (the tests compile this file).
/// What must come true at 1:1, at speed: the player sees who was hit and sees bodies fly.
/// Frame counts are drawn frames at 60 fps (the judge's frame numbers).
/// </summary>
public static class FeelRules
{
    /* ------------------------------------------------ the kill window -- */

    /// <summary>Her step that fells 4 or more (Ev.Kill Mass) opens the kill window at its frame N. The launched bodies
    /// hold the hit-stop to about N+7 and fly from about N+8, so the window covers the stop and the first of the flight.</summary>
    public const int KillHold = 16, KillBack = 6;
    /// <summary>What everything that is not the kill (the Warden's bell, toll, Rebuke lash and gold rim; an enemy kit
    /// mark already up: a closing's band and ring, a lane) is held to in the window.</summary>
    public const float KillDimTo = 0.3f;

    /// <summary>The dim on what is not the kill, `since` drawn frames after the mass kill (negative or none: 1).
    /// KillDimTo from N to N+KillHold, back to 1 by N+KillHold+KillBack (eased, no pop).</summary>
    public static float KillDim(long since)
    {
        if (since < 0 || since > KillHold + KillBack) return 1;
        if (since <= KillHold) return KillDimTo;
        float u = (since - KillHold) / (float)KillBack;
        u = u * u * (3 - 2 * u);
        return KillDimTo + (1 - KillDimTo) * u;
    }

    /// <summary>An enemy tell is a warning first (ruling 10:06): in the kill window only its fill dims; its edge (the
    /// rims' light) keeps TellEdgeFloor or more; in its last TellLandGuard seconds before it lands, and for any lane
    /// (an elite's lane ranks the danger: item 5), nothing dims.</summary>
    public const float TellEdgeFloor = 0.6f, TellLandGuard = 0.3f;

    /// <summary>A tell's fill strength under the kill dim `killDim`, `secsToLand` before its blow lands (a wall already
    /// standing: float.MaxValue).</summary>
    public static float TellFill(float killDim, float secsToLand, bool lane) =>
        lane || secsToLand <= TellLandGuard ? 1 : killDim;

    /// <summary>A tell's edge (rim light) strength under the kill dim, as TellFill.</summary>
    public static float TellEdge(float killDim, float secsToLand, bool lane) =>
        lane || secsToLand <= TellLandGuard ? 1 : Math.Max(killDim, TellEdgeFloor);

    /// <summary>A launched body's warm rim (#ff9a40 kind, the body's own material): whole from its kill frame to
    /// N+LaunchRimHold (the stop and the first frames of its flight), faded to nothing by N+LaunchRimGone.</summary>
    public const int LaunchRimHold = 12, LaunchRimGone = 18;

    /// <summary>A launched body's rim strength (0..1) `since` drawn frames after its kill.</summary>
    public static float LaunchRim(long since)
    {
        if (since < 0 || since >= LaunchRimGone) return 0;
        if (since <= LaunchRimHold) return 1;
        float u = 1 - (since - LaunchRimHold) / (float)(LaunchRimGone - LaunchRimHold);
        return u * u;
    }

    /* ------------------------------------------- the struck survivor -- */

    /// <summary>A struck living body's recoil away from her (m) when her hold ends (was 0.5: a nudge at 1:1).</summary>
    public const double RecoilM = 0.8;

    /// <summary>The hit-react: head and shoulders snap away from her as the hold ends, then recover. Seconds: up over
    /// ReactUp, held to ReactHold, back by ReactEnd (about 7 frames in all at 60 fps).</summary>
    public const double ReactUp = 0.03, ReactHold = 0.05, ReactEnd = 0.12;
    /// <summary>The react's lean (degrees, the body tipped back away from her about its feet) and head turn (degrees of
    /// yaw away from her) at its peak.</summary>
    public const float ReactLeanDeg = 24, ReactTurnDeg = 28;

    /// <summary>The react's strength (0..1) `t` seconds after the hold ended (negative: none).</summary>
    public static float React(double t)
    {
        if (t < 0 || t >= ReactEnd) return 0;
        if (t < ReactUp) { double u = t / ReactUp; return (float)(1 - (1 - u) * (1 - u)); }
        if (t < ReactHold) return 1;
        double v = (t - ReactHold) / (ReactEnd - ReactHold);
        return (float)(1 - v * v * (3 - 2 * v));
    }

    /// <summary>The struck tint and a crit victim's warm rim wait for the victim flash (the pool: 3 frames held, 3 fading)
    /// to go: from TintFrom drawn frames after the strike, for TintFor frames.</summary>
    public const int TintFrom = 6, TintFor = 4;
    /// <summary>The struck tint's strength in the ember look (a launched body's is 1), held down in the kill window.</summary>
    public const float TintWarm = 0.45f;
    public static bool Tinted(long sinceStruck) => sinceStruck >= TintFrom && sinceStruck < TintFrom + TintFor;

    /* ----------------------------------------------------- the numbers -- */

    /// <summary>At most this many new damage numbers a step; the rest are added into the biggest.</summary>
    public const int NumbersPerStep = 2;

    /// <summary>One step's numbers to show: indices into `amounts` (already ordered weightiest first, the order they
    /// would be shown in) and the sum each carries. Past NumbersPerStep (or past 1 on a mass-kill step: one total) the
    /// rest are added into the first (the biggest). `folded[i]` is the index each input was shown under.</summary>
    public static List<(int Index, double Sum)> Fold(IReadOnlyList<double> amounts, bool massStep, out int[] folded)
    {
        int keep = massStep ? 1 : NumbersPerStep;
        var shown = new List<(int, double)>();
        folded = new int[amounts.Count];
        for (int i = 0; i < amounts.Count; i++)
        {
            if (shown.Count < keep) { shown.Add((i, amounts[i])); folded[i] = i; continue; }
            var (j, s) = shown[0];
            shown[0] = (j, s + amounts[i]);
            folded[i] = j;
        }
        return shown;
    }

    /// <summary>A number's lift over its victim (px at 1080): its box's bottom this far over the body's top on screen.</summary>
    public const float NumberOver = 50;
    /// <summary>And this far to the side away from her (px at 1080; the side the victim is on of her; the right when
    /// straight above or below her).</summary>
    public const float NumberAside = 40;

    /// <summary>Where a number's box centre goes on screen (px, y down): over the victim whose body's screen box is
    /// (bx0..bx1, by0..by1), away from her (herX), never across the body. `w`, `h`: the number's box size.</summary>
    public static (float X, float Y) NumberSpot(float bx0, float by0, float bx1, float by1, float herX, float w, float h, float scale = 1)
    {
        float cx = (bx0 + bx1) / 2;
        float side = cx < herX - 1 ? -1 : 1;
        float x = cx + side * NumberAside * scale;
        float y = by0 - NumberOver * scale - h / 2;
        return (x, y);
    }
}
