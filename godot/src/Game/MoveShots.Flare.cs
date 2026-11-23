using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>--moves12 f01 / f02: the Flare's facing (the owner, 22 Nov: "flare seems to face character direction instead of cursor").
/// Eight presses of the Long Cut, press i in the window that starts at 0.5 + 4 i s after S0, the cursor on bearing C = 45 i deg
/// (6 m from her), and f01 holding the keys of the travel bearing T = C + 135 (f02 holds none). Two dummy wolves 18 m out, one on C
/// and one on T: only the cleave's 24 m line reaches them (the sweep is 12 m), so hitC is "the cut went where the cursor was" and
/// hitT "where she was going". One line per press: FLAREFACE i cursor travel press line seam sweep body hitC hitT, all bearings in
/// the harness's convention (atan2(dx, dz) in degrees, 0 = +Z, 90 = +X), read by tools/motion/flare_facing.py.</summary>
public sealed partial class MoveShots
{
    const double FlareWin0 = 0.5, FlareWinLen = 4.0;
    const int FlarePresses = 8;
    const int FlareReadFrames = 3;
    /// <summary>The dummies' distance from her. 18 m (the brief's) is the ruler's clearing's rim (r 17.8 at boss-mid): a foe spawned there is gone
    /// within a step (measured 22 Nov), so 14 m: beyond the sweep's 12 m, inside the clearing, on the cleave's 24 m line.</summary>
    const double FoeAt = 14;

    sealed class FlarePress
    {
        public double Cursor = double.NaN, Travel = double.NaN, Press = double.NaN, Line = double.NaN, Seam = double.NaN, Sweep = double.NaN, Body = double.NaN;
        public double HitC, HitT;
        public bool Pressed, Cleaved, Swept, SeamRead, SweepRead;
        public long CleaveFrame, SweepFrame;
        public Enemy? WolfC, WolfT;
        public bool Metered, Spawned, Done;
        public readonly HashSet<string> Seen = new();
    }

    readonly FlarePress[] fl = Enumerable.Range(0, FlarePresses).Select(_ => new FlarePress()).ToArray();
    bool flareCleared;
    int flareWin = -1;   // the window the clock is in now (-1: none)

    static double Bearing(double dx, double dz) => (Deg(Math.Atan2(dx, dz)) % 360 + 360) % 360;
    /// <summary>An atan2(z, x) angle (the sim's and the view's) as a bearing in the harness's convention.</summary>
    static double BearingOfAngle(double a) => Bearing(Math.Cos(a), Math.Sin(a));
    static string Bd(double v) => double.IsNaN(v) ? "-" : F(v, "0.0");

    void FlareInit()
    {
        // The Flare's key as bound now (a saved preset may have moved it): the take injects that key's code, never a fixed Q.
        var code = controls.Bindings[Act.Flare].FirstOrDefault(c => c.StartsWith("Key") || c.StartsWith("Digit"));
        if (code == null) throw new InvalidOperationException("--moves12 f0x: Act.Flare has no keyboard binding");
        Key k = code.StartsWith("Key") ? Enum.Parse<Key>(code[3..]) : (Key)((int)Key.Key0 + (code[5] - '0'));
        KeyInfo["Q"] = (k, code);
        GD.Print($"MOVES12 flare key {code}");
    }

    static (int I, double U) FlareClock(double t)
    {
        double w = (t - FlareWin0) / FlareWinLen;
        if (w < 0 || w >= FlarePresses) return (-1, 0);
        int i = (int)Math.Floor(w);
        return (i, t - (FlareWin0 + FlareWinLen * i));
    }

    /// <summary>The cursor: her sim spot + 6 m along this window's bearing, through the camera (the screen point the real pointer ray reads).</summary>
    Vector2 FlareCursor(double t, WorldScene sc)
    {
        var b = getBattle(); var (i, _) = FlareClock(t);
        double c = Math.PI / 4 * Math.Max(i, 0);
        if (b == null) return new Vector2(960, 540);
        if (!flareCleared)
        {
            // --no-foes would release every foe every frame (Game.Tour), the dummies with them: the harness clears the den once instead
            // (the dungeon's packs released, nothing else spawns) and the dummies are the only foes.
            flareCleared = true;
            foreach (var e in b.Enemies.Living().ToList()) b.Enemies.Release(e);
            b.NoSpawn = true;
        }
        double wx = b.Player.X + 6 * Math.Sin(c), wz = b.Player.Z + 6 * Math.Cos(c);
        var cam = getCamera();
        var v = new Vector3((float)wx, (float)sc.HeightAt(wx, wz), (float)wz);
        return cam.IsPositionBehind(v) ? new Vector2(960, 540) : cam.UnprojectPosition(v);
    }

    /// <summary>Per frame in the take: the held keys of the travel bearing, the meter, the dummies, the tap of the Flare key, the window's end.</summary>
    void FlareStep(Battle b, double t, HashSet<string> want)
    {
        var (i, u) = FlareClock(t);
        if (i != flareWin)
        {
            if (flareWin >= 0) FlareClose(b, flareWin);
            flareWin = i;
        }
        if (i < 0) return;
        var f = fl[i];
        if (name == "f01" && u < 1.4)
        {
            double tr = Math.PI / 4 * i + 3 * Math.PI / 4, dx = Math.Sin(tr), dz = Math.Cos(tr);
            if (dx > 0.3) want.Add("D"); else if (dx < -0.3) want.Add("A");
            if (dz > 0.3) want.Add("S"); else if (dz < -0.3) want.Add("W");
        }
        if (u >= 0.2 && !f.Metered) { f.Metered = true; b.FlareMeter = Math.Max(b.FlareMeter, Battle.FlareFull); }
        if (u >= 0.4 && !f.Spawned)
        {
            f.Spawned = true;
            double c = Math.PI / 4 * i, tr = c + 3 * Math.PI / 4;
            f.WolfC = FlareDummy(b, b.Player.X + FoeAt * Math.Sin(c), b.Player.Z + FoeAt * Math.Cos(c));
            f.WolfT = FlareDummy(b, b.Player.X + FoeAt * Math.Sin(tr), b.Player.Z + FoeAt * Math.Cos(tr));
        }
        foreach (var (nm, e) in new[] { ("C", f.WolfC), ("T", f.WolfT) })
            if (e != null && !f.Seen.Contains(nm) && (!e.Alive || e.State != EnemyState.Active)) { f.Seen.Add(nm); GD.Print($"FLAREDUMMY i={i} {nm} u {u:0.00} alive {e.Alive} state {e.State} at ({e.X:0.0}, {e.Z:0.0}) hp {e.Hp:0}"); }
        if (u >= 0.7 && u < 0.78) want.Add("Q");
        if (u >= 3.6) FlareClose(b, i);
    }

    Enemy? FlareDummy(Battle b, double x, double z)
    {
        bool was = b.NoSpawn;
        b.NoSpawn = false;
        var e = b.SpawnEnemy("wolf", x, z);
        b.NoSpawn = was;
        if (e == null) { GD.Print($"MOVES12 ERROR: the dummy wolf did not spawn at ({x:0.0}, {z:0.0})"); return null; }
        GD.Print($"FLAREDUMMY spawned id {e.Id} alive {e.Alive} state {e.State} time {b.Time:0.000} frame {Engine.GetFramesDrawn()}");
        e.Speed = 0; e.AttackT = e.RangedT = 99; e.MaxHp = 1e6; e.Hp = 1e6; e.Provoked = true; e.Wake = 0; e.Roused = true; e.Elite = true;
        return e;
    }

    /// <summary>The window's end: each dummy's hp lost, the dummies taken out of the fight, the line logged.</summary>
    void FlareClose(Battle b, int i)
    {
        var f = fl[i];
        if (f.Done) return;
        f.Done = true;
        foreach (var (nm, e) in new[] { ("C", f.WolfC), ("T", f.WolfT) })
            if (e != null) GD.Print($"FLAREDUMMY i={i} {nm} at ({e.X:0.0}, {e.Z:0.0}) from her ({b.Player.X:0.0}, {b.Player.Z:0.0}) hp {e.Hp:0} alive {e.Alive} state {e.State}");
        f.HitC = f.WolfC != null ? 1e6 - f.WolfC.Hp : -1;
        f.HitT = f.WolfT != null ? 1e6 - f.WolfT.Hp : -1;
        foreach (var e in new[] { f.WolfC, f.WolfT }) if (e != null && e.Alive) b.Enemies.Release(e);
        GD.Print($"FLAREFACE i={i} cursor={Bd(f.Cursor)} travel={Bd(f.Travel)} press={Bd(f.Press)} line={Bd(f.Line)} seam={Bd(f.Seam)} sweep={Bd(f.Sweep)} body={Bd(f.Body)} hitC={F(f.HitC, "0")} hitT={F(f.HitT, "0")}");
    }

    void FlareTick(Battle b, double mx, double mz, List<CombatEvent> evs)
    {
        var (i, _) = FlareClock(tNow);
        if (i < 0 || !started) return;
        var f = fl[i];
        foreach (var e in evs)
        {
            if (e is not Ev.Flare fe) continue;
            if (fe.Phase == FlarePhase.Press && !f.Pressed)
            {
                f.Pressed = true;
                var p = b.Player;
                if (getScene()?.Pointer() is { } q) f.Cursor = Bearing(q.X - p.X, q.Z - p.Z);
                f.Travel = Math.Abs(mx) + Math.Abs(mz) > 1e-6 ? Bearing(mx, mz) : double.NaN;
                f.Press = BearingOfAngle(fe.Angle);
            }
            else if (fe.Phase == FlarePhase.Blow && fe.Part == "cleave" && !f.Cleaved)
            {
                f.Cleaved = true; f.CleaveFrame = (long)Engine.GetFramesDrawn();
                f.Line = Bearing(fe.TX - fe.X, fe.TZ - fe.Z);
            }
            else if (fe.Phase == FlarePhase.Blow && fe.Part == "sweep" && !f.Swept)
            {
                f.Swept = true; f.SweepFrame = (long)Engine.GetFramesDrawn();
            }
        }
    }

    FlareFx? flareFx;
    static readonly System.Reflection.BindingFlags Priv = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
    static T? Field<T>(object o, string n) => (T?)o.GetType().GetField(n, Priv)?.GetValue(o);

    static FlareFx? FindFx(Node n)
    {
        if (n is FlareFx fx) return fx;
        foreach (var c in n.GetChildren()) if (FindFx(c) is { } r) return r;
        return null;
    }

    /// <summary>The seam's and the sweep's angles as the view holds them (FlareFx.lcDir / lcLen / lcCleaveT / lcSweepT / lcSweepFrom, the values it publishes
    /// as the shader globals flare_seam.Z and flare_sweep.W): RenderingServer.GlobalShaderParameterGet returns nothing outside the editor.</summary>
    void FlareDraw(WorldScene sc)
    {
        long now = (long)Engine.GetFramesDrawn();
        if (flareFx == null || !GodotObject.IsInstanceValid(flareFx)) flareFx = FindFx(GetTree().Root);
        if (flareFx == null) return;
        foreach (var f in fl)
        {
            // (the view drains the sim's events after the press's stop: read at the first drawn frame, no sooner than FlareReadFrames after the event,
            // where the view holds the cleave (cleave time >= 0, a line) or the sweep (sweep time >= 0))
            if (f.Cleaved && !f.SeamRead && now >= f.CleaveFrame + FlareReadFrames && Field<double>(flareFx, "lcCleaveT") >= 0 && Field<float>(flareFx, "lcLen") > 0)
            {
                f.SeamRead = true;
                var d = Field<Vector2>(flareFx, "lcDir");
                f.Seam = BearingOfAngle(Mathf.Atan2(d.Y, d.X));
                f.Body = (Mathf.RadToDeg(sc.Player.Rotation.Y) % 360 + 360) % 360;
            }
            if (f.Swept && !f.SweepRead && now >= f.SweepFrame + FlareReadFrames && Field<double>(flareFx, "lcSweepT") >= 0)
            {
                f.SweepRead = true;
                f.Sweep = BearingOfAngle(Field<float>(flareFx, "lcSweepFrom") - 0.4);
            }
        }
    }
}
