using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Look;

/// <summary>(P7 take 7) The held cut's stroke, its pure parts (the view: src/Fx/BattleFx.Grip.cs, the paint:
/// shaders/fx_grip_stroke.gdshader). THE PRESS IS LAID, NOT CARRIED: every rib the blade lays stores its own press and
/// whiteness when it is laid; the contact raises the ribs round the blade's crossing once, in place; after that a rib's
/// raise only settles with its own age (drawn frames). Nothing here knows where the head is now.</summary>
public static class GripPaint
{
    /// <summary>One laid rib: the watch's clock it was laid at, its metres along the laid path (S: the fill's anchor) and
    /// as the camera saw them (Q), its base press (x the look's width), the contact's raise on it, its whiteness (0 the
    /// tail's amber, 1 white), the drawn frame the raise began.</summary>
    public struct Rib { public double At; public float S, Q, Base, Raise, White; public int RaiseFrame; }

    /// <summary>The numbers (fx_language.json p7 grip.press): rise = [m seen over which the press rises from the start,
    /// its power, the press at the very start]; lift = [m/s under which the brush has lifted, at which it is whole, the
    /// press's share when lifted]; contact = [the raise at size 1, its reach toward the head (m), toward the tail (m),
    /// the whiteness it adds at size 1]; white = m seen over which the whiteness rises from the start.</summary>
    public readonly record struct Press(float[] Rise, float[] Lift, float[] Contact, float White);

    /// <summary>The contact as it was stamped: its place along the laid path (m), its size, its drawn frame (Size 0: none).</summary>
    public struct Stamp { public float S, Size; public int Frame; }

    static float Clamp01(float x) => Math.Clamp(x, 0f, 1f);
    static float Smooth(float a, float b, float x) { float t = Clamp01((x - a) / Math.Max(b - a, 1e-5f)); return t * t * (3 - 2 * t); }
    /// <summary>A hash in 0..1 (the tines' and streaks' own numbers; the same cut the same every frame).</summary>
    public static float Hash(float i, float seed) { double v = Math.Sin(i * 12.9898 + seed * 78.233) * 43758.5453; return (float)(v - Math.Floor(v)); }

    /// <summary>The base press of a rib laid `q` m (seen) from the stroke's start with the tip at `speed` m/s: the brush
    /// lands (a pointed start), is whole, and lifts as the blade slows (the stroke tapers at both ends).</summary>
    public static float Base(float q, float speed, in Press p)
        => (p.Rise[2] + (1 - p.Rise[2]) * MathF.Pow(Clamp01(q / Math.Max(p.Rise[0], 1e-3f)), p.Rise[1])) * (p.Lift[2] + (1 - p.Lift[2]) * Smooth(p.Lift[0], p.Lift[1], speed));

    /// <summary>The contact's raise at `s` m of the laid path: whole at the crossing, none a reach away either way.</summary>
    public static float Bump(float s, in Stamp c, in Press p)
    {
        if (c.Size <= 0) return 0;
        float x = Clamp01(Math.Abs(s - c.S) / Math.Max(s > c.S ? p.Contact[1] : p.Contact[2], 1e-3f));
        return (1 - x * x) * (1 - x * x);
    }

    /// <summary>Lays one rib at the path's end: `ds` m on from the last (dq as the camera sees it). A rib laid after the
    /// contact inside its reach is laid pressed.</summary>
    public static void Lay(List<Rib> ribs, double at, float ds, float dq, float speed, int frame, in Press p, in Stamp c)
    {
        var r = new Rib { At = at, RaiseFrame = frame };
        if (ribs.Count > 0) { r.S = ribs[^1].S + ds; r.Q = ribs[^1].Q + dq; }
        r.Base = Base(r.Q, speed, p);
        r.White = Clamp01(r.Q / Math.Max(p.White, 1e-3f));
        float b = Bump(r.S, c, p);
        if (b > 0) { r.Raise = c.Size * p.Contact[0] * b; r.White += c.Size * p.Contact[3] * b; }
        ribs.Add(r);
    }

    /// <summary>The contact: the ribs already laid round the crossing are pressed once, where they lie (never again, never
    /// moved); the stamp is kept for the ribs still to be laid inside its reach.</summary>
    public static Stamp Strike(List<Rib> ribs, float s, float size, int frame, in Press p)
    {
        var c = new Stamp { S = s, Size = size, Frame = frame };
        for (int i = 0; i < ribs.Count; i++)
        {
            float b = Bump(ribs[i].S, c, p);
            if (b <= 0) continue;
            var r = ribs[i];
            float raise = size * p.Contact[0] * b;
            if (raise > r.Raise) { r.Raise = raise; r.RaiseFrame = frame; }
            r.White += size * p.Contact[3] * b;
            ribs[i] = r;
        }
        return c;
    }

    /// <summary>A rib's raise now: its own, settling by ITS age (`hold` by drawn frame since it was raised; it only thins).</summary>
    public static float RaiseNow(in Rib r, int frame, float[] hold) => r.Raise * hold[Math.Clamp(frame - r.RaiseFrame, 0, hold.Length - 1)];

    /// <summary>The laid values at the watch's clock `at` (between two ribs: straight between them; outside: the end's):
    /// metres along, press (base + raise now), whiteness, raise now.</summary>
    public static (float S, float Press, float White, float Raise) At(List<Rib> ribs, double at, int frame, float[] hold)
    {
        if (ribs.Count == 0) return (0, 0, 0, 0);
        int lo = 0, hi = ribs.Count - 1;
        if (at <= ribs[0].At) hi = 0;
        else if (at >= ribs[hi].At) lo = hi;
        else
        {
            while (hi - lo > 1) { int m = (lo + hi) / 2; if (ribs[m].At <= at) lo = m; else hi = m; }
        }
        var a = ribs[lo]; var b = ribs[hi];
        float f = hi == lo ? 0 : (float)((at - a.At) / Math.Max(b.At - a.At, 1e-9));
        float ra = RaiseNow(a, frame, hold), rb = RaiseNow(b, frame, hold), rz = ra + (rb - ra) * f;
        return (a.S + (b.S - a.S) * f, a.Base + (b.Base - a.Base) * f + rz, a.White + (b.White - a.White) * f, rz);
    }

    /// <summary>(take 9) WHICH samples are the stroke. Samples lo..n-1; a segment `k` runs from sample k-1 to k:
    /// `cutting(k)` its tip fast and going the cut's way, `still(k)` its tip at rest, `sweep(k)` its radians round her
    /// the cut's way. Until the stroke is BORN (`from` under 0) the newest run of cutting segments is tried: once the
    /// cut has landed (`cut`) the walk back to it passes samples that move without cutting, never a still blade (a pose
    /// that snapped to rest before the swing is not this cut: it drew a bow tie), and the run is a stroke only when it
    /// has swept `birth` radians in all (the blade lifting into the swing does not sweep: it drew a squared chip).
    /// Once born its start is `from` for good: nothing laid is dropped, whatever the later samples do. Returns the
    /// run's first sample, its last cutting sample, and whether it draws.</summary>
    public static (int I0, int Hi, bool Any) Run(int lo, int n, int from, bool cut, bool sided, float birth, Func<int, bool> cutting, Func<int, bool> still, Func<int, double> sweep)
    {
        int j = n - 1;
        if (from >= 0)
        {
            while (j > from && !cutting(j)) j--;
            return (from, j, n - 1 > from);
        }
        if (cut) while (j > lo && !cutting(j) && !still(j)) j--;
        int hi = j;
        while (j > lo && cutting(j)) j--;
        if (hi <= j) return (j, j, false);
        double sum = 0;
        for (int k = j + 1; k <= hi; k++) sum += sweep(k);
        return !sided || sum >= birth ? (j, hi, true) : (j, j, false);
    }

    /// <summary>The cap's outline (the shader's grip_front is this, line for line): how far AHEAD of the blade's line the
    /// paint runs at `a` across the stroke (0 the tip's path, 1 the inner edge), in stroke widths. cap = [its length, the
    /// nose's place across, how far BEHIND the blade's line the inner edge starts, the outer corner's round-off (share of
    /// the length), the inner curve's power (under 1: concave, a fang), the further retreat of the inner edge at the
    /// shed's end]. Convex from the tip's path to the nose, concave from the nose to the inner edge; it crosses the
    /// blade's line at one place only, so the blade's line is never the stroke's edge.</summary>
    public static float CapFront(float a, float[] cap, float shed = 0)
    {
        float an = cap[1], back = cap[2] + cap[5] * shed;
        if (a <= an) { float x = 1 - Clamp01(a / Math.Max(an, 1e-4f)); return cap[0] * (1 - cap[3] * x * x); }
        return cap[0] - (cap[0] + back) * MathF.Pow(Clamp01((a - an) / Math.Max(1 - an, 1e-4f)), cap[4]);
    }

    /// <summary>The splay's tines for a contact of `struck` distinct bodies: none for an air cut, tines[0] for one body,
    /// tines[1] for a crowd of `crowd` or more.</summary>
    public static int Tines(int struck, float[] tines, float crowd)
        => struck <= 0 ? 0 : (int)MathF.Round(tines[0] + (tines[1] - tines[0]) * Clamp01((struck - 1) / Math.Max(crowd - 1, 1f)));

    /// <summary>The thrown streaks: `per` a distinct body struck, at least one for a hit, `most` at most, none for an air cut.</summary>
    public static int Streaks(int struck, float per, float most) => struck <= 0 ? 0 : (int)Math.Clamp(MathF.Ceiling(struck * per), 1, most);

    /// <summary>The spikes rooted on the pressed section's outer edge, 4 numbers each: [its root's place along the laid
    /// path (m), its root's half width (m along), its length out from the edge (m), its slant (m along per m out, the
    /// travel's way)]. First the tines (short, fat: the fanned bristles; len / root / slant = [least, most]), then the
    /// thrown streaks (long, thin: `throwRoot` half width; (take 8) the widths are PIXELS, a streak keeps its length while it is shed: the shader flies it; throwLen = [least, most] share of `far` m, the way to the
    /// cut's reach). Spread over the contact's reaches, no two on one place; `k` and `kt` are the tines' and the streaks'
    /// shares now (they are shed by drawn frame).</summary>
    public static float[] Spikes(in Stamp c, int tines, int streaks, in Press p, float[] len, float[] root, float[] slant,
        float throwRoot, float[] throwLen, float[] throwSlant, float far, float seed, float k, float kt, float throwSpan = 1f)
    {
        var o = new float[(tines + streaks) * 4];
        float lo = c.S - 0.7f * p.Contact[2], span = 0.7f * (p.Contact[1] + p.Contact[2]);
        // (take 8) the streaks are rooted along the whole pressed span and a little past it (they fan), unevenly
        // (take 10: behind the crossing and a little past it: a root is laid when the contact is stamped, so the flick
        // is there on the contact's frame; they lean more the travel's way the nearer the head: a fan, none crossing)
        float tlo = c.S - throwSpan * p.Contact[2], tspan = throwSpan * p.Contact[2] + 0.25f * p.Contact[1];
        for (int i = 0; i < tines + streaks; i++)
        {
            bool tine = i < tines;
            int j = tine ? i : i - tines, n = tine ? tines : streaks;
            float h0 = Hash(i + 1.3f, seed), h1 = Hash(i + 5.7f, seed), h2 = Hash(i + 9.1f, seed);
            o[i * 4] = tine ? lo + span * (j + 0.15f + 0.7f * h0) / n : tlo + tspan * (j + 0.05f + 0.9f * h0) / n;
            o[i * 4 + 1] = tine ? (root[0] + (root[1] - root[0]) * h1) * MathF.Sqrt(k) : throwRoot * kt;
            // (take 10: the flicks' lengths are SPREAD over the range, a golden step apart: long, short, middling; never four alike)
            float hl = Hash(77.7f, seed) + j * 0.618f; hl -= MathF.Floor(hl);
            o[i * 4 + 2] = tine ? (len[0] + (len[1] - len[0]) * h2) * k : far * (throwLen[0] + (throwLen[1] - throwLen[0]) * hl);
            o[i * 4 + 3] = tine ? slant[0] + (slant[1] - slant[0]) * h1 : throwSlant[0] + (throwSlant[1] - throwSlant[0]) * (j + 0.2f + 0.6f * h1) / n;
        }
        return o;
    }
}
