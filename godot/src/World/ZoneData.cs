using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// A zone as the web game builds it, exported by tools/godot/export_zone.mjs
/// into res://data/zones/ZONE: what the logic reads (World/Zone.cs: the
/// heights, colliders, lights, places) and what only the view needs (the
/// ground's paint, where every kit piece stands, the water).
/// </summary>
public sealed class ZoneData
{
    public readonly string Id;
    public readonly ZoneMeta Meta;
    public readonly Heightfield Ground;
    public readonly Image Splat;
    public readonly List<FloraGroup> Flora = new();
    public readonly List<(string Id, Transform3D At)> Props = new();
    public readonly List<LightSpec> Lights = new();
    /// <summary>An ember arena's place, its second paint, how far inside its ring each
    /// height sample is, its edge and its streams (Maps/ArenaGen.cs); null elsewhere.</summary>
    public readonly SurvivorUnchained.Maps.ArenaPlace? Place;
    public readonly Image? Splat2;
    public readonly Image? Splat3;
    /// <summary>An arena's grass as the meadow shader reads paint: G where none grows.</summary>
    public readonly Image? GrassMask;
    public readonly double[]? Inside;
    public readonly List<(double X, double Z)> Rim = new();
    public readonly List<(double X, double Z, double Hw)[]> Streams = new();
    public readonly List<(double X, double Z, double Hw)[]> Rails = new();
    public readonly List<(double X, double Z, double R)> Vents = new();

    public sealed record FloraGroup(string Kind, string Piece, Transform3D[] At, KitLook.Look Look);
    public sealed record LightSpec(Vector3 At, Color Color, float Intensity, float Distance, float Flicker, bool On);

    public string Dir => $"res://data/zones/{Id}";
    public float Size => (float)Meta.Size;
    public int Res => Meta.Res;
    public float Leaves => (float)Meta.Leaves;
    public float[] Heights => Ground.Heights;
    public float Half => Size / 2;
    public float Step => (float)Ground.Step;

    /// <summary>The logic's data files through Godot's own file access
    /// (which reads inside an exported pack).</summary>
    public static void UseGodotFiles()
    {
        DataFiles.Text = rel => FileAccess.GetFileAsString($"res://data/{rel}");
        DataFiles.Bytes = rel => FileAccess.GetFileAsBytes($"res://data/{rel}");
    }

    public ZoneData(string id)
    {
        UseGodotFiles();
        Id = id;
        Meta = ZoneMeta.Load(id);
        Ground = Heightfield.Load(Meta);
        // Straight from the file (not an imported texture: the paint is data).
        // Kept as the file it is (not imported), so a packed build reads the same bytes.
        Splat = new Image();
        Splat.LoadPngFromBuffer(FileAccess.GetFileAsBytes($"{Dir}/splat.png"));

        var tf = FileAccess.GetFileAsBytes($"{Dir}/flora.bin");
        var floats = new float[tf.Length / 4];
        System.Buffer.BlockCopy(tf, 0, floats, 0, tf.Length);
        using var flora = JsonDocument.Parse(FileAccess.GetFileAsString($"{Dir}/flora.json"));
        int at = 0;
        foreach (var g in flora.RootElement.EnumerateArray())
        {
            int n = g.GetProperty("count").GetInt32();
            var list = new Transform3D[n];
            for (int i = 0; i < n; i++, at += 12) list[i] = Read(floats, at);
            // The kind's look: wind, its leaves' colours (sRGB hex, as the web
            // game writes them; linear here, as three.js makes them) and moss.
            Color? la = null, lb = null;
            float amount = 0;
            if (g.TryGetProperty("leaves", out var lv) && lv.ValueKind == JsonValueKind.Object)
            {
                la = new Color(lv.GetProperty("a").GetString()!).SrgbToLinear();
                lb = new Color(lv.GetProperty("b").GetString()!).SrgbToLinear();
                amount = lv.GetProperty("amount").GetSingle();
            }
            var look = new KitLook.Look(
                g.TryGetProperty("wind", out var w) ? w.GetSingle() : 0, la, lb, amount,
                g.TryGetProperty("moss", out var mo) && mo.ValueKind == JsonValueKind.Number ? mo.GetSingle() : 0);
            Flora.Add(new FloraGroup(g.GetProperty("kind").GetString()!, g.GetProperty("piece").GetString()!, list, look));
        }
        using var props = JsonDocument.Parse(FileAccess.GetFileAsString($"{Dir}/props.json"));
        var t = new float[12];
        foreach (var p in props.RootElement.EnumerateArray())
        {
            int k = 0;
            foreach (var v in p.GetProperty("t").EnumerateArray()) t[k++] = v.GetSingle();
            Props.Add((p.GetProperty("id").GetString()!, Read(t, 0)));
        }
        foreach (var l in Meta.Lights)
            Lights.Add(new LightSpec(new Vector3((float)l.X, (float)l.Y, (float)l.Z), new Color(l.Color),
                (float)l.Intensity, (float)l.Distance, (float)l.Flicker, l.On));
    }

    /// <summary>A map made for a run (Maps/MapGen.cs): the same, from memory.
    /// Its flora in 40 m buckets, one group per kind and piece in each, so
    /// what is off screen is culled.</summary>
    public ZoneData(SurvivorUnchained.Maps.MapBuild m)
    {
        UseGodotFiles();
        Id = m.Meta.Id;
        Meta = m.Meta;
        Ground = m.Ground;
        Splat = Image.CreateFromData(m.SplatRes, m.SplatRes, false, Image.Format.Rgba8, m.Splat);
        Place = m.Place;
        if (m.Splat2 != null) Splat2 = Image.CreateFromData(m.SplatRes, m.SplatRes, false, Image.Format.Rgba8, m.Splat2);
        if (m.Splat3 != null) Splat3 = Image.CreateFromData(m.SplatRes, m.SplatRes, false, Image.Format.Rgba8, m.Splat3);
        if (m.Grass != null)
        {
            var g = new byte[m.Grass.Length * 4];
            for (int i = 0; i < m.Grass.Length; i++) g[i * 4 + 1] = (byte)(255 - m.Grass[i]);
            GrassMask = Image.CreateFromData(m.SplatRes, m.SplatRes, false, Image.Format.Rgba8, g);
        }
        Inside = m.Inside;
        Rim.AddRange(m.Rim);
        Streams.AddRange(m.Streams);
        Rails.AddRange(m.Rails);
        Vents.AddRange(m.Vents);
        var groups = new Dictionary<(string Kind, string Piece, int Bx, int Bz), List<Transform3D>>();
        foreach (var f in m.Flora)
        {
            var key = (f.Kind, f.Piece, Mathf.FloorToInt((float)f.X / 40), Mathf.FloorToInt((float)f.Z / 40));
            if (!groups.TryGetValue(key, out var list)) groups[key] = list = new();
            list.Add(new Transform3D(new Basis(Vector3.Up, (float)f.Rot).Scaled(Vector3.One * (float)f.Scale), new Vector3((float)f.X, (float)f.Y, (float)f.Z)));
        }
        if (System.Environment.GetEnvironmentVariable("FLORA_COUNT") != null)
            foreach (var g in m.Flora.GroupBy(f => f.Kind).OrderBy(g => g.Key)) GD.Print($"flora {g.Key}: {g.Count()}");
        foreach (var (key, list) in groups)
        {
            var k = m.Kinds[key.Kind];
            // An ember arena's crowns are dark and cold against the night:
            // they frame the fight and never outshine it.
            bool arena = m.Place != null;
            var look = new KitLook.Look((float)k.Wind, arena ? new Color("#24382e").SrgbToLinear() : k.LeavesA is string a ? new Color(a).SrgbToLinear() : null,
                arena ? new Color("#2e3a26").SrgbToLinear() : k.LeavesB is string b ? new Color(b).SrgbToLinear() : null, arena ? 0.7f : (float)k.LeavesAmount, (float)k.Moss,
                arena ? 0.42f : 1f);
            Flora.Add(new FloraGroup(key.Kind, key.Piece, list.ToArray(), look));
        }
        foreach (var p in m.Props)
            Props.Add((p.Id, new Transform3D(new Basis(Vector3.Up, (float)p.Rot).Scaled(Vector3.One * (float)p.Scale), new Vector3((float)p.X, (float)p.Y, (float)p.Z))));
        foreach (var l in Meta.Lights)
            Lights.Add(new LightSpec(new Vector3((float)l.X, (float)l.Y, (float)l.Z), new Color(l.Color),
                (float)l.Intensity, (float)l.Distance, (float)l.Flicker, l.On));
    }

    /// <summary>A transform as the exporter writes it: basis x, y, z, origin.</summary>
    static Transform3D Read(float[] f, int i) => new(
        new Basis(new Vector3(f[i], f[i + 1], f[i + 2]), new Vector3(f[i + 3], f[i + 4], f[i + 5]), new Vector3(f[i + 6], f[i + 7], f[i + 8])),
        new Vector3(f[i + 9], f[i + 10], f[i + 11]));

    /// <summary>Bilinear height (the web game's Terrain.heightAt).</summary>
    public float HeightAt(float x, float z) => (float)Ground.HeightAt(x, z);
}
