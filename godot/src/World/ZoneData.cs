using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.World;

/// <summary>
/// A zone as the web game builds it, exported by tools/godot/export_zone.mjs
/// into res://data/ZONE: the ground's heights and paint, where every kit
/// piece stands, and the lights.
/// </summary>
public sealed class ZoneData
{
    public readonly string Id;
    public readonly float Size;
    public readonly int Res;
    public readonly float Leaves;
    public readonly float[] Heights;
    public readonly Image Splat;
    public readonly List<FloraGroup> Flora = new();
    public readonly List<(string Id, Transform3D At)> Props = new();
    public readonly List<LightSpec> Lights = new();

    public sealed record FloraGroup(string Kind, string Piece, Transform3D[] At, KitLook.Look Look);
    public sealed record LightSpec(Vector3 At, Color Color, float Intensity, float Distance, float Flicker, bool On);

    public float Half => Size / 2;
    public float Step => Size / (Res - 1);

    public ZoneData(string id)
    {
        Id = id;
        var dir = $"res://data/{id}";
        using var terrain = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/terrain.json"));
        Size = terrain.RootElement.GetProperty("size").GetSingle();
        Res = terrain.RootElement.GetProperty("res").GetInt32();
        Leaves = terrain.RootElement.GetProperty("leaves").GetSingle();
        var hb = FileAccess.GetFileAsBytes($"{dir}/heights.bin");
        Heights = new float[hb.Length / 4];
        System.Buffer.BlockCopy(hb, 0, Heights, 0, hb.Length);
        Splat = Image.LoadFromFile(ProjectSettings.GlobalizePath($"{dir}/splat.png"));

        var tf = FileAccess.GetFileAsBytes($"{dir}/flora.bin");
        var floats = new float[tf.Length / 4];
        System.Buffer.BlockCopy(tf, 0, floats, 0, tf.Length);
        using var flora = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/flora.json"));
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
        using var props = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/props.json"));
        foreach (var p in props.RootElement.EnumerateArray())
        {
            var t = new float[12];
            int k = 0;
            foreach (var v in p.GetProperty("t").EnumerateArray()) t[k++] = v.GetSingle();
            Props.Add((p.GetProperty("id").GetString()!, Read(t, 0)));
        }
        using var lights = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/lights.json"));
        foreach (var l in lights.RootElement.EnumerateArray())
            Lights.Add(new LightSpec(
                new Vector3(l.GetProperty("x").GetSingle(), l.GetProperty("y").GetSingle(), l.GetProperty("z").GetSingle()),
                new Color(l.GetProperty("color").GetString()!), l.GetProperty("intensity").GetSingle(),
                l.GetProperty("distance").GetSingle(), l.GetProperty("flicker").GetSingle(), l.GetProperty("on").GetBoolean()));
    }

    /// <summary>A transform as the exporter writes it: basis x, y, z, origin.</summary>
    static Transform3D Read(float[] f, int i) => new(
        new Basis(new Vector3(f[i], f[i + 1], f[i + 2]), new Vector3(f[i + 3], f[i + 4], f[i + 5]), new Vector3(f[i + 6], f[i + 7], f[i + 8])),
        new Vector3(f[i + 9], f[i + 10], f[i + 11]));

    /// <summary>Bilinear height (the web game's Terrain.heightAt).</summary>
    public float HeightAt(float x, float z)
    {
        float fx = Mathf.Clamp((x + Half) / Step, 0, Res - 1.0001f), fz = Mathf.Clamp((z + Half) / Step, 0, Res - 1.0001f);
        int i = (int)fx, j = (int)fz;
        float tx = fx - i, tz = fz - j;
        float a = Heights[j * Res + i], b = Heights[j * Res + i + 1], c = Heights[(j + 1) * Res + i], d = Heights[(j + 1) * Res + i + 1];
        return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz;
    }
}
