using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// A place, and whatever is happening in it (the web game's game/scene.ts):
/// the zone's look and the fight or walk in it (the Battle). The fight is
/// stepped at a fixed 60 Hz whatever the frame rate, then everything drawn
/// is brought up to it: the survivor, the crowd, the effects. Heavy blows
/// hold the fight still for a few frames (the camera and the world around
/// keep real time). It is also what a zone's runtime reaches into to light
/// lamps, stand people up and have them speak (Play.IZoneLook).
/// </summary>
public partial class WorldScene : Node3D, IZoneLook
{
    public readonly ZoneData Data;
    public readonly ZoneView View;
    public readonly CrowdView Crowd = new();
    public readonly BattleFx Fx;
    public readonly Voices Voices = new();
    public PlayerView? Player;
    public Battle? Battle;
    readonly FollowCamera cam;
    public bool SimPaused;
    /// <summary>A held camera (the title, a cutscene) instead of the follow camera.</summary>
    public (Vector3 Pos, Vector3 Look)? Showcase;
    /// <summary>What the survivor is asked to do (the controls, or the autopilot).</summary>
    public Func<(double X, double Z)> Move = () => (0, 0);
    public Func<Act, bool> Pressed = _ => false;
    /// <summary>Each fixed step, before the fight's (the zone's own logic).</summary>
    public Action<double> OnStep = _ => { };
    /// <summary>What the fight said this frame, for the interface and the world.</summary>
    public Action<List<CombatEvent>> OnEvents = _ => { };
    /// <summary>A blow landed (0..1) and how low the survivor is: the edges of the picture.</summary>
    public float Bruise { get; private set; }
    /// <summary>Heavy blows hold the fight still for a moment (off with the screen's shake).</summary>
    public bool Hitstop = true;
    public double Time { get; private set; }
    double acc, hitstop, hitstopCd, fightTime, damageFlash, slowmo;
    List<CombatEvent> frameEvents = new();
    Vector2 grassAt;
    public const double Step = 1.0 / 60;

    public WorldScene(ZoneData data, FollowCamera cam)
    {
        Data = data;
        this.cam = cam;
        Name = $"World_{data.Id}";
        var start = new Vector2((float)data.Meta.Start.X, (float)data.Meta.Start.Z);
        View = new ZoneView(data, start, 26);
        grassAt = start;
        AddChild(View);
        AddChild(Crowd);
        Fx = new BattleFx((x, z) => data.HeightAt((float)x, (float)z)) { Cam = cam };
        Fx.OnDamageFlash = v => damageFlash = Math.Max(damageFlash, v);
        AddChild(Fx);
        AddChild(Voices);
    }

    public double HeightAt(double x, double z) => Data.HeightAt((float)x, (float)z);

    /// <summary>The fight (or walk) here, and the survivor in it.</summary>
    public Battle StartBattle(Battle b, Loadout lo)
    {
        Battle = b;
        Player?.QueueFree();
        Player = new PlayerView(lo);
        AddChild(Player);
        var p = b.Player;
        cam.Snap((float)p.X, (float)HeightAt(p.X, p.Z), (float)p.Z);
        return b;
    }

    /// <summary>What the survivor visibly carries, changed.</summary>
    public void SetLoadout(Loadout lo)
    {
        if (Battle == null) return;
        Player?.QueueFree();
        Player = new PlayerView(lo);
        AddChild(Player);
    }

    public void Update(double dt)
    {
        var b = Battle;
        Time += dt;
        hitstopCd = Math.Max(0, hitstopCd - dt);
        bool held = hitstop > 0;
        if (held) hitstop -= dt;
        // A perfect dodge: the world slows round you for a breath.
        if (slowmo > 0) slowmo -= dt;
        double fightDt = held ? dt * 0.08 : slowmo > 0 ? dt * 0.3 : dt;
        fightTime += fightDt;
        if (b != null && !SimPaused)
        {
            acc += Math.Min(fightDt, 0.1);
            while (acc >= Step)
            {
                acc -= Step;
                var (mx, mz) = Move();
                if (Pressed(Act.Dash)) b.Dash(mx, mz);
                if (Pressed(Act.Ability)) b.UseAbility(mx, mz);
                OnStep(Step);
                b.Tick(Step, mx, mz);
                var evs = b.Events.Drain();
                if (evs.Count == 0) continue;
                Fx.Handle(evs, b);
                Weigh(evs, b);
                frameEvents.AddRange(evs);
                foreach (var e in evs) if (e is Ev.LevelUp) { Player?.LevelFlare(); break; }
            }
        }
        Draw(dt, fightDt);
        if (frameEvents.Count > 0)
        {
            var evs = frameEvents;
            frameEvents = new();
            OnEvents(evs);
        }
    }

    /// <summary>Heavy blows hold the world still for a few frames: a boss or
    /// an elite going down, a critical that takes a third of what something
    /// had, a blow that really hurt, a shield bash landing. Never twice in
    /// quick succession, so a crowd going down does not stutter.</summary>
    void Weigh(List<CombatEvent> evs, Battle b)
    {
        foreach (var e in evs) if (e is Ev.PerfectDodge && Hitstop) slowmo = 0.38;
        if (hitstopCd > 0 || !Hitstop) return;
        double s = 0;
        foreach (var e in evs)
        {
            if (e is Ev.Kill k && k.ByPlayer && (k.Boss || k.Elite)) s = Math.Max(s, k.Boss ? 0.14 : 0.08);
            else if (e is Ev.Hit h && h.Crit && !h.Dot && h.MaxHp > 0 && h.Amount >= h.MaxHp * 0.35) s = Math.Max(s, 0.045);
            else if (e is Ev.PlayerHit ph && ph.Amount > b.MaxHp * 0.12) s = Math.Max(s, 0.07);
            else if (e is Ev.Ability a && a.Id == "shield_bash") s = Math.Max(s, 0.05);
        }
        if (s > 0) { hitstop = s; hitstopCd = s + 0.3; }
    }

    void Draw(double dt, double fightDt)
    {
        var b = Battle;
        if (b != null)
        {
            var p = b.Player;
            float y = (float)HeightAt(p.X, p.Z);
            Player?.Update(b, fightDt, fightTime, HeightAt);
            if (Showcase == null) cam.Update((float)dt, (float)p.X, y, (float)p.Z, (float)p.Vx, (float)p.Vz);
            Crowd.Update(b, HeightAt, fightTime);
            Fx.PlayerPos = new Vector3((float)p.X, y, (float)p.Z);
            Fx.Update(b, fightDt, fightTime);
            RenderingServer.GlobalShaderParameterSet("survivor", new Vector4((float)p.X, y + 1.1f, (float)p.Z, 1));
            // The meadow grows round the survivor as they go.
            var at = new Vector2((float)p.X, (float)p.Z);
            if (at.DistanceTo(grassAt) > 12) { grassAt = at; View.GrowGrass(at, 26); }
            // Taking a blow bruises the edges of the picture; so does being low.
            damageFlash = Math.Max(0, damageFlash - dt * 2.2);
            double low = p.Alive ? Math.Max(0, 0.35 - p.Hp / b.MaxHp) * 1.2 : 0.6;
            Bruise = (float)Math.Min(1, damageFlash * 0.7 + low);
        }
        if (Showcase is var (pos, look))
            cam.Camera.GlobalTransform = new Transform3D(Godot.Basis.LookingAt(look - pos, Vector3.Up), pos);
    }

    /* ------------------------------------------------ what a zone reaches -- */

    public void SetLit(int light, bool on) => View.SetLit(light, on);
    public bool IsLit(int light) => View.IsLit(light);

    public void Show(string node, bool visible)
    {
        if (View.Node(node) is Node3D n) n.Visible = visible;
    }

    public bool Shown(string node) => View.Node(node)?.Visible ?? false;
    public void Stop(string node) => View.Stop(node);

    public void AddProp(string id, double x, double z, double rot = 0, double scale = 1)
    {
        // The ground under a point of the piece, in its frame.
        float Ground(Vector3 p)
        {
            var w = new Godot.Basis(Vector3.Up, (float)rot) * (p * (float)scale);
            return (float)((HeightAt(x + w.X, z + w.Z) - HeightAt(x, z)) / scale);
        }
        // A KayKit piece (PACK/NAME) is made anew (Pieces).
        var piece = Dressing.Piece(id) ?? (id.Split('/') is [var pack, var name] ? Pieces.For(pack, name, (int)(x * 7 + z * 13), (float)scale, Ground) : null) ?? Stand(id);
        piece.Position = new Vector3((float)x, (float)HeightAt(x, z), (float)z);
        piece.Rotation = new Vector3(0, (float)rot, 0);
        piece.Scale = Vector3.One * (float)scale;
        View.AddChild(piece);
    }

    /// <summary>A piece from a pack not in the Godot game with nothing made
    /// for it yet (Pieces): a plain shape of about its size.</summary>
    static Node3D Stand(string id)
    {
        var root = new Node3D { Name = id.Replace('/', '_') };
        var stone = new StandardMaterial3D { AlbedoColor = new Color("#5a5650"), Roughness = 0.95f };
        if (id.Contains("grave"))
            root.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.55f, 0.8f, 0.14f), Material = stone }, Position = new Vector3(0, 0.35f, 0), Rotation = new Vector3(-0.08f, 0, 0.05f) });
        else
            root.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.5f, 0.5f, 0.5f), Material = stone }, Position = new Vector3(0, 0.25f, 0) });
        return root;
    }

    public int AddLight(double x, double y, double z, string color, double intensity, double distance, double flicker = 0.12, double glowSize = 0.08, string glowColor = "#ffb35a") =>
        View.AddLight(new Vector3((float)x, (float)y, (float)z), new Color(color), (float)intensity, (float)distance, (float)flicker, (float)glowSize, new Color(glowColor));

    public void MoveLight(int light, double x, double y, double z) => View.MoveLight(light, new Vector3((float)x, (float)y, (float)z));

    public INpcView Person(NpcDef def, Spot spot)
    {
        var spec = def.Person ?? new PersonSpec { Sex = Rpg.Sex.Male };
        var v = new PersonView(spec, def.Arms, 0.8 * (def.Scale ?? 1));
        v.Position = new Vector3((float)spot.X, (float)HeightAt(spot.X, spot.Z), (float)spot.Z);
        v.Rotation = new Vector3(0, (float)spot.Facing, 0);
        AddChild(v);
        return v;
    }

    public INpcView Walker(PersonSpec spec, double scale)
    {
        var v = new PersonView(spec, null, scale);
        AddChild(v);
        return v;
    }

    public void SetNight(bool on) => View.SetNight(on);
    public void Plates(List<Plate> plates) => Voices.Plates(plates);

    public void Bark(string text, double x, double y, double z, string? speaker = null) =>
        Voices.Bark(text, new Vector3((float)x, (float)y, (float)z), speaker);

    public IBossView BossView(string kind)
    {
        var v = new WardenView();
        AddChild(v);
        return v;
    }

    public INpcView Fallen(PersonSpec spec, Held? arms, double x, double z, double facing, string clip)
    {
        var v = new PersonView(spec, arms, 0.8);
        AddChild(v);
        v.Place(x, HeightAt(x, z), z, facing, true);
        v.Pose(clip);
        return v;
    }

    public IOrb Orb(string color, double size)
    {
        var o = new OrbView(color, size);
        AddChild(o);
        return o;
    }
}
