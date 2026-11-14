using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using SurvivorUnchained.Play;

namespace H;

public static class Designs
{
    public static IDesign Make(string mode) => mode switch
    {
        "follow" => new FollowDesign(),
        _ => throw new Exception("unknown mode " + mode),
    };

    public static PlateRide.Xf X(Aff a) => new(a.X, a.Y, a.Z, a.O);

    /// <summary>A mesh's rest data for PlateRide: rest places, normals, skeleton influences, per-influence places where
    /// binds disagree, shapes in skeleton rest axes (by the dominant bind, or the given frame).</summary>
    public static PlateRide.MeshIn MeshIn(World w, MeshD m, int channelBase, Aff? frame, int[]? link)
    {
        var bt = w.BindTo(m);
        int n = m.Pos.Length, k = m.K;
        var place = new Vector3[n]; var nrm = new Vector3[n];
        Probe.Skin(m.Pos, m.Nrm, m.Bones, m.Weights, k, bt, place, nrm);
        var bone = new int[n * k]; var wt = new float[n * k];
        Vector3[]? at = null;
        var dom = new int[n];
        for (int i = 0; i < n; i++)
        {
            int best = 0;
            for (int q = 0; q < k; q++)
            {
                int b = m.Bones[i * k + q];
                bone[i * k + q] = b >= 0 && b < m.BindBone.Length ? m.BindBone[b] : -1;
                wt[i * k + q] = m.Weights[i * k + q];
                if (m.Weights[i * k + q] > m.Weights[i * k + best]) best = q;
            }
            dom[i] = m.Bones[i * k + best];
        }
        if (frame == null)
        {
            at = new Vector3[n * k];
            for (int i = 0; i < n; i++)
                for (int q = 0; q < k; q++)
                {
                    int b = m.Bones[i * k + q];
                    at[i * k + q] = b >= 0 && b < bt.Length ? bt[b].Apply(m.Pos[i]) : place[i];
                }
        }
        var sd = new Vector3[]?[m.Shapes.Length]; var sdn = new Vector3[]?[m.Shapes.Length];
        for (int s = 0; s < m.Shapes.Length; s++)
        {
            var sh = m.Shapes[s];
            var d = new Vector3[n]; var dn = new Vector3[n];
            for (int j = 0; j < sh.Idx.Length; j++)
            {
                int i = sh.Idx[j];
                var f = frame ?? (dom[i] >= 0 && dom[i] < bt.Length ? bt[dom[i]] : Aff.I);
                d[i] = f.Basis(sh.DP[j]); dn[i] = f.Basis(sh.DN[j]);
            }
            sd[s] = d; sdn[s] = dn;
        }
        return new PlateRide.MeshIn { K = k, Place = place, Normal = nrm, Bone = bone, Weight = wt, At = at, ChannelBase = channelBase, ShapeD = sd, ShapeDn = sdn, Link = link };
    }
}

/// <summary>PlateRide on her rows: targets from the pieces' own weights, plate points against the body's skin.</summary>
public sealed class FollowDesign : IDesign
{
    sealed class Rig
    {
        public SpringsFile.Row Row = null!;
        public PlateRide F = null!;
        public ClothChains Sim = null!;
        public int[] Bone = Array.Empty<int>(), Lp = Array.Empty<int>(), Par = Array.Empty<int>(), Roots = Array.Empty<int>(), RootLink = Array.Empty<int>();
        public Vector3[] Targets = Array.Empty<Vector3>();
        public Vector3[] LastRoot = Array.Empty<Vector3>(); public Quaternion[] LastQ = Array.Empty<Quaternion>();
        public bool Cut = true; public double Life; public int Resets, Snaps, Since;
        public long Pushes; public float Deepest;
        public (Quaternion Q, Vector3 From, Vector3 To)[] D = Array.Empty<(Quaternion, Vector3, Vector3)>();
    }
    readonly List<Rig> rigs = new();
    readonly List<int[]> carryBone = new();
    int[] chBase = Array.Empty<int>();
    float[] ch = Array.Empty<float>();
    Aff[] skin = Array.Empty<Aff>();

    public void Setup(World w)
    {
        chBase = new int[w.Meshes.Length]; int c = 0;
        for (int m = 0; m < w.Meshes.Length; m++) { chBase[m] = c; c += w.Meshes[m].Shapes.Length; }
        ch = new float[c];
        var clock = System.Diagnostics.Stopwatch.StartNew();
        var body = Designs.MeshIn(w, w.Body, chBase[Array.IndexOf(w.Meshes, w.Body)], null, null);
        foreach (var p in w.Pieces) carryBone.Add(Enumerable.Repeat(-1, p.Mesh.Pos.Length).ToArray());
        foreach (var row in w.Rows.Where(r => w.Pieces.Any(p => p.Row == r.Id)))
        {
            foreach (var l in row.Links) w.Bones.Add(l);
            var segs = row.Links.Select(l => new SpringCarry.Seg(l.Head, l.Tail, l.Reach)).ToArray();
            var pieces = new List<PlateRide.MeshIn>();
            for (int pi = 0; pi < w.Pieces.Count; pi++)
            {
                var p = w.Pieces[pi];
                if (p.Row != row.Id) continue;
                var (link, sh) = SpringCarry.Assign(p.RestP, p.Mesh.Tris, segs, SpringCarry.Parse(row.Rule), row.Share);
                var lk = new int[link.Length];
                for (int i = 0; i < lk.Length; i++)
                {
                    lk[i] = link[i] >= 0 && sh[i] >= 0.999f ? link[i] : -1;
                    if (lk[i] >= 0) carryBone[pi][i] = w.Bones.Find(row.Links[lk[i]].Bone);
                }
                pieces.Add(Designs.MeshIn(w, p.Mesh, chBase[p.MeshIndex], p.CarryM, lk));
                // (the stand-in bones a skinning-plus-delta carry needs: each link's distinct influence bones)
                var pairs = new HashSet<(int, int)>();
                for (int i = 0; i < lk.Length; i++)
                    if (lk[i] >= 0)
                        for (int q = 0; q < p.Mesh.K; q++) if (p.Mesh.Weights[i * p.Mesh.K + q] > 0) pairs.Add((lk[i], p.Mesh.Bones[i * p.Mesh.K + q]));
                Console.WriteLine($"stand-ins {p.Mesh.Name}: {pairs.Count} (link, bind) pairs over {pairs.Select(x => x.Item1).Distinct().Count()} links");
            }
            var (lp, par, rootLink) = ClothChains.Order(row.Links.Select(l => (l.Bone, l.Parent)).ToList());
            var idx = new Dictionary<string, int>();
            for (int i = 0; i < row.Links.Count; i++) idx[row.Links[i].Bone] = i;
            var pl = row.Links.Select(l => new PlateRide.Link(l.Head, l.Tail, idx.TryGetValue(l.Parent, out int pj) ? pj : -1)).ToList();
            var tune = PlateRide.Tuning.Plate with
            {
                Margin = Program.F("margin", PlateRide.Tuning.Plate.Margin), Near = Program.F("near", PlateRide.Tuning.Plate.Near),
                Cell = Program.F("cell", PlateRide.Tuning.Plate.Cell), Inner = (int)Program.F("inner", PlateRide.Tuning.Plate.Inner),
                Rim = (int)Program.F("rim", PlateRide.Tuning.Plate.Rim), Fit = (int)Program.F("fit", PlateRide.Tuning.Plate.Fit),
                MinLever = Program.F("minlever", PlateRide.Tuning.Plate.MinLever), MaxPush = Program.F("maxpush", PlateRide.Tuning.Plate.MaxPush), Slide = !Program.Has("noslide"),
            };
            var f = PlateRide.Build(pl, lp, par, pieces, Program.Has("nocol") ? null : body, tune) ?? throw new Exception("no plates for " + row.Id);
            float scale = w.Frames[0].W.ScaleX;
            var radius = new float[par.Length]; var stiffness = new float[par.Length];
            for (int i = 0; i < row.Links.Count; i++) { radius[lp[i]] = row.Links[i].Radius * scale; stiffness[lp[i]] = Program.Has("stiff") ? Program.F("stiff", 10) : row.Links[i].Stiffness; }
            var t = ClothChains.Tuning.Wool with
            {
                Gravity = Program.F("grav", 9.8f), Substeps = (int)Program.F("substeps", 4), Iterations = (int)Program.F("iters", 3),
                Drag = Program.F("drag", ClothChains.Tuning.Wool.Drag), Bend = Program.F("bend", ClothChains.Tuning.Wool.Bend),
            };
            var sim = new ClothChains(par, radius, t, stiffness);
            if (!Program.Has("nohook")) sim.Hook = f.Collide;
            var rig = new Rig
            {
                Row = row, F = f, Sim = sim, Bone = row.Links.Select(l => w.Bones.Find(l.Bone)).ToArray(), Lp = lp, Par = par,
                Roots = Enumerable.Range(0, par.Length).Where(p => par[p] < 0).ToArray(), RootLink = rootLink, Targets = new Vector3[par.Length],
            };
            rig.LastRoot = new Vector3[rig.Roots.Length]; rig.LastQ = new Quaternion[rig.Roots.Length];
            rigs.Add(rig);
            Console.WriteLine($"follow {row.Id}: {f.Links} links, {f.PlatePoints} plate points, {f.BodyPoints} body points, {f.Candidates} candidates");
        }
        Console.WriteLine($"follow setup {clock.ElapsedMilliseconds} ms");
    }

    public void Frame(World w, Frame f, Aff[] pose, float dt, bool cut)
    {
        int nb = w.Sk.Name.Length;
        if (skin.Length != nb) skin = new Aff[nb];
        for (int b = 0; b < nb; b++) skin[b] = pose[b] * w.Sk.Rest[b].Inverse();
        var sx = skin.Select(Designs.X).ToArray();
        for (int m = 0; m < w.Meshes.Length; m++) for (int s = 0; s < w.Meshes[m].Shapes.Length; s++) ch[chBase[m] + s] = f.ShapeW[m][s];
        var W = Designs.X(f.W);
        foreach (var r in rigs)
        {
            long t0 = System.Diagnostics.Stopwatch.GetTimestamp(); int rs0 = r.Resets;
            r.F.Update(sx, W, ch, r.Targets);
            if (cut && !(Program.Has("nocut") && r.Life > 0)) r.Cut = true;
            // (a pose that snapped: its targets moved more than --snap skeleton units in a frame)
            if (Program.Has("snap") && r.Life > 0 && r.F.Jump > Program.F("snap", 0.05f)) { r.Cut = true; r.Snaps++; }
            var cs = Stat(f.Clip, r.Row.Id);
            if (cut) cs[1] = Math.Max(cs[1], r.F.Jump); else cs[0] = Math.Max(cs[0], r.F.Jump);
            for (int i = 0; i < r.Roots.Length; i++)
            {
                var at = r.Targets[r.Roots[i]];
                var q = r.F.Fitted(r.RootLink[r.Roots[i]]);
                if (!r.Cut && r.Life > 0 && (Vector3.Distance(at, r.LastRoot[i]) > Math.Max(0.35f * f.W.ScaleX, 12 * dt) || Angle(q, r.LastQ[i]) > 40 * MathF.PI / 180)) r.Cut = true;
                r.LastRoot[i] = at; r.LastQ[i] = q;
            }
            var down = -Vector3.UnitY; float ground = f.W.O.Y;
            if (Program.Has("kin") && (Program.O("kin", "1") == "1" || Program.O("kin", "1") == r.Row.Id))
            {
                // (held stiff: no swing, no lag; each frame the plates start at their own skinning and only the body's push moves them)
                if (r.Cut) { r.F.Cut(); r.F.Update(sx, W, ch, r.Targets); r.Cut = false; r.Resets++; }
                r.Sim.Reset(r.Targets, Array.Empty<ClothChains.Capsule>(), ground, down);
                r.Sim.Step(dt, r.Targets, Array.Empty<ClothChains.Capsule>(), ground, down);
            }
            else if (r.Cut) { r.F.Cut(); r.F.Update(sx, W, ch, r.Targets); r.Sim.Reset(r.Targets, Array.Empty<ClothChains.Capsule>(), ground, down); r.Cut = false; r.Resets++; }
            else r.Sim.Step(dt, r.Targets, Array.Empty<ClothChains.Capsule>(), ground, down);
            r.Life += dt;
            { long t1 = System.Diagnostics.Stopwatch.GetTimestamp(); if (r.Resets != rs0) { Timing.ResetT += t1 - t0; Timing.ResetN++; } else { Timing.StepT += t1 - t0; Timing.StepN++; } }
            r.Pushes += r.F.Pushes; r.Deepest = Math.Max(r.Deepest, r.F.Deepest);
            var x = r.Sim.Positions;
            if (r.D.Length != r.Bone.Length) r.D = new (Quaternion, Vector3, Vector3)[r.Bone.Length];
            for (int k = 0; k < r.Bone.Length; k++) r.D[k] = r.F.Delta(k, x);
            // (the plates' unrest against their own skinning, frames 3.. after a reset)
            float jit = r.F.Jitter(x);
            if (r.Resets != rs0) r.Since = 0; else r.Since++;
            if (r.Since >= 3) { cs[2] = Math.Max(cs[2], jit); cs[3] += jit; cs[4]++; }
            for (int k = 0; k < r.Bone.Length; k++)
            {
                var (turn, head) = Program.Has("rigidfit") ? (r.F.Fitted(k), Vector3.Zero) : r.F.Pose(k, x);
                var rest = w.Bones.Rest[r.Bone[k]];
                var g = rest.RotBasis(turn);
                g.O = head;
                if (Program.Has("rigidfit"))
                {
                    // (the fit alone, hinged where the anchors put the head: no swing, no collider)
                    var inv = f.W.Inverse();
                    g.O = inv * r.Targets[r.Lp[k] >= 0 ? r.Par[r.Lp[k]] : 0];
                }
                pose[r.Bone[k]] = g;
            }
        }
    }

    /// <summary>Per clip and row: max target jump within the clip, at its first frame, max jitter, jitter sum, frames.</summary>
    public static readonly Dictionary<(string, string), float[]> Clip = new();
    static float[] Stat(string clip, string row) { if (!Clip.TryGetValue((clip, row), out var a)) Clip[(clip, row)] = a = new float[5]; return a; }
    public static void Say()
    {
        foreach (var ((c, row), a) in Clip)
            if (c != "") Console.WriteLine(FormattableString.Invariant($"MOTION {c} {row} jump {a[0] * 1000:0.0} mm, at start {a[1] * 1000:0.0} mm; jitter max {a[2] * 1000:0.00} mm mean {a[3] / Math.Max(1, a[4]) * 1000:0.00} mm"));
    }

    static float Angle(Quaternion a, Quaternion b) => 2 * MathF.Acos(Math.Min(1, Math.Abs(Quaternion.Dot(a, b))));

    public void Skin(World w, int piece, Aff[] pose, Vector3[] outP)
    {
        var p = w.Pieces[piece];
        w.SkinOriginal(p, pose, outP);
        var cb = carryBone[piece];
        var restInv = new Dictionary<int, Aff>();
        var off = p.Offsets(w.Cur.ShapeW[p.MeshIndex]);
        if (!Program.Has("rigidplate"))
        {
            // (each carried vertex as its own skinning has it, then its link's swing and push)
            foreach (var r in rigs)
                for (int k = 0; k < r.Bone.Length && k < r.D.Length; k++)
                    for (int i = 0; i < outP.Length; i++)
                        if (cb[i] == r.Bone[k]) outP[i] = r.D[k].To + Vector3.Transform(outP[i] - r.D[k].From, r.D[k].Q);
            return;
        }
        for (int i = 0; i < outP.Length; i++)
        {
            int b = cb[i];
            if (b < 0) continue;
            if (!restInv.TryGetValue(b, out var ri)) restInv[b] = ri = pose[b] * w.Bones.Rest[b].Inverse();
            outP[i] = ri * (p.RestP[i] + off[i]);
        }
    }

    public string Info(World w) => string.Join(", ", rigs.Select(r => $"{r.Row.Id}: resets {r.Resets} (snaps {r.Snaps}) pushes {r.Pushes} deepest {r.Deepest * 1000:0.0} mm"));
}

public static class Timing
{
    public static long StepT, StepN, ResetT, ResetN;
    public static string Say() => $"follow timing (Release): step {StepT * 1000.0 / System.Diagnostics.Stopwatch.Frequency / Math.Max(1, StepN):0.000} ms per rig-frame over {StepN}, reset {ResetT * 1000.0 / System.Diagnostics.Stopwatch.Frequency / Math.Max(1, ResetN):0.0} ms over {ResetN}";
}
