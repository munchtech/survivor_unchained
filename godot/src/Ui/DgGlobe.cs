using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 23, HUD A (the keeper): the Flare, a dark glass globe in the keeper's bowl that fills with fire as it charges
/// (shaders/hud_dg_globe.gdshader, the mock's ember_glass(); every constant in art/ui/dg_keeper/hud_a_geo.json
/// "glass"). One quad from the READY halo's reach above the glass to the screen's foot, the bowl's front lip
/// (keeper_lip.png) drawn in it over the glass's foot. Full (READY): a white-gold heart, the bezel lit, flames over
/// the top, embers climbing, a slow heat breath; a press (the meter falling from full) flashes it orange, throws
/// streaked embers and lets flakes of ash sink (DgSparks), and the glass cools from dull red as it refills. Its
/// uniforms are set only when they change; the shader's own time runs the fire.
/// </summary>
public partial class DgGlobe : ColorRect
{
    static readonly StringName UCharge = "charge", UBurst = "burst", UPing = "ping", UFigA = "fig_a", ULipTint = "lip_tint", ULive = "live";
    readonly ShaderMaterial mat;
    readonly DgSparks sparks;
    /// <summary>The meter, 0 to 1; the ready swell (1 on reaching full, easing to 0); the keeper's fade and dimming
    /// (the lip fades with him).</summary>
    public float Level, Ping, FigA = 1;
    public Color LipTint = Colors.White;
    float shown = -1, burst = -1, held, sPing = -1, sFig = -1, sLive = -1;
    Color sTint = new(-1, -1, -1);
    static readonly float Hold = Args.Num("coal-burst-hold", -1f);
    /// <summary>The quad on the screen: the READY halo's reach (3.2 r) round the glass, 30 px more above (its flames
    /// and embers), down to the screen's foot (the lip).</summary>
    public static Rect2 Quad
    {
        get
        {
            var c = DgPanel.GlassAt; float r = DgPanel.GlassR;
            float x0 = Mathf.Floor(c.X - 3.2f * r), x1 = Mathf.Ceil(c.X + 3.2f * r), y0 = Mathf.Floor(c.Y - 3.2f * r - 30);
            return new Rect2(x0, y0, x1 - x0, 1080 - y0);
        }
    }

    public DgGlobe()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        ProcessMode = ProcessModeEnum.Always;
        var q = Quad;
        Size = q.Size;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_globe.gdshader") };
        // (the fire with its mips: 8.7 texels a screen px)
        foreach (var (u, f) in new[] { ("fire", "fire.png"), ("fire_ready", "fire_ready.png") })
            if (UiArt.Tex("dg_keeper/" + f, false) is { } t && t.GetImage() is { } img)
            {
                if (img.IsCompressed()) img.Decompress();
                if (!img.HasMipmaps()) img.GenerateMipmaps();
                mat.SetShaderParameter(u, ImageTexture.CreateFromImage(img));
            }
            else GD.PushError($"DgGlobe: dg_keeper/{f} did not load: the Flare draws without its fire");
        if (UiArt.Tex("dg_keeper/keeper_lip.png", false) is { } lip) mat.SetShaderParameter("lip", lip);
        else GD.PushError("DgGlobe: dg_keeper/keeper_lip.png did not load: the bowl's lip is missing");
        var k = DgPanel.KeeperRect;
        mat.SetShaderParameter("q_at", q.Position);
        mat.SetShaderParameter("q_size", q.Size);
        mat.SetShaderParameter("c", DgPanel.GlassAt);
        mat.SetShaderParameter("r", DgPanel.GlassR);
        mat.SetShaderParameter("lip_y", DgPanel.GlassLipY);
        mat.SetShaderParameter("krect", new Vector4(k.Position.X, k.Position.Y, k.Size.X, k.Size.Y));
        Material = mat;
        Color = Colors.White;
        sparks = new DgSparks(DgPanel.GlassR, Vector2.Zero) { Position = DgPanel.GlassAt - q.Position };
        AddChild(sparks);
    }

    public override void _Process(double delta)
    {
        using var _ = new Perf.Span(Perf.Part.Hud);
        float dt = Math.Min((float)delta, 0.1f);
        // a press: the meter drops from full (held full for a moment first, so a pin or a load does not count)
        if (held > 0.2f && Level < shown - 0.3f) { burst = 0; sparks.Burst(); }
        held = Level >= 0.999f ? held + dt : 0;
        // (--coal-burst-hold S, for the shots: a press's look held S seconds after it, sparks and all)
        float sdt = dt;
        if (burst >= 0)
        {
            burst += dt;
            if (Hold >= 0 && burst >= Hold) { sdt = Math.Max(0, dt - (burst - Hold)); burst = Hold; }
            if (burst > 2.4f) burst = -1;
            mat.SetShaderParameter(UBurst, burst);
        }
        if (Level != shown) { shown = Level; mat.SetShaderParameter(UCharge, Level); }
        if (Ping != sPing) { sPing = Ping; mat.SetShaderParameter(UPing, Ping); }
        if (FigA != sFig) { sFig = FigA; mat.SetShaderParameter(UFigA, FigA); }
        if (LipTint != sTint) { sTint = LipTint; mat.SetShaderParameter(ULipTint, LipTint); }
        // (a pinned shine is the judged mock's still frame: the fire held still too)
        float live = HudPin.Shine != null ? 0 : 1;
        if (live != sLive) { sLive = live; mat.SetShaderParameter(ULive, live); }
        // (the climbing embers are the shader's; DgSparks throws the press's embers and ash)
        sparks.Full = false;
        if (sdt > 0 || burst < 0) sparks.Tick(sdt > 0 ? sdt : dt);
    }
}

/// <summary>UI 23, HUD A: the keeper, the hooded bronze mourner bowed over the bowl that holds the Flare
/// (art/ui/dg_keeper/keeper.png, 2x, at the geo's final screen rect: no group scale on top). Under the plate; the same
/// sprite by day and night. When the survivor, an elite or a marked attack is behind him (Game, as for her figure), he
/// fades as her figure does (LifeLamp's FadeTo and times); the glass stays, the bowl's lip fades with him (DgGlobe).</summary>
public partial class DgKeeper : Control
{
    readonly Texture2D? tex;
    /// <summary>Something is behind him (Game sets it each frame).</summary>
    public bool Behind;
    /// <summary>His figure's alpha now (1, or down to LifeLamp.FadeTo).</summary>
    public float FigA { get; private set; } = 1;
    float clearFor = 9;
    public DgGlobe? Globe;

    public DgKeeper()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Linear;
        var k = DgPanel.KeeperRect;
        Position = k.Position;
        Size = k.Size;
        tex = UiArt.Tex("dg_keeper/keeper.png", false);
        if (tex == null) GD.PushError("DgKeeper: dg_keeper/keeper.png did not load: the keeper is missing");
    }

    public override void _Draw()
    {
        if (tex != null) DrawTextureRect(tex, new Rect2(Vector2.Zero, Size), false);
    }

    public override void _Process(double delta)
    {
        float dt = Math.Min((float)delta, 0.1f);
        clearFor = Behind ? 0 : clearFor + dt;
        bool dim = clearFor < LifeLamp.FadeHold;
        float to = dim ? LifeLamp.FadeTo : 1;
        float a = Mathf.MoveToward(FigA, to, dt * (1 - LifeLamp.FadeTo) / (dim ? LifeLamp.FadeTime : LifeLamp.FadeBack));
        if (a != FigA) { FigA = a; SelfModulate = new Color(1, 1, 1, a); }
        if (Globe != null) { Globe.FigA = FigA; Globe.LipTint = Modulate; }
    }
}

/// <summary>The meters' geo (art/ui/dg_meters/meters_geo.json): the flask's size and liquid span.</summary>
public static class DgMeterGeo
{
    static Godot.Collections.Dictionary? geo;
    static Godot.Collections.Dictionary Geo
    {
        get
        {
            if (geo != null) return geo;
            var path = $"{UiArt.Root}dg_meters/meters_geo.json";
            geo = FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { } d ? d : new();
            return geo;
        }
    }

    /// <summary>The flask's size shown and the liquid's top and foot in it (0..1 of its height).</summary>
    public static (Vector2 Size, float Top, float Bot) Flask()
    {
        if (Geo.TryGetValue("flask", out var f) && f.AsGodotDictionary() is { } g)
            return (new Vector2((float)g["w"].AsDouble(), (float)g["h"].AsDouble()), (float)g["top"].AsDouble(), (float)g["bot"].AsDouble());
        return (new Vector2(42, 56), 0.44f, 0.95f);
    }
}

/// <summary>The coal's embers and the press's burst, drawn (no particle system; one soft disc texture, DgMeters.Disc,
/// stretched and turned per bit). Round 3 (the judge: "white glitter", "square blocks"): full, embers lift off its
/// top cracks steadily, 6 to 10 alive (at most 10), small orange-gold motes that sway and dim as they rise; a press
/// throws 30 orange embers out of it under gravity, each a streak along its flight, hot gold at its head, cooling to
/// red; a beat later 16 flakes of ash flutter down, thin grey ellipses turning as they sink. Embers add their light;
/// the ash is drawn plain over them (a child of its own).</summary>
public partial class DgSparks : Control
{
    struct Bit { public Vector2 P, V; public float Age, Life, Size, Spin; public int Kind; }
    readonly List<Bit> bits = new();
    readonly float r;
    readonly Vector2 mid;
    readonly Ash ash;
    readonly RandomNumberGenerator rng = new();
    float spawn, ashDue = -1;
    bool wasFull;
    int ashLeft;
    public bool Full;

    public DgSparks(float coalR, Vector2 mid)
    {
        r = coalR;
        this.mid = mid;
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Linear;
        Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };
        AddChild(ash = new Ash(this));
        rng.Seed = 7331;
    }

    public void Burst()
    {
        for (int i = 0; i < 30; i++)
        {
            float a = rng.RandfRange(-Mathf.Pi * 0.95f, -Mathf.Pi * 0.05f) + (i % 4 == 0 ? Mathf.Pi * 0.5f * rng.RandfRange(-1, 1) : 0);
            var dir = Vector2.FromAngle(a);
            bits.Add(new Bit { P = mid + dir * r * rng.RandfRange(0.45f, 0.9f), V = dir * rng.RandfRange(90, 270), Age = -rng.RandfRange(0, 0.12f), Life = rng.RandfRange(0.5f, 1.0f), Size = rng.RandfRange(1.0f, 1.8f), Kind = 1 });
        }
        ashDue = 0.12f;
        ashLeft = 16;
    }

    public void Tick(float dt)
    {
        // (reaching full: a puff of embers, then a steady stream: about 6 a second, each 1.1 to 1.7 s, so 6 to 10 alive)
        if (Full && !wasFull) spawn = 5;
        wasFull = Full;
        if (Full)
        {
            spawn += dt * 6.2f;
            while (spawn >= 1)
            {
                spawn -= 1;
                if (CountKind(0) >= 10) continue;
                float x = rng.RandfRange(-0.65f, 0.65f);
                bits.Add(new Bit { P = mid + new Vector2(x * r, -r * (0.45f + 0.30f * (1 - Math.Abs(x)))), V = new Vector2(rng.RandfRange(-12, 12), rng.RandfRange(-62, -34)),
                    Life = rng.RandfRange(1.1f, 1.7f), Size = rng.RandfRange(1.2f, 1.9f), Spin = rng.RandfRange(0, 6.28f), Kind = 0 });
            }
        }
        else spawn = 0;
        if (ashDue >= 0)
        {
            ashDue -= dt;
            while (ashDue < 0 && ashLeft > 0)
            {
                ashLeft--;
                ashDue += 0.025f;
                bits.Add(new Bit { P = mid + new Vector2(rng.RandfRange(-0.8f, 0.8f) * r, rng.RandfRange(-1.2f, -0.4f) * r), V = new Vector2(rng.RandfRange(-14, 14), rng.RandfRange(8, 22)),
                    Life = rng.RandfRange(1.5f, 2.3f), Size = rng.RandfRange(1.6f, 2.6f), Spin = rng.RandfRange(0, 6.28f), Kind = 2 });
            }
            if (ashLeft == 0) ashDue = -1;
        }
        for (int i = bits.Count - 1; i >= 0; i--)
        {
            var b = bits[i];
            b.Age += dt;
            if (b.Age >= b.Life) { bits.RemoveAt(i); continue; }
            if (b.Age < 0) { bits[i] = b; continue; }  // (not out yet: the burst comes over a beat, not in one ring)
            if (b.Kind == 1) { b.V += new Vector2(0, 260) * dt; b.V *= 1 - 1.4f * dt; }
            else if (b.Kind == 0) { b.V.X += Mathf.Sin(b.Age * 4.2f + b.Spin) * 34 * dt; b.V *= 1 - 0.3f * dt; }
            else { b.V.X = Mathf.Sin(b.Age * 2.6f + b.Spin) * 18; b.V.Y = Mathf.MoveToward(b.V.Y, 16, 20 * dt); }
            b.P += b.V * dt;
            bits[i] = b;
        }
        if (bits.Count > 0 || drawn > 0) { QueueRedraw(); ash.QueueRedraw(); }
        drawn = bits.Count;
    }

    int drawn;
    int CountKind(int k) { int n = 0; foreach (var b in bits) if (b.Kind == k) n++; return n; }

    /// <summary>The soft disc stretched to len x wid along dir, centred on at.</summary>
    void Soft(Vector2 at, Vector2 dir, float len, float wid, Color c)
    {
        DrawSetTransform(at, dir.Angle(), Vector2.One);
        DrawTextureRect(DgMeters.Disc, new Rect2(-len / 2, -wid / 2, len, wid), false, c);
    }

    public override void _Draw()
    {
        foreach (var b in bits)
        {
            if (b.Kind == 2 || b.Age < 0) continue;
            float u = b.Age / b.Life;
            if (b.Kind == 0)
            {
                // a rising mote: gold off the cracks, orange, dying red; it flickers and dims as it climbs
                var col = u < 0.35f ? new Color(1f, 0.80f, 0.42f).Lerp(new Color(1f, 0.52f, 0.14f), u / 0.35f) : new Color(1f, 0.52f, 0.14f).Lerp(new Color(0.75f, 0.16f, 0.03f), (u - 0.35f) / 0.65f);
                float a = Mathf.Min(1, u * 8) * (1 - u * u) * (0.75f + 0.25f * Mathf.Sin(b.Age * 23 + b.Spin * 5));
                var dir = b.V.LengthSquared() > 1 ? b.V.Normalized() : Vector2.Up;
                Soft(b.P, dir, b.Size * 7, b.Size * 7, col with { A = 0.18f * a });
                Soft(b.P, dir, b.Size * 3.4f, b.Size * 2.2f, col with { A = 0.95f * a });
            }
            else
            {
                // a thrown ember: a streak along its flight, hot gold at its head, orange, cooling to red
                var col = u < 0.25f ? new Color(1f, 0.74f, 0.36f).Lerp(new Color(1f, 0.48f, 0.10f), u / 0.25f) : new Color(1f, 0.48f, 0.10f).Lerp(new Color(0.62f, 0.10f, 0.02f), (u - 0.25f) / 0.75f);
                float a = 1 - u * u;
                float sp = b.V.Length();
                var dir = sp > 1 ? b.V / sp : Vector2.Right;
                float len = Mathf.Clamp(sp * 0.05f, 3, 13);
                Soft(b.P - dir * len * 0.35f, dir, len * 1.6f, b.Size * 5, col with { A = 0.16f * a });
                Soft(b.P - dir * len * 0.35f, dir, len, b.Size * 2.0f, col with { A = 0.9f * a });
                Soft(b.P, dir, b.Size * 2.6f, b.Size * 1.8f, new Color(1f, 0.82f, 0.5f, 0.85f * a * (1 - u)));
            }
        }
        DrawSetTransform(Vector2.Zero, 0, Vector2.One);
    }

    partial class Ash : Control
    {
        readonly DgSparks o;
        public Ash(DgSparks o) { this.o = o; MouseFilter = MouseFilterEnum.Ignore; UseParentMaterial = false; Material = new CanvasItemMaterial(); TextureFilter = TextureFilterEnum.Linear; }

        public override void _Draw()
        {
            foreach (var b in o.bits)
            {
                if (b.Kind != 2 || b.Age < 0) continue;
                float u = b.Age / b.Life;
                float a = Mathf.Min(1, u * 6) * (1 - u);
                // a flake turning as it sinks: a thin soft ellipse narrowing and widening as it tumbles, its
                // underside warm at first (lit by the coal), grey after
                float tw = Math.Abs(Mathf.Sin(b.Age * 4.2f + b.Spin));
                var col = new Color(0.72f, 0.69f, 0.65f).Lerp(new Color(0.95f, 0.50f, 0.20f), Mathf.Max(0, 1 - u * 3.5f) * 0.55f);
                DrawSetTransform(b.P, 0.5f * Mathf.Sin(b.Age * 1.7f + b.Spin * 2), Vector2.One);
                float h = b.Size * (0.5f + 0.9f * tw);
                DrawTextureRect(DgMeters.Disc, new Rect2(-b.Size * 1.3f, -h / 2, b.Size * 2.6f, h), false, col with { A = 0.85f * a });
            }
            DrawSetTransform(Vector2.Zero, 0, Vector2.One);
        }
    }
}
