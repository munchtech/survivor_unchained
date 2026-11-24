using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>The movement fixes' switches (Sim/MoveFlags) from the game's flags. No flag: the new movement, all fixes on, the
/// dash (the owner's pick, 23 November). --move-old: every fix off (the game as it was), then each alone may be put back:
/// --move-cam-lock, --move-start N, --move-stop N (steps of 1/60 s), --move-stop-hold, --move-dash-held, --move-dash-exit.
/// With --move-ab, F9 in play swaps all new for all old (the owner's A/B; the log says which); never in a tester's launcher.</summary>
public static class MoveSwitch
{
    static bool read, ab, wasDown, on;

    public static void FromArgs()
    {
        if (read) return;
        read = true;
        MoveFlags.Shipped();
        if (Args.Has("move-old")) MoveFlags.All(false);
        if (Args.Has("move-cam-lock")) MoveFlags.CamLock = true;
        if (Args.Has("move-start")) MoveFlags.StartFrames = (int)Args.Num("move-start", 2);
        if (Args.Has("move-stop")) MoveFlags.StopFrames = (int)Args.Num("move-stop", 2);
        if (Args.Has("move-stop-hold")) MoveFlags.StopHold = true;
        if (Args.Has("move-dash-held")) MoveFlags.DashHeld = true;
        if (Args.Has("move-dash-exit")) MoveFlags.DashExit = true;
        rollTime = Args.Has("move-roll") ? Args.Num("move-roll", 0.45f) : 0;
        rollLen = Args.Num("move-roll-len", 0f);
        MoveFlags.RollTime = rollTime; MoveFlags.RollLength = rollLen;
        ab = Args.Has("move-ab");
        on = MoveFlags.CamLock;
    }

    static double rollTime, rollLen;
    static bool rollWasDown;

    /// <summary>Once a frame (the camera's update), while --move-ab is given: F9 swaps all new and all old; F10 swaps the
    /// roll (--move-roll's seconds, or 0.45) and the old dash.</summary>
    public static void Poll()
    {
        if (!ab) return;
        bool down = Input.IsKeyPressed(Key.F9);
        if (down && !wasDown) { on = !on; MoveFlags.All(on); GD.Print($"MOVE AB: {(on ? "new" : "old")}"); }
        wasDown = down;
        bool roll = Input.IsKeyPressed(Key.F10);
        if (roll && !rollWasDown)
        {
            MoveFlags.RollTime = MoveFlags.RollTime > 0 ? 0 : rollTime > 0 ? rollTime : 0.45;
            GD.Print($"MOVE AB roll: {(MoveFlags.RollTime > 0 ? "on" : "off")}");
        }
        rollWasDown = roll;
    }
}
