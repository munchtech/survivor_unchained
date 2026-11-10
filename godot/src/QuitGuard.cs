using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;

namespace SurvivorUnchained;

/// <summary>(L1 lead 21 QUIT) The watchdog of the game's quit: a plain background thread (no Godot timer: the hang it
/// guards against is in Godot's native teardown, with the main loop gone) that ends the process hard when the process has
/// not ended by itself <see cref="Ms"/> after the tree was told to quit. The saves are flushed before it is armed
/// (<see cref="QuitPath"/>). It says one line as it fires (<c>quit guard: fired</c>), so a run can count it; the kill comes
/// whether or not the line could be said (the say runs on its own thread and is given <see cref="SayMs"/>).
/// Plain C#, no Godot type: godot/tests pins the logic. Never armed in a test host (<see cref="InTestHost"/>).</summary>
public sealed class QuitGuard
{
    /// <summary>The player's wait at a hung quit, from the tree's quit to the hard end.</summary>
    public const int Ms = 3000;
    /// <summary>How long the fired line may take before the kill comes anyway.</summary>
    public const int SayMs = 500;
    public const string FiredLine = "quit guard: fired";

    readonly int ms, sayMs;
    readonly Action say, kill;
    readonly ManualResetEventSlim called = new(false);
    int fired;

    public QuitGuard(int ms, Action say, Action kill, int sayMs = SayMs) { this.ms = ms; this.say = say; this.kill = kill; this.sayMs = sayMs; }

    /// <summary>Whether the guard ran out and went for the kill.</summary>
    public bool Fired => Volatile.Read(ref fired) != 0;

    /// <summary>Calls the guard off (nothing in the game does: a quit that ends takes the thread with it).</summary>
    public void Cancel() => called.Set();

    /// <summary>Starts the watch on a background thread (it never holds a process open).</summary>
    public Thread Start()
    {
        var t = new Thread(Watch) { IsBackground = true, Name = "quit guard" };
        t.Start();
        return t;
    }

    void Watch()
    {
        if (called.Wait(ms)) return;
        Volatile.Write(ref fired, 1);
        // The line on a thread of its own: a print that blocks (a lock held by the hung teardown) must not hold the kill.
        var s = new Thread(() => { try { say(); } catch { } }) { IsBackground = true, Name = "quit guard say" };
        s.Start();
        s.Join(sayMs);
        kill();
    }

    /// <summary>Whether this process is a test runner (dotnet test, an IDE's runner): the guard is never armed there.</summary>
    public static bool InTestHost { get; } = FindTestHost();

    static bool FindTestHost()
    {
        try
        {
            if (Process.GetCurrentProcess().ProcessName.Contains("testhost", StringComparison.OrdinalIgnoreCase)) return true;
            foreach (var a in AppDomain.CurrentDomain.GetAssemblies())
            {
                var n = a.GetName().Name ?? "";
                if (n.StartsWith("xunit", StringComparison.OrdinalIgnoreCase) || n.StartsWith("nunit", StringComparison.OrdinalIgnoreCase)
                    || n.StartsWith("Microsoft.TestPlatform", StringComparison.OrdinalIgnoreCase) || n.StartsWith("Microsoft.VisualStudio.TestPlatform", StringComparison.OrdinalIgnoreCase)
                    || n.Equals("testhost", StringComparison.OrdinalIgnoreCase)) return true;
            }
        }
        catch { }
        return false;
    }

    /// <summary>Arms the guard for THIS process: <paramref name="say"/> prints the fired line, then the process is ended
    /// hard with <paramref name="exitCode"/> (the code the quit asked for: a guarded quit is the player's clean exit; the
    /// line is what a run counts). Null, and nothing armed, in a test host.</summary>
    public static QuitGuard? ArmForProcess(Action say, int exitCode = 0, int ms = Ms)
    {
        if (InTestHost) return null;
        var g = new QuitGuard(ms, say, () => EndProcess(exitCode));
        g.Start();
        return g;
    }

    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr process, uint exitCode);

    /// <summary>The hard end: no exit handlers, no DLL detach, nothing that could wait on the hung teardown
    /// (Environment.Exit runs the runtime's shutdown and the C exit handlers, which can).</summary>
    static void EndProcess(int exitCode)
    {
        try { if (OperatingSystem.IsWindows()) TerminateProcess(GetCurrentProcess(), (uint)exitCode); } catch { }
        try { Process.GetCurrentProcess().Kill(); } catch { }
        Environment.Exit(exitCode);
    }
}
