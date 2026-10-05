using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Vertex animation textures: how a horde costs one draw per kind (the web
/// game's render/vat.ts).
///
/// A kind of creature is sampled once: every clip it needs (walk, strike,
/// fall, rise from the grave) is played through its real skeleton, and the
/// posed position and normal of every vertex at every frame is written into
/// two textures. The crowd is then a MultiMesh of the rest geometry whose
/// vertex shader (shaders/vat.gdshader) reads its pose from the textures,
/// each instance at its own frame, so five hundred creatures animate as
/// independently as five for the price of one mesh.
///
/// People (the Risen, the Kerchiefs) are baked from a real PersonView: its
/// skeleton played by its AnimationPlayer, the weapons in its hands carried
/// rigidly with their bones. Beasts are baked the same way from their own
/// models (Beasts.cs), with what their clips lack composed over their poses.
/// </summary>
public sealed class VatAsset
{
    public sealed record Clip(int Start, int Frames, double Fps, double Duration, bool Loop);

    public required string Key;
    public required ArrayMesh Mesh;
    public required int Width, Rows;
    public required Dictionary<string, Clip> Clips;
    public float Height;
    /// <summary>How fast its walk carries it at its natural rate, in metres a
    /// second at its own size; 0 when not known (the crowd then plays the
    /// walk at its natural rate at the kind's full speed).</summary>
    public float Pace;
    /// <summary>How fast its charge (its own gallop, the role "charge")
    /// carries it at its natural rate, as Pace; 0 when it has none.</summary>
    public float ChargePace;

    public Clip For(string role) =>
        Clips.TryGetValue(role, out var c) ? c : Clips.TryGetValue("move", out var m) ? m : Clips["idle"];

    public double Duration(string role) => Clips.TryGetValue(role, out var c) ? c.Duration : 1;

    /// <summary>How many ways down it has ("die", "die2", "die3"...).</summary>
    public int Deaths
    {
        get { int n = 1; while (Clips.ContainsKey($"die{n + 1}")) n++; return n; }
    }

    /// <summary>Its k-th way down (any k: taken round the ones it has), so a
    /// field of the dead can be varied: on the back, on the face, on the side.</summary>
    public string Death(int k)
    {
        int i = ((k % Deaths) + Deaths) % Deaths;
        return i == 0 ? "die" : $"die{i + 1}";
    }

    /// <summary>The two frames (absolute rows of frames) and the blend between them, `t` seconds into a role.</summary>
    public (int F0, int F1, float K) Frame(string role, double t)
    {
        var c = For(role);
        double f = t * c.Fps;
        if (c.Loop) { f %= c.Frames - 1; if (f < 0) f += c.Frames - 1; }
        else f = Math.Clamp(f, 0, c.Frames - 1);
        int f0 = (int)Math.Floor(f);
        int f1 = Math.Min(f0 + 1, c.Frames - 1);
        return (c.Start + f0, c.Start + f1, (float)(f - f0));
    }
}

public static class Vat
{
    const int MaxFrames = 48;
    static readonly Dictionary<string, VatAsset> cache = new();
    static Shader? shader, cutShader, normalShader;

    /// <summary>The roles every crowd kind plays, and which loop.</summary>
    static bool Loops(string role) => role is "move" or "idle" or "burrow" or "cast" or "charge";

    /// <summary>A kind of creature, baked (once a session). `host` lends the
    /// scene tree to a person's animation player while it is sampled.</summary>
    public static VatAsset Of(Visuals.Spec spec, Node host)
    {
        if (cache.TryGetValue(spec.Key, out var hit)) return hit;
        ulong t0 = Time.GetTicksMsec();
        // Wolves of every kind share one bake: their tints and sizes are the crowd's.
        var beast = Beasts.Of(spec.Key);
        var key = beast?.Key ?? spec.Key;
        if (cache.TryGetValue(key, out var shared)) { cache[spec.Key] = shared; return shared; }
        var kept = Load(key);
        var asset = kept != null ? Build(kept) : beast != null ? BakeBeast(beast, host) : BakePerson(spec, host);
        if (beast == null) asset.Pace = Pace(spec);
        else { asset.Pace = (float)beast.Pace; asset.ChargePace = (float)beast.ChargePace; }
        cache[key] = asset;
        cache[spec.Key] = asset;
        if (Args.Has("log"))
        {
            int frames = 0; foreach (var c in asset.Clips.Values) frames += c.Frames;
            GD.Print($"{(kept != null ? "read" : "baked")} {spec.Key}: {asset.Width * asset.Rows} vertices x {frames} frames, {asset.Mesh.GetSurfaceCount()} surfaces, {Time.GetTicksMsec() - t0} ms");
        }
        return asset;
    }

    /* --------------------------------------------------------------- data -- */

    /// <summary>One surface of the bake: its rest arrays, where its vertices
    /// start among all of them, and what it is painted with.</summary>
    sealed class Surf
    {
        public required Vector2[] Uv;
        public Color[]? Color;
        public required int[] Index;
        public required int Count;
        public int Offset;
        public Vector3[] V = Array.Empty<Vector3>(), N = Array.Empty<Vector3>();
        public Texture2D? Tex;
        public Color Albedo = Colors.White;
        public float Roughness = 0.8f, Metallic;
        public Color Glow = Colors.Black;
        /// <summary>The cloth's dye (the person shader's), if dyed: colour (linear), bands (lo, hi, soft), brightness.</summary>
        public bool Dyed;
        public Vector3 DyeColor, DyeH, DyeS, DyeV;
        public float DyeLum = 1;
        /// <summary>Fur and hair cards: cut where the texture's alpha falls below this (-1: solid).</summary>
        public float Cut = -1;
        /// <summary>A normal map (tangent space), drawn with vat_normal.gdshader.</summary>
        public Texture2D? Normal;
    }

    /// <summary>Poses every vertex of every surface (concatenated) for a role at t.</summary>
    delegate void Sampler(string role, double t, Vector3[] pos, Vector3[] nor);

    /* ------------------------------------------------------------- people -- */

    sealed class Skinned
    {
        public Surf Surf = null!;
        public required Vector3[] V, N;
        public required Vector2[] Uv;
        public required int[] Index;
        public Material? Mat;
        public int[]? Bones;
        public float[]? Weights;
        public int Stride;
        public int[]? BindBone;
        public Transform3D[]? BindPose;
        public Transform3D[]? BindNow;
        /// <summary>A rigid part (a weapon): the bone it rides, and where it sits from it.</summary>
        public int Rigid = -1;
        public Transform3D Rel;
        /// <summary>The simplified versions of its triangles the importer made (index lists, finest first).</summary>
        public List<int[]> Lods = new();
    }

    /// <summary>Vertices a crowd person may have in all. (The web game held
    /// them to 4,000 for WebGL; a desktop can give a figure more shape.)</summary>
    const int Budget = 6000;

    /// <summary>What a rigged thing plays for a crowd role: a stretch of a
    /// clip (or one moment of it, held), and moves composed over it (a lunge,
    /// a fall) where the model has no clip for the role. Seam: a looped
    /// stretch of a longer clip, its end eased into its start. Rate: how fast
    /// the clip is played (Length is how long the role lasts).</summary>
    public sealed record Role(string Name, string Clip, double From, double Length, Func<double, Moves>? Over = null, bool Hold = false, bool Seam = false, double Rate = 1, bool? Loop = null)
    {
        /// <summary>Whether it loops: its own say, or the crowd's rule for its name.</summary>
        public bool Loops => Loop ?? Vat.Loops(Name);
    }

    /// <summary>Moves over a pose, in the model's own space (+Z forward, +Y up,
    /// +X its left): bones turned about their own origins (Euler XYZ, radians)
    /// and moved, and the whole body turned and moved.</summary>
    public sealed class Moves
    {
        public readonly Dictionary<string, (Vector3 Turn, Vector3 Move)> Bones = new();
        public Vector3 Turn, Move;
        public Moves Bone(string name, double x, double y = 0, double z = 0) { var o = Bones.GetValueOrDefault(name); Bones[name] = (new Vector3((float)x, (float)y, (float)z), o.Move); return this; }
        public Moves Shift(string name, double x, double y, double z) { var o = Bones.GetValueOrDefault(name); Bones[name] = (o.Turn, new Vector3((float)x, (float)y, (float)z)); return this; }
    }

    static Godot.Basis Euler(Vector3 r) => new Godot.Basis(Vector3.Right, r.X) * new Godot.Basis(Vector3.Up, r.Y) * new Godot.Basis(new Vector3(0, 0, 1), r.Z);

    static VatAsset BakePerson(Visuals.Spec spec, Node host)
    {
        var pv = new PersonView(spec.Person!, spec.Arms, 0.8 * spec.Scale);
        host.AddChild(pv);
        var person = pv.Person;
        var roles = new List<Role>();
        var c = spec.Clips;
        // A kit body falls one of three ways (FolkClips.Deaths), so the dead do not all lie alike.
        bool pistol = spec.Arms?.Right is string right && Arms.All.TryGetValue(right, out var held) && held.Pistol;
        var deaths = person.Kit ? FolkClips.Deaths(person.Woman, !person.Folk, pistol) : null;
        var plays = new List<(string, string?)> { ("move", c.Move), ("idle", c.Idle), ("attack", c.Attack), ("windup", c.Windup), ("rise", c.Rise), ("hit", c.Hit), ("cast", c.Cast),
            ("slam", c.Slam), ("aim", c.Aim), ("shot", c.Shot) };
        if (deaths != null) for (int i = 0; i < deaths.Length; i++) plays.Add((i == 0 ? "die" : $"die{i + 1}", deaths[i]));
        else plays.Add(("die", c.Die));
        foreach (var (role, clip) in plays)
        {
            if (clip == null) continue;
            var name = clip.StartsWith(FolkClips.Prefix) ? clip : Clip(person, clip);
            roles.Add(new Role(role, name, 0, person.Anim.HasAnimation(name) ? person.Anim.GetAnimation(name).Length : 1));
        }
        var asset = BakeRig(spec.Key, pv, person.Skeleton, person.Anim, person.Meshes, roles, 15, Budget, null);
        host.RemoveChild(pv);
        pv.QueueFree();
        return asset;
    }

    /// <summary>A crowd person's clip: the crowd's own where it has one (FolkClips.Crowd), the library's otherwise.</summary>
    static string Clip(People.Person person, string clip) =>
        person.Kit && FolkClips.Crowd(person.Woman, !person.Folk, clip) is string own ? own : People.Resolve(clip);

    static bool Armed(World.Held? arms) => arms?.Right != null || arms?.Left != null || arms?.Forearm != null;

    /// <summary>How fast a kind's walk carries it at its natural rate, in
    /// metres a second at its own size (0: not known, the library's clips).</summary>
    static float Pace(Visuals.Spec spec)
    {
        if (spec.Person == null || FolkClips.Crowd(spec.Person.Sex == Rpg.Sex.Female, Armed(spec.Arms), spec.Clips.Move) is not string move) return 0;
        // (The body stands 1.04 times its skeleton, at the kind's scale.)
        return FolkClips.Speed(move) * 1.04f * (float)spec.Scale;
    }

    /// <summary>A modelled beast (Beasts.cs): its glTF, normalised to face +Z
    /// with its feet at 0 and its body over the origin, at its height.</summary>
    static VatAsset BakeBeast(Beasts.Def def, Node host)
    {
        var view = new Node3D { Name = $"bake:{def.Key}" };
        var model = GD.Load<PackedScene>(def.Path).Instantiate<Node3D>();
        view.AddChild(model);
        host.AddChild(view);
        var skel = FindSkeleton(model)!;
        var anim = (AnimationPlayer)model.FindChild("AnimationPlayer", true, false)!;
        var meshes = new List<MeshInstance3D>();
        foreach (var mi in Meshes(model)) if (mi.Skin != null || mi.Skeleton != "") meshes.Add(mi);
        // Where it stands: from its bones in its first idle pose.
        var idle = def.Roles.Find(r => r.Name == "idle")!;
        anim.Play(idle.Clip, 0);
        anim.Seek(idle.From, true);
        var toView = view.GlobalTransform.AffineInverse() * skel.GlobalTransform;
        Vector3 At(string bone) => toView * skel.GetBoneGlobalPose(skel.FindBone(bone)).Origin;
        Vector3 pelvis = At(def.Pelvis), head = At(def.Head);
        float low = float.MaxValue, high = float.MinValue;
        for (int b = 0; b < skel.GetBoneCount(); b++) { var y = (toView * skel.GetBoneGlobalPose(b).Origin).Y; low = Math.Min(low, y); high = Math.Max(high, y); }
        // Its front: across its hips if it walks upright (a hunched one's head
        // leans anywhere), from pelvis to head if it goes on four legs.
        var fwd = def.Legs is var (left, right) ? (At(left) - At(right)).Cross(Vector3.Up) : head - pelvis;
        fwd = new Vector3(fwd.X, 0, fwd.Z).Normalized();
        float yaw = Mathf.Atan2(fwd.X, fwd.Z);
        float scale = def.Height / Math.Max(1e-3f, high - low);
        // Centred over its feet if upright, along its body if not.
        var mid = def.Legs != null ? pelvis : (pelvis + head) / 2;
        var norm = new Transform3D(Godot.Basis.FromScale(Vector3.One * scale), Vector3.Zero)
            * new Transform3D(new Godot.Basis(Vector3.Up, -yaw), Vector3.Zero)
            * new Transform3D(Godot.Basis.Identity, new Vector3(-mid.X, -low, -mid.Z));
        // What it wears, put on as it stands: on bone attachments, which the
        // bake carries rigidly with their bones.
        var toModel = norm * toView;
        foreach (var prop in def.Props ?? new())
        {
            int bone = skel.FindBone(prop.Bone);
            var from = toModel * skel.GetBoneGlobalPose(bone);
            var tip = toModel * skel.GetBoneGlobalPose(skel.FindBone(prop.Tip)).Origin;
            var up = (tip - from.Origin).Normalized();
            var front = (new Vector3(0, 0, 1) - up * up.Z).Normalized();
            var frame = new Godot.Basis(up.Cross(front), up, front);
            var att = new BoneAttachment3D { BoneName = skel.GetBoneName(bone) };
            skel.AddChild(att);
            var worn = prop.Make();
            worn.Transform = from.AffineInverse() * new Transform3D(frame, tip + frame * prop.Offset);
            att.AddChild(worn);
        }
        // A role of no length plays its whole clip.
        var roles = def.Roles.ConvertAll(r => r.Length > 0 || !anim.HasAnimation(r.Clip) ? r : r with { Length = anim.GetAnimation(r.Clip).Length });
        var asset = BakeRig(def.Key, view, skel, anim, meshes, roles, 20, def.Budget, norm, def.Root);
        host.RemoveChild(view);
        view.QueueFree();
        return asset;
    }

    static Skeleton3D? FindSkeleton(Node n)
    {
        foreach (var c in n.GetChildren()) { if (c is Skeleton3D s) return s; if (FindSkeleton(c) is { } d) return d; }
        return null;
    }

    /// <summary>Anything with a skeleton, an animation player and skinned
    /// meshes (and weapons on bone attachments), baked role by role. `norm`
    /// takes the view's space to the model's own (+Z forward), or none.
    /// `walker`: the bone its clips carry off across the ground (root
    /// motion), which the crowd does not want (it moves them itself).</summary>
    static VatAsset BakeRig(string key, Node3D view, Skeleton3D skel, AnimationPlayer anim, List<MeshInstance3D> meshes, List<Role> roles, double fps, int budget, Transform3D? norm, string? walker = null)
    {
        ulong t0 = Time.GetTicksMsec();
        List<Skinned> parts = new();
        foreach (var mi in meshes)
        {
            var skin = mi.Skin ?? skel.CreateSkinFromRestTransforms();
            int binds = skin.GetBindCount();
            var bindBone = new int[binds];
            var bindPose = new Transform3D[binds];
            for (int i = 0; i < binds; i++)
            {
                string name = skin.GetBindName(i);
                bindBone[i] = name != "" ? skel.FindBone(name) : skin.GetBindBone(i);
                bindPose[i] = skin.GetBindPose(i);
            }
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var p = Part(mi, s);
                p.BindBone = bindBone;
                p.BindPose = bindPose;
                p.BindNow = new Transform3D[binds];
                parts.Add(p);
            }
        }
        // What is held: rigid with the bone of the hand (or forearm) it hangs from.
        foreach (var node in skel.GetChildren())
        {
            if (node is not BoneAttachment3D att) continue;
            int bone = skel.FindBone(att.BoneName);
            foreach (var mi in Meshes(att))
            {
                // Where it sits from the bone: the chain of its parents below the attachment.
                var rel = Transform3D.Identity;
                for (Node? n = mi; n != null && n != att; n = n.GetParent()) if (n is Node3D n3) rel = n3.Transform * rel;
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                {
                    var p = Part(mi, s);
                    p.Rigid = bone;
                    p.Rel = rel;
                    parts.Add(p);
                }
            }
        }
        ulong tParts = Time.GetTicksMsec();
        Slim(parts, budget);
        int total = 0;
        foreach (var p in parts)
        {
            p.Surf = Surface(p.Uv, p.Index, p.V.Length, p.Mat);
            p.Surf.Offset = total;
            total += p.V.Length;
        }

        var toModel = (norm ?? Transform3D.Identity) * view.GlobalTransform.AffineInverse() * skel.GlobalTransform;
        var toSkel = toModel.AffineInverse();
        Transform3D[] poses = new Transform3D[skel.GetBoneCount()];
        var scratch = (new Vector3[total], new Vector3[total]);

        // A clip that walks off: where its root bone is at each end of the
        // stretch a role plays, to be taken out again (a loop's travel spread
        // evenly over it, so its sway stays and its end meets its start).
        int still = walker != null ? skel.FindBone(walker) : -1;
        var travel = new Dictionary<string, (Vector3 From, Vector3 To)>();
        Vector3 Travel(string clip, double at)
        {
            skel.ResetBonePoses();
            if (anim.CurrentAnimation != clip) anim.Play(clip, 0);
            anim.Seek(at, true);
            return toModel * skel.GetBoneGlobalPose(still).Origin;
        }
        var spot = Vector3.Zero;
        if (still >= 0 && roles.Find(x => x.Name == "idle") is { } rest) spot = Travel(rest.Clip, rest.From);

        // Poses the skeleton for a role at t: the clip, then the moves over it.
        Transform3D Pose(Role r, double t)
        {
            double at = r.Hold ? r.From : r.From + t * r.Rate;
            if (still >= 0 && !travel.ContainsKey(r.Name)) travel[r.Name] = (Travel(r.Clip, r.From), Travel(r.Clip, r.From + r.Length * r.Rate));
            // From rest each time: a bone the clip does not move must not keep the last frame's turn.
            skel.ResetBonePoses();
            if (anim.CurrentAnimation != r.Clip) anim.Play(r.Clip, 0);
            anim.Seek(at, true);
            if (still >= 0)
            {
                var (a, b) = travel[r.Name];
                var off = r.Loops && !r.Hold ? a.Lerp(b, (float)((at - r.From) / (r.Length * r.Rate))) : a;
                var now = toModel * skel.GetBoneGlobalPose(still).Origin;
                var want = new Vector3(now.X - off.X + spot.X, now.Y, now.Z - off.Z + spot.Z);
                int parent = skel.GetBoneParent(still);
                var parentG = parent >= 0 ? skel.GetBoneGlobalPose(parent) : Transform3D.Identity;
                skel.SetBonePosePosition(still, parentG.AffineInverse() * (toSkel * want));
            }
            var root = Transform3D.Identity;
            if (r.Over?.Invoke(Math.Clamp(t / Math.Max(1e-6, r.Length), 0, 1)) is { } mv)
            {
                for (int b = 0; b < skel.GetBoneCount(); b++)
                {
                    if (!mv.Bones.TryGetValue(skel.GetBoneName(b), out var m)) continue;
                    // Turned about its own origin in the model's space, then moved.
                    var g = toModel * skel.GetBoneGlobalPose(b);
                    var o = g.Origin;
                    var turned = new Transform3D(Euler(m.Turn), o + m.Move) * new Transform3D(Godot.Basis.Identity, -o) * g;
                    int parent = skel.GetBoneParent(b);
                    var parentG = parent >= 0 ? skel.GetBoneGlobalPose(parent) : Transform3D.Identity;
                    var local = parentG.AffineInverse() * (toSkel * turned);
                    skel.SetBonePosePosition(b, local.Origin);
                    skel.SetBonePoseRotation(b, local.Basis.Orthonormalized().GetRotationQuaternion());
                    skel.SetBonePoseScale(b, local.Basis.Scale);
                }
                root = new Transform3D(Euler(mv.Turn), mv.Move);
            }
            return root;
        }

        void Skin(Transform3D root, Vector3[] pos, Vector3[] nor)
        {
            var m0 = root * toModel;
            for (int b = 0; b < poses.Length; b++) poses[b] = m0 * skel.GetBoneGlobalPose(b);
            foreach (var p in parts)
            {
                int o = p.Surf.Offset;
                if (p.Rigid >= 0)
                {
                    var m = poses[p.Rigid] * p.Rel;
                    for (int i = 0; i < p.V.Length; i++) { pos[o + i] = m * p.V[i]; nor[o + i] = (m.Basis * p.N[i]).Normalized(); }
                    continue;
                }
                // Each bind's matrix once a frame, not once a vertex.
                var now = p.BindNow!;
                for (int k = 0; k < now.Length; k++) now[k] = p.BindBone![k] >= 0 ? poses[p.BindBone[k]] * p.BindPose![k] : m0;
                var bones = p.Bones!; var weights = p.Weights!;
                for (int i = 0; i < p.V.Length; i++)
                {
                    Vector3 v = p.V[i], n = p.N[i], sp = Vector3.Zero, sn = Vector3.Zero;
                    float wsum = 0;
                    for (int k = 0; k < p.Stride; k++)
                    {
                        float w = weights[i * p.Stride + k];
                        if (w <= 0) continue;
                        ref var m = ref now[bones[i * p.Stride + k]];
                        sp += (m * v) * w;
                        sn += (m.Basis * n) * w;
                        wsum += w;
                    }
                    pos[o + i] = wsum > 0 ? sp / wsum : m0 * v;
                    nor[o + i] = sn.LengthSquared() > 0 ? sn.Normalized() : n;
                }
            }
        }

        void Sample(string role, double t, Vector3[] pos, Vector3[] nor)
        {
            var r = roles.Find(x => x.Name == role)!;
            Skin(Pose(r, t), pos, nor);
            // A looped stretch of a longer clip: its last third eased into what
            // came before its start, so its end is its beginning.
            double w = r.Seam ? Math.Clamp((t / r.Length - 0.66) / 0.34, 0, 1) : 0;
            if (w <= 0 || r.From < r.Length * r.Rate * 0.34) return;
            var (bp, bn) = scratch;
            Skin(Pose(r, t - r.Length), bp, bn);
            float k = (float)(w * w * (3 - 2 * w));
            for (int i = 0; i < pos.Length; i++) { pos[i] = pos[i].Lerp(bp[i], k); nor[i] = nor[i].Lerp(bn[i], k).Normalized(); }
        }

        var list = new List<(string Role, double Duration, bool Loop)>();
        foreach (var r in roles) list.Add((r.Name, r.Length, r.Loops));
        var asset = Write(key, parts.ConvertAll(p => p.Surf), total, list, fps, Sample);
        if (Args.Has("vat-probe")) GD.Print($"  {key}: parts+lods {tParts - t0} ms, frames {Time.GetTicksMsec() - tParts} ms, {total} vertices");
        return asset;
    }

    static readonly Dictionary<(Mesh, int, string), ImporterMesh> simpler = new();

    /// <summary>A mesh's surface as the baker takes it: its arrays, its
    /// material, and simplified versions of its triangles (meshoptimizer,
    /// through Godot's ImporterMesh: they share its vertices).</summary>
    static Skinned Part(MeshInstance3D mi, int s)
    {
        // The figure's shape keys, as set on this one.
        var am = mi.Mesh as ArrayMesh;
        int shapes = am?.GetBlendShapeCount() ?? 0;
        var weights = new float[shapes];
        for (int k = 0; k < shapes; k++) weights[k] = mi.GetBlendShapeValue(k);
        var shapeKey = string.Join(",", weights);
        if (!simpler.TryGetValue((mi.Mesh, s, shapeKey), out var im))
        {
            var src = mi.Mesh.SurfaceGetArrays(s);
            if (am != null && shapes > 0 && DisplayServer.GetName() != "headless")
            {
                var basis = src[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var shaped = (Vector3[])basis.Clone();
                var sets = am.SurfaceGetBlendShapeArrays(s);
                for (int k = 0; k < shapes && k < sets.Count; k++)
                {
                    if (weights[k] == 0) continue;
                    var sv = sets[k][(int)Mesh.ArrayType.Vertex].AsVector3Array();
                    bool relative = am.BlendShapeMode == Mesh.BlendShapeMode.Relative;
                    for (int i = 0; i < shaped.Length && i < sv.Length; i++) shaped[i] += (relative ? sv[i] : sv[i] - basis[i]) * weights[k];
                }
                src[(int)Mesh.ArrayType.Vertex] = shaped;
            }
            var b = src[(int)Mesh.ArrayType.Bones];
            var vc = src[(int)Mesh.ArrayType.Vertex].AsVector3Array().Length;
            bool eight = b.VariantType != Variant.Type.Nil && vc > 0 && b.AsInt32Array().Length / vc == 8;
            im = new ImporterMesh();
            im.AddSurface(Mesh.PrimitiveType.Triangles, src, flags: eight ? (ulong)Mesh.ArrayFormat.FlagUse8BoneWeights : 0);
            im.GenerateLods(60, 25, new Godot.Collections.Array());
            simpler[(mi.Mesh, s, shapeKey)] = im;
        }
        var arr = im.GetSurfaceArrays(0);
        var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
        var uvV = arr[(int)Mesh.ArrayType.TexUV];
        var idxV = arr[(int)Mesh.ArrayType.Index];
        var uv = uvV.VariantType == Variant.Type.Nil ? new Vector2[v.Length] : uvV.AsVector2Array();
        var idx = idxV.VariantType == Variant.Type.Nil ? Seq(v.Length) : idxV.AsInt32Array();
        var p = new Skinned
        {
            V = v, N = Normals(arr, v.Length), Uv = uv.Length == v.Length ? uv : new Vector2[v.Length], Index = idx,
            Mat = mi.GetSurfaceOverrideMaterial(s) ?? mi.MaterialOverride ?? mi.Mesh.SurfaceGetMaterial(s),
        };
        var bonesV = arr[(int)Mesh.ArrayType.Bones];
        if (bonesV.VariantType != Variant.Type.Nil)
        {
            p.Bones = bonesV.AsInt32Array();
            p.Weights = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
            p.Stride = v.Length > 0 ? p.Bones.Length / v.Length : 4;
        }
        for (int i = 0; i < im.GetSurfaceLodCount(0); i++)
        {
            var li = im.GetSurfaceLodIndices(0, i);
            if (li.Length >= 3) p.Lods.Add(li);
        }
        p.Lods.Sort((x, y) => y.Length.CompareTo(x.Length));
        return p;
    }

    /// <summary>A figure light enough for a crowd: each part down to one of
    /// its simpler versions, alike in proportion, until all of them together
    /// are within the budget; then only the vertices still used are kept.</summary>
    static void Slim(List<Skinned> parts, int budget)
    {
        int Budget = budget;
        int Used(int[] idx) { var seen = new HashSet<int>(idx); return seen.Count; }
        int all = 0;
        foreach (var p in parts) all += p.V.Length;
        if (all <= Budget) return;
        double ratio = Budget * 1.2 / all;
        var pick = new int[]?[parts.Count];
        for (int tries = 0; tries < 8; tries++)
        {
            int verts = 0;
            for (int i = 0; i < parts.Count; i++)
            {
                var p = parts[i];
                // Every part keeps a few percent of itself: a figure a little
                // over budget beats one whose body has been simplified away.
                int floor = Math.Min(p.Index.Length, Math.Max(90, p.Index.Length / 25 / 3 * 3));
                int want = Math.Max(floor, (int)(p.Index.Length * ratio));
                // Finest first: the last that still has what was asked for is the coarsest that does.
                var best = p.Index;
                foreach (var lod in p.Lods) if (lod.Length >= want) best = lod;
                pick[i] = best;
                verts += Used(best);
            }
            if (verts <= Budget) break;
            ratio *= (double)Budget / verts * 0.9;
        }
        for (int i = 0; i < parts.Count; i++)
        {
            Compact(parts[i], pick[i]!);
        }
    }

    /// <summary>Keep only the vertices a triangle list uses, renumbered.</summary>
    static void Compact(Skinned p, int[] idx)
    {
        var map = new Dictionary<int, int>();
        var order = new List<int>();
        var ni = new int[idx.Length];
        for (int k = 0; k < idx.Length; k++)
        {
            if (!map.TryGetValue(idx[k], out var to)) { to = order.Count; map[idx[k]] = to; order.Add(idx[k]); }
            ni[k] = to;
        }
        T[] Take<T>(T[] src, int stride = 1)
        {
            var o = new T[order.Count * stride];
            for (int i = 0; i < order.Count; i++) Array.Copy(src, order[i] * stride, o, i * stride, stride);
            return o;
        }
        p.V = Take(p.V);
        p.N = Take(p.N);
        p.Uv = Take(p.Uv);
        if (p.Bones != null) p.Bones = Take(p.Bones, p.Stride);
        if (p.Weights != null) p.Weights = Take(p.Weights, p.Stride);
        p.Index = ni;
    }

    static IEnumerable<MeshInstance3D> Meshes(Node n)
    {
        foreach (var c in n.GetChildren())
        {
            if (c is MeshInstance3D mi && mi.Mesh != null) yield return mi;
            foreach (var d in Meshes(c)) yield return d;
        }
    }

    static Vector3[] Normals(Godot.Collections.Array arr, int n)
    {
        var v = arr[(int)Mesh.ArrayType.Normal];
        var a = v.VariantType == Variant.Type.Nil ? Array.Empty<Vector3>() : v.AsVector3Array();
        return a.Length == n ? a : new Vector3[n];
    }

    /// <summary>A surface's rest arrays and its paint, from the material it had.</summary>
    static Surf Surface(Vector2[] uv, int[] idx, int n, Material? mat)
    {
        var s = new Surf { Uv = uv, Index = idx, Count = n };
        if (mat is ShaderMaterial sm)
        {
            s.Tex = sm.GetShaderParameter("albedo_tex").As<Texture2D>();
            s.Albedo = sm.GetShaderParameter("albedo").AsColor();
            s.Roughness = sm.GetShaderParameter("roughness").AsSingle();
            // Metal where a texture says so is detail a crowd figure cannot show: matte.
            s.Metallic = sm.GetShaderParameter("use_metal").AsBool() ? 0 : sm.GetShaderParameter("metallic").AsSingle();
            if (sm.GetShaderParameter("use_dye").AsBool())
            {
                s.Dyed = true;
                s.DyeColor = sm.GetShaderParameter("dye_color").AsVector3();
                s.DyeH = sm.GetShaderParameter("dye_h").AsVector3();
                s.DyeS = sm.GetShaderParameter("dye_s").AsVector3();
                s.DyeV = sm.GetShaderParameter("dye_v").AsVector3();
                s.DyeLum = sm.GetShaderParameter("dye_lum").AsSingle();
            }
        }
        if (mat is BaseMaterial3D bm)
        {
            if (bm.Transparency != BaseMaterial3D.TransparencyEnum.Disabled)
                s.Cut = bm.Transparency == BaseMaterial3D.TransparencyEnum.AlphaScissor ? bm.AlphaScissorThreshold : 0.4f;
            s.Tex = bm.AlbedoTexture;
            if (bm.NormalEnabled && bm.NormalTexture != null) s.Normal = bm.NormalTexture;
            s.Albedo = bm.AlbedoColor;
            s.Roughness = bm.Roughness;
            s.Metallic = bm.MetallicTexture != null ? 0 : bm.Metallic;
            if (bm.EmissionEnabled) s.Glow = bm.Emission * bm.EmissionEnergyMultiplier;
        }
        return s;
    }

    static int[] Seq(int n) { var a = new int[n]; for (int i = 0; i < n; i++) a[i] = i; return a; }

    /* -------------------------------------------------------------- write -- */

    /// <summary>A bake as data: what the cache keeps, and what the mesh and textures are made from.</summary>
    sealed class Baked
    {
        public required string Key;
        public int Width, Rows, FrameCount;
        public float Height;
        public required Dictionary<string, VatAsset.Clip> Clips;
        public required byte[] Pos, Nor;
        public required List<Surf> Surfs;
    }

    static VatAsset Write(string key, List<Surf> surfs, int total, List<(string Role, double Duration, bool Loop)> roles, double fps, Sampler sample)
    {
        var clips = new Dictionary<string, VatAsset.Clip>();
        int frameCount = 0;
        foreach (var (role, dur, loop) in roles)
        {
            int frames = Math.Min(MaxFrames, Math.Max(2, (int)Math.Round(dur * fps) + 1));
            clips[role] = new VatAsset.Clip(frameCount, frames, (frames - 1) / Math.Max(1e-3, dur), dur, loop);
            frameCount += frames;
        }
        int width = Math.Min(4096, Math.Max(1, total));
        int rows = (total + width - 1) / width;
        int texH = rows * frameCount;
        var posBytes = new byte[width * texH * 8];
        var norBytes = new byte[width * texH * 4];
        var pos = new Vector3[total];
        var nor = new Vector3[total];
        float height = 0;
        int frameIndex = 0;
        foreach (var (role, dur, _) in roles)
        {
            var c = clips[role];
            for (int f = 0; f < c.Frames; f++)
            {
                sample(role, (double)f / (c.Frames - 1) * dur * 0.999, pos, nor);
                for (int i = 0; i < total; i++)
                {
                    int row = frameIndex * rows + i / width, col = i % width;
                    int tk = row * width + col;
                    Half(posBytes, tk * 8, pos[i].X); Half(posBytes, tk * 8 + 2, pos[i].Y); Half(posBytes, tk * 8 + 4, pos[i].Z); Half(posBytes, tk * 8 + 6, 1);
                    var n = nor[i];
                    norBytes[tk * 4] = (byte)Math.Round((n.X * 0.5f + 0.5f) * 255);
                    norBytes[tk * 4 + 1] = (byte)Math.Round((n.Y * 0.5f + 0.5f) * 255);
                    norBytes[tk * 4 + 2] = (byte)Math.Round((n.Z * 0.5f + 0.5f) * 255);
                    norBytes[tk * 4 + 3] = 255;
                    if (pos[i].Y > height) height = pos[i].Y;
                }
                // The rest geometry is the first frame.
                if (frameIndex == 0)
                    foreach (var s in surfs) { s.V = pos[s.Offset..(s.Offset + s.Count)]; s.N = nor[s.Offset..(s.Offset + s.Count)]; }
                frameIndex++;
            }
        }
        var baked = new Baked { Key = key, Width = width, Rows = rows, FrameCount = frameCount, Height = height, Clips = clips, Pos = posBytes, Nor = norBytes, Surfs = surfs };
        Save(baked);
        return Build(baked);
    }

    static VatAsset Build(Baked b)
    {
        int texH = b.Rows * b.FrameCount;
        var posTex = ImageTexture.CreateFromImage(Image.CreateFromData(b.Width, texH, false, Image.Format.Rgbah, b.Pos));
        var norTex = ImageTexture.CreateFromImage(Image.CreateFromData(b.Width, texH, false, Image.Format.Rgba8, b.Nor));
        shader ??= GD.Load<Shader>("res://shaders/vat.gdshader");
        cutShader ??= GD.Load<Shader>("res://shaders/vat_cut.gdshader");
        normalShader ??= GD.Load<Shader>("res://shaders/vat_normal.gdshader");
        var mesh = new ArrayMesh();
        foreach (var s in b.Surfs)
        {
            var arrays = new Godot.Collections.Array();
            arrays.Resize((int)Mesh.ArrayType.Max);
            arrays[(int)Mesh.ArrayType.Vertex] = s.V;
            arrays[(int)Mesh.ArrayType.Normal] = s.N;
            arrays[(int)Mesh.ArrayType.TexUV] = s.Uv;
            // White where the model has no colours of its own: the instance's tint multiplies it.
            if (s.Color == null) { s.Color = new Color[s.Count]; Array.Fill(s.Color, Colors.White); }
            arrays[(int)Mesh.ArrayType.Color] = s.Color;
            arrays[(int)Mesh.ArrayType.Index] = s.Index;
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
            // Only a surface with a normal map pays for reading it (a variant
            // of the shader, so every other kind's is unchanged).
            var m = new ShaderMaterial { Shader = s.Cut >= 0 ? cutShader : s.Normal != null ? normalShader : shader };
            if (s.Normal != null && s.Cut < 0) m.SetShaderParameter("normal_tex", s.Normal);
            if (s.Cut >= 0) m.SetShaderParameter("alpha_cut", s.Cut);
            m.SetShaderParameter("vat_pos", posTex);
            m.SetShaderParameter("vat_nor", norTex);
            m.SetShaderParameter("vat_width", b.Width);
            m.SetShaderParameter("vat_rows", b.Rows);
            m.SetShaderParameter("vat_offset", s.Offset);
            m.SetShaderParameter("use_tex", s.Tex != null);
            if (s.Tex != null) m.SetShaderParameter("albedo_tex", s.Tex);
            m.SetShaderParameter("albedo", s.Albedo);
            m.SetShaderParameter("roughness", s.Roughness);
            m.SetShaderParameter("metallic", s.Metallic);
            m.SetShaderParameter("glow_color", new Vector3(s.Glow.R, s.Glow.G, s.Glow.B));
            if (s.Dyed)
            {
                m.SetShaderParameter("use_dye", true);
                m.SetShaderParameter("dye_color", s.DyeColor);
                m.SetShaderParameter("dye_h", s.DyeH);
                m.SetShaderParameter("dye_s", s.DyeS);
                m.SetShaderParameter("dye_v", s.DyeV);
                m.SetShaderParameter("dye_lum", s.DyeLum);
            }
            mesh.SurfaceSetMaterial(mesh.GetSurfaceCount() - 1, m);
        }
        // The posed bodies reach beyond the rest pose (a lunge, a fall): a generous box.
        mesh.CustomAabb = new Aabb(new Vector3(-2.5f, -1.5f, -2.5f), new Vector3(5, Math.Max(3, b.Height + 2), 5));
        return new VatAsset { Key = b.Key, Mesh = mesh, Width = b.Width, Rows = b.Rows, Clips = b.Clips, Height = b.Height };
    }

    /* -------------------------------------------------------------- cache -- */

    // Bakes are kept on disk between runs (a kind costs its figure's models,
    // its clips and seconds of sampling; read back, a few milliseconds). Bump
    // Version whenever what a bake holds or how it is made changes (Visuals,
    // Beasts, this file).
    const int Version = 14;
    static string CachePath(string key) => $"user://vat/{key}.v{Version}.bin";

    static byte[] Bytes<T>(T[] a) where T : struct => System.Runtime.InteropServices.MemoryMarshal.AsBytes(a.AsSpan()).ToArray();
    static T[] Of<T>(byte[] b) where T : struct => System.Runtime.InteropServices.MemoryMarshal.Cast<byte, T>(b).ToArray();

    static void Save(Baked b)
    {
        // A run without a screen keeps no texture data to write down.
        if (DisplayServer.GetName() == "headless") return;
        DirAccess.MakeDirRecursiveAbsolute("user://vat");
        using var f = FileAccess.Open(CachePath(b.Key), FileAccess.ModeFlags.Write);
        if (f == null) return;
        void Blob(byte[] data) { f.Store32((uint)data.Length); f.StoreBuffer(data); }
        f.Store32(Version);
        f.Store32((uint)b.Width); f.Store32((uint)b.Rows); f.Store32((uint)b.FrameCount); f.StoreFloat(b.Height);
        f.Store32((uint)b.Clips.Count);
        foreach (var (role, c) in b.Clips)
        {
            f.StorePascalString(role);
            f.Store32((uint)c.Start); f.Store32((uint)c.Frames); f.StoreDouble(c.Fps); f.StoreDouble(c.Duration); f.Store8((byte)(c.Loop ? 1 : 0));
        }
        Blob(b.Pos);
        Blob(b.Nor);
        f.Store32((uint)b.Surfs.Count);
        foreach (var s in b.Surfs)
        {
            f.Store32((uint)s.Count); f.Store32((uint)s.Offset);
            Blob(Bytes(s.V)); Blob(Bytes(s.N)); Blob(Bytes(s.Uv)); Blob(s.Color != null ? Bytes(s.Color) : Array.Empty<byte>()); Blob(Bytes(s.Index));
            if (!Tex(s.Tex)) { f.Close(); DirAccess.RemoveAbsolute(CachePath(b.Key)); return; }
            foreach (var c in new[] { s.Albedo, s.Glow }) { f.StoreFloat(c.R); f.StoreFloat(c.G); f.StoreFloat(c.B); f.StoreFloat(c.A); }
            f.StoreFloat(s.Roughness); f.StoreFloat(s.Metallic);
            f.Store8((byte)(s.Dyed ? 1 : 0));
            foreach (var v3 in new[] { s.DyeColor, s.DyeH, s.DyeS, s.DyeV }) { f.StoreFloat(v3.X); f.StoreFloat(v3.Y); f.StoreFloat(v3.Z); }
            f.StoreFloat(s.DyeLum);
            f.StoreFloat(s.Cut);
            if (!Tex(s.Normal)) { f.Close(); DirAccess.RemoveAbsolute(CachePath(b.Key)); return; }
        }

        // A texture by its file, or (one inside a model's file) by its pixels.
        bool Tex(Texture2D? t)
        {
            var tp = t?.ResourcePath ?? "";
            if (t == null) f.Store8(0);
            else if (tp != "" && !tp.Contains("::")) { f.Store8(1); f.StorePascalString(tp); }
            else
            {
                var img = t.GetImage();
                if (img == null || img.IsEmpty()) return false;
                f.Store8(2);
                f.Store32((uint)img.GetWidth()); f.Store32((uint)img.GetHeight()); f.Store32((uint)img.GetFormat()); f.Store8((byte)(img.HasMipmaps() ? 1 : 0));
                Blob(img.GetData());
            }
            return true;
        }
    }

    static Baked? Load(string key)
    {
        var path = CachePath(key);
        if (Args.Has("vat-fresh") || !FileAccess.FileExists(path)) return null;
        using var f = FileAccess.Open(path, FileAccess.ModeFlags.Read);
        if (f == null || f.Get32() != Version) return null;
        byte[] Blob() => f.GetBuffer(f.Get32());
        Texture2D? Tex()
        {
            switch (f.Get8())
            {
                case 1: return GD.Load<Texture2D>(f.GetPascalString());
                case 2:
                {
                    int w = (int)f.Get32(), h = (int)f.Get32();
                    var fmt = (Image.Format)f.Get32();
                    bool mips = f.Get8() == 1;
                    return ImageTexture.CreateFromImage(Image.CreateFromData(w, h, mips, fmt, Blob()));
                }
                default: return null;
            }
        }
        int width = (int)f.Get32(), rows = (int)f.Get32(), frames = (int)f.Get32();
        float height = f.GetFloat();
        var clips = new Dictionary<string, VatAsset.Clip>();
        for (int n = (int)f.Get32(), i = 0; i < n; i++)
        {
            var role = f.GetPascalString();
            clips[role] = new VatAsset.Clip((int)f.Get32(), (int)f.Get32(), f.GetDouble(), f.GetDouble(), f.Get8() == 1);
        }
        var pos = Blob();
        var nor = Blob();
        var surfs = new List<Surf>();
        for (int n = (int)f.Get32(), i = 0; i < n; i++)
        {
            int count = (int)f.Get32(), offset = (int)f.Get32();
            var v = Of<Vector3>(Blob()); var nn = Of<Vector3>(Blob()); var uv = Of<Vector2>(Blob()); var col = Blob(); var idx = Of<int>(Blob());
            var tex = Tex();
            Color C() => new(f.GetFloat(), f.GetFloat(), f.GetFloat(), f.GetFloat());
            var albedo = C(); var glow = C();
            var s = new Surf
            {
                Uv = uv, Index = idx, Count = count, Offset = offset, V = v, N = nn, Color = col.Length > 0 ? Of<Color>(col) : null,
                Tex = tex, Albedo = albedo, Glow = glow, Roughness = f.GetFloat(), Metallic = f.GetFloat(),
            };
            s.Dyed = f.Get8() == 1;
            Vector3 V3() => new(f.GetFloat(), f.GetFloat(), f.GetFloat());
            s.DyeColor = V3(); s.DyeH = V3(); s.DyeS = V3(); s.DyeV = V3();
            s.DyeLum = f.GetFloat();
            s.Cut = f.GetFloat();
            s.Normal = Tex();
            surfs.Add(s);
        }
        if (f.GetError() != Error.Ok && f.GetError() != Error.FileEof) return null;
        return new Baked { Key = key, Width = width, Rows = rows, FrameCount = frames, Height = height, Clips = clips, Pos = pos, Nor = nor, Surfs = surfs };
    }

    static void Half(byte[] b, int at, float v)
    {
        ushort h = BitConverter.HalfToUInt16Bits((System.Half)v);
        b[at] = (byte)(h & 0xff);
        b[at + 1] = (byte)(h >> 8);
    }
}

/// <summary>
/// One kind of creature, drawn as many times as there are of it this frame:
/// a MultiMesh of its bake, filled from scratch every frame. The frame's
/// bodies are written into one array and handed over in a single call: three
/// calls into the engine for each body (its place, tint and clip) cost more
/// than the rest of the crowd's frame.
/// </summary>
public partial class VatCrowd : MultiMeshInstance3D
{
    public readonly VatAsset Asset;
    int count, capacity, shown;
    float[] buffer = Array.Empty<float>();
    /// <summary>A body's floats: its transform (12), colour (4) and custom data (4), as Godot lays a MultiMesh's buffer out.</summary>
    const int Stride = 20;

    public VatCrowd(VatAsset asset)
    {
        Asset = asset;
        Name = $"crowd:{asset.Key}";
        Layers = 2;
        CastShadow = ShadowCastingSetting.On;
        // They go everywhere: never culled as a whole (each is small; the GPU is not the limit here).
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
        Grow(64);
    }

    void Grow(int n)
    {
        capacity = n;
        // Keep what is already placed this frame.
        Array.Resize(ref buffer, n * Stride);
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, UseCustomData = true,
            InstanceCount = n, VisibleInstanceCount = 0, Mesh = Asset.Mesh,
        };
    }

    public void Begin() => count = 0;

    /// <summary>One body this frame, `t` seconds into its role's clip.</summary>
    public void Push(Transform3D at, string role, double t, float flash, float dissolve, float frozen, float burning, Color tint, float glow)
    {
        if (count >= capacity) Grow(capacity * 2);
        int o = count++ * Stride;
        var (f0, f1, blend) = Asset.Frame(role, t);
        static int Q(float v, int max) => (int)Math.Round(Math.Clamp(v, 0, 1) * max);
        int word = Q(flash, 255) | Q(dissolve, 255) << 8 | Q(frozen, 15) << 16 | Q(burning, 15) << 20;
        var b = at.Basis;
        var buf = buffer;
        buf[o] = b.X.X; buf[o + 1] = b.Y.X; buf[o + 2] = b.Z.X; buf[o + 3] = at.Origin.X;
        buf[o + 4] = b.X.Y; buf[o + 5] = b.Y.Y; buf[o + 6] = b.Z.Y; buf[o + 7] = at.Origin.Y;
        buf[o + 8] = b.X.Z; buf[o + 9] = b.Y.Z; buf[o + 10] = b.Z.Z; buf[o + 11] = at.Origin.Z;
        buf[o + 12] = tint.R; buf[o + 13] = tint.G; buf[o + 14] = tint.B; buf[o + 15] = glow;
        buf[o + 16] = f0; buf[o + 17] = f1; buf[o + 18] = blend; buf[o + 19] = word;
    }

    public void End()
    {
        // Nothing of this kind now or last frame: nothing to send.
        if (count == 0 && shown == 0) return;
        RenderingServer.MultimeshSetBuffer(Multimesh.GetRid(), new ReadOnlySpan<float>(buffer, 0, capacity * Stride));
        Multimesh.VisibleInstanceCount = shown = count;
    }
}
