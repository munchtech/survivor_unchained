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

    /// <summary>A mass kill's step lands over a frame or two (her step's last kills come a frame late): the blows of this
    /// many drawn frames after the mass step are added into its one total.</summary>
    public const int MassTailFrames = 3;
    public static bool MassTail(long since) => since > 0 && since <= MassTailFrames;

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

    /// <summary>F1 r6 (judge r5 fix 1): a launched body on screen: its box at the blow (px, y down; its hop already
    /// added on top) and where the launch takes it (Lx, Ly: the whole throw on screen, px).</summary>
    public readonly record struct Flight(float X0, float Y0, float X1, float Y1, float Lx, float Ly);

    /// <summary>The clear gap kept between a number and a launched body's path (px at 1080).</summary>
    public const float FlightGap = 8;

    /// <summary>Whether a number's box (nx0..nx1, ny0..ny1) meets the body's whole flight: the convex hull of its box at
    /// the blow and at the end of the throw (separating axes: the screen's two and the one across the throw).</summary>
    public static bool CrossesFlight(float nx0, float ny0, float nx1, float ny1, Flight f)
    {
        if (nx1 <= Math.Min(f.X0, f.X0 + f.Lx) || nx0 >= Math.Max(f.X1, f.X1 + f.Lx)) return false;
        if (ny1 <= Math.Min(f.Y0, f.Y0 + f.Ly) || ny0 >= Math.Max(f.Y1, f.Y1 + f.Ly)) return false;
        float len = MathF.Sqrt(f.Lx * f.Lx + f.Ly * f.Ly);
        if (len < 1e-3f) return true;
        float ax = -f.Ly / len, ay = f.Lx / len;
        float bc = ax * (f.X0 + f.X1) / 2 + ay * (f.Y0 + f.Y1) / 2, br = MathF.Abs(ax) * (f.X1 - f.X0) / 2 + MathF.Abs(ay) * (f.Y1 - f.Y0) / 2;
        float nc = ax * (nx0 + nx1) / 2 + ay * (ny0 + ny1) / 2, nr = MathF.Abs(ax) * (nx1 - nx0) / 2 + MathF.Abs(ay) * (ny1 - ny0) / 2;
        return MathF.Abs(nc - bc) < br + nr;
    }

    /// <summary>The side a launched victim's number takes: across its throw on screen (never along it), the upper of the
    /// two; when the throw is near up or down the screen, the side away from her (herX; the right when level with her).</summary>
    public static (float X, float Y) Across(float lx, float ly, float cx, float herX)
    {
        float len = MathF.Sqrt(lx * lx + ly * ly);
        if (len < 1e-3f) return (cx < herX - 1 ? -1 : 1, 0);
        float ax = -ly / len, ay = lx / len;
        if (MathF.Abs(ay) < 0.3f) { float side = cx < herX - 1 ? -1 : 1; if (ax * side < 0) { ax = -ax; ay = -ay; } }
        else if (ay > 0) { ax = -ax; ay = -ay; }
        return (ax, ay);
    }

    /// <summary>A launched victim's number (judge r5: "432" lay across a body thrown in under it for 8 frames): NumberOver
    /// over its top and NumberAside across its throw (Across), then moved on across it, 10 px at a time, until its box,
    /// lengthened upward by its own rise (`rise`, px), meets none of the flights (the victim's and the step's `others`)
    /// and none of the `keep` rects (her body and the strap under her, each already grown by its gap: F1 lead 29, m4b:
    /// the number placed clear of the flights was then nudged sideways off her, back over a rising body). Where that
    /// side has nothing clear in 24 steps, the other side across the throw; where neither, the least crossed.
    /// `w`, `h`: the number's box size.</summary>
    public static (float X, float Y) NumberSpotLaunched(Flight body, IReadOnlyList<Flight>? others, float herX, float w, float h, float scale = 1, float rise = 0,
        IReadOnlyList<(float X0, float Y0, float X1, float Y1)>? keep = null)
    {
        float cx = (body.X0 + body.X1) / 2;
        var (ax, ay) = Across(body.Lx, body.Ly, cx, herX);
        float g = FlightGap * scale;
        int Crossed(float px, float py)
        {
            float x0 = px - w / 2 - g, x1 = px + w / 2 + g, y0 = py - h / 2 - rise - g, y1 = py + h / 2 + g;
            int n = CrossesFlight(x0, y0, x1, y1, body) ? 1 : 0;
            if (others != null) foreach (var o in others) if (CrossesFlight(x0, y0, x1, y1, o)) n++;
            if (keep != null) foreach (var r in keep) if (x1 > r.X0 && x0 < r.X1 && y1 > r.Y0 && y0 < r.Y1) n++;
            return n;
        }
        (float X, float Y) best = default;
        int least = int.MaxValue;
        for (int side = 1; side >= -1; side -= 2)
        {
            float sx = ax * side, sy = ay * side;
            float x = cx + sx * NumberAside * scale, y = body.Y0 - NumberOver * scale - h / 2 + sy * NumberAside * scale;
            for (int step = 0; step <= 24; step++)
            {
                float px = x + sx * 10 * scale * step, py = y + sy * 10 * scale * step;
                int n = Crossed(px, py);
                if (n == 0) return (px, py);
                if (n < least) { least = n; best = (px, py); }
            }
        }
        return best;
    }

    /// <summary>F1 lead 30 (judge n, m5b/m4: the mass total "501" carried ~250 px up the frame by the launched search,
    /// "1763" ~200 px below-left of its five felled over the living pack): the furthest a mass kill's total box stands
    /// off the felled bodies' box (px at 1080, the gap between the boxes, at its birth).</summary>
    public const float MassReach = 80;

    /// <summary>The gap between two boxes (px; 0 where they meet).</summary>
    public static float BoxGap(float ax0, float ay0, float ax1, float ay1, float bx0, float by0, float bx1, float by1)
    {
        float dx = Math.Max(0, Math.Max(bx0 - ax1, ax0 - bx1)), dy = Math.Max(0, Math.Max(by0 - ay1, ay0 - by1));
        return MathF.Sqrt(dx * dx + dy * dy);
    }

    /// <summary>How many of `flights` a number's box at (px, py) meets, lengthened upward by its rise and grown by FlightGap
    /// (a felled body that is not thrown is a Flight with no throw: its box).</summary>
    public static int FlightsCrossed(float px, float py, float w, float h, IReadOnlyList<Flight>? flights, float scale = 1, float rise = 0)
    {
        if (flights == null) return 0;
        float g = FlightGap * scale, x0 = px - w / 2 - g, x1 = px + w / 2 + g, y0 = py - h / 2 - rise - g, y1 = py + h / 2 + g;
        int n = 0;
        foreach (var f in flights) if (CrossesFlight(x0, y0, x1, y1, f)) n++;
        return n;
    }

    /// <summary>F1 lead 30: where a mass kill's one total goes (its box centre, px, y down): it stays by its kill. Preferred
    /// is NumberSpot over the felled bodies' box (`felled`: NumberOver over its top, NumberAside away from her); among the
    /// spots on a 10 px grid whose box stays within MassReach of `felled`, the one meeting the fewest `flights` (every
    /// launched body's whole flight and every felled body's box) takes it, nearest the preferred on a tie. Never on her: a
    /// spot meeting a `keep` rect (her body, the strap, each grown by its gap) or past `bounds` (the screen's room for a
    /// number: left, top, right, bottom) loses to any that does not. The across-the-throw search (NumberSpotLaunched) is a
    /// single launched victim's: it carried a total up to 250 px off its kill.</summary>
    public static (float X, float Y) MassTotalSpot((float X0, float Y0, float X1, float Y1) felled, IReadOnlyList<Flight>? flights,
        float herX, float w, float h, float scale = 1, float rise = 0,
        IReadOnlyList<(float X0, float Y0, float X1, float Y1)>? keep = null, (float X0, float Y0, float X1, float Y1)? bounds = null,
        float reach = MassReach)
    {
        var (fx0, fy0, fx1, fy1) = felled;
        var pref = NumberSpot(fx0, fy0, fx1, fy1, herX, w, h, scale);
        float r = reach * scale, step = 10 * scale, g = FlightGap * scale;
        int Cost(float px, float py)
        {
            int n = FlightsCrossed(px, py, w, h, flights, scale, rise);
            float x0 = px - w / 2 - g, x1 = px + w / 2 + g, y0 = py - h / 2 - rise - g, y1 = py + h / 2 + g;
            if (keep != null) foreach (var k in keep) if (x1 > k.X0 && x0 < k.X1 && y1 > k.Y0 && y0 < k.Y1) n += 1000;
            if (bounds is { } b && (px - w / 2 < b.X0 || py - h / 2 - rise < b.Y0 || px + w / 2 > b.X1 || py + h / 2 > b.Y1)) n += 1000;
            return n;
        }
        (float X, float Y) best = pref;
        int least = BoxGap(pref.X - w / 2, pref.Y - h / 2, pref.X + w / 2, pref.Y + h / 2, fx0, fy0, fx1, fy1) <= r ? Cost(pref.X, pref.Y) : int.MaxValue;
        float bestD = 0;
        if (least == 0) return pref;
        // (the grid is laid from the preferred spot, so the preferred spot itself is on it)
        int nx0 = (int)MathF.Floor((fx0 - r - w / 2 - pref.X) / step), nx1 = (int)MathF.Ceiling((fx1 + r + w / 2 - pref.X) / step);
        int ny0 = (int)MathF.Floor((fy0 - r - h / 2 - pref.Y) / step), ny1 = (int)MathF.Ceiling((fy1 + r + h / 2 - pref.Y) / step);
        for (int iy = ny0; iy <= ny1; iy++)
            for (int ix = nx0; ix <= nx1; ix++)
            {
                float px = pref.X + ix * step, py = pref.Y + iy * step;
                if (BoxGap(px - w / 2, py - h / 2, px + w / 2, py + h / 2, fx0, fy0, fx1, fy1) > r) continue;
                int n = Cost(px, py);
                float d = (px - pref.X) * (px - pref.X) + (py - pref.Y) * (py - pref.Y);
                if (n < least || (n == least && d < bestD)) { least = n; best = (px, py); bestD = d; }
            }
        return best;
    }

    /// <summary>F1 lead 30 (judge n fix 1): when her kill window opens at frame `open`, a number clears off the kill only if
    /// it was born on an earlier frame (`born` &lt; `open`) and stands within KillClearReach: the total of the kill that
    /// opens the window is never cleared by it.</summary>
    public static bool ClearsAtOpen(long born, long open, float x, float y, float kx, float ky, float scale = 1) =>
        born < open && KillClears(x, y, kx, ky, scale);

    /// <summary>The lowest a number's middle stands (px at 1080): the HUD's band starts under it (judge r5: "315" on the
    /// health orb), and the gap it keeps over a HUD part.</summary>
    public const float NumberFloor = 880, HudGap = 8;

    /// <summary>A number's middle y kept off the HUD (only ever lifted): its middle at or over NumberFloor, its box's bottom
    /// HudGap over the HUD's top under it (`hudTop`, null where none stands), and over the orb's top where its box spans
    /// the orb's x (`orb`: its left, top and right; px on screen). `k`: the screen's height over 1080.</summary>
    public static float HudSafeY(float cx, float cy, float w, float h, float k, float? hudTop = null, (float X0, float Y0, float X1)? orb = null)
    {
        float y = Math.Min(cy, NumberFloor * k);
        if (hudTop is float t) y = Math.Min(y, t - HudGap * k - h / 2);
        if (orb is { } o && cx + w / 2 > o.X0 - HudGap * k && cx - w / 2 < o.X1 + HudGap * k) y = Math.Min(y, o.Y0 - HudGap * k - h / 2);
        return y;
    }

    /// <summary>When her kill window opens (frame N), numbers of earlier steps within KillClearReach of the kill's middle
    /// (px at 1080) clear off it (judge r5: "3783" and "928" stood over a new kill): gone by N + KillClearFrames.</summary>
    public const float KillClearReach = 300;
    public const int KillClearFrames = 3;
    public static bool KillClears(float x, float y, float kx, float ky, float scale = 1)
    {
        float dx = x - kx, dy = y - ky, r = KillClearReach * scale;
        return dx * dx + dy * dy <= r * r;
    }

    /// <summary>A clearing number's alpha `since` frames after the window opened: front-loaded, 0 by KillClearFrames.</summary>
    public static float KillClear(long since)
    {
        if (since < 0) return 1;
        if (since >= KillClearFrames) return 0;
        float u = 1 - (since + 1f) / (KillClearFrames + 1);
        return u * u;
    }
}
