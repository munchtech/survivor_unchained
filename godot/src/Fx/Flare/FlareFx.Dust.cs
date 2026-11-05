using System;
using Godot;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.View;

/// <summary>
/// The stop's dust (H7 r2, judge r1 fix 4, in the Draw web's place; data/content/flare_family.json "dust"): motes hanging
/// frozen in the air over the field while the world is held, told by their stillness (FlareBits' mote, its own batch so
/// this steers it). Cold moon silver, warm in her ember's reach; their light follows the grade in; the band's front blows
/// them out from where it runs, lit as it passes (FlareFx.Blow's BandReachesRt, BandDist). Derived from the judge's fix 4
/// ("frozen dust/motes and a deeper grade") and FLARE_LOOK §1.2's Hold ("still but alive: hair, cloth and motes keep
/// moving"); inherited: FlareBits (the mote kind) and flare_bits.gdshader.
/// </summary>
public partial class FlareFx
{
    readonly FlareBits dust = new(640, false);
    bool dustOn;

    void DustPress()
    {
        if (dust.GetParent() == null) AddChild(dust);
        dust.Clear();
        dustOn = true;
        var d = FlareFamily.Dust;
        var dl = d.Of(Night);
        var cam = GetViewport()?.GetCamera3D();
        var right = cam != null ? new Vector3(cam.GlobalBasis.X.X, 0, cam.GlobalBasis.X.Z).Normalized() : Vector3.Right;
        var fwd = new Vector3(-right.Z, 0, right.X);
        // (fwd: away from the eye on the ground, so "far" is up the screen)
        if (cam != null && fwd.Dot(new Vector3(-cam.GlobalBasis.Z.X, 0, -cam.GlobalBasis.Z.Z)) < 0) fwd = -fwd;
        var cold = new Color(d.Color).SrgbToLinear();
        var warm = new Color(d.WarmColor).SrgbToLinear();
        for (int i = 0; i < d.Count; i++)
        {
            float a = (R() * 2 - 1) * (float)d.Across, b = Mathf.Lerp(-(float)d.Near, (float)d.Far, R());
            var p = Her + right * a + fwd * b;
            p.Y = (float)HeightAt(p.X, p.Z) + Mathf.Lerp((float)d.Low, (float)d.High, R() * R() * 0.6f + R() * 0.4f);
            bool glint = R() < d.Glint;
            float size = Mathf.Lerp((float)d.Size[0], (float)d.Size[1], R() * R()) * (glint ? (float)d.GlintSize : 1);
            float near = Mathf.Exp(-Mathf.Pow(new Vector2(p.X - Her.X, p.Z - Her.Z).Length() / (float)d.WarmReach, 2));
            var c = cold * (float)dl.Light * (glint ? 2f : 0.6f + 0.8f * R());
            c = c.Lerp(warm * (float)dl.Warm, near);
            float drift = (float)d.Drift;
            dust.Spawn(new FlareBits.P
            {
                Kind = FlareBits.Kind.Mote, At = p, V = new Vector3(R() - 0.5f, (R() - 0.3f) * 0.5f, R() - 0.5f) * 2 * drift,
                Life = 60, Size = size, SizeEnd = size, Color = c with { A = 0 }, ColorEnd = c,
                OwnFade = true, Tag = -1, Tag2 = 1,
            });
        }
    }

    /// <summary>A real-time step: in with the grade, blown out by the band.</summary>
    void DustTick(double dt, float grade)
    {
        if (!dustOn) return;
        var d = FlareFamily.Dust;
        bool blown = BlowAtRt >= 0;
        float now = (float)rt;
        int left = 0;
        dust.Each(p =>
        {
            float a = grade, fl = 1;
            if (blown && p.Tag < 0)
            {
                double r = BandReachesRt(p.At.X, p.At.Z);
                if (r < 1e5) p.Tag = now + (float)r;
            }
            if (p.Tag >= 0 && now >= p.Tag)
            {
                float s = now - p.Tag;
                if (p.Tag2 > 0)
                {
                    // The front reaches it: pushed out from where the band runs, and up.
                    float e = 0.12f;
                    float gx = BandDist(p.At.X + e, p.At.Z) - BandDist(p.At.X - e, p.At.Z), gz = BandDist(p.At.X, p.At.Z + e) - BandDist(p.At.X, p.At.Z - e);
                    var g = new Vector3(gx, 0, gz);
                    g = g.LengthSquared() > 1e-6f ? g.Normalized() : new Vector3(R() - 0.5f, 0, R() - 0.5f).Normalized();
                    p.V += g * (float)d.Gust * (0.7f + 0.6f * R()) + Vector3.Up * (float)d.Up * R();
                    p.Drag = (float)d.Drag;
                    p.Tag2 = 0;
                }
                fl = 1 + ((float)d.Flash - 1) * Mathf.Max(0, 1 - s / (float)d.FlashTime);
                a *= Mathf.Max(0, 1 - s / (float)d.Gone);
                if (s >= d.Gone) p.Age = p.Life;
            }
            if (!blown && grade <= 0 && gradeNow <= 0 && t > 0.2) p.Age = p.Life;
            // (ColorEnd keeps its base light; Color is it now, lit by the passing front)
            p.Color = new Color(p.ColorEnd.R * fl, p.ColorEnd.G * fl, p.ColorEnd.B * fl, Mathf.Clamp(a, 0, 1));
            p.ColorEnd.A = p.Color.A;
            left++;
            return p;
        });
        dust.Step((float)dt);
        if (left == 0 && t > 0.2) dustOn = false;
    }

    void DustClear()
    {
        dustOn = false;
        dust.Clear();
    }
}
