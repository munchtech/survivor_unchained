using System;
using Godot;

namespace SurvivorUnchained;

/// <summary>(dev, --mem-log N) Every N seconds (default 10) one log line of the game's own memory monitors: Godot's static
/// memory, video and texture memory, buffers, object, resource and node counts, orphan nodes, the .NET heap and the
/// process's working set and private bytes, with the zone. tools/perf/memrun.py samples the process from outside and
/// reads these lines from the same log (the tester lane, 23 Nov: a tester's build reached 6.8 GB).</summary>
public partial class MemLog : Node
{
    readonly double every;
    double t;

    public MemLog(double every) { this.every = Math.Max(1, every); ProcessMode = ProcessModeEnum.Always; }

    public override void _Process(double delta)
    {
        if ((t += delta) < every) return;
        t = 0;
        Line(GetParent() is Play.Game g ? g.Zone?.Id ?? "-" : "-");
    }

    public static void Line(string where)
    {
        static double M(Performance.Monitor m) => Performance.GetMonitor(m) / 1048576.0;
        static long N(Performance.Monitor m) => (long)Performance.GetMonitor(m);
        using var me = System.Diagnostics.Process.GetCurrentProcess();
        GD.Print($"mem: t {Time.GetTicksMsec() / 1000.0:0} s zone {where} | static {M(Performance.Monitor.MemoryStatic):0} MB, " +
                 $"video {M(Performance.Monitor.RenderVideoMemUsed):0} MB, texture {M(Performance.Monitor.RenderTextureMemUsed):0} MB, " +
                 $"buffers {M(Performance.Monitor.RenderBufferMemUsed):0} MB | objects {N(Performance.Monitor.ObjectCount)}, " +
                 $"resources {N(Performance.Monitor.ObjectResourceCount)}, nodes {N(Performance.Monitor.ObjectNodeCount)}, " +
                 $"orphans {N(Performance.Monitor.ObjectOrphanNodeCount)} | managed {GC.GetTotalMemory(false) / 1048576.0:0} MB | " +
                 $"working set {me.WorkingSet64 / 1048576.0:0} MB, private {me.PrivateMemorySize64 / 1048576.0:0} MB");
    }
}
