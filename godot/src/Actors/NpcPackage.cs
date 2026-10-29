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
/// its nearest ancestor the body has, at the piece's own rest, rather than to the root; unless the piece's manifest entry
/// lists it in "springs" (a cape's chains, a hem's bones): then it is added to the body's skeleton and swung, and the
/// piece's "correctives" driven (PieceSprings).
/// hide: triangle indices into the body mesh's "skin" surface (glTF primitive order), or a string naming a file in
/// the package (".json": such an array; else the tuck-record format of art/armor/armor_tuck: int32 count, then
/// int32 x, y, z in glTF metres x 1e5 and a float, of bind positions: a triangle is dropped when all three corners
/// are listed).
/// </summary>
public static class NpcPackage
{
    public const string Prefix = "npc:";

    public sealed record Piece(string Id, string Slot, string File, Variant Hide, Variant Springs = default, Variant Correctives = default);
    public sealed record Manifest(string Name, string Sex, double Height, int Joints, List<Piece> Pieces, string? HairFile = null, Color? HairColour = null, bool Baked = false, string? LodFile = null, string? Walk = null, float ArmsIn = 0, float ArmsWrist = 0, Godot.Collections.Dictionary? HairUniforms = null);

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
        var file = Overlay(name) is string ov && System.IO.File.Exists($"{ov}/manifest.json") ? $"{ov}/manifest.json" : $"{Dir(name)}/manifest.json";
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
                        p.TryGetValue("file", out var f) ? (string)f : $"armor/{(string)p["id"]}.glb", p.TryGetValue("hide", out var h) ? h : default,
                        p.TryGetValue("springs", out var sp) ? sp : default, p.TryGetValue("correctives", out var cr) ? cr : default));
                }
            // (--npc-wear a,b,...: a shot's package wears only those of its pieces)
            if (Args.Get("npc-wear") is string only && only != "1")
            {
                var keep = only.Split(',');
                pieces.RemoveAll(p => !keep.Contains(p.Id));
            }
            // (its hair: one of her styles carried onto its head, hair/STYLE.glb, and the colour it is dyed; a crop is painted on its head)
            string? hairFile = null; Color? hairColour = null; Godot.Collections.Dictionary? hairUniforms = null;
            if (d.TryGetValue("hair", out var hv) && hv.VariantType == Variant.Type.Dictionary)
            {
                var h = hv.AsGodotDictionary();
                if (h.TryGetValue("file", out var hf) && hf.VariantType == Variant.Type.String) hairFile = (string)hf;
                if (h.TryGetValue("colour", out var hc) && hc.VariantType == Variant.Type.String) hairColour = new Color((string)hc);
                if (h.TryGetValue("uniforms", out var hu) && hu.VariantType == Variant.Type.Dictionary) hairUniforms = hu.AsGodotDictionary();
            }
            m = new Manifest(d.TryGetValue("name", out var n) ? (string)n : name, d.TryGetValue("sex", out var sx) ? (string)sx : "male",
                d.TryGetValue("height", out var ht) ? (double)ht : 0, d.TryGetValue("joints", out var j) ? (int)j : 0, pieces, hairFile, hairColour, d.TryGetValue("baked", out var bk) && bk.VariantType == Variant.Type.Bool && (bool)bk,
                d.TryGetValue("lod", out var lv) && lv.VariantType == Variant.Type.Dictionary && lv.AsGodotDictionary().TryGetValue("file", out var lf) && lf.VariantType == Variant.Type.String ? (string)lf : null,
                // (its walk: "lurch", the crowd's undead lurch (NpcWalks); none, the townsfolk's walk)
                d.TryGetValue("walk", out var wv) && wv.VariantType == Variant.Type.String ? (string)wv : null, HairUniforms: hairUniforms);
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

    /// <summary>--npc-overlay NAME=DIR (a test's package overlay, outside the project: its manifest.json and any piece
    /// file it has are read from DIR, the glb loaded at run time; everything else from the package): null if none.</summary>
    static string? Overlay(string name) =>
        Args.Get("npc-overlay") is string o && o.Split('=', 2) is { Length: 2 } kv && kv[0] == name ? kv[1].Replace('\\', '/') : null;

    static PackedScene? Scene(string file)
    {
        if (scenes.TryGetValue(file, out var ps)) return ps;
        if (file.StartsWith("res://art/npc/") && file["res://art/npc/".Length..].Split('/', 2) is { Length: 2 } nf && Overlay(nf[0]) is string ov
            && System.IO.File.Exists($"{ov}/{nf[1]}"))
        {
            var doc = new GltfDocument();
            var state = new GltfState();
            if (doc.AppendFromFile($"{ov}/{nf[1]}", state) == Error.Ok && doc.GenerateScene(state) is Node gen)
            {
                var packed = new PackedScene();
                packed.Pack(gen);
                gen.Free();
                GD.Print($"npc: {file} from the overlay {ov}");
                return scenes[file] = packed;
            }
            GD.PushWarning($"npc: overlay {ov}/{nf[1]} did not load");
        }
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
        // no LOD pairing, no merge, no hide. Its pieces, when the manifest lists any, are laid on it as on
        // any package (the Ford-Warden's hood and capelet, armor/hood.glb, Warden 6): the body's own cut is the hide.
        var laid = new List<MeshInstance3D>();
        var lodPairs = new List<(MeshInstance3D Full, MeshInstance3D Lod)>();
        var lodShadows = new List<(MeshInstance3D Shadow, MeshInstance3D Like)>();
        var springing = new List<(string Id, List<PieceSprings.Link> Links, List<PieceSprings.Corrective> Correctives, List<MeshInstance3D> Meshes, Transform3D PkgToSkel)>();
        foreach (var piece in m.Pieces)
        {
            if (Scene($"{Dir(name)}/{piece.File}") is not { } ps) continue;
            var scene = ps.Instantiate<Node3D>();
            var from = scene.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>().FirstOrDefault();
            var meshes = scene.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>().ToList();
            string id = piece.Id.Replace('.', '_');
            var full = new Dictionary<string, MeshInstance3D>();   // by material
            var lods = new Dictionary<string, MeshInstance3D>();
            MeshInstance3D? shadow = null;
            // (its spring bones the body lacks, added to the body's skeleton first, so its skin binds to them: PieceSprings)
            var springs = PieceSprings.ReadSprings(piece.Springs);
            var correctives = PieceSprings.ReadCorrectives(piece.Correctives);
            var pkgToSkel = Transform3D.Identity;
            for (Node? n = from; n != null && n != scene; n = n.GetParent()) if (n is Node3D n3) pkgToSkel = n3.Transform * pkgToSkel;
            pkgToSkel = pkgToSkel.AffineInverse();
            if (springs.Count > 0 && !PieceSprings.Off) PieceSprings.AddBones(skel, from, springs, pkgToSkel, $"{name}/{piece.Id}");
            if (springs.Count > 0 || correctives.Count > 0) springing.Add((piece.Id, springs, correctives, meshes, pkgToSkel));
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
        // (no sway at tier 2: what swings, swings by its skin). A baked package's too (Warden 6: the Ford-Warden's beard,
        // beard.glb, hair cards by tools/assets/warden_beard.py). A mesh named NAME.lod1 is its gameplay model and
        // NAME.shadow its shadow caster, switched as the body's are (BakedLod's 18 m on a baked package, HerLod's
        // pairing on the others).
        // (WARDEN_BEARD_HIDE=1: no hair on a package, for a beard's mask by difference: Warden 6 r4's value numbers)
        if (m.HairFile != null && System.Environment.GetEnvironmentVariable("WARDEN_BEARD_HIDE") != "1" && Scene($"{Dir(name)}/{m.HairFile}") is { } hs)
        {
            var scene = hs.Instantiate<Node3D>();
            var from = scene.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>().FirstOrDefault();
            MeshInstance3D? hairFull = null, hairLod = null, hairShadow = null;
            foreach (var mi in scene.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>().ToList())
            {
                string part = mi.Name.ToString().Replace('.', '_');
                bool isLod = part.EndsWith("_lod1"), isShadow = part.EndsWith("_shadow");
                if (from != null && mi.Skin != null) mi.Skin = Rebind(mi.Skin, from, skel, $"{name}/hair");
                mi.GetParent().RemoveChild(mi);
                mi.Owner = null;
                skel.AddChild(mi);
                mi.Skeleton = "..";
                mi.Layers = 2;
                if (isShadow)
                {
                    mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly;
                    hairShadow = mi;
                    continue;
                }
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src)
                        mi.SetSurfaceOverrideMaterial(s, Uniforms(People.Hair(src, m.HairColour ?? People.HisHairColour), src.ResourceName, m.HairUniforms));
                person.Hair.Add(mi);
                if (isLod) { hairLod = mi; continue; }
                person.Meshes.Add(mi);
                hairFull ??= mi;
            }
            scene.Free();
            if (m.Baked)
            {
                // (as BakedLod lays lod.glb: the full mesh is in person.Meshes, which BakedLod ends at 18 m)
                string mode = Args.Get("npc-lod") is string a && a is "off" or "on" ? Args.Get("npc-lod")! : "auto";
                foreach (var l in new[] { hairLod, hairShadow })
                {
                    if (l == null) continue;
                    if (l == hairLod) l.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                    if (mode == "off") l.Visible = false;
                    else if (mode == "auto") { l.VisibilityRangeBegin = 18; l.VisibilityRangeBeginMargin = 1; }
                }
            }
            else if (hairFull != null && HerLod.For(person) is { } hl)
            {
                if (hairLod != null) hl.AddPiece(hairFull, hairLod);
                if (hairShadow != null) hl.AddShadow(hairShadow, hairFull);
            }
            else { hairLod?.QueueFree(); hairShadow?.QueueFree(); }
            if (hairFull != null && System.Environment.GetEnvironmentVariable("WARDEN_BEARDCHECK") == "1") skel.AddChild(new BeardCheck(hairFull));
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
        // Each piece's spring bones swung and its corrective shapes driven, last, over the finished pose (PieceSprings).
        foreach (var sp in springing) PieceSprings.Attach(person, $"{name}/{sp.Id}", name, sp.Links, sp.Correctives, sp.Meshes, sp.PkgToSkel);
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

    /// <summary>A package's hair uniforms (the manifest's hair "uniforms": {"*": {NAME: value}, MATERIAL: {...}}, a
    /// value a number or [x, y, z]) set on its hair's every pass, "*" first, then its material's own (Warden 6 r4: the
    /// Ford-Warden's beard, its mass "hair_mass" and cards "hair", greyed out of the moonlight's blue-white).</summary>
    static Material Uniforms(Material mat, string part, Godot.Collections.Dictionary? u)
    {
        if (u == null || mat is not ShaderMaterial sm) return mat;
        foreach (var who in new[] { "*", part })
        {
            if (!u.TryGetValue(who, out var set) || set.VariantType != Variant.Type.Dictionary) continue;
            foreach (var pass in HairDraw.Passes(sm))
                foreach (var (k, v) in set.AsGodotDictionary())
                {
                    if (v.VariantType is Variant.Type.Float or Variant.Type.Int) pass.SetShaderParameter((string)k, (float)v);
                    else if (v.VariantType == Variant.Type.Array && v.AsGodotArray() is { Count: 3 } a)
                        pass.SetShaderParameter((string)k, new Vector3((float)a[0], (float)a[1], (float)a[2]));
                }
        }
        return mat;
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

/// <summary>WARDEN_BEARDCHECK=1 (Warden 6 beard): a package's hair cards (its full hair mesh) measured in whatever it
/// plays, every 0.2 s on the CPU from the skeleton's pose: card points that go into the body, face, patch or hood (more
/// than 2 mm behind the surface at the nearest of its points, where at rest they were not), and each edge's stretch
/// against its rest. Printed as "beardcheck" lines with the clip playing, and per clip and in sum when it leaves.</summary>
public partial class BeardCheck : Node
{
    sealed class Skinned
    {
        public Vector3[] P = Array.Empty<Vector3>(), N = Array.Empty<Vector3>();
        public int[] B = Array.Empty<int>(), Idx = Array.Empty<int>(), BindBone = Array.Empty<int>();
        public float[] W = Array.Empty<float>();
        public Transform3D[] Bind = Array.Empty<Transform3D>();
        public int K;
    }

    readonly MeshInstance3D hairMesh;
    Skeleton3D skel = null!;
    Skinned? hair;
    readonly List<Skinned> body = new();
    int[] edges = Array.Empty<int>();
    float[] restLen = Array.Empty<float>();
    bool[] outAtRest = Array.Empty<bool>();
    double t, tick;
    int samples, worstCount;
    float worstStretch, worstDepth;
    string worstWhen = "";
    readonly List<float> stretchAll = new();
    readonly Dictionary<string, (int Poke, float Depth, float Stretch)> byClip = new();

    public BeardCheck(MeshInstance3D hair) { hairMesh = hair; Name = "BeardCheck"; }

    BeardCheck() { hairMesh = null!; }

    static Skinned? Read(MeshInstance3D mi, int s, Skeleton3D skel)
    {
        var a = mi.Mesh.SurfaceGetArrays(s);
        if (a[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil || mi.Skin == null) return null;
        var o = new Skinned { P = a[(int)Mesh.ArrayType.Vertex].AsVector3Array(), N = a[(int)Mesh.ArrayType.Normal].AsVector3Array() };
        var bones = a[(int)Mesh.ArrayType.Bones];
        o.B = bones.VariantType == Variant.Type.PackedInt32Array ? bones.AsInt32Array() : Array.ConvertAll(bones.AsFloat32Array(), f => (int)f);
        o.W = a[(int)Mesh.ArrayType.Weights].AsFloat32Array();
        o.Idx = a[(int)Mesh.ArrayType.Index].AsInt32Array();
        o.K = o.B.Length / Math.Max(o.P.Length, 1);
        int n = mi.Skin.GetBindCount();
        o.BindBone = new int[n];
        o.Bind = new Transform3D[n];
        for (int i = 0; i < n; i++)
        {
            string bn = mi.Skin.GetBindName(i);
            o.BindBone[i] = bn != "" ? skel.FindBone(bn) : mi.Skin.GetBindBone(i);
            o.Bind[i] = mi.Skin.GetBindPose(i);
        }
        return o;
    }

    Transform3D[] Mats(Skinned m)
    {
        var r = new Transform3D[m.Bind.Length];
        for (int i = 0; i < r.Length; i++) r[i] = (m.BindBone[i] < 0 ? Transform3D.Identity : skel.GetBoneGlobalPose(m.BindBone[i])) * m.Bind[i];
        return r;
    }

    static (Vector3 P, Vector3 N) At(Skinned m, Transform3D[] M, int v)
    {
        Vector3 p = Vector3.Zero, n = Vector3.Zero;
        for (int k = 0; k < m.K; k++)
        {
            float w = m.W[v * m.K + k];
            if (w <= 0) continue;
            var x = M[m.B[v * m.K + k]];
            p += w * (x * m.P[v]);
            n += w * (x.Basis * m.N[v]);
        }
        return (p, n.Normalized());
    }

    static Dictionary<(int, int, int), List<int>> Grid(Vector3[] p)
    {
        var g = new Dictionary<(int, int, int), List<int>>();
        for (int i = 0; i < p.Length; i++)
        {
            var k = ((int)Mathf.Floor(p[i].X / 0.02f), (int)Mathf.Floor(p[i].Y / 0.02f), (int)Mathf.Floor(p[i].Z / 0.02f));
            if (!g.TryGetValue(k, out var l)) g[k] = l = new List<int>();
            l.Add(i);
        }
        return g;
    }

    static int Nearest(Dictionary<(int, int, int), List<int>> g, Vector3[] hp, Vector3 p, float reach)
    {
        int best = -1;
        float bd = reach * reach;
        int cx = (int)Mathf.Floor(p.X / 0.02f), cy = (int)Mathf.Floor(p.Y / 0.02f), cz = (int)Mathf.Floor(p.Z / 0.02f);
        for (int x = -2; x <= 2; x++)
            for (int y = -2; y <= 2; y++)
                for (int z = -2; z <= 2; z++)
                    if (g.TryGetValue((cx + x, cy + y, cz + z), out var l))
                        foreach (int i in l)
                        {
                            float d = hp[i].DistanceSquaredTo(p);
                            if (d < bd) { bd = d; best = i; }
                        }
        return best;
    }

    // (every body surface's points and normals, posed, or at the meshes' own bind)
    (Vector3[] P, Vector3[] N) BodyPoints(bool rest)
    {
        var ps = new List<Vector3>();
        var ns = new List<Vector3>();
        foreach (var b in body)
        {
            var M = rest ? null : Mats(b);
            for (int v = 0; v < b.P.Length; v++)
            {
                if (rest) { ps.Add(b.P[v]); ns.Add(b.N[v]); }
                else { var (p, n) = At(b, M!, v); ps.Add(p); ns.Add(n); }
            }
        }
        return (ps.ToArray(), ns.ToArray());
    }

    public override void _Ready()
    {
        skel = GetParent<Skeleton3D>();
        hair = hairMesh.Mesh != null ? Read(hairMesh, 0, skel) : null;
        foreach (var c in skel.GetChildren())
        {
            if (c is not MeshInstance3D mi || mi == hairMesh || mi.Mesh == null || mi.CastShadow == GeometryInstance3D.ShadowCastingSetting.ShadowsOnly || mi.VisibilityRangeBegin > 0) continue;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                string mat = mi.Mesh.SurfaceGetMaterial(s)?.ResourceName ?? "";
                if (mat is "generated" or "warden_face" or "warden_patch" or "warden_hood_wool" && Read(mi, s, skel) is { } b) body.Add(b);
            }
        }
        if (hair == null || body.Count == 0) { GD.Print("beardcheck: no hair or body surface"); QueueFree(); return; }
        var seen = new HashSet<long>();
        var el = new List<int>();
        for (int i = 0; i + 2 < hair.Idx.Length; i += 3)
            for (int e = 0; e < 3; e++)
            {
                int a = hair.Idx[i + e], b = hair.Idx[i + (e + 1) % 3];
                long key = (long)Math.Min(a, b) << 32 | (uint)Math.Max(a, b);
                if (seen.Add(key)) { el.Add(a); el.Add(b); }
            }
        edges = el.ToArray();
        restLen = new float[edges.Length / 2];
        for (int i = 0; i < restLen.Length; i++) restLen[i] = hair.P[edges[2 * i]].DistanceTo(hair.P[edges[2 * i + 1]]);
        var (bp, bn) = BodyPoints(true);
        var grid = Grid(bp);
        outAtRest = new bool[hair.P.Length];
        int under = 0;
        for (int v = 0; v < hair.P.Length; v++)
        {
            int h = Nearest(grid, bp, hair.P[v], 0.04f);
            outAtRest[v] = h < 0 || (hair.P[v] - bp[h]).Dot(bn[h]) > -0.002f;
            if (!outAtRest[v]) under++;
        }
        GD.Print($"beardcheck: {hair.P.Length} card points, {restLen.Length} edges, {bp.Length} body points; {under} card points under a surface at rest (not counted)");
    }

    string Clip()
    {
        foreach (var n in skel.GetParent().GetChildren())
            if (n is AnimationPlayer ap && ap.IsPlaying()) return ap.CurrentAnimation.ToString();
        return "-";
    }

    public override void _Process(double delta)
    {
        t += delta;
        if ((tick -= delta) > 0 || hair == null) return;
        tick = 0.2;
        samples++;
        var hm = Mats(hair);
        var hp = new Vector3[hair.P.Length];
        for (int v = 0; v < hp.Length; v++) hp[v] = At(hair, hm, v).P;
        float smax = 0;
        for (int i = 0; i < restLen.Length; i++)
        {
            if (restLen[i] < 1e-4f) continue;
            float r = hp[edges[2 * i]].DistanceTo(hp[edges[2 * i + 1]]) / restLen[i];
            smax = Math.Max(smax, r);
            if ((i & 7) == 0) stretchAll.Add(r);
        }
        var (bp, bn) = BodyPoints(false);
        var grid = Grid(bp);
        int count = 0;
        float depth = 0;
        for (int v = 0; v < hp.Length; v += 2)
        {
            if (!outAtRest[v]) continue;
            int h = Nearest(grid, bp, hp[v], 0.04f);
            if (h < 0) continue;
            float d = -(hp[v] - bp[h]).Dot(bn[h]);
            if (d <= 0.002f) continue;
            count++;
            depth = Math.Max(depth, d);
        }
        string clip = Clip();
        var c = byClip.GetValueOrDefault(clip);
        byClip[clip] = (Math.Max(c.Poke, count), Math.Max(c.Depth, depth), Math.Max(c.Stretch, smax));
        worstStretch = Math.Max(worstStretch, smax);
        if (count > worstCount) { worstCount = count; worstWhen = $"t={t:F1} {clip}"; }
        worstDepth = Math.Max(worstDepth, depth);
        GD.Print($"beardcheck t={t:F1} clip={clip} stretch_max={smax:F3} poke={count} depth_mm={depth * 1000:F1}");
    }

    public override void _ExitTree()
    {
        if (hair == null) return;
        stretchAll.Sort();
        float p99 = stretchAll.Count > 0 ? stretchAll[(int)(stretchAll.Count * 0.99)] : 0;
        float p01 = stretchAll.Count > 0 ? stretchAll[(int)(stretchAll.Count * 0.01)] : 0;
        foreach (var (clip, v) in byClip) GD.Print($"beardcheck CLIP {clip} poke_max={v.Poke} depth_max_mm={v.Depth * 1000:F1} stretch_max={v.Stretch:F3}");
        GD.Print($"beardcheck SUMMARY samples={samples} stretch_max={worstStretch:F3} stretch_p99={p99:F3} squash_p01={p01:F3} poke_max={worstCount} ({worstWhen}) depth_max_mm={worstDepth * 1000:F1} (of every second card point)");
    }
}
