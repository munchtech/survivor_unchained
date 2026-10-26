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

    /// <summary>Work in steps done straight through.</summary>
    public static void All(IEnumerable<object?> work)
    {
        foreach (var s in work) if (s is Task t) t.GetAwaiter().GetResult();
    }
}
