using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Our own set-dressing props (tools/assets/env_props.py, art/world/props): bedrolls, a pack,
/// a chest, a crate, a barrel, sitting logs, a broken wagon, each one GLB (and its LOD1 over 1k
/// triangles) drawn with the one shared painted atlas (env_props_atlas.py: albedo, normal, ORM),
/// its palette and baked occlusion in its vertex colours.
///
/// Where they stand is a zone's data, res://data/zones/ZONE/props_own.json (its "_doc"):
/// "pieces" swaps a kit piece of props.json for a preset wherever it stands (fitted to the kit
/// piece's box), "keep" names places where the kit piece stays; "place" stands a preset at a place
/// (or along a line, a log from a to b), hiding the web game's blocked-out meshes there ("hide") and baring the grass
/// under it ("bare": radius, and how far out the grass thins, times it; with the fires, the first four);
/// "lamps" gives a lamp holder's light its own colour, energy and reach (by its glow node); "nudge" [x, z, dx, dz, degrees]
/// shifts and turns the preset standing in for a kit piece at x, z (a chest set off a log's end); "drop" names landmarks
/// that go (the web game's unlit standing lantern by the camp, which read as an iron cage); "flora_move" [x, z, dx, dz]
/// shifts a tree of the zone's flora (or [x, z] drops it), read where the flora is loaded (ZoneData).
/// </summary>
public static class OwnProps
{
    public const string Dir = "res://art/world/props";
    /// <summary>--props-lod M: where a prop's LOD1 takes over (m from the camera).</summary>
    public static readonly float Lod1From = SurvivorUnchained.Args.Num("props-lod", 22f);

    public sealed record Hide(Vector2 At, float R, float MaxH);
    public sealed record Place(string Preset, Vector2 At, float Rot, float Scale, float Y, Vector3? A, Vector3? B, float R, Hide? Hide, Vector2? Bare);
    /// <summary>(Day: lf5p, its light's share when it is not night: the Low Ford lamps' pools showed in the dawn's daylight; 1 as before.)</summary>
    public sealed record Lamp(Color? Color, float Energy, float Range, float Att, float Day = 1, float Spec = -1);
    public sealed record Nudge(Vector2 At, Vector2 By, float Turn);
    /// <summary>A KayKit piece's own stand-ins (one per copy, by the landmark's number: Preset is the one chosen),
    /// whether the made piece stays under them (Over), and their scale in the piece's frame (a tree of ours).</summary>
    public sealed record KitEntry(string[] Presets, bool Over, float Scale, string Preset = "");
    public sealed record Zone(Dictionary<string, string> Pieces, List<Vector2> Keep, List<Place> Places, Dictionary<string, Lamp> Lamps, List<Nudge>? Nudges = null, List<string>? Drop = null,
        Dictionary<string, KitEntry>? Kits = null, List<Vector2>? NoGutter = null, List<Vector2>? Lit = null, List<(Vector2 At, Vector2? By)>? FloraMove = null, Lamp? LitLight = null,
        List<Vector3>? Clear = null);

    static readonly Dictionary<string, Zone?> zones = new();
    static Dictionary<string, Aabb>? boxes;
    static readonly Dictionary<string, Vector2> axes = new();
    /// <summary>(E8 r2) A preset's own LOD1 distance (props.json "lod_m": the gate's towers and gatehouse, so the play
    /// camera, about 30 m off, sees their joints and bevels, not the decimated LOD1's smooth facets).</summary>
    static readonly Dictionary<string, float> lods = new();
    /// <summary>(E8 later) Presets that cast no shadow (props.json "no_shadow": the camp's ground dressing, what the
    /// open gate shows beyond it).</summary>
    static readonly HashSet<string> unshadowed = new();
    /// <summary>(E8 later r2) Presets with grime runs (props.json "runs": top, drop, len, k, ring): drawn by the runs
    /// material on the faces their vertex alpha flags.</summary>
    static readonly Dictionary<string, (float Top, float Drop, float Len, float K, bool Ring)> runs = new();
    static OrmMaterial3D? mat;

    /// <summary>A zone's own-props data, or null if it has none.</summary>
    public static Zone? For(string zone)
    {
        if (zones.TryGetValue(zone, out var hit)) return hit;
        // --props-own-off: the kit's and the web game's pieces as they were (before/after measures).
        if (SurvivorUnchained.Args.Has("props-own-off")) return zones[zone] = null;
        var path = $"res://data/zones/{zone}/props_own.json";
        Zone? z = null;
        if (FileAccess.FileExists(path))
        {
            using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(path));
            var r = doc.RootElement;
            var pieces = new Dictionary<string, string>();
            if (r.TryGetProperty("pieces", out var ps)) foreach (var p in ps.EnumerateObject()) pieces[p.Name] = p.Value.GetString()!;
            var keep = new List<Vector2>();
            if (r.TryGetProperty("keep", out var ks)) foreach (var k in ks.EnumerateArray()) keep.Add(new Vector2(k[0].GetSingle(), k[1].GetSingle()));
            var places = new List<Place>();
            if (r.TryGetProperty("place", out var pl))
                foreach (var p in pl.EnumerateArray())
                {
                    float F(string n, float d) => p.TryGetProperty(n, out var v) ? v.GetSingle() : d;
                    Vector3? V(string n) => p.TryGetProperty(n, out var v) ? new Vector3(v[0].GetSingle(), v[1].GetSingle(), v[2].GetSingle()) : null;
                    Hide? hide = null;
                    if (p.TryGetProperty("hide", out var h))
                        hide = new Hide(new Vector2(h[0].GetSingle(), h[1].GetSingle()), h[2].GetSingle(), h.GetArrayLength() > 3 ? h[3].GetSingle() : 1.2f);
                    Vector2? bare = p.TryGetProperty("bare", out var br) ? new Vector2(br[0].GetSingle(), br[1].GetSingle()) : null;
                    places.Add(new Place(p.GetProperty("preset").GetString()!, new Vector2(F("x", 0), F("z", 0)), F("rot", 0), F("scale", 1), F("y", 0), V("a"), V("b"), F("r", 0), hide, bare));
                }
            var lamps = new Dictionary<string, Lamp>();
            if (r.TryGetProperty("lamps", out var ls))
                foreach (var l in ls.EnumerateObject())
                {
                    float F(string n, float d) => l.Value.TryGetProperty(n, out var v) ? v.GetSingle() : d;
                    lamps[l.Name] = new Lamp(l.Value.TryGetProperty("color", out var c) ? new Color(c.GetString()!) : null, F("energy", 1), F("range", 0), F("att", 0), F("day", 1), F("spec", -1));
                }
            var nudges = new List<Nudge>();
            if (r.TryGetProperty("nudge", out var nu))
                foreach (var n in nu.EnumerateArray())
                    nudges.Add(new Nudge(new Vector2(n[0].GetSingle(), n[1].GetSingle()), new Vector2(n[2].GetSingle(), n[3].GetSingle()), Mathf.DegToRad(n[4].GetSingle())));
            var drop = new List<string>();
            if (r.TryGetProperty("drop", out var dr)) foreach (var d in dr.EnumerateArray()) drop.Add(d.GetString()!);
            var kits = new Dictionary<string, KitEntry>();
            if (r.TryGetProperty("kits", out var kt))
                foreach (var k in kt.EnumerateObject())
                {
                    var v = k.Value;
                    static string[] Names(JsonElement e) => e.ValueKind == JsonValueKind.Array ? e.EnumerateArray().Select(x => x.GetString()!).ToArray() : [e.GetString()!];
                    kits[k.Name] = v.ValueKind == JsonValueKind.Object
                        ? new KitEntry(Names(v.GetProperty("preset")), v.TryGetProperty("over", out var o) && o.GetBoolean(), v.TryGetProperty("scale", out var sc) ? sc.GetSingle() : 1f)
                        : new KitEntry(Names(v), false, 1f);
                }
            // no_gutter: [x, z] of box colliders that are heaps, not wall or building bases (GroundPaint lays no wet gutter round them).
            var noGut = new List<Vector2>();
            if (r.TryGetProperty("no_gutter", out var ng)) foreach (var g in ng.EnumerateArray()) noGut.Add(new Vector2(g[0].GetSingle(), g[1].GetSingle()));
            // lit: [x, z] of wall torches the web game left without a glow (no zone light): each burns with a flame and light of its own.
            var lit = new List<Vector2>();
            if (r.TryGetProperty("lit", out var lt)) foreach (var g in lt.EnumerateArray()) lit.Add(new Vector2(g[0].GetSingle(), g[1].GetSingle()));
            // flora_move: [x, z, dx, dz] shifts the flora copy whose trunk stands within half a metre of x, z (its ground height
            // follows); [x, z] alone drops it (a canopy thinned where it shades a place: the post's dawn sun, E7b).
            var fm = new List<(Vector2 At, Vector2? By)>();
            if (r.TryGetProperty("flora_move", out var fmv))
                foreach (var m in fmv.EnumerateArray())
                    fm.Add((new Vector2(m[0].GetSingle(), m[1].GetSingle()), m.GetArrayLength() > 3 ? new Vector2(m[2].GetSingle(), m[3].GetSingle()) : null));
            // lit_light: those torches' own light (color, energy times the kit torch's, range, att), so it pools on the ground under them.
            Lamp? litLight = null;
            if (r.TryGetProperty("lit_light", out var ll))
            {
                float F(string n, float d) => ll.TryGetProperty(n, out var v) ? v.GetSingle() : d;
                litLight = new Lamp(ll.TryGetProperty("color", out var c) ? new Color(c.GetString()!) : null, F("energy", 1), F("range", 0), F("att", 0));
            }
            // clear: [x, z, r] where the kit's small props (props/*) go (E9d: the web game's wares on the stalls our own stalls carry)
            var clear = new List<Vector3>();
            if (r.TryGetProperty("clear", out var cl)) foreach (var c in cl.EnumerateArray()) clear.Add(new Vector3(c[0].GetSingle(), c[1].GetSingle(), c[2].GetSingle()));
            z = new Zone(pieces, keep, places, lamps, nudges, drop, kits, noGut, lit, fm, litLight, clear);
        }
        zones[zone] = z;
        return z;
    }

    /// <summary>The own stand-in for a KayKit piece (PACK/NAME) and its landmark number N (kk-PACK-NAME-N), or null to keep
    /// the made one (Pieces). The copies take the entry's presets in turn by N.</summary>
    public static KitEntry? Kit(Zone z, string id, int n)
    {
        if (z.Kits == null || !z.Kits.TryGetValue(id, out var e) || e.Presets.Length == 0) return null;
        return e with { Preset = e.Presets[n % e.Presets.Length] };
    }

    /// <summary>A kit stand-in's node in the kit piece's frame, unscaled (the presets are built in the kit's units),
    /// or null if it was never built. "flora:NAME" is one of our own trees (Dressing.OwnTree).</summary>
    public static Node3D? KitPiece(KitEntry e)
    {
        var n = e.Preset.StartsWith("flora:") ? Dressing.OwnTree(e.Preset[6..]) : Piece(e.Preset);
        if (n != null && e.Scale != 1f) n.Scale = Vector3.One * e.Scale;
        return n;
    }

    /// <summary>Whether a kit piece at a place is cleared away (props_own.json "clear": only the small props, props/*).</summary>
    public static bool Cleared(Zone z, string id, Vector3 at)
    {
        if (z.Clear is not { Count: > 0 } cl || !id.StartsWith("props/")) return false;
        foreach (var c in cl) if (new Vector2(at.X - c.X, at.Z - c.Y).Length() < c.Z) return true;
        return false;
    }

    /// <summary>The preset standing in for a kit piece at a place, or null to keep the kit's.</summary>
    public static string? Swap(Zone z, string id, Vector3 at)
    {
        if (!z.Pieces.TryGetValue(id, out var preset) || !ResourceLoader.Exists($"{Dir}/{preset}.glb")) return null;
        foreach (var k in z.Keep) if (new Vector2(at.X - k.X, at.Z - k.Y).Length() < 0.5f) return null;
        return preset;
    }

    /// <summary>Where a swapped piece at a kit place stands once nudged (its kit transform if no nudge names the place).</summary>
    public static Transform3D Nudged(Zone z, Transform3D at)
    {
        foreach (var n in z.Nudges ?? new())
            if (new Vector2(at.Origin.X - n.At.X, at.Origin.Z - n.At.Y).Length() < 0.5f)
                return new Transform3D(new Basis(Vector3.Up, n.Turn) * at.Basis, at.Origin + new Vector3(n.By.X, 0, n.By.Y));
        return at;
    }

    /// <summary>A preset's box as built (art/world/props/props.json "box").</summary>
    public static Aabb? Box(string preset)
    {
        if (boxes == null)
        {
            boxes = new();
            var f = $"{Dir}/props.json";
            if (FileAccess.FileExists(f))
            {
                using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(f));
                foreach (var p in doc.RootElement.EnumerateObject())
                {
                    var b = p.Value.GetProperty("box");
                    var lo = new Vector3(b[0].GetSingle(), b[1].GetSingle(), b[2].GetSingle());
                    boxes[p.Name] = new Aabb(lo, new Vector3(b[3].GetSingle(), b[4].GetSingle(), b[5].GetSingle()) - lo);
                    if (p.Value.TryGetProperty("axis", out var ax)) axes[p.Name] = new Vector2(ax[0].GetSingle(), ax[1].GetSingle());
                    if (p.Value.TryGetProperty("lod_m", out var lm)) lods[p.Name] = lm.GetSingle();
                    if (p.Value.TryGetProperty("no_shadow", out var ns) && ns.GetBoolean()) unshadowed.Add(p.Name);
                    if (p.Value.TryGetProperty("runs", out var rn))
                        runs[p.Name] = (rn.GetProperty("top").GetSingle(), rn.GetProperty("drop").GetSingle(), rn.GetProperty("len").GetSingle(),
                            rn.GetProperty("k").GetSingle(), rn.GetProperty("ring").GetBoolean());
                }
            }
        }
        return boxes.TryGetValue(preset, out var a) ? a : null;
    }

    /// <summary>--props-plain: the props without their atlas (the vertex colours alone), for pictures.</summary>
    static readonly bool Plain = SurvivorUnchained.Args.Has("props-plain");

    /// <summary>The one material every prop shares: the atlas, its normals and ORM, the vertex colours' tint.</summary>
    public static Material Material
    {
        get
        {
            if (mat != null) return mat;
            mat = new OrmMaterial3D
            {
                ResourceName = "own_props",
                VertexColorUseAsAlbedo = true,
                TextureFilter = BaseMaterial3D.TextureFilterEnum.LinearWithMipmapsAnisotropic,
            };
            if (!Plain)
            {
                mat.AlbedoTexture = GD.Load<Texture2D>($"{Dir}/props_albedo.jpg");
                mat.NormalEnabled = true;
                mat.NormalTexture = GD.Load<Texture2D>($"{Dir}/props_normal.png");
                mat.NormalScale = SurvivorUnchained.Args.Num("props-normal", 1f);
                mat.OrmTexture = GD.Load<Texture2D>($"{Dir}/props_orm.png");
                mat.AOEnabled = false;
            }
            else mat.Roughness = 0.9f;
            return mat;
        }
    }

    static ShaderMaterial? veil;
    static Color veilCol = new(0.37f, 0.33f, 0.41f);
    /// <summary>(E8 later r2) The air sheet's colour: the sky's horizon (Atmosphere, on every change of light).</summary>
    public static void SkyHaze(Color horizon) { veilCol = horizon; veil?.SetShaderParameter("haze_col", horizon); }
    /// <summary>(E8 later r2) "haze_veil" (props_own.json "place"): a 6 x 6.5 m sheet of air facing +z, its foot on the
    /// ground (shaders/haze_veil.gdshader; --haze-veil its share, 0.048), no shadow.</summary>
    static Node3D Veil()
    {
        veil ??= new ShaderMaterial { ResourceName = "haze_veil", Shader = GD.Load<Shader>("res://shaders/haze_veil.gdshader") };
        veil.SetShaderParameter("haze_col", veilCol);
        veil.SetShaderParameter("amount", SurvivorUnchained.Args.Num("haze-veil", 0.048f));
        var root = new Node3D { Name = "own_haze_veil" };
        root.AddChild(new MeshInstance3D
        {
            Name = "haze_veil", Mesh = new QuadMesh { Size = new Vector2(6f, 6.5f) }, MaterialOverride = veil,
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Position = new Vector3(0, 2.75f, 0),
        });
        return root;
    }

    static ShaderMaterial? runsMat;
    /// <summary>(E8 later r2) The prop material plus grime runs and a damp foot per pixel (shaders/props_runs.gdshader).</summary>
    static Material RunsMat
    {
        get
        {
            if (runsMat != null) return runsMat;
            runsMat = new ShaderMaterial { ResourceName = "own_props_runs", Shader = GD.Load<Shader>("res://shaders/props_runs.gdshader") };
            runsMat.SetShaderParameter("albedo_tex", GD.Load<Texture2D>($"{Dir}/props_albedo.jpg"));
            runsMat.SetShaderParameter("normal_tex", GD.Load<Texture2D>($"{Dir}/props_normal.png"));
            runsMat.SetShaderParameter("orm_tex", GD.Load<Texture2D>($"{Dir}/props_orm.png"));
            runsMat.SetShaderParameter("normal_scale", SurvivorUnchained.Args.Num("props-normal", 1f));
            runsMat.SetShaderParameter("moss_k", SurvivorUnchained.Args.Num("props-moss-foot", 1f));
            return runsMat;
        }
    }

    static ShaderMaterial? glow;
    /// <summary>(E8 later) Lit panes: the vertex colour times --props-glow (2), unshaded (the zone's fog still on them).</summary>
    static Material Glow
    {
        get
        {
            if (glow != null) return glow;
            glow = new ShaderMaterial { ResourceName = "own_glow", Shader = new Shader { Code = "shader_type spatial; render_mode unshaded; uniform float energy = 2.0; void fragment() { ALBEDO = COLOR.rgb * energy; }" } };
            glow.SetShaderParameter("energy", SurvivorUnchained.Args.Num("props-glow", 2f));
            return glow;
        }
    }

    static ShaderMaterial? far;
    static bool farShown = true;
    /// <summary>(E8 r2) Whether the far castle draws (Atmosphere.Set: only under a night sky).</summary>
    public static void FarShown(bool on) { farShown = on; far?.SetShaderParameter("shown", on ? 1f : 0f); }
    /// <summary>(E8) The far castle's (C01 s8a, 265 m off): the props atlas times the vertex colours, the zone's fog
    /// off and its own haze in its place (Godot's fog at that range left a flat fog-coloured shape, its windows gone),
    /// the lit windows (vertex alpha 0) glowing their own colour (shaders/far_castle.gdshader).</summary>
    public static Material Far
    {
        get
        {
            if (far != null) return far;
            far = new ShaderMaterial { ResourceName = "far_castle", Shader = GD.Load<Shader>("res://shaders/far_castle.gdshader") };
            far.SetShaderParameter("albedo_tex", GD.Load<Texture2D>($"{Dir}/props_albedo.jpg"));
            far.SetShaderParameter("shown", farShown ? 1f : 0f);
            return far;
        }
    }

    static StandardMaterial3D? paper;
    /// <summary>(E9d) The notices' sheet (tools/assets/env_notice_paper.py), times the vertex colours.</summary>
    static Material Paper => paper ??= new StandardMaterial3D
    {
        ResourceName = "notice_paper", VertexColorUseAsAlbedo = true, Roughness = 0.95f,
        AlbedoTexture = GD.Load<Texture2D>($"{Dir}/notice_paper.png"), TextureFilter = BaseMaterial3D.TextureFilterEnum.LinearWithMipmapsAnisotropic,
    };

    static StandardMaterial3D? water;
    /// <summary>(E9d r3) A trough's water (env_props.py trough_water_mesh, UVs in metres): a grey-blue sky value, glossy, in
    /// broad soft ripples (a smooth noise as its normal map, about 25 cm across); the canvas weave read as woven mesh.</summary>
    static Material Water => water ??= new StandardMaterial3D
    {
        ResourceName = "trough_water", AlbedoColor = new Color("#485a68"), Roughness = 0.14f, MetallicSpecular = 0.45f,
        NormalEnabled = true, NormalScale = 0.55f,
        NormalTexture = new NoiseTexture2D
        {
            Width = 256, Height = 256, Seamless = true, AsNormalMap = true, BumpStrength = 3f,
            Noise = new FastNoiseLite { NoiseType = FastNoiseLite.NoiseTypeEnum.Simplex, Frequency = 0.012f, FractalOctaves = 2, Seed = 5 },
        },
        Uv1Scale = new Vector3(1.2f, 1.2f, 1f),
        TextureFilter = BaseMaterial3D.TextureFilterEnum.LinearWithMipmapsAnisotropic,
    };

    static StandardMaterial3D? cloth;
    /// <summary>(E9d) The stalls' canvas (tools/assets/env_canvas_tile.py: a tiling linen weave, 0.5 m a tile), times the
    /// vertex colours (the dye, stripes, fading and soiling env_props.py bakes).</summary>
    static Material Cloth => cloth ??= new StandardMaterial3D
    {
        ResourceName = "stall_canvas", VertexColorUseAsAlbedo = true, Roughness = 0.93f,
        AlbedoTexture = GD.Load<Texture2D>($"{Dir}/canvas_tile.png"), NormalEnabled = true, NormalTexture = GD.Load<Texture2D>($"{Dir}/canvas_tile_n.png"),
        NormalScale = 0.6f, TextureFilter = BaseMaterial3D.TextureFilterEnum.LinearWithMipmapsAnisotropic,
        // (light through the canvas from above: its underside not black at the close camera)
        BacklightEnabled = true, Backlight = new Color(0.22f, 0.2f, 0.17f),
    };

    /// <summary>--props-skip a,b,...: presets left out (the kit's piece keeps its place), for bisecting.</summary>
    static readonly HashSet<string> Skip = new((SurvivorUnchained.Args.Get("props-skip") ?? "").Split(',', System.StringSplitOptions.RemoveEmptyEntries));

    /// <summary>A preset's node (its LOD0 and LOD1 by distance, shadows on), or null if it was never built.</summary>
    public static Node3D? Piece(string preset)
    {
        if (preset == "haze_veil") return Veil();
        var path = $"{Dir}/{preset}.glb";
        if (!ResourceLoader.Exists(path) || Skip.Contains(preset)) return null;
        var root = GD.Load<PackedScene>(path).Instantiate<Node3D>();
        root.Name = "own_" + preset;
        bool hasLod = false;
        foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false)) if (n.Name.ToString().EndsWith("_LOD1")) hasLod = true;
        // (E9d) clutter under half a metre casts no shadow (the shadow-draw budget)
        bool small = Box(preset) is Aabb bx && bx.Size.Y < 0.5f || unshadowed.Contains(preset);
        float lodFrom = lods.TryGetValue(preset, out var lm) && !SurvivorUnchained.Args.Has("props-lod") ? lm : Lod1From;
        // (E8) a preset with a shadow proxy (<preset>_shadow, a few boxes): the proxy alone casts its shadow
        bool proxy = false;
        foreach (var n in root.FindChildren("*_shadow", "MeshInstance3D", true, false)) proxy = true;
        foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D m || m.Mesh == null) continue;
            if (m.Name.ToString().EndsWith("_shadow")) { m.MaterialOverride = Material; m.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly; continue; }
            // (E8) the far castle: its own material (the atlas, its own haze, its lit windows), no shadow, no LOD
            if (m.Name.ToString().EndsWith("_far"))
            {
                m.MaterialOverride = Far; m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                GD.Print($"(E8) far {m.Name}: cast_shadow {m.CastShadow}, one draw ({m.Mesh.GetSurfaceCount()} surface)");
                continue;
            }
            // (E9d) the notices: their own paper sheet (notice_paper.png), no shadow, no LOD (a few hundred triangles)
            if (m.Name.ToString().EndsWith("_paper")) { m.MaterialOverride = Paper; m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; continue; }
            // (E9d) a stall's canvas: its own tiling sheet (canvas_tile.png), casting the stall's shade, no LOD
            if (m.Name.ToString().EndsWith("_cloth")) { m.MaterialOverride = Cloth; continue; }
            // (E8 later) a near prop's lit panes (a window, a lantern's glass): their colour as it is, unshaded, in the fog
            if (m.Name.ToString().EndsWith("_glow")) { m.MaterialOverride = Glow; m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; continue; }
            if (m.Name.ToString().EndsWith("_water")) { m.MaterialOverride = Water; m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; continue; }
            m.MaterialOverride = Material;
            if (!Plain && runs.TryGetValue(preset, out var rs) && !SurvivorUnchained.Args.Has("props-no-runs"))
            {
                m.MaterialOverride = RunsMat;
                m.SetInstanceShaderParameter("run_top", rs.Top);
                m.SetInstanceShaderParameter("run_drop", rs.Drop);
                m.SetInstanceShaderParameter("run_len", rs.Len);
                m.SetInstanceShaderParameter("run_k", rs.K);
                m.SetInstanceShaderParameter("run_ring", rs.Ring ? 1f : 0f);
            }
            m.CastShadow = small || proxy ? GeometryInstance3D.ShadowCastingSetting.Off : GeometryInstance3D.ShadowCastingSetting.On;
            if (!hasLod) continue;
            if (m.Name.ToString().EndsWith("_LOD1")) m.VisibilityRangeBegin = lodFrom;
            else m.VisibilityRangeEnd = lodFrom;
        }
        return root;
    }

    /// <summary>A preset scaled evenly to a kit piece's height, stood on its floor over the middle of its footprint
    /// (in the kit piece's frame), or null if it was never built.</summary>
    public static Node3D? Fitted(string preset, Aabb kit)
    {
        if (Piece(preset) is not Node3D p || Box(preset) is not Aabb b || b.Size.Y < 1e-4f) return null;
        float k = kit.Size.Y / b.Size.Y;
        var mid = b.GetCenter();
        p.Scale = Vector3.One * k;
        p.Position = new Vector3(kit.GetCenter().X - mid.X * k, kit.Position.Y - b.Position.Y * k, kit.GetCenter().Z - mid.Z * k);
        var holder = new Node3D { Name = preset };
        holder.AddChild(p);
        return holder;
    }

    /// <summary>The zone's placed props, the blocked-out meshes they replace hidden among the landmarks (not yet in the tree).</summary>
    public static Node3D Dress(ZoneData zone, Zone z, Node3D landmarks)
    {
        var root = new Node3D { Name = "OwnProps" };
        foreach (var name in z.Drop ?? new())
            if (landmarks.FindChild(name, true, false) is Node3D gone) gone.Visible = false;
        foreach (var p in z.Places)
        {
            if (p.Hide is Hide h) HideNear(landmarks, h, zone);
            if (Piece(p.Preset) is not Node3D piece) continue;
            if (p.A is Vector3 a && p.B is Vector3 b && Box(p.Preset) is Aabb box)
            {
                // Along a line (a log from a to b, its axis at their height): the preset's long axis (x) on it, its radius r.
                var d = b - a;
                // (a log's own axis and radius where props.json gives them, so a stub or burl over the top doesn't shrink it)
                var axis = axes.TryGetValue(p.Preset, out var av) ? av : new Vector2(box.GetCenter().Y, box.Size.Y / 2);
                float len = d.Length(), k = p.R > 0 ? p.R / axis.Y : 1;
                var along = d / len;
                var side = Vector3.Up.Cross(along).Normalized();
                var basis = new Basis(along * (len / box.Size.X), Vector3.Up * k, -side * k);
                var mid = (a + b) / 2;
                // the preset's axis is at its box's middle height: put it on the line
                piece.Transform = new Transform3D(basis, mid - basis * new Vector3(0, axis.X, 0));
            }
            else
            {
                float y = zone.HeightAt(p.At.X, p.At.Y) + p.Y;
                piece.Transform = new Transform3D(new Basis(Vector3.Up, p.Rot).Scaled(Vector3.One * p.Scale), new Vector3(p.At.X, y, p.At.Y));
            }
            root.AddChild(piece);
        }
        return root;
    }

    /// <summary>Hides the web game's own meshes (not its kit pieces) whose middles stand within r of a place and
    /// whose tops stand under max metres over the ground.</summary>
    static void HideNear(Node3D landmarks, Hide h, ZoneData zone)
    {
        float g = zone.HeightAt(h.At.X, h.At.Y);
        int n = 0;
        foreach (var node in landmarks.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (node is not MeshInstance3D mi || InKit(mi, landmarks)) continue;
            var t = Transform3D.Identity;
            for (Node? q = mi; q != null && q != landmarks; q = q.GetParent()) if (q is Node3D q3) t = q3.Transform * t;
            var box = t * mi.GetAabb();
            var c = box.GetCenter();
            if (new Vector2(c.X - h.At.X, c.Z - h.At.Y).Length() < h.R && box.End.Y < g + h.MaxH) { mi.Visible = false; n++; }
        }
        if (SurvivorUnchained.Args.Has("props-debug")) GD.Print($"own props: hid {n} meshes near {h.At}");
    }

    static bool InKit(Node n, Node top)
    {
        for (var p = n.GetParent(); p != null && p != top; p = p.GetParent()) if (p.Name.ToString().StartsWith("kk-")) return true;
        return false;
    }
}
