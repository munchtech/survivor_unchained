using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;
using Basis = Godot.Basis;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// <summary>
/// --lookdev RIG[,RIG...]|all (L1 B0, tools/style/lookdev.py): the lookdev stage. In an arena (--zone arena: its painted
/// ground, its air), with nothing spawning (--no-foes), every material class is stood in rows the play camera sees at
/// once, on the game's own pieces and paths: her at the middle (the game's idle, facing the camera); three Deep Shaw
/// wolves (the VAT crowd, held where they stand); two townsfolk (Folk.Person); the Waystation's small plaster house
/// (house 25 of its props, our own walls and roof: OwnWalls), a stretch of the square's setts (the town's terrain
/// material, its paint sampled on the square), our barrel and crate, a lamp post; a boulder, a spruce and a young alder
/// (our flora: OWN_ROCK, OWN_FOLIAGE), pebbles and branches; a campfire as the Low Ford camp has it and a standing
/// lantern; five 0.6 m spheres (tools_scenes/lookdev_sphere.gdshader: skin, leather, cloth, iron, bronze).
/// Each rig (night: the Low Ford's play night; day: the town's day; dawn: the Low Ford's dawn; arena: this arena's own
/// night) is set, settles, and is shot three ways: play (FollowCamera's play pose), close (the close view at its
/// nearest, as --close 1) and side (a wider view at 15 degrees of pitch). Frames: godot/.shots/NAME_RIG_CAM_1.png.
/// --lookdev-settle S: seconds a rig settles before its first frame (2.5).
/// </summary>
public partial class Game
{
    static readonly string[] LookRigs = { "night", "day", "dawn", "arena" };
    string[]? lookRigs;
    double lookBuiltAt = -1;
    int lookStep = -1;
    Vector3 lookP, lookR, lookF;
    float lookFacing;
    Camera3D? lookCam;
    readonly List<Flame> lookFlames = new();
    readonly List<Node3D> lookLamps = new();
    OmniLight3D? lookFireLight;

    void Lookdev(double dt)
    {
        if (Args.Get("lookdev") is not string spec || Battle is not { } b || scene == null || zone == null) return;
        lookRigs ??= spec == "all" || spec == "1" ? LookRigs : spec.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).Where(r => LookRigs.Contains(r)).ToArray();
        double t = Shots.Clock;
        if (lookBuiltAt < 0)
        {
            if (t < 1.0) return;
            LookBuild(b);
            lookBuiltAt = t;
            return;
        }
        // Her held in her place, whole, facing the camera.
        b.Player.X = lookP.X; b.Player.Z = lookP.Z; b.Player.Vx = b.Player.Vz = 0; b.Player.Hp = b.MaxHp;
        b.Player.Facing = lookFacing;
        double settle = Args.Num("lookdev-settle", 2.5f), per = settle + 4.0, t0 = lookBuiltAt + 1.5;
        if (t < t0) return;
        int k = (int)((t - t0) / per);
        if (k >= lookRigs.Length)
        {
            if (lookStep != 99) { lookStep = 99; spotClose = null; cam.Camera.MakeCurrent(); Shots.EndIn(1.0); GD.Print("lookdev: done"); }
            return;
        }
        double u = t - t0 - k * per;
        int step = u < settle ? 0 : u < settle + 2.0 ? 1 : u < settle + 3.5 ? 2 : 3;
        int id = k * 4 + step;
        if (id == lookStep) return;
        // (each step asks for the frame of the one before it, then moves on: the rig set, play, close, side)
        string rig = lookRigs[k];
        if (step == 0)
        {
            LookRig(rig);
            spotClose = null;
            cam.Camera.MakeCurrent();
            cam.Snap(lookP.X, lookP.Y, lookP.Z);
        }
        else if (step == 1) { Shots.Want($"{rig}_play", 0); spotClose = 1; }
        else if (step == 2) { Shots.Want($"{rig}_close", 0); spotClose = null; lookCam?.MakeCurrent(); }
        else Shots.Want($"{rig}_side", 0);
        lookStep = id;
    }

    void LookRig(string rig)
    {
        var p = rig switch
        {
            "night" => Atmospheres.LowFordNight, "day" => Atmospheres.WaystationDay, "dawn" => Atmospheres.LowFordDawn,
            _ => zone!.AtmosphereFor(TimeOfDay.Night),
        };
        bool night = rig is "night" or "arena";
        World.Time = rig switch { "day" => TimeOfDay.Day, "dawn" => TimeOfDay.Dawn, _ => TimeOfDay.Night };
        air.Air(rig == "arena" ? scene!.Data.Place?.Air : null);
        air.Set(p);
        scene!.View.SetNight(night);
        scene.Fx.Flare.Night = night;
        scene.View.SetDusk(false);
        // The town's lamps go cold by day (ZoneView.Town); the fire burns in every rig.
        foreach (var f in lookFlames) f.Lit = rig != "day";
        foreach (var l in lookLamps) Lamps.SetLit(l, rig != "day");
        if (lookFireLight != null) lookFireLight.ShadowEnabled = rig != "day";
        GD.Print($"lookdev: rig {rig} ({(rig == "arena" ? "the arena's night" : rig)}) at {Shots.Clock:0.00}s");
    }

    void LookBuild(Battle b)
    {
        var s = scene!;
        // The stage's frame: x to the play camera's right, y away from it (up the screen), on the ground.
        var cb = cam.Camera.GlobalTransform.Basis;
        lookF = new Vector3(-cb.Z.X, 0, -cb.Z.Z).Normalized();
        lookR = new Vector3(cb.X.X, 0, cb.X.Z).Normalized();
        lookP = new Vector3((float)b.Player.X, (float)s.HeightAt(b.Player.X, b.Player.Z), (float)b.Player.Z);
        lookFacing = Mathf.Atan2(-lookF.X, -lookF.Z);
        var basis = new Basis(lookR, Vector3.Up, -lookF);
        Vector3 W(float x, float y, float lift = 0)
        {
            var w = lookP + lookR * x + lookF * y;
            w.Y = (float)s.HeightAt(w.X, w.Z) + lift;
            return w;
        }
        Transform3D At(float x, float y, float yawDeg = 0, float scale = 1, float lift = 0) =>
            new(basis * new Basis(Vector3.Up, Mathf.DegToRad(yawDeg)).Scaled(Vector3.One * scale), W(x, y, lift));
        var root = new Node3D { Name = "Lookdev" };
        s.AddChild(root);
        void Put(Node3D? n, Transform3D at, string what)
        {
            if (n == null) { GD.PushWarning($"lookdev: no {what}"); return; }
            root.AddChild(n);
            n.GlobalTransform = at;
        }
        // Her, idle, facing the camera.
        b.Player.Facing = lookFacing;
        s.Player?.Face(lookFacing, lookP);
        foreach (var w in b.Weapons.Select(x => x.Id).ToList()) b.RemoveWeapon(w);
        // The crowd: three wolves of the pack, held.
        b.NoSpawn = false;
        foreach (var (x, y) in new[] { (-3.6f, 1.6f), (-4.4f, -0.6f), (-2.7f, -2.8f) })
        {
            var w = W(x, y);
            if (b.SpawnEnemy("wolf", w.X, w.Z) is { } e)
            {
                e.BoundX = e.X; e.BoundZ = e.Z;
                e.Status.Ensure(StatusKind.Bound, 1e6, 1, 1, 0);
            }
        }
        b.NoSpawn = true;
        // Folk: two of the town's.
        for (int i = 0; i < 2; i++)
        {
            var look = Lore.FolkLooks[(i * 3 + 1) % Lore.FolkLooks.Count];
            var person = Folk.Person(FolkRole.Adult, look, new Random(31 + i * 17));
            var v = new PersonView(person, null, 0.8 * (look.Scale ?? 1)) { Name = $"LookFolk{i}" };
            root.AddChild(v);
            v.GlobalTransform = new Transform3D(new Basis(Vector3.Up, lookFacing + (i == 0 ? -0.35f : 0.3f)), i == 0 ? W(3.2f, 1.3f) : W(4.4f, -0.9f));
            v.Loop("Idle");
        }
        // The town: the Waystation's small plaster house (house 25: our own walls and roof over the kit's plan), its door to the camera.
        var wz = new ZoneData("waystation");
        var house = new Node3D { Name = "LookHouse" };
        var walls = OwnWalls.For(wz);
        var hc = new Vector3(16f, -0.05f, -30f);
        int pieces = 0;
        for (int i = 0; i < wz.Props.Count; i++)
        {
            if (i >= wz.PropHouse.Count || wz.PropHouse[i] != 25) continue;
            var (pid, pat) = wz.Props[i];
            pieces++;
            if (walls != null && walls.Take(pid, 25, pat, 24)) continue;
            if (Dressing.Piece(pid) is Node3D kp) { kp.Transform = pat; house.AddChild(kp); }
        }
        if (walls != null) foreach (var _ in walls.Build(house)) { }
        root.AddChild(house);
        house.GlobalTransform = new Transform3D(basis, W(-7.5f, 8.5f)) * new Transform3D(Basis.Identity, -hc);
        // The square's setts: the town's terrain material, its paint as it lies on the square, on a patch of this ground.
        LookSetts(root, wz, W);
        Put(OwnProps.Piece("barrel"), At(0.9f, 5.2f, 20), "barrel");
        Put(OwnProps.Piece("crate"), At(2.1f, 5.9f, -12), "crate");
        LookLamp(root, "post_lantern", At(3.6f, 4.6f, 180));
        // The wild: a boulder, a spruce, a young alder, pebbles and branches (the arena's own grass round them).
        Put(Dressing.OwnTree("boulder_b"), At(6.6f, 4.4f, 30), "boulder");
        Put(Dressing.OwnTree("spruce_b"), At(9.8f, 8.5f), "spruce");
        Put(Dressing.OwnTree("alder_c"), At(6.2f, 9.5f, 0, 0.6f), "alder");
        Put(Dressing.OwnTree("pebbles_a"), At(5.4f, 2.4f), "pebbles");
        Put(OwnProps.Piece("branches_a"), At(6.6f, 1.6f, 40), "branches");
        // Light sources: the camp's fire (the Low Ford's: 80 over 18 m, three.js's units) and a standing lantern.
        var fat = W(5.6f, -3.0f);
        root.AddChild(Campfire.Build(fat, 1));
        lookFireLight = new OmniLight3D
        {
            Name = "LookFire", Position = fat + Vector3.Up * 1.1f, LightColor = new Color("#ff9a48"), LightEnergy = 80 / Mathf.Pi,
            OmniRange = 18, OmniAttenuation = 1.7f, ShadowEnabled = true,
        };
        root.AddChild(lookFireLight);
        LookLamp(root, "lantern_standing", At(1.9f, -2.3f, 200));
        // The library's base classes on spheres (0.6 m).
        var shader = GD.Load<Shader>("res://tools_scenes/lookdev_sphere.gdshader");
        var balls = new (string Name, Color C, float Rough, float Metal)[]
        {
            ("skin", new Color(0.80f, 0.60f, 0.50f), 0.7f, 0), ("leather", new Color(0.36f, 0.22f, 0.13f), 0.6f, 0),
            ("cloth", new Color(0.55f, 0.08f, 0.07f), 0.95f, 0), ("iron", new Color(0.45f, 0.45f, 0.47f), 0.45f, 1),
            ("bronze", new Color(0.72f, 0.45f, 0.20f), 0.35f, 1),
        };
        for (int i = 0; i < balls.Length; i++)
        {
            var m = new ShaderMaterial { Shader = shader };
            m.SetShaderParameter("albedo_color", balls[i].C);
            m.SetShaderParameter("roughness", balls[i].Rough);
            m.SetShaderParameter("metallic", balls[i].Metal);
            var mi = new MeshInstance3D { Name = "Sphere_" + balls[i].Name, Mesh = new SphereMesh { Radius = 0.3f, Height = 0.6f, RadialSegments = 48, Rings = 24 }, MaterialOverride = m };
            root.AddChild(mi);
            mi.GlobalPosition = W(-3.2f + i * 1.6f, -5.0f, 0.3f);
        }
        // The side view: 15 degrees of pitch, three-quarters from the camera's right, across the rows.
        var c = W(0, 2.5f, 1.0f);
        var dir = (-lookF * 0.75f + lookR * 0.66f).Normalized();
        float d = (float)Args.Num("lookdev-side-dist", 24f), pitch = Mathf.DegToRad((float)Args.Num("lookdev-side-pitch", 15f));
        lookCam = new Camera3D { Name = "LookSide", Fov = (float)Args.Num("lookdev-side-fov", 42f), Far = 600 };
        s.AddChild(lookCam);
        lookCam.GlobalPosition = c + dir * d * Mathf.Cos(pitch) + Vector3.Up * d * Mathf.Sin(pitch);
        lookCam.LookAt(c, Vector3.Up);
        // How flat the patch is (the brief: a flat 30 x 20 m of the arena's ground).
        float lo = float.MaxValue, hi = float.MinValue;
        for (float x = -15; x <= 15; x += 1) for (float y = -10; y <= 10; y += 1) { var w = W(x, y); lo = Mathf.Min(lo, w.Y); hi = Mathf.Max(hi, w.Y); }
        GD.Print($"lookdev: stage at {lookP} right {lookR} away {lookF}; house 25 {pieces} pieces; 30x20 m heights {lo:0.00}..{hi:0.00}; rigs {string.Join(",", lookRigs!)}");
    }

    void LookLamp(Node3D root, string kind, Transform3D at)
    {
        if (Lamps.Holder(kind) is not Node3D holder || Lamps.Of(kind) is not Lamps.Info info) { GD.PushWarning($"lookdev: no {kind}"); return; }
        root.AddChild(holder);
        holder.GlobalTransform = at;
        lookLamps.Add(holder);
        lookFlames.Add(FlameKit.Add(holder, info.Flame, FlameKind.Lamp, false, 1.6f, light: true));
        Lamps.SetLit(holder, true);
    }

    /// <summary>A 6 x 4 m stretch of the Waystation square's setts: the town's own terrain material, its paint (splat,
    /// mask, exposure, near) read on the square (0, 0) and held over the patch, on this ground's heights.</summary>
    void LookSetts(Node3D root, ZoneData wz, Func<float, float, float, Vector3> W)
    {
        var g = Ground.Build(wz);
        var src = (g.Mesh?.SurfaceGetMaterial(0) ?? g.MaterialOverride) as ShaderMaterial;
        g.QueueFree();
        if (src == null) { GD.PushWarning("lookdev: no town ground material"); return; }
        var mat = (ShaderMaterial)src.Duplicate();
        float sx = (float)Args.Num("lookdev-sq-x", 0f), sz = (float)Args.Num("lookdev-sq-z", 0f);
        foreach (var p in new[] { "splat", "paint_mask", "expo_tex", "near_tex" })
        {
            if (mat.GetShaderParameter(p).As<Texture2D>() is not Texture2D tx || tx.GetImage() is not Image im) continue;
            if (im.IsCompressed()) im.Decompress();
            int px = Mathf.Clamp((int)((sx + wz.Size * 0.5f) / wz.Size * im.GetWidth()), 0, im.GetWidth() - 1);
            int pz = Mathf.Clamp((int)((sz + wz.Size * 0.5f) / wz.Size * im.GetHeight()), 0, im.GetHeight() - 1);
            var one = Image.CreateEmpty(4, 4, false, Image.Format.Rgbaf);
            one.Fill(im.GetPixel(px, pz));
            mat.SetShaderParameter(p, ImageTexture.CreateFromImage(one));
            GD.Print($"lookdev: setts {p} = {im.GetPixel(px, pz)}");
        }
        int nx = 24, ny = 16;
        float x0 = -3, x1 = 3, y0 = 3.5f, y1 = 7.5f;
        var verts = new List<Vector3>();
        for (int j = 0; j <= ny; j++)
            for (int i = 0; i <= nx; i++)
                verts.Add(W(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, 0.02f));
        var idx = new List<int>();
        void Tri(int a, int b2, int c2)
        {
            // (wound as the ground is: (b - a) x (c - a) pointing down)
            if ((verts[b2] - verts[a]).Cross(verts[c2] - verts[a]).Y < 0) idx.AddRange(new[] { a, b2, c2 }); else idx.AddRange(new[] { a, c2, b2 });
        }
        for (int j = 0; j < ny; j++)
            for (int i = 0; i < nx; i++)
            {
                int a = j * (nx + 1) + i, b2 = a + 1, c2 = a + nx + 1, d2 = c2 + 1;
                Tri(a, b2, c2); Tri(b2, d2, c2);
            }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        arrays[(int)Mesh.ArrayType.Normal] = Enumerable.Repeat(Vector3.Up, verts.Count).ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        mesh.SurfaceSetMaterial(0, mat);
        root.AddChild(new MeshInstance3D { Name = "LookSetts", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
    }
}
