using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// One shadowed positional light at a time, in play (E1's rule: a shadowing omni
/// costs six cube faces of shadow draws, and the road's lamps were 1,160 of them).
/// A light that may cast a shadow (a lamp or fire lit at dusk or by night, the
/// Warden's blue light) is offered here; the arbiter picks the one that shadows:
/// the highest priority, then the nearest to her whose range reaches her, kept
/// until a challenger is 3 m nearer. The change is a cross-fade of ShadowOpacity
/// over 0.35 s, so nothing pops.
/// While Suspended (a cinematic) the arbiter stands aside: every offered light
/// shadows at full strength, as it did before the rule, so the judged shots are
/// unchanged. Enabled = false (a perf switch) turns every lamp shadow off.
/// </summary>
public static class ShadowLamp
{
    sealed class Entry
    {
        public OmniLight3D Light = null!;
        public int Priority;
        public bool Offered;
        public float Fade;
    }

    const float FadeTime = 0.35f, Hysteresis = 3f;
    static readonly List<Entry> entries = new();
    static Entry? cur;
    static bool enabled = true, suspended;

    /// <summary>False: no lamp casts a shadow at all (the perf switch "lampshadows").</summary>
    public static bool Enabled
    {
        get => enabled;
        set { if (enabled == value) return; enabled = value; Reset(); }
    }

    /// <summary>True while a cinematic plays: every offered light shadows at full strength.</summary>
    public static bool Suspended
    {
        get => suspended;
        set { if (suspended == value) return; suspended = value; Reset(); }
    }

    static bool Alive(Entry e) => GodotObject.IsInstanceValid(e.Light);

    /// <summary>Every light to its resting state for the mode just entered; Update re-chooses.</summary>
    static void Reset()
    {
        cur = null;
        entries.RemoveAll(e => !Alive(e));
        foreach (var e in entries)
        {
            bool on = enabled && suspended && e.Offered;
            e.Fade = on ? 1 : 0;
            Write(e.Light, on, 1);
        }
        entries.RemoveAll(e => !e.Offered);
    }

    static void Write(OmniLight3D l, bool shadow, float opacity)
    {
        if (l.ShadowEnabled != shadow) l.ShadowEnabled = shadow;
        if (!Mathf.IsEqualApprox(l.ShadowOpacity, opacity)) l.ShadowOpacity = opacity;
    }

    public static void Offer(OmniLight3D l, int priority)
    {
        Entry? e = entries.Find(x => x.Light == l);
        if (e == null) { e = new Entry { Light = l }; entries.Add(e); }
        e.Priority = priority;
        e.Offered = true;
        if (enabled && suspended) { e.Fade = 1; Write(l, true, 1); }
    }

    public static void Withdraw(OmniLight3D l)
    {
        var e = entries.Find(x => x.Light == l);
        if (e == null) return;
        e.Offered = false;
        if (cur == e) cur = null;
        // Suspended or not fading: gone at once. Otherwise it fades out in Update.
        if (suspended || !enabled || e.Fade <= 0) { entries.Remove(e); if (GodotObject.IsInstanceValid(l)) Write(l, false, 1); }
    }

    /// <summary>Once a frame in play: her place on the ground and the frame's time.</summary>
    public static void Update(Vector3 her, double delta)
    {
        if (!enabled || suspended) return;
        entries.RemoveAll(e => !Alive(e));
        if (cur != null && (!cur.Offered || !Alive(cur))) cur = null;

        Entry? best = null;
        float bestD = 0;
        bool bestReach = false;
        foreach (var e in entries)
        {
            if (!e.Offered || !e.Light.IsInsideTree()) continue;
            float d = e.Light.GlobalPosition.DistanceTo(her);
            bool reach = d <= e.Light.OmniRange;
            if (best == null || e.Priority > best.Priority ||
                (e.Priority == best.Priority && ((reach && !bestReach) || (reach == bestReach && d < bestD))))
            { best = e; bestD = d; bestReach = reach; }
        }
        if (best != null && best != cur)
        {
            if (cur == null) cur = best;
            else
            {
                float cd = cur.Light.GlobalPosition.DistanceTo(her);
                bool creach = cd <= cur.Light.OmniRange;
                if (best.Priority > cur.Priority || (best.Priority == cur.Priority && ((bestReach && !creach) || bestD + Hysteresis <= cd)))
                    cur = best;
            }
        }

        float step = (float)delta / FadeTime;
        for (int i = entries.Count - 1; i >= 0; i--)
        {
            var e = entries[i];
            float target = e == cur ? 1 : 0;
            e.Fade = Mathf.MoveToward(e.Fade, target, step);
            bool on = e.Fade > 0 || e == cur;
            Write(e.Light, on, e.Fade);
            if (!e.Offered && !on) { entries.RemoveAt(i); Write(e.Light, false, 1); }
            else if (!on) Write(e.Light, false, 1);
        }
    }
    /// <summary>(--lampdbg) Each offered light as a line: where, its range, its distance from the camera, whether its
    /// reach is in the camera's view, whether it shadows now.</summary>
    public static IEnumerable<string> Describe(Camera3D cam)
    {
        var planes = cam.GetFrustum();
        foreach (var e in entries)
        {
            if (!Alive(e) || !e.Light.IsInsideTree()) continue;
            var p = e.Light.GlobalPosition;
            bool seen = true;
            foreach (var pl in planes) if (pl.DistanceTo(p) > e.Light.OmniRange) { seen = false; break; }
            yield return $"{e.Light.GetPath()} at ({p.X:0.0},{p.Y:0.0},{p.Z:0.0}) range {e.Light.OmniRange:0.0} energy {e.Light.LightEnergy:0.00} cam {cam.GlobalPosition.DistanceTo(p):0.0} m view {(seen ? 1 : 0)} shadow {(e.Light.ShadowEnabled ? 1 : 0)}";
        }
    }
}
