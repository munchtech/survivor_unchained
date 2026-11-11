using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The Ford-Warden's cleave drawn as his blade's own swing (B1 judge r6: "one fan from his hands out to the reach, leading
/// where the blade is, no rings"). While the strike is live his held blade's guard and tip are sampled on each skeleton
/// update (the frame's final pose: no frame of lag), the frames between rounded (the blade's direction slerped about the
/// hand), and the sheet the blade sweeps is drawn between them: hot at the blade, cooling back along the sweep, the tip's
/// path its one bright line; past the steel the sheet carries on, thinner, toward the cleave's reach on the ground and
/// fades to nothing there (no rim line). After the blow it drains tail first into the blade.
/// </summary>
public partial class WardenSwing : MeshInstance3D
{
    struct At { public Vector3 Hilt, Tip, Out; public double Born; }

    readonly List<At> ring = new();
    readonly ImmediateMesh im = new();
    double clock;
    At? last;
    /// <summary>Whether the strike is live (new samples are taken), set by the view each frame.</summary>
    public bool Live;
    /// <summary>The cleave's reach from his centre (Prologue's cone, 6.4 m) the sheet runs on to past the tip; 0: the
    /// blade's own trail only. (r7, the lead's look: run on to the reach it laid a 6.4 m sheet behind him on the raise and
    /// washed half the frame at the landing; the telegraph's cone already shows the reach, so the trail is the steel's.)</summary>
    public float Reach = 0f;
    /// <summary>Seconds a sample lives behind the blade, and the steps each frame is rounded into.</summary>
    const double Life = 0.14;
    const int Sub = 5;
    /// <summary>The steel's share of the sheet's width (guard 0, tip TipV, reach 1).</summary>
    const float TipV = 0.62f;

    const string Code = """
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;
uniform vec3 core : source_color = vec3(0.86, 0.95, 1.0);
uniform vec3 cold : source_color = vec3(0.28, 0.62, 1.0);
uniform float energy = 1.7;
uniform float tipv = 0.62;
float h(float x) { return fract(sin(x * 127.1) * 43758.5); }
float n1(float x) { float i = floor(x), f = fract(x); return mix(h(i), h(i + 1.0), f * f * (3.0 - 2.0 * f)); }
void fragment() {
    float age = UV.x, v = UV.y;
    float lead = exp(-age * 4.0);
    float fade = 1.0 - smoothstep(0.45, 1.0, age);
    float steel = smoothstep(0.0, 0.3, v / tipv);
    float air = v <= tipv ? 1.0 : pow(1.0 - (v - tipv) / (1.0 - tipv), 1.8) * (0.25 + 0.3 * lead);
    float rim = exp(-pow((v - tipv) / mix(0.035, 0.08, age), 2.0));
    float streak = 0.62 + 0.38 * n1(v * 34.0 + age * 2.0);
    float a = (steel * air * (0.15 + 0.6 * lead) * streak * 0.55 + rim * (0.35 + 0.9 * lead)) * fade;
    ALBEDO = mix(cold, core, clamp(lead * 0.7 + rim * 0.6, 0.0, 1.0)) * energy;
    ALPHA = clamp(a, 0.0, 1.0);
}
""";

    public WardenSwing()
    {
        Name = "Swing";
        TopLevel = true;
        Mesh = im;
        CastShadow = ShadowCastingSetting.Off;
        MaterialOverride = new ShaderMaterial { Shader = new Shader { Code = Code } };
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
    }

    /// <summary>The frame's clock (the view's own dt): old samples go, and the sheet is drawn.</summary>
    public void Step(double dt)
    {
        GlobalTransform = Transform3D.Identity;
        clock += dt;
        if (!Live) last = null;
        Draw();
    }

    /// <summary>His skeleton has the frame's pose: the blade (its holder: grip at the origin, +Y to the tip, meta "tip")
    /// sampled if the strike is live, the frame rounded in from the last sample, and the sheet drawn again.</summary>
    public void Sample(Node3D? holder, MeshInstance3D? blade, Vector3 centre)
    {
        if (!Live || holder == null || blade == null || !IsInstanceValid(holder) || !IsInstanceValid(blade) || !blade.IsInsideTree()) return;
        // (r8, the lead's look: the holder's "tip" meta under his scale drew a sheet twice the blade.) The steel itself:
        // its mesh's long axis in the world, the end nearer the grip the hilt (the trace's blade lo/hi/far are of it).
        var bb = blade.GetAabb(); var bx = blade.GlobalTransform;
        int ax = bb.Size.X >= bb.Size.Y && bb.Size.X >= bb.Size.Z ? 0 : bb.Size.Y >= bb.Size.Z ? 1 : 2;
        var mid = bb.GetCenter(); var half = Vector3.Zero; half[ax] = bb.Size[ax] / 2;
        Vector3 e0 = bx * (mid - half), e1 = bx * (mid + half), grip = holder.GlobalPosition;
        if (e0.DistanceSquaredTo(grip) > e1.DistanceSquaredTo(grip)) (e0, e1) = (e1, e0);
        Vector3 h1 = e0.Lerp(e1, 0.55f), t1 = e1; // (r9: his chop is overhead; swept from the guard it laid a half-disc toward the camera: the outer steel only)
        if (last is { } p && clock - p.Born > 1e-4)
            for (int k = 1; k <= Sub; k++)
            {
                float s = k / (float)Sub;
                var hs = p.Hilt.Lerp(h1, s);
                var d = (p.Tip - p.Hilt).Slerp(t1 - h1, s);
                ring.Add(Make(hs, hs + d, centre, p.Born + (clock - p.Born) * s));
            }
        else if (last is { } q) ring[^1] = Make(h1, t1, centre, q.Born);
        else ring.Add(Make(h1, t1, centre, clock));
        last = ring[^1];
        Draw();
    }

    /// <summary>A sample: past the tip the sheet runs on along the tip's way out from his centre to the reach, as much as
    /// the blade lies flat (an upright blade carries no reach into the air), and down toward the ground.</summary>
    At Make(Vector3 hilt, Vector3 tip, Vector3 centre, double born)
    {
        var dir = tip - hilt; var flat = new Vector3(tip.X - centre.X, 0, tip.Z - centre.Z);
        float r = flat.Length(), lie = dir.Length() > 1e-3f ? 1 - Mathf.Abs(dir.Normalized().Y) : 0;
        float w = Reach > 0 ? Mathf.SmoothStep(0.35f, 0.8f, lie) * Mathf.Clamp((Reach - r) / Reach * 3, 0, 1) : 0;
        var outer = Reach > r && r > 0.2f ? tip + flat / r * (Reach - r) * w : tip;
        outer.Y = Mathf.Lerp(tip.Y, centre.Y + 0.3f, 0.6f * w);
        return new At { Hilt = hilt, Tip = tip, Out = outer, Born = born };
    }

    void Draw()
    {
        while (ring.Count > 0 && clock - ring[0].Born > Life) ring.RemoveAt(0);
        im.ClearSurfaces();
        if (ring.Count < 2) return;
        im.SurfaceBegin(Mesh.PrimitiveType.Triangles);
        for (int i = 1; i < ring.Count; i++)
        {
            At a = ring[i - 1], b = ring[i];
            float ua = (float)((clock - a.Born) / Life), ub = (float)((clock - b.Born) / Life);
            Quad(a.Hilt, a.Tip, b.Hilt, b.Tip, ua, ub, 0, TipV);
            Quad(a.Tip, a.Out, b.Tip, b.Out, ua, ub, TipV, 1);
        }
        im.SurfaceEnd();
    }

    void Quad(Vector3 a0, Vector3 a1, Vector3 b0, Vector3 b1, float ua, float ub, float v0, float v1)
    {
        void P(Vector3 p, float u, float v) { im.SurfaceSetUV(new Vector2(Mathf.Clamp(u, 0, 1), v)); im.SurfaceAddVertex(p); }
        P(a0, ua, v0); P(a1, ua, v1); P(b1, ub, v1);
        P(a0, ua, v0); P(b1, ub, v1); P(b0, ub, v0);
    }
}
