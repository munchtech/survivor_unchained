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
    public const int Version = 3;

    const int Px = 256;

    static ItemPhotos? studio;
    static readonly Dictionary<string, ImageTexture> photos = new();
    static readonly Dictionary<string, List<TextureRect>> waiting = new();
    // The photographs as taken (256 px, no mipmaps), for the small crisp takes of StoneIcon.
    static readonly Dictionary<string, Image> sources = new();
    static readonly Dictionary<(string, int, int), ImageTexture> stones = new();
    static readonly Dictionary<string, List<(TextureRect Rect, int W, int H)>> stonesWaiting = new();

    readonly Queue<string> queue = new();
    /// Photographs shaded and saved on a worker, waiting to be put up.
    readonly ConcurrentQueue<(string Key, Image Image)> developed = new();
    int developing;
    bool quitAfter;
    SubViewport view = null!;
    Node3D holder = null!;
    string? taking;
    int wait;

    static string PathOf(string key) => $"user://icons/{key.Replace(':', '_').Replace('/', '_')}.v{Version}.png";

    /// <summary>Reads back the photographs already taken and sets up the
    /// studio to take the rest, a frame or two each. Quitting after: every
    /// photograph taken afresh, then the game closes (--icons).</summary>
    public static void Open(Node host, bool quitAfter = false)
    {
        if (studio != null) return;
        var todo = new List<string>();
        // --icons a,b: only those taken again.
        var only = quitAfter && Args.Get("icons") is { } list && list != "1" ? new HashSet<string>(list.Split(',')) : null;
        foreach (var key in only ?? ItemModels.Keys)
        {
            if (photos.ContainsKey(key)) continue;
            if (!quitAfter && !Args.Has("icons-fresh") && FileAccess.FileExists(PathOf(key)) && Image.LoadFromFile(PathOf(key)) is { } img && !img.IsEmpty())
            {
                sources[key] = (Image)img.Duplicate();
                photos[key] = Texture(img);
                continue;
            }
            todo.Add(key);
        }
        if (todo.Count == 0 || DisplayServer.GetName() == "headless")
        {
            if (quitAfter) QuitPath.Request(host.GetTree());
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

    /// <summary>An item's painted icon or photograph as a texture (null until one exists), for a view that draws it itself.</summary>
    public static Texture2D? Real(string key) => UiArt.Icon("item", key) ?? Photo(key);

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
        // A painted icon (art/ui/icons/item/KEY.png) wins over the photograph.
        if (UiArt.Icon("item", key) is { } painted) { r.Texture = painted; return box; }
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

    /// <summary>A small stone, crisp (bd-ui W19): the photograph cropped to the stone's own edge and set down at exactly
    /// w x h pixels with a Lanczos filter (a 4x-and-more supersample of the 256 px take: the glint and the facets stay
    /// what they are at 256, none of it smeared by a mipmap), centred in a `box` px square. Until the photograph exists,
    /// the glyph stands in. Row stones are 30 x 24 in a 32 box, a well's 40 x 30.</summary>
    public static Control StoneIcon(string key, int w, int h, int box, Color glyph)
    {
        var holder = new Control { CustomMinimumSize = new Vector2(box, box), MouseFilter = Control.MouseFilterEnum.Ignore };
        var r = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, TextureFilter = CanvasItem.TextureFilterEnum.Linear,
            MouseFilter = Control.MouseFilterEnum.Ignore, AnchorLeft = 0.5f, AnchorRight = 0.5f, AnchorTop = 0.5f, AnchorBottom = 0.5f,
            OffsetLeft = -w / 2f, OffsetRight = w - w / 2f, OffsetTop = -h / 2f, OffsetBottom = h - h / 2f,
        };
        holder.AddChild(r);
        if (UiArt.Icon("item", key) is { } painted) { r.Texture = painted; return holder; }
        if (sources.ContainsKey(key)) { r.Texture = StoneTexture(key, w, h); return holder; }
        r.Texture = Glyphs.Texture(key, box * 2, glyph);
        if (studio != null && ItemModels.Has(key))
        {
            if (!stonesWaiting.TryGetValue(key, out var l)) stonesWaiting[key] = l = new();
            l.Add((r, w, h));
        }
        return holder;
    }

    static ImageTexture StoneTexture(string key, int w, int h)
    {
        if (stones.TryGetValue((key, w, h), out var have)) return have;
        var src = (Image)sources[key].Duplicate();
        src.Convert(Image.Format.Rgba8);
        // Its edge: where the stone is (the shadow under it is a faint alpha, left out).
        int x0 = src.GetWidth(), y0 = src.GetHeight(), x1 = -1, y1 = -1;
        for (int y = 0; y < src.GetHeight(); y++)
            for (int x = 0; x < src.GetWidth(); x++)
                if (src.GetPixel(x, y).A > 0.75f) { x0 = Mathf.Min(x0, x); y0 = Mathf.Min(y0, y); x1 = Mathf.Max(x1, x); y1 = Mathf.Max(y1, y); }
        if (x1 < 0) { x0 = 0; y0 = 0; x1 = src.GetWidth() - 1; y1 = src.GetHeight() - 1; }
        var crop = src.GetRegion(new Rect2I(x0, y0, x1 - x0 + 1, y1 - y0 + 1));
        // Straight-alpha edges resized through premultiplied colour, so no dark fringe.
        crop.PremultiplyAlpha();
        crop.Resize(w, h, Image.Interpolation.Lanczos);
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                var c = crop.GetPixel(x, y);
                if (c.A > 0.001f) crop.SetPixel(x, y, new Color(Mathf.Min(1, c.R / c.A), Mathf.Min(1, c.G / c.A), Mathf.Min(1, c.B / c.A), c.A));
            }
        var tex = ImageTexture.CreateFromImage(crop);
        stones[(key, w, h)] = tex;
        return tex;
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
        sources[key] = (Image)img.Duplicate();
        var tex = Texture(img);
        photos[key] = tex;
        stones.Clear();
        if (stonesWaiting.Remove(key, out var sl))
            foreach (var (rect, w, h) in sl) if (IsInstanceValid(rect)) rect.Texture = StoneTexture(key, w, h);
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
        if (quitAfter) { QuitPath.Request(GetTree()); return; }
        QueueFree();
    }
}
