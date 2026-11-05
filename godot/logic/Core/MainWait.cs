using System;
using System.Threading;
using System.Threading.Tasks;

namespace SurvivorUnchained.Core;

/// <summary>
/// The main thread waiting on a worker (a person made ahead, the people-making lock) with the main thread's own queue
/// kept served while it waits. A worker making a person asks the rendering server for things (a mesh's arrays, for a
/// mask) and in Godot's default thread model that call waits for the main thread to flush the server's queue: a main
/// thread blocked in Task.Result or a plain lock on that worker never flushes it, and the game froze (C13's films, 5
/// Nov: the main thread in People.Build's lock, the cast-ahead worker in Mesh.SurfaceGetArrays). The pump is the
/// game's (RenderingServer.ForceSync, which in the default model flushes what other threads queued); off the main thread
/// it is not called (the waits are plain).
/// </summary>
public static class MainWait
{
    /// <summary>How long one wait runs before the pump is served again (ms).</summary>
    public const int SliceMs = 2;

    /// <summary>The task waited for, pump served between slices if on the main thread; true if done within
    /// <paramref name="timeoutMs"/> (-1: no limit). Its fault is not thrown (the caller reads the task).</summary>
    public static bool For(Task t, bool onMain, Action pump, int timeoutMs = -1)
    {
        if (!onMain) { try { return t.Wait(timeoutMs); } catch (AggregateException) { return true; } }
        long end = timeoutMs < 0 ? long.MaxValue : Environment.TickCount64 + timeoutMs;
        while (true)
        {
            try { if (t.Wait(SliceMs)) return true; } catch (AggregateException) { return true; }
            if (Environment.TickCount64 >= end) return false;
            pump();
        }
    }

    /// <summary>The lock taken, pump served between tries if on the main thread (Monitor.Exit releases it).</summary>
    public static void Enter(object gate, bool onMain, Action pump)
    {
        if (!onMain) { Monitor.Enter(gate); return; }
        while (!Monitor.TryEnter(gate, SliceMs)) pump();
    }
}
