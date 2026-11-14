using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;

namespace H;

public sealed record Link(string Bone, string Parent, Vector3 Head, Vector3 Tail, float Radius, float Stiffness, float Reach);

public sealed class SpringsFile
{
    public sealed record Row(string Id, List<Link> Links, string Rule, float Reach, float Share);
    public static List<Row> Load(string path)
    {
        var o = new List<Row>();
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        foreach (var e in doc.RootElement.EnumerateArray())
        {
            var links = new List<Link>();
            float creach = 0.06f, share = 0.6f; string rule = "island";
            if (e.TryGetProperty("carry", out var c))
            {
                if (c.TryGetProperty("reach", out var r)) creach = r.GetSingle();
                if (c.TryGetProperty("share", out var s)) share = s.GetSingle();
                if (c.TryGetProperty("rule", out var ru)) rule = ru.GetString() ?? "island";
            }
            foreach (var s in e.GetProperty("springs").EnumerateArray())
            {
                Vector3 V(string k) { var a = s.GetProperty(k).EnumerateArray().Select(x => x.GetSingle()).ToArray(); return new(a[0], a[1], a[2]); }
                links.Add(new Link(s.GetProperty("bone").GetString()!, s.GetProperty("parent").GetString()!, V("head"), V("tail"),
                    s.TryGetProperty("radius", out var rr) ? rr.GetSingle() : 0.04f, s.TryGetProperty("stiffness", out var st) ? st.GetSingle() : 0,
                    s.TryGetProperty("reach", out var re) ? re.GetSingle() : creach));
            }
            o.Add(new Row(e.GetProperty("id").GetString()!, links, rule, creach, share));
        }
        return o;
    }
}

/// <summary>The skeleton with spring bones added (PieceSprings.AddBones: under their parents at the parent's axes and the head).</summary>
public sealed class Bones
{
    public readonly List<string> Name; public readonly List<int> Parent; public readonly List<Aff> Rest;   // global rest
    public readonly int Body;
    public Bones(Skel s)
    {
        Name = s.Name.ToList(); Parent = s.Parent.ToList(); Rest = s.Rest.ToList(); Body = s.Name.Length;
    }
    public int Find(string n) => Name.IndexOf(n);
    public int Add(Link l)
    {
        int have = Find(l.Bone);
        if (have >= 0) return have;
        int pi = Find(l.Parent);
        if (pi < 0) throw new Exception($"no parent {l.Parent}");
        Name.Add(l.Bone); Parent.Add(pi); Rest.Add(new Aff(Rest[pi].X, Rest[pi].Y, Rest[pi].Z, l.Head));
        return Name.Count - 1;
    }
    /// <summary>Local rest of bone b (its parent's global rest inverted times its global rest).</summary>
    public Aff Local(int b) => Parent[b] >= 0 ? Rest[Parent[b]].Inverse() * Rest[b] : Rest[b];
}

/// <summary>View/PieceSprings replayed in System.Numerics (Targets, the cut rules, Write), over ClothChains.</summary>
public sealed class SpringRig
{
    public readonly string What;
    readonly List<Link> links;
    readonly Bones bones;
    readonly (int A, int B, float R)[] capsules;
    public ClothChains Sim = null!;
    int[] bone = Array.Empty<int>(), parentLink = Array.Empty<int>(), bodyParent = Array.Empty<int>(), linkParticle = Array.Empty<int>(), headParticle = Array.Empty<int>(), order = Array.Empty<int>(), roots = Array.Empty<int>();
    Aff[] rest = Array.Empty<Aff>(), rigid = Array.Empty<Aff>(), posed = Array.Empty<Aff>();
    Vector3[] tailLocal = Array.Empty<Vector3>();
    Vector3[] targets = Array.Empty<Vector3>();
    ClothChains.Capsule[] cols = Array.Empty<ClothChains.Capsule>();
    Vector3[] lastRoot = Array.Empty<Vector3>(); Quaternion[] lastRootQ = Array.Empty<Quaternion>();
    bool cut = true; double life;
    public int Resets;
    public float Scale = 1;
    public ClothChains.Tuning Tune = ClothChains.Tuning.Wool;

    public SpringRig(string what, List<Link> links, Bones bones, (int, int, float)[] capsules)
    {
        What = what; this.links = links; this.bones = bones; this.capsules = capsules;
    }

    public int[] LinkBone => bone;
    public IReadOnlyList<Link> Links => links;

    public void Setup(Aff W, Func<int, Aff> globalRest)
    {
        int n = links.Count;
        Scale = W.ScaleX;
        bone = links.Select(l => bones.Find(l.Bone)).ToArray();
        var idx = new Dictionary<string, int>();
        for (int i = 0; i < n; i++) idx[links[i].Bone] = i;
        parentLink = links.Select(l => idx.TryGetValue(l.Parent, out int pi) ? pi : -1).ToArray();
        bodyParent = bone.Select(b => bones.Parent[b]).ToArray();
        rest = bone.Select(b => bones.Local(b)).ToArray();
        tailLocal = new Vector3[n];
        for (int i = 0; i < n; i++)
        {
            int child = Array.FindIndex(parentLink, p => p == i);
            tailLocal[i] = child >= 0 ? rest[child].O : bones.Rest[bone[i]].Inverse() * links[i].Tail;
        }
        var (lp, par, rootLink) = ClothChains.Order(links.Select(l => (l.Bone, l.Parent)).ToList());
        linkParticle = lp;
        headParticle = lp.Select(p => par[p]).ToArray();
        order = Enumerable.Range(0, n).OrderBy(i => lp[i]).ToArray();
        var radius = new float[par.Length]; var stiffness = new float[par.Length];
        for (int i = 0; i < n; i++) { radius[lp[i]] = links[i].Radius * Scale; stiffness[lp[i]] = links[i].Stiffness; }
        Sim = new ClothChains(par, radius, Tune, stiffness);
        rigid = new Aff[n]; posed = new Aff[n];
        targets = new Vector3[par.Length];
        cols = new ClothChains.Capsule[capsules.Length];
        roots = Enumerable.Range(0, par.Length).Where(p => par[p] < 0).ToArray();
        lastRoot = new Vector3[roots.Length]; lastRootQ = new Quaternion[roots.Length];
        Targets(W, globalRest);
        Sim.SetRest(targets, cols);
    }

    void Targets(Aff W, Func<int, Aff> G)
    {
        foreach (int i in order)
        {
            var parent = parentLink[i] >= 0 ? rigid[parentLink[i]] : G(bodyParent[i]);
            rigid[i] = parent * rest[i];
            targets[linkParticle[i]] = W * (rigid[i] * tailLocal[i]);
            if (parentLink[i] < 0) targets[headParticle[i]] = W * rigid[i].O;
        }
        for (int c = 0; c < capsules.Length; c++)
            cols[c] = new ClothChains.Capsule(W * G(capsules[c].A).O, W * G(capsules[c].B).O, capsules[c].R * Scale);
    }

    /// <summary>One frame: the body's global poses G (body bones), dt. Writes the spring bones' global poses into pose.</summary>
    public void Frame(Aff W, Aff[] pose, float dt, bool forceCut)
    {
        Aff G(int b) => pose[b];
        Targets(W, G);
        if (forceCut) cut = true;
        for (int r = 0; r < roots.Length; r++)
        {
            var at = targets[roots[r]];
            int li = Array.FindIndex(headParticle, h => h == roots[r]);
            var q = (new Aff(W.Basis(rigid[li].X), W.Basis(rigid[li].Y), W.Basis(rigid[li].Z), Vector3.Zero)).Rot();
            if (!cut && life > 0 && (Vector3.Distance(at, lastRoot[r]) > Math.Max(0.35f * Scale, 12 * dt) || Angle(q, lastRootQ[r]) > 40 * MathF.PI / 180))
                cut = true;
            lastRoot[r] = at; lastRootQ[r] = q;
        }
        var down = -Vector3.UnitY;
        float ground = W.O.Y;
        if (cut) { Sim.Reset(targets, cols, ground, down); cut = false; Resets++; }
        else Sim.Step(dt, targets, cols, ground, down);
        life += dt;
        Write(W, pose);
    }

    /// <summary>The spring bones riding their parents rigidly (no swing).</summary>
    public void Rigid(Aff[] pose)
    {
        foreach (int i in order)
        {
            var parent = parentLink[i] >= 0 ? pose[bone[parentLink[i]]] : pose[bodyParent[i]];
            pose[bone[i]] = parent * rest[i];
        }
    }

    static float Angle(Quaternion a, Quaternion b)
    {
        float d = Math.Abs(Quaternion.Dot(a, b));
        return 2 * MathF.Acos(Math.Min(1, d));
    }

    void Write(Aff W, Aff[] pose)
    {
        var inv = W.Inverse();
        var x = Sim.Positions;
        foreach (int i in order)
        {
            var parent = parentLink[i] >= 0 ? posed[parentLink[i]] : pose[bodyParent[i]];
            var g = parent * rest[i];
            var want = inv * x[linkParticle[i]] - g.O;
            var have = g.Basis(tailLocal[i]);
            if (want.LengthSquared() > 1e-12f && have.LengthSquared() > 1e-12f)
            {
                var q = FromTo(Vector3.Normalize(have), Vector3.Normalize(want));
                g = g.RotBasis(q);
            }
            posed[i] = g;
            pose[bone[i]] = g;
        }
    }

    public static Quaternion FromTo(Vector3 a, Vector3 b)
    {
        float d = Vector3.Dot(a, b);
        if (d < -0.9999f) return Quaternion.CreateFromAxisAngle(Math.Abs(a.X) < 0.9f ? Vector3.Normalize(Vector3.Cross(a, Vector3.UnitX)) : Vector3.UnitY, MathF.PI);
        var c = Vector3.Cross(a, b);
        return Quaternion.Normalize(new Quaternion(c, 1 + d));
    }
}
