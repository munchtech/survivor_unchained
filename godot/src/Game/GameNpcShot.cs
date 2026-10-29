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
/// (walk with swap: walking on the spot, three-quarters to the camera). side: a full-body side view instead of chest's
/// close-up (its own camera 4 m off its flank at hip height, fov 30: knees, hem and feet in frame, for a stride check).
/// </summary>
public partial class Game
{
    /// <summary>
    /// --npc-crowd N[:name1,name2,...]: N Marionette packages (default: every folder of art/npc with a manifest) scattered
    /// 3-14 m from her in front of the camera, seeded; half idle at random headings, half walking circles of 2-4 m (perf).
    /// --npc-row [M]: instead a row of them standing across the view facing the camera (each copy dyed its own: NpcDye).
    /// </summary>
    void NpcCrowd()
    {
        if (Args.Get("npc-crowd") is not string arg || scene == null) return;
        var parts = arg.Split(':', 2);
        if (!int.TryParse(parts[0], out int n) || n <= 0) return;
        var names = parts.Length > 1 && parts[1].Length > 0 ? parts[1].Split(',', StringSplitOptions.RemoveEmptyEntries)
            : (DirAccess.GetDirectoriesAt("res://art/npc") ?? new string[0]).Where(d => FileAccess.FileExists($"{NpcPackage.Dir(d)}/manifest.json")).OrderBy(d => d, StringComparer.Ordinal).ToArray();
        if (names.Length == 0) { GD.PushWarning("npc-crowd: no packages"); return; }
        var views = new System.Collections.Generic.List<PersonView>();
        for (int i = 0; i < n; i++)
        {
            var name = names[i % names.Length];
            var m = NpcPackage.Read(name);
            var spec = new PersonSpec { Sex = m?.Sex == "female" ? Rpg.Sex.Female : Rpg.Sex.Male, Body = NpcPackage.Prefix + name };
            var v = new PersonView(spec, null, 0.8) { Name = $"CrowdNpc{i}" };
            scene.AddChild(v);
            v.Loop("Idle");
            views.Add(v);
        }
        GD.Print($"npc-crowd: {n} of [{string.Join(",", names)}]");
        AddChild(new NpcCrowdDriver(this, views));
    }

    sealed partial class NpcCrowdDriver : Node
    {
        readonly Game game;
        readonly System.Collections.Generic.List<PersonView> views;
        double t;
        bool told;
        // per NPC: centre x, z, heading (idle) or circle radius, phase (walk)
        double[][]? at;

        public NpcCrowdDriver(Game game, System.Collections.Generic.List<PersonView> views) { this.game = game; this.views = views; }

        public override void _Process(double delta)
        {
            t += delta;
            if (game.scene == null || game.Battle?.Player is not { } pl || GetViewport().GetCamera3D() is not Camera3D cam) return;
            if (at == null)
            {
                var rng = new Random((int)Args.Num("seed", 1) * 7919 + 17);
                var f = new Vector3((float)(pl.X - cam.GlobalPosition.X), 0, (float)(pl.Z - cam.GlobalPosition.Z)).Normalized();
                double fa = Math.Atan2(f.X, f.Z);
                at = new double[views.Count][];
                for (int i = 0; i < views.Count; i++)
                {
                    // (in front of the camera: from her, away from it, within 60 degrees either side; 3-14 m)
                    double d = 3 + 11 * rng.NextDouble(), a = fa + (rng.NextDouble() - 0.5) * 2.1;
                    double cx = pl.X + Math.Sin(a) * d, cz = pl.Z + Math.Cos(a) * d;
                    bool walk = i % 2 == 1;
                    // (--npc-row [M]: all standing in a row across the view, M m apart (default 1.1), 4 m beyond her,
                    // facing the camera, turned --npc-row-turn degrees (toward the light): a sheet of one package's copies, NpcDye)
                    if (Args.Has("npc-row"))
                    {
                        double sp = Args.Num("npc-row", 1.1f); if (sp <= 0.1) sp = 1.1;
                        double off = (i - (views.Count - 1) / 2.0) * sp;
                        cx = pl.X + f.X * 4 + f.Z * off; cz = pl.Z + f.Z * 4 - f.X * off;
                        walk = false;
                        at[i] = new[] { cx, cz, Math.Atan2(-f.X, -f.Z) + Args.Num("npc-row-turn", 0) * Math.PI / 180, 0, 0 };
                        continue;
                    }
                    at[i] = new[] { cx, cz, walk ? 2 + 2 * rng.NextDouble() : rng.NextDouble() * Math.PI * 2, rng.NextDouble() * Math.PI * 2, walk ? 1 : 0 };
                    if (walk) views[i].Locomotion(1.3);
                }
            }
            for (int i = 0; i < views.Count; i++)
            {
                var r = at[i];
                double x = r[0], z = r[1], heading = r[2];
                if (r[4] > 0)
                {
                    const double Speed = 1.3;
                    double a = r[3] + t * Speed / r[2];
                    x += r[2] * Math.Cos(a); z += r[2] * Math.Sin(a);
                    heading = Math.Atan2(-Math.Sin(a), Math.Cos(a));
                    views[i].Locomotion(Speed);
                }
                views[i].Place(x, game.scene.HeightAt(x, z), z, heading, true);
            }
            // (once, late: where each stands in the frame, head and feet, so a shot's seed can be picked with all of them in it)
            if (!told && t > 9)
            {
                told = true;
                var vp = GetViewport().GetVisibleRect().Size;
                for (int i = 0; i < views.Count; i++)
                {
                    var p = views[i].GlobalPosition;
                    Vector2 feet = cam.UnprojectPosition(p), head = cam.UnprojectPosition(p + Vector3.Up * 1.9f);
                    bool inside = !cam.IsPositionBehind(p) && feet.X > 0 && feet.X < vp.X && feet.Y < vp.Y && head.X > 0 && head.X < vp.X && head.Y > 0;
                    GD.Print($"npc-crowd: {i} feet {feet.X:0},{feet.Y:0} head {head.X:0},{head.Y:0} {(inside ? "in" : "CUT")}");
                }
            }
        }
    }

    void NpcShot()
    {
        if (Args.Get("npc") is not string arg || scene == null) return;
        var parts = arg.Split(':');
        var name = parts[0];
        // (kit folk as the town builds them: "watch", a gate Watchman with sword and shield; "folk", a townsperson;
        // "def.ID", a story NPC from npcs.json, with its own arms and idle)
        var rng = new Random((int)Args.Num("seed", 1));
        PersonSpec spec; Held? arms = null; string idle = "Idle"; double scale = 1;
        if (name == "watch") { spec = Folk.Person(FolkRole.Watch, Lore.WatchLook, rng); arms = new Held { Right = "viking_sword" }; idle = "Idle_Armed"; }
        else if (name == "folk") { var l = Lore.FolkLooks[1 % Lore.FolkLooks.Count]; spec = Folk.Person(FolkRole.Adult, l, rng); scale = l.Scale ?? 1; }
        else if (name.StartsWith("def.") && Lore.Person(name[4..]) is { } def) { spec = def.Person ?? new PersonSpec { Sex = Rpg.Sex.Male }; arms = def.Arms; idle = def.Idle.Length > 0 ? def.Idle : "Idle"; scale = def.Scale ?? 1; }
        else
        {
            var m = NpcPackage.Read(name);
            spec = new PersonSpec { Sex = m?.Sex == "female" ? Rpg.Sex.Female : Rpg.Sex.Male, Body = NpcPackage.Prefix + name };
        }
        var v = new PersonView(spec, arms, 0.8 * scale) { Name = "ShotNpc" };
        scene.AddChild(v);
        v.Loop(idle);
        // (the Watch at night is the patrol's: a lit torch in the left fist, its warm light on the face, as Folk makes him)
        if (name == "watch" && Args.Get("time") == "night")
        {
            v.Hold("handslot.l", "dungeon", "torch_lit");
            v.TorchLight();
        }
        GD.Print($"npc shot: {name} plays {idle}");
        AddChild(new NpcShotDriver(this, v, parts.Contains("walk"), parts.Contains("swap"), parts.Contains("chest") || parts.Contains("side"), parts.Contains("side")));
    }

    sealed partial class NpcShotDriver : Node
    {
        readonly Game game;
        readonly PersonView v;
        readonly bool walk, swap, chest, side;
        double t;
        Camera3D? chestCam, playCam;

        public NpcShotDriver(Game game, PersonView v, bool walk, bool swap, bool chest = false, bool side = false) { this.game = game; this.v = v; this.walk = walk; this.swap = swap || chest; this.chest = chest; this.side = side; }

        public override void _Process(double delta)
        {
            t += delta;
            if (game.scene == null || game.Battle?.Player is not { } pl || GetViewport().GetCamera3D() is not Camera3D cam) return;
            if (swap && game.scene.Player is { } her) her.Visible = false;
            if (swap) game.CloseStandIn = v;
            if (chest) game.scene.Voices.Bare = true;
            if (chest && chestCam == null) playCam = cam;
            if (chest && playCam != null) cam = playCam;
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
            // (in her place, the close-up framed on its own head, not hers: a shorter NPC's head sat low in her frame,
            // a taller one's took the camera inside it; the lift eased, as the bones settle in the first frames)
            var nh = HeadOf(v);
            if (chest)
            {
                if (chestCam == null)
                {
                    chestCam = new Camera3D { Fov = 30, KeepAspect = Camera3D.KeepAspectEnum.Height, Near = 0.05f, Far = 1400 };
                    game.scene.AddChild(chestCam);
                    chestCam.MakeCurrent();
                    GD.Print(side ? "npc shot: side camera at 4 m, hip height, fov 30" : "npc shot: chest camera at 1.4 m, fov 30");
                }
                if (nh is { } hs && side)
                {
                    // (off its flank: the facing turned a quarter, the camera and its aim at hip height)
                    var hip = hs - new Vector3(0, 0.72f, 0);
                    var f = new Vector3((float)Math.Sin(heading), 0, (float)Math.Cos(heading)).Rotated(Vector3.Up, Mathf.DegToRad(90f));
                    chestCam.GlobalPosition = hip + f * 4f;
                    chestCam.LookAt(hip, Vector3.Up);
                }
                else if (nh is { } hp)
                {
                    var f = new Vector3((float)Math.Sin(heading), 0, (float)Math.Cos(heading)).Rotated(Vector3.Up, Mathf.DegToRad(15f));
                    chestCam.GlobalPosition = hp + f * 1.4f + new Vector3(0, 0.0f, 0);
                    chestCam.LookAt(hp + new Vector3(0, -0.08f, 0), Vector3.Up);
                }
            }
            var hh = game.scene.Player is { } h ? HeadOf(h) : null;
            if (swap && nh is { } na && hh is { } hb) game.cam.AimLift = (float)Mathf.Lerp(game.cam.AimLift, na.Y - hb.Y, Math.Min(1, delta * 4));
            if (nh is { } q && (int)(t * 2) != (int)((t - delta) * 2) && t > 6)
                GD.Print($"npc shot {t:0.0}s: camera to its head {(q - c).Length():0.000} m, its head y {q.Y:0.000}, hers {hh?.Y ?? 0:0.000}, lift {game.cam.AimLift:0.000}");
            if (Args.Has("npc-debug") && !dbg && t > 7)
            {
                dbg = true;
                var sk = v.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>().First();
                int hb2 = sk.FindBone("Head");
                GD.Print($"npc debug: Head pose {sk.GetBoneGlobalPose(hb2)}, rest {sk.GetBoneGlobalRest(hb2)}");
                foreach (var mi in sk.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>())
                    GD.Print($"npc debug: mesh {mi.Name} visible {mi.IsVisibleInTree()} surfaces {mi.Mesh?.GetSurfaceCount()} aabb {mi.GetAabb()} skin {mi.Skin?.GetBindCount()} lod_bias {mi.LodBias} trans {mi.Transparency}");
            }
        }

        bool dbg;
        static Vector3? HeadOf(Node n) => n.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>().FirstOrDefault() is { } sk
            && sk.FindBone("Head") is int b && b >= 0 ? sk.GlobalTransform * sk.GetBoneGlobalPose(b).Origin : null;
    }
}
