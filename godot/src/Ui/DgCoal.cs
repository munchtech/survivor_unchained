using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (--hud drowned): the Flare as a live coal held in the river's eddy, in place of the art's
/// glass (Vessel.Coal). Round 2: a banked ember of real charcoal (art/ui/dg_meters/coal_map.png, tools/uiforge/dg_coal.py,
/// from a Krea painting), its own lumpy silhouette sitting low in the eddy's dark cup, under
/// shaders/hud_dg_coal.gdshader: the heat rises from its foot as the meter fills, the wide fissures going white-hot
/// at their cores while the hairlines stay red; full, it breathes, throws sparks and lays orange light on the eddy's
/// bronze ("press Q"); a press (the meter falling from full) flashes it white, bursts embers out of it and lets ash
/// sink, and it goes dark to refill. Its rect is the eddy's hole and the room its light needs (Ext hole radii each way).
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

    public static (float K, Vector2 Off) Coal()
    {
        if (Geo.TryGetValue("coal", out var v) && v.AsGodotDictionary() is { } c)
            return ((float)c["k"].AsDouble(), new Vector2((float)c["ox"].AsDouble(), (float)c["oy"].AsDouble()));
        return (0.9f, new Vector2(0, 0.05f));
    }

    /// <summary>The flask's size shown and the liquid's top and foot in it (0..1 of its height).</summary>
    public static (Vector2 Size, float Top, float Bot) Flask()
    {
        if (Geo.TryGetValue("flask", out var f) && f.AsGodotDictionary() is { } g)
            return (new Vector2((float)g["w"].AsDouble(), (float)g["h"].AsDouble()), (float)g["top"].AsDouble(), (float)g["bot"].AsDouble());
        return (new Vector2(42, 56), 0.44f, 0.95f);
    }
}

/// <summary>The coal's sparks and the press's burst, drawn (no particle system): full, a spark or two a second lifts
/// off its top (at most 8 alive); a press throws 30 embers out of it under gravity and, a beat later, lets 16 flakes of
/// ash sink. Sparks and embers add their light; the ash is drawn plain, over them (a child of its own).</summary>
public partial class DgSparks : Control
{
    struct Bit { public Vector2 P, V; public float Age, Life, Size; public int Kind; }
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
            bits.Add(new Bit { P = mid + dir * r * rng.RandfRange(0.55f, 1.0f), V = dir * rng.RandfRange(70, 260), Age = -rng.RandfRange(0, 0.14f), Life = rng.RandfRange(0.45f, 0.95f), Size = rng.RandfRange(1.0f, 2.2f), Kind = 1 });
        }
        ashDue = 0.12f;
        ashLeft = 16;
    }

    public void Tick(float dt)
    {
        // (reaching full: a puff of sparks, then a steady few)
        if (Full && !wasFull) spawn = 5;
        wasFull = Full;
        if (Full)
        {
            spawn += dt * 3.5f;
            while (spawn >= 1)
            {
                spawn -= 1;
                if (CountKind(0) >= 10) continue;
                float x = rng.RandfRange(-0.6f, 0.6f);
                bits.Add(new Bit { P = mid + new Vector2(x * r, -r * (0.55f + 0.35f * (1 - Math.Abs(x)))), V = new Vector2(rng.RandfRange(-18, 18), rng.RandfRange(-85, -45)),
                    Life = rng.RandfRange(0.8f, 1.4f), Size = rng.RandfRange(1.3f, 2.0f), Kind = 0 });
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
                bits.Add(new Bit { P = mid + new Vector2(rng.RandfRange(-0.8f, 0.8f) * r, rng.RandfRange(-1.1f, -0.3f) * r), V = new Vector2(rng.RandfRange(-14, 14), rng.RandfRange(6, 22)),
                    Life = rng.RandfRange(1.5f, 2.3f), Size = rng.RandfRange(1.8f, 2.8f), Kind = 2 });
            }
            if (ashLeft == 0) ashDue = -1;
        }
        for (int i = bits.Count - 1; i >= 0; i--)
        {
            var b = bits[i];
            b.Age += dt;
            if (b.Age >= b.Life) { bits.RemoveAt(i); continue; }
            if (b.Age < 0) { bits[i] = b; continue; }  // (not out yet: the burst comes over a beat, not in one ring)
            if (b.Kind == 1) { b.V += new Vector2(0, 240) * dt; b.V *= 1 - 1.6f * dt; }
            else if (b.Kind == 0) { b.V.X += Mathf.Sin(b.Age * 9 + b.Size * 13) * 40 * dt; b.V *= 1 - 0.4f * dt; }
            else { b.V.X = Mathf.Sin(b.Age * 3.1f + b.Size * 7) * 16; }
            b.P += b.V * dt;
            bits[i] = b;
        }
        if (bits.Count > 0 || drawn > 0) { QueueRedraw(); ash.QueueRedraw(); }
        drawn = bits.Count;
    }

    int drawn;
    int CountKind(int k) { int n = 0; foreach (var b in bits) if (b.Kind == k) n++; return n; }

    public override void _Draw()
    {
        foreach (var b in bits)
        {
            if (b.Kind == 2 || b.Age < 0) continue;
            float u = b.Age / b.Life;
            // white-gold, through orange, to a dull red as it dies
            var col = u < 0.3f ? new Color(1f, 0.92f, 0.62f).Lerp(new Color(1f, 0.62f, 0.2f), u / 0.3f) : new Color(1f, 0.62f, 0.2f).Lerp(new Color(0.7f, 0.15f, 0.03f), (u - 0.3f) / 0.7f);
            float a = (1 - u * u) * (b.Kind == 1 ? 1 : 0.85f);
            // a streak along its flight, hot at its head, and a faint glow round the head
            var tail = b.P - b.V * (b.Kind == 1 ? 0.03f : 0.10f);
            DrawCircle(b.P, b.Size * (b.Kind == 0 ? 3.2f : 2.0f), col with { A = (b.Kind == 0 ? 0.22f : 0.12f) * a }, true, -1, true);
            DrawLine(tail, b.P, col with { A = 0.55f * a }, b.Size * (b.Kind == 0 ? 1.1f : 0.8f), true);
            DrawCircle(b.P, b.Size * 0.75f, new Color(1f, 0.95f, 0.8f, 0.95f * a), true, -1, true);
        }
    }

    partial class Ash : Control
    {
        readonly DgSparks o;
        public Ash(DgSparks o) { this.o = o; MouseFilter = MouseFilterEnum.Ignore; UseParentMaterial = false; Material = new CanvasItemMaterial(); }

        public override void _Draw()
        {
            foreach (var b in o.bits)
            {
                if (b.Kind != 2) continue;
                float u = b.Age / b.Life;
                float a = Mathf.Min(1, u * 6) * (1 - u);
                // a flake turning as it sinks: an ellipse's worth of two dots, grey, its lit side warm at first
                float tw = Mathf.Abs(Mathf.Sin(b.Age * 5 + b.Size * 3));
                var col = new Color(0.74f, 0.70f, 0.66f).Lerp(new Color(0.95f, 0.55f, 0.25f), Mathf.Max(0, 1 - u * 4) * 0.6f);
                DrawLine(b.P - new Vector2(b.Size * (0.4f + 0.8f * tw), 0), b.P + new Vector2(b.Size * (0.4f + 0.8f * tw), 0), col with { A = 0.8f * a }, b.Size * 0.9f, true);
            }
        }
    }
}
