// The her-springs replay harness: her body and worn pieces as the game dumps them (--wear-dump DIR beside --wear-inside,
// see WearInside.cs), replayed offline in System.Numerics with the game's own engine-free code (ClothChains, PlateFollow,
// SpringCarry, InsideTest linked from godot/logic/Play), measured as the game's probe measures (skirt points inside her
// thigh, pauldron % inside her skin). Build: dotnet build -c Release. Run: dotnet bin/Release/net8.0/harness.dll DIR MODE
// [--every 2] [--clips a,b] [--springs FILE]; MODE: base (plain skinning: the game's BEFORE), rigid, springs (the capsule
// chains), follow (PlateRide, round 2's plate follow, harness-only; --kin [ROW]: held stiff, own skinning plus the push only; --nocut --snap X --rigidplate --margin --near --cell --inner --rim --fit --minlever --maxpush --noslide --nohook --nocol
// --rigidfit --iters --substeps --grav --drag --bend --stiff), shapes, binds.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Numerics;
using SurvivorUnchained.Play;

namespace H;

public static class Program
{
    public static Dictionary<string, string> Opt = new();
    public static string O(string k, string d) => Opt.TryGetValue(k, out var v) ? v : d;
    public static float F(string k, float d) => Opt.TryGetValue(k, out var v) ? float.Parse(v, System.Globalization.CultureInfo.InvariantCulture) : d;
    public static bool Has(string k) => Opt.ContainsKey(k);

    public static int Main(string[] args)
    {
        string dir = args[0], mode = args[1];
        for (int i = 2; i < args.Length; i++)
            if (args[i].StartsWith("--")) { string k = args[i][2..]; string v = i + 1 < args.Length && !args[i + 1].StartsWith("--") ? args[++i] : "1"; Opt[k] = v; }
        var clock = Stopwatch.StartNew();
        var sk = Skel.Load(Path.Combine(dir, "skeleton.txt"));
        var meshes = Directory.GetFiles(dir, "mesh_*.bin").OrderBy(f => int.Parse(Path.GetFileNameWithoutExtension(f)[5..])).Select(MeshD.Load).ToArray();
        var frames = Dump.Frames(Path.Combine(dir, "frames.bin"), sk.Name.Length, meshes);
        Console.WriteLine($"loaded {meshes.Length} meshes ({string.Join(", ", meshes.Select(m => $"{m.Name}[{m.Slot}] {m.Pos.Length}v k{m.K} {m.Shapes.Length}sh"))}), {frames.Count} frames, {clock.ElapsedMilliseconds} ms");
        if (mode == "shapes")
        {
            for (int m = 0; m < meshes.Length; m++)
                for (int s = 0; s < meshes[m].Shapes.Length; s++)
                {
                    float lo = frames.Min(f => f.ShapeW[m][s]), hi = frames.Max(f => f.ShapeW[m][s]);
                    Console.WriteLine($"{meshes[m].Name} {meshes[m].Shapes[s].Name} {meshes[m].Shapes[s].Idx.Length}v w {lo:0.###}..{hi:0.###}");
                }
            return 0;
        }
        if (mode == "binds")
        {
            foreach (var m in meshes)
            {
                var bt = m.BindBone.Select((bone, b) => bone >= 0 ? sk.Rest[bone] * m.Bind[b] : Aff.I).ToArray();
                float worst = 0; int bad = 0;
                for (int i = 0; i < m.Pos.Length; i++)
                {
                    Vector3 at = Vector3.Zero; float sum = 0;
                    for (int q = 0; q < m.K; q++) { float w = m.Weights[i * m.K + q]; if (w <= 0) continue; at += w * bt[m.Bones[i * m.K + q]].Apply(m.Pos[i]); sum += w; }
                    at /= sum;
                    float d = 0;
                    for (int q = 0; q < m.K; q++) { float w = m.Weights[i * m.K + q]; if (w <= 0) continue; d = Math.Max(d, Vector3.Distance(at, bt[m.Bones[i * m.K + q]].Apply(m.Pos[i]))); }
                    worst = Math.Max(worst, d); if (d > 1e-4f) bad++;
                }
                Console.WriteLine($"{m.Name}: binds disagree by up to {worst * 1000:0.00} mm on {bad} vertices; bind count {m.Bind.Length}");
            }
            return 0;
        }
        var world = new World(sk, meshes, frames);
        world.Run(mode);
        return 0;
    }
}
