using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading.Tasks;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Ui;

/// <summary>
/// An item's picture is a photograph of it (the web game's itemIcons.ts,
/// remade). Each item (ItemModels) is set on a turntable in a studio of its
/// own: a warm key light from the upper left, a cool rim from behind, and a
/// photographer's studio all round (Poly Haven's studio_small_08, CC0) for
/// fill and for what metal and glass reflect; photographed on nothing, then
/// given a soft shadow. Photographs are kept in the user folder (icons/),
/// so each is taken once; until it is (and in a run with nothing to render
/// with) the item's glyph stands in, and takes the photograph's place when it
/// is ready.
/// </summary>
public partial class ItemPhotos : Node
{
    /// <summary>Bump when what the photographs show changes.</summary>
    public const int Version = 1;

    const int Px = 256;

    static ItemPhotos? studio;
    static readonly Dictionary<string, ImageTexture> photos = new();
    static readonly Dictionary<string, List<TextureRect>> waiting = new();

    readonly Queue<string> queue = new();
    /// Photographs shaded and saved on a worker, waiting to be put up.
    readonly ConcurrentQueue<(string Key, Image Image)> developed = new();
    int developing;
    bool quitAfter;
    SubViewport view = null!;
    Node3D holder = null!;
    string? taking;
    int wait;

    static string PathOf(string key) => $"user://icons/{key}.v{Version}.png";

    /// <summary>Reads back the photographs already taken and sets up the
    /// studio to take the rest, a frame or two each. Quitting after: every
    /// photograph taken afresh, then the game closes (--icons).</summary>
    public static void Open(Node host, bool quitAfter = false)
    {
        if (studio != null) return;
        var todo = new List<string>();
        // --icons a,b: only those taken again.
        var only = quitAfter && Args.Get("icons") is { } list && list != "1" ? new HashSet<string>(list.Split(',')) : null;
        foreach (var key in ItemModels.Keys)
        {
            if (only != null && !only.Contains(key)) continue;
            if (photos.ContainsKey(key)) continue;
            if (!quitAfter && !Args.Has("icons-fresh") && FileAccess.FileExists(PathOf(key)) && Image.LoadFromFile(PathOf(key)) is { } img && !img.IsEmpty())
            {
                photos[key] = Texture(img);
                continue;
            }
            todo.Add(key);
        }
        if (todo.Count == 0 || DisplayServer.GetName() == "headless")
        {
            if (quitAfter) host.GetTree().Quit();
            return;
        }
        DirAccess.MakeDirRecursiveAbsolute("user://icons");
        studio = new ItemPhotos { quitAfter = quitAfter, Name = "ItemPhotos" };
        foreach (var k in todo) studio.queue.Enqueue(k);
        host.AddChild(studio);
    }

    static ImageTexture Texture(Image img)
    {
        img.GenerateMipmaps();
        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>An item's photograph, if it has been taken.</summary>
    public static Texture2D? Photo(string key) => photos.GetValueOrDefault(key);

    /// <summary>An item's picture as a control: its photograph, or its glyph
    /// (smaller, in the colour given) until the photograph is taken.</summary>
    public static Control Icon(string key, int size, Color glyph)
    {
        var box = new Control { CustomMinimumSize = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Ignore };
        var r = new TextureRect
        {
            AnchorRight = 1, AnchorBottom = 1, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered,
            MouseFilter = Control.MouseFilterEnum.Ignore, TextureFilter = CanvasItem.TextureFilterEnum.LinearWithMipmaps,
        };
        box.AddChild(r);
        if (photos.TryGetValue(key, out var t)) { r.Texture = t; return box; }
        r.Texture = Glyphs.Texture(key, size * 2, glyph);
        float inset = size * 0.14f;
        r.OffsetLeft = r.OffsetTop = inset;
        r.OffsetRight = r.OffsetBottom = -inset;
        if (studio != null && ItemModels.Has(key))
        {
            if (!waiting.TryGetValue(key, out var l)) waiting[key] = l = new();
            l.Add(r);
        }
        return box;
    }

    /* ------------------------------------------------------------- studio -- */

    public override void _Ready()
    {
        view = new SubViewport
        {
            Size = new Vector2I(Px, Px), TransparentBg = true, OwnWorld3D = true, Msaa3D = Viewport.Msaa.Msaa8X,
            RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled,
        };
        AddChild(view);
        var sky = new Sky
        {
            SkyMaterial = new PanoramaSkyMaterial { Panorama = GD.Load<Texture2D>("res://art/studio/studio_small_08_1k.hdr") },
            ProcessMode = Sky.ProcessModeEnum.Quality,
        };
        view.AddChild(new WorldEnvironment
        {
            Environment = new Godot.Environment
            {
                BackgroundMode = Godot.Environment.BGMode.ClearColor, Sky = sky,
                AmbientLightSource = Godot.Environment.AmbientSource.Sky, AmbientLightEnergy = 0.5f,
                ReflectedLightSource = Godot.Environment.ReflectionSource.Sky,
                TonemapMode = Godot.Environment.ToneMapper.Aces, TonemapExposure = 0.92f,
            },
        });
        view.AddChild(new Camera3D { Fov = 26, Transform = new Transform3D(Basis.Identity, new Vector3(0, 0.4f, 5)).LookingAt(Vector3.Zero, Vector3.Up), Current = true });
        view.AddChild(Lamp("#ffe2b8", 1.6f, new Vector3(-3, 4, 4), true));
        view.AddChild(Lamp("#8ab0ff", 1.5f, new Vector3(3, 2, -4), false));
        holder = new Node3D();
        view.AddChild(holder);
    }

    static DirectionalLight3D Lamp(string c, float energy, Vector3 from, bool shadow) => new()
    {
        LightColor = new Color(c), LightEnergy = energy, ShadowEnabled = shadow, DirectionalShadowMaxDistance = 12,
        Transform = new Transform3D(Basis.Identity, from).LookingAt(Vector3.Zero, Vector3.Up),
    };

    public override void _Process(double delta)
    {
        while (developed.TryDequeue(out var d)) Show(d.Key, d.Image);
        if (taking != null)
        {
            // A few frames drawn, so what loads or compiles on the first is in the last.
            if (--wait > 0) return;
            view.RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled;
            Develop(taking, view.GetTexture().GetImage());
            taking = null;
        }
        while (queue.Count > 0)
        {
            var key = queue.Dequeue();
            if (!Stage(key)) continue;
            taking = key;
            wait = 3;
            view.RenderTargetUpdateMode = SubViewport.UpdateMode.Always;
            return;
        }
        if (developing == 0 && developed.IsEmpty) Done();
    }

    /// <summary>The item on the turntable, posed, and framed to fill the picture.</summary>
    bool Stage(string key)
    {
        foreach (var c in holder.GetChildren()) { holder.RemoveChild(c); c.QueueFree(); }
        if (ItemModels.Make(key) is not { } made) { GD.PushWarning($"item photograph {key}: nothing to photograph"); return false; }
        var (model, pose) = made;
        var pivot = new Node3D { Transform = new Transform3D(pose.Basis, Vector3.Zero) };
        pivot.AddChild(model);
        if (Bounds(pivot, pivot.Transform, null) is not Aabb box || box.Size.LengthSquared() < 1e-8f)
        {
            GD.PushWarning($"item photograph {key}: nothing to see");
            pivot.Free();
            return false;
        }
        var s = box.Size;
        float k = 2.1f / Mathf.Max(Mathf.Max(s.X, s.Y), Mathf.Max(s.Z * 0.8f, 1e-3f)) * pose.Scale;
        holder.Scale = Vector3.One * k;
        holder.Position = -box.GetCenter() * k;
        holder.AddChild(pivot);
        foreach (var l in pivot.FindChildren("*", nameof(OmniLight3D), true, false)) ((OmniLight3D)l).OmniRange *= k;
        return true;
    }

    static Aabb? Bounds(Node n, Transform3D at, Aabb? box)
    {
        if (n is MeshInstance3D { Mesh: not null } mi)
        {
            var b = at * mi.GetAabb();
            box = box is Aabb a ? a.Merge(b) : b;
        }
        foreach (var c in n.GetChildren()) box = Bounds(c, c is Node3D c3 ? at * c3.Transform : at, box);
        return box;
    }

    /// <summary>The shading and saving off the main thread, so taking the
    /// photographs never stalls a frame.</summary>
    void Develop(string key, Image img)
    {
        System.Threading.Interlocked.Increment(ref developing);
        Task.Run(() =>
        {
            try
            {
                img.Convert(Image.Format.Rgba8);
                Shade(img);
                img.SavePng(PathOf(key));
                developed.Enqueue((key, img));
            }
            finally { System.Threading.Interlocked.Decrement(ref developing); }
        });
    }

    void Show(string key, Image img)
    {
        var tex = Texture(img);
        photos[key] = tex;
        if (!waiting.Remove(key, out var list)) return;
        foreach (var r in list)
        {
            if (!IsInstanceValid(r)) continue;
            r.Texture = tex;
            r.OffsetLeft = r.OffsetTop = r.OffsetRight = r.OffsetBottom = 0;
        }
    }

    /// <summary>The photograph on nothing: its colour where it is only partly
    /// there (at its edges, through glass) no longer darkened by the empty
    /// backdrop it was drawn over, and a soft shadow below and behind it.</summary>
    static void Shade(Image img)
    {
        int w = img.GetWidth(), h = img.GetHeight();
        var px = img.GetData();
        var alpha = new float[w * h];
        for (int i = 0; i < w * h; i++) alpha[i] = px[i * 4 + 3] / 255f;
        var shadow = Blur(alpha, w, h, 6);
        const int Dx = 3, Dy = 7;
        const float Dark = 0.5f;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                int i = y * w + x;
                float a = alpha[i];
                int sx = x - Dx, sy = y - Dy;
                float sh = sx >= 0 && sy >= 0 ? shadow[sy * w + sx] * Dark : 0;
                float outA = a + sh * (1 - a);
                if (outA <= 0) continue;
                // Premultiplied as drawn: colour over its own alpha, then over the shadow's black.
                for (int c = 0; c < 3; c++)
                {
                    float straight = a > 0 ? Mathf.Min(1, px[i * 4 + c] / 255f / a) : 0;
                    px[i * 4 + c] = (byte)Mathf.Clamp(Mathf.Round(straight * a / outA * 255), 0, 255);
                }
                px[i * 4 + 3] = (byte)Mathf.Round(outA * 255);
            }
        img.SetData(w, h, false, Image.Format.Rgba8, px);
    }

    /// <summary>A box blur, three times over (near enough a Gaussian).</summary>
    static float[] Blur(float[] src, int w, int h, int r)
    {
        var a = (float[])src.Clone();
        var b = new float[a.Length];
        for (int pass = 0; pass < 3; pass++)
        {
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float s = 0;
                    for (int k = -r; k <= r; k++) s += a[y * w + Mathf.Clamp(x + k, 0, w - 1)];
                    b[y * w + x] = s / (2 * r + 1);
                }
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float s = 0;
                    for (int k = -r; k <= r; k++) s += b[Mathf.Clamp(y + k, 0, h - 1) * w + x];
                    a[y * w + x] = s / (2 * r + 1);
                }
        }
        return a;
    }

    void Done()
    {
        SetProcess(false);
        foreach (var c in holder.GetChildren()) c.QueueFree();
        studio = null;
        waiting.Clear();
        if (quitAfter) { GetTree().Quit(); return; }
        QueueFree();
    }
}
