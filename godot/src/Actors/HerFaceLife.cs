using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her face alive when nothing else is moving it: she blinks, every two to
/// six seconds, now and then twice (a lid falls fast and lifts slower), and
/// her eyes move as eyes do, in quick jumps from one place to look at to the
/// next (a saccade, longer the further it goes, Play/GazeShift), resting a moment or a few
/// between, a little apart round where she is looking, often as she blinks. A
/// cinematic's big look turns her head after her eyes (GazeCarry) and her lids ride
/// on her eyes.
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
    public float Wander = PlayWander;
    const float PlayWander = 0.13f, NoReach = 2f;
    /// <summary>Her lids held (1 shut, 0 open at rest) by a cinematic, or null: she blinks on her own.</summary>
    public float? Lids;
    /// <summary>Where her upper lids rest when open (0 wide to 1 shut): her face's own (Lore's faces, People.HerFaceKey).
    /// A blink and a held lid run from it to shut.</summary>
    public float Rest;

    /// <summary>Her eyes jump to where she is looking now (a cinematic's saccade), not at their next rest.</summary>
    public void Snap() => nextLook = t;

    /// <summary>Her eyes and head as she looks (Play/GazeShift): saccades by the main sequence, the head carrying a big
    /// look and the eyes rolling back as it comes, her lids riding on her eyes.</summary>
    readonly SurvivorUnchained.Play.GazeShift gaze = new();
    GazeCarry? carry;
    /// <summary>A cinematic's look waiting for its saccade: a glide's time, the head's share, a blink forced or stopped.</summary>
    double pendOver;
    float? pendHead;
    bool? pendBlink;
    /// <summary>The look the head was last sent for (a new Look sends it again).</summary>
    Vector2 planned;
    double glideEnd;

    /// <summary>A cinematic's gaze cue: where she looks (null: where she was), how far her eyes wander round it, how far
    /// they turn in her head before the head takes the rest (reach, radii), the head's share of the look (null: none, and
    /// no reach either: the head is carried only when a cue asks), a glide's time (over &gt; 0) instead of a jump, a blink forced or stopped. Snap:
    /// now (else at her next natural saccade); cut: set at once, the shot having just cut (no slide seen across it).</summary>
    public void Gaze(Vector2? look, float? wander, bool snap, double over, float? reach, float? head, bool? blink, bool cut)
    {
        if (look is Vector2 l) Look = l;
        if (wander is float w) Wander = w;
        // (inert unless asked, the owner 28 Oct: "keep our cutscenes face movements to a minimum": with no "head" the
        // head is never carried and the eyes aren't held to a reach, as before; "head" (and "reach") opt in)
        if (head is null) { head = 0; gaze.Reach = reach ?? NoReach; }
        else gaze.Reach = reach ?? SurvivorUnchained.Play.GazeShift.DefaultReach;
        pendOver = over; pendHead = head; pendBlink = blink;
        if (cut)
        {
            var h = SurvivorUnchained.Play.GazeShift.HeadFor(N(Look), gaze.Head, float.MaxValue, head, gaze.Reach, HeadOwned());
            gaze.Set(N(Look), h);
            planned = Look;
            pendOver = 0; pendHead = null; pendBlink = null;
            nextLook = t + rng.RandfRange(0.8f, 2.5f);
        }
        else if (snap) Snap();
    }

    /// <summary>The cinematic over: her look back ahead and her head let go, eased.</summary>
    public void Release()
    {
        Look = Vector2.Zero;
        Wander = PlayWander;   // (a cinematic's held wander, 0.02, left her eyes dead in play after it)
        gaze.Reach = SurvivorUnchained.Play.GazeShift.DefaultReach;
        gaze.HeadTo(t, System.Numerics.Vector2.Zero);
        pendOver = 0; pendHead = null; pendBlink = null;
        Snap();
    }

    static System.Numerics.Vector2 N(Vector2 v) => new(v.X, v.Y);

    /// <summary>A scripted head look (HeadTurn with a point and a want) owns her head: her eyes then turn alone.</summary>
    bool HeadOwned() => GetParent()?.GetNodeOrNull<HeadTurn>("HeadTurn") is { Want: > 0, Target: not null };

    readonly RandomNumberGenerator rng = new();
    readonly System.Collections.Generic.List<(MeshInstance3D Mesh, int L, int R)> lids = new();
    ShaderMaterial? eyes;
    double t, nextBlink, blinkAt = -1, nextLook;
    bool twice, second;

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
                else if (mi.FindBlendShapeByName("snarl") is int sn and >= 0) { mouth = mi; open = mi.FindBlendShapeByName("mouth_open"); snarl = sn; smile = mi.FindBlendShapeByName("smile"); }
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
    int open = -1, snarl = -1, smile = -1;
    static readonly bool NoFold = Args.Has("nofold");     // (--nofold: the corners cut as before, for a BEFORE shot)

    /// <summary>Her teeth lit only as far as her lips are parted (her head's mouth_open, or a snarl's lifted lip): with
    /// her lips closed her mouth is dark inside, so the teeth a corner of her lips shows read as shade, not a white
    /// speck (Sunborn at the Look, judge s1). Her side teeth stay in the cheeks' shade anyway (their vertex colour,
    /// tools/assets/heroine_teethshade.py). The teeth's material is remade with each look, so it is set each frame.</summary>
    /// <summary>The parameters' names made once (a string given where a name is wanted is a new tracked name each call,
    /// set each frame: they outlived the young collection).</summary>
    static class P
    {
        public static readonly StringName lit = "lit", shut = "shut", narrow = "narrow", upper_mask = "upper_mask", mask_w = "mask_w", drop_v = "drop_v", band = "band", paint = "paint", grow = "grow", lips_apart = "lips_apart", lips_narrow = "lips_narrow", fold = "fold", open_light = "open_light", head_inv = "head_inv";
    }

    /// <summary>Which of a skin's binds is on her head bone: found once per skin and skeleton (each lookup by bind name
    /// made a new tracked name per bind, each frame), as the loop it replaces found it (by name, or by bone without one).</summary>
    static int HeadBind(Skin skin, Skeleton3D sk, int head, ref (Skin?, Skeleton3D?, int, int) memo)
    {
        if (memo.Item1 == skin && memo.Item2 == sk && memo.Item3 == head) return memo.Item4;
        int found = -1;
        for (int i = 0; i < skin.GetBindCount(); i++)
        {
            string bn = skin.GetBindName(i);
            if ((bn != "" ? sk.FindBone(bn) : skin.GetBindBone(i)) == head) { found = i; break; }
        }
        memo = (skin, sk, head, found);
        return found;
    }
    (Skin?, Skeleton3D?, int, int) tongueBind, teethBind;

    void TeethLight()
    {
        if (teeth == null || mouth == null || teeth.Mesh == null) return;
        float w = Mathf.Max(open >= 0 ? mouth.GetBlendShapeValue(open) : 0, snarl >= 0 ? mouth.GetBlendShapeValue(snarl) : 0);
        float k = Mathf.SmoothStep(0.03f, 0.3f, w);
        for (int s = 0; s < teeth.Mesh.GetSurfaceCount(); s++)
            if (teeth.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "teeth")
            {
                m.SetShaderParameter(P.lit, k);
                // (the lamps cut wholly with her lips shut (her mouth's corner), 0.6 of the way once they part)
                m.SetShaderParameter(P.shut, 1 - 0.4f * Mathf.SmoothStep(0, 0.05f, w));
                // (her side teeth flat in her mouth's shade while her lips are parted only a little: the shader's narrow)
                m.SetShaderParameter(P.narrow, 1 - Mathf.SmoothStep(0.25f, 0.6f, w));
                foreach (var (n, v) in teethParams) m.SetShaderParameter(n, v);
            }
    }

    /// <summary>Her upper teeth seated lower while her lips are parted a little (mouth_open 0.25, the cinematics' most): at
    /// c04a A5 (85 mm at 1.25 m) her upper lip hid all but 0.5-1 mm of her incisors and her mouth read as a black slit
    /// (judge F1, face 30). Shut (no drop under 0.03) and from 0.6 (none) as before. The upper row is the vertices her
    /// mouth_open leaves where they are, found once per mesh into a mask by vertex index (the teeth shader's upper_mask);
    /// the drop is down in her head's own space, so it holds as her head turns. --teethdrop MM sets its most (1.5).</summary>
    void TeethDrop()
    {
        if (teeth?.Mesh is not ArrayMesh am || teeth.Skin is not { } skin || mouth == null || GetParent() is not Skeleton3D sk) return;
        if (am != maskMesh)
        {
            maskMesh = am; upperMask = null;
            int ti = teeth.FindBlendShapeByName("mouth_open");
            if (ti >= 0 && am.GetSurfaceCount() > 0)
            {
                var basis = am.SurfaceGetArrays(0)[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var sv = am.SurfaceGetBlendShapeArrays(0)[ti][(int)Mesh.ArrayType.Vertex].AsVector3Array();
                bool relative = am.BlendShapeMode == Mesh.BlendShapeMode.Relative;
                int n = basis.Length, h = (n + MaskW - 1) / MaskW, up = 0;
                var img = Image.CreateEmpty(MaskW, Mathf.Max(1, h), false, Image.Format.Rg8);
                // (green: the band's height, 0 at her incisors' edge (the upper row's lowest point at rest, Y up) to 1
                // BandSpan above it: the teeth shader's up_t, its ivory band shaded by it (judge F1 r2, face 30))
                var still = new bool[n];
                float edge = float.MaxValue;
                for (int i = 0; i < n && i < sv.Length; i++)
                    if ((relative ? sv[i] : sv[i] - basis[i]).Length() < 0.002f) { still[i] = true; edge = Mathf.Min(edge, basis[i].Y); }
                for (int i = 0; i < n; i++)
                    if (still[i]) { img.SetPixel(i % MaskW, i / MaskW, new Color(1, Mathf.Clamp((basis[i].Y - edge) / BandSpan, 0, 1), 0)); up++; }
                upperMask = ImageTexture.CreateFromImage(img);
                if (MouthCam || Args.Has("teethgrow")) GD.Print($"TEETHMASK {up}/{n} edge {edge:F4}");
            }
        }
        if (upperMask == null) return;
        float w = Mathf.Max(open >= 0 ? mouth.GetBlendShapeValue(open) : 0, snarl >= 0 ? mouth.GetBlendShapeValue(snarl) : 0);
        float d = DropMost * Mathf.SmoothStep(0.03f, 0.2f, w) * (1 - Mathf.SmoothStep(0.35f, 0.6f, w));
        int head = sk.FindBone("Head");
        Vector3 v = Vector3.Zero;
        if (head >= 0 && d > 0)
            if (HeadBind(skin, sk, head, ref teethBind) is var i and >= 0)
            {
                var toMesh = ((sk.GetBoneGlobalPose(head) * skin.GetBindPose(i)).AffineInverse() * teeth.Transform).AffineInverse();
                v = toMesh.Basis * new Vector3(0, -d, 0);
            }
        // (the band, and its gaps' shell behind it, on as far as the drop is: HerFaceLife's shell pass only then)
        float band = DropMost > 0 ? d / DropMost : 0;
        for (int s = 0; s < am.GetSurfaceCount(); s++)
            if (teeth.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "teeth")
            {
                m.SetShaderParameter(P.upper_mask, upperMask);
                m.SetShaderParameter(P.mask_w, MaskW);
                m.SetShaderParameter(P.drop_v, v);
                m.SetShaderParameter(P.band, band);
                if (band > 0.001f && v != Vector3.Zero && ShellGrow > 0)
                {
                    shellShader ??= GD.Load<Shader>("res://shaders/heroine_teeth_shell.gdshader");
                    if (m.NextPass is not ShaderMaterial sm || sm.Shader != shellShader)
                        m.NextPass = sm = new ShaderMaterial { Shader = shellShader, ResourceName = "teeth_shell" };
                    sm.SetShaderParameter(P.paint, m.GetShaderParameter(P.paint));
                    sm.SetShaderParameter(P.upper_mask, upperMask);
                    sm.SetShaderParameter(P.mask_w, MaskW);
                    sm.SetShaderParameter(P.drop_v, v);
                    sm.SetShaderParameter(P.grow, ShellGrow * v.Length() / d);
                    sm.SetShaderParameter(P.band, band);
                    foreach (var pn in new[] { "lit", "narrow", "closed", "side_floor" }) sm.SetShaderParameter(pn, m.GetShaderParameter(pn));
                    foreach (var (pn, pv) in teethParams) sm.SetShaderParameter(pn, pv);
                }
                else if (m.NextPass != null) m.NextPass = null;
                foreach (var (pn, pv) in teethParams) m.SetShaderParameter(pn, pv);
            }
    }

    const float BandSpan = 0.003f;
    static readonly float ShellGrow = Args.Num("teethgrow", 1.2f) / 1000f;
    Shader? shellShader;
    const int MaskW = 256;
    static readonly float DropMost = Args.Has("teethdrop") ? Args.Num("teethdrop", 1.5f) / 1000f : 0.0015f;
    ArrayMesh? maskMesh;
    ImageTexture? upperMask;

    /// <summary>Her mouth's inside lit by how far her lips part (0.25 is the cinematics' most): her tongue's light (its
    /// shader's open_light, 0.75 at 0.25 and under (face 30; face 29's half left her mouth a black slit), full by 0.6, where it was judged) and the shade baked where her lips
    /// meet eased up as they part (the skin's lips_apart). Before any --skin-set / --tongueparam, which win.</summary>
    void MouthShade()
    {
        if (mouth == null) return;
        float w = Mathf.Max(open >= 0 ? mouth.GetBlendShapeValue(open) : 0, snarl >= 0 ? mouth.GetBlendShapeValue(snarl) : 0);
        float apart = Mathf.SmoothStep(0.03f, 0.3f, w), tl = Mathf.Lerp(0.75f, 1f, Mathf.SmoothStep(0.25f, 0.6f, w));
        for (int s = 0; mouth.Mesh != null && s < mouth.Mesh.GetSurfaceCount(); s++)
            if (mouth.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader?.ResourcePath.EndsWith("heroine_skin.gdshader") == true)
            {
                m.SetShaderParameter(P.lips_apart, apart);
                m.SetShaderParameter(P.lips_narrow, 1 - Mathf.SmoothStep(0.3f, 0.6f, w));
                // (the corners' cut of the lamps behind her only as her smile folds them in: at rest the crease is
                // open to the light, and a lamp to her side and behind cut there drew a black smudge past each
                // corner, the lamp at c02 s8; face 30 cine)
                if (smile >= 0 && !NoFold) m.SetShaderParameter(P.fold, Mathf.SmoothStep(0.05f, 0.4f, mouth.GetBlendShapeValue(smile)));
            }
        for (int s = 0; tongue?.Mesh != null && s < tongue.Mesh.GetSurfaceCount(); s++)
            if (tongue.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "tongue")
                m.SetShaderParameter(P.open_light, tl);
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
        int i = HeadBind(skin, sk, head, ref tongueBind);
        if (i < 0) return;
        var inv = (sk.GetBoneGlobalPose(head) * skin.GetBindPose(i)).AffineInverse() * tongue.Transform;
        using Variant vInv = inv;
        for (int s = 0; tongue.Mesh != null && s < tongue.Mesh.GetSurfaceCount(); s++)
            if (tongue.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.ResourceName == "tongue")
                m.SetShaderParameter(P.head_inv, vInv);
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
        TeethDrop();
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
        // A saccade: a jump to somewhere near where she is looking (a new look exactly there, the head sent after
        // it; a big jump of her eyes in her head with a blink), or a cinematic's glide.
        bool owned = HeadOwned();
        if (t >= nextLook && (t >= glideEnd || Look != planned))
        {
            bool fresh = Look != planned;
            var to = fresh ? Look : Look + new Vector2(rng.RandfRange(-1f, 1f) * Wander, rng.RandfRange(-0.6f, 0.6f) * Wander);
            System.Numerics.Vector2? head = fresh
                ? SurvivorUnchained.Play.GazeShift.HeadFor(N(Look), gaze.Head, (N(Look) - gaze.Net).Length(), pendHead, gaze.Reach, owned)
                : null;
            float jump = gaze.Move(t, N(to), fresh ? pendOver : 0, head);
            if (SurvivorUnchained.Play.GazeShift.BlinkOn(jump, fresh ? pendBlink : null, Lids != null) && blinkAt < 0)
            {
                blinkAt = t;
                twice = false;
                second = false;
            }
            // (a glide runs out before her eyes wander from it, or a blink moves them)
            if (fresh) glideEnd = t + pendOver;
            nextLook = t + (fresh ? pendOver : 0) + (rng.Randf() < 0.3f ? rng.RandfRange(0.25f, 0.6f) : rng.RandfRange(0.8f, 3.0f));
            if (fresh) { planned = Look; pendOver = 0; pendHead = null; pendBlink = null; }
        }
        // (a scripted head look owns her head: her own carry let go, eased)
        if (owned) gaze.HeadTo(t, System.Numerics.Vector2.Zero);
        gaze.Step(t);
        var eye = new Vector2(gaze.Eye.X, gaze.Eye.Y);
        if (gaze.Head != System.Numerics.Vector2.Zero || carry != null) Carry(gaze.Head);
        // (from her lids' rest to shut, riding on her eyes' turn up and down; --rest-lid X tries another rest)
        float rest = Args.Has("rest-lid") ? Args.Num("rest-lid", 0) : Rest;
        shut = SurvivorUnchained.Play.GazeShift.Lid(rest, shut, eye.Y);
        foreach (var (mi, l, r) in lids)
        {
            if (l >= 0) mi.SetBlendShapeValue(l, shut);
            if (r >= 0) mi.SetBlendShapeValue(r, shut);
        }
        if (eyes != null)
        {
            eyes.SetShaderParameter(GazeA, eye);
            eyes.SetShaderParameter(GazeB, eye);
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

    /// <summary>The head's carry given to her skeleton's GazeCarry (made the first time there is any), kept after
    /// every other modifier on it, a scripted head look's included, so it lays its turn on top.</summary>
    void Carry(System.Numerics.Vector2 h)
    {
        if (GetParent() is not Skeleton3D sk) return;
        if (carry == null || !IsInstanceValid(carry))
        {
            if (h == System.Numerics.Vector2.Zero) { carry = null; return; }
            sk.AddChild(carry = new GazeCarry());
        }
        for (int i = carry.GetIndex() + 1; i < sk.GetChildCount(); i++)
            if (sk.GetChild(i) is SkeletonModifier3D) { sk.MoveChild(carry, -1); break; }
        carry.Yaw = h.X * SurvivorUnchained.Play.GazeShift.DegPerRadius;
        carry.Pitch = h.Y * SurvivorUnchained.Play.GazeShift.DegPerRadius;
    }

    // (Names made once, not a new one every frame for the collector.)
    static readonly StringName GazeA = "gaze_a", GazeB = "gaze_b";

    static float Ease(float x) => x * x * (3 - 2 * x);
}
