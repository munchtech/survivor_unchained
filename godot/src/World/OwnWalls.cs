using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// Our own town walls (E9b1; tools/assets/env_house.py, art/world/house): each KayKit village wall, corner,
/// window, door and shutter piece of a zone's props.json drawn as one of our presets, built in the kit
/// piece's own frame and box (so it tiles on the 2 m grid and the 3 m storey), all on one trim sheet
/// (house_albedo.jpg, house_normal.png, house_aux.png) and one material (kit.gdshader's OWN_WALL, KitLook.Wall).
///
/// The zone's props_own.json "walls": "pieces" maps a kit piece to its presets as treatments (a list of lists:
/// a house takes the list of its treatment, each copy one preset of it by its place, so a run of wall doesn't
/// repeat); an empty list drops the kit piece (its glass, frame or door is in our piece). "houses" gives each
/// house (props.json's "h", tools/godot/house_ids.py) its plaster tint and its timber treatment, so neighbors differ.
/// Each copy's custom data: r its tint ((i + 0.5) / 8), g its height above its house's ground (the grime rises
/// from the ground, not from each storey's foot), b its own hash (value), a its treatment.
/// One MultiMesh per preset per square of the props' cells, as the kit pieces are drawn.
///
/// Roofs (E9b2; tools/assets/env_roof.py, KitLook.Roof): the roof bodies, spires and chimneys "by_roof" lists take the list
/// of their house's roof covering (its third number: 0 clay pantiles, 1 oak shingles) and carry its roof tint (the fourth)
/// in their custom data's a ((treatment * 8 + roof tint + 0.5) / 32); the gable fronts take their house's treatment's list
/// like the walls. Each chimney's top goes to KitLook.SetChimneys (the soot round it on the roofs).
/// --walls-kit: the kit's walls as they were (before/after measures).
/// </summary>
public sealed class OwnWalls
{
    public const string Dir = "res://art/world/house";

    readonly Dictionary<string, string[][]> pieces = new();
    readonly Dictionary<int, (int Tint, int Style, int Roof, int RoofTint)> houses = new();
    readonly HashSet<string> byRoof = new();
    readonly Dictionary<int, float> ground = new();
    // (E9b4) corner pieces the kit set in the middle of a straight run (the town walls' joints every 8 m): drawn as
    // piers in their wall's frame, the lower storey's ("pier_lo") or the top one's ("pier_hi"), not as an outer
    // corner's quoins (which stood in the face like a post crossing the coping)
    readonly Dictionary<(int, int, int), (Basis Wall, bool Top)> piers = new();
    static (int, int, int) Key(Vector3 p) => (Mathf.RoundToInt(p.X * 4), Mathf.RoundToInt(p.Y * 4), Mathf.RoundToInt(p.Z * 4));
    ZoneData? zone;
    readonly List<(Vector3 At, float Foot)> feet = new();
    readonly Dictionary<(string Preset, int X, int Z), List<(Transform3D At, Color Data, int House, bool Roof)>> groups = new();
    static readonly Dictionary<string, List<(Mesh Mesh, Transform3D Local)>> parts = new();

    /// <summary>The zone's own walls, or null if it has none (or --walls-kit, --props-own-off).</summary>
    public static OwnWalls? For(ZoneData z)
    {
        if (SurvivorUnchained.Args.Has("walls-kit") || SurvivorUnchained.Args.Has("props-own-off")) return null;
        var path = $"res://data/zones/{z.Id}/props_own.json";
        if (!FileAccess.FileExists(path)) return null;
        using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(path));
        if (!doc.RootElement.TryGetProperty("walls", out var w) || !w.TryGetProperty("pieces", out var ps)) return null;
        var o = new OwnWalls { zone = z };
        foreach (var p in ps.EnumerateObject())
            o.pieces[p.Name] = p.Value.EnumerateArray().Select(g => g.EnumerateArray().Select(s => s.GetString()!).ToArray()).ToArray();
        if (w.TryGetProperty("houses", out var hs))
            foreach (var h in hs.EnumerateObject())
                o.houses[int.Parse(h.Name)] = (h.Value[0].GetInt32(), h.Value[1].GetInt32(),
                    h.Value.GetArrayLength() > 2 ? h.Value[2].GetInt32() : 0, h.Value.GetArrayLength() > 3 ? h.Value[3].GetInt32() : 0);
        if (w.TryGetProperty("by_roof", out var br))
            foreach (var id in br.EnumerateArray()) o.byRoof.Add(id.GetString()!);
        // each house's ground: its lowest wall piece's foot
        for (int i = 0; i < z.Props.Count && i < z.PropHouse.Count; i++)
        {
            int h = z.PropHouse[i];
            if (h < 0 || !o.houses.ContainsKey(h) || !o.pieces.ContainsKey(z.Props[i].Id)) continue;
            float y = z.Props[i].At.Origin.Y;
            o.ground[h] = o.ground.TryGetValue(h, out var g) ? Mathf.Min(g, y) : y;
        }
        // the mid-run corners: a wall piece each side of it, opposite, on its storey
        var walls = z.Props.Where(p => p.Id.StartsWith("village/Wall_")).Select(p => p.At).ToList();
        var corners = z.Props.Where(p => p.Id.StartsWith("village/Corner_Exterior")).Select(p => p.At.Origin).ToList();
        foreach (var c in corners)
        {
            var near = walls.Where(t => Mathf.Abs(t.Origin.Y - c.Y) < 0.3f && new Vector2(t.Origin.X - c.X, t.Origin.Z - c.Z).Length() is > 0.5f and < 1.3f).ToList();
            var pair = near.FirstOrDefault(a => near.Any(b => (new Vector2(a.Origin.X + b.Origin.X - 2 * c.X, a.Origin.Z + b.Origin.Z - 2 * c.Z)).Length() < 0.3f));
            if (pair.Basis == default) continue;
            bool top = !corners.Any(u => u.Y > c.Y + 2.5f && u.Y < c.Y + 3.5f && new Vector2(u.X - c.X, u.Z - c.Z).Length() < 0.4f);
            o.piers[Key(c)] = (pair.Basis, top);
        }
        return o;
    }

    /// <summary>(E9c2) A closed house's inside, for the cutaway (HouseFade cuts it to its footing): its frame (world to
    /// the house's: x along its walls, z across), its walls' outer rectangle there, its floor's height, the 2 m cells
    /// its walls close round (an L's notch left out), its chimneys and doors (house frame).</summary>
    public sealed class Inside
    {
        public int House;
        public Transform3D To;
        public Rect2 R;
        public float Ground, Floor;
        public readonly List<Rect2> Cells = new();
        public readonly List<Vector2> Chimneys = new(), Doors = new();
        public Aabb World;
        public bool Holds(Vector3 p, float inset = 0.1f)
        {
            if (!World.Grow(0.1f).HasPoint(p with { Y = World.Position.Y + 0.01f })) return false;
            var q = To * p;
            var v = new Vector2(q.X, q.Z);
            foreach (var c in Cells) if (c.Grow(-inset).HasPoint(v)) return true;
            return false;
        }
    }

    static readonly Dictionary<string, List<Inside>> insides = new();

    /// <summary>(E9c2) The zone's closed houses' insides (none where the zone has no walls of ours).</summary>
    public static List<Inside> InsidesOf(ZoneData z)
    {
        if (insides.TryGetValue(z.Id, out var list)) return list;
        insides[z.Id] = list = new();
        if (SurvivorUnchained.Args.Has("walls-kit") || SurvivorUnchained.Args.Has("props-own-off")
            || !FileAccess.FileExists($"res://data/zones/{z.Id}/props_own.json")) return list;
        var walls = new Dictionary<int, List<Transform3D>>();
        var extra = new Dictionary<int, List<(string Id, Vector3 At)>>();
        for (int i = 0; i < z.Props.Count && i < z.PropHouse.Count; i++)
        {
            int h = z.PropHouse[i];
            if (h < 0) continue;
            var (id, at) = z.Props[i];
            if (id.StartsWith("village/Wall_")) { if (!walls.TryGetValue(h, out var l)) walls[h] = l = new(); l.Add(at); }
            if (id.StartsWith("village/Door_1") || id == "village/Prop_Chimney")
            { if (!extra.TryGetValue(h, out var l)) extra[h] = l = new(); l.Add((id, at.Origin)); }
        }
        foreach (var (h, ws) in walls)
        {
            float g = ws.Min(t => t.Origin.Y);
            var lo = ws.Where(t => t.Origin.Y < g + 0.5f).ToList();
            double sx = 0, sy = 0;
            foreach (var t in lo) { double a = 4 * Mathf.Atan2(t.Basis.Column0.Z, t.Basis.Column0.X); sx += System.Math.Cos(a); sy += System.Math.Sin(a); }
            var to = new Transform3D(new Basis(Vector3.Up, (float)System.Math.Atan2(sy, sx) / 4), Vector3.Zero);
            var pts = lo.Select(t => to * t.Origin).ToList();
            float u0 = pts.Min(p => p.X), u1 = pts.Max(p => p.X), v0 = pts.Min(p => p.Z), v1 = pts.Max(p => p.Z);
            // (a run of town wall, or a lean-to's single face: no inside)
            if (u1 - u0 < 2.5f || v1 - v0 < 2.5f) continue;
            // the wall's outer face is the pieces' origin line, so the corner pieces' origins sit a half piece in:
            // the outer rectangle runs to the walls' far faces (a 2 m piece's ends, from the walls across it)
            var ins = new Inside { House = h, To = to, R = new Rect2(u0, v0, u1 - u0, v1 - v0), Ground = g };
            int nx = Mathf.Max(1, Mathf.RoundToInt((u1 - u0) / 2f)), nz = Mathf.Max(1, Mathf.RoundToInt((v1 - v0) / 2f));
            float cw = (u1 - u0) / nx, ch = (v1 - v0) / nz;
            for (int j = 0; j < nz; j++)
                for (int i = 0; i < nx; i++)
                {
                    float cu = u0 + (i + 0.5f) * cw, cv = v0 + (j + 0.5f) * ch;
                    bool l = pts.Any(p => Mathf.Abs(p.Z - cv) < ch * 0.55f && p.X < cu - 0.3f), r = pts.Any(p => Mathf.Abs(p.Z - cv) < ch * 0.55f && p.X > cu + 0.3f);
                    bool d = pts.Any(p => Mathf.Abs(p.X - cu) < cw * 0.55f && p.Z < cv - 0.3f), up = pts.Any(p => Mathf.Abs(p.X - cu) < cw * 0.55f && p.Z > cv + 0.3f);
                    if (l && r && d && up) ins.Cells.Add(new Rect2(u0 + i * cw, v0 + j * ch, cw, ch));
                }
            if (ins.Cells.Count == 0) continue;
            // the floor: the house's ground, raised to the terrain where it stands higher inside (at most 0.4 m)
            float top = g;
            var back = to.AffineInverse();
            foreach (var c in ins.Cells)
                for (int k = 0; k < 9; k++)
                {
                    var p = back * new Vector3(c.Position.X + c.Size.X * (0.15f + 0.35f * (k % 3)), 0, c.Position.Y + c.Size.Y * (0.15f + 0.35f * (k / 3)));
                    top = Mathf.Max(top, z.HeightAt(p.X, p.Z));
                }
            ins.Floor = Mathf.Min(top, g + 0.4f) + 0.02f;
            foreach (var (id, at) in extra.TryGetValue(h, out var ex) ? ex : new())
            {
                var q = to * at;
                (id.StartsWith("village/Door") ? ins.Doors : ins.Chimneys).Add(new Vector2(q.X, q.Z));
            }
            var wb = new Aabb(back * new Vector3(u0, g, v0), Vector3.Zero);
            foreach (var cq in new[] { new Vector3(u1, g, v0), new Vector3(u0, g, v1), new Vector3(u1, g + 3f, v1) }) wb = wb.Expand(back * cq);
            ins.World = wb;
            list.Add(ins);
        }
        GD.Print($"house insides: {list.Count} ({list.Sum(i => i.Cells.Count)} cells)");
        return list;
    }

    /// <summary>(E9c2) Whether a point is inside one of the zone's closed houses (nothing grows or lies there).</summary>
    public static bool InsideAny(ZoneData z, float x, float zz, float inset = 0.1f)
    {
        var l = InsidesOf(z);
        if (l.Count == 0) return false;
        var p = new Vector3(x, 0, zz);
        foreach (var i in l) if (i.Holds(p, inset)) return true;
        return false;
    }

    /// <summary>(E9c2, E9c3) What furnishes each inside: a floor of boards (or flags, one house in three) on its cells; a hearth
    /// under its chimney ("hearth": Campfire's stone ring, ash bed, logs and embers, a low ember light) with the cauldron and
    /// a log pile beside it; a bed of ours ("own:bed") in the corner farthest from the doors (a big house; else a chest), a
    /// chest at its foot and a rug by it; a table with a bench and a stool on a rug in the middle where the room is big
    /// enough; what a house keeps along its walls (barrels, sacks, crates, a low cupboard, a workbench, apple tubs, pots), backs
    /// to the wall, in runs with gaps, never before a door; strewn rushes ("straw") on the floor left. All under the cut
    /// (0.9 m). Each inside's bare floor (nothing of these over it; its share of the floor inside the walls) is in Bare.</summary>
    public static List<(string Id, Transform3D At)> Furnish(ZoneData z)
    {
        var o = new List<(string, Transform3D)>();
        Bare.Clear();
        Tables.Clear();
        Hearth.Clear();
        foreach (var ins in InsidesOf(z))
        {
            var back = ins.To.AffineInverse();
            uint hh = (uint)(ins.House * 2654435761u);
            uint seq = hh;
            float Rnd() { seq = seq * 1664525u + 1013904223u; return (seq >> 8) / 16777216f; }
            string floor = hh % 3 == 1 ? "village/Floor_UnevenBrick" : "village/Floor_WoodLight";
            Transform3D At(float u, float v, float y, float yaw, Vector3? scale = null)
            {
                var b = new Basis(Vector3.Up, yaw);
                if (scale is Vector3 s) b = b.Scaled(s);
                return new Transform3D(back.Basis * b, back * new Vector3(u, y, v));
            }
            foreach (var c in ins.Cells)
                o.Add((floor, At(c.GetCenter().X, c.GetCenter().Y, ins.Floor, (hh >> 3) % 2 == 0 ? 0 : Mathf.Pi, new Vector3(c.Size.X / 2f, 1, c.Size.Y / 2f))));
            var r = ins.R;
            const float wall = 0.36f;
            var inner = r.Grow(-wall);
            var used = new List<Rect2>();
            var covers = new List<(Rect2 R, float Share)>();
            bool Inside(Rect2 q) => inner.Grow(0.01f).Encloses(q) && CellsCover(ins, q);
            bool Free(Rect2 q, float door = 0.9f) => !used.Any(u => u.Intersects(q)) && Inside(q) && !ins.Doors.Any(d => q.Grow(door).HasPoint(d));
            void Take(Rect2 q, float share = 1f) { used.Add(q); covers.Add((q, share)); }
            var clear = new List<Rect2>();
            // the hearth: under the chimney, against its nearest wall
            foreach (var ch in ins.Chimneys.Take(1))
            {
                float du0 = ch.X - r.Position.X, du1 = r.End.X - ch.X, dv0 = ch.Y - r.Position.Y, dv1 = r.End.Y - ch.Y;
                float m = Mathf.Min(Mathf.Min(du0, du1), Mathf.Min(dv0, dv1));
                const float hr = 0.58f;
                float u = Mathf.Clamp(ch.X, inner.Position.X + hr + 0.1f, inner.End.X - hr - 0.1f), v = Mathf.Clamp(ch.Y, inner.Position.Y + hr + 0.1f, inner.End.Y - hr - 0.1f);
                if (m == du0) u = inner.Position.X + hr + 0.12f; else if (m == du1) u = inner.End.X - hr - 0.12f;
                else if (m == dv0) v = inner.Position.Y + hr + 0.12f; else v = inner.End.Y - hr - 0.12f;
                var hq = new Rect2(u - hr, v - hr, 2 * hr, 2 * hr);
                // (E9d r2) on a hearthstone of laid brick where the floor is boards: no fire on bare planks
                if (floor != "village/Floor_UnevenBrick")
                    o.Add(("village/Floor_UnevenBrick", At(u, v, ins.Floor + 0.012f, (hh >> 2) % 2 == 0 ? 0 : Mathf.Pi / 2, new Vector3(hr + 0.22f, 1, hr + 0.22f))));
                o.Add(("hearth", At(u, v, ins.Floor, (hh % 7) * 0.9f)));
                Hearth[ins.House] = new Vector2(u, v);
                Take(hq.Grow(0.12f), 0.9f);
                clear.Add(hq.Grow(0.12f));
                // the cauldron and the log pile either side of it, along its wall
                bool alongU = m == dv0 || m == dv1;
                var side = alongU ? new Vector2(1, 0) : new Vector2(0, 1);
                var into = alongU ? new Vector2(0, m == dv0 ? 1 : -1) : new Vector2(m == du0 ? 1 : -1, 0);
                float wallYaw = Mathf.Atan2(into.X, into.Y);
                for (int s = -1; s <= 1; s += 2)
                {
                    bool pot = s == ((hh >> 4) % 2 == 0 ? -1 : 1);
                    // (E9c4: the cauldron clear of the hearth's taken ring, 0.7 m: at 1.12 m it never fit, so none stood)
                    var cp = new Vector2(u, v) + side * s * (pot ? 1.24f : 1.08f);
                    var half = pot ? new Vector2(0.5f, 0.5f) : (alongU ? new Vector2(0.32f, 0.5f) : new Vector2(0.5f, 0.32f));
                    var q = new Rect2(cp - half, half * 2);
                    if (!Free(q, 0.6f)) continue;
                    if (pot) o.Add(("props/Cauldron", At(cp.X, cp.Y, ins.Floor, (hh % 5) * 1.2f)));
                    else
                    {
                        // (sawn logs stacked end on to the wall, E9c4: three side by side below, two in their hollows, each
                        // a little askew and its sawn ends out, so the pile reads as logs, not a slab)
                        for (int li = 0; li < 5; li++)
                        {
                            float k = li < 3 ? (li - 1) * 0.21f : (li - 3.5f) * 0.21f;
                            float y = li < 3 ? 0f : 0.15f;
                            float sl = ((int)((hh >> (li + 2)) % 5) - 2) * 0.05f;
                            o.Add(("own:log_short", At(cp.X + side.X * k + into.X * sl, cp.Y + side.Y * k + into.Y * sl, ins.Floor + y,
                                wallYaw + Mathf.Pi / 2 + ((int)((hh >> (li * 3)) % 7) - 3) * 0.035f, Vector3.One * 0.42f)));
                        }
                    }
                    Take(q);
                }
            }
            var door = ins.Doors.Count > 0 ? ins.Doors : new List<Vector2> { r.GetCenter() };
            var corners = new[] { r.Position, new Vector2(r.End.X, r.Position.Y), new Vector2(r.Position.X, r.End.Y), r.End }
                .OrderByDescending(c => door.Min(d => d.DistanceTo(c))).ToList();
            bool big = r.Area >= 40f;
            // the bed (a big house; else a chest) in the corner farthest from the doors, its head to the wall across
            foreach (var c in corners)
            {
                float su = c.X < r.GetCenter().X ? 1 : -1, sv = c.Y < r.GetCenter().Y ? 1 : -1;
                if (big)
                {
                    var half = new Vector2(0.93f, 1.22f);
                    var at = new Vector2(c.X + su * (wall + half.X + 0.06f), c.Y + sv * (wall + half.Y + 0.04f));
                    var q = new Rect2(at - half, half * 2);
                    if (!Free(q)) continue;
                    // (its head, local -z, to the wall at sv)
                    o.Add(("own:bed", At(at.X, at.Y, ins.Floor, sv > 0 ? 0 : Mathf.Pi)));
                    Take(q);
                    // a chest at its foot, a rug along its open side
                    var cq = new Rect2(at.X - 0.5f, at.Y + sv * (half.Y + 0.45f) - 0.33f, 1.0f, 0.66f);
                    if (Free(cq, 0.6f)) { o.Add(("own:chest", At(cq.GetCenter().X, cq.GetCenter().Y, ins.Floor, sv > 0 ? Mathf.Pi : 0, Vector3.One * 0.85f))); Take(cq); }
                    var rq = new Rect2(at.X + su * (half.X + 0.6f) - 0.55f, at.Y - 0.95f, 1.1f, 1.9f);
                    if (Free(rq, 0.4f)) { o.Add(("rug", At(rq.GetCenter().X, rq.GetCenter().Y, ins.Floor + 0.025f, 0, new Vector3(0.55f, 1, 0.95f)))); Take(rq); clear.Add(rq); }
                }
                else
                {
                    var half = new Vector2(0.64f, 0.38f);
                    var at = new Vector2(c.X + su * (wall + half.X + 0.05f), c.Y + sv * (wall + half.Y + 0.05f));
                    var q = new Rect2(at - half, half * 2);
                    if (!Free(q)) continue;
                    o.Add(("props/Chest_Wood", At(at.X, at.Y, ins.Floor, sv > 0 ? 0 : Mathf.Pi)));
                    Take(q);
                }
                break;
            }
            // a table on a rug, a bench along it and a stool, in the middle where the room is 4 by 3.5 m or more (E9c4: the
            // free spot nearest the middle, either way round, clear of the walls by a bench's width, not only the middle itself)
            if (r.Size.X >= 4f && r.Size.Y >= 3.5f || r.Size.Y >= 4f && r.Size.X >= 3.5f)
            {
                var mid = r.GetCenter() + new Vector2(((int)((hh >> 5) % 5) - 2) * 0.15f, ((int)((hh >> 9) % 5) - 2) * 0.15f);
                bool longU = r.Size.X >= r.Size.Y;
                var spots = new List<(Vector2 C, bool U, float D)>();
                for (float cu = inner.Position.X; cu <= inner.End.X; cu += 0.2f)
                    for (float cv = inner.Position.Y; cv <= inner.End.Y; cv += 0.2f)
                        foreach (var u in new[] { longU, !longU })
                            spots.Add((new Vector2(cu, cv), u, new Vector2(cu, cv).DistanceTo(mid) + (u == longU ? 0f : 0.6f)));
                foreach (var (c, alongU, _) in spots.OrderBy(sp => sp.D))
                {
                    var th = alongU ? new Vector2(1.42f, 0.55f) : new Vector2(0.55f, 1.42f);
                    var q = new Rect2(c - th, th * 2);
                    if (!Free(q) || !Inside(q.Grow(0.45f)) || used.Any(uu => uu.Intersects(q.Grow(0.45f)))) continue;
                    // (the rug under it, as big as the room lets it be)
                    var rh = alongU ? new Vector2(1.75f, 1.2f) : new Vector2(1.2f, 1.75f);
                    var rq = new Rect2(c - rh, rh * 2);
                    for (int k = 0; k < 5 && !Free(rq, 0.2f); k++) { rh *= 0.9f; rq = new Rect2(c - rh, rh * 2); }
                    if (Free(rq, 0.2f)) { o.Add(("rug", At(c.X, c.Y, ins.Floor + 0.025f, alongU ? Mathf.Pi / 2 : 0, new Vector3(alongU ? rh.Y : rh.X, 1, alongU ? rh.X : rh.Y)))); covers.Add((rq, 1f)); clear.Add(rq); }
                    o.Add(("props/Table_Large", At(c.X, c.Y, ins.Floor, alongU ? 0 : Mathf.Pi / 2)));
                    Take(q);
                    Tables.Add(ins.House);
                    var off = alongU ? new Vector2(0, 0.85f) : new Vector2(0.85f, 0);
                    var bh = alongU ? new Vector2(1.39f, 0.27f) : new Vector2(0.27f, 1.39f);
                    var bq = new Rect2(c - off - bh, bh * 2);
                    if (Free(bq, 0.5f)) { o.Add(("props/Bench", At(c.X - off.X, c.Y - off.Y, ins.Floor, alongU ? 0 : Mathf.Pi / 2))); Take(bq); }
                    var s = c + off + (alongU ? new Vector2(0.5f, 0) : new Vector2(0, 0.5f));
                    var sq = new Rect2(s - new Vector2(0.25f, 0.25f), new Vector2(0.5f, 0.5f));
                    if (Free(sq, 0.5f)) { o.Add(("props/Stool", At(s.X, s.Y, ins.Floor, (hh % 11) * 0.5f))); Take(sq); }
                    // (a second stool across the end, where it fits)
                    var s2 = c + (alongU ? new Vector2(-(th.X + 0.4f), 0.1f) : new Vector2(0.1f, -(th.Y + 0.4f)));
                    var sq2 = new Rect2(s2 - new Vector2(0.25f, 0.25f), new Vector2(0.5f, 0.5f));
                    if (Free(sq2, 0.5f)) { o.Add(("props/Stool", At(s2.X, s2.Y, ins.Floor, (hh % 13) * 0.7f))); Take(sq2); }
                    break;
                }
            }
            // along the walls: runs of what a house keeps, backs to the wall, gaps between, never before a door
            var kinds = new (string Id, Vector2 Half, float Scale)[]
            {
                ("props/Barrel", new(0.36f, 0.36f), 1f), ("props/Bag", new(0.34f, 0.3f), 1f), ("props/Crate_Wooden", new(0.56f, 0.58f), 0.8f),
                ("props/Cabinet", new(0.68f, 0.19f), 0.88f), ("props/Workbench", new(1.01f, 0.51f), 1f), ("props/Barrel_Apples", new(0.35f, 0.35f), 0.6f),
                ("props/FarmCrate_Apple", new(0.36f, 0.22f), 1f), ("props/Pot_1", new(0.28f, 0.25f), 1f), ("props/Pot_1", new(0.28f, 0.25f), 0.9f),
                ("props/Nightstand_Shelf", new(0.35f, 0.2f), 0.72f), ("props/FarmCrate_Empty", new(0.36f, 0.22f), 1f),
            };
            // (runs: a few of one kind together, then something else)
            int[][] runs = { new[] { 0, 0 }, new[] { 1, 1, 1 }, new[] { 3 }, new[] { 2, 6 }, new[] { 4, 5 }, new[] { 0, 5 }, new[] { 9, 7 }, new[] { 2, 10, 1 }, new[] { 8, 0 }, new[] { 1, 0, 1 } };
            int ri = (int)(hh % (uint)runs.Length);
            for (int sideI = 0; sideI < 4; sideI++)
            {
                // the side's inner edge: along u (v fixed) or along v; into the room
                bool alongU = sideI < 2;
                float fixedC = sideI switch { 0 => inner.Position.Y, 1 => inner.End.Y, 2 => inner.Position.X, _ => inner.End.X };
                var into = sideI switch { 0 => new Vector2(0, 1), 1 => new Vector2(0, -1), 2 => new Vector2(1, 0), _ => new Vector2(-1, 0) };
                // (the piece's front, local +z, into the room)
                float yaw = Mathf.Atan2(into.X, into.Y);
                float a0 = alongU ? inner.Position.X : inner.Position.Y, a1 = alongU ? inner.End.X : inner.End.Y;
                float t = a0 + 0.05f + Rnd() * 0.3f;
                while (t < a1 - 0.3f)
                {
                    var run = runs[ri++ % runs.Length];
                    float t0 = t;
                    bool any = false;
                    foreach (var ki in run)
                    {
                        var (id, h0, sc) = kinds[ki];
                        float along = h0.X * sc, across = h0.Y * sc;
                        float ct = t + along, cn = fixedC + (alongU ? into.Y : into.X) * (across + 0.03f);
                        var cp = alongU ? new Vector2(ct, cn) : new Vector2(cn, ct);
                        var half = alongU ? new Vector2(along, across) : new Vector2(across, along);
                        var q = new Rect2(cp - half, half * 2);
                        if (ct + along > a1 || !Free(q, 0.75f)) { t += 0.25f; continue; }
                        // (a little off square: a barrel or a sack turned, a crate nudged)
                        bool round = id.Contains("Barrel") || id.Contains("Bag") || id.Contains("Pot") || id.Contains("Vase") || id.Contains("Bucket");
                        float jy = round ? Rnd() * Mathf.Tau : (Rnd() - 0.5f) * 0.12f;
                        // (E9c4: the apple tub a short barrel cut down, its fill showing, for the kit's pale empty bucket ring)
                        // (E9d: the kit's pot read as a pale empty ring from above: our own earthenware crock; the round things
                        // set in and out from the wall and a little different in size, so a run of barrels isn't a ruler-straight row)
                        if (round) { cp += (alongU ? new Vector2(0, into.Y) : new Vector2(into.X, 0)) * (Rnd() * 0.09f); sc *= 0.93f + Rnd() * 0.12f; }
                        if (id == "props/Barrel_Apples") { o.Add(("own:basket_apples", At(cp.X, cp.Y, ins.Floor, yaw + jy, Vector3.One * 1.25f))); Take(q); t += 2 * along + 0.04f + Rnd() * 0.08f; any = true; continue; }
                        if (id == "props/Pot_1") { o.Add(("own:crock", At(cp.X, cp.Y, ins.Floor, yaw + jy, Vector3.One * sc * 1.1f))); Take(q); t += 2 * along + 0.04f + Rnd() * 0.08f; any = true; continue; }
                        o.Add((id, At(cp.X, cp.Y, ins.Floor, yaw + jy, id.EndsWith("Apples") ? new Vector3(sc, sc * 0.72f, sc) : Vector3.One * sc)));
                        Take(q);
                        t += 2 * along + 0.04f + Rnd() * 0.08f;
                        any = true;
                    }
                    // (a gap after each run: wider where the room is small)
                    t += any ? (big ? 0.3f : 0.55f) + Rnd() * 0.5f : 0.0f;
                    if (t <= t0) t = t0 + 0.25f;
                }
            }
            // rushes strewn on the floor left (E9c4: clumped along the walls and about the hearth, the middle's boards left
            // bare): patches on a 0.9 m grid where nothing stands, by a wall (within 1 m) or the hearth (1.8 m), ragged (the
            // shader); some left bare
            var hearthAt = Hearth.TryGetValue(ins.House, out var hat) ? hat : (Vector2?)null;
            for (float pu = inner.Position.X + 0.02f; pu < inner.End.X - 0.4f; pu += 0.9f)
                for (float pv = inner.Position.Y + 0.02f; pv < inner.End.Y - 0.4f; pv += 0.9f)
                {
                    var q = new Rect2(pu, pv, Mathf.Min(0.9f, inner.End.X - pu - 0.02f), Mathf.Min(0.9f, inner.End.Y - pv - 0.02f));
                    // (under and around what stands by the walls, as rushes lie: only the hearth's ring and the rugs kept clear)
                    if (!Inside(q) || clear.Any(u => u.Intersects(q.Grow(-0.2f)))) continue;
                    var qc = q.GetCenter();
                    float toWall = Mathf.Min(Mathf.Min(qc.X - inner.Position.X, inner.End.X - qc.X), Mathf.Min(qc.Y - inner.Position.Y, inner.End.Y - qc.Y));
                    bool byHearth = hearthAt is Vector2 hp && qc.DistanceTo(hp) < 1.8f;
                    if (toWall > 1.0f && !byHearth) continue;
                    if (Rnd() < 0.3f) continue;
                    o.Add(("straw", At(qc.X, qc.Y, ins.Floor + 0.018f, Mathf.Floor(Rnd() * 4) * Mathf.Pi / 2, new Vector3(q.Size.X * 0.62f, 1, q.Size.Y * 0.62f))));
                    covers.Add((q, 0.4f));
                }
            Bare[ins.House] = BareShare(ins, inner, covers);
        }
        GD.Print($"house insides furnished: {string.Join(", ", o.GroupBy(x => x.Item1).Select(g => $"{g.Key} {g.Count()}"))}");
        GD.Print($"house insides furnished: tables in {string.Join(" ", Tables.OrderBy(t => t))}; none in {string.Join(" ", Bare.Keys.Where(k => !Tables.Contains(k)).OrderBy(k => k))}");
        GD.Print($"house insides furnished: bare floor {string.Join(" ", Bare.OrderBy(b => b.Key).Select(b => $"{b.Key}:{b.Value:0.00}"))}");
        return o;
    }

    /// <summary>(E9c3) Each furnished inside's bare floor share (house id: 0..1), as Furnish left it.</summary>
    public static readonly Dictionary<int, float> Bare = new();
    /// <summary>(E9c4) The furnished insides given a table (house ids).</summary>
    public static readonly HashSet<int> Tables = new();
    static readonly Dictionary<int, Vector2> Hearth = new();

    // (every corner of q in one of the cells: an L's notch is not floor)
    static bool CellsCover(Inside ins, Rect2 q)
    {
        foreach (var p in new[] { q.Position, q.End, new Vector2(q.Position.X, q.End.Y), new Vector2(q.End.X, q.Position.Y) })
            if (!ins.Cells.Any(c => c.Grow(0.02f).HasPoint(p))) return false;
        return true;
    }

    /// <summary>The share of the floor inside the walls nothing furnishes (a 10 cm raster; straw and the hearth count in part).</summary>
    static float BareShare(Inside ins, Rect2 inner, List<(Rect2 R, float Share)> covers)
    {
        int n = 0;
        float bare = 0;
        for (float u = inner.Position.X + 0.05f; u < inner.End.X; u += 0.1f)
            for (float v = inner.Position.Y + 0.05f; v < inner.End.Y; v += 0.1f)
            {
                var p = new Vector2(u, v);
                if (!ins.Cells.Any(c => c.HasPoint(p))) continue;
                n++;
                float cov = 0;
                foreach (var (rr, s) in covers) if (rr.HasPoint(p)) cov = Mathf.Max(cov, s);
                bare += 1 - cov;
            }
        return n > 0 ? bare / n : 0;
    }

    static uint Hash(Vector3 p) => (uint)(Mathf.FloorToInt(p.X * 2.3f + 0.5f) * 73856093) ^ (uint)(Mathf.FloorToInt(p.Z * 2.3f + 0.5f) * 19349663) ^ (uint)(Mathf.FloorToInt(p.Y + 0.5f) * 83492791);

    /// <summary>(ResourceLoader.Exists asked once a preset: a town asks it for each of its thousands of pieces)</summary>
    static bool Exists(string preset)
    {
        lock (exists)
        {
            if (!exists.TryGetValue(preset, out var e)) exists[preset] = e = ResourceLoader.Exists($"{Dir}/{preset}.glb");
            return e;
        }
    }
    static readonly Dictionary<string, bool> exists = new();

    /// <summary>Takes a kit piece as ours (true: drawn by Build, or dropped), or false to leave it to the kit.</summary>
    public bool Take(string id, int house, Transform3D at, float cell)
    {
        if (!pieces.TryGetValue(id, out var lists)) return false;
        if (lists.Length == 0 || lists[0].Length == 0) return true;
        var (tint, style, roof, roofTint) = houses.TryGetValue(house, out var hl) ? hl : ((int)(Hash(at.Origin) % 6), 0, 0, 0);
        uint hs = Hash(at.Origin);
        bool isRoof = byRoof.Contains(id);
        var list = lists[(isRoof ? roof : style) % lists.Length];
        // (a copy's pick by its place, mixed with its house's, so two houses' runs don't repeat alike)
        var preset = list[(int)((hs ^ (uint)(house * 2654435761u)) % (uint)list.Length)];
        if (id.StartsWith("village/Corner_Exterior") && piers.TryGetValue(Key(at.Origin), out var pier))
        {
            preset = pier.Top ? "pier_hi" : "pier_lo";
            at = new Transform3D(pier.Wall, at.Origin);
        }
        if (!Exists(preset)) return false;
        float gy = ground.TryGetValue(house, out var g0) ? at.Origin.Y - g0 : 0f;
        // (E9c3: b's whole part 1 for a stone piece, its cut capped as rubble; else by its sill beam)
        bool stone = !isRoof && (preset.StartsWith("stone") || preset.StartsWith("quoin") || preset.StartsWith("pier"));
        var data = new Color((tint + 0.5f) / 8f, gy, (hs % 997) / 997f + (stone ? 1f : 0f), isRoof ? (style * 8 + roofTint + 0.5f) / 32f : (style + 0.5f) / 4f);
        var k = (preset, Mathf.FloorToInt(at.Origin.X / cell), Mathf.FloorToInt(at.Origin.Z / cell));
        if (!groups.TryGetValue(k, out var l)) groups[k] = l = new();
        l.Add((at, data, house, isRoof));
        if (!isRoof && ground.TryGetValue(house, out var gf)) feet.Add((at.Origin, gf));
        return true;
    }

    /// <summary>(E9c) The houses' fade units (HouseFade, added under root): each house, or each 12 m length of a long one
    /// (a town wall, so only the length in her way fades), as the volumes it fills: a box in its house's own frame round
    /// its walls (their footprint and height, not the eaves' overhang nor the gables, so a house beside or behind her
    /// is never taken), and each roof body as the prism under its two slopes in its own frame (a roof's box would stand
    /// over the street by its eaves), each spire and chimney as its box. Returns each copy's unit by its house and place.</summary>
    Dictionary<(int, Vector3), int> FadeUnits(Node3D root)
    {
        var unitOf = new Dictionary<(int, Vector3), int>();
        var byHouse = groups.SelectMany(g => g.Value.Select(e => (Preset: g.Key.Preset, e.At, e.House, e.Roof))).Where(e => e.House >= 0).GroupBy(e => e.House);
        var fade = new HouseFade();
        static bool Wall((string Preset, Transform3D At, int House, bool Roof) e) => !e.Roof && !e.Preset.StartsWith("gable");
        foreach (var h in byHouse)
        {
            // the house's frame: its walls' direction, folded to a quarter turn
            double sx = 0, sy = 0;
            foreach (var e in h.Where(Wall))
            {
                double a = 4 * Mathf.Atan2(e.At.Basis.Column0.Z, e.At.Basis.Column0.X);
                sx += System.Math.Cos(a); sy += System.Math.Sin(a);
            }
            float yaw = (float)System.Math.Atan2(sy, sx) / 4;
            // (world to the house's frame: x along its walls, y up, z across)
            var toHouse = new Transform3D(new Basis(Vector3.Up, yaw), Vector3.Zero);
            // its long axis, cut in lengths of at most 12 m (by each copy's own place)
            var walls = h.Where(Wall).Select(e => toHouse * e.At.Origin).DefaultIfEmpty(toHouse * h.First().At.Origin).ToList();
            float u0 = walls.Min(p => p.X), u1 = walls.Max(p => p.X), v0 = walls.Min(p => p.Z), v1 = walls.Max(p => p.Z);
            bool alongU = u1 - u0 >= v1 - v0;
            float lo = alongU ? u0 : v0, len = alongU ? u1 - u0 : v1 - v0;
            int n = Mathf.Max(1, Mathf.RoundToInt(len / 12f));
            var boxes = new Aabb?[n];
            var vols = Enumerable.Range(0, n).Select(_ => new List<HouseFade.Vol>()).ToArray();
            foreach (var e in h)
            {
                var o = toHouse * e.At.Origin;
                int k = Mathf.Clamp((int)(((alongU ? o.X : o.Z) - lo) / Mathf.Max(len, 1e-3f) * n), 0, n - 1);
                unitOf[(h.Key, e.At.Origin)] = fade.Units.Count + k;
                foreach (var (mesh, local) in PartsOf(e.Preset))
                {
                    var bb = mesh.GetAabb();
                    if (Wall(e))
                    {
                        for (int j = 0; j < 8; j++)
                        {
                            var p = toHouse * (e.At * local * bb.GetEndpoint(j));
                            boxes[k] = boxes[k] is Aabb b ? b.Expand(p) : new Aabb(p, Vector3.Zero);
                        }
                    }
                    else if (e.Roof)
                        vols[k].Add(new HouseFade.Vol((e.At * local).AffineInverse(), bb, e.Preset.StartsWith("roof_") ? RidgeOf(mesh) : 0));
                }
            }
            // (E9c2) the cut: 0.9 m over its floor (its ground, for a house with no inside of ours)
            float cutY = (zone != null ? InsidesOf(zone).FirstOrDefault(i => i.House == h.Key)?.Floor : null) ?? (ground.TryGetValue(h.Key, out var gk) ? gk : 0f);
            for (int k = 0; k < n; k++)
            {
                if (boxes[k] is Aabb b) vols[k].Add(new HouseFade.Vol(toHouse, b, 3));
                fade.Units.Add(vols[k].ToArray());
                fade.Cut.Add(cutY + 0.9f);
            }
        }
        // what hangs on the walls (the kit's copies, already under root): taken by the unit whose walls' box, 0.7 m wider, holds
        // it, and (E9c2) faded with it on its curve: the copies given custom data, r its unit + 1 (kit.gdshader's house fade)
        foreach (var mmi in root.GetChildren().OfType<MultiMeshInstance3D>())
        {
            // ((E9c3) and what furnishes the insides, "inside": given their unit and g 1 (the cauldron 2): kit.gdshader brings them in with it)
            bool inside = mmi.HasMeta("inside");
            if (!inside && mmi.GetMeta("prop", "").AsString() is not ("props/Lantern_Wall" or "props/Torch_Metal") || mmi.Multimesh is not MultiMesh mm) continue;
            float mode = !inside ? 0 : mmi.GetMeta("prop", "").AsString() == "props/Cauldron" ? 2 : 1;
            var ats = Enumerable.Range(0, mm.InstanceCount).Select(mm.GetInstanceTransform).ToArray();
            var us = new int[ats.Length];
            for (int i = 0; i < ats.Length; i++)
            {
                us[i] = -1;
                for (int u = 0; u < fade.Units.Count; u++)
                    if (fade.Units[u].FirstOrDefault(v => v.Ridge == 3) is { Ridge: 3 } w && w.Box.Grow(inside ? 0.05f : 0.7f).HasPoint(w.To * ats[i].Origin + (inside ? new Vector3(0, 0.3f, 0) : Vector3.Zero)))
                    {
                        if (!inside) fade.Hung.Add((mm, i, ats[i], u));
                        us[i] = u;
                        break;
                    }
            }
            if (us.All(u => u < 0)) continue;
            mm.InstanceCount = 0;
            mm.UseCustomData = true;
            mm.InstanceCount = ats.Length;
            for (int i = 0; i < ats.Length; i++) { mm.SetInstanceTransform(i, ats[i]); mm.SetInstanceCustomData(i, new Color(us[i] + 1, us[i] >= 0 ? mode : 0, 0, 0)); }
        }
        fade.Name = "house_fade";
        root.AddChild(fade);
        GD.Print($"house fade: {fade.Units.Count} units");
        return unitOf;
    }

    /// <summary>A roof body's ridge: 1 along its mesh's x, 2 along z (the axis its top vertices spread along).</summary>
    static int RidgeOf(Mesh mesh)
    {
        var bb = mesh.GetAabb();
        float top = bb.End.Y - 0.12f * bb.Size.Y;
        float x0 = float.MaxValue, x1 = float.MinValue, z0 = float.MaxValue, z1 = float.MinValue;
        for (int si = 0; si < mesh.GetSurfaceCount(); si++)
            foreach (var v in (Vector3[])mesh.SurfaceGetArrays(si)[(int)Mesh.ArrayType.Vertex])
                if (v.Y >= top) { x0 = Mathf.Min(x0, v.X); x1 = Mathf.Max(x1, v.X); z0 = Mathf.Min(z0, v.Z); z1 = Mathf.Max(z1, v.Z); }
        return x1 - x0 >= z1 - z0 ? 1 : 2;
    }

    static List<(Mesh Mesh, Transform3D Local)> PartsOf(string preset)
    {
        if (parts.TryGetValue(preset, out var list)) return list;
        list = new();
        var scene = GD.Load<PackedScene>($"{Dir}/{preset}.glb").Instantiate<Node3D>();
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D c3 ? at * c3.Transform : at;
                if (c is MeshInstance3D mi && mi.Mesh != null)
                {
                    var m = (Mesh)mi.Mesh.Duplicate();
                    for (int i = 0; i < m.GetSurfaceCount(); i++)
                        if (m.SurfaceGetMaterial(i) is Material mat) m.SurfaceSetMaterial(i, KitLook.For(mat, KitLook.Look.Plain));
                    list.Add((m, t));
                }
                Walk(c, t);
            }
        }
        Walk(scene, Transform3D.Identity);
        scene.Free();
        parts[preset] = list;
        return list;
    }

    /// <summary>The taken pieces as MultiMeshes under root (one per preset per square), in steps (Slices).</summary>
    public IEnumerable<object?> Build(Node3D root)
    {
        int n = 0;
        // the chimneys' tops, for the soot on the roofs round them
        var tops = new List<Vector3>();
        foreach (var ((preset, _, _), list) in groups)
        {
            if (!preset.StartsWith("chim_")) continue;
            float top = PartsOf(preset).Select(p => p.Local * p.Mesh.GetAabb().End).Select(v => v.Y).DefaultIfEmpty(3f).Max();
            foreach (var (at, _, _, _) in list) tops.Add(at * new Vector3(0, top, 0));
        }
        KitLook.SetChimneys(tops);
        // the terrain's height under the town (0.5 m cells), so the walls' grime rises from the ground itself (E9b3)
        if (zone != null && groups.Count > 0)
        {
            var at = groups.Values.SelectMany(l => l).Select(t => t.At.Origin).ToList();
            float x0 = at.Min(p => p.X) - 10f, z0 = at.Min(p => p.Z) - 10f, x1 = at.Max(p => p.X) + 10f, z1 = at.Max(p => p.Z) + 10f;
            const float c = 0.5f;
            int w = Mathf.Min(1024, Mathf.CeilToInt((x1 - x0) / c) + 1), h = Mathf.Min(1024, Mathf.CeilToInt((z1 - z0) / c) + 1);
            // (worked out on a worker thread: the terrain's heights are data; the image made of them here)
            var px = new float[w * h];
            var feetNow = feet.ToArray();
            var zd = zone!;
            yield return System.Threading.Tasks.Task.Run(() =>
            {
                for (int j = 0; j < h; j++)
                    for (int i = 0; i < w; i++)
                        px[j * w + i] = zd.HeightAt(x0 + (i + 0.5f) * (x1 - x0) / w, z0 + (j + 0.5f) * (z1 - z0) / h);
                // (the terrain is pressed down under the houses: within 1.2 m of a wall piece the ground is at least its house's foot,
                // where the street meets the wall)
                float sx = w / (x1 - x0), sz = h / (z1 - z0);
                foreach (var (p, foot) in feetNow)
                    for (int j = Mathf.Max(0, (int)((p.Z - 1.2f - z0) * sz)); j <= Mathf.Min(h - 1, (int)((p.Z + 1.2f - z0) * sz)); j++)
                        for (int i = Mathf.Max(0, (int)((p.X - 1.2f - x0) * sx)); i <= Mathf.Min(w - 1, (int)((p.X + 1.2f - x0) * sx)); i++)
                            if (px[j * w + i] < foot + 0.04f) px[j * w + i] = foot + 0.04f;
            });
            var bytes = new byte[px.Length * 4];
            System.Buffer.BlockCopy(px, 0, bytes, 0, bytes.Length);
            var img = Image.CreateFromData(w, h, false, Image.Format.Rf, bytes);
            KitLook.SetGround(ImageTexture.CreateFromImage(img), new Vector4(x0, z0, x1 - x0, z1 - z0));
        }
        yield return "walls: the ground under the town";
        // (each preset's file loaded on its own step)
        foreach (var (preset, _, _) in groups.Keys) { PartsOf(preset); yield return "walls: a file loaded"; }
        var unitOf = FadeUnits(root);
        yield return "walls: the fade units";
        foreach (var ((preset, _, _), list) in groups)
            foreach (var (mesh, local) in PartsOf(preset))
            {
                yield return "walls: a group";
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseCustomData = true, Mesh = mesh, InstanceCount = list.Count };
                for (int i = 0; i < list.Count; i++)
                {
                    mm.SetInstanceTransform(i, list[i].At * local);
                    // (r's whole part: the copy's fade unit + 1, HouseFade; its fraction the tint)
                    var d = list[i].Data;
                    mm.SetInstanceCustomData(i, new Color(d.R + (unitOf.TryGetValue((list[i].House, list[i].At.Origin), out var u) ? u + 1 : 0), d.G, d.B, d.A));
                }
                var mmi = new MultiMeshInstance3D { Multimesh = mm, Name = "own_" + preset };
                mmi.SetMeta("prop", "house/" + preset);
                mmi.SetMeta("at", new Godot.Collections.Array<Vector3>(list.Select(t => t.At.Origin)));
                root.AddChild(mmi);
                n += list.Count;
            }
        GD.Print($"own walls: {n} pieces in {groups.Count} groups, {tops.Count} chimneys");
    }
}
