using System.Collections.Generic;
using System.Globalization;
using Godot;

namespace SurvivorUnchained;

/// <summary>
/// Screenshots for judging the slice without a screen (tools/godot/run.sh):
///
///   -- --shot NAME [--seconds S] [--every T --count N]
///
/// runs S seconds of game time (the engine is started with --fixed-fps, so a
/// slow software renderer still steps time evenly), saves
/// godot/.shots/NAME.png, and quits; with --every and --count, a run of frames
/// NAME_00.png... T seconds apart. Other slice options are read by name
/// (Args.Get).
/// </summary>
public static class Args
{
    static Dictionary<string, string>? parsed;

    /// <summary>Whether the developer's switches are read at all: in the
    /// editor and debug builds and the measuring build (export preset "Windows (perf)", feature "perf"), never in the player's release build. Every switch
    /// (--quick, --zone, --body, --gold, --shot, --perf...) comes through
    /// here, so a player's copy cannot be talked into a place, a body or a
    /// view the game does not offer (the legal brief, issue 3).</summary>
    public static bool Dev => OS.IsDebugBuild() || OS.HasFeature("perf");

    static Dictionary<string, string> All()
    {
        if (parsed != null) return parsed;
        parsed = new();
        if (!Dev) return parsed;
        var a = OS.GetCmdlineUserArgs();
        for (int i = 0; i < a.Length; i++)
        {
            if (!a[i].StartsWith("--")) continue;
            var key = a[i][2..];
            var val = i + 1 < a.Length && !a[i + 1].StartsWith("--") ? a[++i] : "1";
            parsed[key] = val;
        }
        return parsed;
    }

    public static string? Get(string key) => All().TryGetValue(key, out var v) ? v : null;
    public static float Num(string key, float fallback) =>
        float.TryParse(Get(key), NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : fallback;
    public static bool Has(string key) => All().ContainsKey(key);
}

public partial class Shots : Node
{
    string name = "";
    float seconds, every, until;
    int count, taken;
    // --hud-seq: the instrument's states stepped through, one picture each (HudPin.cs).
    int hudNext, hudPhase;
    double hudAt;
    double time;
    static Shots? live;
    /// <summary>The pictures' own clock (seconds since they began), for what changes between pictures.</summary>
    public static double Clock => live?.time ?? 0;
    /// <summary>Frames the game asks for (--on boss): what, and when.</summary>
    readonly List<(double At, string Tag)> wanted = new();
    readonly Dictionary<string, int> tagged = new();

    /// <summary>--on boss: a frame a moment after each boss move is marked, its Break,
    /// its stagger and its arrival (a telegraph lasts a second; a frame every second
    /// misses most of them). The run ends at --until seconds.</summary>
    public static bool On(string what) => live != null && Args.Get("on") is string on && System.Array.IndexOf(on.Split(','), what) >= 0;

    public static void Want(string tag, double inSeconds)
    {
        if (live == null) return;
        live.wanted.Add((live.time + inSeconds, tag));
    }

    /// <summary>Frames the game asks for this many drawn frames on (a hit-stop holds the clock, not the frames).</summary>
    readonly List<(long At, string Tag)> wantedFrames = new();
    public static void WantFrames(string tag, int frames)
    {
        if (live == null) return;
        live.wantedFrames.Add(((long)Engine.GetFramesDrawn() + frames, tag));
    }

    /// <summary>Whether a frame of that tag is still to be taken.</summary>
    public static bool Pending(string tag) => live != null && (live.wanted.Exists(w => w.Tag == tag) || live.wantedFrames.Exists(w => w.Tag == tag));

    /// <summary>The run ends this many seconds on (sooner than --until: a whole night ends at its result).</summary>
    public static void EndIn(double seconds)
    {
        if (live == null) return;
        live.until = (float)(live.time + seconds);
        live.count = System.Math.Min(live.count, live.taken);
    }

    /// <summary>The camera as each of the last frames was drawn (the frame read back is an earlier one than this
    /// frame's camera: a mark's measuring band missed it by pixels while the camera moved, and a mark's first frames
    /// read as bare ground).</summary>
    readonly string?[] drawnCams = new string?[4];
    void Drawn()
    {
        if (GetViewport()?.GetCamera3D() is not { } c) return;
        System.Array.Copy(drawnCams, 0, drawnCams, 1, drawnCams.Length - 1);
        drawnCams[0] = $"{c.GlobalTransform} fov {c.Fov}";
    }

    /// <summary>"camera": the one the frame read back was drawn with (SHOT_CAMLAG drawn frames back, 1 by default);
    /// "camera_now" and "camera_lag2" beside it for checking.</summary>
    void CamLines()
    {
        if (GetViewport().GetCamera3D() is not { } wc) return;
        int lag = int.TryParse(System.Environment.GetEnvironmentVariable("SHOT_CAMLAG"), out var lg) ? lg : 1;
        var now = $"{wc.GlobalTransform} fov {wc.Fov}";
        GD.Print($"camera {(lag <= 0 ? now : drawnCams[lag - 1] ?? now)}");
        GD.Print($"camera_now {now}");
        GD.Print($"camera_lag2 {drawnCams[1] ?? now}");
    }

    public override void _ExitTree()
    {
        if (live == this) RenderingServer.FramePostDraw -= Drawn;
    }

    public override void _Ready()
    {
        name = Args.Get("shot") ?? "";
        if (name == "") { SetProcess(false); return; }
        live = this;
        RenderingServer.FramePostDraw += Drawn;
        seconds = Args.Num("seconds", 3);
        every = Args.Num("every", 0);
        until = Args.Num("until", Args.Has("on") ? 120 : 0);
        count = (int)Args.Num("count", every > 0 ? 8 : Args.Has("on") || Ui.HudPin.Seq.Length > 0 ? 0 : 1);
        ProcessMode = ProcessModeEnum.Always;
        // --unshaded: paint as it is, without light (a seam in a texture told
        // from one in the lighting).
        if (Args.Has("unshaded")) GetViewport().DebugDraw = Viewport.DebugDrawEnum.Unshaded;
        // --debugdraw Lighting (or NormalBuffer, ...): any of Godot's own views.
        if (Args.Get("debugdraw") is string dd && System.Enum.TryParse<Viewport.DebugDrawEnum>(dd, true, out var mode)) GetViewport().DebugDraw = mode;
    }

    public override void _Process(double delta)
    {
        time += delta;
        if (Ui.HudPin.Seq.Length > 0 && hudNext < Ui.HudPin.Seq.Length)
        {
            if (hudPhase == 0 && time >= seconds + hudNext * Args.Num("hud-seq-every", 1.5f)) { Ui.HudPin.Use(hudNext); hudAt = time; hudPhase = 1; }
            else if (hudPhase == 1 && time >= hudAt + 0.35)
            {
                var hd = ProjectSettings.GlobalizePath("res://.shots");
                DirAccess.MakeDirRecursiveAbsolute(hd);
                var hf = $"{hd}/{name}_hud{hudNext}.png";
                GetViewport().GetTexture().GetImage().SavePng(hf);
                GD.Print($"saved {hf} at {time:0.00}s (hud state {hudNext}: {Ui.HudPin.Seq[hudNext]}){Ui.HerLight.Note()}");
                hudNext++; hudPhase = 0;
                if (hudNext >= Ui.HudPin.Seq.Length && until <= 0 && taken >= count) { GetTree().Quit(); return; }
            }
        }
        // --geom-normals (dent d3, a developer's test): 1.5 s before the picture her skin's stored normals are swapped
        // for ones recomputed from her bind geometry (area-weighted, split copies shared), to tell normal data from shape.
        if (Args.Has("geom-normals") && !geomDone && time >= Args.Num("seconds", 3) - 1.5) { geomDone = true; GeomNormals(); }
        // --no-taa, --mipbias B: the picture without TAA, or its textures
        // sampled sharper (B < 0), to tell what softens fine detail (each
        // frame: the graphics settings are applied after this wakes).
        if (Args.Has("no-taa")) GetViewport().UseTaa = false;
        if (Args.Get("mipbias") is string mb) GetViewport().TextureMipmapBias = float.Parse(mb, System.Globalization.CultureInfo.InvariantCulture);
        // --tonemap linear|reinhardt|filmic|aces|agx, --grade off: the picture through
        // another tone curve, or without the colour grade, to tell what each does to a
        // face's darks (her brows, lashes, the line of her lips).
        if (Args.Get("tonemap") is string tm || Args.Get("grade") == "off")
            foreach (var we in GetTree().Root.FindChildren("*", "WorldEnvironment", true, false))
                if (((WorldEnvironment)we).Environment is { } env)
                {
                    if (Args.Get("tonemap") is string t && System.Enum.TryParse<Godot.Environment.ToneMapper>(t, true, out var mode)) env.TonemapMode = mode;
                    if (Args.Get("grade") == "off") env.AdjustmentEnabled = false;
                }
        // --no-labels: the world's text off (names, marks, speech, hit numbers), for frames that are painted over.
        if (Args.Has("no-labels") && Engine.GetFramesDrawn() % 30 == 0)
            foreach (var n in GetTree().Root.FindChildren("*", "Node3D", true, false))
                if (n is SurvivorUnchained.View.Voices or SurvivorUnchained.View.Hits) ((Node3D)n).Visible = false;
        for (int i = wanted.Count - 1; i >= 0; i--)
        {
            if (time < wanted[i].At) continue;
            var tag = Safe(wanted[i].Tag);
            wanted.RemoveAt(i);
            int k = tagged[tag] = tagged.GetValueOrDefault(tag) + 1;
            var d = ProjectSettings.GlobalizePath("res://.shots");
            DirAccess.MakeDirRecursiveAbsolute(d);
            var f = $"{d}/{name}_{tag}_{k}.png";
            GetViewport().GetTexture().GetImage().SavePng(f);
            GD.Print($"saved {f} at {time:0.00}s frame {Engine.GetFramesDrawn()}{HerAt()}{(Ui.HerLight.Live is { } hl ? $" life {hl.LifeNow:0.000}" : "")}");
            // (the camera, so a mark's ground can be found in the frame and measured)
            CamLines();
        }
        for (int i = wantedFrames.Count - 1; i >= 0; i--)
        {
            if ((long)Engine.GetFramesDrawn() < wantedFrames[i].At) continue;
            var tag = Safe(wantedFrames[i].Tag);
            wantedFrames.RemoveAt(i);
            int k = tagged[tag] = tagged.GetValueOrDefault(tag) + 1;
            var d = ProjectSettings.GlobalizePath("res://.shots");
            DirAccess.MakeDirRecursiveAbsolute(d);
            var f = $"{d}/{name}_{tag}_{k}.png";
            GetViewport().GetTexture().GetImage().SavePng(f);
            GD.Print($"saved {f} at {time:0.00}s frame {Engine.GetFramesDrawn()}{HerAt()}");
            CamLines();
        }
        if (until > 0 && time >= until) { GetTree().Quit(); return; }
        if (taken >= count) return;
        var due = seconds + taken * every;
        if (time < due) return;
        var dir = ProjectSettings.GlobalizePath("res://.shots");
        DirAccess.MakeDirRecursiveAbsolute(dir);
        var file = every > 0 ? $"{dir}/{name}_{taken:00}.png" : $"{dir}/{name}.png";
        GetViewport().GetTexture().GetImage().SavePng(file);
        GD.Print($"saved {file} at {time:0.00}s{HerAt()}{Ui.HerLight.Note()}");
        // (E9b4: the camera, so a frame's pixel can be traced back to the world)
        CamLines();
        if (Args.Has("mark-bones")) PrintMarks();
        if (Args.Get("dump-her") is string dumpTo) DumpHer(dumpTo);
        // --navcheck: the open screen's focus routes walked as the picture is taken.
        if (Args.Has("navcheck")) Audit(GetTree().Root);
        taken++;
        if (taken >= count && until <= 0) GetTree().Quit();
    }

    /// <summary>Where her chest is on the screen this frame (the game sets it while pictures are taken), for crops of her.</summary>
    public static Vector2? Her;
    static string HerAt() => Her is { } h ? $" her {h.X:0} {h.Y:0}" : "";

    /// <summary>--dump-her PATH (dent d3, a developer's measure): her skin surfaces skinned on the CPU at the picture's
    /// frame (shipped weights and pose; blend shapes listed, not applied), per surface PATH_sK.bin: int nv, int ni, then per
    /// vertex 29 floats (world xyz, skinned stored normal xyz, screen xy, depth, uv, bind xyz, bind normal xyz, the blended skin matrix's basis columns and origin), then the
    /// indices; and every playing AnimationPlayer's clip and time.</summary>
    bool geomDone;
    void GeomNormals()
    {
        var stack = new Stack<Node>(); stack.Push(GetTree().Root);
        while (stack.Count > 0)
        {
            var n = stack.Pop();
            foreach (var c in n.GetChildren()) stack.Push(c);
            if (n is not MeshInstance3D mi || mi.Name != "Heroine" || mi.Mesh is not ArrayMesh mesh) continue;
            int ns = mesh.GetSurfaceCount();
            var arrs = new Godot.Collections.Array[ns];
            var acc = new Dictionary<(long, long, long), Vector3>();
            static (long, long, long) K(Vector3 p) => ((long)System.Math.Round(p.X * 1e5), (long)System.Math.Round(p.Y * 1e5), (long)System.Math.Round(p.Z * 1e5));
            for (int s = 0; s < ns; s++)
            {
                arrs[s] = mesh.SurfaceGetArrays(s);
                var v = arrs[s][(int)Mesh.ArrayType.Vertex].AsVector3Array(); var ix = arrs[s][(int)Mesh.ArrayType.Index].AsInt32Array();
                for (int t = 0; t < ix.Length; t += 3)
                {
                    var fn = -(v[ix[t + 1]] - v[ix[t]]).Cross(v[ix[t + 2]] - v[ix[t]]);
                    for (int j = 0; j < 3; j++) { var k = K(v[ix[t + j]]); acc[k] = acc.GetValueOrDefault(k) + fn; }
                }
            }
            var nm = new ArrayMesh { BlendShapeMode = mesh.BlendShapeMode };
            for (int b = 0; b < mesh.GetBlendShapeCount(); b++) nm.AddBlendShape(mesh.GetBlendShapeName(b));
            var over = new Material?[ns];
            for (int s = 0; s < ns; s++) over[s] = mi.GetSurfaceOverrideMaterial(s);
            double dev = 0; int cnt = 0;
            for (int s = 0; s < ns; s++)
            {
                var v = arrs[s][(int)Mesh.ArrayType.Vertex].AsVector3Array(); var old = arrs[s][(int)Mesh.ArrayType.Normal].AsVector3Array();
                var nn = new Vector3[v.Length];
                for (int i = 0; i < v.Length; i++) { nn[i] = acc[K(v[i])].Normalized(); dev += Mathf.RadToDeg(old[i].Normalized().AngleTo(nn[i])); cnt++; }
                arrs[s][(int)Mesh.ArrayType.Normal] = nn;
                long fmt = (long)mesh.SurfaceGetFormat(s);
                GD.Print($"GEOMNORMALS surf {s} format 0x{fmt:X}");
                nm.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrs[s], mesh.SurfaceGetBlendShapeArrays(s), null, (Mesh.ArrayFormat)(fmt & (0x1FFE000L | (1L << 27))));
                nm.SurfaceSetMaterial(s, mesh.SurfaceGetMaterial(s));
            }
            mi.Mesh = nm;
            for (int s = 0; s < ns; s++) mi.SetSurfaceOverrideMaterial(s, over[s]);
            GD.Print($"GEOMNORMALS {mi.GetPath()} surfaces {ns} mean change {dev / System.Math.Max(1, cnt):0.00} deg");
        }
    }

    void DumpHer(string path)
    {
        var cam = GetViewport().GetCamera3D();
        int k = 0;
        var stack = new Stack<Node>(); stack.Push(GetTree().Root);
        while (stack.Count > 0)
        {
            var n = stack.Pop();
            foreach (var c in n.GetChildren()) stack.Push(c);
            if (n is AnimationPlayer ap0 && ap0.GetPath().ToString().Contains("Survivor")) GD.Print($"HERANIM {ap0.GetPath()} cur {ap0.CurrentAnimation} assigned {ap0.AssignedAnimation} pos {(ap0.IsPlaying() ? ap0.CurrentAnimationPosition : -1):0.000}");
            if (n is AnimationTree at && at.GetPath().ToString().Contains("Survivor")) GD.Print($"HERTREE {at.GetPath()} active {at.Active}");
            if (n is AnimationPlayer ap && ap.IsPlaying()) GD.Print($"ANIM {ap.GetPath()} {ap.CurrentAnimation} {ap.CurrentAnimationPosition:0.000}");
            if (n is not MeshInstance3D mi || mi.Mesh is not ArrayMesh mesh || mi.Skin is not Skin skin) continue;
            var skel = mi.GetNodeOrNull<Skeleton3D>(mi.Skeleton);
            if (skel == null) continue;
            var mats = new Transform3D[skin.GetBindCount()];
            for (int b = 0; b < mats.Length; b++)
            {
                int bone = skin.GetBindBone(b);
                if (bone < 0) bone = skel.FindBone(skin.GetBindName(b));
                mats[b] = bone < 0 ? Transform3D.Identity : skel.GlobalTransform * skel.GetBoneGlobalPose(bone) * skin.GetBindPose(b);
            }
            for (int s = 0; s < mesh.GetSurfaceCount(); s++)
            {
                if (mi.GetActiveMaterial(s) is not ShaderMaterial sm || sm.Shader?.ResourcePath?.Contains("heroine_skin") != true) continue;
                var arr = mesh.SurfaceGetArrays(s);
                var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var nr = arr[(int)Mesh.ArrayType.Normal].AsVector3Array();
                var uv = arr[(int)Mesh.ArrayType.TexUV].AsVector2Array();
                var bo = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                var we = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                var ix = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
                int per = bo.Length / System.Math.Max(1, v.Length);
                string bs = "";
                for (int q = 0; q < mesh.GetBlendShapeCount(); q++) bs += $" {mesh.GetBlendShapeName(q)}={mi.GetBlendShapeValue(q):0.###}";
                GD.Print($"DUMP {mi.GetPath()} surf {s} mat {sm.ResourceName} nv {v.Length} ni {ix.Length} per {per} binds {mats.Length} shapes:{bs}");
                using var w = new System.IO.BinaryWriter(System.IO.File.Create($"{path}_s{k++}.bin"));
                w.Write(v.Length); w.Write(ix.Length);
                for (int i = 0; i < v.Length; i++)
                {

                    Vector3 P = Vector3.Zero, N = Vector3.Zero; var B = new Basis(Vector3.Zero, Vector3.Zero, Vector3.Zero); var O = Vector3.Zero;
                    for (int j = 0; j < per; j++)
                    {
                        float wt = we[i * per + j]; if (wt <= 0) continue;
                        var m = mats[bo[i * per + j]];
                        P += wt * (m * v[i]); N += wt * (m.Basis * nr[i]); B.X += wt * m.Basis.X; B.Y += wt * m.Basis.Y; B.Z += wt * m.Basis.Z; O += wt * m.Origin;
                    }
                    N = N.Normalized();
                    var sc = cam.UnprojectPosition(P); float d = cam.GlobalPosition.DistanceTo(P);
                    foreach (var f in new[] { P.X, P.Y, P.Z, N.X, N.Y, N.Z, sc.X, sc.Y, d, uv[i].X, uv[i].Y, v[i].X, v[i].Y, v[i].Z, nr[i].X, nr[i].Y, nr[i].Z, B.X.X, B.X.Y, B.X.Z, B.Y.X, B.Y.Y, B.Y.Z, B.Z.X, B.Z.Y, B.Z.Z, O.X, O.Y, O.Z }) w.Write(f);
                }
                foreach (var i in ix) w.Write(i);
            }
        }
    }

    /// <summary>--mark-bones: "MARK x y" per marked point, in viewport pixels. Today the top of her sternum (the
    /// midpoint of her two clavicle bones' origins), so a sheet's ticks come from her skeleton, not from the picture's lightness.</summary>
    void PrintMarks()
    {
        var cam = GetViewport().GetCamera3D();
        foreach (var n in GetTree().Root.FindChildren("HerPose", "SkeletonModifier3D", true, false))
        {
            if (((SkeletonModifier3D)n).GetSkeleton() is not { } sk) continue;
            int l = sk.FindBone("clavicle_l"), r = sk.FindBone("clavicle_r");
            if (cam == null || l < 0 || r < 0) continue;
            var at = sk.GlobalTransform * ((sk.GetBoneGlobalPose(l).Origin + sk.GetBoneGlobalPose(r).Origin) * 0.5f);
            // --mark-offset U,F (metres): up and forward of her skeleton, so the point can be moved to the notch.
            if (Args.Get("mark-offset") is string mo && mo.Split(',') is { Length: 2 } uf)
            {
                var bs = sk.GlobalTransform.Basis.Orthonormalized();
                at += bs * (Vector3.Up * float.Parse(uf[0], CultureInfo.InvariantCulture) + Vector3.Back * float.Parse(uf[1], CultureInfo.InvariantCulture));
            }
            if (cam.IsPositionBehind(at)) continue;
            var p = cam.UnprojectPosition(at);
            GD.Print($"MARK {p.X:0.0} {p.Y:0.0}");
            return;
        }
    }

    static string Safe(string s)
    {
        var o = new System.Text.StringBuilder();
        foreach (var c in s.ToLowerInvariant()) o.Append(char.IsLetterOrDigit(c) ? c : '_');
        return o.ToString().Trim('_');
    }

    static void Audit(Node n)
    {
        if (n is Ui.Overlay o && o.IsVisibleInTree())
            foreach (var line in o.NavAudit()) GD.Print($"nav {o.Kind}: {line}");
        foreach (var c in n.GetChildren()) Audit(c);
    }
}
