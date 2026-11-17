using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (den r17 D, R16 item 4) The open floor dressed as a lived-in den floor, as den_room.png and den_boss.png cross theirs:
/// flat root runners (the set's painted B6 roots, small) across the open ground; debris clusters (a bone or two, a fur
/// tuft, leaves, in the lair a little blood) in groups with bare earth between, at about 2.5-3.5 m (150-250 px at the play
/// camera); in the lair an arc of rib and tusk bones at the arena's far edge with one or two red carcass pieces. Never in
/// her spawn, the lair's middle fight space, the pits, the hollows or on the boulders (the decals' Ok() rule).
/// The cluster centres thin the old even open sprinkle (DenDecals) between groups; what is laid here is handed to the
/// set's open pieces (SetOpen, SetFur) as taken ground, through c.Boulders, after the floor decals.
/// </summary>
public static partial class DungeonDress
{
    static readonly float OpenRun = SurvivorUnchained.Args.Num("den-open-run", 0f);          // (den r17 D, R16 item 4) root runners: x their density (0 off; den r17 D2, lead item 3: B6 is painted root crowns, many-fingered and raised, that read as crowns stamped one way, not half-buried runners: cut; 1 = d7e)
    static readonly float OpenRunGap = SurvivorUnchained.Args.Num("den-open-run-gap", 9f);  // one runner within this many m
    static readonly float OpenRunK = SurvivorUnchained.Args.Num("den-open-run-k", 0.3f);     // B6 card scale (piece ~10 m wide: 0.3 = 3 m, ~220 px)
    static readonly float OpenClump = SurvivorUnchained.Args.Num("den-open-clump", 1f);      // (den r17 D, R16 item 4) debris clusters: keep chance x (0 off; den r17 D2: fewer, richer groups on a wider lattice, 1 = d7e)
    static readonly float OpenClumpGap = SurvivorUnchained.Args.Num("den-open-clump-gap", 2.8f);   // their lattice, m (2.7 = d7e)
    static readonly float OpenBetween = SurvivorUnchained.Args.Num("den-open-between", 0.35f);      // the old even open sprinkle away from a cluster x this (1 = as r16, .6 = d7e; den r17 D2: bare earth between groups)
    static readonly float OpenClear = SurvivorUnchained.Args.Num("den-open-clear", 1.8f);   // m clear of her spawn (150 px)
    static readonly float OpenLairClear = SurvivorUnchained.Args.Num("den-open-lair-clear", 3.2f);   // m clear of the lair's middle (its fight)
    static readonly float OpenArc = SurvivorUnchained.Args.Num("den-open-arc", 1f);          // (den r17 D, R16 item 4) the lair's rib arc (0 off)
    static readonly float OpenArcR = SurvivorUnchained.Args.Num("den-open-arc-r", 7.5f);     // its radius from the lair's middle, m (pulled in to a bank's foot)
    static readonly float OpenClumpBone = SurvivorUnchained.Args.Num("den-open-clump-bone", 0.5f);   // (den r17 D2, lead item 1) a cluster's chance of one bone, never a second (d7e: every cluster one, 30% a second: the bone confetti; -1 = d7e)
    static readonly float OpenClumpR = SurvivorUnchained.Args.Num("den-open-clump-r", 0.24f);   // (den r17 D2, lead item 2) a cluster's spread past its 0.1 m core, m (.32 = d7e): tighter, one place
    static readonly float OpenArcBone = SurvivorUnchained.Args.Num("den-open-arc-bone", 0.15f);   // (den r17 D2, lead item 1) the arc's chance of a loose bone inside a slot (.35 = d7e)
    static readonly float OpenLeafK = SurvivorUnchained.Args.Num("den-open-leaf-k", 1.5f);   // (den r17 D2, lead item 2) a room group's leaves x this size (1 = d7e: specks that never read as a drift)
    static readonly float OpenArcIn = SurvivorUnchained.Args.Num("den-open-arc-in", 0.7f);   // (den r17 D2, lead item 4) a blocked arc slot steps in this many m (0 = d7e: skipped)
    static readonly float StickYaw = SurvivorUnchained.Args.Num("den-stick-yaw", 30f);      // (den r17 D, R16 item 8) a root decal lies within this many degrees of the screen's level (0 = any way: the standing rods)

    static readonly List<Vector2> openClumps = new();
    static readonly List<(Vector2 p, float half)> openTaken = new();

    /// <summary>(den r17 D, R16 item 8) A flat stick laid along the camera's depth read as a rod standing off the floor:
    /// its yaw folded to within --den-stick-yaw degrees of the world's x (the screen's level).</summary>
    static float StickYawFold(float yaw)
    {
        if (StickYaw <= 0f) return yaw;
        float lim = Mathf.DegToRad(StickYaw);
        float a = Mathf.Wrap(yaw, -Mathf.Pi / 2f, Mathf.Pi / 2f);   // (a stick has no head: yaw and yaw + pi are one)
        if (Mathf.Abs(a) <= lim) return a;
        // (fold the steep ones into the band, kept spread by how steep they were)
        return Mathf.Sign(a) * lim * (Mathf.Abs(a) - lim) / (Mathf.Pi / 2f - lim);
    }

    static void DenOpen(Ctx c, DecalBuf b, System.Func<float, float, float, float, bool> ok, int boss)
    {
        openClumps.Clear(); openTaken.Clear();
        var z = c.Z;
        if (!LoadSet()) return;
        var spawn = z.Rooms.Count > 0 ? new Vector2(z.Rooms[0].X, z.Rooms[0].Z) : new Vector2(1e6f, 1e6f);
        var lairM = boss >= 0 ? new Vector2(z.Rooms[boss].X, z.Rooms[boss].Z) : new Vector2(1e6f, 1e6f);
        float lairRad = boss >= 0 ? z.Rooms[boss].R * 1.05f : 0f;
        bool InLair(Vector2 p) => boss >= 0 && p.DistanceTo(lairM) < lairRad;
        bool Clear(Vector2 p, float pad) => p.DistanceTo(spawn) >= OpenClear + pad && p.DistanceTo(lairM) >= OpenLairClear + pad;
        bool Free(Vector2 p, float pad)
        {
            foreach (var (bp, bh) in c.Boulders) if (bp.DistanceTo(p) < bh + pad) return false;
            foreach (var (tp, th) in openTaken) if (tp.DistanceTo(p) < th + pad) return false;
            return true;
        }
        setSheets!.TryGetValue("O6", out var o6);
        var furs = new List<SetPiece>(); var leafs = new List<SetPiece>();
        if (o6 != null) foreach (var pc in o6) (setLeaves.Contains(pc) ? leafs : furs).Add(pc);
        var dec = Decals();
        var bones = dec.FindAll(d => d.Kind == "bone");
        var leafDec = dec.FindAll(d => d.Kind == "leaves");
        var twigDec = dec.FindAll(d => d.Kind == "twigs");
        int nRun = 0, nClump = 0, nPiece = 0, nArc = 0, nCarc = 0;

        // ---- root runners: the set's painted roots (B6, the long low pieces 1 and 2), small and flat on the open ground ----
        if (OpenRun > 0f && setSheets.TryGetValue("B6", out var b6) && b6.Count >= 3)
        {
            const float g = 4f;
            int n = (int)(z.Size / g);
            var cand = new List<(float u, Vector2 p, int i, int j)>();
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    if (Hash(i, j, 4101) > 0.9f * OpenRun) continue;
                    var p = new Vector2(-z.Half + (i + 0.2f + 0.6f * Hash(i, j, 4102)) * g, -z.Half + (j + 0.2f + 0.6f * Hash(i, j, 4103)) * g);
                    cand.Add((Hash(i, j, 4104), p, i, j));
                }
            cand.Sort((a, q) => a.u.CompareTo(q.u));
            foreach (var (_, p, i, j) in cand)
            {
                float k = OpenRunK * (0.8f + 0.45f * Hash(i, j, 4105));
                var pc = b6[Hash(i, j, 4106) < 0.65f ? 1 : 2];
                float hw = 0.42f * pc.Metres.X * k;   // (the painted roots' reach either side)
                bool good = true;
                for (int s = -2; s <= 2 && good; s++)
                {
                    var q = p + new Vector2(s * hw * 0.5f, 0f);
                    if (!ok(q.X, q.Y, 2.6f, 2.0f) || !Clear(q, 0.6f) || !Free(q, 1.2f)) good = false;
                }
                if (!good || !DenCaps.Take("openrun", p, 1, OpenRunGap)) continue;
                PlaceSetObj(c, "B6", pc, p.X, p.Y, k, 0f, false, 0f);
                for (int s = -2; s <= 2; s++) openTaken.Add((p + new Vector2(s * hw * 0.5f, 0f), 0.7f));
                nRun++;
            }
        }

        // ---- the lair's rib arc at its far edge (up the frame, past the fight), red carcass pieces among it ----
        if (OpenArc > 0f && boss >= 0)
        {
            var rib = new List<Decal>();
            foreach (int ix in new[] { 6, 8 }) if (ix < dec.Count && dec[ix].Kind == "ribcage") rib.Add(dec[ix] with { Kind = "arcrib" });
            var tusk = new List<Decal>();
            foreach (int ix in new[] { 3, 2 }) if (ix < dec.Count && dec[ix].Kind == "bone") tusk.Add(dec[ix] with { Kind = "arctusk" });
            var hide = new List<Decal>();
            foreach (int ix in new[] { 11, 12 }) if (ix < dec.Count && dec[ix].Kind == "hide") hide.Add(dec[ix] with { Kind = "carcass" });
            const int m = 15;
            float span = 2.2f, a0 = -Mathf.Pi / 2f + (Hash(boss, 1, 4201) - 0.5f) * 0.5f;
            int carcAt = 2 + (int)(Hash(boss, 2, 4202) * 3f), carc2 = m - 3 - (int)(Hash(boss, 3, 4203) * 3f);
            // (den r17 D2, lead item 4: s11's arc lay behind a root crown and a boulder) a slot blocked at its radius steps in
            // (--den-open-arc-in m a step, 3 steps), and the arc's middle turns (within +-0.6 rad of up the frame) to where most slots land
            Vector2? Slot(float a0x, int q)
            {
                float a = a0x + (q / (m - 1f) - 0.5f) * span + (Hash(boss, q, 4204) - 0.5f) * 0.08f;
                var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                // (pulled in to a bank's foot when one stands inside the arc's radius)
                float r = OpenArcR;
                for (float t = 4.5f; t < OpenArcR + 0.01f; t += 0.5f) if (Wall(c, lairM.X + dir.X * t, lairM.Y + dir.Y * t) < 1.6f) { r = t - 0.6f; break; }
                r += (Hash(boss, q, 4205) - 0.5f) * 0.5f;
                for (int st = 0; st <= (OpenArcIn > 0f ? 3 : 0); st++, r -= OpenArcIn)
                {
                    var pp = lairM + dir * r;
                    if (r >= 4.2f && ok(pp.X, pp.Y, 0.5f, 1.2f) && Free(pp, 0.5f)) return pp;
                }
                return null;
            }
            if (OpenArcIn > 0f)
            {
                int best = -1; float bestA = a0;
                for (float d = -0.6f; d <= 0.61f; d += 0.2f)
                {
                    int got = 0;
                    for (int q = 0; q < m; q++) if (Slot(-Mathf.Pi / 2f + d, q) != null) got++;
                    if (got > best + 1 || (got >= best && Mathf.Abs(d) < Mathf.Abs(bestA + Mathf.Pi / 2f))) { best = got; bestA = -Mathf.Pi / 2f + d; }
                }
                a0 = bestA;
            }
            for (int q = 0; q < m && rib.Count > 0 && tusk.Count > 0; q++)
            {
                float a = a0 + (q / (m - 1f) - 0.5f) * span + (Hash(boss, q, 4204) - 0.5f) * 0.08f;
                var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                if (Slot(a0, q) is not Vector2 p) continue;
                bool isCarc = (q == carcAt || q == carc2) && hide.Count > 0;
                float yaw = a + (Hash(boss, q, 4206) - 0.5f) * 0.5f;   // (radial: the ribs and tusks point at the fight)
                if (isCarc)
                {
                    if (SetPickBlood(Hash(boss, q, 4207)) is SetPiece bp) PlaceSetObj(c, "O5", bp, p.X, p.Y + 0.15f, 0.55f, 0f, false, 0f);
                    AddDecal(c, b, hide[nCarc % hide.Count], p.X, p.Y, a + Mathf.Pi / 2f, 1.15f + 0.2f * Hash(boss, q, 4208));
                    nCarc++;
                }
                else
                {
                    // (r17 d7b: the decal rib rows read as grey rakes at the camera: the arc is long bones laid radial, tusk-like;
                    // its middle one painted rib cage (O3) when the large-piece cap allows: --den-open-arc-ribs 1 = the decal rows as d7b)
                    bool ribRow = SurvivorUnchained.Args.Num("den-open-arc-ribs", 0f) > 0f && q % 3 != 1;
                    if (q == m / 2 && !ribRow && setSheets.TryGetValue("O3", out var o3) && o3.Count > 0 && PlaceSetObj(c, "O3", o3[0], p.X, p.Y, 0.75f, 0.1f, false) > 0f) { openTaken.Add((p, 1.2f)); nArc++; continue; }
                    var d = ribRow ? rib[(q / 3) % rib.Count] : tusk[q % tusk.Count];
                    AddDecal(c, b, d, p.X, p.Y, yaw, (d.Kind == "arcrib" ? 1.9f : 1.9f) + 0.2f * Hash(boss, q, 4209));
                    if (Hash(boss, q, 4210) < OpenArcBone && bones.Count > 0)   // (now and then a loose bone just inside it)
                    {
                        var lp = p - dir * (0.5f + 0.3f * Hash(boss, q, 4211));
                        if (ok(lp.X, lp.Y, 0.5f, 1.2f)) AddDecal(c, b, bones[(int)(Hash(boss, q, 4212) * bones.Count) % bones.Count], lp.X, lp.Y, Hash(boss, q, 4213) * Mathf.Tau, 0.9f, true);
                    }
                }
                openTaken.Add((p, 0.6f));
                nArc++;
            }
        }

        // ---- debris clusters: 3-6 pieces round a centre, bare earth between ----
        if (OpenClump > 0f)
        {
            float g = OpenClumpGap;
            int n = (int)(z.Size / g);
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    if (Hash(i, j, 4301) > 0.8f * OpenClump) continue;
                    var p = new Vector2(-z.Half + (i + 0.15f + 0.7f * Hash(i, j, 4302)) * g, -z.Half + (j + 0.15f + 0.7f * Hash(i, j, 4303)) * g);
                    if (!ok(p.X, p.Y, 1.6f, 1.6f) || !Clear(p, 0.4f) || !Free(p, 1.0f)) continue;
                    bool near = false;
                    foreach (var q in openClumps) if (q.DistanceSquaredTo(p) < 0.5f * g * g) { near = true; break; }
                    if (near) continue;
                    bool lair = InLair(p);
                    openClumps.Add(p); openTaken.Add((p, 0.8f)); nClump++;
                    int pieces = 3 + (int)(Hash(i, j, 4304) * 3.99f);
                    float a0 = Hash(i, j, 4305) * Mathf.Tau;
                    // (a little old blood under a lair's group, laid first)
                    if (lair && Hash(i, j, 4306) < 0.4f && SetPickBlood(Hash(i, j, 4307)) is SetPiece bp)
                    { PlaceSetObj(c, "O5", bp, p.X, p.Y, 0.4f + 0.15f * Hash(i, j, 4308), 0f, false, 0f); nPiece++; }
                    for (int k = 0; k < pieces; k++)
                    {
                        float a = a0 + k * 2.39996f, rr = 0.1f + OpenClumpR * Mathf.Sqrt(Hash(i * 7 + k, j, 4309));
                        float x = p.X + Mathf.Cos(a) * rr, zz = p.Y + Mathf.Sin(a) * rr;
                        if (!ok(x, zz, 0.8f, 1.0f)) continue;
                        // (the first a bone, then a fur tuft, then leaves; a second bone now and then)
                        int role = k == 0 ? 0 : k == 1 ? 1 : Hash(i * 7 + k, j, 4310) < 0.3f ? 0 : 2;
                        // (den r17 D2, lead item 1) one bone in about half the groups, none a second: the rest leaves and fur
                        if (OpenClumpBone >= 0f) role = k == 0 ? (Hash(i, j, 4314) < OpenClumpBone ? 0 : 3) : k == 1 ? 1 : k == 3 ? 3 : 2;
                        if (role == 3 && twigDec.Count > 0)   // (den r17 D2, lead item 2) a twig in the group where d7e laid a second bone: richer, not brighter
                        { AddDecal(c, b, twigDec[(int)(Hash(i * 7 + k, j, 4311) * twigDec.Count) % twigDec.Count], x, zz, StickYawFold(Hash(i * 7 + k, j, 4312) * Mathf.Tau), 0.9f + 0.2f * Hash(i * 7 + k, j, 4313)); nPiece++; continue; }
                        if (role == 3) role = 2;
                        float u = Hash(i * 7 + k, j, 4311);
                        if (role == 0 && bones.Count > 0)
                            AddDecal(c, b, bones[(int)(u * bones.Count) % bones.Count], x, zz, Hash(i * 7 + k, j, 4312) * Mathf.Tau, 0.85f + 0.3f * Hash(i * 7 + k, j, 4313), true);
                        else if (role == 1 && furs.Count > 0)
                            PlaceSetObj(c, "O6", furs[(int)(u * furs.Count) % furs.Count], x, zz, 0.62f + 0.2f * Hash(i * 7 + k, j, 4313), 0.1f, false, 0f);
                        else if (lair && leafs.Count > 0)
                            PlaceSetObj(c, "O6", leafs[(int)(u * leafs.Count) % leafs.Count], x, zz, 0.5f + 0.15f * Hash(i * 7 + k, j, 4313), 0.1f, false, 0f);
                        else if (!lair && leafDec.Count > 0)
                            AddDecal(c, b, leafDec[(int)(u * leafDec.Count) % leafDec.Count], x, zz, Hash(i * 7 + k, j, 4312) * Mathf.Tau, (0.9f + 0.2f * Hash(i * 7 + k, j, 4313)) * OpenLeafK);
                        else continue;
                        nPiece++;
                    }
                }
        }
        c.Count["open runners"] = nRun; c.Count["open clumps"] = nClump; c.Count["open clump pieces"] = nPiece; c.Count["open arc"] = nArc; c.Count["open carcass"] = nCarc;
        GD.Print($"DenOpen: {nRun} runners, {nClump} clusters ({nPiece} pieces), lair arc {nArc} ({nCarc} carcass)");
    }

    /// <summary>(den r17 D) What DenOpen laid, handed to the set's open pieces as taken ground (after the floor decals).</summary>
    static void DenOpenTaken(Ctx c) { foreach (var t in openTaken) c.Boulders.Add(t); }

    /// <summary>(den r17 D) The old even open sprinkle's keep, thinned away from the clusters (bare earth between groups).</summary>
    static float OpenKeep(float x, float zz)
    {
        if (OpenClump <= 0f || openClumps.Count == 0) return 1f;
        var p = new Vector2(x, zz);
        foreach (var q in openClumps) if (q.DistanceSquaredTo(p) < 1.6f * 1.6f) return 1f;
        return OpenBetween;
    }
}
