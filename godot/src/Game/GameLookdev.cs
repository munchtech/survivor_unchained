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
/// --lookdev-key AZ,EL (L1 B1c): a test fixture, not a rig (B4 makes those): the key held at AZ degrees round from the
/// lens toward its right and EL up, relative to whichever camera shoots, every frame and at every view (front three-quarter
/// about 35,40), and the close view's own key and rim spots held off, so the one key models her and the stage's forms.
/// Its cast shadow is off (the arena's canopy shades her stand at most keys) unless a third value is 1: AZ,EL,1.
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
    static readonly float[]? LookKeyArg = Args.Get("lookdev-key") is string lk
        ? lk.Split(',').Select(v => float.Parse(v, System.Globalization.CultureInfo.InvariantCulture)).ToArray() : null;
    /// <summary>--lookdev-key is holding the key (GameCloseUp holds its key and rim spots off).</summary>
    bool LookKeyHeld => LookKeyArg != null && lookBuiltAt >= 0;

    void LookKey()
    {
        if (LookKeyArg is not { Length: >= 2 } k || GetViewport().GetCamera3D() is not { } c) return;
        var cb = c.GlobalTransform.Basis;
        var back = new Vector3(cb.Z.X, 0, cb.Z.Z).Normalized();
        var right = new Vector3(cb.X.X, 0, cb.X.Z).Normalized();
        float az = Mathf.DegToRad(k[0]), el = Mathf.DegToRad(k[1]);
        var dir = ((back * Mathf.Cos(az) + right * Mathf.Sin(az)) * Mathf.Cos(el) + Vector3.Up * Mathf.Sin(el)).Normalized();
        air.Key.Basis = Basis.LookingAt(-dir, Mathf.Abs(dir.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        air.Key.ShadowEnabled = k.Length > 2 && k[2] > 0.5f;
        // (L1 B4: the fixture's key is the lens's, so no canopy dapple along it)
        RenderingServer.GlobalShaderParameterSet("cel_key", new Vector4(dir.X, dir.Y, dir.Z, 0));
    }

    /// <summary>What the stage holds, by row, each with its world box (for the frame check: LookFrame).</summary>
    readonly List<(string Row, string Name, Func<Aabb?> Box)> lookItems = new();
    readonly List<Enemy> lookWolves = new();

    void Lookdev(double dt)
    {
        if (Args.Get("lookdev") is not string spec || Battle is not { } b || scene == null || zone == null) return;
        lookRigs ??= spec == "all" || spec == "1" ? LookRigs : spec.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).Where(r => LookRigs.Contains(r)).ToArray();
        // No drafts on the stage (the arena's opening Great Blessing would cover every frame).
        b.PendingLevels = 0; b.PendingBlessings.Clear(); b.GreatOwed = 0; draftWait = 0;
        double t = Shots.Clock;
        if (lookBuiltAt < 0)
        {
            if (t < 1.0) return;
            LookBuild(b);
            lookBuiltAt = t;
            return;
        }
        LookKey();
        // Her held in her place, whole, facing the camera.
        b.Player.X = lookP.X; b.Player.Z = lookP.Z; b.Player.Vx = b.Player.Vz = 0; b.Player.Hp = b.MaxHp;
        b.Player.Facing = lookFacing;
        // The wolves held standing in their idle: risen and not yet come on (Ai's Rising, its StateT held up; CrowdView
        // draws a risen body's idle). Bound alone left them running on the spot (the sim's chase speed, the walk clip).
        foreach (var w in lookWolves)
        {
            w.State = EnemyState.Rising; w.StateT = 1e3; w.AnimT = Math.Max(w.AnimT, 5); w.Anim = EnemyAnim.Idle;
            w.X = w.BoundX; w.Z = w.BoundZ; w.Vx = w.Vz = 0;
        }
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
            LookKey();
            spotClose = null;
            cam.Camera.MakeCurrent();
            cam.Snap(lookP.X, lookP.Y, lookP.Z);
        }
        else if (step == 1) { Shots.Want($"{rig}_play", 0); LookFrame($"{rig}_play"); spotClose = 1; }
        else if (step == 2) { Shots.Want($"{rig}_close", 0); LookFrame($"{rig}_close"); spotClose = null; lookCam?.MakeCurrent(); }
        else { Shots.Want($"{rig}_side", 0); LookFrame($"{rig}_side"); }
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
        if (lookFireLight != null)
        {
            lookFireLight.ShadowEnabled = rig != "day";
            // (L1 B4r2: under the rigs the fire's light is the rig's share of it (rigs.json "fires": by day a glow, rule 3; at
            // night strength by day it was the warm half of her shade at the close view, 6.7 m off). --lookdev-fire K scales it.)
            double share = SurvivorUnchained.View.Atmosphere.CelRigs && p.Rig != "" && SurvivorUnchained.Look.Rigs.Current[p.Rig] is { } fr ? fr.FireShare : 1;
            lookFireLight.LightEnergy = 80 / Mathf.Pi * (float)share * (float)Args.Num("lookdev-fire", 1f);
        }
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
        lookItems.Clear();
        void Item(string row, string name, Node3D n) => lookItems.Add((row, name, () => LookBox(n)));
        void Put(Node3D? n, Transform3D at, string what, string row)
        {
            if (n == null) { GD.PushWarning($"lookdev: no {what}"); return; }
            root.AddChild(n);
            n.GlobalTransform = at;
            Item(row, what, n);
        }
        lookItems.Add(("her", "her", () => new Aabb(new Vector3((float)b.Player.X - 0.3f, (float)s.HeightAt(b.Player.X, b.Player.Z), (float)b.Player.Z - 0.2f), new Vector3(0.6f, 1.76f, 0.4f))));
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
                lookWolves.Add(e);
                lookItems.Add(("crowd", $"wolf{lookItems.Count(x => x.Row == "crowd")}", () => new Aabb(new Vector3((float)e.X - 0.6f, (float)s.HeightAt(e.X, e.Z), (float)e.Z - 0.6f), new Vector3(1.2f, 0.85f, 1.2f))));
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
            v.GlobalTransform = new Transform3D(new Basis(Vector3.Up, lookFacing + (i == 0 ? -0.35f : 0.3f)), i == 0 ? W(2.6f, 0.3f) : W(4.5f, -1.1f));
            v.Loop("Idle");
            Item("folk", $"folk{i}", v);
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
        house.GlobalTransform = new Transform3D(basis, W(-7.2f, 7.3f)) * new Transform3D(Basis.Identity, -hc);
        Item("town", "house", house);
        // The square's setts: the town's terrain material, its paint as it lies on the square, on a patch of this ground.
        LookSetts(root, wz, W);
        Put(OwnProps.Piece("barrel"), At(0.1f, 5.3f, 20), "barrel", "town");
        Put(OwnProps.Piece("crate"), At(1.9f, 4.8f, -12), "crate", "town");
        LookLamp(root, "post_lantern", At(3.6f, 4.6f, 180), "town");
        // The wild: a boulder, a spruce, a young alder, pebbles and branches (the arena's own grass round them).
        Put(Dressing.OwnTree("boulder_b"), At(6.8f, 4.1f, 30), "boulder", "wild");
        Put(Dressing.OwnTree("spruce_b"), At(5.7f, 7.4f), "spruce", "wild");
        Put(Dressing.OwnTree("alder_c"), At(3.8f, 7.8f, 0, 0.6f), "alder", "wild");
        Put(Dressing.OwnTree("pebbles_a"), At(5.2f, 2.5f), "pebbles", "wild");
        Put(OwnProps.Piece("branches_a"), At(6.5f, 1.5f, 40), "branches", "wild");
        // The zones' own grass (the arena grows its tussocks only where its paint says, a few here): a round patch of the
        // Low Ford's meadow (Grass.Build, grass_own.gdshader), its paint held open (no setts, mud or blight) and its
        // heights this ground's, so it stands on the arena's soil.
        LookGrass(root, W(Args.Num("lookdev-grass-x", 4.6f), Args.Num("lookdev-grass-y", 3.0f)), Args.Num("lookdev-grass-r", 1.8f));
        // Light sources: the camp's fire (the Low Ford's: 80 over 18 m, three.js's units) and a standing lantern.
        var fat = W(6.1f, -2.9f);
        var fire = Campfire.Build(fat, 1);
        root.AddChild(fire);
        Item("light", "fire", fire);
        lookFireLight = new OmniLight3D
        {
            Name = "LookFire", Position = fat + Vector3.Up * 1.1f, LightColor = new Color("#ff9a48"), LightEnergy = 80 / Mathf.Pi,
            OmniRange = 18, OmniAttenuation = 1.7f, ShadowEnabled = true,
        };
        root.AddChild(lookFireLight);
        LookLamp(root, "lantern_standing", At(1.9f, -2.4f, 200), "light");
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
            Item("spheres", balls[i].Name, mi);
        }
        // The side view: 15 degrees of pitch, 25 degrees round from the play camera's side to its right, across the rows
        // (the layout and this pose were searched together, by numbers, so no row covers another: LookFrame).
        var c = W(0, (float)Args.Num("lookdev-side-y", 7.0f), 1.0f);
        float az = Mathf.DegToRad((float)Args.Num("lookdev-side-az", 25f));
        var dir = (-lookF * Mathf.Cos(az) + lookR * Mathf.Sin(az)).Normalized();
        float d = (float)Args.Num("lookdev-side-dist", 22.2f), pitch = Mathf.DegToRad((float)Args.Num("lookdev-side-pitch", 15f));
        lookCam = new Camera3D { Name = "LookSide", Fov = (float)Args.Num("lookdev-side-fov", 50f), Far = 600 };
        s.AddChild(lookCam);
        lookCam.GlobalPosition = c + dir * d * Mathf.Cos(pitch) + Vector3.Up * d * Mathf.Sin(pitch);
        lookCam.LookAt(c, Vector3.Up);
        // How flat the patch is (the brief: a flat 30 x 20 m of the arena's ground).
        float lo = float.MaxValue, hi = float.MinValue;
        for (float x = -15; x <= 15; x += 1) for (float y = -10; y <= 10; y += 1) { var w = W(x, y); lo = Mathf.Min(lo, w.Y); hi = Mathf.Max(hi, w.Y); }
        GD.Print($"lookdev: stage at {lookP} right {lookR} away {lookF}; house 25 {pieces} pieces; 30x20 m heights {lo:0.00}..{hi:0.00}; rigs {string.Join(",", lookRigs!)}");
    }

    void LookLamp(Node3D root, string kind, Transform3D at, string row)
    {
        if (Lamps.Holder(kind) is not Node3D holder || Lamps.Of(kind) is not Lamps.Info info) { GD.PushWarning($"lookdev: no {kind}"); return; }
        root.AddChild(holder);
        holder.GlobalTransform = at;
        lookLamps.Add(holder);
        lookItems.Add((row, kind, () => LookBox(holder)));
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
        float x0 = -3.2f, x1 = 2.8f, y0 = 3.4f, y1 = 7.4f;
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
        var setts = new MeshInstance3D { Name = "LookSetts", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        root.AddChild(setts);
        lookItems.Add(("town", "setts", () => LookBox(setts)));
    }

    /// <summary>A node's world box: its meshes' boxes merged (a box over 40 m, a culling stand-in, left out).</summary>
    static Aabb? LookBox(Node n)
    {
        Aabb? a = null;
        void Walk(Node x)
        {
            if (x is GeometryInstance3D g and (MeshInstance3D or MultiMeshInstance3D) && g.IsVisibleInTree())
            {
                var bb = g.GlobalTransform * g.GetAabb();
                if (bb.Size.X < 40 && bb.Size.Y < 40 && bb.Size.Z < 40) a = a is Aabb h ? h.Merge(bb) : bb;
            }
            foreach (var c in x.GetChildren()) Walk(c);
        }
        Walk(n);
        return a;
    }

    /// <summary>The frame check, by numbers (lookdev.py check reads these lines): each item's box projected through the
    /// camera now drawing, as a screen rectangle (fractions of the frame), how much of it is inside the frame and how much
    /// of it nearer items' rectangles cover. A frame passes when every item is at least half in frame and at most half
    /// covered (play and side), her rectangle near the middle (play), and her tall in the frame (close).</summary>
    void LookFrame(string tag)
    {
        var c = GetViewport().GetCamera3D();
        if (c == null) { GD.Print($"lookdev-frame {tag} no camera"); return; }
        var vs = GetViewport().GetVisibleRect().Size;
        var rects = new List<(string Row, string Name, Rect2 R, float Depth, bool Behind, float Foot)>();
        Vector2 Scr(Vector3 p) => c.UnprojectPosition(p) / vs;
        foreach (var (row, name, box) in lookItems)
        {
            if (box() is not Aabb bb) { rects.Add((row, name, new Rect2(), 0, true, 0)); continue; }
            float x0 = float.MaxValue, y0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue;
            bool behind = false;
            for (int k = 0; k < 8; k++)
            {
                var p = bb.GetEndpoint(k);
                if (c.IsPositionBehind(p)) { behind = true; continue; }
                var q = c.UnprojectPosition(p);
                x0 = Mathf.Min(x0, q.X / vs.X); x1 = Mathf.Max(x1, q.X / vs.X); y0 = Mathf.Min(y0, q.Y / vs.Y); y1 = Mathf.Max(y1, q.Y / vs.Y);
            }
            // Its foot: a tall piece's (house, tree) the middle of its base on the ground, the rest their whole footprint.
            float foot;
            var ctr = bb.GetCenter();
            if (name is "house" or "spruce" or "alder")
            {
                var bp = new Vector3(ctr.X, (float)scene!.HeightAt(ctr.X, ctr.Z), ctr.Z);
                foot = !c.IsPositionBehind(bp) && new Rect2(0, 0, 1, 1).HasPoint(Scr(bp)) ? 1 : 0;
            }
            else
            {
                var fr = new Rect2(Scr(bb.Position), Vector2.Zero);
                foreach (var e in new[] { new Vector3(bb.Size.X, 0, 0), new Vector3(0, 0, bb.Size.Z), new Vector3(bb.Size.X, 0, bb.Size.Z) }) fr = fr.Expand(Scr(bb.Position + e));
                foot = fr.Intersects(new Rect2(0, 0, 1, 1)) ? fr.Intersection(new Rect2(0, 0, 1, 1)).Area / Mathf.Max(fr.Area, 1e-6f) : 0;
            }
            rects.Add((row, name, x0 > x1 ? new Rect2() : new Rect2(x0, y0, x1 - x0, y1 - y0), c.GlobalPosition.DistanceTo(ctr), behind, foot));
        }
        var frame = new Rect2(0, 0, 1, 1);
        bool close = tag.EndsWith("_close"), play = tag.EndsWith("_play");
        var fails = new List<string>();
        foreach (var it in rects)
        {
            float area = Mathf.Max(it.R.Area, 1e-6f);
            float inside = it.R.Intersects(frame) ? it.R.Intersection(frame).Area / area : 0;
            float hidden = 0;
            foreach (var o in rects)
                if (o.Name != it.Name && o.Name is not ("setts" or "grass" or "branches") && o.Depth < it.Depth - 0.3f && o.R.Intersects(it.R)) hidden += o.R.Intersection(it.R).Area / area;
            hidden = Mathf.Min(hidden, 1);
            var r = it.R;
            GD.Print($"lookdev-frame {tag} {it.Row} {it.Name} rect {r.Position.X:0.000} {r.Position.Y:0.000} {r.End.X:0.000} {r.End.Y:0.000} in {inside:0.00} hidden {hidden:0.00} depth {it.Depth:0.0} foot {it.Foot:0.00}{(it.Behind ? " behind" : "")}");
            if (tag.EndsWith("_play") && lookItems.First(x => x.Name == it.Name).Box() is Aabb wb)
                GD.Print($"lookdev-box {it.Name} {wb.Position.X:0.00} {wb.Position.Y:0.00} {wb.Position.Z:0.00} {wb.Size.X:0.00} {wb.Size.Y:0.00} {wb.Size.Z:0.00}");
            if (close) continue;
            // (the play camera crops what stands tall, as in play: of the house and the trees a third in frame and their
            // base is enough; what lies flat may lie under the props standing on it)
            bool tall = it.Name is "house" or "spruce" or "alder";
            float needIn = play && tall ? 0.3f : 0.5f, maxHid = it.Name is "setts" or "grass" or "branches" or "pebbles" ? 0.8f : 0.5f;
            if (inside < needIn || it.Foot < 0.9f || hidden > maxHid) fails.Add(it.Name);
        }
        var her = rects.First(x => x.Name == "her").R;
        if (play && (Mathf.Abs(her.GetCenter().X - 0.5f) > 0.08f || Mathf.Abs(her.GetCenter().Y - 0.5f) > 0.15f)) fails.Add("her-centre");
        // (the close view is her from the waist or chest up: her head in the top half, centred, and her tall in it)
        if (close && (her.Size.Y < 0.6f || her.Position.Y < 0 || her.Position.Y > 0.5f || Mathf.Abs(her.GetCenter().X - 0.5f) > 0.1f)) fails.Add("her-close");
        // (the held wolves: their state and clip, so a frame shows whether they idle or bite)
        GD.Print($"lookdev-wolves {tag} " + string.Join(" ", lookWolves.Select(w => $"{w.State}/{w.Anim}/{w.AnimT:0.0}/v{Math.Sqrt(w.Vx * w.Vx + w.Vz * w.Vz):0.00}")));
        GD.Print($"lookdev-frame {tag} {(fails.Count == 0 ? "PASS" : "FAIL " + string.Join(",", fails))} ({rects.Count} items)");
    }

    /// <summary>A round patch of the zones' own meadow grass at <paramref name="at"/> (radius r): the Low Ford's kind built as
    /// the zones build it, its paint held open and its heights this ground's.</summary>
    void LookGrass(Node3D root, Vector3 at, float r)
    {
        var lf = new ZoneData("lowford");
        var g = Grass.Build(lf, new Vector2(at.X, at.Z), r);
        if (g.Multimesh?.Mesh?.SurfaceGetMaterial(0) is not ShaderMaterial mat) { GD.PushWarning("lookdev: no meadow grass"); return; }
        ImageTexture One(Color c) { var im = Image.CreateEmpty(4, 4, false, Image.Format.Rgbaf); im.Fill(c); return ImageTexture.CreateFromImage(im); }
        mat.SetShaderParameter("splat", One(new Color(0, 0, 0, 0)));
        mat.SetShaderParameter("paint_mask", One(new Color(0, 0, 0, 0)));
        mat.SetShaderParameter("expo_tex", One(new Color(1, 1, 1, 1)));
        mat.SetShaderParameter("meadow_amt", 0f);
        var hf = scene!.Data.Ground;
        var hb = new byte[hf.Heights.Length * 4];
        Buffer.BlockCopy(hf.Heights, 0, hb, 0, hb.Length);
        mat.SetShaderParameter("heights", ImageTexture.CreateFromImage(Image.CreateFromData(hf.Res, hf.Res, false, Image.Format.Rf, hb)));
        mat.SetShaderParameter("h_size", (float)hf.Size);
        mat.SetShaderParameter("h_res", (float)hf.Res);
        g.Name = "LookGrass";
        root.AddChild(g);
        lookItems.Add(("wild", "grass", () => new Aabb(at - new Vector3(r, 0, r), new Vector3(2 * r, 0.5f, 2 * r))));
        GD.Print($"lookdev: grass patch at {at} r {r}: {g.Multimesh!.InstanceCount} cells");
    }
}
