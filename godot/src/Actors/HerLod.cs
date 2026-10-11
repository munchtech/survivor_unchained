using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her gameplay model (tools/assets/heroine_lod.py: heroine_outfit_SET_lod.gltf): her outfit and the body under it
/// with what nothing can see removed and simplified to a millimetre (half that over her bust, hips and butt), and one
/// welded mesh, simplified further, for her shadow. Drawn only in play with the camera beyond Far (the play camera
/// stands 22 to 34 m off): at the title, in creation, in conversations, at chests, under any held camera and in
/// every cinematic she is the full model (the owner, 11 October 2026: "we worked very hard on these models so they
/// show there no matter what"). Her head, face and hair are always her own.
///
/// The gameplay meshes wear the full meshes' own materials (copied each frame, so a dye, a paint or a ghost's
/// overlay laid on the full model is on them too), all but fur, which grows fewer shells (FurShells).
/// --lod off: never; --lod on: always (pictures side by side); --lod mesh: always, but her shadow from the full
/// model (to tell the two apart); default: as above.
/// </summary>
public partial class HerLod : Node
{
    /// <summary>Set by the game each frame: play, with no conversation, overlay, held camera or cinematic.</summary>
    public static bool InPlay;
    /// <summary>The camera's distance (m) beyond which she is drawn from her gameplay model, and within which she is
    /// drawn whole again (a conversation brings the camera to 12.5 m, a chest to 12-13.5).</summary>
    public const float Far = 18f, Near = 16f;
    /// <summary>Fur shells at range (a pile of 8 mm is under a pixel at the play camera; the full model grows 20).</summary>
    public const int FurShells = 6;
    static readonly string Mode = Args.Get("lod") ?? "auto";

    readonly List<(MeshInstance3D Full, MeshInstance3D Lod, int[] Map, bool[] Own)> pairs = new();
    readonly List<MeshInstance3D> fulls = new();
    MeshInstance3D? shadow, body;
    Skeleton3D skel = null!;
    bool? on;

    /// <summary>Her gameplay model for an outfit, laid on her skeleton beside the full one (People.HerOutfit, after
    /// the outfit's pieces and materials are on her).</summary>
    public static void Attach(People.Person p, string set)
    {
        if (Mode == "off") return;
        var file = $"res://art/people/heroine_outfit_{set}_lod.gltf";
        if (!ResourceLoader.Exists(file)) return;
        p.Skeleton.GetNodeOrNull<HerLod>("HerLod")?.Remove();
        var lod = new HerLod { Name = "HerLod", skel = p.Skeleton };
        var scene = GD.Load<PackedScene>(file).Instantiate<Node3D>();
        var from = (Skeleton3D)scene.FindChildren("*", "Skeleton3D", true, false)[0];
        var children = p.Skeleton.GetChildren().OfType<MeshInstance3D>().ToList();
        foreach (var mi in from.GetChildren().OfType<MeshInstance3D>().ToList())
        {
            var name = mi.Name.ToString();
            if (!name.StartsWith("lod_")) continue;
            from.RemoveChild(mi);
            mi.Owner = null;
            p.Skeleton.AddChild(mi);
            mi.Skeleton = "..";
            mi.Layers = 2;
            mi.Visible = false;
            if (name == "lod_shadow")
            {
                mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly;
                lod.shadow = mi;
                continue;
            }
            mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
            var full = name == "lod_body" ? children.FirstOrDefault(c => c.Name == "Heroine")
                : children.FirstOrDefault(c => c.Name == $"{set}_{name[4..]}");
            if (full == null) { mi.QueueFree(); continue; }
            int n = mi.Mesh.GetSurfaceCount();
            var map = new int[n];
            var own = new bool[n];
            for (int s = 0; s < n; s++)
            {
                var key = mi.Mesh.SurfaceGetMaterial(s)?.ResourceName;
                map[s] = Enumerable.Range(0, full.Mesh.GetSurfaceCount()).FirstOrDefault(f => full.Mesh.SurfaceGetMaterial(f)?.ResourceName == key);
                // (fur: a shorter stack of shells of its own)
                if (key == "fur") own[s] = true;
            }
            if (own.Any(o => o)) People.Fur(mi, FurShells);
            lod.pairs.Add((full, mi, map, own));
            lod.fulls.Add(full);
            if (name == "lod_body") lod.body = full;
        }
        scene.Free();
        p.Skeleton.AddChild(lod);
        GD.Print($"her LOD: {set}, {lod.pairs.Count} meshes and her shadow ({file})");
    }

    void Remove()
    {
        foreach (var (_, l, _, _) in pairs) l.QueueFree();
        shadow?.QueueFree();
        foreach (var f in fulls) if (IsInstanceValid(f)) f.Visible = true;
        QueueFree();
    }

    public override void _Ready()
    {
        if (Args.Has("lod")) GD.Print($"her LOD: ready ({Mode}, in tree {IsInsideTree()}, processing {IsProcessing()})");
    }

    public override void _Process(double delta)
    {
        bool want = Mode is "on" or "mesh";
        if (Mode == "auto" && InPlay && GetViewport().GetCamera3D() is Camera3D cam)
        {
            float d = cam.GlobalPosition.DistanceTo(skel.GlobalPosition + Vector3.Up);
            want = on == true ? d > Near : d > Far;
        }
        if (want != on)
        {
            on = want;
            if (Args.Has("lod")) GD.Print($"her LOD: {(want ? "gameplay model" : "full model")}");
            foreach (var (f, l, _, _) in pairs)
            {
                l.Visible = want;
                if (Mode == "mesh") f.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly;
                else f.Visible = !want;
            }
            if (shadow != null) shadow.Visible = want && Mode != "mesh";
        }
        if (!want) return;
        // Whatever the full model wears, these wear (a dye, her paint, a ghost's overlay).
        foreach (var (f, l, map, own) in pairs)
        {
            for (int s = 0; s < map.Length; s++)
                if (!own[s] && l.GetSurfaceOverrideMaterial(s) != f.GetSurfaceOverrideMaterial(map[s]))
                    l.SetSurfaceOverrideMaterial(s, f.GetSurfaceOverrideMaterial(map[s]));
            if (l.Transparency != f.Transparency) l.Transparency = f.Transparency;
            if (l.MaterialOverlay != f.MaterialOverlay) l.MaterialOverlay = f.MaterialOverlay;
            if (l.MaterialOverride != f.MaterialOverride) l.MaterialOverride = f.MaterialOverride;
        }
        if (shadow != null && body != null && shadow.Transparency != body.Transparency) shadow.Transparency = body.Transparency;
    }
}
