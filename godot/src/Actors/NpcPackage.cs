using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A person Marionette made, as a package (docs/handoff/marionette pipeline P6): art/npc/NAME/ holds body.glb (the
/// body on the game skeleton, its own skin materials), armor/ID.glb (pieces fitted to that body, skinned to the same
/// skeleton, their meshes named as the game's own pieces: ID.SLOT.MAT, ID.lod1.MAT, ID.shadow) and manifest.json
/// ({name, sex, height, joints, pieces:[{id, slot, file, hide}]}). A Person or story NPC whose body is "npc:NAME"
/// (World.PersonSpec.Body) is built here, with no code of its own: the body, each piece bound to the body's skeleton
/// and drawn as her pieces are (HerWear.WearPiece: People.Fur and People.OutfitMaterials), each piece's gameplay and shadow
/// meshes switched at the play camera as hers are (HerLod), the skin each piece lists dropped once and kept for the
/// session, her twist and share bones driven (HerJoints), and the library's and the townsfolk's clips on the shared
/// skeleton. A bone the body lacks (panel_front, breast_*, glute_* on a man) that a piece is skinned to is bound to
/// its nearest ancestor the body has, at the piece's own rest, rather than to the root.
/// hide: triangle indices into the body mesh's "skin" surface (glTF primitive order), or a string naming a file in
/// the package (".json": such an array; else the tuck-record format of art/armor/armor_tuck: int32 count, then
/// int32 x, y, z in glTF metres x 1e5 and a float, of bind positions: a triangle is dropped when all three corners
/// are listed).
/// </summary>
public static class NpcPackage
{
    public const string Prefix = "npc:";

    public sealed record Piece(string Id, string Slot, string File, Variant Hide);
    public sealed record Manifest(string Name, string Sex, double Height, int Joints, List<Piece> Pieces, string? HairFile = null, Color? HairColour = null, bool Baked = false, string? LodFile = null, string? Walk = null, float ArmsIn = 0, float ArmsWrist = 0);

    static readonly Dictionary<string, Manifest?> manifests = new();
    static readonly Dictionary<string, PackedScene> scenes = new();
    /// <summary>The body's meshes with the pieces' skin dropped, by package and mesh (made once a session).</summary>
    static readonly Dictionary<(string, ulong), ArrayMesh> trimmed = new();

    public static string Dir(string name) => $"res://art/npc/{name}";

    /// <summary>The package's name from a body ("npc:NAME"), or null.</summary>
    public static string? NameOf(string? body) => body != null && body.StartsWith(Prefix) ? body[Prefix.Length..] : null;

    public static Manifest? Read(string name)
    {
        if (manifests.TryGetValue(name, out var have)) return have;
        var file = $"{Dir(name)}/manifest.json";
        Manifest? m = null;
        if (!FileAccess.FileExists(file)) GD.PushWarning($"npc: no package {name} ({file})");
        else
        {
            var d = Json.ParseString(FileAccess.GetFileAsString(file)).AsGodotDictionary();
            var pieces = new List<Piece>();
            if (d.TryGetValue("pieces", out var pv))
                foreach (var e in pv.AsGodotArray())
                {
                    var p = e.AsGodotDictionary();
                    pieces.Add(new Piece((string)p["id"], p.TryGetValue("slot", out var s) ? (string)s : "",
                        p.TryGetValue("file", out var f) ? (string)f : $"armor/{(string)p["id"]}.glb", p.TryGetValue("hide", out var h) ? h : default));
                }
            // (--npc-wear a,b,...: a shot's package wears only those of its pieces)
            if (Args.Get("npc-wear") is string only && only != "1")
            {
                var keep = only.Split(',');
                pieces.RemoveAll(p => !keep.Contains(p.Id));
            }
            // (its hair: one of her styles carried onto its head, hair/STYLE.glb, and the colour it is dyed; a crop is painted on its head)
            string? hairFile = null; Color? hairColour = null;
            if (d.TryGetValue("hair", out var hv) && hv.VariantType == Variant.Type.Dictionary)
            {
                var h = hv.AsGodotDictionary();
                if (h.TryGetValue("file", out var hf) && hf.VariantType == Variant.Type.String) hairFile = (string)hf;
                if (h.TryGetValue("colour", out var hc) && hc.VariantType == Variant.Type.String) hairColour = new Color((string)hc);
            }
            m = new Manifest(d.TryGetValue("name", out var n) ? (string)n : name, d.TryGetValue("sex", out var sx) ? (string)sx : "male",
                d.TryGetValue("height", out var ht) ? (double)ht : 0, d.TryGetValue("joints", out var j) ? (int)j : 0, pieces, hairFile, hairColour, d.TryGetValue("baked", out var bk) && bk.VariantType == Variant.Type.Bool && (bool)bk,
                d.TryGetValue("lod", out var lv) && lv.VariantType == Variant.Type.Dictionary && lv.AsGodotDictionary().TryGetValue("file", out var lf) && lf.VariantType == Variant.Type.String ? (string)lf : null,
                // (its walk: "lurch", the crowd's undead lurch (NpcWalks); none, the townsfolk's walk)
                d.TryGetValue("walk", out var wv) && wv.VariantType == Variant.Type.String ? (string)wv : null);
            // (its arm set over the shared clips: "arms": {"in": DEG, "wrist": SHARE}, World.NpcArmSet; a shot's --npc-arms IN,WRIST overrides)
            if (d.TryGetValue("arms", out var av) && av.VariantType == Variant.Type.Dictionary)
            {
                var a = av.AsGodotDictionary();
                var (ai, aw) = SurvivorUnchained.World.NpcArmSet.Parse(string.Format(System.Globalization.CultureInfo.InvariantCulture, "{0},{1}",
                    a.TryGetValue("in", out var ain) ? (double)ain : 0, a.TryGetValue("wrist", out var awr) ? (double)awr : 0));
                m = m with { ArmsIn = ai, ArmsWrist = aw };
            }
            if (Args.Get("npc-arms") is string ao) { var (ai, aw) = SurvivorUnchained.World.NpcArmSet.Parse(ao); m = m with { ArmsIn = ai, ArmsWrist = aw }; }
        }
        return manifests[name] = m;
    }

    /// <summary>The walk a package's manifest names ("walk": "lurch"), as the clip its person plays for "Walk_Loop"
    /// (PersonView.WalkClip), or null: the townsfolk's own walk. The crowd's lurch (FolkClips.Crowd) for the risen.</summary>
    public static string? WalkClip(string name, bool woman) =>
        Read(name)?.Walk is string w && SurvivorUnchained.World.NpcWalks.GameClip(w) is string game ? FolkClips.Crowd(woman, false, game) : null;

    /// <summary>The scene files Build loads (Prefetch).</summary>
    public static IEnumerable<string> Files(string name)
    {
        yield return $"{Dir(name)}/body.glb";
        if (Read(name) is { } m)
        {
            foreach (var p in m.Pieces) yield return $"{Dir(name)}/{p.File}";
            if (m.HairFile != null) yield return $"{Dir(name)}/{m.HairFile}";
            if (m.Baked && m.LodFile != null) yield return $"{Dir(name)}/{m.LodFile}";
        }
    }

    static PackedScene? Scene(string file)
    {
        if (scenes.TryGetValue(file, out var ps)) return ps;
        if (!ResourceLoader.Exists(file)) { GD.PushWarning($"npc: {file} is not there (or not imported: Godot --headless --import)"); return null; }
        return scenes[file] = GD.Load<PackedScene>(file);
    }

    /// <summary>A package's person (null: no such package, or its body is missing).</summary>
    public static People.Person? Build(string name)
    {
        var m = Read(name);
        if (m == null || Scene($"{Dir(name)}/body.glb") is not { } bodyScene) return null;
        var root = bodyScene.Instantiate<Node3D>();
        var skel = (Skeleton3D)root.FindChildren("*", "Skeleton3D", true, false)[0];
        var person = new People.Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer(), Package = name, Woman = m.Sex == "female" };
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>())
        {
            person.Meshes.Add(mi);
            mi.Layers = 2;
            // (its vertex colours, where a part has them (the mouth's depth, the tongue's shade), are data, not colour)
            if (m.Baked) { BakedSurfaces(person, mi, m); continue; }
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                // (its skin as skin: the game's skin shader on the package's own maps, the same on body and head, People.NpcSkin)
                if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D sk && sk.ResourceName is "skin" or "skin_head")
                    mi.SetSurfaceOverrideMaterial(s, People.NpcSkin(sk, mi.Mesh, m.Sex == "female"));
                else if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D bm && bm.VertexColorUseAsAlbedo)
                {
                    var c = (BaseMaterial3D)bm.Duplicate();
                    c.VertexColorUseAsAlbedo = false;
                    mi.SetSurfaceOverrideMaterial(s, c);
                }
        }

        // A baked package is one mesh already (clothes and hair in it, the covered skin deleted, Godot's import LODs on it):
        // no pieces, no LOD pairing, no merge, no hide, no hair file.
        var laid = new List<MeshInstance3D>();
        var lodPairs = new List<(MeshInstance3D Full, MeshInstance3D Lod)>();
        var lodShadows = new List<(MeshInstance3D Shadow, MeshInstance3D Like)>();
        foreach (var piece in m.Baked ? new List<Piece>() : m.Pieces)
        {
            if (Scene($"{Dir(name)}/{piece.File}") is not { } ps) continue;
            var scene = ps.Instantiate<Node3D>();
            var from = scene.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>().FirstOrDefault();
            var meshes = scene.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>().ToList();
            string id = piece.Id.Replace('.', '_');
            var full = new Dictionary<string, MeshInstance3D>();   // by material
            var lods = new Dictionary<string, MeshInstance3D>();
            MeshInstance3D? shadow = null;
            foreach (var mi in meshes)
            {
                var (part, mat) = MeshPart(mi.Name.ToString(), piece.Id, piece.Slot);
                if (from != null && mi.Skin != null) mi.Skin = Rebind(mi.Skin, from, skel, $"{name}/{piece.Id}");
                if (part == "shadow") shadow = mi;
                else if (part == "lod1") lods[mat] = mi;
                else if (!full.TryAdd(mat, mi)) full[mat + "#" + full.Count] = mi;   // (never one mesh over another: every mesh is laid)
            }
            MeshInstance3D? anyFull = null;
            foreach (var (mat, mi) in full)
            {
                HerWear.WearPiece(person, mi, piece.Id);
                laid.Add(mi);
                anyFull ??= mi;
                if (lods.TryGetValue(mat, out var lm))
                {
                    HerWear.Lay(person, lm, piece.Id);
                    People.OutfitMaterials(lm);
                    lodPairs.Add((mi, lm));
                }
            }
            if (anyFull != null && shadow != null)
            {
                HerWear.Lay(person, shadow, piece.Id);
                lodShadows.Add((shadow, anyFull));
            }
            if (full.Count == 0) GD.PushWarning($"npc: {name}'s piece {piece.Id} has no meshes in {piece.File}");
            scene.Free();
        }
        if (lodPairs.Count > 0 || lodShadows.Count > 0)
        {
            var lod = HerLod.For(person);
            if (lod == null)
            {
                foreach (var (_, l) in lodPairs) l.QueueFree();
                foreach (var (s, _) in lodShadows) s.QueueFree();
            }
            else
            {
                foreach (var (f, l) in lodPairs) lod.AddPiece(f, l);
                foreach (var (s, like) in lodShadows) lod.AddShadow(s, like);
            }
        }
        if (laid.Count > 0) HerLod.For(person)?.Merge(laid);

        // Its hair, drawn as hers is (People.Hair: her hair shaders, dyed the manifest's colour), on its Head; static
        // (no sway at tier 2).
        if (!m.Baked && m.HairFile != null && Scene($"{Dir(name)}/{m.HairFile}") is { } hs)
        {
            var scene = hs.Instantiate<Node3D>();
            var from = scene.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>().FirstOrDefault();
            foreach (var mi in scene.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>().ToList())
            {
                if (from != null && mi.Skin != null) mi.Skin = Rebind(mi.Skin, from, skel, $"{name}/hair");
                mi.GetParent().RemoveChild(mi);
                mi.Owner = null;
                skel.AddChild(mi);
                mi.Skeleton = "..";
                mi.Layers = 2;
                person.Meshes.Add(mi);
                person.Hair.Add(mi);
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src)
                        mi.SetSurfaceOverrideMaterial(s, People.Hair(src, m.HairColour ?? People.HisHairColour));
            }
            scene.Free();
        }

        if (m.Baked && m.LodFile != null) BakedLod(person, name, m);

        // The skin under the pieces, dropped.
        if (!m.Baked) Hide(person, name, m);

        // Its arm set over the shared clips (manifest "arms"), before HerJoints so the twist bones follow.
        if (m.ArmsIn > 0f || m.ArmsWrist > 0f) skel.AddChild(new NpcArms(m.ArmsIn, m.ArmsWrist));
        // Her twist and share bones (and any others the rig's helpers name), driven from the pose the clips make.
        skel.AddChild(new HerJoints());
        skel.AddChild(new NpcHeadLevel()); // package NPCs only: head kept level under the heroine's clips
        skel.AddChild(new NpcHands()); // package NPCs only: a loose resting curl over the clips' straight, fanned fingers
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", People.Clips());
        if (FolkClips.Library() is AnimationLibrary folk) person.Anim.AddAnimationLibrary("folk", folk);
        GD.Print($"npc: {name} ({m.Sex}, {skel.GetBoneCount()} bones), {m.Pieces.Count} pieces, {laid.Count} meshes laid");
        return person;
    }

    /// <summary>A baked package's mesh, surface by surface by its source material's name: "skin" and "skin_head" the
    /// package's skin; a name starting "hair" her hair (dyed the manifest's colour, the mesh listed in person.Hair); any other
    /// vertex-colour material as data; every other surface as a laid piece's (People.Fur, People.OutfitMaterials).</summary>
    static void BakedSurfaces(People.Person person, MeshInstance3D mi, Manifest m)
    {
        bool hair = false;
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
        {
            if (mi.Mesh.SurfaceGetMaterial(s) is not BaseMaterial3D src) continue;
            if (src.ResourceName is "skin" or "skin_head") mi.SetSurfaceOverrideMaterial(s, People.NpcSkin(src, mi.Mesh, m.Sex == "female"));
            else if (src.ResourceName.StartsWith("hair"))
            {
                mi.SetSurfaceOverrideMaterial(s, People.Hair(src, m.HairColour ?? People.HisHairColour));
                hair = true;
            }
        }
        if (hair) person.Hair.Add(mi);
        // (surfaces with a material laid already are skipped by both)
        People.Fur(mi);
        People.OutfitMaterials(mi);
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            if (mi.GetSurfaceOverrideMaterial(s) == null && mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D bm && bm.VertexColorUseAsAlbedo)
            {
                var c = (BaseMaterial3D)bm.Duplicate();
                c.VertexColorUseAsAlbedo = false;
                mi.SetSurfaceOverrideMaterial(s, c);
            }
    }

    /// <summary>A baked package's gameplay model (lod.glb: mesh "lod", and "lod_shadow" of one "shadow" surface) on the
    /// body's skeleton, each surface drawn as the body's surface of the same material name; switched with the full meshes
    /// by visibility range at 18 m (--npc-lod off: always full, on: always lod, auto).</summary>
    static void BakedLod(People.Person person, string name, Manifest m)
    {
        string mode = Args.Get("npc-lod") is string a && a is "off" or "on" ? Args.Get("npc-lod")! : "auto";
        if (Scene($"{Dir(name)}/{m.LodFile}") is not { } ps) return;
        var scene = ps.Instantiate<Node3D>();
        var from = scene.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>().FirstOrDefault();
        var byMat = new Dictionary<string, Material>();
        foreach (var bm in person.Meshes)
            for (int s = 0; s < bm.Mesh.GetSurfaceCount(); s++)
                if (bm.Mesh.SurfaceGetMaterial(s) is { } sm && sm.ResourceName != "" && !byMat.ContainsKey(sm.ResourceName)
                    && (bm.GetSurfaceOverrideMaterial(s) ?? sm) is { } use) byMat[sm.ResourceName] = use;
        if (mode == "auto")
            foreach (var bm in person.Meshes) { bm.VisibilityRangeEnd = 18; bm.VisibilityRangeEndMargin = 1; }
        if (mode == "on") foreach (var bm in person.Meshes) bm.Visible = false;
        foreach (var mi in scene.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>().ToList())
        {
            string n = mi.Name.ToString();
            bool shadow = n == "lod_shadow";
            if (!shadow && n != "lod") continue;
            if (from != null && mi.Skin != null) mi.Skin = Rebind(mi.Skin, from, person.Skeleton, $"{name}/{n}");
            mi.GetParent().RemoveChild(mi);
            mi.Owner = null;
            person.Skeleton.AddChild(mi);
            mi.Skeleton = "..";
            mi.Layers = 2;
            if (!shadow)
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.Mesh.SurfaceGetMaterial(s) is { } sm && byMat.TryGetValue(sm.ResourceName, out var use)) mi.SetSurfaceOverrideMaterial(s, use);
            if (shadow) mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly;
            else mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
            if (mode == "off") mi.Visible = false;
            else if (mode == "auto") { mi.VisibilityRangeBegin = 18; mi.VisibilityRangeBeginMargin = 1; }
        }
        scene.Free();
    }

    /// <summary>A piece's skin as the body's skeleton has it: each bind to a bone the body lacks moved to that bone's
    /// nearest ancestor the body has, at the piece's rest (a bind left to a missing bone is bound to the root).</summary>
    static readonly HashSet<string> told = new();

    static Skin Rebind(Skin skin, Skeleton3D from, Skeleton3D to, string what)
    {
        var missing = Enumerable.Range(0, skin.GetBindCount()).Where(i => skin.GetBindName(i) is var b && b != "" && to.FindBone(b) < 0).ToList();
        if (missing.Count == 0) return skin;
        var s = (Skin)skin.Duplicate();
        var moved = new List<string>();
        foreach (int i in missing)
        {
            string bn = skin.GetBindName(i);
            int b = from.FindBone(bn), a = b < 0 ? -1 : from.GetBoneParent(b);
            while (a >= 0 && to.FindBone(from.GetBoneName(a)) < 0) a = from.GetBoneParent(a);
            if (b < 0 || a < 0) { s.SetBindName(i, to.GetBoneName(0)); moved.Add($"{bn}>{to.GetBoneName(0)}"); continue; }
            // (the vertex where it was at rest: ancestor's rest x new bind = bone's rest x old bind)
            s.SetBindPose(i, from.GetBoneGlobalRest(a).AffineInverse() * from.GetBoneGlobalRest(b) * skin.GetBindPose(i));
            s.SetBindName(i, from.GetBoneName(a));
            moved.Add($"{bn}>{from.GetBoneName(a)}");
        }
        if (told.Add(what)) GD.Print($"npc: {what} bound to the body's bones ({string.Join(", ", moved)})");
        return s;
    }

    /// <summary>A piece mesh's part ("" a full mesh, "lod1", "shadow") and material, from its name: ID.MAT (Marionette's
    /// pieces, as her outfits name theirs: ranger.top.darkleather), ID.SLOT.MAT, ID.lod1.MAT or ID.shadow (Godot's import
    /// may write the dots as underscores). Before 20 Oct an ID.MAT name was read as part MAT with no material, so every
    /// mesh of a piece went to one key and only its last was laid (the villager's ranger.top showed its thread alone).</summary>
    public static (string Part, string Mat) MeshPart(string meshName, string id, string slot)
    {
        string n = meshName.Replace('.', '_'), i = id.Replace('.', '_');
        var rest = n.StartsWith(i + "_") ? n[(i.Length + 1)..] : n;
        if (rest == "shadow") return ("shadow", "");
        if (rest.StartsWith("lod1_")) return ("lod1", rest[5..]);
        if (slot.Length > 0 && rest.StartsWith(slot.Replace('.', '_') + "_")) rest = rest[(slot.Length + 1)..];
        return ("", rest);
    }

    /// <summary>Every piece's hidden skin dropped from the body mesh's "skin" surface, once a session.</summary>
    static void Hide(People.Person p, string name, Manifest m)
    {
        if (m.Pieces.All(x => x.Hide.VariantType == Variant.Type.Nil)) return;
        var body = p.Skeleton.GetChildren().OfType<MeshInstance3D>().FirstOrDefault(mi => SkinSurface(mi.Mesh) >= 0);
        if (body == null) { GD.PushWarning($"npc: {name} has no \"skin\" surface to hide under its pieces"); return; }
        var key = (name, body.Mesh.GetRid().Id);
        if (!trimmed.TryGetValue(key, out var mesh))
        {
            int surf = SkinSurface(body.Mesh);
            var arrays = body.Mesh.SurfaceGetArrays(surf);
            var idx = arrays[(int)Mesh.ArrayType.Index].AsInt32Array();
            int tris = idx.Length / 3;
            var drop = new bool[tris];
            int asked = 0;
            HashSet<long>? points = null;
            foreach (var piece in m.Pieces)
            {
                var h = piece.Hide;
                if (h.VariantType == Variant.Type.String)
                {
                    var f = $"{Dir(name)}/{(string)h}";
                    if (f.EndsWith(".json")) h = Json.ParseString(FileAccess.GetFileAsString(f));
                    else { points ??= new(); foreach (var k in HerWear.Points(f)) points.Add(k); continue; }
                }
                if (h.VariantType != Variant.Type.Array) continue;
                foreach (var t in h.AsGodotArray())
                {
                    int i = (int)t;
                    asked++;
                    if (i >= 0 && i < tris) drop[i] = true;
                }
            }
            if (points != null)
            {
                var vs = arrays[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var ks = vs.Select(HerWear.Key).ToArray();
                for (int t = 0; t < tris; t++)
                    if (points.Contains(ks[idx[3 * t]]) && points.Contains(ks[idx[3 * t + 1]]) && points.Contains(ks[idx[3 * t + 2]])) drop[t] = true;
            }
            int n = drop.Count(d => d);
            var kept = new int[(tris - n) * 3];
            for (int t = 0, o = 0; t < tris; t++)
                if (!drop[t]) { kept[o++] = idx[3 * t]; kept[o++] = idx[3 * t + 1]; kept[o++] = idx[3 * t + 2]; }
            mesh = Rebuilt(body.Mesh, surf, kept);
            trimmed[key] = mesh;
            GD.Print($"npc: {name}: {n} of {tris} skin triangles hidden under its pieces ({asked} listed{(points != null ? $", {points.Count} points" : "")})");
        }
        // (the override materials on the old mesh carry over: same surfaces, same order)
        body.Mesh = mesh;
    }

    static int SkinSurface(Mesh mesh)
    {
        for (int s = 0; s < mesh.GetSurfaceCount(); s++)
            if (mesh.SurfaceGetMaterial(s)?.ResourceName == "skin") return s;
        return -1;
    }

    /// <summary>A copy of a mesh with one surface's triangles replaced (its blend shapes, skin weights and materials kept).</summary>
    static ArrayMesh Rebuilt(Mesh src, int surf, int[] index)
    {
        var am = (ArrayMesh)src;
        var outm = new ArrayMesh { BlendShapeMode = am.BlendShapeMode };
        for (int b = 0; b < am.GetBlendShapeCount(); b++) outm.AddBlendShape(am.GetBlendShapeName(b));
        for (int s = 0; s < am.GetSurfaceCount(); s++)
        {
            var arrays = am.SurfaceGetArrays(s);
            if (s == surf) arrays[(int)Mesh.ArrayType.Index] = index;
            var blends = am.SurfaceGetBlendShapeArrays(s);
            var fmt = am.SurfaceGetFormat(s);
            // (the skin's eight weights a vertex, where it has them; the rest Godot works out from the arrays)
            var flags = (fmt & Mesh.ArrayFormat.FlagUse8BoneWeights) != 0 ? Mesh.ArrayFormat.FlagUse8BoneWeights : 0;
            outm.AddSurfaceFromArrays(am.SurfaceGetPrimitiveType(s), arrays, blends, null, flags);
            outm.SurfaceSetMaterial(s, am.SurfaceGetMaterial(s));
            outm.SurfaceSetName(s, am.SurfaceGetName(s));
        }
        return outm;
    }
}
