using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using SurvivorUnchained.Play;

namespace H;

/// <summary>Per link (island group) of each piece: inside counts and depth at chosen frames (--at clip@t,clip@t).</summary>
public static class Diag
{
    public static void Run(World w, IDesign d, string at)
    {
        var want = at.Split(',').Select(s => { var p = s.Split('@'); return (Clip: p[0], T: double.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture)); }).ToList();
        // link of each piece vertex (the game's island carry), and the dominant body bone name per body vertex
        var linkOf = new List<int[]>();
        foreach (var p in w.Pieces)
        {
            var row = w.Rows.FirstOrDefault(r => r.Id == p.Row);
            var lk = new int[p.Mesh.Pos.Length]; Array.Fill(lk, -1);
            if (row != null)
            {
                var segs = row.Links.Select(l => new SpringCarry.Seg(l.Head, l.Tail, l.Reach)).ToArray();
                var (link, sh) = SpringCarry.Assign(p.RestP, p.Mesh.Tris, segs, SpringCarry.Parse(row.Rule), row.Share);
                lk = link;
            }
            linkOf.Add(lk);
        }
        var body = w.Body; int k = body.K;
        var bname = new string[body.Pos.Length];
        for (int i = 0; i < bname.Length; i++)
        {
            int best = 0;
            for (int j = 1; j < k; j++) if (body.Weights[i * k + j] > body.Weights[i * k + best]) best = j;
            int b = body.BindBone[body.Bones[i * k + best]];
            bname[i] = b >= 0 ? w.Sk.Name[b] : "?";
        }
        d.Setup(w);
        var pose = new Aff[w.Bones.Name.Count];
        string last = "";
        var bodyP = new Vector3[body.Pos.Length]; var bodyN = new Vector3[body.Pos.Length];
        for (int fi = 0; fi < w.Frames.Count; fi++)
        {
            var f = w.Frames[fi]; w.Cur = f;
            for (int b = 0; b < w.Sk.Name.Length; b++) pose[b] = f.G[b];
            bool cut = fi == 0 || f.Clip != last; last = f.Clip;
            d.Frame(w, f, pose, 1f / 60, cut);
            if (!want.Any(x => x.Clip == f.Clip && Math.Abs(x.T - f.T) < 0.009)) continue;
            var (bp0, bn0) = Probe.Shaped(body, f.ShapeW[Array.IndexOf(w.Meshes, body)]);
            Probe.Skin(bp0, bn0, body.Bones, body.Weights, body.K, w.Mats(body, pose), bodyP, bodyN);
            var test = new InsideTest(bodyP, bodyN, body.Tris);
            Console.WriteLine($"== {f.Clip}@{f.T:0.000} (frame {f.F})");
            for (int pi = 0; pi < w.Pieces.Count; pi++)
            {
                var p = w.Pieces[pi];
                var pp = new Vector3[p.Mesh.Pos.Length];
                d.Skin(w, pi, pose, pp);
                var dist = new float[pp.Length]; var vert = new int[pp.Length];
                System.Threading.Tasks.Parallel.For(0, pp.Length, i => { var (dd, v) = test.Query(pp[i]); dist[i] = dd; vert[i] = v; });
                var by = new Dictionary<int, (int N, int In, float Deep, Dictionary<string, int> Bones)>();
                for (int i = 0; i < pp.Length; i++)
                {
                    int l = linkOf[pi][i];
                    if (!by.TryGetValue(l, out var s)) s = (0, 0, 0, new Dictionary<string, int>());
                    s.N++;
                    if (vert[i] >= 0 && dist[i] < -Probe.InsideMm / 1000f)
                    {
                        s.In++; s.Deep = Math.Max(s.Deep, -dist[i] * 1000);
                        var bn = bname[vert[i]]; s.Bones[bn] = s.Bones.TryGetValue(bn, out int c) ? c + 1 : 1;
                    }
                    by[l] = s;
                }
                foreach (var (l, s) in by.OrderBy(x => x.Key))
                    if (s.In > 0)
                        Console.WriteLine($"  {p.Mesh.Name,-46} link {l,3} in {s.In,6}/{s.N,6} deep {s.Deep,5:0.0} {string.Join(" ", s.Bones.OrderByDescending(x => x.Value).Take(3).Select(x => $"{x.Key}:{x.Value}"))}");
            }
        }
    }
}
