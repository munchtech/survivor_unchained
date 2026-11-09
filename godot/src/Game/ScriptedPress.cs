using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>--press SPEC[;SPEC...] (pictures only): scripted skill and dash presses for a shooting clip, under --auto idle.
/// SPEC = slot:t:dx,dz[:hold=S]; slot is 1-6 (Act.Skill1..6) or dash; t is Journey.Playtime seconds (as --cast); dx,dz are metres
/// from her position at the press moment (the aim); hold=S keeps the key held S seconds (a channel); move walks her along dx,dz
/// while it is held (a spin steered through a pack), and turn=DEG swings that walk DEG degrees over the hold (a curve). Game.cs wraps scene.Move,
/// Pressed, Held and Pointer through this. Each spec fires once, in time order.</summary>
public sealed class ScriptedPress
{
    const double AimAfter = 0.3, DashMove = 0.2;

    sealed class Spec
    {
        public Act Act; public int Slot; public double T, Dx, Dz, Hold, Turn;
        public bool Fired, Said, Consumed, Walk; public double At, Ax, Az;
    }

    readonly List<Spec> specs = new();
    readonly Func<double> clock;
    readonly Func<(double X, double Z)?> her;

    public ScriptedPress(string text, Func<double> clock, Func<(double X, double Z)?> her)
    {
        this.clock = clock; this.her = her;
        var inv = CultureInfo.InvariantCulture;
        foreach (var raw in text.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var p = raw.Split(':');
            var s = new Spec();
            if (p[0] == "dash") { s.Act = Act.Dash; s.Slot = 0; }
            else { s.Slot = int.Parse(p[0], inv); s.Act = Controls.Skills[s.Slot - 1]; }
            s.T = double.Parse(p[1], inv);
            var d = p[2].Split(',');
            s.Dx = double.Parse(d[0], inv); s.Dz = double.Parse(d[1], inv);
            for (int i = 3; i < p.Length; i++)
                if (p[i].StartsWith("hold=")) s.Hold = double.Parse(p[i][5..], inv);
                else if (p[i] == "move") s.Walk = true;
                else if (p[i].StartsWith("turn=")) s.Turn = double.Parse(p[i][5..], inv) * Math.PI / 180;
            specs.Add(s);
        }
        specs.Sort((a, b) => a.T.CompareTo(b.T));
    }

    void Update()
    {
        double t = clock();
        if (her() is not { } h) return;
        foreach (var s in specs)
        {
            if (s.Fired || t < s.T) continue;
            s.Fired = true; s.At = t; s.Ax = h.X + s.Dx; s.Az = h.Z + s.Dz;
        }
    }

    /// <summary>True on the one frame the press is asserted (read once).</summary>
    public bool Take(Act a)
    {
        Update();
        foreach (var s in specs)
        {
            if (s.Act != a || !s.Fired || s.Consumed) continue;
            s.Consumed = true;
            if (!s.Said && her() is { } h)
            {
                s.Said = true;
                GD.Print(string.Format(CultureInfo.InvariantCulture, "skill press frame {0} slot {1} t {2:0.00} at {3:0.00},{4:0.00} her {5:0.00},{6:0.00}",
                    Engine.GetFramesDrawn(), s.Slot == 0 ? "dash" : s.Slot.ToString(CultureInfo.InvariantCulture), clock(), s.Ax, s.Az, h.X, h.Z));
            }
            return true;
        }
        return false;
    }

    public bool Held(Act a)
    {
        Update();
        double t = clock();
        foreach (var s in specs)
            if (s.Act == a && s.Fired && s.Hold > 0 && t < s.At + s.Hold) return true;
        return false;
    }

    public (double X, double Z)? Pointer()
    {
        Update();
        double t = clock();
        foreach (var s in specs)
            if (s.Fired && t < s.At + Math.Max(AimAfter, s.Hold)) return (s.Ax, s.Az);
        return null;
    }

    public (double X, double Z)? Move()
    {
        Update();
        double t = clock();
        foreach (var s in specs)
        {
            if (s.Walk && s.Fired && t < s.At + s.Hold)
            {
                double lw = Math.Sqrt(s.Dx * s.Dx + s.Dz * s.Dz);
                // turn=DEG: the walk swings that many degrees (from +X toward +Z) over the hold (a curve steered)
                double ta = s.Turn * Math.Clamp((t - s.At) / s.Hold, 0, 1), c = Math.Cos(ta), sn = Math.Sin(ta);
                if (lw > 1e-6) return ((s.Dx * c - s.Dz * sn) / lw, (s.Dx * sn + s.Dz * c) / lw);
            }
            if (s.Act != Act.Dash || !s.Fired || t >= s.At + DashMove) continue;
            double l = Math.Sqrt(s.Dx * s.Dx + s.Dz * s.Dz);
            if (l > 1e-6) return (s.Dx / l, s.Dz / l);
        }
        return null;
    }
}
