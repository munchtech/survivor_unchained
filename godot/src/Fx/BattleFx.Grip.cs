using GripPaint = SurvivorUnchained.Look.GripPaint;
using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Her held grip's cut (P7 lead 5, take 4; the most-seen effect in the game): THE STROKE HER BLADE LEAVES, built from
/// the blade itself. Her held blade's hilt and tip are sampled in world space on every skeleton update (the frame's
/// final pose, after the attachments: no frame of lag), and the trail is painted on the blade's swept area over the
/// cut's fast frames as ONE brushed sweep, a heavy-headed comma: its leading edge is the tip's path, clean and hard;
/// its inner edge starts part way up the blade and runs out to the tip's path, down to a brush tail a few px wide
/// drawn to a point; at its head the blade itself is lit white down to the guard (the head IS her sword, so the stroke
/// is joined to her hand). Painted by the house brush (fx_stroke_at, through shaders/fx_grip_stroke.gdshader) in three
/// nested commas: white-gold the widest and the shortest, gold inside it, amber the tail and the inner side's dry
/// bristles, whose streaks run along the sweep. A short stroke (the frames before the contact, the last of its leaving)
/// is the same comma small: a clean wedge on the blade, never a sliver. It shows two frames before the contact (the
/// sim's AttackAnim and the clip's contact, data/anim/her_events.json), is whole on the contact, its head stays on the
/// blade through the follow-through, and it leaves by running its tail up to the blade (the amber, then the gold
/// stepping out: the white is last), gone 0.15 s after the contact at the cut's END. Through a hitstop the watch's
/// clock holds with the fight, so the trail is the held blade's. Where the blade's line crosses the struck body: a
/// short white cut-through ON the blade, laid along its travel, with a few tears thrown along it.
/// THE LINK: a chain is the next cut inside a window of the last one's contact with the grip still held. Between its
/// cuts the blade's edge stays hot (a core line on the real blade, a glint at its tip: the ribbon at rest), and a cut
/// that crosses the OPPOSITE way grows out of where the last one ended: its tail is a thread from that end through a
/// turn hook into its own first fast sample. Built from the blade's samples and the cuts' sides alone, so it holds on
/// today's reset clips and on chain clips alike. Every size, share and timing is data (fx_language.json p7 "grip").
/// Sunder's is the wider and whiter; the Oathblade's is thinner and more gold, and keeps its gold pool on the ground.
/// Called from Swing() for a held cut; at --cel off or --p7fx-off (or --grip-old) Swing() draws the old crescents.
/// No blade found (never in the campaign): nothing is drawn.
/// </summary>
public partial class BattleFx
{
    static readonly bool GripStrokeOn = FxCel.On && !P7Off && !Args.Has("grip-old");
    static readonly bool GripSay = Args.Has("clip") || Args.Has("grip-say"), GripSayAll = Args.Has("grip-say");
    const string GripShader = "res://shaders/fx_grip_stroke.gdshader";
    /// <summary>The margin drawn past the tip's path (a share of the blade: the pressed ribs' outer edge and the splay's tines).</summary>
    const float GripOver = 0.35f;
    /// <summary>(take 7) The laying's numbers (fx_language.json p7 grip.press).</summary>
    static GripPaint.Press GripPress => gripPress ??= new GripPaint.Press(P7D.All("grip.press.rise"), P7D.All("grip.press.lift"), P7D.All("grip.press.contact"), P7D["grip.press.white"]);
    static GripPaint.Press? gripPress;

    /// <summary>The look by weapon (fx_language.json p7 grip.sunder / grip.oath): the stroke's width at press 1 (a share
    /// of the blade), the longest drawn (m of the tip's path), the contact's size.</summary>
    readonly record struct GripLook(float Head, float MaxLen, float Flash);
    static GripLook? gripSunder, gripOath;

    static GripLook GripLookOf(bool oath)
    {
        if ((oath ? gripOath : gripSunder) is { } l) return l;
        string k = oath ? "grip.oath." : "grip.sunder.";
        var n = new GripLook(P7D[k + "head"], P7D[k + "max_len"], P7D[k + "flash"]);
        if (oath) gripOath = n; else gripSunder = n;
        return n;
    }

    readonly record struct GripAt(Vector3 Hilt, Vector3 Tip, double At);
    readonly List<GripAt> gripRing = new(40);
    Node3D? gripBlade;
    Skeleton3D? gripSkel;
    double gripClock, gripAnimT = -1, gripDue = -1, gripPressAt, gripTimeWas, gripRealWas, gripSeen, gripCt;
    /// <summary>This frame's share inside gripClock, whether it is the frame's own yet (GripSettle), and the last
    /// frame's hold.</summary>
    double gripShare;
    bool gripSettled = true, gripHeldWas;
    bool gripDueOath;
    int gripDueSide;
    ulong gripDrawn, gripEdgeDrawn;

    sealed class GripTrail
    {
        public bool Oath;
        /// <summary>In the watch's clock: the oldest sample drawn, the contact (-1: not yet), and when a trail still
        /// waiting for its cut gives up.</summary>
        public double Tail, Contact = -1, Until;
        /// <summary>The contact (the stroke's own bite), owed until the blade's line has crossed the struck body (or the wait is up).</summary>
        public bool FlashOwed;
        public int FlashTries, Struck, Killed;
        /// <summary>The contact: when the blade crossed the body (the watch's clock; -1: not yet) and its size by the
        /// bodies struck.</summary>
        public double BiteAt = -1;
        public float Bite;
        /// <summary>(take 7) THE LAID RIBS: each stores its own press and whiteness when the blade lays it (GripPaint);
        /// the contact's stamp on them (pressed once, in place), the tip's distance from her then and the cut's reach
        /// (the throw's streaks run out to it).</summary>
        public readonly List<GripPaint.Rib> Laid = new(96);
        public GripPaint.Stamp Stamp;
        public float StampR, Reach;
        /// <summary>The drawn frame the stroke's path first kinked on screen (-1: never): the part before the kink runs
        /// out from then (grip.kink).</summary>
        public int KinkFrame = -1;
        public Vector3 Body;
        /// <summary>Which way it crosses (the clip's, then the blade's own measured on the contact), and the sim's.</summary>
        public int Side, SimSide;
        public bool CutSaid, LinkAsked, Linked;
        /// <summary>The last cut's end (the tip, from her) and its tip's last fast travel: where this one's thread starts.</summary>
        public Vector3 LinkTip, LinkTan;
        /// <summary>This cut's own last fast travel.</summary>
        public Vector3 EndTan = Vector3.Right;
        public int Said;
        /// <summary>The tip's sweep round her over the cut's fast frames (radians, as the sim's angles run).</summary>
        public double Swept, SweptAt;
        /// <summary>The longest it was drawn (m) and the frame of it (the `grip end` line's `full`).</summary>
        public float FullLen;
        public int FullFrame;
        /// <summary>The stroke's own brush (its lanes' jitter), drawn once.</summary>
        public float Seed;
    }

    /// <summary>The chain: the last cut (its weapon, side and contact), where it ended once its trail has run up, and
    /// when it broke (-1: alive).</summary>
    sealed class GripChain
    {
        public bool Oath, Ended;
        public int Side;
        public double Contact, Out = -1;
        public Vector3 EndTip, EndTan;
    }

    GripTrail? gripLive;
    GripChain? gripChain;
    MeshInstance3D? gripNode, gripEdgeNode;
    ImmediateMesh? gripMesh, gripEdgeMesh;
    ShaderMaterial? gripMat, gripEdgeMat;
    int gripWarm;
    readonly List<(Vector3 H, Vector3 T)> gripPts = new(200);
    readonly List<float> gripCum = new(200);
    /// <summary>Each path point's time in the watch's clock (the laid ribs' key).</summary>
    readonly List<double> gripAtT = new(200);

    public override void _EnterTree()
    {
        if (GripStrokeOn) GetTree().ProcessFrame += GripWatch;
    }

    public override void _ExitTree()
    {
        if (!GripStrokeOn) return;
        GetTree().ProcessFrame -= GripWatch;
        GripUnhook();
    }

    void GripUnhook()
    {
        if (gripSkel != null && IsInstanceValid(gripSkel)) gripSkel.SkeletonUpdated -= GripSample;
        gripSkel = null; gripBlade = null;
        gripRing.Clear();
    }

    /// <summary>Each frame, before anything moves: the watch's clock (real time, held with the fight through a hitstop,
    /// whose clock runs at 8%: the trail is the held blade's, it neither runs on nor doubles), the hook on her skeleton
    /// kept on the blade she holds now, the chain's end, and a trail whose skeleton stood still.</summary>
    void GripWatch()
    {
        double real = GetProcessDeltaTime();
        // (the last frame's share, if nothing settled it: no cut, no sample)
        GripSettle(true);
        // Whether the fight is held on THIS frame is known only once the fight has moved (GripSettle): the last frame's
        // hold stands in until then.
        gripShare = gripHeldWas ? real * 0.08 : real;
        gripClock += gripShare;
        gripTimeWas = time; gripRealWas = real; gripSettled = false;
        var bl = Flare.Blade;
        bool has = bl != null && IsInstanceValid(bl) && bl.IsInsideTree();
        if (!has) { if (gripBlade != null || gripSkel != null) GripUnhook(); }
        else if (!ReferenceEquals(bl, gripBlade) || gripSkel == null || !IsInstanceValid(gripSkel))
        {
            GripUnhook();
            Node? n = bl;
            while (n != null && n is not Skeleton3D) n = n.GetParent();
            if (n is Skeleton3D sk) { gripBlade = bl; gripSkel = sk; sk.SkeletonUpdated += GripSample; GripNode(); }
        }
        if (gripChain is { Out: < 0 } ch && (gripClock - ch.Contact > P7D["grip.link.window"] || !GripKeyHeld(ch.Oath))) ch.Out = gripClock;
        ulong f = Engine.GetProcessFrames();
        if (gripLive != null && gripDrawn + 1 < f) GripDraw();
        if (gripChain != null && gripEdgeDrawn + 1 < f) GripEdgeDraw();
    }

    /// <summary>The watch's clock made this frame's own, once the fight's clock has moved (`last`: at the next frame's
    /// start, whatever it did): the frame counts 8% if the fight was held on it, else whole. (Lead 7: the hold was read
    /// a frame late, off the frame before. A hitstop's first sample then had the pose at 8% over a whole frame of clock
    /// and its first free sample a whole frame's travel over 8%: 12 times too slow, 12 times too fast, neither a cut
    /// to GripCutting, so the stroke's run broke twice and the Oathblade's stroke was gone for the hold's frames.)</summary>
    void GripSettle(bool last = false)
    {
        if (gripSettled || gripRealWas <= 0 || (!last && time <= gripTimeWas)) return;
        bool held = !Flare.Active && time > gripTimeWas && time - gripTimeWas < gripRealWas * 0.09;
        double share = held ? gripRealWas * 0.08 : gripRealWas;
        gripClock += share - gripShare;
        gripShare = share; gripHeldWas = held; gripSettled = true;
    }

    /// <summary>The blade now, in world space: its guard end (a little up the blade) and its tip.</summary>
    (Vector3 Hilt, Vector3 Tip)? GripBladeNow()
    {
        if (gripBlade is not { } bl || !IsInstanceValid(bl) || !bl.IsInsideTree()) return null;
        float tip = bl.HasMeta("tip") ? (float)bl.GetMeta("tip") : 1.4f;
        var xf = bl.GlobalTransform;
        return (xf * new Vector3(0, tip * 0.14f, 0), xf * new Vector3(0, tip, 0));
    }

    /// <summary>Her skeleton has its frame's pose (and the attachments theirs): the blade's sample, a held cut's trail
    /// armed from the sim's swing, and the trail and the hot edge drawn from the samples.</summary>
    void GripSample()
    {
        if (GripBladeNow() is not { } now) return;
        GripSettle();
        if (gripRing.Count > 0 && gripRing[^1].At >= gripClock - 1e-6) gripRing[^1] = new GripAt(now.Hilt, now.Tip, gripClock);
        else gripRing.Add(new GripAt(now.Hilt, now.Tip, gripClock));
        if (gripRing.Count > 36) gripRing.RemoveRange(0, gripRing.Count - 36);
        if (gripWarm > 0) GripWarm();
        // A held cut's swing has begun (the sim's AttackAnim: its clip and rate): the trail is owed two frames before
        // the clip's contact comes round. (Sunder's heavy blow is the ground's line, not a cut: nothing is armed for
        // it, so no trail shows that no cut follows; a heavy blow that is a cut is born on its contact.)
        if (b0 is { } b && b.Player.AttackAnim is { Clip: { } clip } aa && aa.T != gripAnimT)
        {
            gripAnimT = aa.T; gripDue = -1; gripPressAt = gripClock;
            if (!Flare.HushesSwings && HerEvents.Contact(clip) is double ct && GripHeld(b, aa.Weapon, out gripDueOath) && (gripDueOath || !aa.Heavy))
            {
                gripDue = aa.T + ct / Math.Max(0.1, aa.Rate);
                gripSeen = (time - aa.T) * 60; gripCt = (gripDue - aa.T) * 60;
                gripDueSide = HerEvents.Side(clip) ?? 0;
                // (take 8, F5) the side is known when the trail is armed (the sim's own next side, read, not taken): a
                // trail of side 0 drew the wind-up's sweep back for its first frames, then dropped it (a chip, a dead frame)
                if (gripDueSide == 0)
                    foreach (var w in b.Weapons)
                        if (w.Id == aa.Weapon) { gripDueSide = w.ClipSide != 0 ? w.ClipSide : (w.Cuts & 1) == 0 ? -1 : 1; break; }
                if (GripSayAll) GD.Print($"grip due frame {Engine.GetFramesDrawn()} clip {clip} side {gripDueSide} (clip's {HerEvents.Side(clip) ?? 0})");
            }
        }
        double lead = P7D["grip.lead_frames"] / 60.0;
        if (gripDue >= 0 && time >= gripDue - lead - 0.004)
        {
            if (time < gripDue + 0.05) GripArm(new GripTrail { Oath = gripDueOath, Side = gripDueSide, Tail = Math.Max(gripPressAt, gripClock), Until = gripClock + lead + 2.5 / 60 });
            gripDue = -1;
        }
        if (gripLive != null) GripDraw();
        if (gripChain != null) GripEdgeDraw();
    }

    static bool GripHeld(Battle b, string weapon, out bool oath)
    {
        oath = false;
        foreach (var w in b.Weapons)
            if (w.Id == weapon)
            {
                oath = IsOath(w.Art);
                return w.Hold && (oath || w.Art == "slash_heavy") && !(oath && AaFxOff);
            }
        return false;
    }

    /// <summary>Whether the grip's key is still down (the chain lives only while she keeps cutting).</summary>
    bool GripKeyHeld(bool oath)
    {
        if (b0 is not { } b) return false;
        foreach (var w in b.Weapons)
            if (w.Hold && w.Held && (oath ? IsOath(w.Art) : w.Art == "slash_heavy")) return true;
        return false;
    }

    /// <summary>A new trail: its own bristles, and (its side known from its clip) whether it grows out of the last cut.</summary>
    void GripArm(GripTrail tr)
    {
        gripLive = tr;
        gripMat?.SetShaderParameter("fx_stroke_seed", R() * 97f);
        if (tr.Side != 0) GripLinkAsk(tr);
    }

    /// <summary>The link: the chain alive, the same grip, the last cut ended, and this one crossing the other way.</summary>
    void GripLinkAsk(GripTrail tr)
    {
        tr.LinkAsked = true;
        if (P7D["grip.link.on"] < 0.5f) return;
        if (gripChain is not { Ended: true, Out: < 0 } ch || ch.Oath != tr.Oath || ch.Side != -tr.Side || gripClock - ch.Contact > P7D["grip.link.window"]) return;
        tr.Linked = true; tr.LinkTip = ch.EndTip; tr.LinkTan = ch.EndTan;
    }

    /// <summary>Swing()'s held cut: the contact. The trail (already two frames old, or born here from the samples) is
    /// whole on this frame; the slit waits for the blade to cross the struck body.</summary>
    void GripCut(Ev.Slash e, Vector3 at, float reach, float g, bool oath)
    {
        if (oath && AaFxOff) return;
        GripSettle();
        // (round 4) a swing of several arcs calls this once an arc in one frame, each re-arming the trail: the bodies
        // struck are the CUT's DISTINCT bodies (the arcs' Fresh summed), not its last arc's
        var arc0 = gripLive is { Contact: >= 0, FlashOwed: true } gl && gl.Contact == gripClock ? gl : null;
        if (gripLive is not { Contact: < 0 } tr) { tr = new GripTrail { Oath = oath, Tail = gripClock - 5 / 60.0 }; GripArm(tr); }
        tr.Oath = oath; tr.Contact = gripClock; tr.SimSide = e.Side; tr.Reach = reach;
        if (tr.Side == 0) tr.Side = e.Side;   // (take 8) before this frame's stroke is drawn, not after it
        if (e.Struck > 0)
        {
            tr.FlashOwed = true; tr.Struck = e.Fresh; tr.Killed = e.Killed;
            tr.Body = V(e.HitX, Y(e.HitX, e.HitZ) + 1.0, e.HitZ);
            // (one number a cut, by raise-to: a swing of several arcs calls this once an arc and still shakes once)
            HitShake(P7D[oath ? "hit_budget.grip_shake_oath" : "hit_budget.grip_shake", oath ? 0.02f : 0.06f], "grip");
        }
        if (arc0 != null && arc0 != tr)
        {
            if (!tr.FlashOwed) tr.Body = arc0.Body;
            tr.FlashOwed = true; tr.Struck += arc0.Struck; tr.Killed += arc0.Killed;
        }
        float r = Mathf.Clamp(reach * 0.62f, 1.7f, 2.1f), mid = (float)e.Angle;
        double tx = e.X + Mathf.Cos(mid) * r * 0.9f, tz = e.Z + Mathf.Sin(mid) * r * 0.9f;
        if (!oath)
        {
            // The heavy blade's grit where it passes nearest the ground (grip.contact.grit puffs: 0 now, by day they
            // read as dark blobs on the stroke).
            if ((int)P7D["grip.contact.grit"] is > 0 and var grit) Dust(tx, tz, grit, 1.6f * g);
            HitShake(P7D["hit_budget.grip_shake_air", 0.02f], "grip");
            return;
        }
        // The Oathblade's own: its gold on the ground under the cut, the struck's streaks along its path (HitKit), and a
        // ranked blade's hanging glints.
        oathAt = at; oathMirror = mirror; oathKits = 0;
        OathPool(V(tx, Y(tx, tz) + 0.3, tz), e.Art == "slash_blood" ? new Color("#ff6a40") : new Color("#ffc25a"));
        if (e.Rank >= 5 && e.Art != "slash_blood")
        {
            float span = Mathf.Clamp((float)e.Arc * 0.68f, 1.5f, 2.6f);
            for (int i = 0; i < 3; i++)
            {
                float a = (float)e.Angle + span * (R() - 0.5f);
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                Sparks.Spawn(at + o * r * 0.95f, Vector3.Up * 0.4f, 0.25f, 0.1f, OathGold, OathGold * 0.3f, 0.02f, 0, 2, sprite: Sprites.Of("star"), spinV: 3);
            }
        }
    }

    void GripNode()
    {
        if (gripNode != null && IsInstanceValid(gripNode)) return;
        (gripNode, gripMesh, gripMat) = GripNewNode("GripTrail", 0);
        (gripEdgeNode, gripEdgeMesh, gripEdgeMat) = GripNewNode("GripEdge", 2);
        // (take 8, F0) the stroke's shader is its own (fx_grip_stroke: the bristles are its lanes, grip.fill); the brush
        // include's fx_stroke_shape / fx_bristle are not its uniforms, and the dead key read here (grip.dry) threw before
        // the warm-up was ever asked for: the first cut paid the first use
        gripWarm = 3;
    }

    (MeshInstance3D, ImmediateMesh, ShaderMaterial) GripNewNode(string name, int mode)
    {
        var mesh = new ImmediateMesh();
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>(GripShader) };
        FxCel.Apply(mat, School.Physical, FxAfter.On);
        mat.SetShaderParameter("grip_mode", mode);
        var node = new MeshInstance3D { Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false, Name = name };
        AddChild(node);
        node.GlobalTransform = Transform3D.Identity;
        if (FxAfter.On) FxAfter.Adopt(node);
        return (node, mesh, mat);
    }

    /// <summary>The first use's compiles paid when she takes the blade, not on her first cut: the trail and the hot
    /// edge drawn for three frames, a few centimetres across, under her feet.</summary>
    void GripWarm()
    {
        if (gripLive != null || gripChain != null || gripMesh == null || gripNode == null || gripMat == null || gripEdgeMesh == null || gripEdgeNode == null) { gripWarm = 0; return; }
        gripWarm--;
        var o = PlayerPos + Vector3.Down * 0.3f;
        gripMesh.ClearSurfaces(); gripEdgeMesh.ClearSurfaces();
        if (gripWarm <= 0) { gripNode.Visible = false; gripEdgeNode.Visible = false; return; }
        gripMesh.SurfaceBegin(Mesh.PrimitiveType.Triangles);
        for (int i = 0; i < 3; i++) { gripMesh.SurfaceSetColor(new Color(1, 0, 0)); gripMesh.SurfaceSetUV(new Vector2(0.01f, 0.9f)); gripMesh.SurfaceSetUV2(new Vector2(1, 1)); gripMesh.SurfaceAddVertex(o + new Vector3(i == 1 ? 0.02f : 0, 0, i == 2 ? 0.02f : 0)); }
        gripMesh.SurfaceEnd();
        GripSet(GripLookOf(false), 0.02f, 0, 0.02f, 0, 0, o, null, 0);
        gripNode.Visible = true;
        GripEdgeQuads(o, o + new Vector3(0.02f, 0, 0), 0);
    }

    /// <summary>The trail is over. One that ran its course after a cut leaves the chain its end: where the blade's tip is
    /// now (from her) and the way it last travelled fast.</summary>
    void GripEnd(bool ran)
    {
        if (ran && gripLive is { } tr && gripChain is { Ended: false } ch && gripRing.Count > 0)
        {
            ch.Ended = true; ch.EndTip = gripRing[^1].Tip - PlayerPos; ch.EndTan = tr.EndTan;
            if (GripSay)
            {
                // the timing's numbers (for the clip's contact, her_events.json): the frame the tip was fastest going the
                // cut's way (a sample a frame, counted back from now) and the frame the stroke was longest
                int n = gripRing.Count, pk = n - 1;
                double best = 0;
                for (int k = 1; k < n; k++)
                {
                    if (gripRing[k].At < tr.Tail || !GripCutting(k, 0, tr.Side)) continue;
                    double v = gripRing[k].Tip.DistanceTo(gripRing[k - 1].Tip) / Math.Max(1e-4, gripRing[k].At - gripRing[k - 1].At);
                    if (v > best) { best = v; pk = k; }
                }
                GD.Print($"grip end frame {Engine.GetFramesDrawn()} side {tr.Side} measured {(Math.Abs(tr.Swept) < 0.3 ? 0 : Math.Sign(tr.Swept))} swept {Mathf.RadToDeg(tr.Swept):0} deg gap {(tr.Linked ? 1 : 0)} peak {Engine.GetFramesDrawn() - (n - 1 - pk)} ({best:0.0} m/s) full {tr.FullFrame} ({tr.FullLen:0.00} m)");
            }
        }
        gripLive = null;
        if (gripNode != null && IsInstanceValid(gripNode)) gripNode.Visible = false;
    }

    /// <summary>(take 7) The stroke's material for this frame: `total` and `tailU` are the laid path's metres at the blade
    /// and at the drawn tail; `age` s since the contact (under 0: not yet); the spikes (GripPaint.Spikes), the first
    /// `tines` of them the splay's.</summary>
    void GripSet(GripLook look, float total, float tailU, float blade, float age, float seed, Vector3 her, float[]? spikes, int tines, int since = -1)
    {
        var m = gripMat!;
        var shed = P7D.All("grip.shed_at"); var pt = P7D.All("grip.point"); var cap = P7D.All("grip.cap"); var rag = P7D.All("grip.cap_rag");
        var share = P7D.All("grip.fill.share"); var vals = P7D.All(Flare.Night ? "grip.fill.values_night" : "grip.fill.values_day"); var gold = P7D.All("grip.fill.gold"); var dense = P7D.All("grip.fill.press");
        var st = P7D.All("grip.fill.streak"); var dr = P7D.All("grip.fill.dry"); var tn = P7D.All("grip.fill.tine"); var ct = P7D.All("grip.fill.cut");
        var sw = P7D.All("grip.shed_white");
        m.SetShaderParameter("grip_total", total);
        m.SetShaderParameter("grip_tail_u", tailU);
        m.SetShaderParameter("grip_blade", Mathf.Max(blade, 0.05f));
        m.SetShaderParameter("grip_head", look.Head);
        m.SetShaderParameter("grip_point", new Vector2(pt[0], pt[1]));
        m.SetShaderParameter("grip_cap", new Vector4(cap[0], cap[1], cap[2], cap[3]));
        m.SetShaderParameter("grip_cap2", new Vector2(cap[4], cap[5]));
        m.SetShaderParameter("grip_rag", new Vector3(rag[0], rag[1], rag[2]));
        m.SetShaderParameter("grip_px", P7Px(her));
        m.SetShaderParameter("grip_seed", seed);
        m.SetShaderParameter("grip_narrow", P7D["grip.shed_to"]);
        // leaving: the shed (the whole stroke thins) and the dry gaps (the last three drawn frames: mostly streaks at the end)
        m.SetShaderParameter("grip_leave", age < 0 ? Vector3.Zero : new Vector3(Mathf.Clamp((age - shed[0]) / Mathf.Max(shed[1] - shed[0], 1e-4f), 0, 1), P7D.Curve("grip.dry_out", age), P7D.Curve("grip.dry_tail", age)));
        m.SetShaderParameter("grip_fill", new Vector4(P7D["grip.fill.lanes"], share[0], share[1], P7D["grip.fill.comb"]));
        m.SetShaderParameter("grip_gold", new Vector3(gold[0], gold[1], gold[2]));
        m.SetShaderParameter("grip_dense", new Vector2(dense[0], dense[1]));
        m.SetShaderParameter("grip_loaded", P7D["grip.press.loaded"]);
        m.SetShaderParameter("grip_streak", new Vector4(st[0], st[1], dr[0], dr[1]));
        m.SetShaderParameter("grip_tine", new Vector4(tn[0], tn[1], ct[0], ct[1]));
        m.SetShaderParameter("grip_shedw", new Vector2(sw[0], sw[1]));
        m.SetShaderParameter("grip_out", P7D["grip.splay.out"]);
        // (vii) the stroke's own white (sRGB in the data; the bands are linear), by day and by night
        var w = P7D.All(Flare.Night ? "grip.white.night" : "grip.white.day");
        m.SetShaderParameter("grip_white", new Vector3(GripLin(w[0]), GripLin(w[1]), GripLin(w[2])));
        // (take 8, iii) the fill's two deeper values: the white x these, in sRGB (steps the eye reads at 1:1)
        m.SetShaderParameter("grip_val1", new Vector3(GripLin(w[0] * vals[0]), GripLin(w[1] * vals[1]), GripLin(w[2] * vals[2])));
        m.SetShaderParameter("grip_val2", new Vector3(GripLin(w[0] * vals[3]), GripLin(w[1] * vals[4]), GripLin(w[2] * vals[5])));
        var sp = new float[48];
        int ns = Math.Min(12, (spikes?.Length ?? 0) / 4);
        if (spikes != null) Array.Copy(spikes, sp, ns * 4);
        m.SetShaderParameter("grip_spike", sp);
        m.SetShaderParameter("grip_spike_n", ns);
        m.SetShaderParameter("grip_tine_n", Math.Min(tines, ns));
        // (take 8, iv) a thrown streak FLIES as it is shed: its near end leaves the root, it breaks into dashes
        var fl = P7D.All("grip.throw.fly"); var da = P7D.All("grip.throw.dash");
        int sf = Math.Clamp(since, 0, fl.Length - 1);
        m.SetShaderParameter("grip_fly", new Vector4(since < 0 ? 0 : fl[sf], since < 0 ? 1 : da[Math.Min(sf, da.Length - 1)], P7D["grip.throw.dash_m"], P7D["grip.throw.bend"]));
        m.SetShaderParameter("grip_throw_gold", P7D["grip.throw.color"]);
        gripNode!.CustomAabb = new Aabb(her - new Vector3(8, 3, 8), new Vector3(16, 7, 16));
    }

    static float GripLin(float c) => c <= 0.04045f ? c / 12.92f : Mathf.Pow((c + 0.055f) / 1.055f, 2.4f);

    /// <summary>Whether the blade's tip was fast between sample `j - 1` and `j`.</summary>
    bool GripFast(int j, float slow)
    {
        // (above grip.snap m/s it is no cut: the blade's pose snapping from rest into the clip)
        double d = gripRing[j].Tip.DistanceTo(gripRing[j - 1].Tip), dt = Math.Max(1e-4, gripRing[j].At - gripRing[j - 1].At);
        return d >= slow * dt && d <= P7D["grip.snap"] * dt;
    }

    /// <summary>Whether the blade was CUTTING between sample `j - 1` and `j`: its tip fast, and going round her the
    /// cut's own way (its clip's side; 0: either way). The wind-up's sweep back is fast too: it leaves no stroke.</summary>
    bool GripCutting(int j, float slow, int side) => GripFast(j, slow) && (side == 0 || GripSweep(j) * side > -0.02);

    /// <summary>How far the tip went round her between sample `k - 1` and `k`, as the sim's angles run (radians).</summary>
    double GripSweep(int k)
    {
        var a = gripRing[k - 1].Tip - PlayerPos; var b = gripRing[k].Tip - PlayerPos;
        return Mathf.Wrap(Mathf.Atan2(b.Z, b.X) - Mathf.Atan2(a.Z, a.X), -Mathf.Pi, Mathf.Pi);
    }

    /// <summary>A drawn rib: hilt side, tip, the laid path's metres (U), how much the blade's own sweep, its limit where
    /// the path turns on screen, this frame's metres from the drawn tail (M), and its LAID press, whiteness and raise.</summary>
    struct GripRibV { public Vector3 H, T; public float U, Real, Cap, M, Press, White, Raise; }
    readonly List<GripRibV> gripRibs = new();
    Vector2[] gripRibP = new Vector2[64], gripRibD = new Vector2[64];
    float[] gripRibW = new float[64], gripRibL = new float[64], gripRibC = new float[64];

    /// <summary>(round 4) Lays the ribbon's ribs (hilt side, tip, metres along, how much the blade's own sweep) from
    /// `start` m of the path, each with its CAP: on screen no rib may cross another inside the stroke's width (where
    /// two cross, the one whose crossing lies farther along it ends there, x grip.kink[0]), so where the tip's path turns
    /// the stroke is held inside the turn and pinches at a sharp kink; it never lies over itself. Returns the path's
    /// metres at the last KINK (a rib held under grip.kink[1] of the stroke's own width there), -1 if none.</summary>
    float GripLay(GripTrail tr, GripLook look, float start, float len, Camera3D? faceCam, Vector3 faceBack, float[] face, float[] kk, out float seen, out float way, out float shown, out float after)
    {
        after = 0;
        gripRibs.Clear();
        var hold = P7D.All("grip.press.hold");
        int s = 0;
        while (s < gripPts.Count - 2 && gripCum[s + 1] <= start) s++;
        // the stroke's length as the camera sees it (m at her): a cut swept toward the camera is short on screen
        seen = len;
        if (faceCam != null)
        {
            seen = 0;
            var was = faceCam.UnprojectPosition(gripPts[s].T);
            for (int i = s + 1; i < gripPts.Count; i++) { var p = faceCam.UnprojectPosition(gripPts[i].T); seen += p.DistanceTo(was); was = p; }
            seen *= P7Px(PlayerPos);
        }
        float shownSum = 0, realSum = 0;
        for (int i = s; i < gripPts.Count; i++)
        {
            var sd = faceBack.Cross(gripPts[Math.Min(i + 1, gripPts.Count - 1)].T - gripPts[Math.Max(i - 1, 0)].T);
            if (sd.LengthSquared() < 1e-8f) continue;
            var rl = gripPts[i].H - gripPts[i].T;
            shownSum += rl.Dot(sd.Normalized()); realSum += rl.Length();
        }
        way = Mathf.Abs(shownSum) > 0.15f * realSum ? Mathf.Sign(shownSum) : 0;
        if (way == 0)
        {
            var sd = faceBack.Cross(gripPts[^1].T - gripPts[^2].T);
            way = sd.Dot(PlayerPos + Vector3.Up * 1.1f - gripPts[^1].T) < 0 ? -1 : 1;
        }
        shown = shownSum / Mathf.Max(realSum, 1e-4f);
        for (int i = s; i < gripPts.Count; i++)
        {
            var (h, t) = gripPts[i];
            float u = gripCum[i] - start;
            double laidAt = gripAtT[i];
            if (i == s && u < 0)
            {
                // the drawn tail's own point, between two of the path's
                float f = -u / Mathf.Max(1e-5f, gripCum[i + 1] - gripCum[i]);
                h = h.Lerp(gripPts[i + 1].H, f); t = t.Lerp(gripPts[i + 1].T, f); u = 0; laidAt += (gripAtT[i + 1] - laidAt) * f;
            }
            float real = 1;
            var side = faceBack.Cross(gripPts[Math.Min(i + 1, gripPts.Count - 1)].T - gripPts[Math.Max(i - 1, 0)].T);
            if (face[1] > 0 && side.LengthSquared() > 1e-8f)
            {
                side = side.Normalized() * way;
                var rl = h - t;
                float rlen = Mathf.Max(rl.Length(), 1e-4f);
                real = Mathf.SmoothStep(face[0], face[1], rl.Dot(side) / rlen);
                if (real < 1)
                {
                    var dir = (rl / rlen).Lerp(side, 1 - real);
                    h = t + (dir.LengthSquared() > 1e-4f ? dir.Normalized() : side) * rlen;
                }
            }
            // (take 7) the rib's paint is what was LAID at its place: its metres, its press, its whiteness
            var lv = GripPaint.At(tr.Laid, laidAt, Engine.GetFramesDrawn(), hold);
            gripRibs.Add(new GripRibV { H = h, T = t, U = lv.S, Real = real, Cap = 1f, M = u, Press = lv.Press, White = lv.White, Raise = lv.Raise });
        }
        int n = gripRibs.Count;
        if (faceCam == null || kk[0] <= 0 || n < 3) return -1;
        if (gripRibP.Length < n) { int m = n * 2; gripRibP = new Vector2[m]; gripRibD = new Vector2[m]; gripRibW = new float[m]; gripRibL = new float[m]; gripRibC = new float[m]; }
        // the ribs on screen (px): from the tip toward the hilt, as long as the stroke is wide there (its laid press)
        const float swell = 1f;
        for (int i = 0; i < n; i++)
        {
            var rb = gripRibs[i];
            var p = faceCam.UnprojectPosition(rb.T); var d = faceCam.UnprojectPosition(rb.H) - p;
            float l = d.Length();
            gripRibP[i] = p; gripRibL[i] = l; gripRibD[i] = l > 1e-3f ? d / l : Vector2.Zero;
            gripRibW[i] = Mathf.Min(look.Head * rb.Press, 0.98f) * l;
            gripRibC[i] = float.MaxValue;
        }
        for (int i = 0; i < n - 1; i++)
        {
            float wi = gripRibW[i] * swell;
            if (wi < 0.5f) continue;
            for (int j = i + 1; j < n; j++)
            {
                float wj = gripRibW[j] * swell;
                float cr = gripRibD[i].Cross(gripRibD[j]);
                if (wj < 0.5f || Mathf.Abs(cr) < 1e-5f) continue;
                var r = gripRibP[j] - gripRibP[i];
                float a = r.Cross(gripRibD[j]) / cr, b = r.Cross(gripRibD[i]) / cr;
                if (a <= 0 || a >= wi || b <= 0 || b >= wj) continue;
                if (a >= b) gripRibC[i] = Mathf.Min(gripRibC[i], a); else gripRibC[j] = Mathf.Min(gripRibC[j], b);
            }
        }
        float kink = -1;
        int at = -1;
        for (int i = 0; i < n; i++)
        {
            if (gripRibC[i] == float.MaxValue) continue;
            var rb = gripRibs[i];
            rb.Cap = Mathf.Min(1f, gripRibC[i] * kk[0] / Mathf.Max(gripRibL[i], 1e-3f));
            gripRibs[i] = rb;
            if (gripRibC[i] < kk[1] * gripRibW[i]) { kink = start + rb.M; at = i; }
        }
        // the stroke AFTER the kink, as long as the camera sees it (m at her)
        for (int i = Math.Max(at, 0); at >= 0 && i < n - 1; i++) after += gripRibP[i + 1].DistanceTo(gripRibP[i]);
        after *= P7Px(PlayerPos);
        return kink;
    }

    /// <summary>The trail from the samples: the cut's fast run (the wind-up's drift before it leaves no trail; the head's
    /// slow frames at the swing's end stay, the head is the blade), the blade's path splined between frames (the hilt's
    /// place and the blade's direction, so the blade keeps its length through a fast turn), a linked cut's thread before
    /// it, the whole capped at the look's length and run up toward the head as it leaves.</summary>
    void GripDraw()
    {
        if (gripLive is not { } tr || gripMesh == null || gripNode == null || !IsInstanceValid(gripNode)) return;
        gripDrawn = Engine.GetProcessFrames();
        double age = tr.Contact < 0 ? -1 : gripClock - tr.Contact;
        if (tr.Contact < 0 && gripClock > tr.Until) { GripEnd(false); return; }
        float cut = age < 0 ? 0 : P7D.Curve("grip.retract", (float)age);
        if (cut >= 0.999f) { GripEnd(true); return; }
        var look = GripLookOf(tr.Oath);
        float slow = P7D["grip.slow"];
        int n = gripRing.Count, lo = 0;
        while (lo < n - 1 && gripRing[lo].At < tr.Tail - 1e-6) lo++;
        int j = n - 1;
        if (age >= 0) while (j > lo && !GripCutting(j, slow, tr.Side)) j--;
        int hi = j;
        while (j > lo && GripCutting(j, slow, tr.Side)) j--;
        int i0 = j;
        bool any = hi > i0;
        if (any) tr.EndTan = (gripRing[hi].Tip - gripRing[hi - 1].Tip).Normalized();
        if (any && hi == n - 1 && gripRing[hi].At > tr.SweptAt) { tr.SweptAt = gripRing[hi].At; tr.Swept += GripSweep(hi); }
        if (age >= -1e-6 && !tr.CutSaid)
        {
            // the cut's first frame: its side is its clip's (her_events.json), else the sim's count; the blade's own
            // sweep is measured over the whole cut and said at its end (`grip end`: the number her_events takes)
            tr.CutSaid = true;
            if (tr.Side == 0) tr.Side = tr.SimSide;
            if (!tr.LinkAsked) GripLinkAsk(tr);
            gripChain = new GripChain { Oath = tr.Oath, Side = tr.Side, Contact = tr.Contact };
            if (GripSay) GD.Print($"grip cut frame {Engine.GetFramesDrawn()} side {tr.Side} linked {(tr.Linked ? 1 : 0)} oath {tr.Oath} seen +{gripSeen:0.0}f ct {gripCt:0.0}f");
        }
        if (tr.FlashOwed && age >= -1e-6) GripContact(tr, look, i0);
        if (GripSayAll && tr.Said < 16 && n >= 2)
        {
            tr.Said++;
            var s1 = gripRing[^1]; var s0 = gripRing[^2];
            var d = s1.Tip - PlayerPos;
            GD.Print($"grip frame {Engine.GetFramesDrawn()} age {age * 60:0.0}f cut {cut:0.00} samples {n - i0} fast {hi - i0} tip az {Mathf.RadToDeg(Mathf.Atan2(d.Z, d.X)):0} r {new Vector2(d.X, d.Z).Length():0.00} y {d.Y:0.00} speed {s1.Tip.DistanceTo(s0.Tip) / Math.Max(1e-4, s1.At - s0.At):0.0} m/s step {(s1.At - s0.At) * 1000:0.0} ms linked {tr.Linked} px/m {1 / P7Px(PlayerPos):0}");
        }
        gripPts.Clear(); gripCum.Clear(); gripAtT.Clear();
        if (!any) { gripNode.Visible = false; return; }
        for (int k = i0; k < n - 1; k++)
        {
            var a = gripRing[k]; var b = gripRing[k + 1];
            var pa = gripRing[Math.Max(k - 1, i0)]; var pb = gripRing[Math.Min(k + 2, n - 1)];
            Vector3 da = a.Tip - a.Hilt, db = b.Tip - b.Hilt, dpa = pa.Tip - pa.Hilt, dpb = pb.Tip - pb.Hilt;
            float la = da.Length(), lb = db.Length();
            da /= la; db /= lb; dpa = dpa.Normalized(); dpb = dpb.Normalized();
            int sub = Mathf.Clamp(Mathf.CeilToInt(Mathf.RadToDeg(da.AngleTo(db)) / 4f), 1, 20);
            for (int q = 0; q < sub; q++)
            {
                float t = q / (float)sub;
                var h = a.Hilt.CubicInterpolate(b.Hilt, pa.Hilt, pb.Hilt, t);
                var dir = da.CubicInterpolate(db, dpa, dpb, t).Normalized();
                gripPts.Add((h, h + dir * Mathf.Lerp(la, lb, t)));
                gripAtT.Add(a.At + (b.At - a.At) * t);
            }
        }
        var last = gripRing[n - 1];
        gripPts.Add((last.Hilt, last.Tip));
        gripAtT.Add(last.At);
        int linkN = tr.Linked ? GripThread(tr) : 0;
        for (int i = 0; i < linkN; i++) gripAtT.Insert(0, gripAtT[0]);
        float cum = 0;
        gripCum.Add(0);
        for (int i = 1; i < gripPts.Count; i++) { cum += gripPts[i].T.DistanceTo(gripPts[i - 1].T); gripCum.Add(cum); }
        float thread = gripCum[linkN];
        // (take 7) THE LAYING: what the blade has passed since the last drawn frame is laid now, each rib with its own press
        // (GripPaint: the brush lands, is whole, lifts as the blade slows) and whiteness. The contact presses the ribs
        // round the crossing ONCE, where they lie. Nothing laid is ever moved or pressed again: it only ages.
        var faceCam = GetViewport()?.GetCamera3D();
        int frame = Engine.GetFramesDrawn(), laid0 = tr.Laid.Count;
        var press = GripPress;
        float pxm = P7Px(PlayerPos);
        for (int i = linkN; i < gripPts.Count; i++)
        {
            double at = gripAtT[i];
            if (tr.Laid.Count > 0 && at <= tr.Laid[^1].At + 1e-7) continue;
            float ds = 0, dq = 0;
            if (i > linkN && tr.Laid.Count > 0)
            {
                ds = gripPts[i].T.DistanceTo(gripPts[i - 1].T);
                dq = faceCam != null ? faceCam.UnprojectPosition(gripPts[i].T).DistanceTo(faceCam.UnprojectPosition(gripPts[i - 1].T)) * pxm : ds;
            }
            // the tip's speed here: this frame's, run in from the frame before's (no step in the press at a frame's joint)
            int k1 = n - 1;
            while (k1 > 1 && gripRing[k1 - 1].At >= at) k1--;
            double dt1 = Math.Max(1e-4, gripRing[k1].At - gripRing[k1 - 1].At);
            float v1 = (float)(gripRing[k1].Tip.DistanceTo(gripRing[k1 - 1].Tip) / dt1), v0 = v1;
            if (k1 > i0 + 1) v0 = (float)(gripRing[k1 - 1].Tip.DistanceTo(gripRing[k1 - 2].Tip) / Math.Max(1e-4, gripRing[k1 - 1].At - gripRing[k1 - 2].At));
            GripPaint.Lay(tr.Laid, at, ds, dq, Mathf.Lerp(v0, v1, Mathf.Clamp((float)((at - gripRing[k1 - 1].At) / dt1), 0, 1)), frame, press, tr.Stamp);
        }
        if (tr.BiteAt >= 0 && tr.Stamp.Size <= 0 && tr.Laid.Count > 0)
        {
            tr.Stamp = GripPaint.Strike(tr.Laid, GripPaint.At(tr.Laid, tr.BiteAt, frame, P7D.All("grip.press.hold")).S, tr.Bite, frame, press);
            var hd = last.Tip - PlayerPos;
            tr.StampR = new Vector2(hd.X, hd.Z).Length();
        }
        // the drawn length: capped, and run up toward the head as it leaves
        float len = Mathf.Min(cum, look.MaxLen), start = cum - len;
        if (len < P7D["grip.min_len"]) { gripNode.Visible = false; return; }
        if (len > tr.FullLen) { tr.FullLen = len; tr.FullFrame = Engine.GetFramesDrawn(); }
        // (take 5) A cut whose blade sweeps a plane the camera sees edge-on (sword_fore's) left a sliver. Where the blade's
        // line shows less than grip.face[1] of itself across the path on screen, the ribbon is turned toward the camera
        // (wholly under face[0]), head and all, always to ONE side for the whole stroke (no twist); each vertex carries how
        // much it is still the blade's own sweep (COLOR.r: the lit blade is drawn only there, so it never leaves the sword).
        var faceBack = faceCam != null ? faceCam.GlobalBasis.Z.Normalized() : Vector3.Up;
        var face = P7D.All("grip.face");
        // (round 4) laid, and if the tip's path kinks on screen laid again from nearer the kink: the part before it (swept
        // edge-on, turned to the camera: an L with the part after it) runs out toward the kink over grip.kink.run's drawn
        // frames, but only once the part AFTER the kink is grip.kink[2] m long on screen (a stroke of its own: it must not
        // blink; until then the kink is only held inside its turn, a clean mitre)
        float bladeNow = last.Tip.DistanceTo(last.Hilt);
        var kk = P7D.All("grip.kink"); var krun = P7D.All("grip.kink_run");
        float seen = len, way = 0, shown = 0, kinkAt = -1;
        for (int pass = 0; pass < 2; pass++)
        {
            float k = GripLay(tr, look, start, len, faceCam, faceBack, face, kk, out seen, out way, out shown, out float after);
            if (pass == 0) kinkAt = k;
            if (pass == 1 || k < 0 || after < kk[2]) break;
            if (tr.KinkFrame < 0) tr.KinkFrame = Engine.GetFramesDrawn();
            float run = krun[Math.Min(Engine.GetFramesDrawn() - tr.KinkFrame, krun.Length - 1)];
            float to = Mathf.Min(Mathf.Lerp(start, k, run), cum - 2 * P7D["grip.min_len"]);
            if (to <= start + 1e-3f) break;
            start = to; len = cum - start;
        }
        // (take 7, v) no stroke is held back for being short: it is born on its first drawn frame as the cap and a point
        if (gripRibs.Count < 2) { gripNode.Visible = false; return; }
        if (tr.Seed == 0) tr.Seed = 1f + R() * 96f;
        // (iv) the splay's tines and the thrown streaks: rooted round the stamp, counted by the cut's distinct struck,
        // the streaks out to the cut's reach, both shed by drawn frame
        float[]? spikes = null;
        int tines = 0, streaks = 0;
        float sheet0 = 1, sheet1 = 0, far = 0;
        if (tr.Stamp.Size > 0)
        {
            int since = frame - tr.Stamp.Frame;
            var sf = P7D.All("grip.splay.frames"); var tf = P7D.All("grip.throw.frames");
            float ks = since < sf.Length ? sf[since] : 0, kt = since < tf.Length ? tf[since] : 0;
            if (ks > 0) tines = GripPaint.Tines(tr.Struck, P7D.All("grip.splay.tines"), P7D.All("grip.contact.by_struck")[0]);
            if (kt > 0) streaks = GripPaint.Streaks(tr.Struck, P7D["grip.throw.per_struck"], P7D["grip.throw.most"]);
            far = Mathf.Max(P7D["grip.throw.min"], tr.Reach - tr.StampR);
            spikes = GripPaint.Spikes(tr.Stamp, tines, streaks, press, P7D.All("grip.splay.len"), P7D.All("grip.splay.root"), P7D.All("grip.splay.slant"),
                P7D["grip.throw.px"], P7D.All("grip.throw.len"), P7D.All("grip.throw.slant"), far, tr.Seed, ks, kt, P7D["grip.throw.span"]);
            for (int i = tines; i < tines + streaks; i++)
            {
                float u0 = spikes[i * 4], u1 = u0 + spikes[i * 4 + 3] * spikes[i * 4 + 2];
                if (sheet1 < sheet0) { sheet0 = Mathf.Min(u0, u1); sheet1 = Mathf.Max(u0, u1); }
                sheet0 = Mathf.Min(sheet0, Mathf.Min(u0, u1)); sheet1 = Mathf.Max(sheet1, Mathf.Max(u0, u1));
            }
            float pad = 0.2f + 1.6f * P7D["grip.throw.bend"] * far;   // (a streak's lean may run against the travel, and it bends)
            sheet0 -= pad; sheet1 += pad;
        }
        // (i) the cap: one more rib, the head's own carried straight on along the path's tangent (the shader cuts the nose)
        var hr = gripRibs[^1];
        var tan = tr.EndTan;
        for (int i = gripRibs.Count - 2; i >= 0; i--)
            if (gripRibs[i].T.DistanceSquaredTo(hr.T) > 0.0064f) { tan = (hr.T - gripRibs[i].T).Normalized(); break; }
        float ext = P7D.All("grip.cap")[0] * look.Head * hr.Press * bladeNow + P7D.All("grip.cap_rag")[1] + 0.06f;
        var cr = hr;
        cr.H += tan * ext; cr.T += tan * ext; cr.U += ext; cr.M += ext;
        gripRibs.Add(cr);
        // ONE mesh: the ribbon (guard side to the margin past the tip's path) and, along the pressed section, the
        // throw's sheet on from the margin, out from her to the cut's reach
        float raiseMost = Mathf.Max(press.Contact[0] * P7D.All("grip.contact.by_struck")[1], 1e-3f), farV = far / Mathf.Max(bladeNow, 0.05f);
        var her = PlayerPos;
        void Put(in GripRibV r, Vector3 p, float v)
        {
            gripMesh.SurfaceSetColor(new Color(Mathf.Clamp(r.White / 2.5f, 0, 1), Mathf.Clamp(r.Raise / raiseMost, 0, 1), 0));
            gripMesh.SurfaceSetUV(new Vector2(r.U, v)); gripMesh.SurfaceSetUV2(new Vector2(r.Cap, r.Press)); gripMesh.SurfaceAddVertex(p);
        }
        Vector3 Thrown(Vector3 m)
        {
            var d = new Vector3(m.X - her.X, 0, m.Z - her.Z);
            var o = m + (d.LengthSquared() > 1e-6f ? d.Normalized() : Vector3.Right) * far;
            o.Y = Mathf.Max(o.Y, her.Y + 0.8f);
            return o;
        }
        gripMesh.ClearSurfaces();
        gripMesh.SurfaceBegin(Mesh.PrimitiveType.Triangles);
        float peak = 0, peakU = 0;
        for (int i = 0; i + 1 < gripRibs.Count; i++)
        {
            var a = gripRibs[i]; var b = gripRibs[i + 1];
            if (a.Press > peak) { peak = a.Press; peakU = a.U; }
            Vector3 am = a.T + (a.T - a.H) * GripOver, bm = b.T + (b.T - b.H) * GripOver;
            Put(a, a.H, 0); Put(a, am, 1 + GripOver); Put(b, b.H, 0);
            Put(b, b.H, 0); Put(a, am, 1 + GripOver); Put(b, bm, 1 + GripOver);
            if (streaks == 0 || a.U < sheet0 || b.U > sheet1) continue;
            Vector3 ao = Thrown(am), bo = Thrown(bm);
            Put(a, am, 1 + GripOver); Put(a, ao, 1 + GripOver + farV); Put(b, bm, 1 + GripOver);
            Put(b, bm, 1 + GripOver); Put(a, ao, 1 + GripOver + farV); Put(b, bo, 1 + GripOver + farV);
        }
        gripMesh.SurfaceEnd();
        GripSet(look, hr.U, gripRibs[0].U, bladeNow, (float)age, tr.Seed, PlayerPos, spikes, tines, tr.Stamp.Size > 0 ? frame - tr.Stamp.Frame : -1);
        if (GripSayAll && tr.Said <= 16 && faceCam != null)
        {
        // (--grip-say) the ribbon as the camera sees it: the samples' tips on screen (px), the turn's side, the bite
            var said = new System.Text.StringBuilder();
            for (int k = i0; k < n; k++) { var p = faceCam.UnprojectPosition(gripRing[k].Tip); said.Append($" {p.X:0},{p.Y:0}"); }
            var hp = faceCam.UnprojectPosition(last.Hilt);
            GD.Print($"grip ribbon frame {Engine.GetFramesDrawn()} len {len:0.00} cum {cum:0.00} seen {seen:0.00} way {way:0} shown {shown:0.00} kink {(kinkAt < 0 ? -1 : kinkAt - (cum - len)):0.00} laid {tr.Laid.Count} (+{tr.Laid.Count - laid0}) press {peak:0.00} at {peakU - gripRibs[0].U:0.00} of {hr.U - gripRibs[0].U:0.00} tines {tines} streaks {streaks} far {far:0.00} hilt {hp.X:0},{hp.Y:0} tips{said}");
        }
        gripNode.Visible = true;
    }

    /// <summary>A linked cut's thread, put before the sail's points: from where the last cut ended (its tip then, from her
    /// now), on along the way it was travelling, round a turn hook and into this cut's first fast sample along its own
    /// travel. Its ribbon faces the camera and turns into the blade's own plane as it arrives. Returns the points added
    /// (0: the two cuts are too far apart to join; the start is a plain point).</summary>
    int GripThread(GripTrail tr)
    {
        var (h1, p1) = gripPts[0];
        var p0 = PlayerPos + tr.LinkTip;
        float gap = p0.DistanceTo(p1);
        if (gap > P7D["grip.link.max_gap"] || gripPts.Count < 2) return 0;
        var t1 = gripPts[Math.Min(3, gripPts.Count - 1)].T - p1;
        if (t1.LengthSquared() < 1e-6f) return 0;
        t1 = t1.Normalized();
        var t0 = tr.LinkTan.LengthSquared() > 1e-6f ? tr.LinkTan.Normalized() : -t1;
        var cam = GetViewport()?.GetCamera3D();
        var back = cam != null ? cam.GlobalBasis.Z.Normalized() : Vector3.Up;
        // the hook: past the end by `hook` (a cubic's overshoot is 4/27 of its tangent), and when the two points meet
        // (a cut that turns straight back on itself) a loop `hook_w` wide, out on the far side from her and back on the near
        float m = P7D["grip.link.hook"] * 27f / 4f, w = P7D["grip.link.hook_w"] * Mathf.Clamp(1 - gap / 0.8f, 0, 1);
        var lat = back.Cross(t0);
        lat = lat.LengthSquared() > 1e-6f ? lat.Normalized() : Vector3.Up;
        if (lat.Dot(p0 - (PlayerPos + Vector3.Up * 1.1f)) < 0) lat = -lat;
        Vector3 At(float t)
        {
            float t2 = t * t, t3 = t2 * t;
            return p0 * (2 * t3 - 3 * t2 + 1) + t0 * (m * (t3 - 2 * t2 + t)) + p1 * (-2 * t3 + 3 * t2) + t1 * (m * (t3 - t2)) + lat * (w * Mathf.Sin(Mathf.Tau * t));
        }
        var hb = h1 - p1;
        float blade = hb.Length();
        hb /= Mathf.Max(blade, 1e-4f);
        int count = Math.Max(4, (int)P7D["grip.link.points"]);
        // the ribbon's inward side, turning with the thread (never flipped along it), the way round that meets the blade
        var vEnd = back.Cross(At(1f) - At(0.98f));
        float sign = vEnd.Dot(hb) < 0 ? -1 : 1;
        var pts = new (Vector3 H, Vector3 T)[count];
        for (int i = 0; i < count; i++)
        {
            float t = i / (float)count;
            var p = At(t);
            var v = back.Cross(At(t + 0.02f) - p) * sign;
            v = v.LengthSquared() > 1e-8f ? v.Normalized() : hb;
            float k = Mathf.SmoothStep(0.65f, 1f, t);
            v = v.Lerp(hb, k);
            v = v.LengthSquared() > 1e-6f ? v.Normalized() : hb;
            pts[i] = (p + v * blade, p);
        }
        gripPts.InsertRange(0, pts);
        return count;
    }

    /// <summary>The contact, ON the blade: the pose at which the blade's line crosses the struck body (among the cut's
    /// samples: it may have crossed already, or cross within the wait). (Round 3) No second object: the crossing's time
    /// is the stroke's BITE (GripDraw: the ribbon swells and whitens there, larger for a crowd or a kill, for
    /// grip.contact.frames frames). The wait up and no crossing: on the blade as it is.</summary>
    void GripContact(GripTrail tr, GripLook look, int i0)
    {
        int n = gripRing.Count;
        if (n < 2) { tr.FlashOwed = false; return; }
        var body = tr.Body;
        Vector3 hilt = default, tip = default;
        double when = gripRing[^1].At;
        bool found = false;
        int waited = tr.FlashTries;
        for (int k = Math.Max(1, i0 + 1); k < n && !found; k++)
        {
            var a = gripRing[k - 1]; var b = gripRing[k];
            Vector2 da = new(a.Tip.X - a.Hilt.X, a.Tip.Z - a.Hilt.Z), db = new(b.Tip.X - b.Hilt.X, b.Tip.Z - b.Hilt.Z);
            Vector2 ba = new(body.X - a.Hilt.X, body.Z - a.Hilt.Z), bb = new(body.X - b.Hilt.X, body.Z - b.Hilt.Z);
            float sa = da.Cross(ba), sb = db.Cross(bb);
            if (sa * sb > 0 || (da.Dot(ba) <= 0 && db.Dot(bb) <= 0)) continue;
            float t = Mathf.Abs(sa) / Mathf.Max(1e-6f, Mathf.Abs(sa) + Mathf.Abs(sb));
            hilt = a.Hilt.Lerp(b.Hilt, t); tip = a.Tip.Lerp(b.Tip, t); when = a.At + (b.At - a.At) * t;
            found = true;
        }
        if (!found)
        {
            if (++tr.FlashTries <= (int)P7D["grip.contact.wait_frames"]) return;
            var s1 = gripRing[^1];
            hilt = s1.Hilt; tip = s1.Tip;
        }
        tr.FlashOwed = false;
        Vector2 d2 = new(tip.X - hilt.X, tip.Z - hilt.Z), bd = new(body.X - hilt.X, body.Z - hilt.Z);
        float kb = Mathf.Clamp(bd.Dot(d2) / Mathf.Max(1e-4f, d2.LengthSquared()), P7D["grip.contact.k_min"], 1f);
        var at = hilt + (tip - hilt) * kb;
        // (take 6) ONE shared impact, sized by the bodies struck (a kill larger still), capped; no chips, no mark
        var by = P7D.All("grip.contact.by_struck");
        float size = look.Flash * Mathf.Min(by[1], Mathf.Lerp(1f, by[1], Mathf.Clamp((tr.Struck - 1) / Mathf.Max(by[0] - 1, 1f), 0f, 1f)) * (tr.Killed > 0 ? P7D["grip.contact.kill"] : 1f));
        if (GripSay) GD.Print($"grip contact frame {Engine.GetFramesDrawn()} struck {tr.Struck} killed {tr.Killed} oath {tr.Oath} size {size:0.00} on blade {kb:0.00} crossed {(found ? 1 : 0)} waited {waited} at {at}");
        tr.BiteAt = when; tr.Bite = size;
    }

    /// <summary>The hot edge, the ribbon at rest: while the chain lives, a core line on the real blade and a glint at its
    /// tip; the chain broken, it steps out gold, then amber, and is gone.</summary>
    void GripEdgeDraw()
    {
        if (gripChain is not { } ch || gripEdgeMesh == null || gripEdgeNode == null || !IsInstanceValid(gripEdgeNode)) return;
        gripEdgeDrawn = Engine.GetProcessFrames();
        int step = 0;
        if (ch.Out >= 0)
        {
            step = 1 + (int)((gripClock - ch.Out) * 60 / Math.Max(1, P7D["grip.edge.out_frames"]) + 0.05);
            if (step > 2) { gripChain = null; gripEdgeNode.Visible = false; return; }
        }
        if (P7D["grip.link.on"] < 0.5f || GripBladeNow() is not { } now) { gripEdgeNode.Visible = false; return; }
        GripEdgeQuads(now.Hilt, now.Tip, step);
    }

    void GripEdgeQuads(Vector3 hilt, Vector3 tip, int step)
    {
        var cam = GetViewport()?.GetCamera3D();
        var back = cam != null ? cam.GlobalBasis.Z.Normalized() : Vector3.Up;
        var dir = tip - hilt;
        var side = back.Cross(dir);
        if (side.LengthSquared() < 1e-8f) { gripEdgeNode!.Visible = false; return; }
        side = side.Normalized();
        var along = dir.Normalized();
        float px = P7Px(tip), w = P7D["grip.edge.px"], hpx = w * 0.5f + 2f;
        var gl = P7D.All("grip.edge.glint_px");
        var lift = back * P7D["grip.edge.lift"];
        Vector3 a = hilt + lift, b = tip + lift, o = side * (hpx * px);
        var mesh = gripEdgeMesh!;
        mesh.ClearSurfaces();
        mesh.SurfaceBegin(Mesh.PrimitiveType.Triangles);
        void Quad(Vector3 p00, Vector3 p10, Vector3 p01, Vector3 p11, Vector2 u00, Vector2 u11, float kind)
        {
            var c = new Color(kind, 0, 0);
            mesh.SurfaceSetColor(c); mesh.SurfaceSetUV(u00); mesh.SurfaceAddVertex(p00);
            mesh.SurfaceSetColor(c); mesh.SurfaceSetUV(new Vector2(u11.X, u00.Y)); mesh.SurfaceAddVertex(p10);
            mesh.SurfaceSetColor(c); mesh.SurfaceSetUV(u11); mesh.SurfaceAddVertex(p11);
            mesh.SurfaceSetColor(c); mesh.SurfaceSetUV(u00); mesh.SurfaceAddVertex(p00);
            mesh.SurfaceSetColor(c); mesh.SurfaceSetUV(u11); mesh.SurfaceAddVertex(p11);
            mesh.SurfaceSetColor(c); mesh.SurfaceSetUV(new Vector2(u00.X, u11.Y)); mesh.SurfaceAddVertex(p01);
        }
        Quad(a - o, b - o, a + o, b + o, new Vector2(0, -hpx), new Vector2(1, hpx), 0);
        Vector3 gx = along * (gl[0] * px), gy = side * (gl[1] * px);
        Quad(b - gx - gy, b + gx - gy, b - gx + gy, b + gx + gy, new Vector2(-1, -1), new Vector2(1, 1), 1);
        mesh.SurfaceEnd();
        var m = gripEdgeMat!;
        m.SetShaderParameter("grip_size", new Vector2(w, 0));
        m.SetShaderParameter("grip_thin", (float)step);
        gripEdgeNode!.CustomAabb = new Aabb(tip - new Vector3(3, 3, 3), new Vector3(6, 6, 6));
        gripEdgeNode.Visible = true;
    }
}
