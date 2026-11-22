using System.Linq;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>--moves12 TAKE: the movement baseline's measuring harness (dev only, never in play). One scripted take per process:
/// her inputs go in through the real input code (Controls._Input for keys, buttons; Controls.ScriptStick/ScriptLook through the
/// real deadzones for a pad; MoveShots.Mouse as the mouse the pointer ray reads), and two logs (ticks.csv one row per sim step,
/// frames.csv one row per drawn frame) and an on-screen overlay (keys, sticks, cursor, take name, clock) are written for the movie.
/// Flags: --moves12-input kbm|pad (default kbm), --moves12-at T (S0 = the first frame with fight time >= T, default 4),
/// --moves12-out DIR (default res://.shots/move_baseline/TAKE). Angles: atan2(dx, dz) in degrees, 0 = +Z (toward the camera),
/// 90 = +X (screen right): the code's own convention (PlayerState.Facing is the same angle in radians). Times are seconds after S0.
/// With the flag off nothing here exists: the hooks are null statics.</summary>
public sealed partial class MoveShots : Node
{
    /// <summary>The scripted mouse (screen px); null = the real one. Read by Game.PointerGround.</summary>
    public static Vector2? Mouse;
    /// <summary>Called by WorldScene.Update after every sim step (battle, move x, move z asked, the step's events).</summary>
    public static Action<Battle, double, double, List<CombatEvent>>? OnTick;
    /// <summary>Called by WorldScene.Draw after the camera moved (frame dt, fight dt, drawn x, drawn z).</summary>
    public static Action<double, double, double, double>? OnDraw;

    /* ------------------------------------------------------------------ the takes (times in s after S0) -- */

    sealed record Btn(string K, double A, double B);
    sealed record Pt(double T, float X, float Y);
    sealed record Sweep(double T, double Dur, Vector2 To);
    sealed class Take
    {
        public string Title = "";
        public double End;
        public bool Pad;
        /// <summary>A fixed cursor pixel, or a world point (metres from her S0 spot, x then z) re-projected every frame.</summary>
        public Vector2? Screen, World;
        public Sweep[] Sweeps = [];
        /// <summary>Held keys and buttons: W A S D SPACE LMB LB.</summary>
        public Btn[] Btns = [];
        /// <summary>Pad sticks: keypoints, linear between, zero before the first.</summary>
        public Pt[] Stick = [], Look = [];
        /// <summary>s07: the keyboard circle round the world cursor, radius 5, counter-clockwise, for 6 s.</summary>
        public bool Circle;
        /// <summary>s12: a dummy wolf at her S0 spot + (5, -0.3), spawned 1.5 s before S0.</summary>
        public bool Wolf;
        /// <summary>s12d: the cursor follows the nearest living foe (its drawn spot, re-projected every frame).</summary>
        public bool Follow;
    }

    static Btn B(string k, double a, double b) => new(k, a, b);
    const float R3 = 3 / 60f, R2 = 2 / 60f, R4 = 4 / 60f;   // pad ramps: up over 3 frames, down over 2
    static Pt[] Ramp(double a, double b, float x, float y) => [new(a, 0, 0), new(a + R3, x, y), new(b, x, y), new(b + R2, 0, 0)];

    /// <summary>LMB taps every 0.45 s from 0.3 s to `to` (0.08 s each).</summary>
    static Btn[] Taps(double to) { var l = new List<Btn>(); for (double t = 0.3; t < to; t += 0.45) l.Add(B("LMB", t, t + 0.08)); return l.ToArray(); }

    static readonly Dictionary<string, Take> Takes = new()
    {
        ["s01"] = new() { Title = "1+2 START / STOP", End = 5.0, Screen = new(1280, 540), Btns = [B("D", 0, 2.0)] },
        ["s03"] = new() { Title = "3 REVERSAL", End = 5.0, Screen = new(1280, 540), Sweeps = [new(1.5, 0.1, new(640, 540))], Btns = [B("D", 0, 1.5), B("A", 1.5, 3.0)] },
        ["s04"] = new() { Title = "4 QUARTER TURN", End = 5.0, Screen = new(1280, 540), Sweeps = [new(1.5, 0.1, new(960, 300))], Btns = [B("D", 0, 1.5), B("W", 1.5, 3.0)] },
        ["s05"] = new() { Title = "5 STRAFE (aim fixed)", End = 4.5, World = new(0, -9), Btns = [B("D", 0, 1.5), B("A", 1.5, 3.0)] },
        ["s06"] = new() { Title = "6 BACKPEDAL", End = 3.5, World = new(0, -5), Btns = [B("S", 0, 1.5)] },
        ["s07"] = new() { Title = "7 CIRCLE THE AIM", End = 7.5, World = new(0, -5), Circle = true },
        ["s08"] = new() { Title = "8 DASH FROM REST", End = 3.0, Screen = new(1300, 360), Btns = [B("SPACE", 0.5, 0.6)] },
        ["s09"] = new() { Title = "9 DASH AT A RUN", End = 5.0, Screen = new(1280, 540), Btns = [B("D", 0, 3.5), B("SPACE", 1.5, 1.6)] },
        ["s10a"] = new() { Title = "10 DASH ACROSS THE AIM", End = 4.5, Screen = new(960, 300), Btns = [B("D", 0, 3.0), B("SPACE", 1.5, 1.6)] },
        ["s10b"] = new() { Title = "10 DASH AGAINST THE AIM", End = 4.5, Screen = new(640, 540), Btns = [B("D", 0, 3.0), B("SPACE", 1.5, 1.6)] },
        ["s10c"] = new() { Title = "10 DASH, TWO KEYS HELD", End = 4.5, Screen = new(960, 800), Btns = [B("W", 0, 3.0), B("D", 0, 3.0), B("SPACE", 1.5, 1.6)] },
        ["s10d"] = new() { Title = "10 DASH, NOTHING HELD, CURSOR DOWN-LEFT", End = 3.0, Screen = new(500, 700), Btns = [B("SPACE", 0.5, 0.6)] },
        ["s10e"] = new() { Title = "10 DASH, S HELD, CURSOR RIGHT", End = 4.5, Screen = new(1280, 540), Btns = [B("S", 0, 3.0), B("SPACE", 1.5, 1.6)] },
        ["s11"] = new() { Title = "11 STRIKE WHILE MOVING", End = 5.0, Screen = new(1280, 540), Btns = [B("D", 0, 3.5), B("LMB", 1.5, 1.58)] },
        ["s12"] = new() { Title = "12 HEAVY HIT WHILE MOVING", End = 4.0, World = new(5.0f, -0.3f), Wolf = true,
            Btns = [B("D", 0, 2.5), B("LMB", 0.75, 0.83), B("LMB", 1.2, 1.28), B("LMB", 1.65, 1.73)] },
        // s12d: shot 12 in a den room with a real pack (foes on): the mouse tracks the nearest foe, she runs at the pack, tapping LMB.
        ["s12d"] = new() { Title = "12 HEAVY HIT WHILE MOVING (den pack)", End = 6.0, Follow = true,
            Btns = [B("W", 0, 5.5), .. Taps(5.2)] },
        ["s13"] = new() { Title = "13 STILL MOUSE", End = 5.5, Screen = new(1100, 560), Btns = [B("D", 0, 1.5), B("A", 1.5, 3.0), B("W", 3.0, 4.0)] },
        ["p01"] = new() { Title = "PAD 1+2 START / STOP", End = 5.0, Pad = true, Stick = Ramp(0, 2.0, 1, 0) },
        ["p03"] = new() { Title = "PAD 3 REVERSAL", End = 5.0, Pad = true,
            Stick = [new(0, 0, 0), new(R3, 1, 0), new(1.5, 1, 0), new(1.5 + R4, -1, 0), new(3.0, -1, 0), new(3.0 + R2, 0, 0)] },
        ["p08"] = new() { Title = "PAD 8 DASH FROM REST", End = 3.0, Pad = true, Stick = Ramp(0.5, 0.8, 0.707f, -0.707f), Btns = [B("LB", 0.55, 0.65)] },
        ["p08b"] = new() { Title = "PAD 8 DASH, STICK AT REST", End = 3.0, Pad = true, Look = Ramp(0, 2.0, 0, -1), Btns = [B("LB", 1.0, 1.1)] },
        ["p10a"] = new() { Title = "PAD 10 DASH ACROSS THE AIM", End = 4.5, Pad = true, Stick = Ramp(0, 3.0, 1, 0), Look = Ramp(1.0, 3.0, 0, -1), Btns = [B("LB", 1.5, 1.6)] },
        ["p10b"] = new() { Title = "PAD 10 DASH AGAINST THE AIM", End = 4.5, Pad = true, Stick = Ramp(0, 3.0, 1, 0), Look = Ramp(1.0, 3.0, -1, 0), Btns = [B("LB", 1.5, 1.6)] },
    };

    static readonly Dictionary<string, (Key Key, string Code)> KeyInfo = new()
    {
        ["W"] = (Key.W, "KeyW"), ["A"] = (Key.A, "KeyA"), ["S"] = (Key.S, "KeyS"), ["D"] = (Key.D, "KeyD"), ["SPACE"] = (Key.Space, "Space"),    };

    /* ------------------------------------------------------------------------------------------- state -- */

    readonly Func<Battle?> getBattle;
    readonly Func<WorldScene?> getScene;
    readonly Func<Camera3D> getCamera;
    readonly Func<FollowCamera> getCam;
    readonly Controls controls;
    readonly Take take;
    readonly string name, outDir;
    readonly bool pad;
    readonly double at;
    bool started, ended, flushed, wolfDone, wolfGone, foes2, foes0; Enemy? wolfE;
    double t0, tNow, quitAt;
    (double X, double Z) anchor;
    readonly HashSet<string> held = new();
    bool stickOn;
    int tick, stepsThisFrame;
    readonly List<(double Tf, string[] C)> tickRows = new(), frameRows = new();
    Overlay? overlay;
    Vector2 lastFoePx = new(960, 540);

    const string TickHead = "tick,frame,t_fight,t_shot,x,z,vx,vz,speed,mx,mz,sim_facing_deg,dashT,dash_dx,dash_dz,castT,iframes,ptr_x,ptr_z,ev";
    const string FrameHead = "frame,dt,t_fight,t_shot,steps,x,z,dx,dz,face_deg,aim_deg,ptr_x,ptr_z,look_x,look_y,look_z,campos_x,campos_y,campos_z,her_px_x,her_px_y,her_rate,her_held,anim,keys,lmb,mouse_x,mouse_y,stick_x,stick_y,slook_x,slook_y,using_pad,interp_on,cam_pitch_deg,cam_dist,fov";

    public MoveShots(Func<Battle?> battle, Func<WorldScene?> scene, Func<Camera3D> camera, Func<FollowCamera> cam, Controls controls)
    {
        getBattle = battle; getScene = scene; getCamera = camera; getCam = cam; this.controls = controls;
        ProcessPriority = -200;   // before Controls (-100): this frame's input is in before Controls.Poll reads it
        name = Args.Get("moves12") ?? "";
        if (!Takes.TryGetValue(name, out take!)) throw new ArgumentException("--moves12: no take '" + name + "' (" + string.Join(" ", Takes.Keys) + ")");
        pad = Args.Get("moves12-input") == "pad";
        if (pad != take.Pad) GD.Print($"MOVES12 warning: take {name} is a {(take.Pad ? "pad" : "kbm")} take, run as {(pad ? "pad" : "kbm")}");
        at = Args.Has("moves12-at") ? Args.Num("moves12-at", 4) : 4;
        outDir = Args.Get("moves12-out") ?? "res://.shots/move_baseline/" + name;
        outDir = ProjectSettings.GlobalizePath(outDir);
        OnTick = Tick;
        OnDraw = Draw;
    }

    public override void _Ready()
    {
        overlay = new Overlay(this);
        var layer = new CanvasLayer { Layer = 120 };
        layer.AddChild(overlay);
        AddChild(layer);
    }

    public override void _ExitTree()
    {
        Flush();
        OnTick = null; OnDraw = null; Mouse = null; Controls.ScriptStick = null; Controls.ScriptLook = null;
    }

    static string F(double v, string f = "0.0000") => v.ToString(f, CultureInfo.InvariantCulture);
    static double Deg(double rad) => rad * 180 / Math.PI;

    /* ---------------------------------------------------------------------------------------- the take -- */

    public override void _Process(double delta)
    {
        if (getBattle() is not { } b || getScene() is not { } sc || sc.Player == null) return;
        if (ended)
        {
            if (b.Time - t0 >= quitAt) { Flush(); GetTree().Quit(); }
            return;
        }
        if (take.Wolf && !wolfDone && b.Time >= at - 0.05)
        {
            wolfDone = true;
            bool was = b.NoSpawn;
            b.NoSpawn = false;
            var e = b.SpawnEnemy("wolf", b.Player.X + 5.0, b.Player.Z - 0.3);
            b.NoSpawn = was;
            if (e == null) GD.Print("MOVES12 ERROR: the dummy wolf did not spawn");
            else { wolfE = e; e.Speed = 0; e.AttackT = e.RangedT = 99; e.MaxHp = 1e6; e.Hp = 1e6; e.Provoked = true; e.Wake = 0; e.Roused = true; e.Elite = true; GD.Print($"MOVES12 dummy wolf at ({e.X:0.00}, {e.Z:0.00})"); }
        }
        if (!started)
        {
            if (pad) controls.UsingPad = true;
            if (b.Time >= at)
            {
                started = true;
                t0 = b.Time;
                anchor = (b.Player.X, b.Player.Z);
                // s12d only: every landing strike crits (a stat buff through the sim's own route), so her heavy-hit stops can be sampled
                if (name == "s12d") { b.AddBuff("moves12_crit", Stat.CritChance, 5.0, ModKind.Flat, take.End + 1, 1); GD.Print("MOVES12 crits forced: moves12_crit +500% critChance"); }
                GD.Print($"MOVES12 S0 frame {Engine.GetFramesDrawn()} t {b.Time:0.000} at ({anchor.X:0.000}, {anchor.Z:0.000})");
            }
            else anchor = (b.Player.X, b.Player.Z);
        }
        double t = started ? b.Time - t0 : b.Time - at;   // before S0 the clock is negative (she stands still)
        tNow = t;
        if (Args.Has("moves12-foes"))
        {
            if (!foes2 && t >= -2) { foes2 = true; LogFoes(b, "S0-2s"); }
            if (!foes0 && started) { foes0 = true; LogFoes(b, "S0"); }
        }
        if (!pad) Mouse = CursorAt(t, sc);
        if (!started) return;

        // the pad's sticks, through the real deadzones in Controls.Poll
        if (take.Stick.Length > 0 || take.Look.Length > 0)
        {
            var st = Eval(take.Stick, t); var lk = Eval(take.Look, t);
            Controls.ScriptStick = st; Controls.ScriptLook = lk;
            bool on = st.Length() > 0.0001f;
            if (on != stickOn) { stickOn = on; GD.Print($"MOVES12 in {t:0.000} frame {Engine.GetFramesDrawn()} {(on ? "stick on " + st : "stick off")}"); }
        }

        // keys and buttons
        var want = new HashSet<string>();
        if (take.Circle) { if (t < 6.0) CircleKeys(b, want); }
        else foreach (var btn in take.Btns) if (t >= btn.A && t < btn.B) want.Add(btn.K);
        foreach (var k in new List<string>(held)) if (!want.Contains(k)) Set(k, false, t);
        foreach (var k in want) if (!held.Contains(k)) Set(k, true, t);
        // a held key that Controls dropped (focus-out clears them) is pressed again
        foreach (var k in held)
            if (KeyInfo.TryGetValue(k, out var ki) && !controls.IsDown(ki.Code))
            {
                GD.Print($"MOVES12 refocus key {k} frame {Engine.GetFramesDrawn()}");
                controls._Input(new InputEventKey { PhysicalKeycode = ki.Key, Keycode = ki.Key, Pressed = true });
            }

        if (t >= take.End)
        {
            ended = true;
            quitAt = take.End + 0.2;
            foreach (var k in new List<string>(held)) Set(k, false, t);
            Controls.ScriptStick = null; Controls.ScriptLook = null;
            GD.Print($"MOVES12 END frame {Engine.GetFramesDrawn()} t {b.Time:0.000}");
        }
    }

    void Set(string k, bool on, double t)
    {
        if (on) held.Add(k); else held.Remove(k);
        if (KeyInfo.TryGetValue(k, out var ki))
            controls._Input(new InputEventKey { PhysicalKeycode = ki.Key, Keycode = ki.Key, Pressed = on });
        else if (k == "LMB")
            controls._Input(new InputEventMouseButton { ButtonIndex = MouseButton.Left, Pressed = on, Position = Mouse ?? new Vector2(960, 540) });
        else if (k == "LB")
            controls._Input(new InputEventJoypadButton { ButtonIndex = JoyButton.LeftShoulder, Pressed = on });
        GD.Print($"MOVES12 in {t:0.000} frame {Engine.GetFramesDrawn()} {k} {(on ? "down" : "up")}");
    }

    /// <summary>The keyboard circle (s07): the tangent round C (counter-clockwise on the screen) plus half the radius error toward C,
    /// pushed to the nearest of the eight key directions.</summary>
    void CircleKeys(Battle b, HashSet<string> want)
    {
        double cx = anchor.X + take.World!.Value.X, cz = anchor.Z + take.World.Value.Y;
        double rx = b.Player.X - cx, rz = b.Player.Z - cz, d = Math.Sqrt(rx * rx + rz * rz);
        if (d < 1e-3) { rx = 0; rz = 1; d = 1; }
        double tx = rz / d, tz = -rx / d;
        double k = 0.5 * (d - 5);
        double dx = tx - k * rx / d, dz = tz - k * rz / d;
        int oct = (int)Math.Round(Math.Atan2(dz, dx) / (Math.PI / 4));
        int kx = (int)Math.Round(Math.Cos(oct * Math.PI / 4)), kz = (int)Math.Round(Math.Sin(oct * Math.PI / 4));
        if (kx > 0) want.Add("D"); else if (kx < 0) want.Add("A");
        if (kz < 0) want.Add("W"); else if (kz > 0) want.Add("S");
    }

    void LogFoes(Battle b, string when)
    {
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            double d = Math.Sqrt((e.X - b.Player.X) * (e.X - b.Player.X) + (e.Z - b.Player.Z) * (e.Z - b.Player.Z));
            GD.Print($"MOVES12 FOE {when} def={e.Def.Id} x={F(e.X, "0.00")} z={F(e.Z, "0.00")} elite={e.Elite} boss={e.Boss} dist={F(d, "0.00")}");
        }
    }

    /// <summary>The nearest living foe's drawn spot on the screen (null: none).</summary>
    Vector2? FoePixel(WorldScene sc)
    {
        var b = getBattle(); if (b == null) return null;
        Enemy? best = null; double bd = double.MaxValue;
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            double d = (e.X - b.Player.X) * (e.X - b.Player.X) + (e.Z - b.Player.Z) * (e.Z - b.Player.Z);
            if (d < bd) { bd = d; best = e; }
        }
        if (best == null) return null;
        var (ex, ez) = sc.Drawn.Of(best);
        var cam = getCamera();
        var v = new Vector3((float)ex, (float)sc.HeightAt(ex, ez), (float)ez);
        return cam.IsPositionBehind(v) ? null : cam.UnprojectPosition(v);
    }

    Vector2 CursorAt(double t, WorldScene sc)
    {
        Vector2 pos;
        if (take.Follow) pos = FoePixel(sc) ?? lastFoePx;
        else if (take.World is { } w)
        {
            double wx = anchor.X + w.X, wz = anchor.Z + w.Y;
            var cam = getCamera();
            var v = new Vector3((float)wx, (float)sc.HeightAt(wx, wz), (float)wz);
            pos = cam.IsPositionBehind(v) ? new Vector2(960, 540) : cam.UnprojectPosition(v);
        }
        else pos = take.Screen ?? new Vector2(960, 540);
        if (take.Follow) lastFoePx = pos;
        foreach (var s in take.Sweeps)
        {
            if (t <= s.T) break;
            float k = (float)Math.Clamp((t - s.T) / s.Dur, 0, 1);
            if (k < 1) { pos = pos.Lerp(s.To, k); break; }
            pos = s.To;
        }
        return pos;
    }

    static Vector2 Eval(Pt[] pts, double t)
    {
        if (pts.Length == 0 || t <= pts[0].T) return Vector2.Zero;
        for (int i = 1; i < pts.Length; i++)
            if (t < pts[i].T)
            {
                var a = pts[i - 1]; var c = pts[i];
                float k = (float)((t - a.T) / (c.T - a.T));
                return new Vector2(a.X, a.Y).Lerp(new Vector2(c.X, c.Y), k);
            }
        return new Vector2(pts[^1].X, pts[^1].Y);
    }

    /* ------------------------------------------------------------------------------------------- logs -- */

    void Tick(Battle b, double mx, double mz, List<CombatEvent> evs)
    {
        tick++; stepsThisFrame++;
        var p = b.Player;
        var ptr = getScene()?.Pointer();
        var sb = new StringBuilder();
        foreach (var e in evs)
        {
            if (sb.Length > 0) sb.Append('|');
            sb.Append(e.GetType().Name);
            if (e is Ev.Hit h && LeadRule.Heavy(h)) sb.Append(":heavy");
            if (e is Ev.Slash sl) sb.Append(":struck" + sl.Struck + ":reach" + sl.Reach.ToString("0.00", CultureInfo.InvariantCulture) + ":wolf" + string.Join("", b.Enemies.Items.Where(en => en.MaxHp > 1e5).Select(en => en.Hp.ToString("0") + "_" + en.Alive + en.State + en.Disposition + en.Provoked + en.Wake + en.Roused + b.LampHush)));
        }
        if (wolfE != null && !wolfGone && !wolfE.Alive) { wolfGone = true; if (sb.Length > 0) sb.Append('|'); sb.Append("WOLFGONE:hp" + wolfE.Hp.ToString("0") + ":" + wolfE.State); }
        tickRows.Add((b.Time, [tick.ToString(CultureInfo.InvariantCulture), Engine.GetFramesDrawn().ToString(CultureInfo.InvariantCulture), F(b.Time), "",
            F(p.X), F(p.Z), F(p.Vx), F(p.Vz), F(Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz)), F(mx), F(mz), F(Deg(p.Facing), "0.00"),
            F(p.DashT), F(p.DashDX, "0.000"), F(p.DashDZ, "0.000"), F(p.CastT), F(p.Iframes),
            ptr is { } q ? F(q.X) : "", ptr is { } q2 ? F(q2.Z) : "", sb.ToString()]));
    }

    void Draw(double dt, double fightDt, double hx, double hz)
    {
        var sc = getScene(); var b = getBattle();
        if (sc == null || b == null) return;
        var p = b.Player;
        var cam = getCam(); var camera = getCamera();
        var ptr = sc.Pointer();
        double face = sc.Player != null ? Mathf.RadToDeg(sc.Player.Rotation.Y) : 0;
        string aim = ptr is { } q ? F(Deg(Math.Atan2(q.X - hx, q.Z - hz)), "0.00") : "";
        var her = sc.HerDrawn;
        var px = camera.IsPositionBehind(her + new Vector3(0, 1.1f, 0)) ? Vector2.Zero : camera.UnprojectPosition(her + new Vector3(0, 1.1f, 0));
        var look = cam.LookAt; var cp = camera.GlobalPosition;
        string keys = "";
        foreach (var k in new[] { "W", "A", "S", "D" }) if (controls.IsDown(KeyInfo[k].Code)) keys += k;
        if (controls.IsDown("Space")) keys += (keys.Length > 0 ? "+" : "") + "SPACE";
        var ms = Mouse ?? Vector2.Zero; var ss = Controls.ScriptStick ?? Vector2.Zero; var sl = Controls.ScriptLook ?? Vector2.Zero;
        frameRows.Add((b.Time, [Engine.GetFramesDrawn().ToString(CultureInfo.InvariantCulture), F(dt, "0.00000"), F(b.Time), "", stepsThisFrame.ToString(CultureInfo.InvariantCulture),
            F(p.X), F(p.Z), F(hx), F(hz), F(face, "0.00"), aim, ptr is { } q3 ? F(q3.X) : "", ptr is { } q4 ? F(q4.Z) : "",
            F(look.X), F(look.Y), F(look.Z), F(cp.X), F(cp.Y), F(cp.Z), F(px.X, "0.0"), F(px.Y, "0.0"),
            F(sc.Stops.Rate(SurvivorUnchained.Look.HitStops.Her), "0.000"), sc.Stops.Held(SurvivorUnchained.Look.HitStops.Her) ? "1" : "0", "",
            keys, controls.IsDown("Mouse0") ? "1" : "0", Mouse is null ? "" : F(ms.X, "0.0"), Mouse is null ? "" : F(ms.Y, "0.0"),
            F(ss.X, "0.000"), F(ss.Y, "0.000"), F(sl.X, "0.000"), F(sl.Y, "0.000"), controls.UsingPad ? "1" : "0", SurvivorUnchained.View.Interp.On ? "1" : "0",
            F(Mathf.RadToDeg(cam.Pitch), "0.00"), F(cam.Distance, "0.00"), F(camera.Fov, "0.0")]));
        stepsThisFrame = 0;
    }

    void Flush()
    {
        if (flushed) return;
        flushed = true;
        if (!started) { GD.Print("MOVES12 never reached S0; nothing written"); return; }
        Directory.CreateDirectory(outDir);
        Write("ticks.csv", TickHead, tickRows);
        Write("frames.csv", FrameHead, frameRows);
        GD.Print($"MOVES12 wrote {outDir}: {tickRows.Count} ticks, {frameRows.Count} frames (all from the take's start; rows before S0-1 s are dropped)");
    }

    void Write(string file, string head, List<(double Tf, string[] C)> rows)
    {
        var sb = new StringBuilder(head).Append('\n');
        foreach (var (tf, c) in rows)
        {
            double ts = tf - t0;
            if (ts < -1.0) continue;
            c[3] = F(ts);
            sb.Append(string.Join(",", c)).Append('\n');
        }
        File.WriteAllText(Path.Combine(outDir, file), sb.ToString(), new UTF8Encoding(false));
    }

    /* ----------------------------------------------------------------------------------------- overlay -- */

    sealed partial class Overlay : Control
    {
        readonly MoveShots m;
        public Overlay(MoveShots owner)
        {
            m = owner;
            MouseFilter = MouseFilterEnum.Ignore;
            SetAnchorsPreset(LayoutPreset.FullRect);
        }

        public override void _Process(double delta) => QueueRedraw();

        void Cap(string label, Vector2 pos, Vector2 size, bool lit)
        {
            DrawRect(new Rect2(pos, size), lit ? new Color(1f, 0.85f, 0.2f, 0.95f) : new Color(0, 0, 0, 0.55f));
            DrawRect(new Rect2(pos, size), Colors.White, false, 3);
            var f = ThemeDB.FallbackFont;
            var ts = f.GetStringSize(label, HorizontalAlignment.Left, -1, 28);
            DrawString(f, pos + new Vector2((size.X - ts.X) / 2, (size.Y + ts.Y * 0.62f) / 2), label, HorizontalAlignment.Left, -1, 28, lit ? Colors.Black : Colors.White);
        }

        void Stick(Vector2 c, Vector2 v)
        {
            DrawArc(c, 60, 0, Mathf.Tau, 48, Colors.White, 3);
            DrawCircle(c, 60, new Color(0, 0, 0, 0.45f));
            DrawArc(c, 60, 0, Mathf.Tau, 48, Colors.White, 3);
            DrawCircle(c + v.LimitLength(1) * 52, 11, v.Length() > 0.18f ? new Color(1f, 0.85f, 0.2f) : Colors.White);
        }

        public override void _Draw()
        {
            var c = m.controls;
            var f = ThemeDB.FallbackFont;
            string tag = $"SHOT {m.take.Title}  {(m.pad ? "pad" : "kbm")}  t={m.tNow.ToString("+0.00;-0.00", CultureInfo.InvariantCulture)} s  f {Engine.GetFramesDrawn()}";
            DrawStringOutline(f, new Vector2(40, 74), tag, HorizontalAlignment.Left, -1, 48, 10, new Color(0, 0, 0, 0.9f));
            DrawString(f, new Vector2(40, 74), tag, HorizontalAlignment.Left, -1, 48, Colors.White);
            float y = 1080 - 60, x = 40, s = 56;
            if (!m.pad)
            {
                Cap("W", new Vector2(x + s + 6, y - 2 * s - 6), new Vector2(s, s), c.IsDown("KeyW"));
                Cap("A", new Vector2(x, y - s), new Vector2(s, s), c.IsDown("KeyA"));
                Cap("S", new Vector2(x + s + 6, y - s), new Vector2(s, s), c.IsDown("KeyS"));
                Cap("D", new Vector2(x + 2 * s + 12, y - s), new Vector2(s, s), c.IsDown("KeyD"));
                Cap("SPACE", new Vector2(x, y + 6), new Vector2(3 * s + 12, 44), c.IsDown("Space"));
                Cap("LMB", new Vector2(x + 3 * s + 40, y - s), new Vector2(86, s), c.IsDown("Mouse0"));
                if (Mouse is { } p)
                {
                    DrawLine(p + new Vector2(-22, 0), p + new Vector2(22, 0), new Color(0, 0, 0, 0.9f), 7);
                    DrawLine(p + new Vector2(0, -22), p + new Vector2(0, 22), new Color(0, 0, 0, 0.9f), 7);
                    DrawLine(p + new Vector2(-20, 0), p + new Vector2(20, 0), new Color(1, 0.3f, 0.3f), 3);
                    DrawLine(p + new Vector2(0, -20), p + new Vector2(0, 20), new Color(1, 0.3f, 0.3f), 3);
                }
            }
            else
            {
                Stick(new Vector2(110, 1080 - 110), Controls.ScriptStick ?? Vector2.Zero);
                Stick(new Vector2(260, 1080 - 110), Controls.ScriptLook ?? Vector2.Zero);
                Cap("LB", new Vector2(340, 1080 - 90), new Vector2(80, 56), m.held.Contains("LB"));
                DrawString(f, new Vector2(60, 1080 - 190), "LEFT", HorizontalAlignment.Left, -1, 24, Colors.White);
                DrawString(f, new Vector2(214, 1080 - 190), "RIGHT", HorizontalAlignment.Left, -1, 24, Colors.White);
            }
        }
    }
}
