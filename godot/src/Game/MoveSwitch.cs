using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>The movement fixes' switches (Sim/MoveFlags) from the game's flags: --move-new (all of them), or each alone:
/// --move-cam-lock, --move-start N, --move-stop N (steps of 1/60 s), --move-stop-hold, --move-dash-held, --move-dash-exit.
/// With --move-ab, F9 in play swaps all new for all old (the owner's A/B; the log says which). No flag: the game as it was.</summary>
public static class MoveSwitch
{
    static bool read, ab, wasDown, on;

    public static void FromArgs()
    {
        if (read) return;
        read = true;
        if (Args.Has("move-new")) MoveFlags.All(true);
        if (Args.Has("move-cam-lock")) MoveFlags.CamLock = true;
        if (Args.Has("move-start")) MoveFlags.StartFrames = (int)Args.Num("move-start", 2);
        if (Args.Has("move-stop")) MoveFlags.StopFrames = (int)Args.Num("move-stop", 2);
        if (Args.Has("move-stop-hold")) MoveFlags.StopHold = true;
        if (Args.Has("move-dash-held")) MoveFlags.DashHeld = true;
        if (Args.Has("move-dash-exit")) MoveFlags.DashExit = true;
        ab = Args.Has("move-ab");
        on = MoveFlags.CamLock;
    }

    /// <summary>Once a frame (the camera's update): F9 swaps new and old while --move-ab is given.</summary>
    public static void Poll()
    {
        if (!ab) return;
        bool down = Input.IsKeyPressed(Key.F9);
        if (down && !wasDown) { on = !on; MoveFlags.All(on); GD.Print($"MOVE AB: {(on ? "new" : "old")}"); }
        wasDown = down;
    }
}
