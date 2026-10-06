using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her face alive when nothing else is moving it: she blinks, every two to
/// six seconds, now and then twice (a lid falls fast and lifts slower), and
/// her eyes move as eyes do, in quick jumps from one place to look at to the
/// next (a saccade, a twentieth of a second), resting a moment or a few
/// between, a little apart round where she is looking, often as she blinks.
/// Her lids are her head's blink shapes (on her lashes too); her eyes are
/// slid by their shader's gaze (shaders/heroine_eye.gdshader). Added under
/// her skeleton.
/// </summary>
public partial class HerFaceLife : Node
{
    /// <summary>Where she is looking, in her irises' radii (+x her left, +y
    /// down): a cinematic or a conversation can turn her eyes.</summary>
    public Vector2 Look;
    /// <summary>How far her eyes wander round it.</summary>
    public float Wander = 0.13f;
    /// <summary>Her lids held (1 shut, 0 open) by a cinematic, or null: she blinks on her own.</summary>
    public float? Lids;

    /// <summary>Her eyes jump to where she is looking now (a cinematic's saccade), not at their next rest.</summary>
    public void Snap() => nextLook = t;

    readonly RandomNumberGenerator rng = new();
    readonly System.Collections.Generic.List<(MeshInstance3D Mesh, int L, int R)> lids = new();
    ShaderMaterial? eyes;
    double t, nextBlink, blinkAt = -1, nextLook;
    bool twice, second;
    Vector2 from, to, gaze;
    double lookAt = -1;

    public HerFaceLife() { Name = "HerFaceLife"; }

    public override void _Ready()
    {
        rng.Randomize();
        if (GetParent() is not Skeleton3D sk) return;
        foreach (var c in sk.GetChildren())
            if (c is MeshInstance3D mi)
            {
                int l = mi.FindBlendShapeByName("blink_l"), r = mi.FindBlendShapeByName("blink_r");
                if (l >= 0 || r >= 0) lids.Add((mi, l, r));
                for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader?.ResourcePath.EndsWith("heroine_eye.gdshader") == true)
                        eyes = m;
            }
        nextBlink = rng.RandfRange(1.0f, 4.0f);
        nextLook = rng.RandfRange(0.4f, 1.5f);
        // --open-eyes: a still of her face with her lids up and her eyes ahead
        // (a blink caught in a still read as a face with its eyes shut).
        if (Args.Has("open-eyes")) { Lids = 0; Wander = 0; }
        // --eyecycle paint,#rrggbb,...: her irises dyed each in turn, one a picture
        // (--seconds, then every --every): the eye shader's colours measured as
        // the game shows them, against the portraits' (paint: as painted).
        if (Args.Get("eyecycle") is string cyc)
            cycle = System.Array.ConvertAll(cyc.Split(','), s => s == "paint" ? (Color?)null : new Color(s));
        // --eyeparam name=value,...: her eye shader's numbers set (pictures of them tried).
        if (eyes != null && Args.Get("eyeparam") is string ep)
            foreach (var kv in ep.Split(','))
                if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f))
                    eyes.SetShaderParameter(k, f);
        // --skinparam name=value,...: her skin shader's numbers (or #rrggbb
        // colours) set on her head and body, each frame (her skin is remade
        // as a look is chosen), for pictures of them tried.
        if (Args.Get("skinparam") is string spar)
            foreach (var kv in spar.Split(','))
                if (kv.Split('=') is [var k, var v])
                    skinParams.Add((k, v.StartsWith('#') ? new Color(v)
                        : float.Parse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture)));
    }

    readonly System.Collections.Generic.List<(string Name, Variant Value)> skinParams = new();

    void SkinParams()
    {
        if (GetParent() is not Skeleton3D sk) return;
        foreach (var c in sk.GetChildren())
            if (c is MeshInstance3D mi)
                for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader?.ResourcePath.EndsWith("heroine_skin.gdshader") == true)
                        foreach (var (k, v) in skinParams) m.SetShaderParameter(k, v);
    }

    Color?[]? cycle;

    public override void _Process(double delta)
    {
        t += delta;
        if (skinParams.Count > 0) SkinParams();
        // A blink: the lid down in 70 ms, held a moment, up in 150 ms.
        if (t >= nextBlink && blinkAt < 0)
        {
            blinkAt = t;
            twice = !second && rng.Randf() < 0.15f;
            second = false;
            if (rng.Randf() < 0.5f) nextLook = t + 0.05;          // (eyes often move as she blinks)
        }
        float shut = 0;
        if (Lids is float held) { shut = held; blinkAt = -1; nextBlink = t + rng.RandfRange(1.5f, 3.5f); }
        else if (blinkAt >= 0)
        {
            double b = t - blinkAt;
            shut = b < 0.07 ? Ease((float)(b / 0.07)) : b < 0.1 ? 1 : b < 0.25 ? 1 - Ease((float)((b - 0.1) / 0.15)) : 0;
            if (b >= 0.25)
            {
                blinkAt = -1;
                second = twice;
                nextBlink = t + (twice ? 0.08 : rng.RandfRange(2.0f, 6.0f));
            }
        }
        foreach (var (mi, l, r) in lids)
        {
            if (l >= 0) mi.SetBlendShapeValue(l, shut);
            if (r >= 0) mi.SetBlendShapeValue(r, shut);
        }
        // A saccade: a quick jump to somewhere near where she is looking.
        if (t >= nextLook)
        {
            from = gaze;
            to = Look + new Vector2(rng.RandfRange(-1f, 1f) * Wander, rng.RandfRange(-0.6f, 0.6f) * Wander);
            lookAt = t;
            nextLook = t + (rng.Randf() < 0.3f ? rng.RandfRange(0.25f, 0.6f) : rng.RandfRange(0.8f, 3.0f));
        }
        if (lookAt >= 0)
        {
            float k = Mathf.Clamp((float)((t - lookAt) / 0.05), 0, 1);
            gaze = from.Lerp(to, Ease(k));
            if (k >= 1) lookAt = -1;
        }
        if (eyes != null)
        {
            eyes.SetShaderParameter("gaze_a", gaze);
            eyes.SetShaderParameter("gaze_b", gaze);
            if (cycle != null)
            {
                float every = Args.Num("every", 1), first = Args.Num("seconds", 3);
                int i = Mathf.Clamp((int)Mathf.Floor((float)(Shots.Clock - first + every / 2) / every), 0, cycle.Length - 1);
                eyes.SetShaderParameter("recolour", cycle[i] == null ? 0f : 1f);
                // (a dye as itself: her painted iris's own correction, the tint, left off)
                if (cycle[i] is Color c) { eyes.SetShaderParameter("iris_colour", c); eyes.SetShaderParameter("ring_colour", c); eyes.SetShaderParameter("tint", Colors.White); }
            }
        }
    }

    static float Ease(float x) => x * x * (3 - 2 * x);
}
