using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (--hud drowned): the Flare as a live coal held in the river's eddy, in place of the art's
/// glass (Vessel.Coal). A lump of real charcoal (art/ui/dg_meters/coal_map.png, tools/uiforge/dg_coal.py, from a Krea
/// painting), its own lumpy silhouette sitting low in the eddy's dark cup, under shaders/hud_dg_coal.gdshader.
/// Round 3 (the judge: "a dark porthole", "only the lower cracks"): the heat front climbs the coal from its foot to
/// its top with the meter, the cracks below it orange-gold with a hot leading edge and the dark above, so the amount
/// reads at a glance; full, every crack white-gold top to bottom, a slow heat breath (3.3 s), 6 to 10 embers rising
/// and its light on the eddy's bronze (a BOOM button begging to be pressed); a press (the meter falling from full)
/// flashes it orange, throws streaked embers and lets flakes of ash sink, and it cools to refill. Its rect is the eddy's hole and the room its light needs (Ext hole radii each way).
/// </summary>
public partial class DgCoal : ColorRect
{
    public const float Ext = 2.6f;
    static readonly StringName ULevel = "level", UBurst = "burst";
    readonly ShaderMaterial mat;
    readonly DgSparks sparks;
    /// <summary>The meter, 0 to 1 (the art's level).</summary>
    public float Level;
    float shown = -1, burst = -1, held;
    static readonly float Hold = Args.Num("coal-burst-hold", -1f);

    public DgCoal()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        ProcessMode = ProcessModeEnum.Always;
        float r = DgRiver.FlareR;
        Size = Vector2.One * 2 * r * Ext;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_coal.gdshader") };
        var geo = DgMeterGeo.Coal();
        if (UiArt.Tex("dg_meters/coal_map.png") is { } map && map.GetImage() is { } img)
        {
            // (with its mips: the shader reads a coarse one for the coal's light round it)
            if (img.IsCompressed()) img.Decompress();
            if (!img.HasMipmaps()) img.GenerateMipmaps();
            mat.SetShaderParameter("coal", ImageTexture.CreateFromImage(img));
        }
        else GD.PushError("DgCoal: dg_meters/coal_map.png did not load: the coal draws blank");
        mat.SetShaderParameter("ext", Ext);
        mat.SetShaderParameter("px", r);
        mat.SetShaderParameter("k", geo.K);
        mat.SetShaderParameter("off", geo.Off);
        mat.SetShaderParameter("y0", geo.Y0);
        mat.SetShaderParameter("y1", geo.Y1);
        Material = mat;
        Color = Colors.White;
        sparks = new DgSparks(r * geo.K, geo.Off * r) { Position = Size / 2 };
        AddChild(sparks);
    }

    public override void _Process(double delta)
    {
        float dt = Math.Min((float)delta, 0.1f);
        // a press: the meter drops from full (held full for a moment first, so a pin or a load does not count)
        if (held > 0.2f && Level < shown - 0.3f) { burst = 0; sparks.Burst(); }
        held = Level >= 0.98f ? held + dt : 0;
        // (--coal-burst-hold S, for the shots: a press's look held S seconds after it, sparks and all)
        float sdt = dt;
        if (burst >= 0)
        {
            burst += dt;
            if (Hold >= 0 && burst >= Hold) { sdt = Math.Max(0, dt - (burst - Hold)); burst = Hold; }
            if (burst > 2.4f) burst = -1;
            mat.SetShaderParameter(UBurst, burst);
        }
        if (Level != shown) { shown = Level; mat.SetShaderParameter(ULevel, Level); }
        sparks.Full = Level >= 0.999f;
        if (sdt > 0 || burst < 0) sparks.Tick(sdt > 0 ? sdt : dt);
    }
}

/// <summary>The coal's placement in the eddy's hole (art/ui/dg_meters/meters_geo.json "coal", written by
/// tools/uiforge/dg_coal.py): its map's half size and its middle's offset, in the hole's radii.</summary>
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

    public static (float K, Vector2 Off, float Y0, float Y1) Coal()
    {
        if (Geo.TryGetValue("coal", out var v) && v.AsGodotDictionary() is { } c)
            return ((float)c["k"].AsDouble(), new Vector2((float)c["ox"].AsDouble(), (float)c["oy"].AsDouble()),
                c.TryGetValue("y0", out var a) ? (float)a.AsDouble() : -0.84f, c.TryGetValue("y1", out var b) ? (float)b.AsDouble() : 0.84f);
        return (0.9f, new Vector2(0, 0.05f), -0.84f, 0.84f);
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
