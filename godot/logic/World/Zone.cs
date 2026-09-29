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
    double TintStrength, double Saturation, double Vibrance, double Contrast);

public sealed record AtmospherePreset(
    SkySettings Sky, string KeyColor, double KeyIntensity, double KeyElevation, double KeyAzimuth, double ShadowStrength,
    string HemiSky, string HemiGround, double HemiIntensity, double EnvIntensity, string FogColor, double FogDensity,
    double Exposure, string Rim, double RimStrength, GradeSettings Grade);

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

    public static ZoneMeta Load(string id) => Json.Parse<ZoneMeta>(DataFiles.Text($"zones/{id}/zone.json"));

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
