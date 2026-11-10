using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The corner map asks the zone for its marks and the goals for their pins on a change of place, fog, goals or
/// her fallen belongings, and otherwise only twice a second (Game.MiniView, M4). That holds while no mark walks: a mark
/// may come, go, change its kind or jump (a townsperson's routine places them elsewhere while nobody is near), but none
/// glides. A mark that moves a little each frame would step on the corner map: this fails then, and MiniView's
/// cadence has to follow moves.</summary>
public class MiniMarksTests
{
    [Theory]
    [InlineData("waystation", TimeOfDay.Day)]
    [InlineData("waystation", TimeOfDay.Night)]
    [InlineData("verge", TimeOfDay.Day)]
    [InlineData("verge", TimeOfDay.Night)]
    [InlineData("lowford", TimeOfDay.Day)]
    public void The_corner_maps_marks_never_walk(string zone, TimeOfDay time)
    {
        var s = Route.New();
        s.W.Time = time;
        s.Enter(zone);
        var b = s.B!;
        double x0 = b.Player.X, z0 = b.Player.Z;
        Dictionary<string, (double X, double Z)> Marks()
        {
            var o = new Dictionary<string, (double, double)>();
            foreach (var m in s.Zone!.MapMarks()) o[$"mark:{m.Label}"] = (m.X, m.Z);
            foreach (var g in Goals.Active(Goals.All, s.J.Ctx, s.Zone.Id, s.Zone.Interactables)) o[$"goal:{g.Def.Id}"] = (g.X, g.Z);
            return o;
        }
        var before = Marks();
        Assert.NotEmpty(before);
        for (int i = 0; i < 30 * 20; i++)
        {
            // (she walks a slow ring round where she came in, so those who turn to her, or keep off her, have cause to)
            double a = i / 30.0 * 0.6;
            b.Player.X = x0 + Math.Sin(a) * 6; b.Player.Z = z0 + (1 - Math.Cos(a)) * 6;
            s.Wait(1 / 30.0);
            var now = Marks();
            foreach (var (k, at) in now)
            {
                if (!before.TryGetValue(k, out var was)) continue;
                double d = Math.Sqrt((at.X - was.X) * (at.X - was.X) + (at.Z - was.Z) * (at.Z - was.Z));
                Assert.True(d == 0 || d > 2, $"{zone}: {k} moved {d:0.000} m in one frame (a walking mark: Game.MiniView asks only twice a second)");
            }
            before = now;
        }
    }
}
