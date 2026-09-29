using Godot;
using SurvivorUnchained.Actors;
using SurvivorUnchained.Fx;
using SurvivorUnchained.World;

namespace SurvivorUnchained;

/// <summary>
/// The slice's fight: the survivor, the Risen climbing out of the dark to
/// surround them, a sword that cuts, and what a cut feels like (a pause on
/// the hit, a shake, blood, the number). WASD to move in play; for
/// screenshots (--shot) an autopilot circles the fire, cutting what comes.
/// </summary>
public partial class Fight : Node3D
{
    readonly ZoneData zone;
    readonly Vector3 fire;
    Survivor you = null!;
    Horde horde = null!;
    Hits hits = null!;
    Camera3D cam = null!;
    OmniLight3D lantern = null!;
    Vector3 pos, look;
    float facing, swingCd, impactT = -1, spawnT, trauma, shakeT, hp = 200, autoT;
    bool mirror;
    readonly RandomNumberGenerator rng = new() { Seed = 21 };
    readonly bool auto = Args.Has("shot") || Args.Has("auto");

    const float Reach = 2.7f, Arc = 1.5f, Speed = 5.2f;

    public Fight(ZoneData zone, Vector3 start, Vector3 fire)
    {
        this.zone = zone;
        this.fire = fire;
        pos = start;
    }

    public override void _Ready()
    {
        you = new Survivor();
        AddChild(you);
        horde = new Horde();
        AddChild(horde);
        horde.Fill((int)Args.Num("risen", 18));
        hits = new Hits();
        AddChild(hits);
        // The survivor carries a light (the web game's lantern glow).
        lantern = new OmniLight3D { LightColor = new Color("#ffb070"), LightEnergy = 1.2f, OmniRange = 9, OmniAttenuation = 1.3f, ShadowEnabled = false };
        AddChild(lantern);
        cam = new Camera3D { Fov = 34, Far = 600, Current = true };
        AddChild(cam);
        look = pos;
        // A few already out of the ground when the shot starts.
        for (int i = 0; i < (int)Args.Num("start", 8); i++) SpawnNear(8, 13, true);
    }

    void SpawnNear(float min, float max, bool upright = false)
    {
        float a = rng.Randf() * Mathf.Tau, d = rng.RandfRange(min, max);
        var at = pos + new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * d;
        var r = horde.Raise(at, Mathf.Atan2(pos.X - at.X, pos.Z - at.Z));
        if (r != null && upright) { r.State = "walk"; horde.Play(r, "Zombie_Walk_Fwd", 0); r.Person.Anim.Seek(rng.Randf() * 1.2f, true); }
    }

    public override void _Process(double delta)
    {
        float dt = (float)delta;
        MoveSurvivor(dt);
        UpdateHorde(dt);
        Attack(dt);
        spawnT -= dt;
        int alive = 0;
        foreach (var r in horde.All) if (r.Alive) alive++;
        if (spawnT <= 0 && alive < horde.All.Count - 2) { SpawnNear(10, 15); spawnT = 0.7f; }
        PlaceCamera(dt);
    }

    void MoveSurvivor(float dt)
    {
        Vector3 want;
        if (auto)
        {
            // Circle the fire at a walk-and-cut pace.
            autoT += dt * 0.32f;
            var target = fire + new Vector3(Mathf.Cos(autoT), 0, Mathf.Sin(autoT)) * 6.5f;
            want = (target - pos) with { Y = 0 };
            if (want.Length() > 1) want = want.Normalized();
        }
        else
        {
            want = new Vector3(Input.GetAxis("ui_left", "ui_right"), 0, Input.GetAxis("ui_up", "ui_down"));
            if (Input.IsKeyPressed(Key.A)) want.X -= 1;
            if (Input.IsKeyPressed(Key.D)) want.X += 1;
            if (Input.IsKeyPressed(Key.W)) want.Z -= 1;
            if (Input.IsKeyPressed(Key.S)) want.Z += 1;
            if (want.Length() > 1) want = want.Normalized();
        }
        pos += want * Speed * dt;
        pos.Y = zone.HeightAt(pos.X, pos.Z);
        if (want.Length() > 0.1f && impactT < 0) facing = Mathf.LerpAngle(facing, Mathf.Atan2(want.X, want.Z), 1 - Mathf.Exp(-12 * dt));
        you.Move(want.Length() * Speed, dt);
        you.Position = pos;
        you.Rotation = new Vector3(0, facing, 0);
        lantern.Position = pos + new Vector3(0, 2.4f, 0.4f);
    }

    void UpdateHorde(float dt)
    {
        foreach (var r in horde.All)
        {
            if (r.State == "down") continue;
            r.StateT += dt;
            r.HitFlash = Mathf.Max(0, r.HitFlash - dt * 7);
            var glow = new Color(1f, 0.78f, 0.55f) * (r.HitFlash * 0.9f);
            foreach (var m in r.Mats) m.Emission = glow;
            var to = (pos - r.Pos) with { Y = 0 };
            float dist = to.Length();
            switch (r.State)
            {
                case "rising":
                    if (r.StateT > 1.3f) { r.State = "walk"; horde.Play(r, "Zombie_Walk_Fwd", 0.3f); }
                    break;
                case "walk":
                {
                    // Toward the survivor, shouldering the others aside.
                    var step = dist > 0.01f ? to / dist : Vector3.Zero;
                    var sep = Vector3.Zero;
                    foreach (var o in horde.All)
                    {
                        if (o == r || !o.Alive) continue;
                        var d = (r.Pos - o.Pos) with { Y = 0 };
                        float l = d.Length();
                        if (l < 0.9f && l > 0.001f) sep += d / l * (0.9f - l);
                    }
                    if (r.StateT > 0.35f) r.Pos += (step * 1.25f + sep * 2.2f) * dt;
                    r.Facing = Mathf.LerpAngle(r.Facing, Mathf.Atan2(to.X, to.Z), 1 - Mathf.Exp(-5 * dt));
                    r.AttackCd -= dt;
                    if (dist < 1.25f && r.AttackCd <= 0) { r.State = "attack"; r.StateT = 0; horde.Play(r, "Zombie_Scratch", 0.15f); }
                    break;
                }
                case "attack":
                    r.Facing = Mathf.LerpAngle(r.Facing, Mathf.Atan2(to.X, to.Z), 1 - Mathf.Exp(-8 * dt));
                    if (r.StateT > 0.7f && r.StateT - dt <= 0.7f && dist < 1.6f) { hp -= 6; trauma = Mathf.Min(1, trauma + 0.25f); }
                    if (r.StateT > 1.5f) { r.State = "walk"; r.StateT = 0.4f; r.AttackCd = 1.4f; horde.Play(r, "Zombie_Walk_Fwd", 0.25f); }
                    break;
                case "dying":
                    if (r.StateT > 9) { r.State = "dead"; r.Person.Root.Visible = false; }
                    else if (r.StateT > 7) r.Pos.Y -= dt * 0.5f; // the ground takes them back
                    break;
            }
            r.Pos += r.Push * dt;
            r.Push *= Mathf.Exp(-9 * dt);
            float ground = zone.HeightAt(r.Pos.X, r.Pos.Z);
            if (r.State != "dying") r.Pos.Y = ground;
            r.Person.Root.Position = r.Pos;
            r.Person.Root.Rotation = new Vector3(0, r.Facing, 0);
        }
    }

    void Attack(float dt)
    {
        swingCd -= dt;
        if (impactT >= 0)
        {
            impactT += dt;
            if (impactT >= 0.14f) { Impact(); impactT = -1; }
            return;
        }
        if (swingCd > 0) return;
        Risen? near = null;
        float best = Reach + 0.4f;
        foreach (var r in horde.All)
        {
            if (!r.Alive) continue;
            float d = (r.Pos - pos).Length();
            if (d < best) { best = d; near = r; }
        }
        if (near == null) return;
        facing = Mathf.Atan2(near.Pos.X - pos.X, near.Pos.Z - pos.Z);
        you.Rotation = new Vector3(0, facing, 0);
        you.Swing();
        mirror = !mirror;
        hits.Arc(pos + Vector3.Up * 1.05f, facing, Reach, 0.24f, mirror);
        swingCd = 0.62f;
        impactT = 0;
    }

    void Impact()
    {
        var fwd = new Vector3(Mathf.Sin(facing), 0, Mathf.Cos(facing));
        int landed = 0;
        foreach (var r in horde.All)
        {
            if (!r.Alive) continue;
            var to = (r.Pos - pos) with { Y = 0 };
            float d = to.Length();
            if (d > Reach || (d > 0.6f && fwd.AngleTo(to) > Arc * 0.62f)) continue;
            bool crit = rng.Randf() < 0.15f;
            int dmg = (int)(rng.RandfRange(11, 17) * (crit ? 2.1f : 1));
            r.Hp -= dmg;
            r.HitFlash = 1;
            var away = d > 0.01f ? to / d : fwd;
            r.Push += away * (crit ? 6 : 3.5f);
            var chest = r.Pos + Vector3.Up * 1.25f;
            hits.Spray(chest, away);
            hits.Number(r.Pos + Vector3.Up * 2.1f, dmg, crit);
            if (rng.Randf() < 0.6f) hits.Stain(r.Pos + away * rng.RandfRange(0.4f, 1.2f), rng.RandfRange(0.7f, 1.3f));
            landed++;
            if (r.Hp <= 0)
            {
                r.State = "dying"; r.StateT = 0;
                horde.Play(r, "Death01", 0.08f);
                hits.Stain(r.Pos, rng.RandfRange(1.6f, 2.2f));
            }
            else if (r.State != "rising") { horde.Play(r, "Hit_Chest", 0.05f); r.Person.Anim.Queue("Zombie_Walk_Fwd"); r.State = "walk"; r.StateT = 0; }
        }
        if (landed > 0)
        {
            trauma = Mathf.Min(1, trauma + 0.12f + 0.05f * landed);
            Hitstop(0.045f + 0.012f * Mathf.Min(landed, 3));
        }
    }

    /// <summary>The world holds still for a breath on a hit.</summary>
    void Hitstop(float seconds)
    {
        Engine.TimeScale = 0.06;
        GetTree().CreateTimer(seconds, true, false, true).Timeout += () => Engine.TimeScale = 1;
    }

    /// <summary>The web game's follow camera: steep, three-quarter, leading a
    /// little; shake by trauma.</summary>
    void PlaceCamera(float dt)
    {
        look = look.Lerp(pos + Vector3.Up * 0.8f, 1 - Mathf.Exp(-7 * dt));
        float pitch = Mathf.DegToRad(Args.Num("pitch", 56)), dist = Args.Num("dist", 23);
        var at = look + new Vector3(0, Mathf.Sin(pitch) * dist, Mathf.Cos(pitch) * dist);
        trauma = Mathf.Max(0, trauma - dt * 1.4f);
        shakeT += dt;
        float s = trauma * trauma, t = shakeT * 22;
        float N(float a) => Mathf.Sin(t + a) * 0.5f + Mathf.Sin(t * 2.3f + a * 1.7f) * 0.3f + Mathf.Sin(t * 4.1f + a * 3.1f) * 0.2f;
        cam.Position = at + new Vector3(N(1) * 0.7f, N(2) * 0.5f, N(3) * 0.7f) * s;
        cam.LookAt(look + new Vector3(N(4), 0, N(5)) * s * 0.25f);
    }
}
