using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>
/// P1's body B (tools/body, godot/art/people/body_p1): its rig's drivers and correctives, a line-for-line port of
/// tools/body/rig_drive.py (rig.json "poser"), so the build's checks and the game evaluate the same laws. Pure doubles,
/// no Godot: G are bone worlds (skeleton space, 4x4 row-major, columns the bone's axes, [r,3] its head), the helpers
/// carried at rest; Drive returns the driven worlds and each corrective shape's weight. godot/tests/P1RigTests.cs
/// holds it to rig_drive.drive on tools/body/p1_rig_fixture.py's poses. Derivation: (c) inherited, rig_drive.py.
/// </summary>
public sealed class P1Rig
{
    public readonly string[] Names;
    public readonly int[] Parent;
    public readonly P1M4[] Rest;
    public readonly Dictionary<string, int> Index;
    readonly int[][] subtree;
    readonly JsonElement rig;
    /// <summary>The bones the rig's helper rows set (never keyed: carried at rest before Drive). Not the "unroll" rows'
    /// bones (lowerarm, calf): those are keyed limb bones whose roll the rig moves on to the child.</summary>
    public readonly HashSet<int> Helpers = new();
    /// <summary>rig.json girdle "clavicle_by": "shrug" (P1 R1 arm chain): the girdle law leaves the clavicle alone; it is
    /// the clip's (the map of A's, B's clavicle head and shoulder being A's) lifted at runtime by A's own HerShrug (run on
    /// B by role, where A runs it), so B's arm follows A's through every blend. The scapula's rows still run.</summary>
    public readonly bool ShrugDriven;
    /// <summary>rig.json girdle "clavicle_roll": "neutral" (P1 R1 arm chain round 27): before the scapula's rows the
    /// clavicle is laid on its own line by the least turn from its neutral (its parent's carried rest), the clip's roll
    /// about that line handed to the upper arm, which keeps its world. The clips key A's clavicle (the plain map, so the
    /// game's local-space blends run as A's do and A's HerShrug lifts it as A's) and B's clavicle skin (upper chest,
    /// trapezius) still never takes A's roll.</summary>
    public readonly bool ClavicleRollNeutral;

    public P1Rig(string[] names, int[] parent, P1M4[] rest, JsonElement rig)
    {
        Names = names; Parent = parent; Rest = rest; this.rig = rig; keepBuf = new P1M4[names.Length];
        ShrugDriven = rig.TryGetProperty("girdle", out var g0) && g0.TryGetProperty("clavicle_by", out var cb) && cb.GetString() == "shrug";
        ClavicleRollNeutral = rig.TryGetProperty("girdle", out var g1) && g1.TryGetProperty("clavicle_roll", out var cr) && cr.GetString() == "neutral";
        Index = new Dictionary<string, int>();
        for (int i = 0; i < names.Length; i++) Index[names[i]] = i;
        var children = Enumerable.Range(0, names.Length).Select(j => Enumerable.Range(0, names.Length).Where(k => parent[k] == j).ToArray()).ToArray();
        subtree = new int[names.Length][];
        for (int j = 0; j < names.Length; j++)
        {
            var o = new List<int>(); var st = new Stack<int>(); st.Push(j);
            while (st.Count > 0) { int k = st.Pop(); o.Add(k); foreach (var c in children[k]) st.Push(c); }
            subtree[j] = o.ToArray();
        }
        if (rig.TryGetProperty("helpers", out var hs))
            foreach (var h in hs.EnumerateArray())
                foreach (var s in Sides(h.GetProperty("name").GetString()!))
                    if (h.GetProperty("kind").GetString() != "unroll" && Index.TryGetValue(h.GetProperty("name").GetString()!.Replace("{s}", s), out var j)) Helpers.Add(j);
    }

    static string[] Sides(string text) => text.Contains("{s}") ? new[] { "l", "r" } : new[] { "" };

    // ------------------------------------------------------------- algebra --
    static P1M3 Unit(P1M4 m)
    {
        var r = m.Lin();
        for (int c = 0; c < 3; c++)
        {
            double n = Math.Sqrt(r[0, c] * r[0, c] + r[1, c] * r[1, c] + r[2, c] * r[2, c]);
            for (int i = 0; i < 3; i++) r[i, c] /= n;
        }
        return r;
    }

    static P1V N(P1V v) => v / Math.Max(v.Len(), 1e-12);

    public static P1V RotVec(P1M3 R)
    {
        double c = Math.Clamp((R[0, 0] + R[1, 1] + R[2, 2] - 1) / 2, -1, 1);
        double a = Math.Acos(c);
        if (a < 1e-9) return new P1V(0, 0, 0);
        var v = new P1V(R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]);
        double n = v.Len();
        if (n < 1e-9)
        {
            // (a half turn: the axis is (R + I)'s longest column, eigh's top vector up to its sign)
            P1V best = new(0, 0, 0);
            for (int k = 0; k < 3; k++)
            {
                var col = new P1V(R[0, k] + (k == 0 ? 1 : 0), R[1, k] + (k == 1 ? 1 : 0), R[2, k] + (k == 2 ? 1 : 0));
                if (col.Len() > best.Len()) best = col;
            }
            return N(best) * a;
        }
        return v / n * a;
    }

    public static P1M3 Expm(P1V v)
    {
        double a = v.Len();
        if (a < 1e-12) return P1M3.Id;
        var k = v / a;
        var K = new P1M3(0, -k.Z, k.Y, k.Z, 0, -k.X, -k.Y, k.X, 0);
        return P1M3.Id + K * Math.Sin(a) + (K * K) * (1 - Math.Cos(a));
    }

    static P1M3 Arc(P1V a, P1V b)
    {
        var v = P1V.Cross(a, b);
        double s = v.Len(), c = Math.Clamp(P1V.Dot(a, b), -1, 1);
        if (s < 1e-12) return P1M3.Id;
        return Expm(v / s * Math.Atan2(s, c));
    }

    static double Roll(P1M3 Rd, P1V y)
    {
        var v = RotVec(Rd);
        double a = v.Len();
        if (a < 1e-12) return 0;
        var q = v / a * Math.Sin(a / 2);
        return 2 * Math.Atan2(P1V.Dot(q, y), Math.Cos(a / 2));
    }

    public static double Smooth(double t) { t = Math.Min(Math.Max(t, 0), 1); return t * t * (3 - 2 * t); }

    static P1M4 About(P1V c, P1M3 m) => P1M4.From(m, c - m * c);

    void Apply(P1M4[] G, int j, P1M4 A) { foreach (var k in subtree[j]) G[k] = A * G[k]; }

    P1M3 Turn(P1M4[] G, int j) => Unit(G[j]) * Unit(Rest[j]).T();

    P1M4 Carried(P1M4[] G, int j) { int p = Parent[j]; return G[p] * Rest[p].Inverse() * Rest[j]; }

    static P1V Head(P1M4[] G, int j) => G[j].T();

    P1V ChildHead(P1M4[] G, int j, string? child) => child != null ? G[Index[child]].T() : G[j].T() + Unit(G[j]).Col(1) * 0.1;

    // ------------------------------------------------------------ readings --
    static P1V Vec(JsonElement e) => new(e[0].GetDouble(), e[1].GetDouble(), e[2].GetDouble());
    static string Sub(JsonElement e, string s) => e.GetString()!.Replace("{s}", s);
    static double Num(JsonElement h, string k, double d) => h.TryGetProperty(k, out var v) ? v.GetDouble() : d;
    static double Deg(double r) => r * 180.0 / Math.PI;
    static double Rad(double d) => d * Math.PI / 180.0;

    // Everything the rows read out of rig.json is read once into these records (built lazily on first use, the rig
    // being fixed), so Drive and CorrectiveWeights walk arrays and make no strings per frame. One thread at a time.
    static readonly string[] LR = { "l", "r" };
    static readonly string[] NoSide = { "" };

    /// <summary>One side's girdle readings (rig.json "girdle"): the base for the elevation, the rest on first use of the
    /// girdle rows and of the clavicle law.</summary>
    sealed class GSide
    {
        public double Sg; public int Arm, End, Torso; public P1V Down, Front;
        public bool GirdleReady; public int Cl, Sc; public P1V Side, ScapAxis; public P1Rows ScapUp = null!, ScapTilt = null!; public double GlideM;
        public int[]? RollKeep;
        public bool ClavReady; public P1V Up; public P1Rows ClavElev = null!, ClavRetract = null!; public double Protract; public RetractC? Retract;
    }

    sealed class RetractC { public double F0, F1; public P1Rows ByReach = null!; }

    readonly Dictionary<string, GSide> gsides = new();
    readonly P1M4[] keepBuf;

    GSide Gs(string s)
    {
        if (gsides.TryGetValue(s, out var g)) return g;
        var gd = rig.GetProperty("girdle");
        g = new GSide
        {
            Sg = s == "l" ? 1 : -1,
            Arm = Index[Sub(gd.GetProperty("arm"), s)], End = Index[Sub(gd.GetProperty("arm_end"), s)],
            Torso = Index[gd.GetProperty("torso").GetString()!], Down = Vec(gd.GetProperty("down")), Front = Vec(gd.GetProperty("front")),
        };
        gsides[s] = g;
        return g;
    }

    GSide GirdleOf(string s)
    {
        var g = Gs(s);
        if (g.GirdleReady) return g;
        var gd = rig.GetProperty("girdle");
        g.Cl = Index[Sub(gd.GetProperty("clavicle"), s)]; g.Sc = Index[Sub(gd.GetProperty("scap"), s)];
        g.Side = Vec(gd.GetProperty("side"));
        g.ScapUp = P1Rows.From(gd.GetProperty("scap_up")); g.ScapTilt = P1Rows.From(gd.GetProperty("scap_tilt"));
        g.ScapAxis = Vec(gd.GetProperty("scap_axis"));
        g.GlideM = gd.GetProperty("glide_m").GetDouble();
        if (gd.TryGetProperty("clavicle_roll_keep", out var rk))
        {
            var l = new List<int>();
            foreach (var e in rk.EnumerateArray())
                if (Index.TryGetValue(e.GetString()!.Replace("{s}", s), out var j)) l.Add(j);
            g.RollKeep = l.ToArray();
        }
        g.GirdleReady = true;
        return g;
    }

    GSide ClavOf(string s)
    {
        var g = Gs(s);
        if (g.ClavReady) return g;
        var gd = rig.GetProperty("girdle");
        g.Up = Vec(gd.GetProperty("up"));
        g.ClavElev = P1Rows.From(gd.GetProperty("clav_elev")); g.ClavRetract = P1Rows.From(gd.GetProperty("clav_retract"));
        g.Protract = gd.GetProperty("protract_per_reach").GetDouble();
        if (gd.TryGetProperty("retract_plane", out var rp))
        {
            var fd = rp.GetProperty("fade");
            g.Retract = new RetractC { F0 = fd[0].GetDouble(), F1 = fd[1].GetDouble(), ByReach = P1Rows.From(rp.GetProperty("by_reach")) };
        }
        g.ClavReady = true;
        return g;
    }

    double Elevation(P1M4[] G, GSide gs)
    {
        int j = gs.Arm, c = gs.End;
        var down = Turn(G, gs.Torso) * gs.Down;
        var d = N(Head(G, c) - Head(G, j));
        return Deg(Math.Acos(Math.Clamp(P1V.Dot(d, down), -1, 1)));
    }

    double Flexion(P1M4[] G, string prox, string joint, string dist)
    {
        var u = N(Head(G, Index[joint]) - Head(G, Index[prox]));
        var d = N(Head(G, Index[dist]) - Head(G, Index[joint]));
        return Deg(Math.Acos(Math.Clamp(P1V.Dot(u, d), -1, 1)));
    }

    P1V Direction(P1M4[] G, string bone, string end, string frame)
    {
        var d = N(Head(G, Index[end]) - Head(G, Index[bone]));
        return Turn(G, Index[frame]).T() * d;
    }

    // ------------------------------------------------------------- helpers --
    /// <summary>rig_drive.table: a table's monotone C1 curve at x (Hermite cubics, Fritsch-Butland slopes, 0 slope at
    /// the end nodes, held flat past them).</summary>
    public static double Table(double x, JsonElement T) => Table(x, P1Rows.From(T));

    /// <summary>Table over rows read once (P1Rows.From): the same arithmetic as Table(x, JsonElement).</summary>
    public static double Table(double x, P1Rows r)
    {
        int n = r.N;
        if (x <= r.X[0]) return r.Y[0];
        if (x >= r.X[n - 1]) return r.Y[n - 1];
        int i = 0;
        while (x > r.X[i + 1]) i++;
        double t = (x - r.X[i]) / r.H[i], t2 = t * t, t3 = t2 * t;
        return (2 * t3 - 3 * t2 + 1) * r.Y[i] + (t3 - 2 * t2 + t) * r.H[i] * r.M[i] + (-2 * t3 + 3 * t2) * r.Y[i + 1]
            + (t3 - t2) * r.H[i] * r.M[i + 1];
    }

    /// <summary>rig_drive.retract_plane: the retraction table's scale by the arm's forward reach beyond the rest
    /// ("by_reach" table), faded in over the elevation band "fade" (1 below it).</summary>
    public static double RetractPlane(double A, double reach, JsonElement gd)
    {
        if (!gd.TryGetProperty("retract_plane", out var rp)) return 1.0;
        var fd = rp.GetProperty("fade");
        double g = Smooth((A - fd[0].GetDouble()) / (fd[1].GetDouble() - fd[0].GetDouble()));
        if (g <= 0) return 1.0;
        return 1.0 + g * (Table(reach, rp.GetProperty("by_reach")) - 1.0);
    }

    static double RetractPlane(double A, double reach, RetractC? rp)
    {
        if (rp == null) return 1.0;
        double g = Smooth((A - rp.F0) / (rp.F1 - rp.F0));
        if (g <= 0) return 1.0;
        return 1.0 + g * (Table(reach, rp.ByReach) - 1.0);
    }

    /// <summary>rig_drive.share_amount: `amount` above the rest elevation, below.amount under it, smoothstep-blended
    /// over A0 -+ band.</summary>
    public static double ShareAmount(JsonElement h, double? A, double? A0)
    {
        double a = Num(h, "amount", 0);
        if (!h.TryGetProperty("below", out var b) || A is not double av || A0 is not double a0) return a;
        double band = b.GetProperty("band").GetDouble(), ab = b.GetProperty("amount").GetDouble();
        return ShareAmount(a, band, ab, av, a0);
    }

    static double ShareAmount(double a, double band, double ab, double? A, double? A0)
    {
        if (A is not double av || A0 is not double a0) return a;
        double t = Smooth((av - (a0 - band)) / (2.0 * band));
        return ab + t * (a - ab);
    }

    /// <summary>The world turn the girdle law lays on clavicle_{s} about its head for this pose (null: none). Read from the
    /// torso's turn and the upper arm's direction only, so the clavicle's own pose doesn't change it (the clip bridge
    /// keys the clavicle under it: P1Bake.Hold).</summary>
    public P1M3? ClavicleTurn(P1M4[] G, string s)
    {
        if (ShrugDriven) return null;
        return ClavicleTurn(G, ClavOf(s));
    }

    P1M3? ClavicleTurn(P1M4[] G, GSide gs)
    {
        double sg = gs.Sg;
        int arm = gs.Arm, end = gs.End;
        double A = Elevation(G, gs), A0 = Elevation(Rest, gs);
        var Rt = Turn(G, gs.Torso);
        var front = Rt * gs.Front;
        var up = Rt * gs.Up;
        var d = N(Head(G, end) - Head(G, arm));
        var d0 = N(Head(Rest, end) - Head(Rest, arm));
        double reach = P1V.Dot(d, front) - P1V.Dot(Rt * d0, front);
        double the = Table(A, gs.ClavElev) - Table(A0, gs.ClavElev);
        double thr = RetractPlane(A, reach, gs.Retract) * (Table(A, gs.ClavRetract) - Table(A0, gs.ClavRetract))
            - gs.Protract * reach;
        if (Math.Abs(the) <= 1e-9 && Math.Abs(thr) <= 1e-9) return null;
        return Expm(up * (sg * Rad(thr))) * Expm(front * (sg * Rad(the)));
    }

    /// <summary>rig_drive.girdle: the scapulohumeral rhythm by tables of the arm's elevation and its forward reach,
    /// relative to the rest.</summary>
    double Girdle(P1M4[] G, string s)
    {
        var R0 = Rest;
        var gs = GirdleOf(s);
        double sg = gs.Sg;
        int cl = gs.Cl, sc = gs.Sc, arm = gs.Arm;
        int end = gs.End;
        double A = Elevation(G, gs), A0 = Elevation(R0, gs);
        var Rt = Turn(G, gs.Torso);
        var front = Rt * gs.Front;
        var side = Rt * gs.Side;
        var d = N(Head(G, end) - Head(G, arm));
        var d0 = N(Head(R0, end) - Head(R0, arm));
        double reach = P1V.Dot(d, front) - P1V.Dot(Rt * d0, front);
        var armOld = G[arm];
        if (!ShrugDriven && ClavicleTurn(G, ClavOf(s)) is P1M3 Rc)
        {
            Apply(G, cl, About(Head(G, cl), Rc));
            // the upper arm keeps its world turn (the clip's aim), riding the moved clavicle
            var nw = armOld.WithT(G[arm].T());
            Apply(G, arm, nw * G[arm].Inverse());
        }
        if (ClavicleRollNeutral)
        {
            // the clavicle's roll about its own line (y, its head to the shoulder) beyond its neutral handed to the upper
            // arm: the line is kept, the upper arm's subtree keeps its world, the scapula and the share helper ride it
            var y = Unit(G[cl]).Col(1);
            double ang = Roll(Turn(G, cl) * Turn(G, Parent[cl]).T(), y);
            if (Math.Abs(ang) >= 1e-12)
            {
                // (P1 R1 round 30) girdle "clavicle_roll_keep": helpers under the clavicle that keep the clip's roll
                // (their world kept): the trapezius, A's top of the shoulder riding A's clavicle roll (rig_drive.girdle)
                var sub = subtree[arm];
                foreach (var k in sub) keepBuf[k] = G[k];
                if (gs.RollKeep != null) foreach (var k in gs.RollKeep) keepBuf[k] = G[k];
                Apply(G, cl, About(Head(G, cl), Expm(y * -ang)));
                foreach (var k in sub) G[k] = keepBuf[k];
                if (gs.RollKeep != null) foreach (var k in gs.RollKeep) G[k] = keepBuf[k];
            }
        }
        double thu = Table(A, gs.ScapUp) - Table(A0, gs.ScapUp);
        double thp = Table(A, gs.ScapTilt) - Table(A0, gs.ScapTilt);
        if (Math.Abs(thu) > 1e-9 || Math.Abs(thp) > 1e-9)
        {
            var ax = gs.ScapAxis;
            var n = Rt * N(new P1V(ax.X * sg, ax.Y, ax.Z));
            var Rs = Expm(side * (-Rad(thp))) * Expm(n * (sg * Rad(thu)));
            Apply(G, sc, About(Head(G, sc), Rs));
        }
        double glide = gs.GlideM * reach;
        if (Math.Abs(glide) > 1e-12) Apply(G, sc, P1M4.From(P1M3.Id, front * glide));
        return A;
    }

    P1M3 RelTurn(P1M4[] G, int j, int p) => Turn(G, p).T() * Turn(G, j);

    enum HK { Unroll, Aim, CounterTwist, Twist, Share, Point, Unknown }

    /// <summary>One helper row for one side (rig.json "helpers"), read once. J &lt; 0: the bone is absent, the row is skipped.</summary>
    sealed class HelperC
    {
        public int J = -1, SideIdx = -1; public bool Left; public HK Kind; public string KindName = "";
        public int Ch, On, F;
        public bool ReadHip; public int HipTorso; public P1V HipDown; public string HipEnd = "";
        public double Ar0, Ar1; public string? OnEnd; public double AimM, Turn, Sp, Sa; public bool HasOff; public P1V Off;
        public bool HasBelow; public double Amount, Band, Ab;
        public double Crease, Pivot, Bulge, BulgeMax, TurnPivot;
        public string F0 = "", F1 = "", F2 = ""; public double From, To, Push;
    }

    HelperC[]? helperList;

    HelperC[] BuildHelpers()
    {
        var list = new List<HelperC>();
        if (rig.TryGetProperty("helpers", out var hs))
            foreach (var h in hs.EnumerateArray())
                foreach (var s in Sides(h.GetProperty("name").GetString()!))
                    list.Add(BuildHelper(h, s));
        return helperList = list.ToArray();
    }

    HelperC BuildHelper(JsonElement h, string s)
    {
        var c = new HelperC { Left = s == "l", SideIdx = s == "l" ? 0 : s == "r" ? 1 : -1 };
        if (!Index.TryGetValue(Sub(h.GetProperty("name"), s), out int j)) return c;
        c.J = j;
        var kind = h.GetProperty("kind").GetString();
        c.KindName = kind ?? "";
        if (kind == "unroll") { c.Kind = HK.Unroll; c.Ch = Index[Sub(h.GetProperty("child"), s)]; return c; }
        if (kind == "aim")
        {
            c.Kind = HK.Aim;
            c.On = Index[Sub(h.GetProperty("on"), s)];
            if (h.TryGetProperty("read", out var rd) && rd.GetString() == "hip")
            {
                c.ReadHip = true;
                c.HipTorso = Index[h.GetProperty("torso").GetString()!];
                c.HipDown = Vec(h.GetProperty("down"));
                c.HipEnd = Sub(h.GetProperty("on_end"), s);
            }
            var Ar = h.GetProperty("A");
            c.Ar0 = Ar[0].GetDouble(); c.Ar1 = Ar[1].GetDouble();
            c.OnEnd = h.TryGetProperty("on_end", out var oe) && Sub(oe, s) is { Length: > 0 } oes ? oes : null;
            c.AimM = Num(h, "aim_m", 0);
            c.Turn = Num(h, "turn", 0); c.Sp = Num(h, "sp", 0); c.Sa = Num(h, "sa", 0);
            if (h.TryGetProperty("off", out var off)) { c.HasOff = true; c.Off = Vec(off); }
            return c;
        }
        c.F = Index[Sub(h.GetProperty("follow"), s)];
        c.HasBelow = h.TryGetProperty("below", out var b);
        c.Amount = Num(h, "amount", 0);
        if (c.HasBelow) { c.Band = b.GetProperty("band").GetDouble(); c.Ab = b.GetProperty("amount").GetDouble(); }
        if (kind is "counter_twist" or "twist") { c.Kind = kind == "twist" ? HK.Twist : HK.CounterTwist; return c; }
        if (kind is "share" or "point")
        {
            c.Kind = kind == "point" ? HK.Point : HK.Share;
            c.Crease = Num(h, "crease", 1); c.Pivot = Num(h, "pivot", 0); c.Bulge = Num(h, "bulge", 0);
            c.BulgeMax = Num(h, "bulge_max", 1); c.TurnPivot = Num(h, "turn_pivot", 0);
            if (kind == "point")
            {
                var fl = h.GetProperty("flex");
                c.F0 = Sub(fl[0], s); c.F1 = Sub(fl[1], s); c.F2 = Sub(fl[2], s);
                c.From = h.GetProperty("from").GetDouble(); c.To = h.GetProperty("to").GetDouble(); c.Push = h.GetProperty("push").GetDouble();
            }
            return c;
        }
        c.Kind = HK.Unknown;
        return c;
    }

    // the girdle's A and the rest's A0 per side ("l", "r") for the helper rows; null without the girdle
    readonly double?[] infoA = new double?[2], infoA0 = new double?[2];

    void Helper(P1M4[] G, HelperC h)
    {
        var R0 = Rest;
        if (h.J < 0) return;
        int j = h.J;
        var kind = h.Kind;
        double? infA = h.SideIdx >= 0 ? infoA[h.SideIdx] : null, infA0 = h.SideIdx >= 0 ? infoA0[h.SideIdx] : null;
        if (kind == HK.Unroll)
        {
            int ch = h.Ch;
            int p = Parent[j];
            var y = Unit(G[j]).Col(1);
            double ang = Roll(Turn(G, j) * Turn(G, p).T(), y);
            if (Math.Abs(ang) < 1e-12) return;
            var sub = subtree[ch];
            foreach (var k in sub) keepBuf[k] = G[k];
            Apply(G, j, About(Head(G, j), Expm(y * -ang)));
            foreach (var k in sub) G[k] = keepBuf[k];
            return;
        }
        if (kind == HK.Aim)
        {
            int p = Parent[j];
            int on = h.On;
            double? A = infA;
            if (h.ReadHip) A = FlexionFromDown(G, on, h);
            double g = A is double a ? Smooth((a - h.Ar0) / (h.Ar1 - h.Ar0)) : 0;
            if (g <= 0) return;
            var Gc = G[j];
            var hj = Head(G, j);
            string? onEnd = h.OnEnd;
            double aimM = h.AimM;
            var end = ChildHead(G, on, onEnd);
            var aim = Head(G, on) + N(end - Head(G, on)) * aimM;
            // the same aim at rest, carried by the helper's parent: its swing since rest
            var end0 = ChildHead(R0, on, onEnd);
            var aim0 = Head(R0, on) + N(end0 - Head(R0, on)) * aimM;
            var Cp = G[p] * R0[p].Inverse();
            var aim0w = Cp * aim0;
            var Rsw = Arc(N(aim0w - hj), N(aim - hj));
            var R = Expm(RotVec(Rsw) * (g * h.Turn));
            var y = R * Unit(Gc).Col(1);
            double sp = h.Sp, sa = h.Sa;
            var Sc = P1M3.Id * (1 + g * sp) + P1M3.Outer(y, y) * (g * (sa - sp));
            var M = About(hj, Sc * R);
            var o = h.HasOff ? h.Off * g : new P1V(0, 0, 0);
            o = new P1V(o.X * (h.Left ? 1 : -1), o.Y, o.Z);
            M = M.WithT(M.T() + Cp.Lin() * o);
            G[j] = M * Gc;
            return;
        }
        int f = h.F;
        int pj = Parent[j];
        double amt = h.HasBelow ? ShareAmount(h.Amount, h.Band, h.Ab, infA, infA0) : h.Amount;
        if (kind is HK.CounterTwist or HK.Twist)
        {
            var y = Unit(G[j]).Col(1);
            double ang = kind == HK.CounterTwist
                ? -amt * Roll(Turn(G, f) * Turn(G, Parent[f]).T(), y)
                : amt * Roll(Turn(G, f) * Turn(G, pj).T(), y);
            if (Math.Abs(ang) > 1e-12) Apply(G, j, About(Head(G, j), Expm(y * ang)));
            return;
        }
        if (kind is HK.Share or HK.Point)
        {
            var Gc = Carried(G, j);                  // the share as its parent carries it
            G[j] = Gc;
            var Rp = Turn(G, pj);
            var Rrel = RelTurn(G, f, pj);
            var rv = RotVec(Rrel);
            var Rh = Rp * Expm(rv * amt) * Rp.T();     // the half turn, in the world
            var z = Rp * (Unit(R0[f]).Col(2) * h.Crease);
            var c = Head(G, j) + z * h.Pivot;
            double b = Deg(rv.Len());
            double k = Math.Min(1 + h.Bulge * (1 - Math.Cos(Rad(Math.Min(b, 180)) / 2)), h.BulgeMax);
            var zz = Rh * z;
            var Sw = P1M3.Id + P1M3.Outer(zz, zz) * (k - 1);
            var tp = Head(G, j) + z * h.TurnPivot;
            var M = About(c, Sw) * About(tp, Rh);
            if (kind == HK.Point)
            {
                double F = Flexion(G, h.F0, h.F1, h.F2);
                double push = h.Push * Smooth((F - h.From) / (h.To - h.From));
                M = M.WithT(M.T() - zz * push);
            }
            G[j] = M * Gc;
            return;
        }
        throw new ArgumentException($"unknown helper kind {h.KindName}");
    }

    double FlexionFromDown(P1M4[] G, int on, HelperC h)
    {
        var down = Turn(G, h.HipTorso) * h.HipDown;
        int end = Index[h.HipEnd];
        var d = N(Head(G, end) - Head(G, on));
        return Deg(Math.Acos(Math.Clamp(P1V.Dot(d, down), -1, 1)));
    }

    // --------------------------------------------------------- correctives --
    public static double[] FlexWeights(double F, IReadOnlyList<double> keys)
    {
        var k = keys as double[] ?? keys.ToArray();
        var w = new double[k.Length];
        FlexInto(F, k, w);
        return w;
    }

    static void FlexInto(double F, double[] keys, double[] w)
    {
        if (F <= keys[0]) w[0] = 1;
        else if (F >= keys[^1]) w[^1] = 1;
        else
        {
            int i = 0;
            while (i + 1 < keys.Length && keys[i + 1] <= F) i++;   // (searchsorted right, minus one)
            double t = Smooth((F - keys[i]) / (keys[i + 1] - keys[i]));
            w[i] = 1 - t; w[i + 1] = t;
        }
    }

    static void RbfPhi(P1V d, P1V[] K, double sigma, double[] o)
    {
        for (int i = 0; i < K.Length; i++)
        {
            double ang = Deg(Math.Acos(Math.Clamp(P1V.Dot(K[i], d), -1, 1)));
            o[i] = Math.Exp(-(ang / sigma) * (ang / sigma));
        }
    }

    static P1V[] Keys(JsonElement k) => k.EnumerateArray().Select(Vec).ToArray();

    static double ArcTh(P1V v, P1V e1, P1V e2) => Deg(Math.Atan2(P1V.Dot(v, e2), P1V.Dot(v, e1)));

    /// <summary>One corrective row for one side (rig.json "correctives"), read once. Law: 0 flex, 1 rbf, 2 arc, 3 legacy.</summary>
    sealed class CorrC
    {
        public int Law;
        public string[] Bones = Array.Empty<string>(); public double[] Keys = Array.Empty<double>(); public double[] W = Array.Empty<double>();
        public string?[] Shapes = Array.Empty<string?>();
        public string Bone = "", End = "", Frame = "";
        public double Sigma; public P1V[] K = Array.Empty<P1V>(); public double[][] M = Array.Empty<double[]>(); public int Ns; public double[] Phi = Array.Empty<double>();
        public P1V ArcA, E1, E2; public double[] Tk = Array.Empty<double>(); public double G0, G1;
        public int J; public string On = "swing"; public string Name = "";
        public bool HasKeys, Sm; public double Lo, At, Hi, From, To;
    }

    CorrC[]? corrList;

    CorrC[] BuildCorrectives()
    {
        var list = new List<CorrC>();
        if (rig.TryGetProperty("correctives", out var cs))
            foreach (var c in cs.EnumerateArray())
            {
                string law = c.TryGetProperty("law", out var l) ? l.GetString() ?? "" : "";
                foreach (var s in c.GetRawText().Contains("{s}") ? LR : NoSide)
                {
                    string sub(string x) => x.Replace("{s}", s);
                    string side = s == "" ? "l" : s;
                    var o = new CorrC();
                    if (law == "flex")
                    {
                        var bones = c.GetProperty("bones").EnumerateArray().Select(b => sub(b.GetString()!)).ToArray();
                        if (bones.Any(b => !Index.ContainsKey(b))) continue;
                        o.Law = 0; o.Bones = bones;
                        o.Keys = c.GetProperty("keys").EnumerateArray().Select(x => x.GetDouble()).ToArray();
                        o.W = new double[o.Keys.Length];
                        o.Shapes = c.GetProperty("shapes").EnumerateArray().Select(nm => nm.ValueKind == JsonValueKind.String ? sub(nm.GetString()!) : null).ToArray();
                    }
                    else if (law is "rbf" or "arc")
                    {
                        if (!Index.ContainsKey(sub(c.GetProperty("bone").GetString()!))) continue;
                        o.Bone = sub(c.GetProperty("bone").GetString()!); o.End = sub(c.GetProperty("end").GetString()!); o.Frame = sub(c.GetProperty("frame").GetString()!);
                        o.K = Keys(c.GetProperty("keys").GetProperty(side));
                        o.Shapes = c.GetProperty("shapes").EnumerateArray().Select(nm => (string?)sub(nm.GetString()!)).ToArray();
                        if (law == "rbf")
                        {
                            o.Law = 1;
                            o.Sigma = c.GetProperty("sigma_deg").GetDouble();
                            o.M = c.GetProperty("M").GetProperty(side).EnumerateArray().Select(r => r.EnumerateArray().Select(x => x.GetDouble()).ToArray()).ToArray();
                            o.Ns = o.M[0].Length;
                            o.W = new double[o.Ns];
                            o.Phi = new double[o.K.Length];
                        }
                        else
                        {
                            o.Law = 2;
                            var gd = c.GetProperty("gate_deg");
                            o.G0 = gd[0].GetDouble(); o.G1 = gd[1].GetDouble();
                            var K = o.K;
                            o.ArcA = N(P1V.Cross(K[0], K[^1]));
                            o.E1 = N(K[0] - o.ArcA * P1V.Dot(K[0], o.ArcA));
                            o.E2 = P1V.Cross(o.ArcA, o.E1);
                            o.Tk = new double[K.Length];
                            for (int i = 0; i < K.Length; i++) o.Tk[i] = ArcTh(K[i], o.E1, o.E2);
                            o.Tk[0] = 0;
                            o.W = new double[K.Length];
                        }
                    }
                    else if (c.TryGetProperty("bone", out var bn) && Index.TryGetValue(sub(bn.GetString()!), out int j))
                    {
                        o.Law = 3; o.J = j;
                        o.On = c.TryGetProperty("on", out var oo) ? oo.GetString()! : "swing";
                        o.Name = sub(c.GetProperty("name").GetString()!);
                        if (c.TryGetProperty("keys", out var k))
                        {
                            o.HasKeys = true; o.Lo = k[0].GetDouble(); o.At = k[1].GetDouble(); o.Hi = k[2].GetDouble();
                        }
                        else
                        {
                            o.From = c.GetProperty("from").GetDouble(); o.To = c.GetProperty("to").GetDouble();
                            o.Sm = !c.TryGetProperty("smoothstep", out var ss) || ss.GetBoolean();
                        }
                    }
                    else continue;
                    list.Add(o);
                }
            }
        return corrList = list.ToArray();
    }

    public Dictionary<string, double> CorrectiveWeights(P1M4[] G)
    {
        var o = new Dictionary<string, double>();
        foreach (var c in corrList ?? BuildCorrectives())
        {
            if (c.Law == 0)
            {
                Array.Clear(c.W);
                FlexInto(Flexion(G, c.Bones[0], c.Bones[1], c.Bones[2]), c.Keys, c.W);
                var w = c.W;
                int i = 0;
                foreach (var nm in c.Shapes)
                {
                    if (nm != null) o[nm] = w[i];
                    i++;
                }
            }
            else if (c.Law is 1 or 2)
            {
                var d = Direction(G, c.Bone, c.End, c.Frame);
                double[] w;
                int off = 0;
                if (c.Law == 1)
                {
                    RbfPhi(d, c.K, c.Sigma, c.Phi);
                    var phi = c.Phi; var M = c.M;
                    w = c.W;
                    for (int q = 0; q < c.Ns; q++)
                    {
                        double acc = 0;
                        for (int r = 0; r < phi.Length; r++) acc += phi[r] * M[r][q];
                        w[q] = Math.Clamp(acc, 0, 1);
                    }
                }
                else
                {
                    w = c.W;
                    Array.Clear(w);
                    FlexInto(ArcTh(d, c.E1, c.E2), c.Tk, w);
                    double beta = Math.Abs(Deg(Math.Asin(Math.Clamp(P1V.Dot(d, c.ArcA), -1, 1))));
                    double gate = 1 - Smooth((beta - c.G0) / (c.G1 - c.G0));
                    for (int i = 1; i < w.Length; i++) w[i] *= gate;
                    off = 1;
                }
                int ix = 0;
                foreach (var nm in c.Shapes)
                {
                    double wi = w[ix + off];
                    o[nm!] = wi < 1e-5 ? 0 : wi;   // exactly 0 at the rest key
                    ix++;
                }
            }
            else o[c.Name] = LegacyWeight(c, AngleOf(G, c.J, c.On));
        }
        return o;
    }

    P1M4 Local(P1M4[] G, int j) { int p = Parent[j]; return p < 0 ? G[j] : G[p].Inverse() * G[j]; }

    double AngleOf(P1M4[] G, int j, string on)
    {
        var R0 = Unit(Local(Rest, j));
        var R1 = Unit(Local(G, j));
        var d = R0.T() * R1;
        if (on == "angle") return Deg(Math.Acos(Math.Clamp((d[0, 0] + d[1, 1] + d[2, 2] - 1) / 2, -1, 1)));
        var y = d.Col(1);
        if (on == "flex") return Deg(Math.Atan2(y.Z, y.Y));
        return Deg(Math.Acos(Math.Clamp(y.Y, -1, 1)));
    }

    static double LegacyWeight(CorrC c, double deg)
    {
        if (c.HasKeys)
        {
            double lo = c.Lo, at = c.At, hi = c.Hi;
            if (deg <= lo) return 0;
            if (deg < at) return (deg - lo) / (at - lo);
            if (hi <= at) return 1;
            return Math.Max(0, 1 - (deg - at) / (hi - at));
        }
        double from = c.From, to = c.To;
        double t = Math.Clamp((deg - from) / (to - from), 0, 1);
        return c.Sm ? t * t * (3 - 2 * t) : t;
    }

    // ------------------------------------------------------- hand clearance --
    /// <summary>rig_drive.grid_at: a [t][theta] table, bilinear; t rows at t0 + i dt (held at the ends), theta bins
    /// centred at -pi + (j + 0.5) 2 pi / n (periodic).</summary>
    public static double GridAt(double[][] D, double t, double th, double t0, double dt)
    {
        int nt = D.Length, nth = D[0].Length;
        double x = Math.Min(Math.Max((t - t0) / dt, 0.0), nt - 1.0);
        int i = Math.Min((int)Math.Floor(x), nt - 2);
        double fx = x - i;
        double y = (th + Math.PI) / (2 * Math.PI) * nth - 0.5;
        int j = (int)Math.Floor(y);
        double fy = y - j;
        int j0 = ((j % nth) + nth) % nth, j1 = (((j + 1) % nth) + nth) % nth;
        return (1 - fx) * ((1 - fy) * D[i][j0] + fy * D[i][j1]) + fx * ((1 - fy) * D[i + 1][j0] + fy * D[i + 1][j1]);
    }

    sealed record HandSide(int Thigh, int Arm, int[] Palm, int[] Points, P1V Axis, P1V E1, P1V E2, double Length, double[][] R, double[][] Dr)
    {
        // per-frame scratch (one slot a point, and the palm)
        public readonly double[] Gs = new double[Points.Length + 1], Drs = new double[Points.Length + 1], W = new double[Points.Length + 1];
        public readonly P1V[] Dirs = new P1V[Points.Length + 1];
    }
    HandSide?[]? hands;
    bool hcRead; double hcT0, hcDt, hcSoft, hcNear, hcFar;

    static double[][] Grid(JsonElement e) => e.EnumerateArray().Select(r => r.EnumerateArray().Select(x => x.GetDouble()).ToArray()).ToArray();

    HandSide? HandOf(JsonElement hc, string s)
    {
        if (!hc.GetProperty("sides").TryGetProperty(s, out var sd)) return null;
        int[] Bones(string key) => hc.GetProperty(key).EnumerateArray().Select(n => n.GetString()!.Replace("{s}", s))
            .Where(Index.ContainsKey).Select(n => Index[n]).ToArray();
        return new HandSide(Index[Sub(hc.GetProperty("thigh"), s)], Index[Sub(hc.GetProperty("arm"), s)], Bones("palm"), Bones("points"),
            Vec(sd.GetProperty("axis")), Vec(sd.GetProperty("e1")), Vec(sd.GetProperty("e2")), sd.GetProperty("length_m").GetDouble(),
            Grid(sd.GetProperty("r")), Grid(sd.GetProperty("dr")));
    }

    /// <summary>rig_drive.hand_clear (rig.json "hand_clear", tools/body/hand_clear.py; absent on the ref body: no
    /// change): the arm opened by the least turn about its head so the palm moves k dr out from the thigh, dr this
    /// body's thigh surface beyond the ref body's, k the hand's proximity to it (the points' soft-minimum gap).</summary>
    void HandClear(P1M4[] G, JsonElement hc, int side)
    {
        hands ??= new[] { HandOf(hc, "l"), HandOf(hc, "r") };
        var h = hands[side];
        if (h == null || h.Palm.Length == 0) return;
        if (!hcRead)
        {
            hcT0 = hc.GetProperty("t0").GetDouble(); hcDt = hc.GetProperty("dt").GetDouble();
            hcSoft = hc.GetProperty("soft_m").GetDouble(); hcNear = hc.GetProperty("near_m").GetDouble(); hcFar = hc.GetProperty("far_m").GetDouble();
            hcRead = true;
        }
        var R = Unit(G[h.Thigh]); var o = Head(G, h.Thigh);
        double t0 = hcT0, dt = hcDt;
        var palm = new P1V(0, 0, 0);
        foreach (var k in h.Palm) palm += Head(G, k);
        palm /= h.Palm.Length;
        var gs = h.Gs; var drs = h.Drs; var dirs = h.Dirs; int cnt = 0;
        int np = h.Points.Length;
        for (int pi = 0; pi <= np; pi++)
        {
            var p = pi < np ? Head(G, h.Points[pi]) : palm;
            var q = R.T() * (p - o);
            var rho = q - h.Axis * P1V.Dot(q, h.Axis);
            double d = rho.Len();
            if (d < 1e-9) continue;
            double t = P1V.Dot(q, h.Axis) / h.Length, ang = Math.Atan2(P1V.Dot(rho, h.E2), P1V.Dot(rho, h.E1));
            double dr = GridAt(h.Dr, t, ang, t0, dt);
            gs[cnt] = d - (GridAt(h.R, t, ang, t0, dt) - dr);
            drs[cnt] = dr;
            dirs[cnt] = R * (rho / d);
            cnt++;
        }
        if (cnt == 0) return;
        double soft = hcSoft, near = hcNear, far = hcFar;
        double gm = gs[0];
        for (int i = 1; i < cnt; i++)
        {
            double v0 = gs[i];
            if (v0 < gm) gm = v0;
            else if (double.IsNaN(v0)) { gm = v0; break; }
        }
        var w = h.W;
        for (int i = 0; i < cnt; i++) w[i] = Math.Exp(-(gs[i] - gm) / soft);
        double sw = 0; for (int i = 0; i < cnt; i++) sw += w[i];
        double gsoft = gm - soft * Math.Log(sw);
        double kp = 1.0 - Smooth((gsoft - near) / (far - near));
        if (kp <= 0.0) return;
        double drm = 0; var dir = new P1V(0, 0, 0);
        for (int i = 0; i < cnt; i++) { drm += w[i] * drs[i]; dir += dirs[i] * w[i]; }
        drm /= sw;
        var v = N(dir) * (kp * drm);
        if (v.Len() < 1e-9) return;
        var c = Head(G, h.Arm);
        var a = palm - c;
        Apply(G, h.Arm, About(c, Arc(N(a), N(a + v))));
    }

    // --------------------------------------------------------------- drive --
    /// <summary>rig_drive.drive: the girdle (per side), the hand clearance (per side, with "hand_clear"), the helper rows in order, then the correctives' weights. The
    /// input array is left as it was.</summary>
    public (P1M4[] G, Dictionary<string, double> Weights) Drive(P1M4[] input)
    {
        var G = (P1M4[])input.Clone();
        if (rig.TryGetProperty("girdle", out _))
            for (int si = 0; si < 2; si++) { var s = LR[si]; infoA[si] = Girdle(G, s); infoA0[si] = Elevation(Rest, Gs(s)); }
        else { infoA[0] = infoA[1] = infoA0[0] = infoA0[1] = null; }
        if (rig.TryGetProperty("hand_clear", out var hc))   // (P1 R1 sliders: after the girdle, before the rows; absent on the ref body)
            for (int side = 0; side < 2; side++) HandClear(G, hc, side);
        foreach (var h in helperList ?? BuildHelpers())
            Helper(G, h);
        return (G, CorrectiveWeights(G));
    }
}

/// <summary>A rig.json table's rows read once (x, y, the Hermite slopes), for P1Rig.Table.</summary>
public sealed class P1Rows
{
    public readonly int N;
    public readonly double[] X, Y, H, M;

    P1Rows(double[] x, double[] y)
    {
        X = x; Y = y; N = x.Length;
        int n = N, n1 = Math.Max(n - 1, 0);
        H = new double[n1]; M = new double[n];
        var dl = new double[n1];
        for (int k = 0; k < n - 1; k++) { H[k] = X[k + 1] - X[k]; dl[k] = (Y[k + 1] - Y[k]) / H[k]; }
        for (int k = 1; k < n - 1; k++)
            if (dl[k - 1] * dl[k] > 0)
            {
                double w1 = 2 * H[k] + H[k - 1], w2 = H[k] + 2 * H[k - 1];
                M[k] = (w1 + w2) / (w1 / dl[k - 1] + w2 / dl[k]);
            }
    }

    public static P1Rows From(JsonElement T)
    {
        var rows = T.EnumerateArray().Select(r => (X: r[0].GetDouble(), Y: r[1].GetDouble())).ToArray();
        return new P1Rows(rows.Select(r => r.X).ToArray(), rows.Select(r => r.Y).ToArray());
    }
}

/// <summary>A 3-vector in doubles.</summary>
public readonly record struct P1V(double X, double Y, double Z)
{
    public static P1V operator +(P1V a, P1V b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    public static P1V operator -(P1V a, P1V b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);
    public static P1V operator *(P1V a, double k) => new(a.X * k, a.Y * k, a.Z * k);
    public static P1V operator /(P1V a, double k) => new(a.X / k, a.Y / k, a.Z / k);
    public static double Dot(P1V a, P1V b) => a.X * b.X + a.Y * b.Y + a.Z * b.Z;
    public static P1V Cross(P1V a, P1V b) => new(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X);
    public double Len() => Math.Sqrt(Dot(this, this));
    public double this[int i] => i == 0 ? X : i == 1 ? Y : Z;
}

/// <summary>Nine doubles inline (P1M3's storage: no array on the heap).</summary>
[System.Runtime.CompilerServices.InlineArray(9)]
public struct P1D9 { double e0; }

/// <summary>Sixteen doubles inline (P1M4's storage).</summary>
[System.Runtime.CompilerServices.InlineArray(16)]
public struct P1D16 { double e0; }

/// <summary>A 3x3 in doubles, row-major. A value (a struct of nine inline doubles, copied on assignment): the rig's
/// per-frame algebra makes no garbage (it was a class over a double[9]: two heap objects a product, about 75 MB/s in
/// play, the main cause of the young collections). Nothing wrote into a matrix it did not just make, so copying
/// rather than sharing changes no number (godot/tests' parity holds bit for bit).</summary>
public struct P1M3
{
    P1D9 a;
    /// <summary>The nine numbers, row-major (a view of this matrix: write through it only on a variable).</summary>
    [System.Diagnostics.CodeAnalysis.UnscopedRef] public Span<double> A => a;
    public P1M3(params double[] v) { for (int i = 0; i < 9; i++) a[i] = v[i]; }
    public P1M3(double a0, double a1, double a2, double a3, double a4, double a5, double a6, double a7, double a8)
    {
        a[0] = a0; a[1] = a1; a[2] = a2; a[3] = a3; a[4] = a4; a[5] = a5; a[6] = a6; a[7] = a7; a[8] = a8;
    }
    public static P1M3 Id => new(1, 0, 0, 0, 1, 0, 0, 0, 1);
    public double this[int r, int c] { readonly get => a[r * 3 + c]; set => a[r * 3 + c] = value; }
    public static P1M3 operator *(P1M3 a, P1M3 b)
    {
        var o = new P1M3();
        for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = a[r, 0] * b[0, c] + a[r, 1] * b[1, c] + a[r, 2] * b[2, c];
        return o;
    }
    public static P1V operator *(P1M3 a, P1V v) => new(a[0, 0] * v.X + a[0, 1] * v.Y + a[0, 2] * v.Z, a[1, 0] * v.X + a[1, 1] * v.Y + a[1, 2] * v.Z, a[2, 0] * v.X + a[2, 1] * v.Y + a[2, 2] * v.Z);
    public static P1M3 operator *(P1M3 a, double k) { var o = new P1M3(); for (int i = 0; i < 9; i++) o.a[i] = a.a[i] * k; return o; }
    public static P1M3 operator +(P1M3 a, P1M3 b) { var o = new P1M3(); for (int i = 0; i < 9; i++) o.a[i] = a.a[i] + b.a[i]; return o; }
    public readonly P1M3 T() { var o = new P1M3(); for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = this[c, r]; return o; }
    public readonly P1V Col(int c) => new(this[0, c], this[1, c], this[2, c]);
    public static P1M3 Outer(P1V a, P1V b) { var o = new P1M3(); for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = a[r] * b[c]; return o; }
}

/// <summary>A 4x4 affine in doubles, row-major ([r,3] the translation). A value, as P1M3.</summary>
public struct P1M4
{
    P1D16 a;
    /// <summary>The sixteen numbers, row-major (a view of this matrix: write through it only on a variable).</summary>
    [System.Diagnostics.CodeAnalysis.UnscopedRef] public Span<double> A => a;
    public double this[int r, int c] { readonly get => a[r * 4 + c]; set => a[r * 4 + c] = value; }
    public static P1M4 Id { get { var m = new P1M4(); m[0, 0] = m[1, 1] = m[2, 2] = m[3, 3] = 1; return m; } }
    public static P1M4 FromRows(IReadOnlyList<double> v) { var m = new P1M4(); for (int i = 0; i < 16; i++) m.a[i] = v[i]; return m; }
    public static P1M4 From(P1M3 l, P1V t)
    {
        var m = Id;
        for (int r = 0; r < 3; r++) { for (int c = 0; c < 3; c++) m[r, c] = l[r, c]; m[r, 3] = t[r]; }
        return m;
    }
    public readonly P1M3 Lin() { var o = new P1M3(); for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = this[r, c]; return o; }
    public readonly P1V T() => new(this[0, 3], this[1, 3], this[2, 3]);
    public readonly P1M4 WithT(P1V t) { var m = this; m[0, 3] = t.X; m[1, 3] = t.Y; m[2, 3] = t.Z; return m; }
    public static P1M4 operator *(P1M4 a, P1M4 b)
    {
        var o = new P1M4();
        for (int r = 0; r < 4; r++) for (int c = 0; c < 4; c++) o[r, c] = a[r, 0] * b[0, c] + a[r, 1] * b[1, c] + a[r, 2] * b[2, c] + a[r, 3] * b[3, c];
        return o;
    }
    public static P1V operator *(P1M4 a, P1V p) => a.Lin() * p + a.T();
    /// <summary>The affine inverse (the linear part by its adjugate: any invertible 3x3, scaled or not).</summary>
    public readonly P1M4 Inverse()
    {
        var m = Lin();
        double a = m[0, 0], b = m[0, 1], c = m[0, 2], d = m[1, 0], e = m[1, 1], f = m[1, 2], g = m[2, 0], h = m[2, 1], i = m[2, 2];
        double det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
        var inv = new P1M3((e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det,
                         (f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det,
                         (d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det);
        return From(inv, (inv * T()) * -1);
    }
}
