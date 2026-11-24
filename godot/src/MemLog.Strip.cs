using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained;

/// <summary>(dev, --mem-strip S; the tester lane, 24 Nov: what is a place's "other" video memory, the engine's total less its
/// textures and buffers?) At S s (default 40), one way, never for play:
/// 1. a calibration: 2000 one-triangle meshes made, then freed: the video memory one small buffer really takes beside what
///    the buffer counter says (a D3D12 buffer is placed at 64 KB unless the driver packs it tighter);
/// 2. the place taken apart: the tree cut into its biggest groups (no group holds the camera), each freed in turn, biggest
///    first, and the monitors read 30 frames later: what each group's textures, buffers and "other" were.
/// Each line: "mem strip: ..." with the change since the last line, in MB.</summary>
public partial class MemLog
{
    readonly double stripAt = Args.Has("mem-strip") ? Args.Num("mem-strip", 40) : -1;
    int stripStep = -1, stripWait;
    (double Tex, double Buf, double Vid) stripPrev;
    readonly List<ArrayMesh> stripMeshes = new();
    List<Node>? stripGroups;

    void StripTick()
    {
        if (stripAt < 0 || Time.GetTicksMsec() / 1000.0 < stripAt || stripStep == int.MaxValue) return;
        if (stripWait-- > 0) return;
        var m = Mon();
        string Line(string what, int n = 0) =>
            $"mem strip: {what}: texture {m.Tex - stripPrev.Tex:+0.0;-0.0;0}, buffers {m.Buf - stripPrev.Buf:+0.0;-0.0;0}, " +
            $"video {m.Vid - stripPrev.Vid:+0.0;-0.0;0}, other {(m.Vid - m.Tex - m.Buf) - (stripPrev.Vid - stripPrev.Tex - stripPrev.Buf):+0.0;-0.0;0} MB" +
            (n > 0 ? $" ({(m.Vid - stripPrev.Vid) * 1024 / n:0.0} KB video and {(m.Buf - stripPrev.Buf) * 1048576 / n:0} B buffers each)" : "") +
            $" | now video {m.Vid:0} texture {m.Tex:0} buffers {m.Buf:0} other {m.Vid - m.Tex - m.Buf:0}";
        stripWait = 30;
        switch (stripStep++)
        {
            case -1:
                GD.Print($"mem strip: start | video {m.Vid:0} texture {m.Tex:0} buffers {m.Buf:0} other {m.Vid - m.Tex - m.Buf:0} MB");
                for (int i = 0; i < 2000; i++)
                {
                    var a = new Godot.Collections.Array();
                    a.Resize((int)Mesh.ArrayType.Max);
                    a[(int)Mesh.ArrayType.Vertex] = new[] { new Vector3(i, 0, 0), new Vector3(i, 1, 0), new Vector3(i, 0, 1) };
                    var mesh = new ArrayMesh();
                    mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, a);
                    stripMeshes.Add(mesh);
                }
                break;
            case 0:
                GD.Print(Line("2000 one-triangle meshes made", 2000));
                foreach (var x in stripMeshes) x.Dispose();
                stripMeshes.Clear();
                break;
            case 1:
                GD.Print(Line("the 2000 freed", 2000));
                stripGroups = Groups();
                GD.Print($"mem strip: {stripGroups.Count} groups: " + string.Join(", ", stripGroups.Select(g => $"{Short(g)} ({Count(g)})")));
                goto default;
            default:
                if (stripGroups == null) { stripStep = int.MaxValue; return; }
                int k = stripStep - 2;
                if (k > 0) GD.Print(Line($"freed {stripName}"));
                if (k >= stripGroups.Count) { GD.Print("mem strip: done"); stripStep = int.MaxValue; return; }
                var g = stripGroups[k];
                stripName = IsInstanceValid(g) ? $"{Short(g)} ({Count(g)} nodes, {Surfaces(g)} unique mesh surfaces, {Mats(g)} unique materials)" : "(gone)";
                if (IsInstanceValid(g)) g.QueueFree();
                break;
        }
        stripPrev = m;
    }
    string stripName = "";

    static int Count(Node n) { int c = 1; foreach (var k in n.GetChildren()) c += Count(k); return c; }
    string Short(Node n) => GetParent() is { } gp && gp.IsAncestorOf(n) ? gp.GetPathTo(n).ToString() : n.GetPath().ToString();

    static int Surfaces(Node root)
    {
        var seen = new HashSet<ulong>();
        int s = 0;
        void Add(Mesh? m) { if (m != null && seen.Add(m.GetInstanceId())) s += m.GetSurfaceCount(); }
        foreach (var n in All(root))
            switch (n)
            {
                case MeshInstance3D mi: Add(mi.Mesh); break;
                case MultiMeshInstance3D mm: Add(mm.Multimesh?.Mesh); break;
                case GpuParticles3D gp: for (int d = 0; d < gp.DrawPasses; d++) Add(gp.GetDrawPassMesh(d)); break;
            }
        return s;
    }

    static int Mats(Node root)
    {
        var seen = new HashSet<ulong>();
        foreach (var n in All(root))
        {
            if (n is GeometryInstance3D g)
            {
                if (g.MaterialOverride != null) seen.Add(g.MaterialOverride.GetInstanceId());
                if (g is MeshInstance3D mi && mi.Mesh != null)
                    for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++) if (mi.GetActiveMaterial(s) is { } m) seen.Add(m.GetInstanceId());
            }
            else if (n is CanvasItem c && c.Material != null) seen.Add(c.Material.GetInstanceId());
        }
        return seen.Count;
    }

    static IEnumerable<Node> All(Node n) { yield return n; foreach (var k in n.GetChildren()) foreach (var x in All(k)) yield return x; }

    // The game node's subtrees, the biggest split into its children while it holds over 400 nodes, up to 18 groups; none holds
    // the camera in use or this node; biggest first.
    List<Node> Groups()
    {
        var cam = GetViewport().GetCamera3D();
        bool Ok(Node n) => n != this && !n.IsAncestorOf(this) && (cam == null || (n != cam && !n.IsAncestorOf(cam)));
        var game = GetParent();
        // --mem-strip-under NAME: the children of the first node so named under the game, one group each (up to 40, biggest first)
        if (Args.Get("mem-strip-under") is { Length: > 0 } under && game.FindChild(under, true, false) is { } u)
            return u.GetChildren().Where(Ok).OrderByDescending(Count).Take(40).ToList();
        var groups = game.GetChildren().Where(n => n != this).ToList();
        for (int guard = 0; guard < 40; guard++)
        {
            var big = groups.Where(n => !Ok(n) || Count(n) > 400).Where(n => n.GetChildCount() > 0).OrderByDescending(Count).FirstOrDefault();
            if (big == null || groups.Count >= 18 && Ok(big)) break;
            groups.Remove(big);
            groups.AddRange(big.GetChildren());
        }
        return groups.Where(Ok).OrderByDescending(Count).Take(18).ToList();
    }
}
