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
    /// <summary>Her lids held (1 shut, 0 open at rest) by a cinematic, or null: she blinks on her own.</summary>
    public float? Lids;
    /// <summary>Where her upper lids rest when open (0 wide to 1 shut): her face's own (Lore's faces, People.HerFaceKey).
    /// A blink and a held lid run from it to shut.</summary>
    public float Rest;

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
                if (mi.Name.ToString().Contains("Teeth")) teeth = mi;
                else if (mi.Name.ToString().Contains("Tongue")) tongue = mi;
                else if (mi.FindBlendShapeByName("snarl") is int sn and >= 0) { mouth = mi; open = mi.FindBlendShapeByName("mouth_open"); snarl = sn; }
                for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader?.ResourcePath.EndsWith("heroine_eye.gdshader") == true)
                        eyes = m;
            }
        // (printed once her pose is final, her pose's modifiers run: --mouth-cam)
        if (MouthCam) sk.SkeletonUpdated += PrintMouthCam;
        nextBlink = rng.RandfRange(1.0f, 4.0f);
        nextLook = rng.RandfRange(0.4f, 1.5f);
        // --open-eyes: a still of her face with her lids up and her eyes ahead
        // (a blink caught in a still read as a face with its eyes shut).
        if (Args.Has("open-eyes")) { Lids = 0; Wander = 0; }
        // --lids X: her lids held so far down (0 at rest, 1 shut), for pictures of a lid tried.
        if (Args.Has("lids")) Lids = Args.Num("lids", 0);
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
        // --teethparam name=value,...: her teeth shader's numbers set, each frame after TeethLight's (pictures of them tried).
        if (Args.Get("teethparam") is string tpar)
            foreach (var kv in tpar.Split(','))
                if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f))
                    teethParams.Add((k, f));
        // --tongueparam name=value,...: her tongue shader's numbers, each frame (pictures of them tried).
        if (Args.Get("tongueparam") is string gpar)
            foreach (var kv in gpar.Split(','))
                if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f))
                    tongueParams.Add((k, f));
    }

    readonly System.Collections.Generic.List<(string Name, Variant Value)> skinParams = new();
    readonly System.Collections.Generic.List<(string Name, float Value)> teethParams = new();
    readonly System.Collections.Generic.List<(string Name, float Value)> tongueParams = new();

    MeshInstance3D? teeth, mouth, tongue;
    int open = -1, snarl = -1;

    /// <summary>Her teeth lit only as far as her lips are parted (her head's mouth_open, or a snarl's lifted lip): with
    /// her lips closed her mouth is dark inside, so the teeth a corner of her lips shows read as shade, not a white
    /// speck (Sunborn at the Look, judge s1). Her side teeth stay in the cheeks' shade anyway (their vertex colour,
    /// tools/assets/heroine_teethshade.py). The teeth's material is remade with each look, so it is set each frame.</summary>
    void TeethLight()
    {
        if (teeth == null || mouth == null || teeth.Mesh == null) return;
        float w = Mathf.Max(open >= 0 ? mouth.GetBlendShapeValue(open) : 0, snarl >= 0 ? mouth.GetBlendShapeValue(snarl) : 0);
        float k = Mathf.SmoothStep(0.03f, 0.3f, w);
        for (int s = 0; s < teeth.Mesh.GetSurfaceCount(); s++)
            if (teeth.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "teeth")
            {
                m.SetShaderParameter("lit", k);
                // (the lamps cut wholly with her lips shut (her mouth's corner), 0.6 of the way once they part)
                m.SetShaderParameter("shut", 1 - 0.4f * Mathf.SmoothStep(0, 0.05f, w));
                // (her side teeth flat in her mouth's shade while her lips are parted only a little: the shader's narrow)
                m.SetShaderParameter("narrow", 1 - Mathf.SmoothStep(0.25f, 0.6f, w));
                foreach (var (n, v) in teethParams) m.SetShaderParameter(n, v);
            }
    }

    /// <summary>Her mouth's inside lit by how far her lips part (0.25 is the cinematics' most): her tongue's light (its
    /// shader's open_light, half at 0.25 and under, full by 0.6, where it was judged) and the shade baked where her lips
    /// meet eased up as they part (the skin's lips_apart). Before any --skin-set / --tongueparam, which win.</summary>
    void MouthShade()
    {
        if (mouth == null) return;
        float w = Mathf.Max(open >= 0 ? mouth.GetBlendShapeValue(open) : 0, snarl >= 0 ? mouth.GetBlendShapeValue(snarl) : 0);
        float apart = Mathf.SmoothStep(0.03f, 0.3f, w), tl = Mathf.Lerp(0.5f, 1f, Mathf.SmoothStep(0.25f, 0.6f, w));
        for (int s = 0; mouth.Mesh != null && s < mouth.Mesh.GetSurfaceCount(); s++)
            if (mouth.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader?.ResourcePath.EndsWith("heroine_skin.gdshader") == true)
                m.SetShaderParameter("lips_apart", apart);
        for (int s = 0; tongue?.Mesh != null && s < tongue.Mesh.GetSurfaceCount(); s++)
            if (tongue.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "tongue")
                m.SetShaderParameter("open_light", tl);
    }

    /// <summary>--mouth-cam: each frame, the camera in her head's own space (the glb's, as her head, teeth and tongue are
    /// all on her Head bone): "MOUTHCAM t T o X Y Z bx .. by .. bz .. fov F vp W H", so a tool casting rays at the glb
    /// sees her mouth as the picture does (the smile pass: what fills her mouth's opening, found offline).</summary>
    static readonly bool MouthCam = Args.Has("mouth-cam");

    void PrintMouthCam()
    {
        if (teeth?.Skin is not { } skin || GetParent() is not Skeleton3D sk || GetViewport().GetCamera3D() is not { } cam) return;
        int head = sk.FindBone("Head");
        for (int i = 0; i < skin.GetBindCount(); i++)
        {
            string bn = skin.GetBindName(i);
            int b = bn != "" ? sk.FindBone(bn) : skin.GetBindBone(i);
            if (b != head) continue;
            var m = sk.GlobalTransform * sk.GetBoneGlobalPose(head) * skin.GetBindPose(i);
            var c = m.AffineInverse() * cam.GlobalTransform;
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            string V(Vector3 v) => string.Format(ci, "{0:0.000000} {1:0.000000} {2:0.000000}", v.X, v.Y, v.Z);
            var vp = GetViewport().GetVisibleRect().Size;
            GD.Print(string.Format(ci, "MOUTHCAM t {0:0.000} o {1} bx {2} by {3} bz {4} fov {5:0.000} keep {6} vp {7} {8} mi {9}",
                t, V(c.Origin), V(c.Basis.Column0), V(c.Basis.Column1), V(c.Basis.Column2), cam.Fov, (int)cam.KeepAspect,
                vp.X, vp.Y, V(teeth.Transform.Origin)) + MouthKeys());
            return;
        }
    }

    /// <summary>The head's blend weights in use (" w name=v ..."), so an offline ray cast poses her mouth as drawn.</summary>
    string MouthKeys()
    {
        if (mouth?.Mesh is not ArrayMesh am) return "";
        var sb = new System.Text.StringBuilder(" w");
        for (int i = 0; i < am.GetBlendShapeCount(); i++)
            if (mouth.GetBlendShapeValue(i) is float v && Mathf.Abs(v) > 0.0005f)
                sb.Append(string.Format(System.Globalization.CultureInfo.InvariantCulture, " {0}={1:0.0000}", am.GetBlendShapeName(i), v));
        return sb.ToString();
    }

    void SkinParams()
    {
        if (GetParent() is not Skeleton3D sk) return;
        foreach (var c in sk.GetChildren())
            if (c is MeshInstance3D mi)
                for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader?.ResourcePath.EndsWith("heroine_skin.gdshader") == true)
                        foreach (var (k, v) in skinParams) m.SetShaderParameter(k, v);
    }

    /// <summary>Her tongue's points in her head's own space (the glb's, as made), for its shader's shade by how far each
    /// point is off her mouth's middle (heroine_tongue.gdshader's head_inv): its side falls into the shade beside her back
    /// teeth wherever her head turns. Set each frame, as her head moves and her material is remade with each look.</summary>
    void TongueFrame()
    {
        if (tongue?.Skin is not { } skin || GetParent() is not Skeleton3D sk) return;
        int head = sk.FindBone("Head");
        if (head < 0) return;
        for (int i = 0; i < skin.GetBindCount(); i++)
        {
            string bn = skin.GetBindName(i);
            if ((bn != "" ? sk.FindBone(bn) : skin.GetBindBone(i)) != head) continue;
            var inv = (sk.GetBoneGlobalPose(head) * skin.GetBindPose(i)).AffineInverse() * tongue.Transform;
            for (int s = 0; tongue.Mesh != null && s < tongue.Mesh.GetSurfaceCount(); s++)
                if (tongue.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "tongue")
                    m.SetShaderParameter("head_inv", inv);
            return;
        }
    }

    void TongueParams()
    {
        if (GetParent() is not Skeleton3D sk) return;
        foreach (var c in sk.GetChildren())
            if (c is MeshInstance3D mi)
                for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "tongue")
                        foreach (var (k, v) in tongueParams) m.SetShaderParameter(k, v);
    }

    Color?[]? cycle;

    public override void _Process(double delta)
    {
        t += delta;
        MouthShade();
        if (skinParams.Count > 0) SkinParams();
        if (tongueParams.Count > 0) TongueParams();
        TeethLight();
        TongueFrame();
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
        // (from her lids' rest to shut; --rest-lid X tries another rest)
        float rest = Args.Has("rest-lid") ? Args.Num("rest-lid", 0) : Rest;
        shut = rest + (1 - rest) * shut;
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
            eyes.SetShaderParameter(GazeA, gaze);
            eyes.SetShaderParameter(GazeB, gaze);
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

    // (Names made once, not a new one every frame for the collector.)
    static readonly StringName GazeA = "gaze_a", GazeB = "gaze_b";

    static float Ease(float x) => x * x * (3 - 2 * x);
}
