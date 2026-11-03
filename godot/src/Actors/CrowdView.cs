using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The horde on screen (the web game's render/crowd.ts): every creature the
/// fight has, drawn each frame from the simulation into one batch per kind
/// (Vat.cs: baked vertex animation, so a kind is one draw however many there
/// are). Which clip a creature plays, and how far into it, is decided here;
/// the simulation only says what it is doing. The dead lie where they fell
/// for a while, then the ground takes them back.
/// </summary>
public partial class CrowdView : Node3D
{
    const double RiseTime = 1.1;
    // The dead lie longer where there are few of them (the story's fights) and are taken back
    // sooner in a horde, where the living must stand out (docs/EXPERIENCE_AUDIT.md, finding 3).
    const double CorpseLie = 18, CorpseLieCrowded = 8, CorpseSink = 2.5;
    /// <summary>The most bodies left lying (fewer at the lower qualities).</summary>
    public int CorpseMax = 160;
    /// <summary>How still the world is held (WorldScene.Hold): a blow's flash fades rather than
    /// freezing white on a body for the length of a chest's opening.</summary>
    public float Still;
    bool shadows = true;
    /// <summary>Whether the crowd casts shadows (not at the lowest quality).</summary>
    public bool Shadows
    {
        get => shadows;
        set
        {
            shadows = value;
            foreach (var c in crowds.Values) c.CastShadow = value ? GeometryInstance3D.ShadowCastingSetting.On : GeometryInstance3D.ShadowCastingSetting.Off;
        }
    }

    /// <summary>A creature's own walk clock and heading, kept between frames.</summary>
    sealed class Gait
    {
        public double Seed, Phase, Facing;
        public bool Walking;
        public bool Seen;
        /// <summary>How it falls, chosen at its first dying frame and kept for its body.</summary>
        public string? Death;
        /// <summary>Its last living pose (a Flare's statue holds it).</summary>
        public string? LastRole;
        public double LastT;
        /// <summary>A slam's windup, while its blow and the get-up after it play (0: none).</summary>
        public double Slam;
        /// <summary>It knelt to aim: the shot that ends it is its own clip, not its melee strike.</summary>
        public bool Aimed;
        /// <summary>How far into its shot it was last frame (a new strike starts the clock again).</summary>
        public double ShotT;
        /// <summary>Burnt by a Flare's ring as it died (0..1), kept for its body.</summary>
        public float Char;
        /// <summary>Thrown as it died (view only): the sim stops a dying body's knockback slide (Ai returns before it),
        /// so a body killed by a heavy shove (Shield Bash, a slam, a rush) fell where it stood. Its fall carries the
        /// slide the sim gave it instead: offset (X, Z) and speed (Vx, Vz, decaying as Ai's slide does).</summary>
        public double ThrowX, ThrowZ, ThrowVx, ThrowVz;
        public bool Thrown;
        /// <summary>Away from the blow at its first dying frame (world heading, radians; NaN: not yet).</summary>
        public double Away = double.NaN;
        // (the census's: a 0.5 s window of where it was drawn and what it played, and how long its pose has held)
        public double CT = -1, CX, CZ, CClipT, CPhase, FSince;
        public string? CRole;
        public long FKey = -1;
        public EnemyState LastState;
        public double LastX, LastZ;
        /// <summary>How fast it is drawn moving (m/s, eased over about 0.15 s: the interpolated place, every shove in it), and which way.</summary>
        public double DrawnSpeed, DVx, DVz;
        /// <summary>Its death's twist under the blow: from the facing it had to the one its fall needs (NaN: none).</summary>
        public double FaceFrom, FaceTo = double.NaN;
        /// <summary>When the blow that knocked it back began its stagger (-1: none).</summary>
        public double KnockAt = -1;
        /// <summary>Shoved back against its facing: its steps run backward.</summary>
        public bool Back;
        public bool HasLast;
        /// <summary>Where the sim had it last frame, and how far the view holds it off that (a strike's planted feet).</summary>
        public double SimX, SimZ, OffX, OffZ;
        public string? SlideRole;
        public double SlideSince;
    }

    /// <summary>A dying body's knockback (m/s) at or over this is carried by its fall (ThrowOf); under it, it falls in place.</summary>
    const double ThrowFrom = 6;
    /// <summary>The farthest a fall carries a body (metres): the view has no walls to stop it.</summary>
    const double ThrowMax = 2.5;

    /// <summary>A dying body's thrown offset this frame: Ai's knockback slide (v * e^-9t, about v/9 metres) run in the
    /// view from its first dying frame, capped at ThrowMax. The sim is untouched.</summary>
    (double X, double Z) ThrowOf(Enemy e, Gait g)
    {
        if (!g.Thrown)
        {
            g.Thrown = true;
            g.ThrowX = g.ThrowZ = 0;
            double v = Math.Sqrt(e.Kbx * e.Kbx + e.Kbz * e.Kbz);
            (g.ThrowVx, g.ThrowVz) = v >= ThrowFrom ? (e.Kbx, e.Kbz) : (0, 0);
        }
        if (g.ThrowVx != 0 || g.ThrowVz != 0)
        {
            g.ThrowX += g.ThrowVx * dt; g.ThrowZ += g.ThrowVz * dt;
            double k = Math.Exp(-dt * 9);
            g.ThrowVx *= k; g.ThrowVz *= k;
            double d = Math.Sqrt(g.ThrowX * g.ThrowX + g.ThrowZ * g.ThrowZ);
            if (d > ThrowMax) { g.ThrowX *= ThrowMax / d; g.ThrowZ *= ThrowMax / d; g.ThrowVx = g.ThrowVz = 0; }
            if (Math.Abs(g.ThrowVx) + Math.Abs(g.ThrowVz) < 0.05) g.ThrowVx = g.ThrowVz = 0;
        }
        return (g.ThrowX, g.ThrowZ);
    }

    /// <summary>Where a body is drawn (the fight's interpolation, plus a dying body's throw): for the fx that sit on it.</summary>
    public (double X, double Z) DrawnAt(Enemy e)
    {
        var (x, z) = Drawn?.Of(e) ?? (e.X, e.Z);
        if (gaits.TryGetValue(e.Id, out var g) && g.Seed == e.Seed)
        {
            x += g.OffX; z += g.OffZ;
            if (e.State == EnemyState.Dying && g.Thrown) { x += g.ThrowX; z += g.ThrowZ; }
        }
        return (x, z);
    }

    /// <summary>Where in a slam's clip the fists (or the axe) meet the ground (crowd.py's SLAM_IMPACT): the
    /// windup is played to land exactly there as the sim's blow lands, however long the kind winds up.</summary>
    const double SlamImpact = 1.0;

    /// <summary>A body Burns Twice holds frozen in its last living pose, drawn until the Flare says it shattered,
    /// also after the fight has let it go (FlareFx.Kill: statues until an ember or the BOOM's ring breaks them).</summary>
    sealed record Statue(long Key, int Id, string Visual, string Role, double T, float X, float Z, float Facing, float Scale, Color Tint, float Glow);
    readonly Dictionary<long, Statue> statues = new();

    sealed record Corpse(long Key, string Visual, string Role, float X, float Z, float Facing, float Scale, Color Tint, float Glow, double Born)
    {
        /// <summary>Burnt by a Flare's ring (0..1), kept as it lies.</summary>
        public float Char;
        /// <summary>The fallen's enemy id (its struck rim lasts into its fall: most of a crowd her blade strikes dies of it).</summary>
        public int Id = -1;
        /// <summary>When it began to burn up with the Long Cut's struck (this view's clock; -1 not burning).</summary>
        public double BurnAt = -1;
        /// <summary>Its Long Cut death is ash (off the drawn seam), not gold.</summary>
        public bool Ash;
        /// <summary>How it lies on the slope (the ground's tilt under it; identity on the flat).</summary>
        public Godot.Basis Tilt = Godot.Basis.Identity;
        public bool Tilted;
    }

    /// <summary>Who a body is, for its slot in its kind's batch (VatCrowd): the same while it lives
    /// and while it lies after, never another's (a creature's place in the fight's list is reused).</summary>
    static long KeyOf(Enemy e) => ((long)e.Id << 32) ^ (BitConverter.DoubleToInt64Bits(e.Seed) & 0xffffffffL) ^ (BitConverter.DoubleToInt64Bits(e.Seed) >> 32);

    static readonly string[] Deaths = ["die", "die2", "die3"];

    /// <summary>How this one falls: one of its rig's deaths (on its back, face down, on its side),
    /// chosen by its seed but never the pose of the nearest body of its kind already lying within a
    /// metre and a half, so a field of the dead reads as a fight and not one pose stamped over and over.</summary>
    string DeathOf(VatAsset asset, Enemy e)
    {
        int have = 1;
        while (have < Deaths.Length && asset.Clips.ContainsKey(Deaths[have])) have++;
        int k = (int)(Math.Abs(e.Seed) * 7919) % have;
        if (have < 2) return Deaths[k];
        Corpse? near = null;
        float best = 1.5f * 1.5f;
        foreach (var c in corpses)
        {
            if (c.Visual != Vary.Body(e.Def.Visual, e.Seed)) continue;
            float dx = c.X - (float)e.X, dz = c.Z - (float)e.Z, d = dx * dx + dz * dz;
            if (d < best) { best = d; near = c; }
        }
        if (near != null && near.Role == Deaths[k]) k = (k + 1) % have;
        return Deaths[k];
    }

    /// <summary>The farthest a strike's planted feet hold a body off where the fight has it (metres).</summary>
    const double PlantMax = 0.45;

    /// <summary>The most a death turns a body to fall away (a kit body has a fall within this of any heading; a rig with one
    /// fall struck from behind twists this far and no further).</summary>
    const double TwistMax = 100 * Math.PI / 180;

    static double Hash01(double seed, double salt) { double v = Math.Sin(seed * 12.9898 + salt * 78.233) * 43758.5453; return v - Math.Floor(v); }

    /// <summary>THE DEATH-DIRECTION RULE: a body falls away from the blow (its knockback, else away from her), within
    /// 40 degrees of it by its seed (no starburst of spokes round her; a thrown body too: it slides along its throw and
    /// lands a little turned, and most of her kills are thrown). Of its
    /// deaths, its seed's if that one needs a turn of at most TwistMax and is not the nearest lying body's of its kind
    /// (DeathOf's rule), else the one that needs the least; the facing it needs is eased in as it falls (Draw).</summary>
    string DeathToward(VatAsset asset, Enemy e, Gait g, bool thrown)
    {
        double spread = 40 * Math.PI / 180;
        double target = g.Away + (Hash01(e.Seed, 3.7) * 2 - 1) * spread;
        string seeded = DeathOf(asset, e);
        string? best = null, bestFree = null;
        double bestTurn = double.MaxValue, bestFreeTurn = double.MaxValue;
        string? nearRole = NearestRole(e);
        foreach (var (role, off) in asset.FallOff!)
        {
            if (!asset.Clips.ContainsKey(role)) continue;
            double turn = Math.Abs(Wrap(target - off - g.Facing));
            if (turn < bestTurn) { bestTurn = turn; best = role; }
            if (role != nearRole && turn < bestFreeTurn) { bestFreeTurn = turn; bestFree = role; }
        }
        if (best == null) return seeded;
        string pick = asset.FallOff.TryGetValue(seeded, out var so) && Math.Abs(Wrap(target - so - g.Facing)) <= TwistMax ? seeded
            : bestFree != null && bestFreeTurn <= TwistMax ? bestFree : best;
        double need = Wrap(target - asset.FallOff[pick] - g.Facing);
        // (past what it can twist, it turns as far as it can toward straight away, not toward its seed's offset)
        if (Math.Abs(need) > TwistMax) need = Wrap(g.Away - asset.FallOff[pick] - g.Facing);
        g.FaceFrom = g.Facing;
        g.FaceTo = g.Facing + Math.Clamp(need, -TwistMax, TwistMax);
        return pick;
    }

    /// <summary>The death of the nearest body of its kind already lying within a metre and a half (null: none).</summary>
    string? NearestRole(Enemy e)
    {
        Corpse? near = null;
        float best = 1.5f * 1.5f;
        string visual = Vary.Body(e.Def.Visual, e.Seed);
        foreach (var c in corpses)
        {
            if (c.Visual != visual) continue;
            float dx = c.X - (float)e.X, dz = c.Z - (float)e.Z, d = dx * dx + dz * dz;
            if (d < best) { best = d; near = c; }
        }
        return near?.Role;
    }

    readonly Dictionary<string, VatCrowd> crowds = new();
    readonly Dictionary<int, Gait> gaits = new();
    readonly List<Corpse> corpses = new();
    readonly HashSet<(int, double)> laidOut = new();
    Battle? battle;
    double time, dt;
    int living;

    public CrowdView() { Name = "Crowd"; Placed = DrawnAt; }

    /// <summary>The live crowd's DrawnAt (the fx that sit on a body: its stun glint; the beats' throw log).</summary>
    public static Func<Enemy, (double X, double Z)>? Placed;

    /// <summary>Where each is drawn, between the fight's steps (WorldScene's).</summary>
    public Interp? Drawn;

    /// <summary>Whether a creature is under the ground by its script's say (set by the view; null: none is).</summary>
    public static Func<Enemy, bool>? Under;
    /// <summary>The Flare's say over a body it struck down (FlareFx.DeathOf): 1 held standing until its blow lands, -1 shattered
    /// (not drawn), 0 its own death.</summary>
    public static Func<int, int>? FlareDeath;
    /// <summary>How a held body is drawn (FlareFx.StatueLook: x frozen, y char, z dissolve, w burning): Burns Twice's
    /// ice statues, the Long Cut's burn-up in gold.</summary>
    public static Func<int, Godot.Vector4>? FlareStatueLook;
    /// <summary>Seconds since the Long Cut reached a corpse's place, or -1 (FlareFx.CorpseBurnAge).</summary>
    public static Func<double, double, double>? FlareCorpseBurn;
    /// <summary>Whether a corpse there goes as ash, not gold (FlareFx.CorpseAsh: off the Long Cut's drawn seam).</summary>
    public static Func<double, double, bool>? FlareCorpseAsh;
    /// <summary>A held body's struck flash (FlareFx.StatueFlash: the Long Cut's rim for 2-3 frames as its moment comes).</summary>
    public static Func<int, float>? FlareStatueFlash;
    /// <summary>A body's hit-kit struck look this frame (BattleFx.HitKit): (flash blend 0-0.5, gold rim 0-1); X &lt; 0 none.
    /// It replaces the sim's flash on the body (her auto-attacks' struck: no cream wash, no chalk ghosts by night).</summary>
    public static Func<int, Vector2>? StruckRim;
    /// <summary>The view's own struck flash for a body whose blow it draws later than the sim lands it (the Warden's
    /// heave: the flinch waits for the heave); null for the sim's.</summary>
    public static Func<int, float?>? FlashHeld;

    /// <summary>The Flare's char over a body here (FlareFx.CharAt: x, z, living), and whether its ring passed here 4 frames
    /// or more ago (FlareFx.RingPast). Judge 6 A2: a body the ring passes is ice that shatters or char, never beige.</summary>
    public static Func<double, double, bool, float>? FlareChar;
    public static Func<double, double, bool>? FlareRingPast;
    /// <summary>Last frame's audit: bodies drawn where the ring passed 4+ frames ago, and those of them not charred.</summary>
    public static int FlareAuditSeen, FlareAuditBad;
    // (the pictures' census, for the Long Cut's log: what the crowd drew this frame)
    static int censusFall, censusStatue, censusCorpse, censusBurn;
    static double censusFallD, b0X, b0Z;
    public static string FlareCensus => $"drawn: struck standing {censusStatue}, falling (not the Flare's) {censusFall} at mean {(censusFall > 0 ? censusFallD / censusFall : 0):0.0} m from her, corpses {censusCorpse} (burning {censusBurn})";
    // (--crowd-census: the deaths' fall against the blow, the dead's rest on the ground, the walkers' feet; a line a second)
    static readonly bool CensusOn = SurvivorUnchained.Args.Has("crowd-census");
    int cnDeaths, cnIn45, cnIn90, cnOver90, cnKnown, cnKb; double cnRC, cnRS;
    readonly Dictionary<string, int> cnRoles = new();
    int cnCorpN, cnSinking; double cnErrSum, cnErrMax, cnSinkMax;
    int cnFrames, cnActive, cnStall, cnWin; readonly Dictionary<string, int> cnSlide = new(), cnHeld = new();
    int cnLunge, cnLungeDie, cnLungeN; double cnLungeAng;
    double cnNext = -1, cnSlideT;
    readonly Dictionary<string, double> cnSlideNow = new();

    static double Wrap(double a) => Math.Atan2(Math.Sin(a), Math.Cos(a));

    void CensusDeath(Gait g, VatAsset asset, string role, double x, double z)
    {
        cnDeaths++;
        if (!cnRoles.TryAdd(role, 1)) cnRoles[role]++;
        if (asset.FallOff == null || !asset.FallOff.TryGetValue(role, out var off) || double.IsNaN(g.Away)) return;
        cnKnown++;
        double fall = g.Facing + off, d = Math.Abs(Wrap(fall - g.Away));
        if (d <= Math.PI / 4) cnIn45++; else if (d <= Math.PI / 2) cnIn90++; else cnOver90++;
        var p = battle!.Player;
        double r = Wrap(fall - Math.Atan2(z - p.Z, x - p.X));
        cnRC += Math.Cos(r); cnRS += Math.Sin(r);
    }

    void CensusWalker(Enemy e, Gait g, VatAsset asset, string role, double t, double x, double z)
    {
        if (e.State == EnemyState.Lunging)
        {
            double vx = (x - g.LastX) / Math.Max(dt, 1e-4), vz = (z - g.LastZ) / Math.Max(dt, 1e-4);
            if (vx * vx + vz * vz > 0.25 && g.LastState == EnemyState.Lunging) { cnLungeAng += Math.Abs(Wrap(g.Facing - Math.Atan2(vz, vx))); cnLungeN++; }
            cnLunge++;
        }
        if (e.State != EnemyState.Active) { g.CT = -1; g.FKey = -1; return; }
        cnActive++;
        bool loco0 = role is "move" or "move2" or "hit";
        if (role != g.SlideRole) { g.SlideRole = role; g.SlideSince = time; }
        if (g.DrawnSpeed > 0.3 && !loco0 && time - g.SlideSince > 0.2) { cnSlideT += dt; if (!cnSlideNow.TryAdd(role, dt)) cnSlideNow[role] += dt; }
        long fk = ((long)role.GetHashCode() << 20) ^ asset.Frame(role, t).F0;
        if (fk != g.FKey) { g.FKey = fk; g.FSince = time; }
        else if (time - g.FSince > 1.5) { if (!cnHeld.TryAdd(role, 1)) cnHeld[role]++; }
        if (g.CT < 0) { g.CT = time; g.CX = x; g.CZ = z; g.CClipT = t; g.CRole = role; g.CPhase = g.Phase; return; }
        if (time - g.CT < 0.5) return;
        double span = time - g.CT, sp = Math.Sqrt((x - g.CX) * (x - g.CX) + (z - g.CZ) * (z - g.CZ)) / span;
        bool loco = role is "move" or "move2" or "hit";
        cnWin++;
        if (sp > 0.3 && (!loco || Math.Abs(t - g.CClipT) < 1e-3))
        {
            string k = role != g.CRole ? $"{g.CRole}>{role}" : role;
            if (!cnSlide.TryAdd(k, 1)) cnSlide[k]++;
        }
        if (loco && role != "hit" && g.CRole == role && Math.Abs(g.Phase - g.CPhase) < 0.05) cnStall++;
        g.CT = time; g.CX = x; g.CZ = z; g.CClipT = t; g.CRole = role; g.CPhase = g.Phase;
    }

    void CensusLog()
    {
        if (!CensusOn) return;
        cnFrames++;
        if (cnNext < 0) cnNext = time + 1;
        if (time < cnNext) return;
        double cnSpan = Math.Max(1e-3, time - cnNext + 1);
        cnNext = time + 1;
        double R = cnKnown > 0 ? Math.Sqrt(cnRC * cnRC + cnRS * cnRS) / cnKnown : 1;
        double sd = R >= 1 ? 0 : Math.Sqrt(-2 * Math.Log(Math.Max(R, 1e-9))) * 180 / Math.PI;
        static string D(Dictionary<string, int> m, double per)
        {
            var l = new List<string>();
            foreach (var (k, v) in m) l.Add($"{k}:{v / per:0.#}");
            return l.Count == 0 ? "-" : string.Join(",", l);
        }
        int fr = Math.Max(1, cnFrames);
        GD.Print($"crowd census t={time:0.0}: deaths {cnDeaths} (fall known {cnKnown}, by knockback {cnKb}) roles {D(cnRoles, 1)}; fall vs away <=45 {cnIn45} 45-90 {cnIn90} >90 {cnOver90}; fall-radial sd {sd:0} deg"
            + $" | corpses {cnCorpN / (double)fr:0}/frame far-end |dy| mean {(cnCorpN > 0 ? cnErrSum / cnCorpN : 0):0.000} max {cnErrMax:0.000} m, sinking {cnSinking / (double)fr:0.0}/frame, sink max {cnSinkMax:0.00} m"
            + $" | active {cnActive / (double)fr:0}/frame, windows {cnWin}: sliding (0.5 s windows) {D(cnSlide, 1)} walk-stalled {cnStall}, held>1.5s {D(cnHeld, fr)}/frame"
            + $" | drawn moving >0.3 m/s in a held pose: {cnSlideT / Math.Max(1e-3, cnSpan):0.0} bodies ({string.Join(",", cnSlideNow.Select(kv => $"{kv.Key}:{kv.Value / Math.Max(1e-3, cnSpan):0.0}"))})"
            + $" | lunging {cnLunge / (double)fr:0.0}/frame facing-vs-travel {(cnLungeN > 0 ? cnLungeAng / cnLungeN * 180 / Math.PI : 0):0} deg, died mid-lunge {cnLungeDie}");
        cnCorpN = cnFrames = cnActive = cnWin = cnStall = cnSinking = cnLunge = cnLungeN = 0; cnErrSum = cnErrMax = cnSinkMax = cnLungeAng = 0;
        cnSlide.Clear(); cnHeld.Clear(); cnSlideNow.Clear(); cnSlideT = 0;
    }

    /// <summary>Char: the body's paint times this (albedo under 0.06 linear).</summary>
    static readonly Color CharTint = new(0.06f, 0.048f, 0.04f, 1);

    static Color Charred(Color tint, float k) => k <= 0 ? tint : new Color(Math.Sign(tint.R + 1e-9f) * Mathf.Lerp(Math.Abs(tint.R), CharTint.R, k), Mathf.Lerp(tint.G, CharTint.G, k), Mathf.Lerp(tint.B, CharTint.B, k), tint.A);

    /// <summary>Counts what is drawn: the char the body's paint gets, and whether it is ice (vat.gdshaderinc paints the
    /// fireball's colour only on the frozen, so a body drawn unfrozen and charred is black under it; judge 7 (1)).</summary>
    static void Audit(double x, double z, float k, float frozen = 0)
    {
        if (FlareRingPast?.Invoke(x, z) != true) return;
        FlareAuditSeen++;
        if (k < 0.99f || frozen > 0) FlareAuditBad++;
    }

    /// <summary>A cinematic's say over a creature it stages (set by the cinematic, null when none plays):
    /// how far down it is drawn (Grimtunnel waist-deep in the ford, C03), and a role it holds once up and
    /// standing, with the seconds since it began (his arms round the heart), or null for its own; and which
    /// way it is drawn facing (to her, whatever its own mind), or null.</summary>
    public static Func<Enemy, (double Sink, string? Role, double T, double? Facing)?>? Staged;

    /// <summary>How many are standing, and lying (for the log).</summary>
    public (int Living, int Dead) Counts => (living, corpses.Count);

    /// <summary>Bake the kinds a place will have ahead (behind the fade), so
    /// the first wolf does not hitch the frame.</summary>
    public void Prepare(IEnumerable<string> visuals)
    {
        var kinds = new List<string>();
        foreach (var v in visuals)
            if (!v.StartsWith("view:")) { kinds.Add(v); if (Vary.Bodies.TryGetValue(v, out var alt)) kinds.Add(alt.Visual); }
        // The people still to be baked (a first launch) are built from the
        // kit's models: their textures decoded side by side first, not one by
        // one as each model loads.
        var files = new List<string>();
        foreach (var v in kinds)
            if (Visuals.Of(v) is { Person: { } person } spec && !Vat.Ready(spec)) files.AddRange(People.Files(person));
        if (files.Count > 0) Prefetch.Scenes(files);
        foreach (var v in kinds) Crowd(v);
    }

    VatCrowd Crowd(string visual)
    {
        if (crowds.TryGetValue(visual, out var c)) return c;
        c = new VatCrowd(Vat.Of(Visuals.Of(visual), this));
        if (!shadows) c.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
        AddChild(c);
        crowds[visual] = c;
        return c;
    }

    public void Update(Battle b, Func<double, double, double> heightAt, double now)
    {
        if (b != battle)
        {
            battle = b;
            gaits.Clear();
            corpses.Clear();
            laidOut.Clear();
            statues.Clear();
        }
        dt = Math.Clamp(now - time, 0, 0.1);
        time = now;
        foreach (var c in crowds.Values) c.Begin();
        foreach (var g in gaits.Values) g.Seen = false;
        living = 0;
        FlareAuditSeen = FlareAuditBad = 0;
        censusFall = censusStatue = censusCorpse = censusBurn = 0; censusFallD = 0; b0X = b.Player.X; b0Z = b.Player.Z;
        whiteFlashes = 0;
        eliteFlashes = 0;
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.Def.Visual.StartsWith("view:", StringComparison.Ordinal)) continue;
            Draw(e, heightAt);
        }
        // The Flare's statues, then the dead after the living.
        DrawStatues(heightAt);
        DrawCorpses(heightAt);
        foreach (var c in crowds.Values) c.End();
        CensusLog();
        // Whatever the fight let go of forgets its gait.
        if (gaits.Count > 2 * living + 64)
        {
            var gone = new List<int>();
            foreach (var (id, g) in gaits) if (!g.Seen) gone.Add(id);
            foreach (var id in gone) gaits.Remove(id);
        }
    }

    /// <summary>Bodies flashed white this frame, and how many may be: past it, a flash stays at the
    /// rim (the shader's whole-body white needs a flash over this).</summary>
    int whiteFlashes;
    const int WhiteFlashes = 3;
    /// <summary>Champions flashed white this frame, on top of the three: eight elite risen under one
    /// Iron Palms went white together, the same white-out the cap was made against.</summary>
    int eliteFlashes;
    const int EliteFlashes = 2;
    /// <summary>The flare the rest keep, at the rim only. At 0.55 the rim's term alone turned pale
    /// bodies (the Risen) into cream ghosts at thirty metres (seen from above, most of a body is
    /// rim): seven at once round one Iron Palms, struck again each frame as they flew.</summary>
    const float FlashRimOnly = 0.12f;

    void Draw(Enemy e, Func<double, double, double> heightAt)
    {
        // Its body already lies where it fell: the fight lets it go shortly.
        if (laidOut.Contains((e.Id, e.Seed))) return;
        // (its body: the kind's, or its second body for a share of copies: Vary.Body)
        var crowd = Crowd(Vary.Body(e.Def.Visual, e.Seed));
        var asset = crowd.Asset;
        if (!gaits.TryGetValue(e.Id, out var g) || g.Seed != e.Seed)
            gaits[e.Id] = g = new Gait { Seed = e.Seed, Phase = e.Seed * 7, Facing = e.Facing };
        g.Seen = true;
        string role = "idle";
        var (ex, ez) = Drawn?.Of(e) ?? (e.X, e.Z);
        // A strike plants its feet: the crowd's shoves and its own last steps during it are held off (up to PlantMax) and
        // walked out after it (the census: a strike slid on its feet for 2 to 5 bodies at a time at the press).
        if (g.HasLast)
        {
            bool planted = e.State == EnemyState.Active && e.Anim == EnemyAnim.Attack && e.AnimT < asset.Duration("attack") && Staged == null;
            if (planted) { g.OffX -= ex - g.SimX; g.OffZ -= ez - g.SimZ; }
            else { double k = Math.Exp(-dt / 0.2); g.OffX *= k; g.OffZ *= k; }
            double od = Math.Sqrt(g.OffX * g.OffX + g.OffZ * g.OffZ);
            if (od > PlantMax) { g.OffX *= PlantMax / od; g.OffZ *= PlantMax / od; }
        }
        g.SimX = ex; g.SimZ = ez;
        ex += g.OffX; ez += g.OffZ;
        if (e.State == EnemyState.Dying) { var (tx, tz) = ThrowOf(e, g); ex += tx; ez += tz; }
        else g.Thrown = false;
        double t = e.AnimT, y = heightAt(ex, ez);
        float dissolve = 0;
        Godot.Vector4 fallBurn = default;
        double speed = Math.Sqrt(e.Vx * e.Vx + e.Vz * e.Vz);
        // How it is drawn moving: the sim's walk, and also every shove the sim gives it without a walk (the crowd's
        // press: FinishMove keeps them out of each other; a knockback's slide).
        if (dt > 0 && g.LastState == e.State && g.HasLast)
        {
            double ivx = (ex - g.LastX) / dt, ivz = (ez - g.LastZ) / dt;
            if (ivx * ivx + ivz * ivz < 900) { double k = Math.Min(1, dt / 0.15); g.DVx += (ivx - g.DVx) * k; g.DVz += (ivz - g.DVz) * k; }
        }
        g.DrawnSpeed = Math.Sqrt(g.DVx * g.DVx + g.DVz * g.DVz);
        // THE WALKER RULE: a held pose never slides. A body drawn moving walks (its steps run with how fast it is drawn
        // going, also when the crowd shoves it and its own mind stands still), and one knocked back staggers back.
        // (The census: about 11 bodies at a time in a 250 night horde slid in their idle or strike, up to 25 at the press.)
        double moving = Math.Max(speed, g.DrawnSpeed);
        // Walking or standing, with a margin between the two, so a creature
        // jostled at the edge of walking pace does not flicker between clips.
        g.Walking = moving > (g.Walking ? 0.2 : 0.45);
        double kbNow = Math.Sqrt(e.Kbx * e.Kbx + e.Kbz * e.Kbz);
        if (e.State == EnemyState.Active && kbNow >= 1 && asset.Clips.ContainsKey("hit") && (g.KnockAt < 0 || time - g.KnockAt > 0.25)) g.KnockAt = time;
        switch (e.State)
        {
            // (risen, a varied pack's copy stands its own moment before it comes on: Ai, Vary.Delay)
            case EnemyState.Rising when e.AnimT >= RiseTime && asset.Clips.ContainsKey("idle"):
                role = "idle"; t = time + e.Seed * 9;
                break;
            case EnemyState.Rising:
                role = "rise";
                t = e.AnimT * (asset.Duration("rise") / RiseTime);
                break;
            case EnemyState.Dying:
            {
                // Burst apart: nothing is left to fall (the gore threw it). A Flare's kill is the Flare's to show first: the
                // frost's overkill bursts nearly every body, and the pack vanished at frost +0.1 s (s2a).
                int flareSays = FlareDeath?.Invoke(e.Id) ?? 0;
                if (flareSays == 0 && e.Burst) return;
                if (flareSays < 0) return;
                if (flareSays > 0)
                {
                    long key = KeyOf(e);
                    if (!statues.ContainsKey(key))
                    {
                        var (st, sg) = TintOf(e);
                        string sr = g.LastRole ?? (g.Death ??= DeathOf(asset, e));
                        statues[key] = new Statue(key, e.Id, Vary.Body(e.Def.Visual, e.Seed), sr, g.LastRole != null ? g.LastT : 0, (float)ex, (float)ez, (float)g.Facing,
                            (float)((e.Def.Scale ?? 1) * Vary.Size(e.Seed, e.Def.Size ?? 0)) * Beasts.Size(e.Def.Visual), st, sg);
                    }
                    return;
                }
                if (g.Death == null)
                {
                    double kb = Math.Sqrt(e.Kbx * e.Kbx + e.Kbz * e.Kbz);
                    if (kb > 0.5) { g.Away = Math.Atan2(e.Kbz, e.Kbx); cnKb++; }
                    else g.Away = Math.Atan2(ez - battle!.Player.Z, ex - battle.Player.X);
                    if (g.LastState == EnemyState.Lunging) cnLungeDie++;
                    if (asset.FallOff != null) g.Death = DeathToward(asset, e, g, kb >= ThrowFrom);
                }
                role = g.Death ??= DeathOf(asset, e);
                // The twist under the blow: eased over the fall's first 0.2 s, then held (never a one-frame snap).
                if (!double.IsNaN(g.FaceTo)) g.Facing = g.FaceFrom + Wrap(g.FaceTo - g.FaceFrom) * Smooth(e.DieT, 0, 0.2);
                if (FlareChar != null) g.Char = Math.Max(g.Char, FlareChar(ex, ez, false));
                // The Long Cut burns her own kills still falling in its reach on the struck's clock (the fuse plus 0.05 s a
                // metre), and they are gone before they land: r2's ring of bodies falling away from her, black by day and
                // blue-grey by night, were these (the hold slows their fall), not the struck, who never fall.
                if (FlareCorpseBurn?.Invoke(ex, ez) is double fk && fk >= 0)
                {
                    bool fa = FlareCorpseAsh?.Invoke(ex, ez) ?? false;
                    if (fk >= SurvivorUnchained.View.FlareFx.BurnTimeOf(fa)) { laidOut.Add((e.Id, e.Seed)); return; }
                    fallBurn = SurvivorUnchained.View.FlareFx.BurnLook((float)fk, fa);
                }
                censusFall++; censusFallD += Math.Sqrt((ex - b0X) * (ex - b0X) + (ez - b0Z) * (ez - b0Z));
                t = e.DieT * Math.Max(1, asset.Duration(role) / (Ai.DieTime * 0.62));
                // Summons fade; the rest fall and stay.
                if (e.Disposition == Disposition.Ally) dissolve = Smooth(e.DieT, Ai.DieTime * 0.55, Ai.DieTime);
                else if (e.DieT >= Ai.DieTime - 0.12) { if (CensusOn) CensusDeath(g, asset, role, ex, ez); LayOut(e, ex, ez, g.Facing, role, g.Char); return; }
                break;
            }
            case EnemyState.Burrowed:
                role = "burrow";
                y -= 0.25;
                t = time + e.Seed * 3;
                break;
            case EnemyState.Surfacing:
                role = "rise";
                t = (0.55 - e.StateT) * 1.2;
                break;
            case EnemyState.Windup:
                role = "windup";
                t = time;
                break;
            case EnemyState.Casting when e.Cast == CastKind.Slam && asset.Clips.ContainsKey("slam"):
                // Up overhead and down, the fists meeting the ground as the blow lands.
                role = "slam";
                g.Slam = Math.Max(0.1, e.AnimT + e.StateT);
                t = e.AnimT * SlamImpact / g.Slam;
                break;
            case EnemyState.Casting when e.Cast == CastKind.Aim && asset.Clips.ContainsKey("aim"):
                // Down on one knee, the crossbow brought up to the eye, and held on its line.
                role = "aim";
                g.Aimed = true;
                g.ShotT = 0;
                break;
            case EnemyState.Casting:
                // A cast of its own (a howl, a rally) from its start; a stand-in windup loops.
                role = asset.Clips.ContainsKey("cast") ? "cast" : "windup";
                t = role == "cast" ? e.AnimT : time;
                break;
            case EnemyState.Lunging:
                role = "move";
                t = time * 1.8 + e.Seed * 5;
                break;
            default:
                // After a slam, the rest of it: the blow held on the ground, then the get-up (its
                // clock runs on until a strike starts it again).
                if (g.Slam > 0 && e.Anim != EnemyAnim.Attack && SlamImpact + e.AnimT - g.Slam < asset.Duration("slam"))
                {
                    role = "slam";
                    t = SlamImpact + e.AnimT - g.Slam;
                    break;
                }
                g.Slam = 0;
                // After an aim, the shot: the release, the kick and the rise.
                if (g.Aimed && e.AnimT >= g.ShotT && e.AnimT < asset.Duration("shot") && asset.Clips.ContainsKey("shot"))
                {
                    role = "shot";
                    t = g.ShotT = e.AnimT;
                    break;
                }
                g.Aimed = false;
                g.ShotT = 0;
                if (e.Anim == EnemyAnim.Attack && e.AnimT < asset.Duration("attack")) { role = "attack"; t = e.AnimT; }
                // Knocked back: staggered off the blow, its feet carried by the clip, until the stagger is done.
                else if (g.KnockAt >= 0 && time - g.KnockAt < asset.Duration("hit")) { role = "hit"; t = time - g.KnockAt; }
                else if (g.Walking)
                {
                    // Its own walk clock, run faster or slower with its pace:
                    // time times pace would leap to a new pose at every change of speed.
                    // A walk whose pace is known keeps its feet on the ground at any size and speed.
                    // (a share of a varied pack walks its kind's second gait, the other hand reaching: Vary.Second)
                    role = battle?.VaryPacks == true && asset.Clips.ContainsKey("move2") && Vary.Second(e.Seed, 0.45) ? "move2" : "move";
                    double size = (e.Def.Scale ?? 1) * Beasts.Size(e.Def.Visual) * Vary.Size(e.Seed, e.Def.Size ?? 0);
                    // (shoved against its facing, its steps run backward: it is pushed back a step, it does not moonwalk)
                    g.Back = speed < 0.2 && g.DrawnSpeed > 0.2 && Math.Abs(Wrap(Math.Atan2(g.DVz, g.DVx) - g.Facing)) > Math.PI * (g.Back ? 0.45 : 0.61);
                    g.Phase += (g.Back ? -dt : dt) * (asset.Pace > 0
                        ? Math.Clamp(moving / (asset.Pace * size), 0.5, 1.8)
                        : Math.Clamp(moving / Math.Max(0.5, e.Def.Speed), 0.6, 1.6));
                    t = g.Phase;
                }
                else { role = "idle"; t = time + e.Seed * 9; }
                break;
        }
        // Turned toward where it is going when it walks, toward what it wants
        // when it stands or strikes; never in a single frame.
        bool free = e.State == EnemyState.Active && e.Anim != EnemyAnim.Attack;
        // (shoved and walking with it: toward where it is carried, or, carried back, still facing what it wants)
        double aim = !(g.Walking && free) ? e.Facing
            : speed >= 0.2 || g.DrawnSpeed < 0.2 ? (speed > 1e-6 ? Math.Atan2(e.Vz, e.Vx) : e.Facing)
            : g.Back ? e.Facing : Math.Atan2(g.DVz, g.DVx);
        if (e.State != EnemyState.Dying)
        {
            double turn = Math.Atan2(Math.Sin(aim - g.Facing), Math.Cos(aim - g.Facing));
            g.Facing += turn * Math.Min(1, dt * (free ? 9 : 18));
        }
        // Gone along under the ground by its script (Grimtunnel's Under): drawn burrowing, as the
        // burrowed are (its back, hat and lamp above the earth), while the effects heave the mound.
        // (each copy of a many-at-once kind its own size: EnemyDef.Size, Sim.Vary)
        float sc = (float)((e.Def.Scale ?? 1) * Vary.Size(e.Seed, e.Def.Size ?? 0)) * Beasts.Size(e.Def.Visual);
        // (Sunk by its size: at a lampling's quarter metre a foreman of twice its size still walked
        // the dirt whole.)
        if (e.State == EnemyState.Active && Under?.Invoke(e) == true) { role = "burrow"; y -= 0.25 + 0.32 * Math.Max(0, sc - 1); t = time + e.Seed * 3; }
        if (Staged?.Invoke(e) is var (stSink, stRole, stT, stFace))
        {
            y -= stSink;
            if (stFace is double fc) g.Facing = fc;
            if (stRole != null && e.State == EnemyState.Active && asset.Clips.ContainsKey(stRole)) { role = stRole; t = stT; }
        }
        // Struck: a squash, and a flinch along the blow, gone with the flash.
        float f = e.State == EnemyState.Dying ? 0 : (FlashHeld?.Invoke(e.Id) ?? (float)e.Flash) * (1 - Still);
        // The struck flare's instant of white across the whole body is for a few at once, and two
        // champions besides (any ruler always); the rest keep it at the rim. A blast that hits sixty
        // at once turned sixty bodies white in the same frame.
        // The flinch keeps the whole blow; only the light is held back (a crowd's struck all read by
        // their flinch, a few by their flare).
        float flare = f;
        // A tick of a burn or a poison is no blow: a breath at the rim, no white and no flinch. (Burning
        // ground's ticks turned three bodies a frame into white cut-outs, over and over.)
        if (e.LastDot && !e.Boss) { flare = Math.Min(f, FlashRimOnly); f *= 0.2f; }
        else if (f > FlashRimOnly && !e.Boss && e.Named == null
            && (e.Elite ? ++eliteFlashes > EliteFlashes : ++whiteFlashes > WhiteFlashes)) flare = FlashRimOnly;
        // The flinch along the blow: big enough to read from thirty metres up, twice on a critical (S-17).
        float push = e.LastCrit ? 0.45f : 0.25f;
        var at = new Vector3((float)(ex + e.LastDx * f * push), (float)y, (float)(ez + e.LastDz * f * push));
        var basis = new Godot.Basis(Vector3.Up, (float)(Math.PI / 2 - g.Facing)) * Godot.Basis.FromScale(new Vector3(sc * (1 + f * 0.1f), sc * (1 - f * 0.1f), sc * (1 + f * 0.1f)));
        // (a falling body comes down onto the slope it will lie on: THE CORPSE REST RULE, eased in as it goes down)
        if (e.State == EnemyState.Dying && e.Disposition != Disposition.Ally)
        {
            float w = Smooth(e.DieT, Ai.DieTime * 0.3, Ai.DieTime - 0.12);
            if (w > 0) basis = Godot.Basis.Identity.Slerp(RestTilt(heightAt, ex, ez, FallHeading(asset, role, g.Facing), sc), w) * basis;
        }
        // (Held by a ground that is not the cold, a thicket's or a rot's: its slow is no rime.)
        bool held = battle != null && e.HeldUntil > battle.Time;
        float frozen = e.Status.Has(StatusKind.Frozen) ? 1 : !held && e.Status[StatusKind.Chill] is { } chill ? (float)Math.Min(0.5, chill.Stacks * 0.09) : 0;
        float burning = e.Status.Has(StatusKind.Burn) ? 1 - 0.8f * Still : 0;
        var (tint, glow) = TintOf(e);
        float chr = e.State == EnemyState.Dying ? g.Char : FlareChar?.Invoke(ex, ez, true) ?? 0;
        tint = Charred(tint, chr);
        Audit(ex, ez, chr, frozen);
        if (e.State != EnemyState.Dying) { g.LastRole = role; g.LastT = t; }
        if (CensusOn) CensusWalker(e, g, asset, role, t, ex, ez);
        g.LastState = e.State; g.LastX = ex; g.LastZ = ez; g.HasLast = true;
        if (fallBurn.W > 0 || fallBurn.Z > 0) { dissolve = Math.Max(dissolve, fallBurn.Z); burning = fallBurn.W; frozen = fallBurn.X; }
        var hk = StruckRim?.Invoke(e.Id) ?? new Vector2(-1, 0);
        if (hk.X >= 0) flare = hk.X;
        crowd.Push(KeyOf(e), new Transform3D(basis, at), role, t, flare, dissolve, frozen, burning, tint, glow, e.LastCrit && !e.LastDot && hk.X < 0, hk.X >= 0 ? Math.Max(hk.Y, 0.001f) : 0);
        living++;
    }

    (Color, float) TintOf(Enemy e)
    {
        var (tint, glow) = Visuals.Tint(e.Def.Visual);
        // A kind's own colour on a shared rig, and a champion's Signs (combat's, agreed with animation).
        if (e.Def.Tint is var (tr, tg, tb)) tint *= new Color((float)tr, (float)tg, (float)tb);
        if (e.Def.Glow is { } dg) glow = Math.Max(glow, (float)dg);
        if (e.Elite) { glow = Math.Max(glow, 0.05f); tint *= new Color(1.08f, 1.02f, 0.92f); }
        // A nemesis (one that took a hero before) burns with it; a ruler, herald or named foe is
        // itself, lifted only a little: painted orange, Greymuzzle was not an old grey wolf.
        if (e.Named is { } nm)
        {
            if (nm.SourceHero != "") { glow = 0.25f; tint *= new Color(1.3f, 0.75f, 0.6f); }
            else glow = Math.Max(glow, 0.06f);
        }
        if (e.Disposition == Disposition.Neutral && !e.Provoked) tint *= new Color(0.95f, 0.95f, 0.95f);
        // A varied pack's copy (the Low Ford's risen): its own skin value (0.35 to 1: NPC 18 r3, not a crowd of bone-white
        // bodies at night; the drowned woman, painted darker, 0.9 to 1: lower sank her to one dark blob out of firelight) and, for about a third, a coat of river mud: a
        // little browner all over and dark patches over the legs and hem (vat.gdshaderinc's mud, flagged by a negative red
        // in the tint: a uniform tint alone read as no mud at all).
        if (battle?.VaryPacks == true && e.Def.Weave is > 0)
        {
            var (val, mud) = Vary.Coat(e.Seed, Vary.Body(e.Def.Visual, e.Seed) == e.Def.Visual ? 0.35 : 0.9, 0.3);
            tint *= new Color((float)val, (float)val, (float)val);
            if (mud) { tint *= new Color(0.9f, 0.84f, 0.76f); tint.R = -tint.R; }
        }
        return (tint, glow);
    }

    /// <summary>The Flare's statues: each until it shatters; let go unbroken (the Flare ended), it lies where it stood.</summary>
    void DrawStatues(Func<double, double, double> heightAt)
    {
        if (statues.Count == 0) return;
        List<long>? gone = null;
        foreach (var st in statues.Values)
        {
            int says = FlareDeath?.Invoke(st.Id) ?? 0;
            if (says <= 0)
            {
                (gone ??= new()).Add(st.Key);
                if (says == 0 && !(battle != null && st.Id < battle.Enemies.Items.Length && battle.Enemies.Items[st.Id].Alive))
                    corpses.Add(new Corpse(st.Key, st.Visual, Crowd(st.Visual).Asset.Clips.ContainsKey("die") ? "die" : st.Role, st.X, st.Z, st.Facing, st.Scale, st.Tint, st.Glow * 0.3f, time) { Char = FlareChar?.Invoke(st.X, st.Z, false) ?? 0 });
                continue;
            }
            var basis = new Godot.Basis(Vector3.Up, Mathf.Pi / 2 - st.Facing) * Godot.Basis.FromScale(Vector3.One * st.Scale);
            // (A statue still standing where the ring passed 4 frames ago is a body neither shattered nor charred.)
            Audit(st.X, st.Z, 0, 1);
            censusStatue++;
            var lk = FlareStatueLook?.Invoke(st.Id) ?? new Godot.Vector4(1, 0, 0, 0);
            Crowd(st.Visual).Push(st.Key, new Transform3D(basis, new Vector3(st.X, (float)heightAt(st.X, st.Z), st.Z)), st.Role, st.T, FlareStatueFlash?.Invoke(st.Id) ?? 0, lk.Z, lk.X, lk.W, Charred(st.Tint, lk.Y), st.Glow);

        }
        if (gone != null) foreach (var k in gone) statues.Remove(k);
    }

    static float Smooth(double x, double lo, double hi)
    {
        double k = Math.Clamp((x - lo) / (hi - lo), 0, 1);
        return (float)(k * k * (3 - 2 * k));
    }

    /// <summary>The body stays where it fell when the fight lets it go.</summary>
    void LayOut(Enemy e, double x, double z, double facing, string role, float charred = 0)
    {
        if (!laidOut.Add((e.Id, e.Seed))) return;
        var (tint, glow) = Visuals.Tint(e.Def.Visual);
        if (e.Def.Tint is var (tr, tg, tb)) tint *= new Color((float)tr, (float)tg, (float)tb);
        if (e.Def.Glow is { } dg) glow = Math.Max(glow, (float)dg);
        corpses.Add(new Corpse(KeyOf(e), Vary.Body(e.Def.Visual, e.Seed), role, (float)x, (float)z, (float)facing, (float)((e.Def.Scale ?? 1) * Vary.Size(e.Seed, e.Def.Size ?? 0)) * Beasts.Size(e.Def.Visual), tint, glow * 0.3f, time) { Char = charred, Id = e.Id });
        while (corpses.Count > CorpseMax) corpses.RemoveAt(0);
    }

    /// <summary>How far a body settles as it dissolves (metres at its size).</summary>
    const float SinkDepth = 0.08f;
    /// <summary>The steepest a lying body is tilted to its ground. (20 degrees left the Verge's hillside dead, on 36 degree
    /// slopes, 0.4 m into or over the ground at their far end; past 40 a body would rather roll.)</summary>
    const double TiltMax = 40 * Math.PI / 180;

    /// <summary>Which way a body lying in this death runs from its feet (world heading), or null where it is not known.</summary>
    static double? FallHeading(VatAsset asset, string role, double facing) =>
        asset.FallOff != null && asset.FallOff.TryGetValue(role, out var off) ? facing + off : null;

    /// <summary>The turn that lays a body on the ground's slope under it: the plane through the ground at its feet, at
    /// its far end (1.2 m along its fall at its size) and to either side of its middle; where its fall is not known, the
    /// slope round its middle. At most TiltMax.</summary>
    static Godot.Basis RestTilt(Func<double, double, double> heightAt, double x, double z, double? heading, double scale)
    {
        double y0 = heightAt(x, z), L = 1.2 * scale, wd = 0.3 * scale, h = heading ?? 0;
        double ax = Math.Cos(h), az = Math.Sin(h), bx = -az, bz = ax;
        double along, across;
        if (heading != null)
        {
            along = (heightAt(x + ax * L, z + az * L) - y0) / L;
            double mx = x + ax * L * 0.5, mz = z + az * L * 0.5;
            across = (heightAt(mx + bx * wd, mz + bz * wd) - heightAt(mx - bx * wd, mz - bz * wd)) / (2 * wd);
        }
        else
        {
            double r = 0.5 * scale;
            along = (heightAt(x + ax * r, z + az * r) - heightAt(x - ax * r, z - az * r)) / (2 * r);
            across = (heightAt(x + bx * r, z + bz * r) - heightAt(x - bx * r, z - bz * r)) / (2 * r);
        }
        var n = new Vector3((float)(-(along * ax + across * bx)), 1, (float)(-(along * az + across * bz))).Normalized();
        float ang = Mathf.Acos(Math.Clamp(n.Y, -1, 1));
        if (ang < 1e-4f) return Godot.Basis.Identity;
        var axis = Vector3.Up.Cross(n).Normalized();
        return new Godot.Basis(axis, Math.Min(ang, (float)TiltMax));
    }

    static readonly bool DbgNoCorpses = SurvivorUnchained.Args.Has("dbg-no-corpses");
    void DrawCorpses(Func<double, double, double> heightAt)
    {
        double lie = CorpseLieCrowded + (CorpseLie - CorpseLieCrowded) * Math.Clamp(1 - (corpses.Count - 30) / 70.0, 0, 1);
        corpses.RemoveAll(c => time - c.Born >= lie + CorpseSink);
        // The Long Cut burns up the dead in its reach with the struck, and they are gone after: those down when it came,
        // and those still falling then (her kills just before the press lie down after it: the hold slows their fall),
        // as they land, up to 2.5 s after its moment. (The first try asked only the already-down: the star stayed.)
        if (FlareCorpseBurn != null)
            corpses.RemoveAll(c =>
            {
                if (c.BurnAt < 0)
                {
                    double k = FlareCorpseBurn(c.X, c.Z);
                    // (on the struck's clock, not restarted as it lands: her kills falling in reach burn as they fall, and one
                    // laid out after its moment had restarted its burn, the lying star at cleave +0.55 s in r3a)
                    if (k >= 0) { c.BurnAt = time - k; c.Ash = FlareCorpseAsh?.Invoke(c.X, c.Z) ?? false; }
                }
                return c.BurnAt >= 0 && time - c.BurnAt >= SurvivorUnchained.View.FlareFx.BurnTimeOf(c.Ash);
            });
        if (DbgNoCorpses) return;
        foreach (var c in corpses)
        {
            var crowd = Crowd(c.Visual);
            double age = time - c.Born;
            // THE CORPSE REST RULE: it lies on the ground's slope under it (RestTilt, once: the ground does not move), and
            // is taken back where it lies, dissolving over CorpseSink and settling a few centimetres with it (it slid 1.1 m
            // down through the floor: the night arena's dead were seen sinking).
            float sink = Smooth(age, lie, lie + CorpseSink);
            if (!c.Tilted)
            {
                c.Tilt = RestTilt(heightAt, c.X, c.Z, FallHeading(crowd.Asset, c.Role, c.Facing), c.Scale); c.Tilted = true;
            }
            var at = new Vector3(c.X, (float)heightAt(c.X, c.Z) - sink * SinkDepth * c.Scale, c.Z);
            var basis = c.Tilt * new Godot.Basis(Vector3.Up, Mathf.Pi / 2 - c.Facing) * Godot.Basis.FromScale(Vector3.One * c.Scale);
            // The dead go dark and a little cold as soon as they are down, so the living read
            // at a glance against them (the risen are pale: a body the same grey as the walking
            // ones made the horde twice its size). Then they darken on as they lie.
            float k = 1 - 0.5f * Smooth(age, 0.3, 1.3) - 0.15f * Smooth(age, 1.3, lie);
            if (FlareChar != null) c.Char = Math.Max(c.Char, FlareChar(c.X, c.Z, false));
            var tint = Charred(c.Tint * new Color(k * 0.88f, k * 0.92f, k, 1), c.Char);
            tint.A = 1;
            Audit(c.X, c.Z, c.Char);
            censusCorpse++;
            if (CensusOn && crowd.Asset.FallOff != null && crowd.Asset.FallOff.TryGetValue(c.Role, out var coff))
            {
                // The ground at the body's far end against the body drawn there (its basis carries any tilt).
                double h = c.Facing + coff, L = 1.2 * c.Scale;
                var flat = new Vector3((float)(Math.Cos(h) * L), 0, (float)(Math.Sin(h) * L));
                var tip = at + new Vector3(0, sink * SinkDepth * c.Scale, 0) + c.Tilt * flat;
                double err = Math.Abs(heightAt(tip.X, tip.Z) - tip.Y);
                cnCorpN++; cnErrSum += err; cnErrMax = Math.Max(cnErrMax, err);
                if (sink > 0) { cnSinking++; cnSinkMax = Math.Max(cnSinkMax, heightAt(c.X, c.Z) - at.Y); }
            }
            if (c.BurnAt >= 0)
            {
                var lk = SurvivorUnchained.View.FlareFx.BurnLook((float)(time - c.BurnAt), c.Ash);
                censusBurn++;
                crowd.Push(c.Key, new Transform3D(basis, at), c.Role, crowd.Asset.Duration(c.Role) * 0.999, 0, Math.Max(lk.Z, sink), lk.X, lk.W, Charred(tint, lk.Y), c.Glow);
                continue;
            }
            crowd.Push(c.Key, new Transform3D(basis, at), c.Role, crowd.Asset.Duration(c.Role) * 0.999, 0, sink, 0, 0, tint, c.Glow, false, c.Id >= 0 && StruckRim?.Invoke(c.Id) is { X: >= 0 } cr ? Math.Max(cr.Y, 0.001f) : 0, c.Id >= 0 && StruckRim?.Invoke(c.Id) is { X: > 0 } cf ? cf.X : 0);
        }
    }

    public override void _ExitTree()
    {
        corpses.Clear();
        gaits.Clear();
    }
}
