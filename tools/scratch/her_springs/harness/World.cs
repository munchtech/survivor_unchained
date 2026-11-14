using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text;
using SurvivorUnchained.Play;

namespace H;

public interface IDesign
{
    void Setup(World w);
    /// <summary>One frame of the body (pose: body bones' globals, skeleton space); cut: a forced reset.</summary>
    void Frame(World w, Frame f, Aff[] pose, float dt, bool cut);
    /// <summary>The piece's vertices posed (skeleton space).</summary>
    void Skin(World w, int piece, Aff[] pose, Vector3[] outP);
    string Info(World w) => "";
}

public sealed class Piece
{
    public string Row = "";            // springs row id
    public Vector3[] RestP = Array.Empty<Vector3>();   // rest place (skeleton space)
    public bool[] Sel = Array.Empty<bool>();
    public int MeshIndex;
    public Aff CarryM = Aff.I;              // (PieceCarry's springs' binds' frame: the bind most vertices ride most)
    /// <summary>Each vertex's blend shape offset at the frame's weights, in the springs' binds' frame (skeleton rest).</summary>
    public Vector3[] Offsets(float[] w)
    {
        var o = new Vector3[Mesh.Pos.Length];
        for (int s = 0; s < w.Length; s++)
        {
            if (Math.Abs(w[s]) <= 1e-6f) continue;
            var sh = Mesh.Shapes[s];
            for (int i = 0; i < sh.Idx.Length; i++) o[sh.Idx[i]] += w[s] * sh.DP[i];
        }
        for (int i = 0; i < o.Length; i++) if (o[i] != Vector3.Zero) o[i] = CarryM.Basis(o[i]);
        return o;
    }
    public MeshD Mesh = null!;
}

public sealed class World
{
    public readonly Skel Sk; public readonly MeshD[] Meshes; public readonly List<Frame> Frames;
    public readonly MeshD Body;
    public readonly string[] Region;
    public readonly List<Piece> Pieces = new();
    public readonly Bones Bones;
    public readonly List<SpringsFile.Row> Rows;
    public int Every;
    public HashSet<string>? ClipSet;

    public World(Skel sk, MeshD[] meshes, List<Frame> frames)
    {
        Sk = sk; Meshes = meshes; Frames = frames;
        Body = meshes.First(m => m.Slot == "body");
        int k = Body.K;
        var names = Body.BindBone.Select(b => b >= 0 ? Probe.Region(sk.Name[b]) : "torso").ToArray();
        Region = new string[Body.Pos.Length];
        for (int i = 0; i < Region.Length; i++)
        {
            int best = 0;
            for (int j = 1; j < k; j++) if (Body.Weights[i * k + j] > Body.Weights[i * k + best]) best = j;
            int bind = Body.Bones[i * k + best];
            Region[i] = bind >= 0 && bind < names.Length ? names[bind] : "torso";
        }
        Bones = new Bones(sk);
        Rows = SpringsFile.Load(Program.O("springs", System.IO.Path.GetFullPath(System.IO.Path.Combine(AppContext.BaseDirectory, "../../../../../../../godot/art/people/springs.json"))));
        foreach (var m in meshes.Where(m => m.Slot != "body"))
        {
            string row = m.Name.StartsWith("warden_skirt") ? "warden.skirt" : m.Name.StartsWith("plate_pauldrons_warden") ? "plate_pauldrons_warden" : m.Name.StartsWith("warden_pauldrons") ? "warden.pauldrons" : "";
            var p = new Piece { Mesh = m, Row = row, MeshIndex = Array.IndexOf(meshes, m) };
            p.RestP = RestPlaces(m);
            {
                var bt = BindTo(m);
                var votes = new int[Math.Max(1, bt.Length)];
                for (int i = 0; i < m.Pos.Length; i++)
                {
                    int best = 0;
                    for (int q = 1; q < m.K; q++) if (m.Weights[i * m.K + q] > m.Weights[i * m.K + best]) best = q;
                    int b = m.Bones[i * m.K + best];
                    if (b >= 0 && b < bt.Length) votes[b]++;
                }
                if (bt.Length > 0) p.CarryM = bt[Array.IndexOf(votes, votes.Max())];
            }
            Pieces.Add(p);
        }
        Every = (int)Program.F("every", 2);
        if (Program.Has("clips")) ClipSet = new HashSet<string>(Program.O("clips", "").Split(','));
    }

    public Aff[] BindTo(MeshD m) => m.BindBone.Select((bone, b) => bone >= 0 ? Sk.Rest[bone] * m.Bind[b] : Aff.I).ToArray();

    /// <summary>Each vertex's rest place: its weights' blend of its binds' frames at the skeleton rest (PieceCarry.Pick).</summary>
    public Vector3[] RestPlaces(MeshD m)
    {
        var t = BindTo(m);
        var o = new Vector3[m.Pos.Length];
        Probe.Skin(m.Pos, m.Nrm, m.Bones, m.Weights, m.K, t, o, null);
        return o;
    }

    public Aff[] Mats(MeshD m, Aff[] pose) => m.BindBone.Select((bone, b) => bone >= 0 ? pose[bone] * m.Bind[b] : Aff.I).ToArray();

    /// <summary>The original skin of a piece at pose.</summary>
    public void SkinOriginal(Piece p, Aff[] pose, Vector3[] outP)
    {
        var (sp, sn) = Probe.Shaped(p.Mesh, Cur.ShapeW[p.MeshIndex]);
        Probe.Skin(sp, sn, p.Mesh.Bones, p.Mesh.Weights, p.Mesh.K, Mats(p.Mesh, pose), outP, null);
    }
    public Frame Cur = null!;

    public void Run(string mode)
    {
        IDesign d = mode switch
        {
            "base" => new BaseDesign(),
            "game" => new GameDesign(),
            _ => Designs.Make(mode),
        };
        if (Program.Has("at")) { Diag.Run(this, d, Program.O("at", "")); return; }
        var clock = Stopwatch.StartNew();
        d.Setup(this);
        Console.WriteLine($"setup {clock.ElapsedMilliseconds} ms {d.Info(this)}");
        var pose = new Aff[Bones.Name.Count];
        string lastClip = "";
        var worst = new Dictionary<string, (Probe.Stat Sk, double SkT, Probe.Stat Pa, double PaT, float PaPct)>();
        var order = new List<string>();
        var bodyP = new Vector3[Body.Pos.Length]; var bodyN = new Vector3[Body.Pos.Length];
        var piecesP = Pieces.Select(p => new Vector3[p.Mesh.Pos.Length]).ToArray();
        long measured = 0; double msTest = 0;
        var max = new Dictionary<string, float[]>();
        var log = Program.Has("log") ? new StreamWriter(Program.O("log", "h.jsonl")) : null;
        for (int fi = 0; fi < Frames.Count; fi++)
        {
            var f = Frames[fi];
            for (int b = 0; b < Sk.Name.Length; b++) pose[b] = f.G[b];
            Cur = f;
            bool cut = fi == 0 || f.Clip != lastClip;
            lastClip = f.Clip;
            d.Frame(this, f, pose, 1f / 60, cut);
            if (f.Clip == "" || f.F % Every != 0 || (ClipSet != null && !ClipSet.Contains(f.Clip))) continue;
            var c0 = Stopwatch.StartNew();
            var (bp0, bn0) = Probe.Shaped(Body, f.ShapeW[Array.IndexOf(Meshes, Body)]);
            Probe.Skin(bp0, bn0, Body.Bones, Body.Weights, Body.K, Mats(Body, pose), bodyP, bodyN);
            var test = new InsideTest(bodyP, bodyN, Body.Tris);
            var st = new Dictionary<string, Probe.Stat>();
            for (int i = 0; i < Pieces.Count; i++)
            {
                var p = Pieces[i];
                d.Skin(this, i, pose, piecesP[i]);
                var s = Probe.Count(test, Region, piecesP[i]);
                if (!st.TryGetValue(p.Mesh.Slot, out var a)) st[p.Mesh.Slot] = a = new Probe.Stat();
                a.N += s.N; a.Inside += s.Inside; a.Thigh += s.Thigh; a.Arm += s.Arm; a.Torso += s.Torso; a.Deep = Math.Max(a.Deep, s.Deep);
                a.DThigh = Math.Max(a.DThigh, s.DThigh); a.DArm = Math.Max(a.DArm, s.DArm); a.DTorso = Math.Max(a.DTorso, s.DTorso);
            }
            msTest += c0.Elapsed.TotalMilliseconds; measured++;
            if (!worst.ContainsKey(f.Clip)) { worst[f.Clip] = (new Probe.Stat(), 0, new Probe.Stat(), 0, 0); order.Add(f.Clip); }
            var w = worst[f.Clip];
            if (st.TryGetValue("skirt", out var sks) && sks.Thigh > w.Sk.Thigh) { w.Sk = sks; w.SkT = f.T; }
            if (st.TryGetValue("pauldrons", out var pas) && pas.N > 0 && 100f * pas.Inside / pas.N > w.PaPct) { w.Pa = pas; w.PaT = f.T; w.PaPct = 100f * pas.Inside / pas.N; }
            worst[f.Clip] = w;
            if (!max.TryGetValue(f.Clip, out var mx)) max[f.Clip] = mx = new float[8];
            if (sks != null) { mx[0] = Math.Max(mx[0], sks.Thigh); mx[1] = Math.Max(mx[1], sks.DThigh); mx[2] = Math.Max(mx[2], sks.Torso + sks.Arm); mx[3] = Math.Max(mx[3], Math.Max(sks.DTorso, sks.DArm)); mx[4] = Math.Max(mx[4], sks.Deep); }
            if (pas != null && pas.N > 0) { mx[5] = Math.Max(mx[5], 100f * pas.Inside / pas.N); mx[6] = Math.Max(mx[6], pas.Deep); }
            log?.WriteLine($"{{\"clip\":\"{f.Clip}\",\"t\":{f.T:0.###},\"f\":{f.F},\"skirt\":[{St(st, "skirt")}],\"paul\":[{St(st, "pauldrons")}]}}");
        }
        log?.Dispose();
        Console.WriteLine(Timing.Say());
        Console.WriteLine($"measured {measured} frames, {msTest / Math.Max(1, measured):0} ms each, total {clock.Elapsed.TotalSeconds:0.0} s {d.Info(this)}");
        Console.WriteLine($"{"clip",-22} skirt thigh (t, deep mm, torso)      pauldrons % (t, deep mm)");
        int sumSk = 0; float sumPa = 0;
        foreach (var c in order)
        {
            var w = worst[c];
            sumSk += w.Sk.Thigh; sumPa += w.PaPct;
            Console.WriteLine($"{c,-22} {w.Sk.Thigh,6} ({w.SkT:0.00}s, {w.Sk.Deep,5:0.0}, {w.Sk.Torso,5})      {w.PaPct,5:0.0}% ({w.PaT:0.00}s, {w.Pa.Deep,4:0.0})");
        }
        Console.WriteLine($"{"SUM",-22} {sumSk,6}                         {sumPa / Math.Max(1, order.Count),5:0.0}% mean");
        FollowDesign.Say();
        // the clip's maxima over every measured frame (the lead's bar): thigh pts, thigh deep, torso pts, torso deep, skirt deep, pauldron %, pauldron deep
        foreach (var c in order)
            if (max.TryGetValue(c, out var m))
                Console.WriteLine(FormattableString.Invariant($"MAX {c} {m[0]:0} {m[1]:0.0} {m[2]:0} {m[3]:0.0} {m[4]:0.0} {m[5]:0.00} {m[6]:0.0}"));
    }

    static string St(Dictionary<string, Probe.Stat> st, string k) => st.TryGetValue(k, out var s) ? $"{s.N},{s.Inside},{s.Thigh},{s.Arm},{s.Torso},{s.Deep:0.0},{s.DThigh:0.0},{s.DArm:0.0},{s.DTorso:0.0}" : "";
}

public sealed class BaseDesign : IDesign
{
    public void Setup(World w) { }
    public void Frame(World w, Frame f, Aff[] pose, float dt, bool cut) { }
    public void Skin(World w, int piece, Aff[] pose, Vector3[] outP) => w.SkinOriginal(w.Pieces[piece], pose, outP);
}

/// <summary>The game as it is (38bf97ee2..913806564): island carry onto pelvis/trap-rooted spring bones, ClothChains.</summary>
public sealed class GameDesign : IDesign
{
    readonly List<SpringRig> rigs = new();
    // per piece: each vertex's link bone (-1: original), by rig
    readonly List<int[]> carryBone = new();
    public static (int A, int B, float R)[] Capsules(World w)
    {
        // as the game's log has them (her:A's body capsules)
        var names = new (string A, string B, float R)[] { ("thigh_l","calf_l",0.114f),("calf_l","foot_l",0.080f),("thigh_r","calf_r",0.111f),("calf_r","foot_r",0.082f),
            ("pelvis","spine_01",0.157f),("spine_01","spine_02",0.127f),("spine_02","spine_03",0.105f),("spine_03","neck_01",0.150f),("upperarm_l","lowerarm_l",0.056f),("upperarm_r","lowerarm_r",0.056f) };
        return names.Select(n => (w.Sk.Find(n.A), w.Sk.Find(n.B), n.R)).ToArray();
    }
    public void Setup(World w)
    {
        var caps = Capsules(w);
        foreach (var row in w.Rows.Where(r => w.Pieces.Any(p => p.Row == r.Id)))
        {
            foreach (var l in row.Links) w.Bones.Add(l);
            var rig = new SpringRig(row.Id, row.Links, w.Bones, Program.Has("nocol") ? Array.Empty<(int, int, float)>() : caps);
            rig.Tune = rig.Tune with { Gravity = Program.F("grav", 9.8f) };
            rigs.Add(rig);
        }
        foreach (var p in w.Pieces)
        {
            var row = w.Rows.FirstOrDefault(r => r.Id == p.Row);
            var cb = new int[p.Mesh.Pos.Length];
            Array.Fill(cb, -1);
            if (row != null)
            {
                var segs = row.Links.Select(l => new SpringCarry.Seg(l.Head, l.Tail, l.Reach)).ToArray();
                var (link, sh) = SpringCarry.Assign(p.RestP, p.Mesh.Tris, segs, SpringCarry.Parse(row.Rule), row.Share);
                for (int i = 0; i < cb.Length; i++) if (link[i] >= 0 && sh[i] >= 0.999f) cb[i] = w.Bones.Find(row.Links[link[i]].Bone);
                Console.WriteLine($"carry {p.Mesh.Name}: {cb.Count(x => x >= 0)} of {cb.Length}");
            }
            carryBone.Add(cb);
        }
    }
    bool setUp;
    public void Frame(World w, Frame f, Aff[] pose, float dt, bool cut)
    {
        if (!setUp) { setUp = true; foreach (var r in rigs) r.Setup(f.W, b => w.Bones.Rest[b]); }
        if (Program.Has("rigid")) { foreach (var r in rigs) r.Rigid(pose); return; }
        foreach (var r in rigs) r.Frame(f.W, pose, dt, cut);
    }
    public void Skin(World w, int piece, Aff[] pose, Vector3[] outP)
    {
        var p = w.Pieces[piece];
        w.SkinOriginal(p, pose, outP);
        var cb = carryBone[piece];
        var restInv = new Dictionary<int, Aff>();
        var off = p.Offsets(w.Cur.ShapeW[p.MeshIndex]);
        for (int i = 0; i < outP.Length; i++)
        {
            int b = cb[i];
            if (b < 0) continue;
            if (!restInv.TryGetValue(b, out var ri)) restInv[b] = ri = pose[b] * w.Bones.Rest[b].Inverse();
            outP[i] = ri * (p.RestP[i] + off[i]);
        }
    }
    public string Info(World w) => "resets " + string.Join(",", rigs.Select(r => $"{r.What}:{r.Resets}"));
}
