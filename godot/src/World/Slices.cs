using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A long piece of main-thread work (a place built ahead of the journey to it)
/// done a few milliseconds a frame: its steps run until the frame's share is
/// spent. A step that yields a task is waited for (the frames go on meanwhile:
/// work on a worker thread); null is where a frame may end. A step started
/// runs to its end, so the steps are kept short (a piece, a light, a file).
/// The same steps run straight through where nothing waits (Run.All).
/// </summary>
public sealed class Slices
{
    readonly IEnumerator<object?> steps;
    Task? wait;
    public bool Done { get; private set; }
    /// <summary>The main thread's time spent on it, the longest share in one frame, and the frames it took.</summary>
    public double MainMs, MaxMs;
    public int Frames;
    /// <summary>The longest single step, and where it ended (the step's own name, if it yields one).</summary>
    public double LongestMs;
    public string Longest = "";
    string last = "start";

    public Slices(IEnumerable<object?> work) => steps = work.GetEnumerator();

    /// <summary>Steps until `budgetMs` of this frame are spent, or a task is
    /// waited for; true once all are done.</summary>
    public bool Step(double budgetMs)
    {
        if (Done) return true;
        long t0 = Stopwatch.GetTimestamp();
        Frames++;
        while (true)
        {
            if (wait != null)
            {
                if (!wait.IsCompleted) break;
                // (a worker's failure is the work's: thrown here, as it would have been in one go)
                wait.GetAwaiter().GetResult();
                wait = null;
            }
            long s0 = Stopwatch.GetTimestamp();
            if (!steps.MoveNext()) { Done = true; break; }
            double sms = Stopwatch.GetElapsedTime(s0).TotalMilliseconds;
            if (sms > LongestMs) { LongestMs = sms; Longest = steps.Current as string ?? Longest; }
            // (--perf: each step over a frame's share named, from the yield before it to its own)
            if (sms > 8 && Perf.On) GD.Print($"perf ahead step {sms:0.0} ms: {last} .. {steps.Current as string ?? steps.Current?.GetType().Name ?? "-"}");
            if (steps.Current is string label) last = label;
            if (steps.Current is Task t) wait = t;
            if (Stopwatch.GetElapsedTime(t0).TotalMilliseconds >= budgetMs) break;
        }
        double ms = Stopwatch.GetElapsedTime(t0).TotalMilliseconds;
        MainMs += ms;
        MaxMs = Math.Max(MaxMs, ms);
        return Done;
    }

    /// <summary>The rest at once (a worker's task waited for).</summary>
    public void Finish()
    {
        while (!Step(double.MaxValue)) wait?.Wait();
    }

    /// <summary>The main thread's frames so far (PumpAhead counts them), and the worker's share of each for work
    /// done on a worker thread (Paced): what it hands the renderer is drawn on the main thread at the frame's end,
    /// so a frame's worth at a time.</summary>
    public static long Frame;
    public static volatile float PacedMs = 4;

    /// <summary>Work in steps on a worker thread, paced by the main thread's frames: once a frame's share
    /// (PacedMs) is spent, the next step waits for the next frame.</summary>
    public static void Paced(IEnumerable<object?> work)
    {
        long f = System.Threading.Interlocked.Read(ref Frame);
        long t0 = Stopwatch.GetTimestamp();
        long s0 = t0;
        string last = "start";
        foreach (var s in work)
        {
            if (s is Task t) t.GetAwaiter().GetResult();
            double sms = Stopwatch.GetElapsedTime(s0).TotalMilliseconds;
            if (sms > 10 && Perf.On) GD.Print($"perf ahead worker step at {Perf.Now:0.000} {sms:0.0} ms: {last} .. {s as string ?? s?.GetType().Name ?? "-"}");
            if (s is string label) last = label;
            s0 = Stopwatch.GetTimestamp();
            if (Stopwatch.GetElapsedTime(t0).TotalMilliseconds < PacedMs) continue;
            while (System.Threading.Interlocked.Read(ref Frame) == f) System.Threading.Thread.Sleep(1);
            f = System.Threading.Interlocked.Read(ref Frame);
            t0 = s0 = Stopwatch.GetTimestamp();
        }
    }

    /// <summary>Work in steps done straight through.</summary>
    public static void All(IEnumerable<object?> work)
    {
        foreach (var s in work) if (s is Task t) t.GetAwaiter().GetResult();
    }
}
