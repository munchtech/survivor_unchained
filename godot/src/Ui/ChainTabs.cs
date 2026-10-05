using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The day's book's tabs riding a chain (the owner: "maybe we slide along the chain as we slide
/// tabs in that part of the ui, that could be really cool, especially with a sound - an organic
/// chain not just the same image either"). The links run along a shallow sag under the names,
/// face-on and edge-on in turn; under the open tab one link is pried open and heated through.
/// Turning a tab slides the whole chain on a spring until that link settles under the new one,
/// overshooting by a fraction of a link; the sag dips as it runs and bobs once as it stops; and it
/// rattles (Sfx.ChainSlide). UI art's links (art/ui/chain/, tools/uiforge/chainanim.py, the motion
/// this follows): each link keeps its own picture as it travels, picked from its own place along
/// the chain, so it never reads as one image repeated. Until the art is there, links are drawn.
/// </summary>
public partial class ChainTabs : Control
{
    /// <summary>
    /// How the chain is made and how it moves, from art/ui/chain/chain.json where UI art tunes it
    /// (the owner found the first "a little wimpy"): its pitch and fade, the slide's spring, the
    /// sag's rest, its dip with speed and its spring, and the heated run under the open tab, a span
    /// of links hottest at its middle and cooling to dull red at its ends.
    /// </summary>
    sealed class Feel
    {
        public float Pitch = 16, Fade = 36, Run = 64;
        public int Variants = 6, Heat = 2;
        public float SlideK = 210, SlideC = 24, SagRest = 4.5f, SagDip = 4.5f, SagSpeed = 240, SagK = 110, SagC = 9;

        public static Feel Load()
        {
            var f = new Feel();
            var path = $"{UiArt.Root}chain/chain.json";
            if (!FileAccess.FileExists(path)) return f;
            try
            {
                using var doc = System.Text.Json.JsonDocument.Parse(FileAccess.GetFileAsString(path));
                var r = doc.RootElement;
                float N(string k, float d) => r.TryGetProperty(k, out var e) && e.ValueKind == System.Text.Json.JsonValueKind.Number ? e.GetSingle() : d;
                (float, float) Pair(string k, float a, float b) =>
                    r.TryGetProperty(k, out var e) && e.ValueKind == System.Text.Json.JsonValueKind.Array && e.GetArrayLength() >= 2 ? (e[0].GetSingle(), e[1].GetSingle()) : (a, b);
                f.Pitch = N("pitch", f.Pitch);
                f.Fade = N("fade", f.Fade);
                f.Run = N("run", f.Run);
                f.Variants = (int)N("variants", f.Variants);
                // (heat: links each side of the open one that glow; a span of 2 is five links)
                f.Heat = (int)N("heat", f.Heat);
                (f.SlideK, f.SlideC) = Pair("slide", f.SlideK, f.SlideC);
                (f.SagK, f.SagC) = Pair("sag_spring", f.SagK, f.SagC);
                f.SagRest = N("sag_rest", f.SagRest);
                f.SagDip = N("sag_dip", f.SagDip);
                f.SagSpeed = N("sag_speed", f.SagSpeed);
            }
            catch (Exception e) { GD.PushWarning($"chain.json: {e.Message}"); }
            return f;
        }
    }

    static Feel? feel;
    static Feel F => feel ??= Feel.Load();
    float Pitch => F.Pitch;
    float Fade => F.Fade;
    float Run => F.Run;
    int Variants => Math.Max(1, F.Variants);
    readonly int on;
    readonly HBoxContainer row;
    // Each tab is a screen of its own: the chain's place is kept across them, so the slide starts
    // where the last screen left it.
    static float lastX = float.NaN;
    static ulong lastAt;
    float x, v, sag, sagV, chainY;
    bool placed;

    public ChainTabs((string Name, string Key)[] tabs, int on, Action<int> pick)
    {
        this.on = on;
        MouseFilter = MouseFilterEnum.Ignore;
        // The links are made at twice their size: drawn smaller, and turned on the sag, they want mipmaps.
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        bool pad = Controls.Instance?.UsingPad == true;
        row = Style.H(26);
        if (pad) row.AddChild(Style.PadButton("LB"));
        for (int i = 0; i < tabs.Length; i++)
        {
            int k = i;
            var b = new Button { FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, Flat = true };
            foreach (var s in new[] { "normal", "hover", "pressed", "focus" })
                b.AddThemeStyleboxOverride(s, new StyleBoxEmpty { ContentMarginLeft = 0, ContentMarginRight = 0 });
            var inner = Style.H(8, Style.Label(tabs[i].Name, Style.UiBold, 16, i == on ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false));
            if (!pad) inner.AddChild(Style.Key(tabs[i].Key));
            inner.MouseFilter = MouseFilterEnum.Ignore;
            b.AddChild(inner);
            b.CustomMinimumSize = inner.GetCombinedMinimumSize();
            b.MouseEntered += () => { if (k != on) inner.Modulate = new Color(1.25f, 1.2f, 1.1f); };
            b.MouseExited += () => inner.Modulate = Colors.White;
            b.Pressed += () => { if (k != on) pick(k); };
            // The tabs are turned with LB and RB (or [ and ]), not walked to.
            Nav.Skip(b);
            row.AddChild(b);
        }
        if (pad) row.AddChild(Style.PadButton("RB"));
        AddChild(row);
        glow = new HeatGlow(this);
        AddChild(glow);
        var min = row.GetCombinedMinimumSize();
        chainY = min.Y + 9;
        CustomMinimumSize = new Vector2(min.X, chainY + 16);
    }

    /// <summary>A tab's middle, in this control's own pixels.</summary>
    float Centre(int tab)
    {
        int i = 0;
        foreach (var c in row.GetChildren())
        {
            if (c is not Button b) continue;
            if (i++ == tab) return b.Position.X + b.Size.X / 2;
        }
        return 0;
    }

    int Tabs => row.GetChildren().Count(c => c is Button);

    public override void _Process(double delta)
    {
        float goal = Centre(on);
        if (!placed)
        {
            if (row.Size.X <= 0) return;
            placed = true;
            sag = F.SagRest;
            bool fresh = !float.IsNaN(lastX) && Time.GetTicksMsec() - lastAt < 1500;
            x = fresh ? lastX : goal;
            if (fresh && Math.Abs(goal - x) > 2) Sound.Sfx.ChainSlide((int)Math.Round(Math.Abs(goal - x) / Pitch), 0.32);
        }
        // The slide: a spring a little under its damping, firm enough that it stops like iron, not rubber.
        float dt = (float)Math.Min(delta, 1 / 30.0);
        v += (F.SlideK * (goal - x) - F.SlideC * v) * dt;
        x += v * dt;
        if (Math.Abs(goal - x) < 0.05f && Math.Abs(v) < 0.5f) { x = goal; v = 0; }
        // The sway: the chain hangs with its weight, dips deeper as it runs, and bobs once as it stops.
        float sagGoal = F.SagRest + Math.Min(Math.Abs(v) / F.SagSpeed, 1) * F.SagDip;
        sagV += (F.SagK * (sagGoal - sag) - F.SagC * sagV) * dt;
        sag += sagV * dt;
        lastX = x;
        lastAt = Time.GetTicksMsec();
        QueueRedraw();
    }

    static readonly Dictionary<string, Texture2D?> sprites = new();

    /// <summary>A link's picture with its mipmaps (made at twice its size, shown at half).</summary>
    static Texture2D? Sprite(string name)
    {
        if (sprites.TryGetValue(name, out var t)) return t;
        var path = $"{UiArt.Root}chain/{name}.png";
        Image? img = null;
        if (ResourceLoader.Exists(path)) img = GD.Load<Texture2D>(path)?.GetImage();
        else if (FileAccess.FileExists(path)) img = Image.LoadFromFile(ProjectSettings.GlobalizePath(path));
        if (img == null || img.IsEmpty()) return sprites[name] = null;
        if (img.IsCompressed()) img.Decompress();
        img.GenerateMipmaps();
        var tex = ImageTexture.CreateFromImage(img);
        tex.SetSizeOverride(new Vector2I(img.GetWidth() / 2, img.GetHeight() / 2));
        return sprites[name] = tex;
    }

    static float Hash(int k, int salt)
    {
        uint h = (uint)(k * 374761393 + salt * 668265263);
        h = (h ^ (h >> 13)) * 1274126177;
        return ((h ^ (h >> 16)) & 0xffff) / 65535f;
    }

    public override void _Draw()
    {
        int n = Tabs;
        if (n == 0) return;
        float x0 = Centre(0) - Run, x1 = Centre(n - 1) + Run, mid = (x0 + x1) / 2, half = (x1 - x0) / 2;
        float Y(float at) { float t = (at - mid) / half; return chainY + sag * (1 - t * t); }
        int k0 = (int)Math.Floor((x0 - x) / Pitch) - 1, k1 = (int)Math.Ceiling((x1 - x) / Pitch) + 1;
        heated.Clear();
        // Face-on links first; those on edge pass through their ends and lie over them.
        for (int pass = 0; pass < 2; pass++)
            for (int k = k0; k <= k1; k++)
            {
                bool face = (k & 1) == 0;
                if (face != (pass == 0)) continue;
                float lx = x + k * Pitch;
                float a = Mathf.Pow(Mathf.Clamp(Math.Min(lx - x0, x1 - lx) / Fade, 0, 1), 1.3f);
                if (a <= 0) continue;
                var at = new Vector2(lx, Y(lx));
                float ang = Mathf.Atan2(Y(lx + 1) - Y(lx - 1), 2);
                int variant = ((k * 7 + 3) % Variants + Variants) % Variants;
                float heat = Heat(k);
                // The heated run: UI art's hot links where they are painted (hot_face_N, hot_edge_N),
                // else the cold link warmed toward the fire's colour; the glow over it is HeatGlow's.
                var hot = heat > 0 && k != 0 ? Sprite($"hot_{(face ? "face" : "edge")}_{variant}") : null;
                var tex = k == 0 && Sprite("open") is { } open ? open : hot ?? Sprite($"{(face ? "face" : "edge")}_{variant}");
                DrawSetTransform(at, ang);
                var tint = hot != null ? new Color(1, 1, 1).Lerp(HeatColour(heat).Lightened(0.5f), 0.25f * (1 - heat))
                    : heat > 0 && k != 0 ? Colors.White.Lerp(HeatColour(heat).Lightened(0.35f), 0.6f * heat) : Colors.White;
                if (tex != null) DrawTexture(tex, -tex.GetSize() / 2, tint with { A = a });
                else DrawLink(k, face, a, heat);
                if (heat > 0) heated.Add((at, heat * a));
            }
        DrawSetTransform(Vector2.Zero);
        glow.QueueRedraw();
    }

    /// <summary>How hot a link is: the open tab's run of links, hottest at its middle (1), cooling to
    /// its ends; the rest cold (0).</summary>
    static float Heat(int k) => Math.Abs(k) > F.Heat ? 0 : 1 - Math.Abs(k) / (F.Heat + 1f);

    /// <summary>Iron by its heat: bright orange at the heart, through ember, to a dull red at the ends.</summary>
    public static Color HeatColour(float h) => h > 0.6f ? new Color("#ff7a26").Lerp(new Color("#ffc070"), (h - 0.6f) / 0.4f) : new Color("#7a2410").Lerp(new Color("#ff7a26"), h / 0.6f);

    /// <summary>Where the heated links lie this frame, and how hot.</summary>
    readonly List<(Vector2 At, float Heat)> heated = new();

    /// <summary>The heat's light, laid over the links additively: a glow round each hot link,
    /// its colour and size by how hot it is.</summary>
    partial class HeatGlow : Control
    {
        static GradientTexture2D? soft;
        readonly ChainTabs chain;

        public HeatGlow(ChainTabs chain)
        {
            this.chain = chain;
            MouseFilter = MouseFilterEnum.Ignore;
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };
            soft ??= new GradientTexture2D
            {
                Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
                Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.35f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.35f, 1f } },
            };
        }

        public override void _Draw()
        {
            foreach (var (at, h) in chain.heated)
            {
                float r = 9 + 9 * h;
                DrawTextureRect(soft!, new Rect2(at - new Vector2(r * 1.4f, r), new Vector2(r * 2.8f, r * 2)), false, HeatColour(h) with { A = 0.18f + 0.32f * h });
            }
        }
    }

    readonly HeatGlow glow;

    /// <summary>A link drawn, until UI art's are there: each a little different by its place on the chain.</summary>
    void DrawLink(int k, bool face, float a, float heat)
    {
        float tone = 0.78f + 0.3f * Hash(k, 1);
        var iron = new Color(0.56f * tone, 0.52f * tone, 0.47f * tone, 0.95f * a).Lerp(HeatColour(heat) with { A = 0.95f * a }, 0.8f * heat);
        if (k == 0)
        {
            DrawCircle(new Vector2(0, 3), 7, new Color(1, 0.5f, 0.15f, 0.2f * a));
            DrawArc(Vector2.Zero, 9, 1.9f, 1.9f + Mathf.Tau - 0.9f, 20, new Color("#d0915a") with { A = a }, 2.4f, true);
            DrawCircle(new Vector2(0, 7), 2.4f, Style.Ember with { A = a });
        }
        else if (face)
        {
            var pts = new Vector2[17];
            for (int i = 0; i <= 16; i++) pts[i] = new Vector2(Mathf.Cos(i * Mathf.Tau / 16) * 11, Mathf.Sin(i * Mathf.Tau / 16) * 6);
            DrawPolyline(pts, iron, 2.4f, true);
        }
        else
        {
            DrawLine(new Vector2(-10, 0), new Vector2(10, 0), iron.Darkened(0.12f), 3.4f, true);
            DrawLine(new Vector2(-9, -1.2f), new Vector2(9, -1.2f), new Color(1, 0.93f, 0.8f, 0.22f * a), 1, true);
        }
    }
}

/// <summary>
/// A panel's title. On a page or a counter whose title does not sit on the tab chain, it hangs
/// between two short lengths of chain (approved on the dressed board, "cool where it is"), each
/// ending at the name in a link pried open, ember in the break: UI art's ornaments/title_chain_l.png
/// and _r.png drawn at their own size outward from the name, their open ends 6 px from the letters,
/// centred on its capitals. The chain is kept for where it means something, so the book's panel,
/// whose tabs already ride one, has the name alone.
/// </summary>
public partial class Title : Control
{
    readonly string text;
    readonly int size;
    readonly float tw;
    readonly bool chains;

    public Title(string text, int size = 30, bool chains = true)
    {
        this.text = text.ToUpperInvariant();
        this.size = size;
        this.chains = chains;
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        tw = Style.Display.GetStringSize(this.text, HorizontalAlignment.Left, -1, size).X;
        float arm = chains ? (UiArt.Art("ornaments/title_chain_l.png")?.GetWidth() ?? 80) + 6 : 0;
        CustomMinimumSize = new Vector2(tw + 2 * arm, size * 1.3f);
        SizeFlagsHorizontal = SizeFlags.ExpandFill;
        Resized += QueueRedraw;
    }

    public override void _Draw()
    {
        float cx = Size.X / 2;
        var font = Style.Display;
        float baseline = Size.Y * 0.5f + size * 0.36f;
        var at = new Vector2(cx - tw / 2, baseline);
        DrawString(font, at + new Vector2(0, 1), text, HorizontalAlignment.Left, -1, size, new Color(0, 0, 0, 0.8f));
        DrawString(font, at, text, HorizontalAlignment.Left, -1, size, Kit.Ink);
        if (!chains) return;
        // The middle of the capitals: where a chain hung from the name would meet it.
        float y = baseline - size * 0.36f;
        var l = UiArt.Art("ornaments/title_chain_l.png");
        var r = UiArt.Art("ornaments/title_chain_r.png");
        if (l != null && r != null)
        {
            var ls = l.GetSize();
            var rs = r.GetSize();
            DrawTexture(l, new Vector2(cx - tw / 2 - 6 - ls.X, y - ls.Y / 2));
            DrawTexture(r, new Vector2(cx + tw / 2 + 6, y - rs.Y / 2));
            return;
        }
        foreach (int side in new[] { -1, 1 })
        {
            float x0 = cx + side * (tw / 2 + 16);
            for (int k = 0; k < 6; k++)
            {
                float lx = x0 + side * k * 12, a = 1 - k / 6f;
                var iron = new Color(0.56f, 0.52f, 0.47f, 0.9f * a);
                if (k == 0)
                {
                    // The link at the name, sprung open toward it, the ember in the gap.
                    float from = side > 0 ? Mathf.Pi + 0.8f : 0.8f;
                    DrawArc(new Vector2(lx, y), 6.5f, from, from + Mathf.Tau - 1.6f, 14, new Color("#c9a46c"), 2, true);
                    DrawCircle(new Vector2(lx - side * 5, y), 2.2f, Style.Ember);
                }
                else if (k % 2 == 1)
                {
                    var pts = new Vector2[13];
                    for (int i = 0; i <= 12; i++) pts[i] = new Vector2(lx + Mathf.Cos(i * Mathf.Tau / 12) * 6.5f, y + Mathf.Sin(i * Mathf.Tau / 12) * 3.8f);
                    DrawPolyline(pts, iron, 1.8f, true);
                }
                else DrawLine(new Vector2(lx - 5.5f, y), new Vector2(lx + 5.5f, y), iron.Darkened(0.1f), 2.6f, true);
            }
        }
    }
}
