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

    public P1Rig(string[] names, int[] parent, P1M4[] rest, JsonElement rig)
    {
        Names = names; Parent = parent; Rest = rest; this.rig = rig;
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

    double Elevation(P1M4[] G, string s)
    {
        var gd = rig.GetProperty("girdle");
        int j = Index[Sub(gd.GetProperty("arm"), s)], c = Index[Sub(gd.GetProperty("arm_end"), s)];
        var down = Turn(G, Index[gd.GetProperty("torso").GetString()!]) * Vec(gd.GetProperty("down"));
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
    public static double Table(double x, JsonElement T)
    {
        var rows = T.EnumerateArray().Select(r => (X: r[0].GetDouble(), Y: r[1].GetDouble())).ToArray();
        int n = rows.Length;
        if (x <= rows[0].X) return rows[0].Y;
        if (x >= rows[n - 1].X) return rows[n - 1].Y;
        var h = new double[n - 1]; var dl = new double[n - 1];
        for (int k = 0; k < n - 1; k++) { h[k] = rows[k + 1].X - rows[k].X; dl[k] = (rows[k + 1].Y - rows[k].Y) / h[k]; }
        var m = new double[n];
        for (int k = 1; k < n - 1; k++)
            if (dl[k - 1] * dl[k] > 0)
            {
                double w1 = 2 * h[k] + h[k - 1], w2 = h[k] + 2 * h[k - 1];
                m[k] = (w1 + w2) / (w1 / dl[k - 1] + w2 / dl[k]);
            }
        int i = 0;
        while (x > rows[i + 1].X) i++;
        double t = (x - rows[i].X) / h[i], t2 = t * t, t3 = t2 * t;
        return (2 * t3 - 3 * t2 + 1) * rows[i].Y + (t3 - 2 * t2 + t) * h[i] * m[i] + (-2 * t3 + 3 * t2) * rows[i + 1].Y
            + (t3 - t2) * h[i] * m[i + 1];
    }

    /// <summary>rig_drive.girdle: the scapulohumeral rhythm by tables of the arm's elevation and its forward reach,
    /// relative to the rest.</summary>
    double Girdle(P1M4[] G, string s)
    {
        var R0 = Rest;
        var gd = rig.GetProperty("girdle");
        double sg = s == "l" ? 1 : -1;
        int cl = Index[Sub(gd.GetProperty("clavicle"), s)], sc = Index[Sub(gd.GetProperty("scap"), s)], arm = Index[Sub(gd.GetProperty("arm"), s)];
        int end = Index[Sub(gd.GetProperty("arm_end"), s)];
        double A = Elevation(G, s), A0 = Elevation(R0, s);
        var Rt = Turn(G, Index[gd.GetProperty("torso").GetString()!]);
        var front = Rt * Vec(gd.GetProperty("front"));
        var up = Rt * Vec(gd.GetProperty("up"));
        var side = Rt * Vec(gd.GetProperty("side"));
        var d = N(Head(G, end) - Head(G, arm));
        var d0 = N(Head(R0, end) - Head(R0, arm));
        double reach = P1V.Dot(d, front) - P1V.Dot(Rt * d0, front);
        double the = Table(A, gd.GetProperty("clav_elev")) - Table(A0, gd.GetProperty("clav_elev"));
        double thr = Table(A, gd.GetProperty("clav_retract")) - Table(A0, gd.GetProperty("clav_retract"))
            - gd.GetProperty("protract_per_reach").GetDouble() * reach;
        var armOld = G[arm];
        if (Math.Abs(the) > 1e-9 || Math.Abs(thr) > 1e-9)
        {
            var Rc = Expm(up * (sg * Rad(thr))) * Expm(front * (sg * Rad(the)));
            Apply(G, cl, About(Head(G, cl), Rc));
            // the upper arm keeps its world turn (the clip's aim), riding the moved clavicle
            var nw = armOld.WithT(G[arm].T());
            Apply(G, arm, nw * G[arm].Inverse());
        }
        double thu = Table(A, gd.GetProperty("scap_up")) - Table(A0, gd.GetProperty("scap_up"));
        double thp = Table(A, gd.GetProperty("scap_tilt")) - Table(A0, gd.GetProperty("scap_tilt"));
        if (Math.Abs(thu) > 1e-9 || Math.Abs(thp) > 1e-9)
        {
            var ax = Vec(gd.GetProperty("scap_axis"));
            var n = Rt * N(new P1V(ax.X * sg, ax.Y, ax.Z));
            var Rs = Expm(side * (-Rad(thp))) * Expm(n * (sg * Rad(thu)));
            Apply(G, sc, About(Head(G, sc), Rs));
        }
        double glide = gd.GetProperty("glide_m").GetDouble() * reach;
        if (Math.Abs(glide) > 1e-12) Apply(G, sc, P1M4.From(P1M3.Id, front * glide));
        return A;
    }

    P1M3 RelTurn(P1M4[] G, int j, int p) => Turn(G, p).T() * Turn(G, j);

    void Helper(P1M4[] G, JsonElement h, string s, Dictionary<string, double> info)
    {
        var R0 = Rest;
        if (!Index.TryGetValue(Sub(h.GetProperty("name"), s), out int j)) return;
        var kind = h.GetProperty("kind").GetString();
        if (kind == "unroll")
        {
            int ch = Index[Sub(h.GetProperty("child"), s)];
            int p = Parent[j];
            var y = Unit(G[j]).Col(1);
            double ang = Roll(Turn(G, j) * Turn(G, p).T(), y);
            if (Math.Abs(ang) < 1e-12) return;
            var keep = subtree[ch].ToDictionary(k => k, k => G[k]);
            Apply(G, j, About(Head(G, j), Expm(y * -ang)));
            foreach (var kv in keep) G[kv.Key] = kv.Value;
            return;
        }
        if (kind == "aim")
        {
            int p = Parent[j];
            int on = Index[Sub(h.GetProperty("on"), s)];
            double? A = info.TryGetValue("A" + s, out var av) ? av : null;
            if (h.TryGetProperty("read", out var rd) && rd.GetString() == "hip") A = FlexionFromDown(G, on, h, s);
            var Ar = h.GetProperty("A");
            double g = A is double a ? Smooth((a - Ar[0].GetDouble()) / (Ar[1].GetDouble() - Ar[0].GetDouble())) : 0;
            if (g <= 0) return;
            var Gc = G[j];
            var hj = Head(G, j);
            string? onEnd = h.TryGetProperty("on_end", out var oe) && Sub(oe, s) is { Length: > 0 } oes ? oes : null;
            double aimM = Num(h, "aim_m", 0);
            var end = ChildHead(G, on, onEnd);
            var aim = Head(G, on) + N(end - Head(G, on)) * aimM;
            // the same aim at rest, carried by the helper's parent: its swing since rest
            var end0 = ChildHead(R0, on, onEnd);
            var aim0 = Head(R0, on) + N(end0 - Head(R0, on)) * aimM;
            var Cp = G[p] * R0[p].Inverse();
            var aim0w = Cp * aim0;
            var Rsw = Arc(N(aim0w - hj), N(aim - hj));
            var R = Expm(RotVec(Rsw) * (g * Num(h, "turn", 0)));
            var y = R * Unit(Gc).Col(1);
            double sp = Num(h, "sp", 0), sa = Num(h, "sa", 0);
            var Sc = P1M3.Id * (1 + g * sp) + P1M3.Outer(y, y) * (g * (sa - sp));
            var M = About(hj, Sc * R);
            var o = h.TryGetProperty("off", out var off) ? Vec(off) * g : new P1V(0, 0, 0);
            o = new P1V(o.X * (s == "l" ? 1 : -1), o.Y, o.Z);
            M = M.WithT(M.T() + Cp.Lin() * o);
            G[j] = M * Gc;
            return;
        }
        int f = Index[Sub(h.GetProperty("follow"), s)];
        int pj = Parent[j];
        double amt = Num(h, "amount", 0);
        if (kind is "counter_twist" or "twist")
        {
            var y = Unit(G[j]).Col(1);
            double ang = kind == "counter_twist"
                ? -amt * Roll(Turn(G, f) * Turn(G, Parent[f]).T(), y)
                : amt * Roll(Turn(G, f) * Turn(G, pj).T(), y);
            if (Math.Abs(ang) > 1e-12) Apply(G, j, About(Head(G, j), Expm(y * ang)));
            return;
        }
        if (kind is "share" or "point")
        {
            var Gc = Carried(G, j);                  // the share as its parent carries it
            G[j] = Gc;
            var Rp = Turn(G, pj);
            var Rrel = RelTurn(G, f, pj);
            var rv = RotVec(Rrel);
            var Rh = Rp * Expm(rv * amt) * Rp.T();     // the half turn, in the world
            var z = Rp * (Unit(R0[f]).Col(2) * Num(h, "crease", 1));
            var c = Head(G, j) + z * Num(h, "pivot", 0);
            double b = Deg(rv.Len());
            double k = Math.Min(1 + Num(h, "bulge", 0) * (1 - Math.Cos(Rad(Math.Min(b, 180)) / 2)), Num(h, "bulge_max", 1));
            var zz = Rh * z;
            var Sw = P1M3.Id + P1M3.Outer(zz, zz) * (k - 1);
            var tp = Head(G, j) + z * Num(h, "turn_pivot", 0);
            var M = About(c, Sw) * About(tp, Rh);
            if (kind == "point")
            {
                var fl = h.GetProperty("flex");
                double F = Flexion(G, Sub(fl[0], s), Sub(fl[1], s), Sub(fl[2], s));
                double from = h.GetProperty("from").GetDouble(), to = h.GetProperty("to").GetDouble();
                double push = h.GetProperty("push").GetDouble() * Smooth((F - from) / (to - from));
                M = M.WithT(M.T() - zz * push);
            }
            G[j] = M * Gc;
            return;
        }
        throw new ArgumentException($"unknown helper kind {kind}");
    }

    double FlexionFromDown(P1M4[] G, int on, JsonElement h, string s)
    {
        int p = Index[h.GetProperty("torso").GetString()!];
        var down = Turn(G, p) * Vec(h.GetProperty("down"));
        int end = Index[Sub(h.GetProperty("on_end"), s)];
        var d = N(Head(G, end) - Head(G, on));
        return Deg(Math.Acos(Math.Clamp(P1V.Dot(d, down), -1, 1)));
    }

    // --------------------------------------------------------- correctives --
    public static double[] FlexWeights(double F, IReadOnlyList<double> keys)
    {
        var w = new double[keys.Count];
        if (F <= keys[0]) w[0] = 1;
        else if (F >= keys[^1]) w[^1] = 1;
        else
        {
            int i = 0;
            while (i + 1 < keys.Count && keys[i + 1] <= F) i++;   // (searchsorted right, minus one)
            double t = Smooth((F - keys[i]) / (keys[i + 1] - keys[i]));
            w[i] = 1 - t; w[i + 1] = t;
        }
        return w;
    }

    static double[] RbfPhi(P1V d, P1V[] K, double sigma)
    {
        var o = new double[K.Length];
        for (int i = 0; i < K.Length; i++)
        {
            double ang = Deg(Math.Acos(Math.Clamp(P1V.Dot(K[i], d), -1, 1)));
            o[i] = Math.Exp(-(ang / sigma) * (ang / sigma));
        }
        return o;
    }

    static P1V[] Keys(JsonElement k) => k.EnumerateArray().Select(Vec).ToArray();

    static double[] ArcWeights(P1V d, P1V[] K, double g0, double g1)
    {
        var a = N(P1V.Cross(K[0], K[^1]));
        var e1 = N(K[0] - a * P1V.Dot(K[0], a));
        var e2 = P1V.Cross(a, e1);
        double Th(P1V v) => Deg(Math.Atan2(P1V.Dot(v, e2), P1V.Dot(v, e1)));
        var tk = K.Select(Th).ToArray();
        tk[0] = 0;
        var w = FlexWeights(Th(d), tk).Skip(1).ToArray();
        double beta = Math.Abs(Deg(Math.Asin(Math.Clamp(P1V.Dot(d, a), -1, 1))));
        double gate = 1 - Smooth((beta - g0) / (g1 - g0));
        for (int i = 0; i < w.Length; i++) w[i] *= gate;
        return w;
    }

    public Dictionary<string, double> CorrectiveWeights(P1M4[] G)
    {
        var o = new Dictionary<string, double>();
        if (!rig.TryGetProperty("correctives", out var cs)) return o;
        foreach (var c in cs.EnumerateArray())
        {
            string law = c.TryGetProperty("law", out var l) ? l.GetString() ?? "" : "";
            foreach (var s in Sides(c.GetRawText()))
            {
                string sub(string x) => x.Replace("{s}", s);
                string side = s == "" ? "l" : s;
                if (law == "flex")
                {
                    var bones = c.GetProperty("bones").EnumerateArray().Select(b => sub(b.GetString()!)).ToArray();
                    if (bones.Any(b => !Index.ContainsKey(b))) continue;
                    var w = FlexWeights(Flexion(G, bones[0], bones[1], bones[2]), c.GetProperty("keys").EnumerateArray().Select(x => x.GetDouble()).ToArray());
                    int i = 0;
                    foreach (var nm in c.GetProperty("shapes").EnumerateArray())
                    {
                        if (nm.ValueKind == JsonValueKind.String) o[sub(nm.GetString()!)] = w[i];
                        i++;
                    }
                }
                else if (law is "rbf" or "arc")
                {
                    if (!Index.ContainsKey(sub(c.GetProperty("bone").GetString()!))) continue;
                    var d = Direction(G, sub(c.GetProperty("bone").GetString()!), sub(c.GetProperty("end").GetString()!), sub(c.GetProperty("frame").GetString()!));
                    var K = Keys(c.GetProperty("keys").GetProperty(side));
                    double[] w;
                    if (law == "rbf")
                    {
                        var phi = RbfPhi(d, K, c.GetProperty("sigma_deg").GetDouble());
                        var M = c.GetProperty("M").GetProperty(side);
                        int ns = M[0].GetArrayLength();
                        w = new double[ns];
                        for (int q = 0; q < ns; q++)
                        {
                            double acc = 0;
                            for (int r = 0; r < phi.Length; r++) acc += phi[r] * M[r][q].GetDouble();
                            w[q] = Math.Clamp(acc, 0, 1);
                        }
                    }
                    else
                    {
                        var gd = c.GetProperty("gate_deg");
                        w = ArcWeights(d, K, gd[0].GetDouble(), gd[1].GetDouble());
                    }
                    int i = 0;
                    foreach (var nm in c.GetProperty("shapes").EnumerateArray())
                    {
                        o[sub(nm.GetString()!)] = w[i] < 1e-5 ? 0 : w[i];   // exactly 0 at the rest key
                        i++;
                    }
                }
                else if (c.TryGetProperty("bone", out var bn) && Index.TryGetValue(sub(bn.GetString()!), out int j))
                {
                    string on = c.TryGetProperty("on", out var oo) ? oo.GetString()! : "swing";
                    o[sub(c.GetProperty("name").GetString()!)] = LegacyWeight(c, AngleOf(G, j, on));
                }
            }
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

    static double LegacyWeight(JsonElement c, double deg)
    {
        if (c.TryGetProperty("keys", out var k))
        {
            double lo = k[0].GetDouble(), at = k[1].GetDouble(), hi = k[2].GetDouble();
            if (deg <= lo) return 0;
            if (deg < at) return (deg - lo) / (at - lo);
            if (hi <= at) return 1;
            return Math.Max(0, 1 - (deg - at) / (hi - at));
        }
        double from = c.GetProperty("from").GetDouble(), to = c.GetProperty("to").GetDouble();
        double t = Math.Clamp((deg - from) / (to - from), 0, 1);
        bool sm = !c.TryGetProperty("smoothstep", out var ss) || ss.GetBoolean();
        return sm ? t * t * (3 - 2 * t) : t;
    }

    // --------------------------------------------------------------- drive --
    /// <summary>rig_drive.drive: the girdle (per side), the helper rows in order, then the correctives' weights. The
    /// input array is left as it was.</summary>
    public (P1M4[] G, Dictionary<string, double> Weights) Drive(P1M4[] input)
    {
        var G = (P1M4[])input.Clone();
        var info = new Dictionary<string, double>();
        if (rig.TryGetProperty("girdle", out _))
            foreach (var s in new[] { "l", "r" }) info["A" + s] = Girdle(G, s);
        if (rig.TryGetProperty("helpers", out var hs))
            foreach (var h in hs.EnumerateArray())
                foreach (var s in Sides(h.GetProperty("name").GetString()!))
                    Helper(G, h, s, info);
        return (G, CorrectiveWeights(G));
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

/// <summary>A 3x3 in doubles, row-major.</summary>
public sealed class P1M3
{
    public readonly double[] A = new double[9];
    public P1M3() { }
    public P1M3(params double[] v) { Array.Copy(v, A, 9); }
    public static P1M3 Id => new(1, 0, 0, 0, 1, 0, 0, 0, 1);
    public double this[int r, int c] { get => A[r * 3 + c]; set => A[r * 3 + c] = value; }
    public static P1M3 operator *(P1M3 a, P1M3 b)
    {
        var o = new P1M3();
        for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = a[r, 0] * b[0, c] + a[r, 1] * b[1, c] + a[r, 2] * b[2, c];
        return o;
    }
    public static P1V operator *(P1M3 a, P1V v) => new(a[0, 0] * v.X + a[0, 1] * v.Y + a[0, 2] * v.Z, a[1, 0] * v.X + a[1, 1] * v.Y + a[1, 2] * v.Z, a[2, 0] * v.X + a[2, 1] * v.Y + a[2, 2] * v.Z);
    public static P1M3 operator *(P1M3 a, double k) { var o = new P1M3(); for (int i = 0; i < 9; i++) o.A[i] = a.A[i] * k; return o; }
    public static P1M3 operator +(P1M3 a, P1M3 b) { var o = new P1M3(); for (int i = 0; i < 9; i++) o.A[i] = a.A[i] + b.A[i]; return o; }
    public P1M3 T() { var o = new P1M3(); for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = this[c, r]; return o; }
    public P1V Col(int c) => new(this[0, c], this[1, c], this[2, c]);
    public static P1M3 Outer(P1V a, P1V b) { var o = new P1M3(); for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = a[r] * b[c]; return o; }
}

/// <summary>A 4x4 affine in doubles, row-major ([r,3] the translation).</summary>
public sealed class P1M4
{
    public readonly double[] A = new double[16];
    public double this[int r, int c] { get => A[r * 4 + c]; set => A[r * 4 + c] = value; }
    public static P1M4 Id { get { var m = new P1M4(); m[0, 0] = m[1, 1] = m[2, 2] = m[3, 3] = 1; return m; } }
    public static P1M4 FromRows(IReadOnlyList<double> v) { var m = new P1M4(); for (int i = 0; i < 16; i++) m.A[i] = v[i]; return m; }
    public static P1M4 From(P1M3 l, P1V t)
    {
        var m = Id;
        for (int r = 0; r < 3; r++) { for (int c = 0; c < 3; c++) m[r, c] = l[r, c]; m[r, 3] = t[r]; }
        return m;
    }
    public P1M3 Lin() { var o = new P1M3(); for (int r = 0; r < 3; r++) for (int c = 0; c < 3; c++) o[r, c] = this[r, c]; return o; }
    public P1V T() => new(this[0, 3], this[1, 3], this[2, 3]);
    public P1M4 WithT(P1V t) { var m = new P1M4(); Array.Copy(A, m.A, 16); m[0, 3] = t.X; m[1, 3] = t.Y; m[2, 3] = t.Z; return m; }
    public static P1M4 operator *(P1M4 a, P1M4 b)
    {
        var o = new P1M4();
        for (int r = 0; r < 4; r++) for (int c = 0; c < 4; c++) o[r, c] = a[r, 0] * b[0, c] + a[r, 1] * b[1, c] + a[r, 2] * b[2, c] + a[r, 3] * b[3, c];
        return o;
    }
    public static P1V operator *(P1M4 a, P1V p) => a.Lin() * p + a.T();
    /// <summary>The affine inverse (the linear part by its adjugate: any invertible 3x3, scaled or not).</summary>
    public P1M4 Inverse()
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
