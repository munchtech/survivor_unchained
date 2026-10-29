using System;
using System.Collections.Generic;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.World;

/* A zone as data: what tools/godot/export_zone.mjs writes from the web game's
 * build of it into data/zones/<id>/zone.json and heights.bin. The view builds
 * the place from the rest of the files; this is what the game's logic reads:
 * the ground's heights, the colliders (with the ids the runtime refers to),
 * where the survivor starts, the lights and fires the runtime lights and puts
 * out, the named places and paths, and what the map is drawn from. */

public readonly record struct XZ(double X, double Z);

public sealed class Start
{
    public double X, Z, Facing;
}

public sealed class LightDef
{
    public double X, Y, Z;
    public string Color = "#ffffff";
    public double Intensity, Distance, Flicker;
    public bool On;
    /// <summary>The landmark nodes that glow with it (shown while it is on).</summary>
    public List<string> Glow = new();
}

public sealed class FireDef
{
    public double X, Y, Z, Size;
    /// <summary>The light it burns with (an index into the lights): a fire
    /// burns while its light is on.</summary>
    public int Light;
    /// <summary>In a ring of stones (a campfire); without, a fire where it caught (a deadfall).</summary>
    public bool Ring = true;
}

public sealed class Point3
{
    public double X, Y, Z;
}

public sealed class ColliderDef
{
    public int Id;
    public ColliderKind Kind;
    public double X, Z, R, Hw, Hd, Rot;
    public string? Tag;
    public bool Soft, PlayerOnly;
}

public sealed class ZoneMapDef
{
    /// <summary>[kind, x, z, scale] per tree and rock, for the map.</summary>
    public List<JsonElement> Flora = new();
    public JsonElement? Extent;
    public List<JsonElement> Buildings = new();
}

public sealed class WaterMaskDef
{
    /// <summary>n by n cells over the zone, a byte each, 1 where there is water.</summary>
    public int N;
    public string Bits = "";
}

/// <summary>The light, air and colour of a moment of the day (the web game's
/// render/atmosphere.ts): colours as sRGB hex.</summary>
public sealed record SkySettings(string Top, string Horizon, string Bottom, string Glow, double GlowPower, double Stars, double Moon);

public sealed record GradeSettings(double[] Lift, double[] Gamma, double[] Gain, string ShadowTint, string HighlightTint,
    double TintStrength, double Saturation, double Vibrance, double Contrast)
{
    /// <summary>How much of the shadow tint's darkening is held off in the toe (0 to 1): the tint stays a colour there,
    /// so dark values (an iris, dark hair, unlit ground) keep their detail instead of falling to black.</summary>
    public double Toe { get; init; }
    /// <summary>The moon's colour over what it lights (0: none; play's own grades, E1 round 3): a weakly coloured pixel
    /// (moonlit grass, stone, a slate shade) gives up MoonDrop of its own chroma and takes MoonSat of lightness in the
    /// moon's hue (Oklab degrees); one coloured past MoonLo..MoonHi (C/L: a fire, her ember's pool, skin by it) keeps its
    /// own. Faded out over lightness MoonTop - MoonWidth..MoonTop (Oklab L), so at dawn it cools the shade only. After the
    /// warm-hue hold and the toe's: they kept the khaki of olive grass and the brown of the shade under a blue moon.</summary>
    public double Moon { get; init; }
    public double MoonHue { get; init; } = 250;
    public double MoonSat { get; init; } = 0.06;
    public double MoonDrop { get; init; } = 0.75;
    public double MoonLo { get; init; } = 0.06;
    public double MoonHi { get; init; } = 0.16;
    public double MoonTop { get; init; } = 0.9;
    public double MoonWidth { get; init; } = 0.2;
    /// <summary>The paint grade (art style round 2, approved 20 Oct; 0: off), after the moon's step, in Oklab: PaintVib
    /// raises the chroma of what is dull and not dark (skin hues held), PaintHi that of the lit brights, PaintLift lifts the
    /// darkest values, and PaintShadowK of PaintShadow's hue and chroma (sRGB hex; "" none) is laid on what is dark and
    /// weakly coloured: painted shadows coloured blue to violet, not slate. --grade-try overrides any of them for pictures.</summary>
    public double PaintVib { get; init; }
    public double PaintHi { get; init; }
    public string PaintShadow { get; init; } = "";
    public double PaintShadowK { get; init; }
    public double PaintLift { get; init; }
    /// <summary>How much of skin's hues (Oklab h 15-90, C over 0.012) the painted shadow spares (0: none; Face 44, skin A0). Laid on
    /// her shaded skin, the blue lerp passed through red and violet on the way: deep skin's shade side went from h 40-55 to
    /// 20-43, brick-red and purple patches with hard edges where her shade crossed its L and C thresholds.</summary>
    public double PaintShadowSkin { get; init; }
    /// <summary>The vibrance's share in the darks (Oklab L 0.44 and under; all of it from L 0.52): G1 r2's 0.2.</summary>
    public double PaintVibDark { get; init; } = 0.2;
}

public sealed record AtmospherePreset(
    SkySettings Sky, string KeyColor, double KeyIntensity, double KeyElevation, double KeyAzimuth, double ShadowStrength,
    string HemiSky, string HemiGround, double HemiIntensity, double EnvIntensity, string FogColor, double FogDensity,
    double Exposure, string Rim, double RimStrength, GradeSettings Grade)
{
    /// <summary>The volumetric fog's density: the air the lamps' halos and the key's shafts are seen in.</summary>
    public double Haze { get; init; } = 0.0012;
    /// <summary>How thick the mist lies on a river (0: none, as the cinematics' presets have it; 1: thick).</summary>
    public double Mist { get; init; }
    /// <summary>The mist's colour (sRGB hex): the key's light in the air, as the eye sees it.</summary>
    public string MistColor { get; init; } = "#000000";
    /// <summary>Her carried light's strength against its base (play's night lights her pool more, in a darker world).</summary>
    public double Ember { get; init; } = 1;
    /// <summary>The moon's rim on the crowd in play, in shade as in its light (0: none, as the cinematics' presets have it).</summary>
    public double CrowdRim { get; init; }
    /// <summary>A river's light, the sky in it, and how far its ripples bend it (1: as built; the water shader's water_air).</summary>
    public double RiverLight { get; init; } = 1;
    public double RiverSky { get; init; } = 1;
    public double RiverBend { get; init; } = 1;
    /// <summary>(Low Ford r3) How far the river's moon glint is the water look's moonlight (moon_*: rougher, sparse, a soft column, tinted; the water shader's water_air.w); 0 as built.</summary>
    public double RiverMoon { get; init; } = 0;
    /// <summary>(Low Ford r3) How far a warm lamp's or fire's light on our own grass turns toward ochre, its lime taken out (grass_own.gdshader's flora_lamp); 0 as built.</summary>
    public double GrassLampOchre { get; init; } = 0;
    /// <summary>(Low Ford lf5p) Our broadleaf bushes' and alders' leaves by night pulled this share toward their own grey (kit.gdshader's flora_night.x); 0 as built.</summary>
    public double BushNightSat { get; init; } = 0;
    /// <summary>(Low Ford lf5p) How far the meadow ground in her ember's pool turns from green to straw, so her warm light reads ochre on it, not chartreuse (terrain.gdshader's flora_night.y; her own lighting untouched); 0 as built.</summary>
    public double GroundEmberOchre { get; init; } = 0;
    /// <summary>Hoar frost on the ground's exposed tops in play (0: none; 1: a night's full frost; look bible 1f),
    /// and how much of it the sun has thawed where it falls (0: none; 1: all of it, leaving it in the shade).</summary>
    public double Frost { get; init; }
    public double FrostThaw { get; init; }
}

public sealed class ZoneMeta
{
    public string Id = "";
    /// <summary>The ground: a square this many metres across, heights on a
    /// res by res grid, paint on a splatRes by splatRes image.</summary>
    public double Size;
    public int Res, SplatRes;
    /// <summary>How much of the ground is strewn with leaves (the terrain shader).</summary>
    public double Leaves;
    /// <summary>The colour the blight's veins glow (sRGB hex).</summary>
    public string BlightGlow = "#8cff5a";
    /// <summary>How far from the centre the survivor may go, each way.</summary>
    public double Bound;
    public Start Start = new();
    /// <summary>The zone's air by day (the runtime changes it with the hour).</summary>
    public AtmospherePreset Atmosphere = null!;
    public List<LightDef> Lights = new();
    public List<FireDef> Fires = new();
    public List<Point3> Chimneys = new();
    /// <summary>Lights moths gather round after dark (indices into the lights).</summary>
    public List<int> Moths = new();
    /// <summary>Landmark nodes that only show after dark (light spilled from
    /// a doorway).</summary>
    public List<string> NightNodes = new();
    /// <summary>Landmark nodes the zone starts with hidden (the runtime
    /// shows them).</summary>
    public List<string> HiddenNodes = new();
    public List<ColliderDef> Colliders = new();
    /// <summary>What the zone's runtime reaches into, zone by zone (the
    /// Verge's brambles and fires, Lowford's pylons, the Waystation's doors).</summary>
    public JsonElement Refs;
    /// <summary>The zone module's named places (a table of points, or a number).</summary>
    public Dictionary<string, JsonElement> Places = new();
    /// <summary>The zone module's paths: [x, z] points.</summary>
    public Dictionary<string, double[][]> Paths = new();
    public ZoneMapDef? Map;
    public WaterMaskDef? WaterMask;
    public int LandmarkMeshes;

    public static ZoneMeta Load(string id)
    {
        var z = Json.Parse<ZoneMeta>(DataFiles.Text($"zones/{id}/zone.json"));
        AddPropColliders(z, id);
        return z;
    }

    /// <summary>Box colliders for the placed props in zones/{id}/props_own.json: each "place" entry with
    /// "col": [cx, cz, hw, hd] (metres, in the preset's own frame, before its rotation and scale).</summary>
    public static void AddPropColliders(ZoneMeta z, string id)
    {
        string text;
        try { text = DataFiles.Text($"zones/{id}/props_own.json"); }
        catch { return; }
        if (string.IsNullOrWhiteSpace(text)) return;  // a zone with no props_own.json (the verge) reads as empty
        using var doc = JsonDocument.Parse(text);
        if (!doc.RootElement.TryGetProperty("place", out var place) || place.ValueKind != JsonValueKind.Array) return;
        int nextId = 0;
        foreach (var c in z.Colliders) nextId = Math.Max(nextId, c.Id + 1);
        foreach (var e in place.EnumerateArray())
        {
            var c = PropCollider(e);
            if (c == null) continue;
            c.Id = nextId++;
            z.Colliders.Add(c);
        }
    }

    /// <summary>One "place" entry as a box collider (Id left 0), or null without a "col". Godot's
    /// Basis(Up, rot) sends local x to world (cos, -sin) and local z to (sin, cos); the box's own x axis
    /// runs along (cos Rot, sin Rot), so its Rot is -rot.</summary>
    public static ColliderDef? PropCollider(JsonElement e)
    {
        if (e.ValueKind != JsonValueKind.Object || !e.TryGetProperty("col", out var col)
            || col.ValueKind != JsonValueKind.Array || col.GetArrayLength() < 4) return null;
        double cx = col[0].GetDouble(), cz = col[1].GetDouble(), hw = col[2].GetDouble(), hd = col[3].GetDouble();
        double x = e.TryGetProperty("x", out var px) ? px.GetDouble() : 0;
        double zz = e.TryGetProperty("z", out var pz) ? pz.GetDouble() : 0;
        double rot = e.TryGetProperty("rot", out var pr) ? pr.GetDouble() : 0;
        double s = e.TryGetProperty("scale", out var ps) ? ps.GetDouble() : 1;
        double cos = Math.Cos(rot), sin = Math.Sin(rot);
        hw *= s; hd *= s;
        return new ColliderDef
        {
            Kind = ColliderKind.Box,
            X = x + (cx * cos + cz * sin) * s,
            Z = zz + (-cx * sin + cz * cos) * s,
            Hw = hw, Hd = hd, Rot = -rot,
            R = Math.Sqrt(hw * hw + hd * hd),
            Tag = "prop",
        };
    }

    /// <summary>A named place: Places[table][name] as a point.</summary>
    public XZ Place(string table, string name)
    {
        var p = Places[table].GetProperty(name);
        return new XZ(p.GetProperty("x").GetDouble(), p.GetProperty("z").GetDouble());
    }

    /// <summary>The colliders, in the world the fight is in, each with the id
    /// the web game gave it (the runtime removes some by id: a bramble wall
    /// burned away).</summary>
    public CollisionWorld Collision()
    {
        var w = new CollisionWorld(Size) { Bound = Bound };
        foreach (var c in Colliders)
            w.Restore(new Collider
            {
                Id = c.Id, Kind = c.Kind, X = c.X, Z = c.Z, R = c.R, Hw = c.Hw, Hd = c.Hd, Rot = c.Rot,
                Tag = c.Tag, Soft = c.Soft, PlayerOnly = c.PlayerOnly,
            });
        return w;
    }

    /// <summary>Is there water here, on the map's mask.</summary>
    public bool WaterAt(double x, double z)
    {
        if (WaterMask == null) return false;
        mask ??= Convert.FromBase64String(WaterMask.Bits);
        int n = WaterMask.N;
        int i = (int)Math.Floor((x + Size / 2) / Size * n), j = (int)Math.Floor((z + Size / 2) / Size * n);
        return i >= 0 && j >= 0 && i < n && j < n && mask[j * n + i] != 0;
    }

    byte[]? mask;
}

/// <summary>The ground's heights (the web game's Terrain.heightAt): res by
/// res samples over a square size metres across, centred on the origin, row
/// by row from -z, each row from -x.</summary>
public sealed class Heightfield
{
    public readonly double Size, Half, Step;
    public readonly int Res;
    public readonly float[] Heights;

    public Heightfield(double size, int res, float[] heights)
    {
        if (heights.Length != res * res) throw new ArgumentException($"{heights.Length} heights for a {res}² grid");
        Size = size; Res = res; Heights = heights;
        Half = size / 2;
        Step = size / (res - 1);
    }

    public static Heightfield Load(ZoneMeta z)
    {
        var b = DataFiles.Bytes($"zones/{z.Id}/heights.bin");
        var h = new float[b.Length / 4];
        Buffer.BlockCopy(b, 0, h, 0, b.Length);
        return new Heightfield(z.Size, z.Res, h);
    }

    /// <summary>Bilinear height at a point (clamped to the edge).</summary>
    public double HeightAt(double x, double z)
    {
        double fx = Math.Clamp((x + Half) / Step, 0, Res - 1.0001), fz = Math.Clamp((z + Half) / Step, 0, Res - 1.0001);
        int i = (int)fx, j = (int)fz;
        double tx = fx - i, tz = fz - j;
        double a = Heights[j * Res + i], b = Heights[j * Res + i + 1], c = Heights[(j + 1) * Res + i], d = Heights[(j + 1) * Res + i + 1];
        return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz;
    }
}
