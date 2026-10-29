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
    /// <summary>A cinematic has the camera: the follow camera waits.</summary>
    public bool CameraHeld;
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
    /// <summary>How still the world is held (0 none, 1 all but stopped): the survivor and the crowd
    /// keep a breath of motion while what is staged over them (a chest opening) moves at full
    /// speed. The fight itself is paused by SimPaused.</summary>
    public float Hold;
    /// <summary>A freeze frame (a tutorial callout): the effects hold still with the fight.</summary>
    public bool FxStill;
    double acc, hitstop, hitstopCd, fightTime, viewTime, damageFlash, slowmo, fall;

    /// <summary>A dash or an art pressed a little early, kept until it can fire (seconds left).</summary>
    double dashHeld, artHeld;
    const double Buffer = 0.12;

    /// <summary>The world slowed to under a third for a while (an evolution's first volley).</summary>
    public void Slow(double seconds) => slowmo = Math.Max(slowmo, seconds);
    /// <summary>The night's peak in real seconds: the world slows hard as what ruled it falls
    /// and eases back to full speed (docs/EXPERIENCE_AUDIT.md, finding 2).</summary>
    const double Fall = 2.2;
    List<CombatEvent> frameEvents = new();
    public const double Step = 1.0 / 60;
    /// <summary>Where what moves is drawn, between the steps (Interp): everything drawn reads it, not the fight's own places.</summary>
    public readonly Interp Drawn = new();
    /// <summary>Where she is drawn this frame (on the ground; Interp).</summary>
    public Vector3 HerDrawn { get; private set; }

    public WorldScene(ZoneData data, FollowCamera cam) : this(data, cam, new ZoneView(data, new Vector2((float)data.Meta.Start.X, (float)data.Meta.Start.Z))) { }

    /// <summary>Round a zone already stood up (built ahead: Game.Prepare).</summary>
    public WorldScene(ZoneData data, FollowCamera cam, ZoneView view)
    {
        Data = data;
        this.cam = cam;
        Name = $"World_{data.Id}";
        View = view;
        AddChild(View);
        AddChild(Crowd);
        Fx = new BattleFx((x, z) => data.HeightAt((float)x, (float)z)) { Cam = cam, Lines = Voices };
        Fx.OnDamageFlash = v => damageFlash = Math.Max(damageFlash, v);
        AddChild(Fx);
        AddChild(Voices);
    }

    public override void _EnterTree() => GetTree().NodeAdded += FxNoShadow;

    /// <summary>Nothing under the Fx root casts a shadow (E1): many fx meshes are made without
    /// setting CastShadow, and Godot's default is On. Corpses (Gore) count as fx.</summary>
    void FxNoShadow(Node n)
    {
        if (n is not GeometryInstance3D g || g.CastShadow == GeometryInstance3D.ShadowCastingSetting.Off) return;
        for (Node? p = n.GetParent(); p != null; p = p.GetParent())
            if (p == Fx) { g.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; return; }
    }

    public double HeightAt(double x, double z) => Data.HeightAt((float)x, (float)z);

    readonly Vector4[] wadeFeet = new Vector4[8];
    readonly List<(double D2, Vector4 F)> wadeNear = new();

    /// <summary>Who stands in the still water (env 22): her and the nearest seven of the living within 30 m of her, each
    /// as (x, z, how deep: 0 at 1 cm, 1 by 25 cm, how fast), for the water's rings at their feet (Water.Wade).</summary>
    void Wading(Battle b, double hx, double hz, float y)
    {
        if (SurvivorUnchained.View.Water.Level is not float wl) return;
        static float Deep(float d) => Mathf.SmoothStep(0.01f, 0.25f, d);
        int n = 0;
        if (wl - y > 0.01f) wadeFeet[n++] = new Vector4((float)hx, (float)hz, Deep(wl - y), (float)Math.Sqrt(b.Player.Vx * b.Player.Vx + b.Player.Vz * b.Player.Vz));
        wadeNear.Clear();
        foreach (var e in b.Enemies.Living())
        {
            var (ex, ez) = Drawn.Of(e);
            double d2 = (ex - hx) * (ex - hx) + (ez - hz) * (ez - hz);
            if (d2 > 900) continue;
            float ey = (float)HeightAt(ex, ez);
            if (wl - ey <= 0.01f) continue;
            wadeNear.Add((d2, new Vector4((float)ex, (float)ez, Deep(wl - ey), (float)Math.Sqrt(e.Vx * e.Vx + e.Vz * e.Vz))));
        }
        wadeNear.Sort((a, c) => a.D2.CompareTo(c.D2));
        foreach (var (_, f) in wadeNear) { if (n == wadeFeet.Length) break; wadeFeet[n++] = f; }
        SurvivorUnchained.View.Water.Wade(wadeFeet.AsSpan(0, n));
    }

    /// <summary>The fight (or walk) here, and the survivor in it.</summary>
    public Battle StartBattle(Battle b, Loadout lo)
    {
        Battle = b;
        Player?.QueueFree();
        Player = new PlayerView(lo);
        look = Loadouts.Look(lo);
        AddChild(Player);
        var p = b.Player;
        // Facing the way she arrives (her facing otherwise follows only her steps, and she
        // stood facing south wherever she came in until she moved).
        Player.Face((float)p.Facing, new Vector3((float)p.X, (float)HeightAt(p.X, p.Z), (float)p.Z));
        cam.Snap((float)p.X, (float)HeightAt(p.X, p.Z), (float)p.Z);
        return b;
    }

    /// <summary>What the survivor visibly carries, changed.</summary>
    public void SetLoadout(Loadout lo)
    {
        if (Battle == null) return;
        // A ring or an amulet changes nothing that shows: the figure stays, and does not blink.
        var key = Loadouts.Look(lo);
        if (Player != null && key == look) return;
        look = key;
        // A swap still being dressed gives way to this one (the latest wins: nothing of the older is shown).
        DropIncoming();
        if (Player != null && key == shown) return;
        var old = Player;
        Perf.Lap("swap: (before)");
        // (a live swap: her new figure's garment tuck is laid over the next frames, on a worker; she wears what she wore
        // till it is done: Update)
        HerWear.Live = old != null;
        PlayerView next;
        try { next = new PlayerView(lo); }
        finally { HerWear.Live = false; }
        Perf.Lap("swap: the player view made");
        if (old != null && HerWear.Busy(next.Person)) { incoming = next; return; }
        Show(next, key);
    }

    /// <summary>Her new figure in place of the old.</summary>
    void Show(PlayerView next, string key)
    {
        var old = Player;
        Player = next;
        shown = key;
        AddChild(Player);
        Perf.Lap("swap: the player view added");
        // The new figure stands where the old one stood, facing its way, already posed.
        // The old one goes out of sight now: freed at the frame's end, it was drawn over the new
        // one for that frame, and the two showed through each other.
        if (old != null) { Player.Follow(old); old.Visible = false; old.QueueFree(); }
    }

    void DropIncoming()
    {
        if (incoming == null) return;
        HerWear.Cancel(incoming.Person);
        incoming.Free();   // (never in the tree)
        incoming = null;
    }

    /// <summary>Her next figure while a live swap dresses it (HerWear.Busy), and the look she shows.</summary>
    PlayerView? incoming;
    string shown = "";

    public override void _ExitTree()
    {
        GetTree().NodeAdded -= FxNoShadow;
        DropIncoming();
    }

    string look = "";

    public void Update(double dt)
    {
        // A live swap's figure dressed over frames, shown once it is.
        HerWear.Pump();
        if (incoming != null && !HerWear.Busy(incoming.Person)) { var next = incoming; incoming = null; Show(next, look); }
        var b = Battle;
        Time += dt;
        hitstopCd = Math.Max(0, hitstopCd - dt);
        bool held = hitstop > 0;
        if (held) hitstop -= dt;
        // A perfect dodge: the world slows round you for a breath.
        if (slowmo > 0) slowmo -= dt;
        if (fall > 0) fall -= dt;
        // The fall eases from a tenth of the speed back to all of it, the last of it quickest.
        double falling = fall > 0 ? 0.1 + 0.9 * Math.Pow(1 - fall / Fall, 2.2) : 1;
        double fightDt = held ? dt * 0.08 : slowmo > 0 ? dt * Math.Min(0.3, falling) : dt * falling;
        // A Flare holds the world's clock itself (FLARE_LOOK §1.2): 8% from the press to the Spend, its own hitstops.
        var flare = Fx.Flare;
        if (flare.Active) fightDt = dt * flare.WorldRate;
        fightTime += fightDt;
        if (b != null && !SimPaused) flare.Watch(b);
        // A press kept from before a pause (a draft, a chest) is not spent after it.
        if (SimPaused) dashHeld = artHeld = 0;
        if (b != null && !SimPaused)
        {
            acc += Math.Min(fightDt, 0.1);
            while (acc >= Step)
            {
                acc -= Step;
                // (Before the frame's last step: what is drawn is placed from here toward its end.)
                if (acc < Step) Drawn.Before(b);
                var (mx, mz) = Move();
                // A press a little early is kept for 120 ms and fires the moment it can, in the
                // direction held then (S-05): the dash is where timing lives, and a dropped press
                // cost most exactly when it mattered.
                if (Pressed(Act.Dash)) dashHeld = Buffer;
                if (dashHeld > 0) dashHeld = b.Dash(mx, mz) ? 0 : dashHeld - Step;
                if (Pressed(Act.Flare)) artHeld = Buffer;
                if (artHeld > 0) artHeld = b.UseFlare(mx, mz) ? 0 : artHeld - Step;
                OnStep(Step);
                Perf.Begin(Perf.Part.Sim);
                b.Tick(Step, mx, mz);
                Perf.End(Perf.Part.Sim);
                var evs = b.Events.Drain();
                if (evs.Count == 0) continue;
                Perf.Begin(Perf.Part.Fx);
                Fx.Handle(evs, b);
                Perf.End(Perf.Part.Fx);
                Weigh(evs, b);
                frameEvents.AddRange(evs);
                foreach (var e in evs)
                {
                    if (e is Ev.LevelUp) Player?.LevelFlare();
                    else if (e is Ev.Muzzle shot) Player?.OnMuzzle(shot.Angle);
                    else if (e is Ev.Ability ab)
                    {
                        if (ab.Id == "mirror_strike") Player?.Reflections.Strike(ab.Who);
                        else Player?.OnAbility(ab.Id);
                    }
                }
            }
            // Her clock: while the world waits at 8% the Flare's own clock is lent the rest of real time, so its
            // Release lands at her key pose (Battle.FlareLead; it never fires a blow and stops at the key).
            if (flare.Frozen)
            {
                b.FlareLead(Math.Max(0, dt * flare.LeadRate - fightDt));
                var evs = b.Events.Drain();
                if (evs.Count > 0)
                {
                    Fx.Handle(evs, b);
                    Weigh(evs, b);
                    frameEvents.AddRange(evs);
                }
            }
        }
        Drawn.After(acc, Step);
        Draw(dt, fightDt);
        if (frameEvents.Count > 0)
        {
            var evs = frameEvents;
            frameEvents = new();
            using var _ = new Perf.Span(Perf.Part.Events);
            OnEvents(evs);
        }
    }

    /// <summary>Heavy blows hold the world still for a few frames: a boss or
    /// an elite going down, a critical that takes a third of what something
    /// had, a blow that really hurt, a shield bash landing. Never twice in
    /// quick succession, so a crowd going down does not stutter.</summary>
    void Weigh(List<CombatEvent> evs, Battle b)
    {
        foreach (var e in evs)
        {
            if (e is Ev.PerfectDodge && Hitstop) slowmo = 0.38;
            if (e is Ev.Victory && Hitstop) fall = Fall;
        }
        if (hitstopCd > 0 || !Hitstop) return;
        double s = 0;
        foreach (var e in evs)
        {
            if (e is Ev.Kill k && k.ByPlayer && (k.Boss || k.Elite)) s = Math.Max(s, k.Boss ? 0.14 : 0.08);
            else if (e is Ev.Hit h && h.Crit && !h.Dot && h.MaxHp > 0 && h.Amount >= h.MaxHp * 0.35) s = Math.Max(s, 0.045);
            else if (e is Ev.PlayerHit ph && ph.Amount > b.MaxHp * 0.12) s = Math.Max(s, 0.07);
            // Her arts land with their own weight (S-17): the leap's landing, the rush's stop, the bash.
            else if (e is Ev.Ability a && a.Id is "shield_bash" or "bull_rush") s = Math.Max(s, 0.05);
            else if (e is Ev.Ability l && l.Id == "leap") s = Math.Max(s, 0.06);
        }
        if (s > 0) { hitstop = s; hitstopCd = s + 0.3; }
    }

    // (A name made once, not a new one every frame for the collector.)
    static readonly StringName SurvivorParam = "survivor";

    // The held staff (the Flare's head light), found once per figure.
    PlayerView? staffOf;
    Node3D? staff;

    void Draw(double dt, double fightDt)
    {
        var b = Battle;
        if (b != null)
        {
            var p = b.Player;
            // Where she is drawn: between the last two steps (Interp), as everything else is.
            var (hx, hz, leap) = Drawn.Her(b);
            float y = (float)HeightAt(hx, hz);
            HerDrawn = new Vector3((float)hx, y, (float)hz);
            // The living's own clock: the fight's, all but stopped while the world is held.
            double viewDt = fightDt * (1 - 0.97 * Math.Clamp(Hold, 0, 1));
            viewTime += viewDt;
            // She runs on her own clock through a Flare's freeze and its hitstops (full speed; 10% in a hitstop).
            var flare = Fx.Flare;
            double herDt = flare.Frozen || flare.Stop > 0 ? dt * flare.HerRate : viewDt;
            Perf.Begin(Perf.Part.Player);
            Player?.Update(b, hx, hz, leap, herDt, viewTime, HeightAt);
            Perf.End(Perf.Part.Player);
            // (a teaching freeze holds the camera too: the words were placed for this picture)
            if (Showcase == null && !CameraHeld && !FxStill) cam.Update((float)dt, (float)hx, y, (float)hz, (float)p.Vx, (float)p.Vz);
            Perf.Begin(Perf.Part.Crowd);
            Crowd.Still = Hold;
            Crowd.Drawn = Drawn;
            Crowd.Update(b, HeightAt, viewTime);
            Perf.End(Perf.Part.Crowd);
            Fx.PlayerPos = HerDrawn;
            Fx.Drawn = Drawn;
            Perf.Begin(Perf.Part.Fx);
            Fx.Update(b, FxStill ? 0 : fightDt, fightTime);
            flare.Her = HerDrawn;
            if (staffOf != Player) { staffOf = Player; staff = Player?.FindChild("arm:mage_staff", true, false) as Node3D; }
            flare.Staff = staff;
            flare.Tick(FxStill ? 0 : dt, b);
            Perf.End(Perf.Part.Fx);
            RenderingServer.GlobalShaderParameterSet(SurvivorParam, new Vector4((float)hx, y + 1.1f, (float)hz, 1));
            SurvivorUnchained.View.HouseFade.Her = new Vector4((float)hx, y + 1.1f, (float)hz, 1);
            Wading(b, hx, hz, y);
            // The meadow grows round the survivor as they go.
            var at = new Vector2((float)hx, (float)hz);
            View.FollowGrass(at);
            // The one shadowed lamp at a time (E1): the nearest to her, cross-faded.
            ShadowLamp.Update(HerDrawn, dt);
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
    public void HideProps(string id, double x, double z, double r) => View.HideProps(id, (float)x, (float)z, (float)r);
    public void Stop(string node) => View.Stop(node);

    public void AddProp(string id, double x, double z, double rot = 0, double scale = 1, double lift = 0)
    {
        // The ground under a point of the piece, in its frame.
        float Ground(Vector3 p)
        {
            var w = new Godot.Basis(Vector3.Up, (float)rot) * (p * (float)scale);
            return (float)((HeightAt(x + w.X, z + w.Z) - HeightAt(x, z)) / scale);
        }
        // A KayKit piece (PACK/NAME) is made anew (Pieces).
        var piece = Dressing.Piece(id) ?? (id.Split('/') is [var pack, var name] ? Pieces.For(pack, name, (int)(x * 7 + z * 13), (float)scale, Ground) : null) ?? Stand(id);
        piece.Position = new Vector3((float)x, (float)(HeightAt(x, z) + lift), (float)z);
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
        var v = new PersonView(spec, def.Arms, 0.8 * (def.Scale ?? 1)) { PhaseKey = $"{def.Id}@{spot.X:0.0},{spot.Z:0.0}" };
        v.Position = new Vector3((float)spot.X, (float)HeightAt(spot.X, spot.Z), (float)spot.Z);
        v.Rotation = new Vector3(0, (float)spot.Facing, 0);
        AddChild(v);
        v.Lod();
        return v;
    }

    public INpcView Walker(PersonSpec spec, double scale)
    {
        Folk.ChurnEvery = Args.Num("folk-churn", 0);
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        var v = new PersonView(spec, null, scale);
        long t1 = System.Diagnostics.Stopwatch.GetTimestamp();
        AddChild(v);
        long t2 = System.Diagnostics.Stopwatch.GetTimestamp();
        v.Lod();
        if (Perf.On) GD.Print($"perf walker: made {(t1 - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency:0.0} ms, in the tree {(t2 - t1) * 1000.0 / System.Diagnostics.Stopwatch.Frequency:0.0} ms, its shadow begun {(System.Diagnostics.Stopwatch.GetTimestamp() - t2) * 1000.0 / System.Diagnostics.Stopwatch.Frequency:0.0} ms");
        return v;
    }

    public INpcView WalkerLater(PersonSpec spec, double scale)
    {
        if (Args.Get("walker-later") == "off") return Walker(spec, scale);
        var v = new WalkerView(spec, scale);
        AddChild(v);
        return v;
    }

    public void SetNight(bool on) => View.SetNight(on);
    public void Plates(List<Plate> plates) => Voices.Plates(plates);

    public void Bark(string text, double x, double y, double z, string? speaker = null, string? voice = null) =>
        Voices.Bark(text, new Vector3((float)x, (float)y, (float)z), speaker, voice: voice);

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

    public IOrb EmberCore(double size)
    {
        var o = new EmberCoreView(size);
        AddChild(o);
        return o;
    }

    public IOrb Orb(string color, double size)
    {
        var o = new OrbView(color, size);
        AddChild(o);
        return o;
    }

    public IOrb Piece(string id, double scale)
    {
        var node = Dressing.Piece(id) ?? (id.Split('/') is [var pack, var name] ? Pieces.For(pack, name, 0, 1) : null);
        if (node == null) return Orb("#8a5a2a", scale * 0.35);
        var v = new PieceView(node);
        AddChild(v);
        return v;
    }
}
