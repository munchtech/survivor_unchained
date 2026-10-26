using System.Collections.Generic;
using System.Threading.Tasks;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// A townsperson come out of a door into a running town (IZoneLook.WalkerLater): made on a worker thread (People.Build,
/// out of the tree: MR4, a walker made on the main thread held its frame ~28 ms), stood in the scene when it is done,
/// a frame or few later, with the calls made of it meanwhile played on it then (where it is, its loop, its pace, what
/// it holds, its last gesture). Until then nothing of it shows (it has nothing to show).
/// </summary>
public partial class WalkerView : Node3D, INpcView
{
    PersonView? inner;
    Task<PersonView>? job;
    PersonSpec spec;
    double scale;
    (double X, double Y, double Z, double H, bool V)? place;
    (string Clip, double Blend, double Speed)? loop;
    (string Clip, double Speed)? act;
    double? pace;
    readonly List<(string Slot, string? Pack, string? Piece)> holds = new();

    public WalkerView(PersonSpec spec, double scale)
    {
        this.spec = spec;
        this.scale = scale;
        job = Task.Run(() => { var v = new PersonView(spec, null, scale); v.BeginShadow(); return v; });
    }

    public override void _Process(double delta)
    {
        if (job is not { IsCompleted: true } j) return;
        job = null;
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        PersonView v;
        if (j.IsCompletedSuccessfully) v = j.Result;
        else { GD.PushWarning($"walker made on a worker failed ({j.Exception?.InnerException?.Message}): made here"); v = new PersonView(spec, null, scale); }
        AddChild(v);
        v.Lod();
        foreach (var (s, pk, pc) in holds) v.Hold(s, pk, pc);
        if (place is var (x, y, z, h, vis)) v.Place(x, y, z, h, vis);
        if (loop is var (c, b, sp)) v.Loop(c, b, sp);
        if (pace is double p) v.Locomotion(p);
        if (act is var (ac, asp)) v.Act(ac, asp);
        v.Settle();
        inner = v;
        SetProcess(false);
        if (Perf.On) GD.Print($"perf walker stood up: {(System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency:0.0} ms on the main thread");
    }

    public void Place(double x, double y, double z, double heading, bool visible)
    {
        if (inner != null) inner.Place(x, y, z, heading, visible); else place = (x, y, z, heading, visible);
    }

    public void Loop(string clip, double blend = 0.3, double speed = 1)
    {
        if (inner != null) inner.Loop(clip, blend, speed); else { loop = (clip, blend, speed); act = null; }
    }

    public void Act(string clip, double speed = 1)
    {
        if (inner != null) inner.Act(clip, speed); else act = (clip, speed);
    }

    public void Locomotion(double speed)
    {
        if (inner != null) inner.Locomotion(speed); else pace = speed;
    }

    public void Hold(string slot, string? pack, string? piece)
    {
        if (inner != null) inner.Hold(slot, pack, piece); else holds.Add((slot, pack, piece));
    }

    void INpcView.Dispose()
    {
        // (made still on the worker: freed when it is done)
        if (job is { } j) { job = null; j.ContinueWith(t => { if (t.IsCompletedSuccessfully) t.Result.CallDeferred(Node.MethodName.QueueFree); }); }
        QueueFree();
    }
}
