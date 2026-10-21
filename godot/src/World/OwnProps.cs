using System.Collections.Generic;
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
/// that go (the web game's unlit standing lantern by the camp, which read as an iron cage).
/// </summary>
public static class OwnProps
{
    public const string Dir = "res://art/world/props";
    /// <summary>--props-lod M: where a prop's LOD1 takes over (m from the camera).</summary>
    public static readonly float Lod1From = SurvivorUnchained.Args.Num("props-lod", 22f);

    public sealed record Hide(Vector2 At, float R, float MaxH);
    public sealed record Place(string Preset, Vector2 At, float Rot, float Scale, float Y, Vector3? A, Vector3? B, float R, Hide? Hide, Vector2? Bare);
    public sealed record Lamp(Color? Color, float Energy, float Range, float Att);
    public sealed record Nudge(Vector2 At, Vector2 By, float Turn);
    public sealed record Zone(Dictionary<string, string> Pieces, List<Vector2> Keep, List<Place> Places, Dictionary<string, Lamp> Lamps, List<Nudge>? Nudges = null, List<string>? Drop = null);

    static readonly Dictionary<string, Zone?> zones = new();
    static Dictionary<string, Aabb>? boxes;
    static readonly Dictionary<string, Vector2> axes = new();
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
                    lamps[l.Name] = new Lamp(l.Value.TryGetProperty("color", out var c) ? new Color(c.GetString()!) : null, F("energy", 1), F("range", 0), F("att", 0));
                }
            var nudges = new List<Nudge>();
            if (r.TryGetProperty("nudge", out var nu))
                foreach (var n in nu.EnumerateArray())
                    nudges.Add(new Nudge(new Vector2(n[0].GetSingle(), n[1].GetSingle()), new Vector2(n[2].GetSingle(), n[3].GetSingle()), Mathf.DegToRad(n[4].GetSingle())));
            var drop = new List<string>();
            if (r.TryGetProperty("drop", out var dr)) foreach (var d in dr.EnumerateArray()) drop.Add(d.GetString()!);
            z = new Zone(pieces, keep, places, lamps, nudges, drop);
        }
        zones[zone] = z;
        return z;
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

    /// <summary>A preset's node (its LOD0 and LOD1 by distance, shadows on), or null if it was never built.</summary>
    public static Node3D? Piece(string preset)
    {
        var path = $"{Dir}/{preset}.glb";
        if (!ResourceLoader.Exists(path)) return null;
        var root = GD.Load<PackedScene>(path).Instantiate<Node3D>();
        root.Name = "own_" + preset;
        bool hasLod = false;
        foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false)) if (n.Name.ToString().EndsWith("_LOD1")) hasLod = true;
        foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D m || m.Mesh == null) continue;
            m.MaterialOverride = Material;
            m.CastShadow = GeometryInstance3D.ShadowCastingSetting.On;
            if (!hasLod) continue;
            if (m.Name.ToString().EndsWith("_LOD1")) m.VisibilityRangeBegin = Lod1From;
            else m.VisibilityRangeEnd = Lod1From;
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
