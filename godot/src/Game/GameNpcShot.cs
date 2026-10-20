using System;
using System.Linq;
using Godot;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// <summary>
/// --npc NAME[:walk][:swap]: a Marionette package (NpcPackage, art/npc/NAME) stood in the place, for pictures. Beside
/// her, a step and a half to the camera's right, facing the camera (idle), or walking a small circle there (walk);
/// swap: in her place instead and she hidden, so the close-up (--close C --idle-after S) frames it as it frames her
/// (walk with swap: walking on the spot, three-quarters to the camera).
/// </summary>
public partial class Game
{
    void NpcShot()
    {
        if (Args.Get("npc") is not string arg || scene == null) return;
        var parts = arg.Split(':');
        var name = parts[0];
        var m = NpcPackage.Read(name);
        var spec = new PersonSpec { Sex = m?.Sex == "female" ? Rpg.Sex.Female : Rpg.Sex.Male, Body = NpcPackage.Prefix + name };
        var v = new PersonView(spec, null, 0.8) { Name = "ShotNpc" };
        scene.AddChild(v);
        v.Loop("Idle");
        AddChild(new NpcShotDriver(this, v, parts.Contains("walk"), parts.Contains("swap")));
    }

    sealed partial class NpcShotDriver : Node
    {
        readonly Game game;
        readonly PersonView v;
        readonly bool walk, swap;
        double t;

        public NpcShotDriver(Game game, PersonView v, bool walk, bool swap) { this.game = game; this.v = v; this.walk = walk; this.swap = swap; }

        public override void _Process(double delta)
        {
            t += delta;
            if (game.scene == null || game.Battle?.Player is not { } pl || GetViewport().GetCamera3D() is not Camera3D cam) return;
            if (swap && game.scene.Player is { } her) her.Visible = false;
            var c = cam.GlobalPosition;
            double x = pl.X, z = pl.Z;
            if (!swap)
            {
                // (the camera's right, flat)
                var r = cam.GlobalBasis.X; r.Y = 0; r = r.Normalized();
                double o = walk ? 2.4 : 1.5;
                x += r.X * o; z += r.Z * o;
            }
            double heading = Math.Atan2(c.X - x, c.Z - z);
            if (walk && swap)
            {
                // (in her place: walking on the spot, three-quarters to the camera, so the close-up keeps it framed)
                heading += 0.6;
                v.Locomotion(1.3);
            }
            else if (walk)
            {
                const double R = 1.4, Speed = 1.3;
                double a = t * Speed / R;
                x += R * Math.Cos(a); z += R * Math.Sin(a);
                // (along the circle: the tangent of (cos a, sin a))
                heading = Math.Atan2(-Math.Sin(a), Math.Cos(a));
                v.Locomotion(Speed);
            }
            v.Place(x, game.scene.HeightAt(x, z), z, heading, true);
        }
    }
}
