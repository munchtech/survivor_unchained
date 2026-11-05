using System.Threading.Tasks;
using Godot;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.View;

/// <summary>The game's side of Core.MainWait: whether this is the main thread, and its pump (RenderingServer.ForceSync, bound to the server's sync(),
/// which in the default thread model flushes the calls other threads queued for it, so a worker making a person
/// on a worker is not left waiting on a main thread that waits on it).</summary>
public static class MainPump
{
    static readonly System.Action Serve = () => RenderingServer.ForceSync();
    static bool OnMain => OS.GetThreadCallerId() == OS.GetMainThreadId();

    /// <summary>The task waited for (served while waiting, on the main thread); true if done in time.</summary>
    public static bool Wait(Task t, int timeoutMs = -1) => MainWait.For(t, OnMain, Serve, timeoutMs);

    /// <summary>The lock taken (served while waiting, on the main thread); Monitor.Exit releases it.</summary>
    public static void Enter(object gate) => MainWait.Enter(gate, OnMain, Serve);
}
