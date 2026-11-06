using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her soft tissue on springs, as data (godot/data/body/springs.json, per body; P1 R1 jiggle): each spring is a mass at a
/// point of its bone that follows that point in the WORLD (root motion, turns, the clip), so a stride, a stop, a dash's
/// landing or an attack's twist sets it swinging, overshooting and settling, each side on its own. Mass-normalised
/// stiffness k = (2 pi freq)^2 and damping 2 zeta omega act on the offset from the point and on the velocity relative to
/// it (a steady run carries no lag); rest weight (sag along gravity, press toward the midline, tilt as she leans);
/// per-axis limits in her chest frame and a soft reach; the breast's skinned surface samples kept out of each upper
/// arm's capsule and across her midline no deeper than the clip's own pose puts them. Support (0 bare .. 1 push-up) per
/// group ("top", "bottom") stiffens, damps and shortens. Pure: skeleton-space globals in, new globals and locals out
/// (P1Jiggle drives it on B; the tests and the harness run it offline on the baked clips).
/// </summary>
public sealed class P1Springs
{
    public sealed class Spring
    {
        public string Name = "", Group = "top";
        public int Bone, Parent, Of = -1;
        public bool Shift, Collide;
        public double Side;                                  // +1 her left (+X), -1 her right
        public double Freq, Zeta, Reach, Sag, Press, Tilt, Stretch, Q = 1;
        public double[] Lim = new double[6];                 // in, out, up, down, fwd, back (m, sized)
        public P1V Tip;                                      // the mass's point in the bone's local frame
        // state (world)
        public P1V P, V, LastT, Tv, X, Eq;
        public bool Live;
        // per frame (skeleton space)
        public P1M4 In = P1M4.Id, G = P1M4.Id, Gp = P1M4.Id;
        public double K, C, ReachE;
        public double[] LimE = new double[6];
    }

    sealed class Sample { public P1V P; public int[] J = Array.Empty<int>(); public double[] W = Array.Empty<double>(); }

    public readonly List<Spring> Springs = new();
    /// <summary>Support per group: "top" (the worn top's, ArmorHold.support) and "bottom"; 0 bare .. 1 push-up.</summary>
    public readonly Dictionary<string, double> Support = new() { ["top"] = 0, ["bottom"] = 0 };
    public double Amount = 1, Squash = 1;
    public readonly int[] Needed;
    readonly int[] parent;
    readonly P1M4[] rest, restInv;
    readonly Dictionary<string, Dictionary<string, double>> supportF = new();
    readonly double subHz;
    readonly Dictionary<double, Sample[]> samples = new();   // by side
    readonly Dictionary<double, (int Upper, int Lower, double R)> arms = new();
    readonly int sampleN, iterations;
    readonly double armExtra, cleavageGap;
    static readonly P1V Down = new(0, -1, 0);
    /// <summary>The extra damping (times its own) on the swing outward past three quarters of the reach.</summary>
    public double Cushion = 4;

    public P1Springs(JsonElement springsDoc, string body, JsonElement? samplesDoc, string[] names, int[] parentOf, P1M4[] restG)
    {
        parent = parentOf; rest = restG; restInv = restG.Select(m => m.Inverse()).ToArray();
        var index = new Dictionary<string, int>();
        for (int i = 0; i < names.Length; i++) index[names[i]] = i;
        var b = springsDoc.GetProperty("bodies").GetProperty(body);
        subHz = b.TryGetProperty("substep_hz", out var sh) ? sh.GetDouble() : 240;
        foreach (var g in b.GetProperty("support").EnumerateObject())
            supportF[g.Name] = g.Value.EnumerateObject().ToDictionary(p => p.Name, p => p.Value.GetDouble());
        var col = b.GetProperty("colliders");
        sampleN = col.GetProperty("samples").GetInt32();
        iterations = col.GetProperty("iterations").GetInt32();
        armExtra = col.GetProperty("arm_extra_m").GetDouble();
        cleavageGap = col.GetProperty("cleavage_gap_m").GetDouble();
        var lens = new Dictionary<string, double>();
        foreach (var row in b.GetProperty("springs").EnumerateArray())
            foreach (var s in new[] { "l", "r" })
            {
                string N(string k) => row.GetProperty(k).GetString()!.Replace("{s}", s);
                if (!index.TryGetValue(N("bone"), out int bone)) continue;
                var sp = new Spring
                {
                    Name = N("name"), Bone = bone, Parent = parentOf[bone], Group = row.GetProperty("group").GetString()!,
                    Shift = row.GetProperty("mode").GetString() == "shift",
                    Collide = row.TryGetProperty("collide", out var c) && c.GetBoolean(),
                    Side = restG[bone][0, 3] >= 0 ? 1 : -1,
                    Stretch = row.GetProperty("stretch").GetDouble(),
                };
                double len;
                if (sp.Shift) { sp.Tip = new P1V(0, 0, 0); len = 0; }
                else if (row.TryGetProperty("tip", out _) && index.TryGetValue(N("tip"), out int tip))
                { sp.Tip = restInv[bone] * restG[tip].T(); len = sp.Tip.Len(); }
                else { len = row.GetProperty("len_m").GetDouble(); sp.Tip = new P1V(0, len, 0); }
                lens[sp.Name] = len;
                double sizeLen = row.TryGetProperty("size_of", out _) && lens.TryGetValue(N("size_of"), out var l2) ? l2 : len;
                double q = sizeLen > 0 ? sizeLen / row.GetProperty("size_ref_m").GetDouble() : 1;
                sp.Q = q;
                sp.Freq = row.GetProperty("freq_hz").GetDouble() * Math.Pow(q, -row.GetProperty("size_exp").GetDouble());
                sp.Zeta = row.GetProperty("zeta").GetDouble();
                sp.Reach = row.GetProperty("reach").GetDouble() * q;
                sp.Sag = row.GetProperty("sag").GetDouble() * q;
                sp.Press = row.GetProperty("press").GetDouble() * q;
                sp.Tilt = row.GetProperty("tilt").GetDouble() * q;
                var lim = row.GetProperty("limits");
                sp.Lim = new[] { "in", "out", "up", "down", "fwd", "back" }.Select(k => lim.GetProperty(k).GetDouble() * q).ToArray();
                Springs.Add(sp);
            }
        // tips after their roots: a spring whose skeleton parent is sprung rides that spring's new pose
        var ordered = Springs.Where(x => !x.Shift).Concat(Springs.Where(x => x.Shift)).ToList();
        Springs.Clear(); Springs.AddRange(ordered);
        for (int i = 0; i < Springs.Count; i++) Springs[i].Of = Springs.FindIndex(o => o.Bone == Springs[i].Parent);
        var need = new HashSet<int>();
        foreach (var sp in Springs) { need.Add(sp.Bone); need.Add(sp.Parent); }
        if (samplesDoc is JsonElement sd)
        {
            foreach (var side in sd.GetProperty("breasts").EnumerateObject())
            {
                double sgn = side.Name == "l" ? 1 : -1;
                samples[sgn] = side.Value.EnumerateArray().Select(r => new Sample
                {
                    P = V3(r.GetProperty("p")),
                    J = r.GetProperty("j").EnumerateArray().Select(j => index.TryGetValue(j.GetString()!, out int k) ? k : -1).ToArray(),
                    W = r.GetProperty("w").EnumerateArray().Select(w => w.GetDouble()).ToArray(),
                }).ToArray();
                foreach (var smp in samples[sgn]) foreach (int j in smp.J) if (j >= 0) need.Add(j);
            }
            foreach (var a in sd.GetProperty("arm_radius").EnumerateObject())
            {
                double sgn = a.Name == "l" ? 1 : -1;
                if (index.TryGetValue("upperarm_" + a.Name, out int u) && index.TryGetValue("lowerarm_" + a.Name, out int lo))
                { arms[sgn] = (u, lo, a.Value.GetDouble() + armExtra); need.Add(u); need.Add(lo); }
            }
        }
        need.Remove(-1);
        Needed = need.OrderBy(x => x).ToArray();
    }

    static P1V V3(JsonElement e) { var a = e.EnumerateArray().Select(x => x.GetDouble()).ToArray(); return new P1V(a[0], a[1], a[2]); }

    public void Reset() { foreach (var s in Springs) s.Live = false; }

    double F(string group, string key)
    {
        double sup = Math.Clamp(Support.TryGetValue(group, out var v) ? v : 0, 0, 1);
        return supportF.TryGetValue(group, out var f) && f.TryGetValue(key, out var x) ? 1 + sup * (x - 1) : 1;
    }

    /// <summary>One frame: W her skeleton's world transform, G the skeleton-space globals as the clip and the laws posed
    /// them (only Needed are read), dt seconds. Fills each spring's G (new global) and keeps its state.</summary>
    public void Step(P1M4 W, P1M4[] G, double dt, bool collide = true)
    {
        dt = Math.Clamp(dt, 0, 1.0 / 20);
        var Wl = Ortho(W.Lin()); var WlT = Wl.T();
        foreach (var s in Springs)
        {
            double omega = 2 * Math.PI * s.Freq * Math.Sqrt(F(s.Group, "stiff"));
            s.K = omega * omega; s.C = 2 * s.Zeta * F(s.Group, "zeta") * omega;
            double rf = F(s.Group, "reach");
            s.ReachE = s.Reach * rf;
            for (int k = 0; k < 6; k++) s.LimE[k] = s.Lim[k] * rf;
        }
        foreach (var pass in new[] { false, true })
        {
            foreach (var s in Springs.Where(x => x.Shift == pass))
            {
                var par = s.Of >= 0 ? Springs[s.Of] : null;
                s.Gp = par != null ? par.G : G[s.Parent];
                s.In = par != null ? par.G * (G[par.Bone].Inverse() * G[s.Bone]) : G[s.Bone];
                Integrate(s, W, Wl, dt);
                Finish(s, WlT);
            }
            if (collide && samples.Count > 0) Collide(Wl, G, WlT, pass);
        }
    }

    P1M3 Frame(Spring s, P1M3 Wl) => Ortho(Wl * s.Gp.Lin() * restInv[s.Parent].Lin());

    void Integrate(Spring s, P1M4 W, P1M3 Wl, double dt)
    {
        var Tw = W * (s.In * s.Tip);
        var Fm = Frame(s, Wl);
        var inward = Fm * new P1V(-s.Side, 0, 0);
        s.Eq = inward * (s.Press * F(s.Group, "press")) + Down * (s.Sag * F(s.Group, "sag")) + (Down - Fm * Down) * (s.Tilt * F(s.Group, "reach"));
        bool jump = !s.Live || (Tw - s.LastT).Len() > 0.5;
        if (jump || dt <= 0)
        {
            if (jump) { s.P = Tw + s.Eq; s.V = new P1V(0, 0, 0); s.Tv = s.V; s.Live = true; }
            s.LastT = Tw; s.X = s.P - Tw;
            return;
        }
        s.Tv = (Tw - s.LastT) / dt;
        int n = Math.Max(1, (int)Math.Ceiling(dt * subHz - 1e-9));
        double h = dt / n;
        var FmT = Fm.T();
        for (int i = 0; i < n; i++)
        {
            var Ti = s.LastT + (Tw - s.LastT) * ((i + 1.0) / n);
            var x = s.P - Ti;
            var a = (x - s.Eq) * -s.K - (s.V - s.Tv) * s.C;
            double over = x.Len() - s.ReachE * 0.75;
            if (over > 0)
            {
                // past three quarters of its reach the skin and ligament take up: stiffer, and the swing out soaked up
                // (a cushioned stop, not a slam into the limit)
                var u = x / x.Len(); double vo = P1V.Dot(s.V - s.Tv, u);
                a -= u * (over * s.K * 6 + (vo > 0 ? vo * s.C * Cushion : 0));
            }
            s.V += a * h; s.P += s.V * h;
            // the limits, in her chest frame (in: toward her midline): a hard stop with a little rebound
            var l = FmT * (s.P - Ti); var vr = FmT * (s.V - s.Tv);
            double lx = l.X * s.Side, vx = vr.X * s.Side, ly = l.Y, vy = vr.Y, lz = l.Z, vz = vr.Z;
            Clamp(ref lx, ref vx, -s.LimE[0], s.LimE[1]);
            Clamp(ref ly, ref vy, -s.LimE[3], s.LimE[2]);
            Clamp(ref lz, ref vz, -s.LimE[5], s.LimE[4]);
            var lc = new P1V(lx * s.Side, ly, lz); var vc = new P1V(vx * s.Side, vy, vz);
            double len = lc.Len();
            if (len > s.ReachE) { var u = lc / len; lc = u * s.ReachE; double vu = P1V.Dot(vc, u); if (vu > 0) vc -= u * (vu * 1.2); }
            s.P = Ti + Fm * lc; s.V = s.Tv + Fm * vc;
        }
        s.LastT = Tw; s.X = s.P - Tw;
    }

    static void Clamp(ref double l, ref double v, double lo, double hi)
    {
        if (l > hi) { l = hi; if (v > 0) v *= -0.2; }
        else if (l < lo) { l = lo; if (v < 0) v *= -0.2; }
    }

    void Finish(Spring s, P1M3 WlT)
    {
        var xs = WlT * (s.X * Amount);
        if (s.Shift) { s.G = s.In.WithT(s.In.T() + xs); return; }
        var from = s.In.Lin() * s.Tip; var to = from + xs;
        var R = Between(from, to);
        double k = 1 + Math.Clamp((to.Len() - from.Len()) / Math.Max(s.ReachE, 1e-4), -1, 1) * s.Stretch * Squash;
        double side = 1 / Math.Sqrt(Math.Max(k, 0.5));
        var D = new P1M3(side, 0, 0, 0, k, 0, 0, 0, side);
        s.G = P1M4.From(R * s.In.Lin() * D, s.In.T());
    }

    /// <summary>The bone's new local (its parent's new global, or the input's, inverse times its new global).</summary>
    public P1M4 Local(Spring s, P1M4[] G) => (s.Of >= 0 ? Springs[s.Of].G : G[s.Parent]).Inverse() * s.G;

    // ------------------------------------------------------------------ colliders --
    /// <summary>The breast's samples skinned (skeleton space, LBS as the GPU does) with the springs' new poses, or
    /// without them (the clip's own pose); count 0: every sample (the harness), else the first count (the game).</summary>
    public P1V[] Skin(double side, P1M4[] G, bool sprung, int count = 0)
    {
        if (!samples.TryGetValue(side, out var ss)) return Array.Empty<P1V>();
        int n = count > 0 ? Math.Min(count, ss.Length) : ss.Length;
        var M = new Dictionary<int, P1M4>();
        P1M4 Mat(int j)
        {
            if (M.TryGetValue(j, out var m)) return m;
            var s = sprung ? Springs.FirstOrDefault(x => x.Bone == j) : null;
            return M[j] = (s != null ? s.G : G[j]) * restInv[j];
        }
        var o = new P1V[n];
        for (int i = 0; i < n; i++)
        {
            var p = new P1V(0, 0, 0);
            for (int k = 0; k < ss[i].J.Length; k++) if (ss[i].J[k] >= 0) p += Mat(ss[i].J[k]) * ss[i].P * ss[i].W[k];
            o[i] = p;
        }
        return o;
    }

    /// <summary>A point's depth (m, positive inside) in an upper arm's capsule (armSide +1 her left), and the way out.</summary>
    public double ArmDepth(P1V p, double armSide, P1M4[] G, out P1V normal)
    {
        var (u, lo, r) = arms[armSide];
        var a = G[u].T(); var b = G[lo].T(); var ab = b - a;
        double t = Math.Clamp(P1V.Dot(p - a, ab) / Math.Max(P1V.Dot(ab, ab), 1e-12), 0, 1);
        var d = p - (a + ab * t); double len = d.Len();
        normal = len > 1e-9 ? d / len : new P1V(0, 0, 1);
        return r - len;
    }

    /// <summary>A point's crossing of her midline (m, positive: past it toward the other side), the plane through the
    /// chest bone's rest midline turned with it.</summary>
    public double MidDepth(P1V p, double side, P1M4 chest, int chestBone)
    {
        var Fm = Ortho(chest.Lin() * restInv[chestBone].Lin());
        var mid = chest * (restInv[chestBone] * new P1V(0, rest[chestBone][1, 3], rest[chestBone][2, 3]));
        return -side * P1V.Dot(Fm.Col(0), p - mid);
    }

    public IEnumerable<double> Arms => arms.Keys;

    /// <summary>The breasts (tips false: their roots, turned; true: their tips, shifted) moved out of the upper arms and
    /// back from her midline by the worst sample's added depth over its lever, the velocity into it taken out.</summary>
    void Collide(P1M3 Wl, P1M4[] G, P1M3 WlT, bool tips)
    {
        foreach (var s in Springs.Where(x => tips ? x.Shift && x.Of >= 0 && Springs[x.Of].Collide : x.Collide && !x.Shift))
        {
            var root = tips ? Springs[s.Of] : s;
            var ss = samples[root.Side];
            var basePts = Skin(root.Side, G, false, sampleN);
            var head = root.In.T(); double tipLen = Math.Max(root.Tip.Len(), 1e-3);
            int me = Springs.IndexOf(s);
            void Carry() { if (!tips) foreach (var t in Springs.Where(x => x.Of == me)) { t.In = s.G * (G[s.Bone].Inverse() * G[t.Bone]); Finish(t, WlT); } }
            double Worst(out P1V n, out double lever)
            {
                // (its tip carried by its new pose, with the tip's last offset: the tip's own step follows)
                Carry();
                var pts = Skin(root.Side, G, true, sampleN);
                double worst = 0; n = default; lever = 1;
                for (int i = 0; i < pts.Length; i++)
                {
                    double lv = 1;
                    if (!tips) lv = Math.Clamp((pts[i] - head).Len() / tipLen, 0.5, 2.5);
                    else { double w = 0; for (int k = 0; k < ss[i].J.Length; k++) if (ss[i].J[k] == s.Bone) w += ss[i].W[k]; lv = Math.Clamp(w, 0.25, 1); }
                    foreach (double a in arms.Keys)
                    {
                        double d = ArmDepth(pts[i], a, G, out var nn) - Math.Max(ArmDepth(basePts[i], a, G, out _), 0);
                        if (d > worst) { worst = d; n = nn; lever = lv; }
                    }
                    double m = MidDepth(pts[i], root.Side, root.Gp, root.Parent) + cleavageGap - Math.Max(MidDepth(basePts[i], root.Side, root.Gp, root.Parent) + cleavageGap, 0);
                    if (m > worst) { worst = m; lever = lv; n = Ortho(root.Gp.Lin() * restInv[root.Parent].Lin()).Col(0) * root.Side; }
                }
                return worst;
            }
            const double tol = 1e-4;
            double worst = 0;
            for (int it = 0; it < iterations; it++)
            {
                worst = Worst(out var n, out double lever);
                if (worst <= tol) break;
                var nw = Wl * n;
                s.X += nw * (worst / lever * 1.1);
                double vn = P1V.Dot(s.V - s.Tv, nw);
                if (vn < 0) s.V -= nw * (vn * 1.2);
                s.P = s.LastT + s.X;
                Finish(s, WlT);
            }
            worst = Worst(out _, out _);
            if (worst > tol)
            {
                // the push could not clear it (a point pressed toward the bone's head, a turn cannot move it out): the
                // offset drawn back toward none, where the surface is the clip's own (no added depth by definition)
                var x0 = s.X; double lo = 0, hi = 1;
                for (int k = 0; k < 6; k++)
                {
                    double mid = (lo + hi) / 2;
                    s.X = x0 * mid; Finish(s, WlT);
                    if (Worst(out _, out _) > tol) hi = mid; else lo = mid;
                }
                s.X = x0 * lo; s.V = s.Tv + (s.V - s.Tv) * lo; s.P = s.LastT + s.X;
                Finish(s, WlT); Carry();
            }
        }
    }

    // ------------------------------------------------------------------ small maths --
    public static P1M3 Ortho(P1M3 m)
    {
        var x = m.Col(0); x /= Math.Max(x.Len(), 1e-12);
        var y = m.Col(1); y -= x * P1V.Dot(x, y); y /= Math.Max(y.Len(), 1e-12);
        var z = P1V.Cross(x, y);
        return new P1M3(x.X, y.X, z.X, x.Y, y.Y, z.Y, x.Z, y.Z, z.Z);
    }

    /// <summary>The rotation turning direction a to direction b (Rodrigues).</summary>
    public static P1M3 Between(P1V a, P1V b)
    {
        double la = a.Len(), lb = b.Len();
        if (la < 1e-9 || lb < 1e-9) return P1M3.Id;
        var u = a / la; var v = b / lb;
        var ax = P1V.Cross(u, v); double s = ax.Len(), c = P1V.Dot(u, v);
        if (s < 1e-12) return P1M3.Id;
        var k = ax / s;
        var K = new P1M3(0, -k.Z, k.Y, k.Z, 0, -k.X, -k.Y, k.X, 0);
        return P1M3.Id + K * s + K * K * (1 - c);
    }
}
