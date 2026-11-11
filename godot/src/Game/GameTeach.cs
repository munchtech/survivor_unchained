using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* The tutorial's callouts, as the game runs them (logic/Play/Teach.cs keeps the line; Callout.cs
 * draws them). A freeze stops the fight until the player answers; Esc skips it. The profile
 * remembers what was seen (Settings.SeenTips); the Tips setting turns them all off. */
public partial class Game
{
    sealed class ProfileMemory : ITeachMemory
    {
        public bool Tips => Settings.Current.Tips;
        public bool Seen(string id) => Settings.Current.SeenTips.Contains(id);
        public void Mark(string id) { if (!Seen(id)) { Settings.Current.SeenTips.Add(id); Settings.Current.Save(); } }
    }

    Teacher? teacher;
    ICalloutView? calloutShown;
    double teachClock;
    bool teachFroze;
    /// <summary>The draft's offers while one is being presented (the callout's card, before the panel is drawn).</summary>
    List<Offer>? teachOffers;

    Teacher Teacher => teacher ??= MakeTeacher();

    Teacher MakeTeacher()
    {
        // --teach-reset: every callout unseen again (test runs may overwrite the owner's profile).
        if (Args.Has("teach-reset")) { Settings.Current.SeenTips.Clear(); Settings.Current.Save(); }
        if (Shots.On("teach")) SurvivorUnchained.Play.Zones.Prologue.Trace = s => GD.Print(s);
        return new Teacher(new ProfileMemory()) { Log = TeachLog };
    }

    /// <summary>A zone's callout at its moment.</summary>
    public void Teach(Callout c) => Teacher.Offer(c, teachClock, TeachBusy());
    /// <summary>Whether a callout was seen on this profile.</summary>
    /// (Asks the Teacher first, so --teach-reset has cleared the profile before any zone reads it: a test
    /// run's Begin saw last run's "art" and let the Flare's great blessings through, round 2 judge.)
    public bool Taught(string id) { _ = Teacher; return Settings.Current.SeenTips.Contains(id); }
    /// <summary>(the autopilot) It keeps the Flare in the Barrow until F8 has asked for it.</summary>
    /// (M6 l4: and the lent Flare at the Warden until A11b is seen: m6r4's autopilot spent it on C02's hand-back, the meter
    /// empty before A11b's moment)
    public bool HoldFlare => zone is Zones.Prologue { Now: Zones.Prologue.Stage.Barrow } && !Taught("art")
        || zone is Zones.Prologue { Now: Zones.Prologue.Stage.Boss } && !Taught("flare") && Settings.Current.Tips;

    /// <summary>The callout on the screen now (the autopilot answers a freeze).</summary>
    public Callout? Teaching => teacher?.Current;
    public bool Saying => hud.SayUp;
    /// <summary>Whether a callout waits in the line (the autopilot holds its draught for F10's).</summary>
    public bool TeachWaiting(string id) => teacher?.Queued(id) == true;
    /// <summary>Real seconds it has been up.</summary>
    public double TeachingFor => teacher?.Current != null ? RealNow - teacher.ShownAt : 0;
    static double RealNow => Time.GetTicksMsec() / 1000.0;

    void TeachLog(string what, Callout c, string how)
    {
        if (!Args.Dev) return;
        string real = what is "queued" || (what == "dropped" && teacher?.Current != c) ? "-" : $"{(RealNow - (teacher?.ShownAt ?? RealNow)) * 1000:0}";
        if (what == "shown") real = "0";
        var at = Primary(c);
        string waited = what is "queued" or "shown" or "dropped" ? $" waited={(teacher?.LogWaited is { Length: > 0 } w ? w : "-")}" : "";
        GD.Print($"teach {c.Id} {what} t={Battle?.Time ?? 0:0.0} real={real} kind={c.Kind.ToString().ToLowerInvariant()} target={(at is Vector2 v ? $"{v.X:0},{v.Y:0}" : "-")}{(how != "" ? " how=" + how : "")}{waited}{(Battle is { } hb ? $" hp={hb.Player.Hp:0}/{hb.MaxHp:0}" : "")}");
    }

    /// <summary>What has the screen, for the line of callouts.</summary>
    Busy TeachBusy()
    {
        var b = Busy.None;
        if (cine != null) b |= Busy.Cinematic;
        if (inTransit || hud.FadeAmount > 0.02f) b |= Busy.Transit;
        if (hudMode == "fall" || Battle?.Player.Alive == false) b |= Busy.Fall;
        if (screens.Current != null || hudMode is "dialogue" or "chest" or "fall" || zone?.Choice != null) b |= Busy.Overlay;
        if (hudMode == "draft") b |= Busy.Draft;
        if (hud.BannerUp && !hud.HoldBanner) b |= Busy.Banner;
        if (hud.SayUp) b |= Busy.Say;
        if (hud.PromptUp) b |= Busy.Prompt;
        if (hud.TipUp) b |= Busy.Hint;
        if (Battle?.DraftOwed == true && hudMode != "draft") b |= Busy.Owed;
        return b;
    }

    /// <summary>A world point on the HUD's canvas, if it is on the screen.</summary>
    Vector2? OnScreen((double X, double Y, double Z) p)
    {
        var w = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
        if (camera.IsPositionBehind(w)) return null;
        var s = camera.UnprojectPosition(w);
        return s.X is > 40 and < 1880 && s.Y is > 40 and < 1040 ? s : null;
    }

    /// <summary>Where a callout points now: its points and areas on the HUD's canvas (none: not there).</summary>
    /// <summary>--no-open (a dev flag for pictures): a lesson that waits for the open (the red line) may show under a canopy.</summary>
    static readonly bool noOpen = Args.Has("no-open");   // (Args: read in dev builds only, SU-007)

    (List<Vector2> Points, List<Rect2> Areas, bool Gone, int WorldOn) Resolve(Callout c)
    {
        var pts = new List<Vector2>();
        var areas = new List<Rect2>();
        bool gone = false;
        int worldOn = 0;
        var t = c.Target;
        switch (t.Hud)
        {
            case null: break;
            // (the whole chain, bracketed: it is the bar that fills, not its lock)
            case "chain": areas.Add(HudBottom.Map(Instrument.ChainFill)); break;
            // (the filled links, left of the lock: F2's, where the ember fills; the lock itself is L1's)
            // (the run of the bar, bracketed at its two ends: her hair to the Flare's cup. Experience 10 tried a bare point
            // on the crest instead; the teach judge (r1, r2) failed it: "a player can't tell what 'this' is")
            // (UI 27: the bottom HUD's parts are its own 1080 px: brought onto the screen at its scale, HudBottom)
            case "chain_fill": areas.Add(HudBottom.Map(Instrument.ChainFill)); break;
            case "dash": pts.Add(HudBottom.Map(DgSmall.DashMid)); break;
            case "draught": pts.Add(HudBottom.Map(DgSmall.DraughtMid)); break;
            case "art": pts.Add(HudBottom.Map(Instrument.ArtAt)); break;
            case "banner": if (hud.BannerUp) areas.Add(hud.BannerArea); break;
            // (au1 item 14: the parts never taught, each by the HUD's own accessor, bracketed)
            case "prompt": if (hud.PromptArea is Rect2 pa) areas.Add(pa); break;
            case "minimap": if (hud.MinimapArea is Rect2 ma) areas.Add(ma); break;
            // (M6 A9: a place's mark on the corner map, "map:X,Z", by the disc's own transform; off the disc, the whole map)
            case var s when s.StartsWith("map:"):
                if (hud.MinimapArea is Rect2 mm && Battle?.Player is { } mp && s[4..].Split(',') is [var sx, var sz]
                    && double.TryParse(sx, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var wx)
                    && double.TryParse(sz, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var wz))
                {
                    if (Minimap.OnDisc(wx - mp.X, wz - mp.Z) is Vector2 md) pts.Add(mm.Position + md);
                    else areas.Add(mm);
                }
                break;
            // (M7a A5a: the level card offering a lamp)
            case "lamp_offer": if (hud.LevelCardArea is Rect2 la) areas.Add(la); break;
            case "tally": if (hud.TallyArea is Rect2 ta) areas.Add(ta); break;
            // (the numbers card: held up by UpdateTeach while this callout is the one showing; no area on the first frame)
            case "card": hud.TeachCard = true; if (hud.XpCardArea is Rect2 xa) areas.Add(xa); break;
            case "cards":
                if (hud.DraftShown is { } dp && dp.CardAreas().ToList() is { Count: > 0 } all)
                    areas.Add(all.Select(x => x.Rect).Aggregate((a, b) => a.Merge(b)));
                break;
            case "card:weapon":
                if (hud.DraftShown is { } dw && dw.CardAreas().FirstOrDefault(x => x.Offer.Kind == OfferKind.Weapon) is { Rect.Size.X: > 0 } wc)
                    areas.Add(wc.Rect);
                break;
            case var s when s.StartsWith("socket:"):
                // (a slot is square: bracketed, not ringed)
                if (hud.SocketRect(s[7..]) is Rect2 sr) areas.Add(sr);
                break;
            // (M6: a skill key's seat on the bar, "seat:Skill1", by M4's seats: bracketed as a socket is)
            case var s when s.StartsWith("seat:"):
                if (SeatSlot(s) is int sl && hud.SeatRect(sl) is Rect2 st) areas.Add(st);
                break;
            // (M6: Resolve, the hair of the Drowned Girl: her figure above the bar line, where the veins run)
            case "resolve": if (hud.FigureRect is Rect2 fr) areas.Add(HudBottom.Map(fr)); break;
        }
        if (t.World != null)
        {
            var world = t.World();
            if (world.Count == 0) gone = true;
            // (all of them well inside the screen, or none is pointed at yet)
            foreach (var w in world)
            {
                if (OnScreen(w) is not Vector2 v) continue;
                // (each one ringed only well inside the screen: the rest get an edge arrow)
                if (t.Each && !InSafe(v)) continue;
                // (a candidate: the first well inside the screen is the one)
                if (t.Safe)
                {
                    if (t.Open && OS.GetCmdlineUserArgs().Contains("--teach-diag") && (Battle?.Time ?? 0) - diagAt > 0.25)
                    {
                        diagAt = Battle?.Time ?? 0; InOpen(w);
                        GD.Print($"teachdiag {c.Id} t={diagAt:0.0} v={v.X:0},{v.Y:0} safe={InSafe(v)} block={diagBlock}");
                    }
                    if (!InSafe(v)) continue;
                    // (M6 l4: and its ring whole above the HUD: m6r4's captain stood at the safe area's foot, its ring
                    // drawn over the Drowned Girl)
                    if (t.Ring?.Invoke() is { Count: > 0 } rs && rs.Any(q => OnScreen(q) is not Vector2 rv || !InSafe(rv)
                        || rv.Y + Math.Clamp(PxPerMetre(q) * (float)t.RingRadius, 28, 110) > RingFloor)) continue;
                    // (the point itself ringed when nothing else is: its ring above the HUD too; m6r7's Leap point
                    // sat at the safe area's foot, its ring on the right-hand figure)
                    if (t.Ring == null && v.Y + Math.Clamp(PxPerMetre(w) * (float)t.Radius, 20, 56) > RingFloor) continue;
                    if (t.Open && !noOpen && !InOpen(w)) continue;
                    // (and what must be read with it: on the screen and in the open, or it waits)
                    if (t.Open && !noOpen && t.Seen?.Invoke() is { } seen && seen.Any(q => OnScreen(q) is not Vector2 sv || !Canvas.HasPoint(sv) || !InOpen(q, true)))
                    {
                        if (OS.GetCmdlineUserArgs().Contains("--teach-diag")) GD.Print($"teachdiag {c.Id} t={Battle?.Time ?? 0:0.0} seen-blocked block={diagBlock}");
                        break;
                    }
                    pts.Add(v); worldOn++;
                    // (and what is ringed beside it, on the screen: the Knight himself)
                    if (t.Ring?.Invoke() is { } ring)
                        foreach (var q in ring)
                            if (OnScreen(q) is Vector2 rv && Canvas.HasPoint(rv)) { pts.Add(rv); worldOn++; }
                    break;
                }
                pts.Add(v);
                worldOn++;
            }
        }
        return (pts, areas, gone, worldOn);
    }

    /// <summary>Whether a point on the ground, and she, are in the open: nothing standing 2.6 m or more over
    /// the ground (a roof, a canopy) lies between them and the camera. By the world's bounding boxes:
    /// coarse, so it errs toward waiting. (The ground's big chunks and the low things are passed over.)</summary>
    double diagAt = -9; string diagBlock = "-";
    static readonly Rect2 Canvas = new(40, 40, 1840, 1000);

    /// <summary>(`raised`: the point is where it is, not on the ground: a figure's head; the figure's own
    /// shape, small and round the point, is passed over.)</summary>
    /// <summary>A mesh's faces, for a line's true strike (built once a mesh).</summary>
    readonly Dictionary<Rid, TriangleMesh?> faces = new();
    TriangleMesh? Faces(Mesh m)
    {
        if (faces.TryGetValue(m.GetRid(), out var tm)) return tm;
        return faces[m.GetRid()] = m.GenerateTriangleMesh();
    }

    bool InOpen((double X, double Y, double Z) p, bool raised = false)
    {
        diagBlock = "-";
        if (scene == null) return true;
        var scenario = camera.GetWorld3D().Scenario;
        var from = camera.GlobalPosition;
        bool Clear(Vector3 to, float ground)
        {
            foreach (var id in RenderingServer.InstancesCullRay(from, to, scenario))
            {
                if (GodotObject.InstanceFromId((ulong)id) is not GeometryInstance3D g || !g.IsVisibleInTree()) continue;
                var box = g.GlobalTransform * g.GetAabb();
                if (raised && box.HasPoint(to) && box.Size.X < 3 && box.Size.Z < 3) continue;
                if (box.Size.X > 60 || box.Size.Z > 60 || box.End.Y < ground + 2.6f) continue;
                // (a scatter's box is the whole field's: each of its plants is asked on its own)
                if (g is MultiMeshInstance3D { Multimesh: { Mesh: { } mesh } mm })
                {
                    var local = mesh.GetAabb();
                    int n = mm.VisibleInstanceCount >= 0 ? mm.VisibleInstanceCount : mm.InstanceCount;
                    for (int k = 0; k < n; k++)
                    {
                        var ib = g.GlobalTransform * mm.GetInstanceTransform(k) * local;
                        if (raised && ib.HasPoint(to) && ib.Size.X < 3 && ib.Size.Z < 3) continue;
                        if (Covers(ib, g, to, ground)) return false;
                    }
                    continue;
                }
                if (Covers(box, g, to, ground)) return false;
            }
            return true;
        }
        bool Covers(Aabb box, Node g, Vector3 to, float ground)
        {
            if (box.End.Y < ground + 2.6f || box.IntersectsSegment(from, to) == null) return false;
            for (int i = 1; i < 48; i++)
            {
                var q = from.Lerp(to, i / 48f);
                if (q.Y > ground + 2.6f && box.HasPoint(q))
                {
                    // (a mesh's box is coarse: a wall standing across the view boxes a field of open ground
                    // behind it. Its own faces are asked: the line must strike them. MR5 item 12: a cracked
                    // wall's box hid the Knight's lane, and her, through both windups.)
                    if (g is MeshInstance3D { Mesh: { } mesh } mi && Faces(mesh) is { } tm)
                    {
                        var inv = mi.GlobalTransform.AffineInverse();
                        if (tm.IntersectSegment(inv * from, inv * to).Count == 0) return false;
                    }
                    diagBlock = $"{g.GetPath()} box={box.Position}/{box.Size}";
                    return true;
                }
            }
            return false;
        }
        float gy = (float)scene.HeightAt(p.X, p.Z);
        if (raised) return Clear(new Vector3((float)p.X, (float)p.Y, (float)p.Z), gy);
        if (!Clear(new Vector3((float)p.X, gy + 0.1f, (float)p.Z), gy)) return false;
        if (Battle?.Player is { } pl)
        {
            float hy = (float)scene.HeightAt(pl.X, pl.Z);
            if (!Clear(new Vector3((float)pl.X, hy + 1.0f, (float)pl.Z), hy)) return false;
        }
        return true;
    }

    /// <summary>(the autopilot) Whether a figure standing here, foot to head (`up` metres), is in the open
    /// from the camera, as a freeze in the open (Aim.Open, Aim.Seen) asks.</summary>
    public bool OpenGround(double x, double z, double up)
    {
        if (scene == null) return true;
        double gy = scene.HeightAt(x, z);
        return InOpen((x, gy + 0.1, z), true) && InOpen((x, gy + up * 0.75, z), true) && InOpen((x, gy + up, z), true);
    }

    /// <summary>Where a thing pointed at stands well inside the screen: clear of its edges, the map and the HUD.</summary>
    static readonly Rect2 SafeArea = new(300, 150, 1320, 700);
    /// <summary>(M6 l4) A ring's lowest pixel: above the HUD's figures and seats (the Drowned Girl's head at about 890).</summary>
    const float RingFloor = 870;
    /// <summary>The minimap and the zone's header and objectives under it (top right): a ring there sat
    /// against the words (au1 item 9, the lamps).</summary>
    static readonly Rect2 HudCorner = new(1460, 0, 460, 450);
    static bool InSafe(Vector2 v) => SafeArea.HasPoint(v) && !HudCorner.HasPoint(v);

    /// <summary>The callout's things in the world that are off the screen: the point on the screen's edge
    /// toward each, and which way (a lamp behind the camera's edge gets a chevron there).</summary>
    List<(Vector2 At, Vector2 Dir)> OffScreen(Callout c)
    {
        var list = new List<(Vector2, Vector2)>();
        if (c.Target.World == null || c.Target.Safe) return list;
        var mid = new Vector2(960, 540);
        foreach (var p in c.Target.World())
        {
            var w = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            if (camera.IsPositionBehind(w) || OnScreen(p) is Vector2 on && (!c.Target.Each || InSafe(on))) continue;
            var d = camera.UnprojectPosition(w) - mid;
            float far = d.Length() - Ui.Callout.EdgeTip - 8;
            if (far < 1) continue;
            d = d.Normalized();
            // (pinned where the line toward it leaves the safe frame: the marker's top at y 150, clear of
            // the boss bar's words; 24 px in at the sides; over the HUD's foot; 24 px clear of the map and
            // the objectives under it (x 1520 on, to y 480). Its tip points along the line, at the thing.)
            Vector2? at = null;
            for (float t = 0; t < Math.Min(far, 1400); t += 2)
            {
                var c0 = mid + d * t;
                var lo = c0 - Vector2.One * Ui.Callout.EdgeRim;
                var hi = c0 + Vector2.One * Ui.Callout.EdgeRim;
                var tip = c0 + d * Ui.Callout.EdgeTip;
                lo = new Vector2(Math.Min(lo.X, tip.X), Math.Min(lo.Y, tip.Y));
                hi = new Vector2(Math.Max(hi.X, tip.X), Math.Max(hi.Y, tip.Y));
                if (lo.X < 24 || lo.Y < 150 || hi.X > 1920 - 24 || hi.Y > 860) break;
                if (hi.X > 1520 - 24 && lo.Y < 480 + 24) break;
                at = c0;
            }
            if (at is not Vector2 a0) continue;
            list.Add((a0, d));
        }
        return list;
    }

    Vector2? Primary(Callout c)
    {
        if (scene == null) return null;
        var (pts, areas, _, _) = Resolve(c);
        return pts.Count > 0 ? pts[0] : areas.Count > 0 ? areas[0].GetCenter() : null;
    }

    /// <summary>A "seat:Skill2" aim's slot (Skill1 is slot 0), if it names a skill key.</summary>
    static int? SeatSlot(string hud) => Enum.TryParse<Act>(hud[5..], true, out var a) && a is >= Act.Skill1 and <= Act.Skill6 ? a - Act.Skill1 : null;

    Presence Where(Callout c)
    {
        var t = c.Target;
        if (t.Hud == "card:weapon") return teachOffers?.Any(o => o.Kind == OfferKind.Weapon) == true ? Presence.Here : Presence.NotYet;
        if (t.Hud == "cards") return teachOffers is { Count: > 0 } ? Presence.Here : Presence.NotYet;
        if (t.Hud is string s && s.StartsWith("socket:") && hud.SocketOf(s[7..]) == null) return Presence.NotYet;
        if (t.Hud is string st && st.StartsWith("seat:") && (SeatSlot(st) is not int sl || hud.SeatRect(sl) == null)) return Presence.NotYet;
        // (a HUD part that comes and goes: here while it shows)
        if (t.Hud == "lamp_offer" && hud.LevelCardArea == null) return Presence.NotYet;
        if (t.Hud == "prompt" && hud.PromptArea == null || t.Hud == "minimap" && hud.MinimapArea == null
            || t.Hud == "tally" && hud.TallyArea == null) return Presence.NotYet;
        // (a freeze on her own state: never the moment a roof hides her)
        if (t.HerSeen && Battle?.Player is { } pl && scene != null && !InOpen((pl.X, scene.HeightAt(pl.X, pl.Z) + 1.3, pl.Z), true)) return Presence.NotYet;
        if (t.World != null)
        {
            // (several things: here when one of the world's is on the screen; a HUD part alone doesn't count)
            var (_, _, gone, worldOn) = Resolve(c);
            if (gone) return Presence.Gone;
            if (worldOn == 0) return Presence.NotYet;
        }
        return Presence.Here;
    }

    /// <summary>Each frame in play: the line moves on, and what is up is aimed.</summary>
    void UpdateTeach(double dt)
    {
        if (scene == null || Mode != "play") return;
        if (!scene.SimPaused) teachClock += dt;
        TeachHurt(dt);
        PaceLog();
        var t = Teacher;
        if (hudMode == "draft") teachOffers = offers; else teachOffers = null;
        var was = t.Current;
        var now = t.Update(teachClock, RealNow, TeachBusy(), Where);
        if (was != null && t.Current != was) TeachDown(was);
        if (now != null) TeachUp(now);
        hud.TeachCard = t.Current?.Target.Hud == "card";
        AimCallout();
        // (--teach-diag with --shot: each freeze's frame first with the ember halos held out, to measure them by)
        // (the callout's own frame a few frames after, halos back: the two differ by the halos alone)
        if (haloDiag != null && !Shots.Pending("teach_" + haloDiag + "_nohalo")) { scene.Fx.HalosHidden = false; haloDiag = null; }
        if (dimDiag != null)
        {
            // (undimmed, then the old flat dim, then this one)
            bool held = Shots.Pending("teach_" + dimDiag + "_nodim"), old = Shots.Pending("teach_" + dimDiag + "_olddim");
            Ui.Callout.DimHeld = held; Ui.Callout.DimOld = !held && old;
            if (!held && !old) dimDiag = null;
        }
    }

    string? haloDiag, dimDiag;

    string? paceStage;
    bool paceSprung, paceInterrupted, paceWinding; int paceWindups;
    double paceHpT;

    /// <summary>--pace (the tutorial's pacing audit): each Prologue stage as it begins, and her health
    /// every 5 s of play, with the game's clock.</summary>
    /// <summary>A pace note said; the Ford-Warden's (B1, the boss's trace) also shot with --shot at each move's tell and
    /// landing, and --until-ford quits 12 s after he falls (the run stops at the boss's death).</summary>
    void FordNote(string note, Battle b)
    {
        GD.Print(note);
        if (!note.StartsWith("ford ")) return;
        if (note.StartsWith("ford down") && Args.Has("until-ford")) After(12, () => QuitPath.Request(GetTree(), 0, "until-ford"));
        if (!Args.Has("shot")) return;
        string t = $"{b.Time:000.0}";
        if (note.StartsWith("ford mode") && note.IndexOf("->", StringComparison.Ordinal) is int ar and > 0)
        {
            string m = note[(ar + 2)..note.IndexOf(' ', ar)];
            // (a tell half-way through, a blow as it lands, a stun and a channel a beat in)
            double at = m switch { "windup" => 0.55, "cleave" => 0.12, "chargeWind" => 0.7, "charge" => 0.25, "stun" => 0.4, "channel" => 1.0, "dead" => 1.0, _ => -1 };
            if (at >= 0) Shots.Want($"ford_{t}_{m}", at);
            if (m == "stun") Shots.Want($"ford_{t}_stun2", 2.0);
            // (the strike's own frames, sw and cl, are the view's, on his clock: WardenView.StrikeShots)
        }
        else if (note.StartsWith("ford touch") || note.StartsWith("ford cleave")) Shots.Want($"ford_{t}_{note.Split(' ')[1]}", 0.02);
    }

    void PaceLog()
    {
        if (!Args.Has("pace") || Battle is not { } b) return;
        string? st = zone is Zones.Prologue pr ? pr.Now.ToString() : null;
        if (st != paceStage) { paceStage = st; GD.Print($"pace stage {st} t={b.Time:0.0} hp={b.Player.Hp:0}/{b.MaxHp:0} at=({b.Player.X:0},{b.Player.Z:0})"); }
        if (zone is Zones.Prologue { Sprung: true } && !paceSprung)
        {
            paceSprung = true;
            GD.Print($"pace sprung t={b.Time:0.0} hp={b.Player.Hp:0}/{b.MaxHp:0}");
            if (Args.Has("shot")) { Shots.Want("ambush_sprung", 1.6); Shots.Want("ambush_volley", 2.3); }
        }
        if (zone is Zones.Prologue pz)
            while (pz.PaceNotes.Count > 0)
            {
                var n = pz.PaceNotes.Dequeue();
                if (n.StartsWith("ford mode ")) { paceWinding = n.Contains("->windup "); if (paceWinding) paceWindups++; }
                FordNote(n, b);
            }
        // --b1interrupt (B1 harness): his second cleave windup is interrupted at 0.55 s, as a Flare or a perfect dodge would.
        if (Args.Has("b1interrupt") && zone is Zones.Prologue { BossInFrame: { } bw } && !paceInterrupted
            && paceWinding && paceWindups == 2 && bw.AnimT >= 0.55 && bw.AnimT < 0.9)
        {
            paceInterrupted = true;
            GD.Print($"pace b1interrupt t={b.Time:0.00} at={bw.AnimT:0.00} state={bw.State}");
            b.Interrupt(bw);
            if (Args.Has("shot")) { Shots.Want("ford_int_0", 1 / 60.0); Shots.Want("ford_int_1", 0.15); Shots.Want("ford_int_2", 0.45); Shots.Want("ford_int_3", 0.9); }
        }
        if (b.Time - paceHpT >= 5) { paceHpT = b.Time; GD.Print($"pace hp t={b.Time:0.0} hp={b.Player.Hp:0}/{b.MaxHp:0} stage={st} at=({b.Player.X:0},{b.Player.Z:0}) draughts={Journey?.Draughts}"); }
    }

    double hurtT;
    bool hurtDone, flareGiven;

    /// <summary>--teach-hurt (a scripted run): her health down to 35% once, 10 s of play into the
    /// Prologue's boss, so the draught's callout (F10) is seen.</summary>
    void TeachHurt(double dt)
    {
        if (hurtDone || !Args.Has("teach-hurt") || scene!.SimPaused) return;
        // (and the Flare full once at the Barrow, so F8 is seen: the autopilot keeps it, HoldFlare)
        if (!flareGiven && zone is Zones.Prologue { Now: Zones.Prologue.Stage.Barrow } && Battle is { Flare: not null } fb && fb.Player.Alive)
        {
            flareGiven = true;
            fb.FlareMeter = Math.Max(fb.FlareMeter, Battle.FlareFull);
            if (Args.Dev) GD.Print($"teach flare t={fb.Time:0.0} meter={fb.FlareMeter:0}");
        }
        if (zone is not Zones.Prologue { Now: Zones.Prologue.Stage.Boss } || Battle is not { } b || !b.Player.Alive) return;
        hurtT += dt;
        if (hurtT < 10) return;
        hurtDone = true;
        b.Player.Hp = Math.Min(b.Player.Hp, b.MaxHp * 0.35);
        if (Args.Dev) GD.Print($"teach hurt t={b.Time:0.0} hp={b.Player.Hp:0}/{b.MaxHp:0} draughts={Journey.Draughts}");
    }

    void TeachUp(Callout c)
    {
        Act? answer = c.Answer != null && Enum.TryParse<Act>(c.Answer, true, out var a) ? a : null;
        if (c.Kind == CalloutKind.Freeze)
        {
            scene!.SimPaused = true;
            teachFroze = true;
            controls.ClearLatches();
            // (the banner shown again under it, without the key it names: the callout says it)
            if (c.Target.Banner is { } ban)
            {
                hud.Announce(ban with { Sub = ban.Sub is { } sub ? System.Text.RegularExpressions.Regex.Replace(sub, @"\s*\([^()]*\)\s*$", "") : null });
                hud.HoldBanner = true;
            }
            // A freeze frame: the figures and the effects hold still too.
            scene.Hold = 1;
            scene.FxStill = true;
            scene.Fx.Frozen = true;
        }
        hud.HoldTip = true;
        // (no damage numbers over the words while a callout is up)
        if (scene != null) scene.Fx.Hits.Visible = false;
        // The part taught is kept (the HUD stays whole; the world dims on a freeze); the chain's callout fades the six places.
        hud.Spotlight(c.Target.Hud == "chain_fill" ? "chain" : c.Target.Hud, c.Kind == CalloutKind.Freeze, c.Target.Hud is "chain" or "chain_fill");
        // (night: the zone after dark, or a fight by the ember's light)
        var view = new Ui.Callout { Night = scene?.View.Night == true || !Ui.Cuff.Day };
        hud.Callout(view);
        view.Show(new CalloutLook(c.Title, c.Line, c.Kind, answer, c.Kind == CalloutKind.Freeze ? answer ?? Act.Interact : null,
            answer != null ? c.Title.ToLowerInvariant() switch { "dash" => "to dash", "draught" => "to drink", "swing" => "to swing", "groundbreaker" => "to heave", _ => "to use it" } : "to go on")
        { Headed = c.Kind == CalloutKind.Panel || c.Target.Banner != null, Mark = c.Mark, MarkInk = c.MarkInk });
        calloutShown = view;
        AimCallout();
        // (--shot: a frame of each, and a freeze holds until it is taken)
        if (Args.Has("shot") && c.Kind == CalloutKind.Freeze && OS.GetCmdlineUserArgs().Contains("--teach-diag") && scene != null)
        {
            haloDiag = c.Id;
            scene.Fx.HalosHidden = true;
            Shots.Want("teach_" + c.Id + "_nohalo", 0.75);
        }
        // (--dim-diag with --shot: each freeze's frame first undimmed, then dimmed, the same frozen moment)
        if (Args.Has("shot") && c.Kind == CalloutKind.Freeze && OS.GetCmdlineUserArgs().Contains("--dim-diag"))
        {
            dimDiag = c.Id;
            Ui.Callout.DimHeld = true;
            Shots.Want("teach_" + c.Id + "_nodim", 0.75);
            Shots.Want("teach_" + c.Id + "_olddim", 0.9);
        }
        if (Args.Has("shot")) Shots.Want("teach_" + c.Id, haloDiag == c.Id ? 1.05 : dimDiag == c.Id ? 1.1 : 0.9);
    }

    void TeachDown(Callout c)
    {
        // (--shot: frames just after the card is taken down, to see that none of its words is left on the world)
        if (Args.Has("shot") && c.Kind == CalloutKind.Freeze) { Shots.Want("teach_" + c.Id + "_after1", 0.6); Shots.Want("teach_" + c.Id + "_after2", 1.6); }
        calloutShown?.TakeDown();
        calloutShown = null;
        hud.TeachCard = false;
        hud.HoldTip = false;
        hud.HoldBanner = false;
        hud.Spotlight(null, false, false);
        if (scene != null) scene.Fx.Hits.Visible = true;
        if (teachFroze)
        {
            teachFroze = false;
            if (scene != null) { scene.Hold = 0; scene.FxStill = false; scene.Fx.Frozen = false; }
            if (scene != null && screens.Current == null && cine == null && InputOwner.RunsOnClose(hudMode, storybook != null, storyAsked != null)) scene.SimPaused = false;
        }
    }

    void AimCallout()
    {
        if (calloutShown == null || teacher?.Current is not { } c) return;
        var (pts, areas, _, worldOn) = Resolve(c);
        // The look's needs: how big each thing is (a HUD part's ring; a thing in the world, about a
        // man's width at the camera's distance), and where she stands (the words never cover her).
        var radii = new List<float>();
        int hudPts = pts.Count - worldOn;
        if (pts.Count > worldOn)
            radii.Add(HudBottom.Scale * c.Target.Hud switch
            {
                "art" => DgPanel.GlassOuterR,
                "dash" => DgSmall.DashR,
                "draught" => DgSmall.FlaskR,
                "chain" or "chain_fill" => DgPanel.RingR1,
                _ => DgPanel.SeatR,
            });
        int bare = -1;
        List<int>? noArrow = null;
        if (c.Target.World != null)
            foreach (var w in c.Target.World())
                if (OnScreen(w) is Vector2 v) radii.Add(Math.Clamp(PxPerMetre(w) * (float)c.Target.Radius, 20, 56));
        // (a Safe point is the one picked, its things ringed after it: the point bare, the arrow on it,
        // the things ringed at their own size with no arrow)
        if (c.Target.Safe && c.Target.Ring != null && worldOn > 1)
        {
            radii.RemoveRange(Math.Min(radii.Count, hudPts + 1), Math.Max(0, radii.Count - hudPts - 1));
            bare = hudPts;
            noArrow = [];
            foreach (var q in c.Target.Ring())
                if (OnScreen(q) is Vector2 rv && Canvas.HasPoint(rv))
                {
                    noArrow.Add(radii.Count);
                    radii.Add(Math.Clamp(PxPerMetre(q) * (float)c.Target.RingRadius, 28, 110));
                }
        }
        Rect2? her = null;
        if (Battle?.Player is { } pl && scene != null)
        {
            double gy = scene.HeightAt(pl.X, pl.Z);
            if (OnScreen((pl.X, gy, pl.Z)) is Vector2 feet && OnScreen((pl.X, gy + 1.9, pl.Z)) is Vector2 head)
            {
                float h = Math.Max(40, feet.Y - head.Y);
                // (down to her health bar under her feet)
                // (her bar is wider than she is: about 76 px whatever the zoom)
                // (and what she holds: a blade's tip reaches about 1.35 m from her middle, either side, and
                // over her head when raised)
                float ppm = h / 1.9f;
                float wide = Math.Max(Math.Max(h * 0.72f, 84), 2 * 1.35f * ppm);
                float over = Math.Max(6, 0.45f * ppm);
                her = new Rect2(feet.X - wide / 2, head.Y - over, wide, h + 50 + over);
            }
        }
        // The figures on the screen: an arrow bends round them.
        var avoid = new List<Rect2>();
        var shun = new List<Rect2>();
        if (Battle is { } bt && scene != null)
            foreach (var en in bt.Enemies.Living())
            {
                if (en.State == EnemyState.Dying || avoid.Count >= 80) continue;
                double gy = scene.HeightAt(en.X, en.Z);
                if (OnScreen((en.X, gy, en.Z)) is Vector2 f && OnScreen((en.X, gy + 1.8 * (en.Def.Scale ?? 1), en.Z)) is Vector2 hd)
                {
                    float h = Math.Max(24, f.Y - hd.Y);
                    avoid.Add(new Rect2(f.X - h * 0.3f, hd.Y, h * 0.6f, h));
                    if (c.Target.ShunBig && (en.Def.Scale ?? 1) >= 1.4) shun.Add(new Rect2(f.X - h * 0.45f, hd.Y, h * 0.9f, h));
                }
            }
        // (what a lesson names but does not ring, e.g. the Knight that casts the red line: its own pool)
        var pools = new List<Vector3>();
        // (the first is his feet: one ground pool about 1.5 m across; the rest are his body, as crisp as she is)
        var crisp = new List<Vector3>();
        if (c.Target.Seen?.Invoke() is { } seenPts)
            for (int si = 0; si < seenPts.Count; si++)
            {
                var q = seenPts[si];
                if (OnScreen(q) is not Vector2 qv) continue;
                if (si == 0) pools.Add(new Vector3(qv.X, qv.Y, PxPerMetre(q) * 1.5f));
                else crisp.Add(new Vector3(qv.X, qv.Y, PxPerMetre(q) * 0.5f));
            }
        calloutShown.Aim(new CalloutAim(pts, areas, c.Kind == CalloutKind.Panel ? hud.DraftShown?.TipArea : null)
        {
            Her = her, Radii = radii, HudPoints = hudPts, Avoid = avoid, Edges = OffScreen(c), Cold = c.Target.Cold, Shun = shun, Pools = pools, Crisp = crisp,
            WordsNear = c.Target.WordsNear is { } wn ? new Vector2((float)wn.X * 1920, (float)wn.Y * 1080) : null,
            Bare = bare, NoArrow = noArrow,
            AreaGrow = c.Target.Hud is string sk && sk.StartsWith("socket:") ? 6 : c.Target.Hud is "chain" or "chain_fill" ? 2 : 12,
        });
    }

    /// <summary>How many of the canvas's pixels a metre is, at a point in the world.</summary>
    float PxPerMetre((double X, double Y, double Z) p)
    {
        var w = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
        return camera.UnprojectPosition(w + camera.GlobalTransform.Basis.X).DistanceTo(camera.UnprojectPosition(w));
    }

    /// <summary>A key while a freeze is up: its answer goes on (and happens), any other key but
    /// moving goes on from one that asks nothing, Esc skips it. True: the key is spent.</summary>
    bool TeachKey(Act a)
    {
        if (teacher?.Current is not { Kind: CalloutKind.Freeze } c) return false;
        double real = RealNow;
        if (a is Act.Pause or Act.Cancel) { teacher.Close("skip", real); TeachDown(c); controls.ClearLatches(); return true; }
        if (!teacher.CanContinue(real)) return true;
        Act? answer = c.Answer != null && Enum.TryParse<Act>(c.Answer, true, out var an) ? an : null;
        if (answer is Act want)
        {
            if (a != want) return true;
            teacher.Close("key", real);
            TeachDown(c);
            // The press goes through: the dash rolls (its latch is kept), the draught is drunk, the art cast.
            return false;
        }
        if (a is Act.Up or Act.Down or Act.Left or Act.Right) return true;
        teacher.Close("key", real);
        TeachDown(c);
        controls.ClearLatches();
        return true;
    }

    /// <summary>The draft is presented: a panel callout on it ends with the panel it was on, and the
    /// next can come up on this one. True: one speaks on this panel (the tip's place is its).</summary>
    bool TeachPanel(List<Offer> list)
    {
        if (teacher == null || scene == null) return false;
        if (teacher.Current is { Kind: CalloutKind.Panel } up) { teacher.Close("picked", RealNow); TeachDown(up); }
        teachOffers = list;
        var was = teacher.Current;
        var now = teacher.Update(teachClock, RealNow, TeachBusy() | Busy.Draft, Where);
        if (was != null && teacher.Current != was) TeachDown(was);
        if (now != null) TeachUp(now);
        return teacher.Current is { Kind: CalloutKind.Panel };
    }

    /// <summary>The place is left: what waits is let go, what is up comes down.</summary>
    void TeachLeave()
    {
        if (teacher == null) return;
        var up = teacher.Current;
        teacher.Clear(teachClock);
        if (up != null) TeachDown(up);
    }
}
