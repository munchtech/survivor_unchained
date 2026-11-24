using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained;

/// <summary>(dev, --mem-strip S; the tester lane, 24 Nov: what is a place's "other" video memory, the engine's total less its
/// textures and buffers?) At S s (default 40), one way, never for play:
/// 1. a calibration: 2000 one-triangle meshes made, then freed: the video memory one small buffer really takes beside what
///    the buffer counter says (a D3D12 buffer is placed at 64 KB unless the driver packs it tighter);
/// 2. (--mem-strip-ribbons N) N idle trail meshes (Fx/Ribbons) made, then freed: what one costs beside what it is counted;
/// 3. the place taken apart: the tree cut into its biggest groups (no group holds the camera), each freed in turn, biggest
///    first, and the monitors read 30 frames later: what each group's textures, buffers and "other" were;
/// 4. (--mem-strip-under NAME instead of 3) a garbage collection, then that node's children a class at a time, a collection, the
///    node itself, a collection: what its children held, what only its C# fields held, and what its freeing let go.
/// Read it with care: a step's line is whatever changed in its 30 frames, so a load still running or an engine pool that lets go
/// on its own lands on whichever step it falls in (24 Nov: one -52 MB drop landed on Ribbons, then on another group the next run).
/// Each line: "mem strip: ..." with the change since the last line, in MB.</summary>
public partial class MemLog
{
    readonly double stripAt = Args.Has("mem-strip") ? Args.Num("mem-strip", 40) : -1;
    int stripWait;
    bool stripDone;
    (double Tex, double Buf, double Vid) stripPrev;
    // The steps still to run: each is the name its line is printed under (the change it caused) and what it does.
    Queue<(string Name, int Count, Action? Do)>? stripSteps;

    void StripTick()
    {
        if (stripAt < 0 || stripDone || Time.GetTicksMsec() / 1000.0 < stripAt) return;
        if (stripWait-- > 0) return;
        var m = Mon();
        stripWait = 30;
        if (stripSteps == null)
        {
            GD.Print($"mem strip: start | video {m.Vid:0} texture {m.Tex:0} buffers {m.Buf:0} other {m.Vid - m.Tex - m.Buf:0} MB");
            stripSteps = new();
            Plan(stripSteps);
        }
        else if (stripLast is var (name, n))
            GD.Print($"mem strip: {name}: texture {m.Tex - stripPrev.Tex:+0.0;-0.0;0}, buffers {m.Buf - stripPrev.Buf:+0.0;-0.0;0}, " +
                $"video {m.Vid - stripPrev.Vid:+0.0;-0.0;0}, other {(m.Vid - m.Tex - m.Buf) - (stripPrev.Vid - stripPrev.Tex - stripPrev.Buf):+0.0;-0.0;0} MB" +
                (n > 0 ? $" ({(m.Vid - stripPrev.Vid) * 1024 / n:0.0} KB video and {(m.Buf - stripPrev.Buf) * 1048576 / n:0} B buffers each)" : "") +
                $" | now video {m.Vid:0} texture {m.Tex:0} buffers {m.Buf:0} other {m.Vid - m.Tex - m.Buf:0}");
        stripPrev = m;
        if (stripSteps.Count == 0) { GD.Print("mem strip: done"); stripDone = true; return; }
        var step = stripSteps.Dequeue();
        stripLast = (step.Name, step.Count);
        step.Do?.Invoke();
    }
    (string, int)? stripLast;

    void Plan(Queue<(string, int, Action?)> q)
    {
        // 1. one small buffer: 2000 one-triangle meshes made, then freed
        var tiny = new List<ArrayMesh>();
        q.Enqueue(("2000 one-triangle meshes made", 2000, () =>
        {
            for (int i = 0; i < 2000; i++)
            {
                var a = new Godot.Collections.Array();
                a.Resize((int)Mesh.ArrayType.Max);
                a[(int)Mesh.ArrayType.Vertex] = new[] { new Vector3(i, 0, 0), new Vector3(i, 1, 0), new Vector3(i, 0, 1) };
                var mesh = new ArrayMesh();
                mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, a);
                tiny.Add(mesh);
            }
        }));
        q.Enqueue(("the 2000 freed", 2000, () => { foreach (var x in tiny) x.Dispose(); tiny.Clear(); }));
        // 2. --mem-strip-ribbons N: N trail meshes (Fx/Ribbons, two dynamic meshes of 9000 vertices each) made idle, then freed
        int nr = Args.Has("mem-strip-ribbons") ? (int)Args.Num("mem-strip-ribbons", 4) : 0;
        var rib = new List<Node>();
        if (nr > 0)
        {
            q.Enqueue(($"{nr} idle Ribbons made", nr, () => { for (int i = 0; i < nr; i++) { var r = new View.Ribbons(); rib.Add(r); GetParent().AddChild(r); } }));
            q.Enqueue(($"the {nr} Ribbons freed", nr, () => { foreach (var r in rib) r.QueueFree(); rib.Clear(); }));
        }
        // (two steps that free nothing: what moves on its own in 30 frames)
        q.Enqueue(("nothing freed (a control)", 0, null));
        q.Enqueue(("nothing freed (a control)", 0, null));
        // 3. the place taken apart, biggest group first; under a node (--mem-strip-under), a collection first, then its children
        //    freed a class at a time (its MeshInstance3Ds, then its MultiMeshInstance3Ds, ...), each class's line naming them
        var groups = Groups(out var under);
        if (Args.Has("mem-strip-list")) foreach (var g in groups.Take(2)) ListMeshes(g);
        if (under == null)
        {
            GD.Print($"mem strip: {groups.Count} groups: " + string.Join(", ", groups.Select(g => $"{Short(g)} ({Count(g)})")));
            // each group freed, then a collection: a mesh or material a script made is held by its C# wrapper until the
            // collector finalizes it, so the freeing alone lets go of little (24 Nov: BattleFx's children freed, 0; a collection
            // after, -60 MB, in town and den alike)
            q.Enqueue(("a garbage collection (before)", 0, Collect));
            foreach (var g in groups)
            {
                string what = $"{Short(g)} ({Count(g)} nodes, {Surfaces(g)} unique mesh surfaces, {Mats(g)} unique materials)";
                q.Enqueue(($"freed {what}", 0, () => { if (IsInstanceValid(g)) g.QueueFree(); }));
                q.Enqueue(($"  then a collection", 0, Collect));
            }
            // (--mem-statics: then what still holds each texture: MemLog.Statics)
            if (Args.Has("mem-statics")) q.Enqueue(("the statics census", 0, () => Statics(GetTree().Root)));
            return;
        }
        q.Enqueue(("a garbage collection (before)", 0, Collect));
        foreach (var kind in groups.GroupBy(g => g.GetClass()).OrderByDescending(k => k.Sum(Count)))
        {
            var list = kind.ToList();
            string names = string.Join(", ", list.Take(8).Select(g => g.Name.ToString())) + (list.Count > 8 ? $", ... {list.Count - 8} more" : "");
            q.Enqueue(($"freed {Short(under)}'s {list.Count} {kind.Key} ({list.Sum(Count)} nodes, {list.Sum(Surfaces)} unique mesh surfaces, {list.Sum(Mats)} materials: {names})",
                0, () => { foreach (var g in list) if (IsInstanceValid(g)) g.QueueFree(); }));
        }
        // 4. what the node itself still holds once its children are gone: a collection frees what only a C# field held, then the node
        q.Enqueue(("a garbage collection (what only C# held)", 0, Collect));
        q.Enqueue(($"freed {Short(under)} itself", 0, () => { if (IsInstanceValid(under)) under.QueueFree(); }));
        q.Enqueue(("a garbage collection after", 0, Collect));
    }

    // --mem-strip-list (dev): a group's unique meshes by where they come from (a file's folder, or "made: " the node's name
    // without its numbers and the mesh's class): how many, their surfaces, vertices, and the instances that draw them. On D3D12
    // each surface's vertex, attribute and index buffers are placed at 64 KB apiece, so many small surfaces cost far more than
    // their bytes.
    static void ListMeshes(Node root)
    {
        var rows = new Dictionary<string, (HashSet<ulong> Meshes, int Surf, long Verts, int Inst)>();
        foreach (var n in All(root))
        {
            Mesh? m = n switch { MeshInstance3D mi => mi.Mesh, MultiMeshInstance3D mm => mm.Multimesh?.Mesh, _ => null };
            if (m == null) continue;
            string key = m.ResourcePath is { Length: > 0 } rp && !rp.Contains("::")
                ? System.IO.Path.GetDirectoryName(rp.Replace("res://", ""))?.Replace(System.IO.Path.DirectorySeparatorChar, '/') ?? rp
                : m.ResourcePath.Contains("::") ? "in " + m.ResourcePath[..m.ResourcePath.IndexOf("::")].Replace("res://", "")
                : $"made: {System.Text.RegularExpressions.Regex.Replace(n.Name.ToString(), @"[@\d_]+", "")} {m.GetClass()}";
            rows.TryGetValue(key, out var r);
            r.Meshes ??= new HashSet<ulong>();
            r.Inst++;
            if (r.Meshes.Add(m.GetInstanceId()))
            {
                r.Surf += m.GetSurfaceCount();
                if (m is ArrayMesh am) for (int s = 0; s < am.GetSurfaceCount(); s++) r.Verts += am.SurfaceGetArrayLen(s);
            }
            rows[key] = r;
        }
        GD.Print($"mem strip list {root.Name}: {rows.Sum(r => r.Value.Meshes.Count)} unique meshes, {rows.Sum(r => r.Value.Surf)} surfaces, {rows.Sum(r => r.Value.Inst)} instances");
        foreach (var (k, r) in rows.OrderByDescending(r => r.Value.Surf).Take(30))
            GD.Print($"mem strip list {root.Name}: {r.Surf} surfaces, {r.Meshes.Count} meshes, {r.Verts} vertices, {r.Inst} instances: {k}");
    }

    static void Collect() { GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect(); }

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
    List<Node> Groups(out Node? under)
    {
        under = null;
        var cam = GetViewport().GetCamera3D();
        bool Ok(Node n) => n != this && !n.IsAncestorOf(this) && (cam == null || (n != cam && !n.IsAncestorOf(cam)));
        var game = GetParent();
        // --mem-strip-under NAME: every child of the first node so named under the game, one group each (biggest first), then the node
        if (Args.Get("mem-strip-under") is { Length: > 0 } name && game.FindChild(name, true, false) is { } u)
        {
            under = u;
            return u.GetChildren().Where(Ok).OrderByDescending(Count).ToList();
        }
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
