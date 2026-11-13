using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Look thumbnails (bd-ui W23): a wardrobe look pictured as her wearing its own pieces, not the item's icon. A studio of its own
/// (OwnWorld3D, lit like the item photographs) stands her with ONLY that look shown (her equipment taken off, no dyes, nothing
/// held), through the same build the world uses (Loadouts.Of -> PersonView -> HerWear), a few frames, then photographs her
/// framed for the slot (Body neck to knee, Head head and shoulders, Feet knee down). Cached by def + slot + size, written to
/// user://icons/ so later runs read them back. Until a thumbnail exists the control shows the item's own picture.
/// </summary>
public partial class LookThumbs : Node
{
    const int Version = 5;
    static LookThumbs? studio;
    static readonly Dictionary<string, ImageTexture> done = new();
    static readonly Dictionary<string, List<TextureRect>> waiting = new();
    static readonly Queue<(string Key, string Def, string Slot, int Size)> queue = new();
    static readonly HashSet<string> queued = new();

    /// <summary>Whose looks are pictured (her); null = the running game's character.</summary>
    public static CharacterData? Her;

    static string Key(string def, string slot, int size) => $"{def}.{slot}.{size}";
    static string PathOf(string key) => $"user://icons/look_{key.Replace(':', '_').Replace('/', '_')}.v{Version}.png";

    /// <summary>The look's thumbnail as a size x size control. Locked: 15% brightness, desaturated, an 18 px lock at 80% bottom-right.</summary>
    public static Control For(string defId, string slot, int size, bool locked)
    {
        var box = new Control { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Ignore, ClipContents = true };
        var r = new TextureRect
        {
            AnchorRight = 1, AnchorBottom = 1, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCovered,
            MouseFilter = Control.MouseFilterEnum.Ignore, TextureFilter = CanvasItem.TextureFilterEnum.LinearWithMipmaps,
        };
        box.AddChild(r);
        var key = Key(defId, slot, size);
        if (Get(key) is { } t) r.Texture = t;
        else
        {
            // (until she is photographed: the item's own picture)
            if (Items.Find(defId) is { } def && ItemPhotos.Real(def.Icon) is { } pic) r.Texture = pic;
            if (!waiting.TryGetValue(key, out var l)) waiting[key] = l = new();
            l.Add(r);
            Request(key, defId, slot, size);
        }
        if (locked)
        {
            r.Material = new ShaderMaterial { Shader = Dim };
            var lk = Glyphs.Icon("lock", 18, Kit.Ink2);
            lk.Modulate = new Color(1, 1, 1, 0.8f);
            lk.Size = new Vector2(18, 18);
            lk.Position = new Vector2(size - 18 - 4, size - 18 - 4);
            lk.MouseFilter = Control.MouseFilterEnum.Ignore;
            box.AddChild(lk);
        }
        return box;
    }

    static readonly Shader Dim = new()
    {
        Code = "shader_type canvas_item; void fragment() { vec4 c = texture(TEXTURE, UV); float g = dot(c.rgb, vec3(0.299, 0.587, 0.114)); COLOR = vec4(vec3(g * 0.15), c.a); }",
    };

    static Texture2D? Get(string key)
    {
        if (done.TryGetValue(key, out var t)) return t;
        var p = PathOf(key);
        if (!FileAccess.FileExists(p)) return null;
        var img = Image.LoadFromFile(ProjectSettings.GlobalizePath(p));
        if (img == null) return null;
        img.GenerateMipmaps();
        return done[key] = ImageTexture.CreateFromImage(img);
    }

    static void Request(string key, string def, string slot, int size)
    {
        if (!queued.Add(key)) return;
        queue.Enqueue((key, def, slot, size));
        if (studio != null && GodotObject.IsInstanceValid(studio)) return;
        if (Engine.GetMainLoop() is not SceneTree tree) return;
        DirAccess.MakeDirRecursiveAbsolute("user://icons");
        studio = new LookThumbs { Name = "LookThumbs" };
        tree.Root.CallDeferred(Node.MethodName.AddChild, studio);
    }

    /* ------------------------------------------------------------- studio -- */

    SubViewport view = null!;
    Node3D stage = null!;
    Camera3D cam = null!;
    (string Key, string Slot, int Size)? taking;
    int wait;
    string framing = "body";

    /// <summary>Camera from her own bones once she stands: Body neck to knee, Head crown to shoulders, Feet knee down.</summary>
    void Frame()
    {
        Skeleton3D? sk = null;
        foreach (var c in stage.GetChildren()) if (c is PersonView pv) sk = Find(pv);
        if (sk == null) return;
        Vector3 At(string bone) => sk.GlobalTransform * sk.GetBoneGlobalPose(Mathf.Max(0, sk.FindBone(bone))).Origin;
        Vector3 head = At("Head"), pelvis = At("pelvis"), foot = At("foot_l");
        float knee = foot.Y + (pelvis.Y - foot.Y) * 0.5f;
        var (top, bottom) = framing switch
        {
            "head" => (head.Y + 0.3f, head.Y - 0.2f),
            "feet" => (knee + 0.04f, foot.Y - 0.05f),
            _ => (head.Y + 0.03f, knee),
        };
        float h = (top - bottom) * (framing == "head" ? 1.5f : 1.1f);
        var at = new Vector3(head.X, (top + bottom) / 2, 0);
        float dist = h / 2 / Mathf.Tan(Mathf.DegToRad(cam.Fov / 2));
        var from = at + new Vector3(0, 0.02f, dist);
        cam.Transform = new Transform3D(Basis.LookingAt(at - from, Vector3.Up), from);
    }

    static Skeleton3D? Find(Node n)
    {
        foreach (var c in n.GetChildren()) { if (c is Skeleton3D s) return s; if (Find(c) is { } d) return d; }
        return null;
    }

    public override void _Ready()
    {
        view = new SubViewport { Size = new Vector2I(256, 256), TransparentBg = true, OwnWorld3D = true, Msaa3D = Viewport.Msaa.Msaa4X, RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled };
        AddChild(view);
        view.AddChild(new WorldEnvironment
        {
            Environment = new Godot.Environment
            {
                BackgroundMode = Godot.Environment.BGMode.ClearColor, BackgroundColor = new Color(0, 0, 0, 0),
                AmbientLightSource = Godot.Environment.AmbientSource.Color, AmbientLightColor = new Color("#4a4440"), AmbientLightEnergy = 0.7f,
                TonemapMode = Godot.Environment.ToneMapper.Agx,
            },
        });
        stage = new Node3D();
        view.AddChild(stage);
        // (the item studio's lamps: a warm key high left in front, a cool rim behind, plus a soft fill)
        stage.AddChild(Lamp("#ffe2b8", 1.8f, new Vector3(-3, 4, 4)));
        stage.AddChild(Lamp("#8ab0ff", 1.5f, new Vector3(3, 2, -4)));
        stage.AddChild(Lamp("#c0a890", 0.6f, new Vector3(2, 1, 5)));
        cam = new Camera3D { Fov = 24, Current = true };
        view.AddChild(cam);
    }

    static DirectionalLight3D Lamp(string c, float energy, Vector3 from) => new()
    {
        LightColor = new Color(c), LightEnergy = energy,
        Transform = new Transform3D(Basis.Identity, from).LookingAt(Vector3.Zero, Vector3.Up),
    };

    /// <summary>Her with only this look shown: her own equipment off, no dyes, the look collected.</summary>
    static CharacterData? Wearing(string defId, string slot)
    {
        var src = Her ?? (Engine.GetMainLoop() is SceneTree t ? FindGame(t.Root)?.Journey.Ch : null);
        if (src == null) return null;
        var ch = Core.Json.Clone(src);
        ch.Equipment = new Equipment();
        ch.Looks ??= new(); ch.Looks.Add(defId);
        ch.Shown = new() { [slot] = defId };
        ch.Dyes = new();
        ch.Headgear = true;
        return ch;
    }

    static Game? FindGame(Node n)
    {
        foreach (var c in n.GetChildren()) { if (c is Game g) return g; }
        return null;
    }

    public override void _Process(double delta)
    {
        if (taking is { } cur)
        {
            if (--wait == 3) Frame();
            if (wait > 0) return;
            view.RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled;
            Develop(cur.Key, cur.Size, view.GetTexture().GetImage());
            taking = null;
        }
        while (queue.Count > 0)
        {
            var (key, def, slot, size) = queue.Dequeue();
            if (!Stage(def, slot, size)) { queued.Remove(key); continue; }
            taking = (key, slot, size);
            wait = 6;
            view.RenderTargetUpdateMode = SubViewport.UpdateMode.Always;
            return;
        }
    }

    bool Stage(string defId, string slot, int size)
    {
        foreach (var c in stage.GetChildren()) if (c is PersonView) { stage.RemoveChild(c); c.QueueFree(); }
        if (Wearing(defId, slot) is not { } ch) return false;
        var lo = Loadouts.Of(ch);
        var v = new PersonView(lo.Person, null, 0.8);
        EraseNoMore(v);
        stage.AddChild(v);
        v.Rotation = new Vector3(0, 0.3f, 0);
        v.Loop("Idle_Loop", 0);
        v.Settle();
        int px = Mathf.Max(192, size * 2);
        view.Size = new Vector2I(px, px);
        framing = slot;
        return true;
    }

    void Develop(string key, int size, Image img)
    {
        img.ClearMipmaps();
        int px = Mathf.Max(192, size * 2);
        if (img.GetWidth() != px) img.Resize(px, px, Image.Interpolation.Lanczos);
        img.SavePng(ProjectSettings.GlobalizePath(PathOf(key)));
        img.GenerateMipmaps();
        var tex = ImageTexture.CreateFromImage(img);
        done[key] = tex;
        if (waiting.Remove(key, out var l)) foreach (var r in l) if (GodotObject.IsInstanceValid(r)) r.Texture = tex;
    }

    /// <summary>Her hair, brows and paint carry a last pass that erases the picture's alpha (the world's FSR 2 reactive mask); off here, as Portrait does.</summary>
    static void EraseNoMore(Node n)
    {
        foreach (var c in n.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (c is not MeshInstance3D mi || mi.Mesh == null) continue;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var m = mi.GetSurfaceOverrideMaterial(s);
                while (m != null)
                {
                    if (m.NextPass is ShaderMaterial next && next.Shader?.ResourcePath.EndsWith("_erase.gdshader") == true) m.NextPass = next.NextPass;
                    else m = m.NextPass;
                }
            }
        }
    }
}
