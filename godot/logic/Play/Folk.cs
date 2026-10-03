using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* A town's worth of people walking about (the web game's game/folk.ts).
 *
 * The zone gives a graph of places (doors, stalls, the well, the board, the
 * gates, and the lanes between) and says how many should be out at this
 * hour. Each walker picks somewhere to go, walks the lanes to it and does
 * the thing you do there: haggles at a stall, draws a bucket, reads the
 * board, goes indoors for a while. Some walk in twos and talk when they stop.
 * When the hour says fewer, the extra ones head for a door and go home; when
 * it says more, doors open and people come out. Children chase each other
 * round the square by day; after dark a watchman walks the rounds with a
 * torch. None of them blocks the survivor: they step aside. */

public enum FolkKind { Door, Stall, Well, Board, Gate, Path }
public enum FolkRole { Adult, Child, Watch }

public sealed class FolkNode
{
    public string Id = "";
    public double X, Z;
    public FolkKind Kind = FolkKind.Path;
    /// <summary>What to face when there (the stall's counter, the board).</summary>
    public XZ? Face;
    /// <summary>Part of the square (where children play).</summary>
    public bool Square;
    public bool Tavern;
}

public readonly record struct FolkPlan(int Adults, int Children, bool Watch);

public sealed class Folk
{
    sealed class Walker
    {
        public int Id;
        public INpcView View = null!;
        public FolkRole Role;
        /// <summary>Whose voice says their lines.</summary>
        public Sex Sex;
        public double X, Z, Vx, Vz, Heading;
        public List<FolkNode> Path = new();
        public FolkNode? Dest;
        public FolkNode At = null!;
        public string State = "walk";
        public double T, Speed;
        public bool Leaving, Gone, Shown = true;
        public Walker? Lead;
        public int Side = 1;
        public string? Carry;
        public double BarkT;
        public int Torch = -1;
        /// <summary>The round a watchman walks, and where on it he is.</summary>
        public int Round;
        /// <summary>Which way to go round something in the way, and for how long.</summary>
        public int Detour = 1;
        public double DetourT;
        /// <summary>Closest yet to the next waypoint, and how long since that improved.</summary>
        public double Best = double.PositiveInfinity, StuckT;
        /// <summary>Until the bucket comes up out of the well.</summary>
        public double BucketT;
    }

    public sealed class Options
    {
        public List<FolkNode> Nodes = new();
        public List<(string A, string B)> Edges = new();
        public CollisionWorld Col = null!;
        public IZoneLook Look = null!;
        /// <summary>How many should be out, now.</summary>
        public Func<FolkPlan> Plan = () => new(0, 0, false);
        /// <summary>Is it dark? (torches, and the tavern draws people)</summary>
        public Func<bool> Dark = () => false;
        /// <summary>What the town is saying, now: lines whose conditions hold.</summary>
        public Func<FolkRole, List<FolkLine>> Lines = _ => new();
        /// <summary>The watch's round, as node ids.</summary>
        public string[] Round = Array.Empty<string>();
    }

    readonly Options o;
    readonly Random rng;
    List<Walker> walkers = new();
    readonly Dictionary<string, List<FolkNode>> adj = new();
    double spawnT, barkT = 4;
    readonly List<string> said = new();
    bool started;
    int nextId = 1;

    public Folk(Options opts, Random rng)
    {
        o = opts;
        this.rng = rng;
        var byId = o.Nodes.ToDictionary(n => n.Id);
        foreach (var n in o.Nodes) adj[n.Id] = new();
        foreach (var (a, b) in o.Edges)
        {
            if (!byId.TryGetValue(a, out var na) || !byId.TryGetValue(b, out var nb)) continue;
            adj[a].Add(nb);
            adj[b].Add(na);
        }
    }

    public int Count => walkers.Count;
    double Rnd(double a, double b) => a + rng.NextDouble() * (b - a);
    T Pick<T>(IReadOnlyList<T> a) => a[rng.Next(a.Count)];
    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    /// <summary>For tools: lanes that run through something solid (sampled every 0.4 m).</summary>
    public List<string> Validate()
    {
        var bad = new List<string>();
        var byId = o.Nodes.ToDictionary(n => n.Id);
        foreach (var n in o.Nodes) if (o.Col.Blocked(n.X, n.Z, 0.3, true)) bad.Add($"node {n.Id} ({n.X:0.0},{n.Z:0.0})");
        foreach (var (a, b) in o.Edges)
        {
            if (!byId.TryGetValue(a, out var na) || !byId.TryGetValue(b, out var nb)) { bad.Add($"edge {a}-{b}: missing node"); continue; }
            double len = Dist(na.X, na.Z, nb.X, nb.Z);
            int n = (int)Math.Ceiling(len / 0.4);
            for (int i = 1; i < n; i++)
            {
                double x = na.X + (nb.X - na.X) * i / n, z = na.Z + (nb.Z - na.Z) * i / n;
                if (o.Col.Blocked(x, z, 0.3, true)) { bad.Add($"edge {a}-{b} at ({x:0.0},{z:0.0})"); break; }
            }
        }
        return bad;
    }

    /// <summary>For tools: where everyone is and what they are doing.</summary>
    public IEnumerable<(double X, double Z, FolkRole Role, string State, bool Shown)> Debug() =>
        walkers.Select(w => (w.X, w.Z, w.Role, w.State, w.Shown));

    /* ------------------------------------------------------------ people -- */

    /// <summary>Someone from the town, in the flesh: a man or a woman in the
    /// plain clothes of a look (its colours dye them), with skin, hair and a
    /// beard of their own. The watch wear leathers, a pauldron and a hood;
    /// children are small, with a child's larger head and no figure.</summary>
    public static PersonSpec Person(FolkRole role, FolkLook l, Random rng)
    {
        bool child = role == FolkRole.Child;
        var sex = rng.NextDouble() < (role == FolkRole.Watch ? 0.3 : 0.5) ? Sex.Female : Sex.Male;
        bool hood = role == FolkRole.Watch || (!child && l.Model == "rogue_hooded");
        string kind = role == FolkRole.Watch ? "ranger" : l.Model == "rogue_hooded" || rng.NextDouble() < 0.2 ? "ranger" : "peasant";
        var styles = Lore.HairStyles(sex);
        var hairs = Lore.Hairs.Where(h => h.Color != "").ToList();
        var skin = Lore.Skins[rng.Next(Lore.Skins.Count)].Color;
        return new PersonSpec
        {
            Sex = sex, Outfit = Lore.OutfitFor(sex, kind, hood, role == FolkRole.Watch),
            Hair = hood ? null : rng.NextDouble() < 0.08 ? null : styles[rng.Next(styles.Count)],
            Beard = sex == Sex.Male && !child && rng.NextDouble() < 0.6,
            HairColor = hairs[rng.Next(hairs.Count)].Color, Skin = skin == "" ? null : skin,
            Figure = sex == Sex.Female ? (child ? 0 : 0.6 + rng.NextDouble() * 0.8) : null,
            Head = child ? 1.25 : null,
            Dye = new Dye { Cloth = l.Tint, Under = l.Under },
        };
    }

    Walker Make(FolkRole role, FolkNode at, FolkLook? look = null)
    {
        var l = look ?? (role == FolkRole.Child ? Pick(Lore.ChildLooks) : role == FolkRole.Watch ? Lore.WatchLook : Pick(Lore.FolkLooks));
        var spec = Person(role, l, rng);
        var w = new Walker
        {
            Id = nextId++, View = o.Look.Walker(spec, 0.8 * (l.Scale ?? 1)), Role = role, Sex = spec.Sex,
            X = at.X + Rnd(-0.6, 0.6), Z = at.Z + Rnd(-0.6, 0.6), At = at,
            Speed = role == FolkRole.Child ? Rnd(3.3, 3.9) : role == FolkRole.Watch ? 1.25 : Rnd(1.35, 1.8),
            BarkT = Rnd(8, 30), Heading = rng.NextDouble() * Math.PI * 2,
        };
        if (role == FolkRole.Watch)
        {
            w.View.Hold("handslot.l", "dungeon", "torch_lit");
            w.Torch = o.Look.AddLight(w.X, 2.2, w.Z, "#ffa050", 5.5, 10, 0.22, 0);
        }
        walkers.Add(w);
        return w;
    }

    void Remove(Walker w)
    {
        w.Gone = true;
        w.View.Dispose();
        if (w.Torch >= 0) o.Look.SetLit(w.Torch, false);
        foreach (var f in walkers) if (f.Lead == w) { f.Lead = null; f.Leaving = true; GoHome(f); }
    }

    /* -------------------------------------------------------------- ways -- */

    FolkNode Nearest(double x, double z, Func<FolkNode, bool>? filter = null)
    {
        FolkNode? best = null;
        double bd = double.PositiveInfinity;
        foreach (var n in o.Nodes)
        {
            if (filter != null && !filter(n)) continue;
            double d = Dist(n.X, n.Z, x, z);
            if (d < bd) { bd = d; best = n; }
        }
        return best!;
    }

    /// <summary>The lanes from one place to another (breadth first; the town is small).</summary>
    List<FolkNode> Route(FolkNode from, FolkNode to)
    {
        if (from == to) return [to];
        var prev = new Dictionary<string, FolkNode?> { [from.Id] = null };
        var q = new Queue<FolkNode>();
        q.Enqueue(from);
        while (q.Count > 0)
        {
            var n = q.Dequeue();
            if (n == to) break;
            foreach (var m in adj.GetValueOrDefault(n.Id) ?? new()) if (!prev.ContainsKey(m.Id)) { prev[m.Id] = n; q.Enqueue(m); }
        }
        if (!prev.ContainsKey(to.Id)) return [to];
        var out_ = new List<FolkNode>();
        for (FolkNode? n = to; n != null && n != from; n = prev.GetValueOrDefault(n.Id)) out_.Insert(0, n);
        return out_;
    }

    void Send(Walker w, FolkNode dest)
    {
        var from = Nearest(w.X, w.Z);
        w.Path = Route(from, dest);
        // Do not walk back to a node you are already past.
        if (w.Path.Count > 1 && Dist(from.X, from.Z, w.X, w.Z) < 3 && w.Path[0] == from) w.Path.RemoveAt(0);
        w.Dest = dest;
        w.State = "walk";
        w.Best = double.PositiveInfinity; w.StuckT = 0;
    }

    void GoHome(Walker w)
    {
        bool dark = o.Dark();
        // Home is the nearest door; strangers leave by a gate.
        Send(w, Nearest(w.X, w.Z, n => n.Kind == FolkKind.Door || (!dark && n.Kind == FolkKind.Gate)));
    }

    /// <summary>Somewhere to go next, by what there is to do at this hour.</summary>
    void Errand(Walker w)
    {
        bool dark = o.Dark();
        if (w.Role == FolkRole.Child)
        {
            Send(w, Pick(o.Nodes.Where(n => n.Square && n != w.At).ToList()));
            return;
        }
        if (w.Role == FolkRole.Watch)
        {
            w.Round = (w.Round + 1) % o.Round.Length;
            var n = o.Nodes.FirstOrDefault(m => m.Id == o.Round[w.Round]);
            if (n != null) Send(w, n);
            return;
        }
        double Weight(FolkNode n) => n == w.At ? 0 : n.Kind switch
        {
            FolkKind.Stall => dark ? 0 : 3,
            FolkKind.Well => dark ? 0.2 : 1.6,
            FolkKind.Board => 1.2,
            FolkKind.Door => n.Tavern ? (dark ? 5 : 0.8) : dark ? 1.4 : 0.35,
            FolkKind.Gate => dark ? 0 : 0.25,
            _ => 0,
        };
        var pool = o.Nodes.Select(n => (n, v: Weight(n))).Where(p => p.v > 0).ToList();
        double r = rng.NextDouble() * pool.Sum(p => p.v);
        foreach (var (n, v) in pool) { r -= v; if (r <= 0) { Send(w, n); return; } }
        Send(w, pool[0].n);
    }

    /// <summary>What you do when you get there.</summary>
    void Arrive(Walker w, FolkNode n)
    {
        w.At = n;
        w.Dest = null;
        if (w.Lead != null) return; // a companion does what the other one does
        if (w.Leaving && n.Kind is FolkKind.Door or FolkKind.Gate) { HideGroup(w, true); return; }
        switch (n.Kind)
        {
            case FolkKind.Door:
                // In for a while; out again later, or not.
                w.State = "inside"; w.T = Rnd(8, 28);
                HideGroup(w, false);
                return;
            case FolkKind.Gate:
                if (rng.NextDouble() < 0.6) { HideGroup(w, true); return; }
                break;
            case FolkKind.Stall:
                w.State = "busy"; w.T = Rnd(6, 13);
                if (w.Role == FolkRole.Adult) w.View.Act("Interact", 0.8);
                return;
            case FolkKind.Well:
                w.State = "busy"; w.T = Rnd(4.5, 7);
                w.View.Act("PickUp", 0.7);
                w.BucketT = 1.4;
                return;
            case FolkKind.Board:
                w.State = "busy"; w.T = Rnd(4, 9);
                return;
            default:
                if (w.Role == FolkRole.Child)
                {
                    w.State = "busy"; w.T = Rnd(0.4, 2.2);
                    if (rng.NextDouble() < 0.35) w.View.Act("Cheer", 1.2);
                    return;
                }
                if (w.Role == FolkRole.Watch) { w.State = "busy"; w.T = Rnd(2, 5); return; }
                break;
        }
        Errand(w);
    }

    /// <summary>In through a door (for a while, or for good), with whoever walks with you.</summary>
    void HideGroup(Walker w, bool forGood)
    {
        foreach (var f in walkers.Where(m => m == w || m.Lead == w).ToList())
        {
            if (forGood) { f.Gone = true; continue; }
            f.State = "inside"; f.T = w.T;
            f.Shown = false;
            if (f.Carry != null) { f.Carry = null; f.View.Hold("handslot.r", null, null); }
        }
    }

    void Spawn(FolkRole role, double px, double pz, bool scatter)
    {
        bool dark = o.Dark();
        FolkNode at;
        if (scatter)
        {
            // Already out and about when you arrive: anywhere but under your feet.
            var pool = o.Nodes.Where(n => (role == FolkRole.Child ? n.Square : role == FolkRole.Watch ? o.Round.Contains(n.Id) : n.Kind != FolkKind.Door) && Dist(n.X, n.Z, px, pz) > 7).ToList();
            at = Pick(pool.Count > 0 ? pool : o.Nodes);
        }
        else
        {
            // Out of a door (or in at a gate by day), preferably not in your face.
            var pool = o.Nodes.Where(n => (n.Kind == FolkKind.Door || (!dark && n.Kind == FolkKind.Gate)) && Dist(n.X, n.Z, px, pz) > 6).ToList();
            at = Pick(pool.Count > 0 ? pool : o.Nodes);
            if (role == FolkRole.Child) at = Pick(o.Nodes.Where(n => n.Square).ToList());
        }
        var w = Make(role, at);
        if (role == FolkRole.Watch) w.Round = Math.Max(0, Array.IndexOf(o.Round, at.Id));
        if (role == FolkRole.Child)
        {
            var friend = Make(FolkRole.Child, at);
            friend.Lead = w; friend.Side = 0;
            friend.X += 1.5;
        }
        else if (role == FolkRole.Adult && rng.NextDouble() < 0.3)
        {
            var friend = Make(FolkRole.Adult, at);
            friend.Lead = w; friend.Side = rng.NextDouble() < 0.5 ? -1 : 1;
            friend.Speed = w.Speed;
        }
        Errand(w);
        if (scatter && w.Path.Count > 1)
        {
            // Somewhere along the way already.
            int k = rng.Next(w.Path.Count - 1);
            var a = k == 0 ? at : w.Path[k - 1];
            var b = w.Path[k];
            double t = rng.NextDouble();
            w.X = a.X + (b.X - a.X) * t; w.Z = a.Z + (b.Z - a.Z) * t;
            w.Path = w.Path.Skip(k).ToList();
            foreach (var f in walkers) if (f.Lead == w) { f.X = w.X + 0.9; f.Z = w.Z; }
        }
    }

    /* ------------------------------------------------------------ update -- */

    public void Update(double dt, double px, double pz)
    {
        var plan = o.Plan();
        walkers = walkers.Where(w => { if (w.Gone) { Remove(w); return false; } return true; }).ToList();
        // Keep the numbers to the hour.
        List<Walker> Leaders(FolkRole r) => walkers.Where(w => w.Role == r && w.Lead == null && !w.Leaving).ToList();
        var want = new Dictionary<FolkRole, int> { [FolkRole.Adult] = plan.Adults, [FolkRole.Child] = plan.Children > 0 ? 1 : 0, [FolkRole.Watch] = plan.Watch ? 1 : 0 };
        spawnT -= dt;
        foreach (var role in new[] { FolkRole.Adult, FolkRole.Child, FolkRole.Watch })
        {
            var have = Leaders(role);
            if (!started) { for (int i = have.Count; i < want[role]; i++) Spawn(role, px, pz, true); continue; }
            if (have.Count < want[role] && spawnT <= 0) { Spawn(role, px, pz, false); spawnT = Rnd(3, 7); }
            if (have.Count > want[role])
            {
                // The one furthest from you goes home first.
                var w = have.OrderByDescending(a => Dist(a.X, a.Z, px, pz)).First();
                w.Leaving = true;
                if (w.State != "inside") GoHome(w);
                else w.Gone = true;
            }
        }
        started = true;
        barkT -= dt;
        foreach (var w in walkers.ToList()) Step(w, dt, px, pz);
    }

    void Step(Walker w, double dt, double px, double pz)
    {
        var v = w.View;
        if (w.Lead is { Gone: true }) { w.Lead = null; w.Leaving = true; GoHome(w); }
        var lead = w.Lead;
        double y0 = o.Look.HeightAt(w.X, w.Z);
        if (w.State == "inside" || (lead != null && lead.State == "inside"))
        {
            w.Shown = false;
            if (lead != null) { w.X = lead.X; w.Z = lead.Z; w.State = "inside"; v.Place(w.X, y0, w.Z, w.Heading, false); return; }
            w.T -= dt;
            if (w.T <= 0)
            {
                if (w.Leaving) { w.Gone = true; return; }
                w.Shown = true;
                w.State = "walk";
                foreach (var f in walkers) if (f.Lead == w) { f.State = "walk"; f.Shown = true; f.X = w.X + 0.6; f.Z = w.Z; }
                Errand(w);
            }
            v.Place(w.X, y0, w.Z, w.Heading, w.Shown);
            return;
        }
        w.Shown = true;
        // Where this one wants to be.
        double tx = w.X, tz = w.Z, speed = w.Speed;
        double? face = null;
        if (lead != null)
        {
            double lh = Math.Sqrt(lead.Vx * lead.Vx + lead.Vz * lead.Vz) > 0.2 ? Math.Atan2(lead.Vx, lead.Vz) : lead.Heading;
            if (w.Side == 0)
            {
                // A child chasing: straight at the other one.
                tx = lead.X - Math.Sin(lh) * 1.3; tz = lead.Z - Math.Cos(lh) * 1.3;
                speed = lead.Speed * 1.05;
            }
            else
            {
                tx = lead.X + Math.Cos(lh) * 0.95 * w.Side; tz = lead.Z - Math.Sin(lh) * 0.95 * w.Side;
                speed = lead.Speed * 1.15;
            }
            if (lead.State == "busy") face = Math.Atan2(lead.X - w.X, lead.Z - w.Z);
        }
        else if (w.State == "busy")
        {
            w.T -= dt;
            if (w.BucketT > 0 && (w.BucketT -= dt) <= 0 && w.Carry == null)
            {
                w.Carry = "bucket_water";
                v.Hold("handslot.r", "hex_nature", "bucket_water");
            }
            if (w.At.Face is XZ f) face = Math.Atan2(f.X - w.X, f.Z - w.Z);
            // Two walking together talk while they stop.
            var friend = walkers.FirstOrDefault(m => m.Lead == w);
            if (friend != null && w.At.Kind != FolkKind.Stall && w.At.Kind != FolkKind.Well) face = Math.Atan2(friend.X - w.X, friend.Z - w.Z);
            if (w.T <= 0)
            {
                if (w.At.Kind == FolkKind.Stall && rng.NextDouble() < 0.4 && w.Role == FolkRole.Adult) { w.T = Rnd(3, 6); v.Act("Interact", 0.8); }
                else if (w.Leaving) GoHome(w);
                else Errand(w);
            }
        }
        else if (w.Path.Count > 0)
        {
            var n = w.Path[0];
            tx = n.X; tz = n.Z;
            double d = Dist(n.X, n.Z, w.X, w.Z);
            // Not getting any closer (someone in the way, a crate): give up on
            // this waypoint after a while and take the next.
            if (d < w.Best - 0.2) { w.Best = d; w.StuckT = 0; } else w.StuckT += dt;
            if (d < (w.Path.Count > 1 ? 1.2 : 0.45) || w.StuckT > 4)
            {
                w.Path.RemoveAt(0);
                w.Best = double.PositiveInfinity; w.StuckT = 0;
                if (w.Path.Count == 0) Arrive(w, n);
            }
        }
        else if (w.State == "walk") Arrive(w, w.Dest ?? w.At);
        // Steering: toward the target, around the survivor and each other.
        double dx = tx - w.X, dz = tz - w.Z;
        double dist = Math.Sqrt(dx * dx + dz * dz);
        double wantV = w.State == "busy" && lead == null ? 0 : Math.Min(speed, dist * (lead != null ? 1.8 : 3));
        if (lead != null && dist < 0.25) wantV = 0;
        double ax = dist > 1e-3 ? dx / dist * wantV : 0, az = dist > 1e-3 ? dz / dist * wantV : 0;
        if (wantV > 0.2)
        {
            // Something solid just ahead: turn along it, the same way each
            // time until clear, so nobody dithers against a crate. (A thinner
            // probe than the body, so sliding along a wall reads as free.)
            double ux = ax / wantV, uz = az / wantV;
            w.DetourT -= dt;
            if (o.Col.Blocked(w.X + ux * 0.75, w.Z + uz * 0.75, 0.18, true))
            {
                if (w.DetourT <= 0) w.Detour = rng.NextDouble() < 0.5 ? 1 : -1;
                w.DetourT = 0.8;
                foreach (var a in new[] { 0.5, 0.9, 1.3, 1.7, 2.2 })
                {
                    double ang = a * w.Detour, c = Math.Cos(ang), sn = Math.Sin(ang);
                    double rx = ux * c - uz * sn, rz = ux * sn + uz * c;
                    if (!o.Col.Blocked(w.X + rx * 0.75, w.Z + rz * 0.75, 0.18, true)) { ax = rx * wantV; az = rz * wantV; break; }
                }
            }
        }
        double pdx = w.X - px, pdz = w.Z - pz, pd = Math.Sqrt(pdx * pdx + pdz * pdz);
        if (pd < 1.7 && pd > 1e-3)
        {
            // Step aside: away from you, and to the side if you are in the way.
            double push = (1.7 - pd) * 3.2;
            ax += pdx / pd * push; az += pdz / pd * push;
            if (wantV > 0.3 && ax * -pdx + az * -pdz > 0) { ax += -pdz / pd * 1.2; az += pdx / pd * 1.2; }
        }
        foreach (var other in walkers)
        {
            if (other == w || other.State == "inside" || other == lead || other.Lead == w) continue;
            double ox = w.X - other.X, oz = w.Z - other.Z, od = Math.Sqrt(ox * ox + oz * oz);
            if (od < 0.85 && od > 1e-3) { ax += ox / od * (0.85 - od) * 4; az += oz / od * (0.85 - od) * 4; }
        }
        double k = Math.Min(1, dt * 6);
        w.Vx += (ax - w.Vx) * k; w.Vz += (az - w.Vz) * k;
        w.X += w.Vx * dt; w.Z += w.Vz * dt;
        o.Col.Resolve(ref w.X, ref w.Z, 0.32);
        double sp = Math.Sqrt(w.Vx * w.Vx + w.Vz * w.Vz);
        v.Locomotion(sp);
        double heading = sp > 0.3 ? Math.Atan2(w.Vx, w.Vz) : face ?? (pd < 4 ? Math.Atan2(px - w.X, pz - w.Z) : w.Heading);
        w.Heading = MathX.DampAngle(w.Heading, heading, 6, dt);
        double y = o.Look.HeightAt(w.X, w.Z);
        v.Place(w.X, y, w.Z, w.Heading, true);
        if (w.Torch >= 0)
        {
            // The light goes where the torch goes (in the left hand).
            bool dark = o.Dark();
            o.Look.MoveLight(w.Torch, w.X + Math.Cos(w.Heading) * 0.35, y + 1.9, w.Z - Math.Sin(w.Heading) * 0.35);
            o.Look.SetLit(w.Torch, dark);
        }
        Bark(w, dt, pd, y);
    }

    /// <summary>Something said as you pass: the town's opinion, or the weather.</summary>
    void Bark(Walker w, double dt, double pd, double y)
    {
        w.BarkT -= dt;
        if (pd > 4.2 || pd < 1 || w.BarkT > 0 || barkT > 0 || w.Lead != null) return;
        var lines = o.Lines(w.Role).Where(l => !said.Contains(l.Text)).ToList();
        if (lines.Count == 0) return;
        // News first, while it is fresh.
        var news = lines.Where(l => l.When != null || l.Died == true).ToList();
        var pool = news.Count > 0 && rng.NextDouble() < 0.7 ? news : lines;
        var line = Pick(pool);
        said.Add(line.Text);
        if (said.Count > 8) said.RemoveAt(0);
        w.BarkT = Rnd(40, 80);
        barkT = Rnd(7, 13);
        o.Look.Bark(line.Text, w.X, y + 0.2, w.Z, voice: w.Sex == Sex.Female ? "f" : "m");
    }

    public void Dispose()
    {
        foreach (var w in walkers) if (!w.Gone) Remove(w);
        walkers.Clear();
    }
}
