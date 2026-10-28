using System;
using System.Collections.Generic;
using System.Numerics;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>What sort of weapon a piece is: the socket it rides in when sheathed follows from the kind, never from the item,
/// so a new asset needs only its kind (Arms.Spec) and no socket code.</summary>
public enum WeaponKind { None, Blade1H, Blade2H, Blunt, Axe, Axe2H, Dagger, Wand, Staff, Shield, Crossbow }

/// <summary>The kind tables and the clearance file, without the engine (Actors/Arms.cs holds the geometry).</summary>
public static class WeaponSockets
{
    /// <summary>The named sockets (rows of Arms.Sockets, and the keys of the clearance file).</summary>
    public const string Back = "back", HipBlade = "hip_blade", HipLoop = "hip_loop", HipBelt = "hip_belt",
        BeltBack = "belt_back", Sling = "sling", BackDiag = "back_diag",
        BackStaff = "back_staff"; // unused: the slung staff failed under the arcanist's hat (animation 45); for a hatless outfit, unjudged
    public static readonly string[] All = { Back, HipBlade, HipLoop, HipBelt, BeltBack, Sling, BackDiag, BackStaff };

    /// <summary>The socket a kind rides in sheathed; null if it stays in her hand (the staff: carried upright on the combat mount, animation 45).</summary>
    public static string? SocketOf(WeaponKind kind) => kind switch
    {
        WeaponKind.Shield => Back,
        WeaponKind.Blade1H => HipBlade,
        WeaponKind.Blunt or WeaponKind.Axe => HipLoop,
        WeaponKind.Wand => HipBelt,
        WeaponKind.Dagger => BeltBack,
        WeaponKind.Crossbow => Sling,
        WeaponKind.Blade2H or WeaponKind.Axe2H => BackDiag,
        _ => null,
    };

    /// <summary>Whether a socket sits at her waist (hip blade, hip loop, hip belt, belt back) rather than on her back or slung.
    /// Creation's Look step keeps waist pieces sheathed and shown (her town stand's hands rest on them) and hides back ones,
    /// which would cover her hair when the Look turns her to show a braid. Null (no socket) is not at the waist.</summary>
    public static bool AtWaist(string? socket) => socket is HipBlade or HipLoop or HipBelt or BeltBack;

    /// <summary>A kind from a tag: the glTF node extra "kind", or a name suffix ("longsword.blade1h", "kind=axe2h", "_staff");
    /// anything unknown is None.</summary>
    public static WeaponKind Parse(string? tag)
    {
        if (string.IsNullOrWhiteSpace(tag)) return WeaponKind.None;
        var t = tag.Trim().ToLowerInvariant();
        foreach (var sep in new[] { '=', '.', '_', ':', '-' })
        {
            int i = t.LastIndexOf(sep);
            if (i >= 0 && Enum.TryParse<WeaponKind>(t[(i + 1)..], true, out var k) && Enum.IsDefined(k) && k != WeaponKind.None) return k;
        }
        return Enum.TryParse<WeaponKind>(t, true, out var whole) && Enum.IsDefined(whole) ? whole : WeaponKind.None;
    }

    /// <summary>Length of a scabbard: from `guard` past the sheath point to the blade's tip, along the shaft. Tip and sheath
    /// point are on the piece's long axis (tip at Length * (1 - Grip) and the sheath point at the grip, 0, when no anchors say
    /// otherwise), so a longer blade gives a longer scabbard. Never under 5 cm.</summary>
    public static float BladeLength(float tipY, float sheathY, float guard) => Math.Max(0.05f, tipY - sheathY - guard);

    /// <summary>Whether an anchor (anchor_grip, anchor_sheath) found at `path` (the node names from the file's root down to
    /// the anchor's parent) is this piece's: in a file of several pieces (Arms.Spec Node: both daggers share daggers.glb)
    /// only an anchor under the piece's own node counts, so one dagger's anchor never mounts the other. A whole-file piece
    /// (no Node) takes any anchor in the file.</summary>
    public static bool AnchorIsPiece(string? specNode, IEnumerable<string> path)
    {
        if (specNode == null) return true;
        foreach (var n in path) if (n == specNode) return true;
        return false;
    }

    /// <summary>The piece's shaft (long) and side (mid) axes in model space. An anchor (anchor_grip, else anchor_sheath) says
    /// the shaft outright: its -Y runs down the blade or haft toward the tip, so `anchorDown` (that -Y) is the shaft, exactly,
    /// whatever else the mesh carries (a coil or a crossguard tilts the bounds' principal axis: 4 degrees on the bound staff).
    /// Without one, the bounds' principal axes stand. The side axis is the bounds' second axis made square to the shaft (the
    /// anchor's +Z then turns the piece about the shaft).</summary>
    public static (Vector3 Long, Vector3 Mid) ShaftAxes(Vector3 pcaLong, Vector3 pcaMid, Vector3? anchorDown)
    {
        if (anchorDown is not { } down || down.LengthSquared() < 1e-12f) return (pcaLong, pcaMid);
        var lng = Vector3.Normalize(down);
        foreach (var c in new[] { pcaMid, pcaLong, Vector3.UnitX, Vector3.UnitZ })
        {
            var m = c - lng * Vector3.Dot(c, lng);
            if (m.LengthSquared() > 1e-4f) return (lng, Vector3.Normalize(m));
        }
        return (lng, Vector3.UnitX);
    }

    /// <summary>The line her right `grip` fist closes round, in hand_r's space: the hollow of the fist the keyed clips close
    /// on a staff (tools/anim/keyed.py WRAP), its centre midway across the four fingers, and its direction, butt toward
    /// head (8.2 degrees off hand +Z: 6.6 toward the fingers, 5 toward the palm on the thumb's side, as her palm slopes).
    /// Fitted 13 October on her skin and the arcanist's glove: the palm and every finger's inner pads lie on the leather
    /// (13.65 mm round the line), the thumb over the forefinger. (The old pocket, -39, 58, 2 mm, lay at the thumb's root,
    /// 40 mm off the palm and 30-50 mm off the pads: the shaft ran beside the fist, not through it.) An anchored piece's
    /// grip point and shaft are laid on it.</summary>
    /// 18 October (animation 38): refitted on a diagonal (fistfit; keyed.py WRAP["staff"]): the shaft from the forefinger's root
    /// to the heel under the little finger, 27.7 deg off hand +Z (was 8.2), so the little finger reaches it; keyed.py GRIP["staff"] 18.
    public static readonly Vector3 FistAtR = new(-0.0326f, 0.0841f, -0.0104f);
    public static readonly Vector3 FistDirR = Vector3.Normalize(new Vector3(-0.2116f, 0.4141f, 0.8853f));

    /// <summary>The line her right fist closes round on a one-handed blade (tools/anim/keyed.py WRAP["sword"]), in hand_r's
    /// space: where the blade's grip point (Arms.Spec.Grip along its long axis) lands, and the shaft's direction, pommel
    /// toward blade. The shaft keeps the diagonal grip her sword clips are keyed to (keyed.py GRIP["sword"], Arms.Spec.Lean
    /// 35: hand +Z turned 35 degrees toward the fingers, so the blade points where the clips aim it); the line is moved onto
    /// the fist's hollow, up under the knuckles: from the forefinger's root (its first bone lies on the grip) across to the
    /// heel of the palm, 36.7 mm off the bones toward the palm (the palm rests on the grip). Fitted 14 October on her skin
    /// and the chevalier sword's hilt (a barrel 13.3-18.5 mm round, 125 mm between collar and ferrule): every finger's two
    /// outer pads lie on it (0.3-1.0 mm out), the thumb over the middle finger; the hand spans 76 mm of the 125, its
    /// forefinger 15 mm short of the ferrule and its little finger 13 mm clear of the pommel's collar. (The old seat, the
    /// grip point at the mount, -25, 75, 0 mm, ran the hilt through the lower palm, the fingers 20-34 mm off it.)</summary>
    public static readonly Vector3 BladeAtR = new(-0.0431f, 0.0888f, -0.0131f);
    public static readonly Vector3 BladeDirR = new(0f, 0.57357644f, 0.81915204f);

    /// <summary>The line her right fist closes round on an axe's haft (tools/anim/keyed.py WRAP["axe"]), in hand_r's space:
    /// where the haft's grip point (Arms.Spec.Grip along its long axis) lands, and the direction the piece's +Y is turned
    /// onto, butt toward head: the viking axe's haft (9 degrees off its long axis, which the head pulls) turned onto the
    /// lean its clips are keyed to (keyed.py GRIP["axe"], 30), its butt under the heel of her palm. SUPERSEDED (anim-40,
    /// 19 October: the haft conformed, PocketR Axe is BladeAtR); kept for the record. NOT LIVE (not in
    /// PocketR): its haft is 40 mm thick toward the palm and 58 across (155 mm round, where her fist closes on about 90),
    /// so no fist closes on it: the best fit (tools/anim/fistfit.py axe --fit, 14 October) brings the fingers' ends only
    /// 123-177 degrees round it, the middle finger's end 12 mm off. The haft wants thinning to about 30 mm across over
    /// the hand's span (as tools/assets/grip_thin.py did the chevalier sword's grip), then the fit, then PocketR.</summary>
    public static readonly Vector3 AxeAtR = new(-0.0382f, 0.1119f, 0.0381f);
    public static readonly Vector3 AxeDirR = Vector3.Normalize(new Vector3(-0.00086f, 0.62927f, 0.77719f));

    /// <summary>The line her right fist closes round on a dagger's hilt (tools/anim/keyed.py WRAP["daggers"]), in hand_r's
    /// space: where the hilt's grip point (Arms.Spec.Grip along its long axis) lands, and its direction, pommel toward
    /// blade: the mount's own (Arms.Spec.Lean 30, keyed.py GRIP["daggers"]), so the seat only moves the hilt. Fitted 14
    /// October on her skin, the ranger's glove and the dagger's hilt (a flat hexagon 15 mm thick toward the palm, 29
    /// across, measured on its own section, tools/anim/fistfit.py): the palm and every finger's outer pad on it (0.3-1.1
    /// mm out, the forefinger's and middle finger's middle bones 3 mm off the flat), nothing into it, the thumb over the
    /// forefinger; her forefinger 4 mm short of the guard, the heel of her palm on the pommel. (The plain mount, -25, 75,
    /// 0 mm, ran the hilt 10 mm into her palm and little finger, the forefinger 15 mm off it.) Live only for a dagger whose
    /// Spec is Seated.</summary>
    public static readonly Vector3 DaggerAtR = new(-0.0324f, 0.0720f, -0.0139f);
    public static readonly Vector3 DaggerDirR = new(0f, 0.5f, 0.8660254f);

    /// <summary>A pistol-held piece's grip (the crossbow's, tools/assets/crossbow_grip.py): its line, foot toward the stock,
    /// leans this many degrees off square to the stock toward the bow (its foot back toward the butt), as a pistol-grip
    /// crossbow's. In the piece (Arms.Make: +Y along the stock toward the bow, +Z its top, the anchor_grip's origin the
    /// grip point) the grip runs (0, sin, cos) of it. grip_spec.json Crossbow "rake".</summary>
    public const float PistolRake = 22.5f;

    /// <summary>The line her right fist closes round on the crossbow's pistol grip (tools/anim/keyed.py WRAP["crossbow"]), in
    /// hand_r's space: where the grip point (its anchor_grip's origin) lands, and the grip's direction, foot toward the
    /// stock. The direction is the rake itself (hand +Z turned PistolRake toward the fingers), so the seat (PistolSeat) lays
    /// the stock along hand +Y (the fingers' and the forearm's line, the bow forward) and its top out of the thumb side,
    /// as the plain pistol mount held it: the clips' aim is unchanged, only the piece moves onto the fist.</summary>
    public static readonly Vector3 CrossbowAtR = new(-0.0410f, 0.0951f, -0.0092f);
    public static readonly Vector3 CrossbowDirR = new(0f, 0.38268343f, 0.92387953f);

    /// <summary>The fitted pocket of her right fist for a kind of piece, or none (that kind keeps the plain mount): the
    /// staff's (FistAtR / FistDirR), the one-handed blade's (BladeAtR / BladeDirR), the dagger's (DaggerAtR / DaggerDirR) and the
    /// crossbow's pistol grip (CrossbowAtR / CrossbowDirR: laid by PistolSeat, not FistSeat).
    /// A new kind needs its line here, its fist in keyed.py WRAP, and its pieces' Arms.Spec Seated (or an anchor_grip).</summary>
    public static (Vector3 At, Vector3 Dir)? PocketR(WeaponKind kind) => kind switch
    {
        WeaponKind.Staff => (FistAtR, FistDirR),
        WeaponKind.Blade1H => (BladeAtR, BladeDirR),
        // The wand: Made.Wand's grip is the one-handed blade's (13.7 mm round, anim-40), held in the same fist.
        WeaponKind.Wand => (BladeAtR, BladeDirR),
        // The one-handed axe: its haft conformed to the same fist (anim-40: the viking axe's wrap an oval 34.7 x 21.7 mm,
        // its anchor_grip on the haft's line), held as the blade is (keyed.py WRAP["axe"], GRIP["axe"] turns the hand so
        // the axe lies in the world as its clips were keyed).
        WeaponKind.Axe => (BladeAtR, BladeDirR),
        WeaponKind.Dagger => (DaggerAtR, DaggerDirR),
        WeaponKind.Crossbow => (CrossbowAtR, CrossbowDirR),
        _ => null,
    };

    /// <summary>hand_r's space to hand_l's: her body's mirror (the plane x = 0 of her skeleton at rest) carried through her
    /// rest hand frames, Rl^T diag(-1, 1, 1) Rr (tools/anim/fistfit.py MIRROR, from data/heroine_skeleton.json). Not a plain
    /// X flip: her rest hands sit 0.4 degrees off each other's mirror. Rows; a reflection (det -1), its own transpose's
    /// inverse, so a point in hand_l's space maps back by its transpose.</summary>
    public static readonly Vector3[] MirrorRL =
    {
        new(-0.999976f, 0.006672f, 0.001970f),
        new(0.006660f, 0.999958f, -0.006359f),
        new(0.002012f, 0.006345f, 0.999978f),
    };

    /// <summary>A hand_r point or direction in hand_l's space (MirrorRL).</summary>
    public static Vector3 ToLeft(Vector3 v) => new(Vector3.Dot(MirrorRL[0], v), Vector3.Dot(MirrorRL[1], v), Vector3.Dot(MirrorRL[2], v));

    /// <summary>The line her left fist closes round on the second dagger (dagger_b: its own hilt, thinner than the first's,
    /// about 11 mm toward the palm and 23 across), given in hand_r's frame as its mirror image (so it reads beside
    /// DaggerAtR / DaggerDirR; PocketL takes it to hand_l by ToLeft). Fitted on her left hand (tools/anim/fistfit.py
    /// daggers --side l --fit: keyed.py WRAP["daggers_l"]), the direction the mount's own (Lean 30).</summary>
    public static readonly Vector3 DaggerLeftAt = new(-0.0334f, 0.0840f, -0.0139f);
    public static readonly Vector3 DaggerLeftDir = new(0f, 0.5f, 0.8660254f);

    /// <summary>Her left fist's pocket (hand_l space), for a kind whose left fist is fitted (keyed.py wrap_of gives it
    /// "l"): its line in hand_r's frame taken through the mirror (ToLeft). Only the dagger (the pair Visuals and her
    /// stalker hold: daggers right, dagger_b left); every other kind keeps the plain mount in her left hand until its left
    /// fist is fitted too (fistfit.py --side l).</summary>
    public static (Vector3 At, Vector3 Dir)? PocketL(WeaponKind kind) => kind switch
    {
        WeaponKind.Dagger => (ToLeft(DaggerLeftAt), Vector3.Normalize(ToLeft(DaggerLeftDir))),
        _ => null,
    };

    /// <summary>The pocket a clip's LEFT grip tilt (meta "grip_tilt_l", animation 58) turns the piece in her left fist about
    /// (hand_l space): the fitted left pocket where there is one (PocketL), else the right's mirrored (ToLeft of PocketR):
    /// her left fist then closes on the piece in the right's tilted fist laid mirrored (keyed.py wrap_of), so a piece that
    /// otherwise keeps the plain mount (the reaver's second axe) is seated on this pocket while the clip tilts it
    /// (PersonView.Slide eases it over by the clip's tilt weight). None for a kind without a right pocket, or a pistol grip.</summary>
    public static (Vector3 At, Vector3 Dir)? TiltPocketL(WeaponKind kind) =>
        PocketL(kind) ?? (kind != WeaponKind.Crossbow && PocketR(kind) is { } p ? (ToLeft(p.At), Vector3.Normalize(ToLeft(p.Dir))) : null);

    /// <summary>The palm's normal a left tilt turns about (hand_l space): hand_r's +X through the mirror, reversed, since a
    /// mirror reverses a turn's sense (M R(a, t) M^T = R(-M a, t)): the same + tilt turns the left piece as the right's
    /// mirror image (its head away from her fingers). keyed.py TILT_AXIS_L is the same.</summary>
    public static Vector3 TiltAxisL => Vector3.Normalize(-ToLeft(Vector3.UnitX));

    /// <summary>The fitted pocket of a fist by its bone (hand_r: PocketR, hand_l: PocketL), else none.</summary>
    public static (Vector3 At, Vector3 Dir)? Pocket(WeaponKind kind, string bone) => bone switch
    {
        "hand_r" => PocketR(kind),
        "hand_l" => PocketL(kind),
        _ => null,
    };

    /// <summary>The staff's seat (FistSeat with the staff's pocket).</summary>
    public static (Quaternion Turn, Vector3 At) FistSeat(Vector3 mx, Vector3 my, Vector3 mz, Vector3 origin) =>
        FistSeat(mx, my, mz, origin, FistAtR, FistDirR);

    /// <summary>Where a piece sits inside its mount so that its grip point (an anchor's origin, else the Spec's grip; on
    /// the shaft's centreline) lands on the fist's pocket `pocketAt` and its shaft (the piece's +Y, an anchor's -Y) runs
    /// along the fist's line `pocketDir` (both in its hand's space): a turn (the least that takes +Y onto the line, so the
    /// piece's +Z keeps its roll) and an offset, both in the mount's space. `mx, my, mz, origin`: the mount in the hand's
    /// space, as it is held (with its Lean).</summary>
    public static (Quaternion Turn, Vector3 At) FistSeat(Vector3 mx, Vector3 my, Vector3 mz, Vector3 origin, Vector3 pocketAt, Vector3 pocketDir)
    {
        Vector3 In(Vector3 v) => new(Vector3.Dot(v, mx), Vector3.Dot(v, my), Vector3.Dot(v, mz));
        var at = In(pocketAt - origin);
        var dir = Vector3.Normalize(In(pocketDir));
        var axis = Vector3.Cross(Vector3.UnitY, dir);
        float s = axis.Length(), c = Vector3.Dot(Vector3.UnitY, dir);
        var turn = s < 1e-7f ? Quaternion.Identity : Quaternion.CreateFromAxisAngle(axis / s, MathF.Atan2(s, c));
        return (turn, at);
    }

    /// <summary>Where a pistol-held piece (the crossbow) sits inside its mount so that its grip point (its anchor_grip's
    /// origin) lands on the fist's pocket `pocketAt` and its grip's line, (0, sin PistolRake, cos PistolRake) in the piece,
    /// runs along the fist's line `pocketDir` (both in its hand's space), turned about that line so the stock (the piece's
    /// +Y) leans toward the hand's +Y (the fingers', the forearm's line: the bow forward) and its top (+Z) out of the thumb
    /// side. A turn and an offset in the mount's space (`mx, my, mz, origin`: the mount in the hand's space), the piece's own
    /// axes: no PieceTransform under it.</summary>
    public static (Quaternion Turn, Vector3 At) PistolSeat(Vector3 mx, Vector3 my, Vector3 mz, Vector3 origin, Vector3 pocketAt, Vector3 pocketDir)
    {
        Vector3 In(Vector3 v) => new(Vector3.Dot(v, mx), Vector3.Dot(v, my), Vector3.Dot(v, mz));
        var d = Vector3.Normalize(In(pocketDir));
        var fwd = In(Vector3.UnitY);
        var s = fwd - d * Vector3.Dot(fwd, d);
        s = s.LengthSquared() < 1e-10f ? Vector3.Normalize(Vector3.Cross(d, In(Vector3.UnitX))) : Vector3.Normalize(s);
        float r = PistolRake * MathF.PI / 180f, sr = MathF.Sin(r), cr = MathF.Cos(r);
        var y = sr * d + cr * s;          // the stock, toward the bow
        var z = cr * d - sr * s;          // its top
        var x = Vector3.Cross(y, z);
        var m = new Matrix4x4(x.X, x.Y, x.Z, 0, y.X, y.Y, y.Z, 0, z.X, z.Y, z.Z, 0, 0, 0, 0, 1);
        return (Quaternion.Normalize(Quaternion.CreateFromRotationMatrix(m)), In(pocketAt - origin));
    }

    /// <summary>Metres to push a socket out of her body along its normal for an outfit: art/anim/socket_clearance.json, written by
    /// `armscheck.py --sockets` as {outfit: {socket: metres}}. Unknown outfit or socket: 0.</summary>
    public sealed class Clearance
    {
        readonly Dictionary<string, Dictionary<string, float>> table = new();

        public static Clearance Parse(string? json)
        {
            var c = new Clearance();
            if (string.IsNullOrWhiteSpace(json)) return c;
            try
            {
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.ValueKind != JsonValueKind.Object) return c;
                foreach (var o in doc.RootElement.EnumerateObject())
                {
                    if (o.Value.ValueKind != JsonValueKind.Object) continue;
                    var row = new Dictionary<string, float>();
                    foreach (var s in o.Value.EnumerateObject())
                        if (s.Value.ValueKind == JsonValueKind.Number) row[s.Name] = (float)s.Value.GetDouble();
                    c.table[o.Name] = row;
                }
            }
            catch (JsonException) { }
            return c;
        }

        /// <summary>The outfit's name as the file has it: a calling ("stalker" is the ranger's), "" is none.</summary>
        public static string Outfit(string? calling) => string.IsNullOrEmpty(calling) ? "none" : calling == "stalker" ? "ranger" : calling;

        public float Metres(string? calling, string socket) =>
            table.TryGetValue(Outfit(calling), out var row) && row.TryGetValue(socket, out var m) ? m : 0f;
    }
}
