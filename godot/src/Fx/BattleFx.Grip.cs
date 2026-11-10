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
    /// <summary>The margin drawn past the tip (a share of the blade: the glow, the edge's antialiasing).</summary>
    const float GripOver = 0.12f;

    /// <summary>The look by weapon (fx_language.json p7 grip.sunder / grip.oath): the comma's width at the blade (a share
    /// of it), the power its inner edge runs out by, the longest drawn (m of the tip's path), the bands' ends across
    /// the width by step of leaving, how far back the core and the mid reach, the width by step of leaving, the
    /// contact's size.</summary>
    /// <remarks>(take 6) Knots = the three bands' ends (core, mid, end) as one line each across the width: 4 knots of
    /// [across, share of the length] per band (a shorter list's last knot repeated); Streaks = the tail's lanes,
    /// [width share, share of the tail kept] each.</remarks>
    readonly record struct GripLook(float Head, float P, float MaxLen, float[] Knots, float[] Streaks, float Taper, float Flash);
    static GripLook? gripSunder, gripOath;

    static GripLook GripLookOf(bool oath)
    {
        if ((oath ? gripOath : gripSunder) is { } l) return l;
        string k = oath ? "grip.oath." : "grip.sunder.";
        var knots = new float[24];
        string[] bands = { "core", "mid", "end" };
        for (int b = 0; b < 3; b++)
        {
            var src = P7D.All(k + bands[b]);
            int last = Math.Max(0, src.Length / 2 - 1);
            for (int j = 0; j < 4 && src.Length >= 2; j++)
            {
                int s = Math.Min(j, last) * 2;
                knots[b * 8 + j * 2] = src[s];
                knots[b * 8 + j * 2 + 1] = src[s + 1];
            }
        }
        var n = new GripLook(P7D[k + "head"], P7D[k + "p"], P7D[k + "max_len"], knots, P7D.All(k + "streaks"), P7D[k + "taper"], P7D[k + "flash"]);
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
        /// <summary>The contact's slit, owed until the blade's line has crossed the struck body (or the wait is up).</summary>
        public bool FlashOwed;
        public int FlashTries, Struck, Killed;
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
        if (gripLive is not { Contact: < 0 } tr) { tr = new GripTrail { Oath = oath, Tail = gripClock - 5 / 60.0 }; GripArm(tr); }
        tr.Oath = oath; tr.Contact = gripClock; tr.SimSide = e.Side;
        if (e.Struck > 0)
        {
            tr.FlashOwed = true; tr.Struck = e.Struck; tr.Killed = e.Killed;
            tr.Body = V(e.HitX, Y(e.HitX, e.HitZ) + 1.0, e.HitZ);
            Cam?.AddTrauma(oath ? 0.02f : 0.04f);
        }
        float r = Mathf.Clamp(reach * 0.62f, 1.7f, 2.1f), mid = (float)e.Angle;
        double tx = e.X + Mathf.Cos(mid) * r * 0.9f, tz = e.Z + Mathf.Sin(mid) * r * 0.9f;
        if (!oath)
        {
            // The heavy blade's grit where it passes nearest the ground (grip.contact.grit puffs: 0 now, by day they
            // read as dark blobs on the stroke).
            if ((int)P7D["grip.contact.grit"] is > 0 and var grit) Dust(tx, tz, grit, 1.6f * g);
            Cam?.AddTrauma(0.02f);
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
        // the brush as the stroke takes it: the across and the along are the stroke's own (the comma's shape is the
        // shader's), the bristles laid by the shader in pixels and metres, the boundaries' waver small (the across
        // magnifies it in the white)
        gripMat.SetShaderParameter("fx_stroke_shape", new Vector4(1f, 0.3f, 1f, 0f));
        gripMat.SetShaderParameter("fx_bristle", new Vector4(24f, 12f, P7D.All("grip.dry")[4], P7D["grip.waver"]));
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

    /// <summary>The first use's compiles paid when she takes the blade, not on her first cut: the trail, the hot edge
    /// and the contact drawn for three frames, a few centimetres across, under her feet.</summary>
    void GripWarm()
    {
        if (gripLive != null || gripChain != null || gripMesh == null || gripNode == null || gripMat == null || gripEdgeMesh == null || gripEdgeNode == null) { gripWarm = 0; return; }
        gripWarm--;
        var o = PlayerPos + Vector3.Down * 0.3f;
        gripMesh.ClearSurfaces(); gripEdgeMesh.ClearSurfaces();
        if (gripWarm <= 0) { gripNode.Visible = false; gripEdgeNode.Visible = false; return; }
        gripMesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = 0; i < 2; i++)
        {
            gripMesh.SurfaceSetUV(new Vector2(i * 0.02f, 0)); gripMesh.SurfaceAddVertex(o + new Vector3(i * 0.02f, 0, 0));
            gripMesh.SurfaceSetUV(new Vector2(i * 0.02f, 1)); gripMesh.SurfaceAddVertex(o + new Vector3(i * 0.02f, 0, 0.02f));
        }
        gripMesh.SurfaceEnd();
        GripSet(GripLookOf(false), 0.02f, 0, 0, 0.02f, 0, o);
        gripNode.Visible = true;
        GripEdgeQuads(o, o + new Vector3(0.02f, 0, 0), 0);
        if (gripWarm == 2) GripFlash(o, Vector3.Right, Vector3.Forward, 0.02f, 1, false);
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

    void GripSet(GripLook look, float total, float thread, float blade, float age, float seed, Vector3 her)
    {
        var m = gripMat!;
        float px = P7Px(her);
        blade = Mathf.Max(blade, 0.05f);
        var lit = P7D.All("grip.lit");
        var pt = P7D.All("grip.point");
        var jit = P7D.All("grip.lane.jitter");
        var fp = P7D.All("grip.lane.point");
        var gap = P7D.All("grip.lane.gap");
        var ge = P7D.All("grip.glow_end");
        var shed = P7D.All("grip.shed_at");
        // a short stroke is the comma small, a wedge: its head no wider than `aspect` of its own length
        float body = Mathf.Max(total - thread, 0.01f);
        float head = Mathf.Min(look.Head, body * P7D["grip.aspect"] / blade);
        float tail = Mathf.Min(P7D["grip.tail_px"] * px / blade, head * 0.25f);
        // the lit blade: from the comma's head down toward the guard as the stroke grows
        float full = Mathf.Clamp((body - lit[1]) / Mathf.Max(lit[2] - lit[1], 1e-3f), 0, 1);
        // (take 6) the bands: one ragged line each across the width; lanes only in the tail (its streaks)
        var lanes = new float[16];
        Array.Copy(look.Streaks, lanes, Math.Min(16, look.Streaks.Length));
        m.SetShaderParameter("grip_knot", look.Knots);
        m.SetShaderParameter("grip_lanes", lanes);
        m.SetShaderParameter("grip_lane_n", Math.Min(8, look.Streaks.Length / 2));
        m.SetShaderParameter("grip_lane", new Vector4(jit[0], jit[1], look.Taper, look.P));
        var tl = P7D.All("grip.lane.tail");
        m.SetShaderParameter("grip_tips", new Vector4(tl[0], fp[0], fp[1], P7D["grip.lane.slant"]));
        m.SetShaderParameter("grip_tail", tl[1]);
        var cl = P7D.All("grip.band.clumps");
        var td = P7D.All("grip.band.depth");
        m.SetShaderParameter("grip_clump", new Vector4(cl[0], cl[1], P7D["grip.band.uneven"], P7D["grip.band.ratio"]));
        m.SetShaderParameter("grip_tooth", new Vector4(td[0], td[1], P7D["grip.band.round"], 0));
        m.SetShaderParameter("grip_narrow", P7D["grip.shed_to"]);
        m.SetShaderParameter("grip_gap", new Vector4(gap[0], gap[1], gap[2], gap[3]));
        m.SetShaderParameter("grip_shed", new Vector4(age, shed[0], shed[1], P7D["grip.lane.shed"]));
        m.SetShaderParameter("grip_seed", seed);
        m.SetShaderParameter("grip_total", total);
        m.SetShaderParameter("grip_thread", thread);
        m.SetShaderParameter("grip_blade", blade);
        m.SetShaderParameter("grip_shape", new Vector3(tail, head, look.P));
        m.SetShaderParameter("grip_dry", new Vector3(ge[0], 0, ge[1]));
        m.SetShaderParameter("grip_lit", new Vector2(lit[0] * px, full));
        m.SetShaderParameter("grip_glow", P7D["grip.glow"]);
        m.SetShaderParameter("grip_point", Mathf.Min(pt[0], total * pt[1]));
        m.SetShaderParameter("grip_px", px);
        gripNode!.CustomAabb = new Aabb(her - new Vector3(5, 3, 5), new Vector3(10, 7, 10));
    }

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
        gripPts.Clear(); gripCum.Clear();
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
            }
        }
        var last = gripRing[n - 1];
        gripPts.Add((last.Hilt, last.Tip));
        int linkN = tr.Linked ? GripThread(tr) : 0;
        float cum = 0;
        gripCum.Add(0);
        for (int i = 1; i < gripPts.Count; i++) { cum += gripPts[i].T.DistanceTo(gripPts[i - 1].T); gripCum.Add(cum); }
        float thread = gripCum[linkN];
        // the drawn length: capped, and run up toward the head as it leaves
        float len = Mathf.Min(cum, look.MaxLen), start = cum - len;
        if (len < P7D["grip.min_len"]) { gripNode.Visible = false; return; }
        if (len > tr.FullLen) { tr.FullLen = len; tr.FullFrame = Engine.GetFramesDrawn(); }
        int s = 0;
        while (s < gripPts.Count - 2 && gripCum[s + 1] <= start) s++;
        // (take 5) A cut whose blade sweeps a plane the camera sees edge-on (sword_fore's) left a sliver. Where the blade's
        // line shows less than grip.face[1] of itself across the path on screen, the ribbon is turned toward the camera
        // (wholly under face[0]), head and all, always to ONE side for the whole stroke (no twist); each vertex carries how
        // much it is still the blade's own sweep (COLOR.r: the lit blade is drawn only there, so it never leaves the sword).
        var faceCam = GetViewport()?.GetCamera3D();
        var faceBack = faceCam != null ? faceCam.GlobalBasis.Z.Normalized() : Vector3.Up;
        var face = P7D.All("grip.face");
        float shownSum = 0, realSum = 0;
        for (int i = s; i < gripPts.Count; i++)
        {
            var sd = faceBack.Cross(gripPts[Math.Min(i + 1, gripPts.Count - 1)].T - gripPts[Math.Max(i - 1, 0)].T);
            if (sd.LengthSquared() < 1e-8f) continue;
            var rl = gripPts[i].H - gripPts[i].T;
            shownSum += rl.Dot(sd.Normalized()); realSum += rl.Length();
        }
        float way = Mathf.Abs(shownSum) > 0.15f * realSum ? Mathf.Sign(shownSum) : 0;
        if (way == 0)
        {
            var sd = faceBack.Cross(gripPts[^1].T - gripPts[^2].T);
            way = sd.Dot(PlayerPos + Vector3.Up * 1.1f - gripPts[^1].T) < 0 ? -1 : 1;
        }
        Vector3 hA = default, tA = default, hB = default, tB = default;
        float realB = 1;
        gripMesh.ClearSurfaces();
        gripMesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = s; i < gripPts.Count; i++)
        {
            var (h, t) = gripPts[i];
            float u = gripCum[i] - start;
            if (i == s && u < 0)
            {
                // the drawn tail's own point, between two of the path's
                float f = -u / Mathf.Max(1e-5f, gripCum[i + 1] - gripCum[i]);
                h = h.Lerp(gripPts[i + 1].H, f); t = t.Lerp(gripPts[i + 1].T, f); u = 0;
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
            gripMesh.SurfaceSetColor(new Color(real, 0, 0)); gripMesh.SurfaceSetUV(new Vector2(u, 0)); gripMesh.SurfaceAddVertex(h);
            gripMesh.SurfaceSetColor(new Color(real, 0, 0)); gripMesh.SurfaceSetUV(new Vector2(u, 1 + GripOver)); gripMesh.SurfaceAddVertex(t + (t - h) * GripOver);
            (hA, tA, hB, tB, realB) = (hB, tB, h, t, real);
        }
        // a few centimetres past the head, for the head's own edge
        {
            float f = 0.05f / Mathf.Max(0.005f, tB.DistanceTo(tA));
            Vector3 h = hB + (hB - hA) * f, t = tB + (tB - tA) * f;
            gripMesh.SurfaceSetColor(new Color(realB, 0, 0)); gripMesh.SurfaceSetUV(new Vector2(len + 0.05f, 0)); gripMesh.SurfaceAddVertex(h);
            gripMesh.SurfaceSetColor(new Color(realB, 0, 0)); gripMesh.SurfaceSetUV(new Vector2(len + 0.05f, 1 + GripOver)); gripMesh.SurfaceAddVertex(t + (t - h) * GripOver);
        }
        gripMesh.SurfaceEnd();
        // the stroke keeps its length while it leaves: the shader sheds it lane by lane (grip.shed_at, grip.lane.shed)
        if (tr.Seed == 0) tr.Seed = 1f + R() * 96f;
        GripSet(look, len, Mathf.Max(0, thread - start), last.Tip.DistanceTo(last.Hilt), (float)age, tr.Seed, PlayerPos);
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
    /// samples: it may have crossed already, or cross within the wait), the blade's point nearest the body, a
    /// cut-through laid along the tip's travel there, larger for a kill or a crowd. The wait up and no crossing: on the
    /// blade as it is.</summary>
    void GripContact(GripTrail tr, GripLook look, int i0)
    {
        int n = gripRing.Count;
        if (n < 2) { tr.FlashOwed = false; return; }
        var body = tr.Body;
        Vector3 hilt = default, tip = default, travel = default;
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
            hilt = a.Hilt.Lerp(b.Hilt, t); tip = a.Tip.Lerp(b.Tip, t); travel = b.Tip - a.Tip;
            found = true;
        }
        if (!found)
        {
            if (++tr.FlashTries <= (int)P7D["grip.contact.wait_frames"]) return;
            var s1 = gripRing[^1]; var s0 = gripRing[^2];
            hilt = s1.Hilt; tip = s1.Tip; travel = s1.Tip - s0.Tip;
        }
        tr.FlashOwed = false;
        if (travel.LengthSquared() < 1e-6f) travel = tr.EndTan;
        Vector2 d2 = new(tip.X - hilt.X, tip.Z - hilt.Z), bd = new(body.X - hilt.X, body.Z - hilt.Z);
        float kb = Mathf.Clamp(bd.Dot(d2) / Mathf.Max(1e-4f, d2.LengthSquared()), P7D["grip.contact.k_min"], 1f);
        var at = hilt + (tip - hilt) * kb;
        // (take 6) ONE shared impact, sized by the bodies struck (a kill larger still), capped; no chips
        var by = P7D.All("grip.contact.by_struck");
        float size = look.Flash * Mathf.Min(by[1], Mathf.Lerp(1f, by[1], Mathf.Clamp((tr.Struck - 1) / Mathf.Max(by[0] - 1, 1f), 0f, 1f)) * (tr.Killed > 0 ? P7D["grip.contact.kill"] : 1f));
        int sparks = 0;
        if (GripSay) GD.Print($"grip contact frame {Engine.GetFramesDrawn()} struck {tr.Struck} killed {tr.Killed} oath {tr.Oath} size {size:0.00} on blade {kb:0.00} crossed {(found ? 1 : 0)} waited {waited} at {at}");
        GripFlash(at, travel.Normalized(), hilt - tip, size, sparks, tr.Oath);
    }

    /// <summary>The contact's picture: a quad facing the camera, its long axis the blade's travel as the camera sees it,
    /// drawn in the trail's shader (its second mode): the cut-through and its kernel for three frames (two whole, one
    /// thin), the tears flying on for a few more.</summary>
    void GripFlash(Vector3 at, Vector3 travel, Vector3 blade, float size, int sparks, bool oath)
    {
        var cam = GetViewport()?.GetCamera3D();
        var back = cam != null ? cam.GlobalBasis.Z.Normalized() : Vector3.Up;
        // (lead 7) The mark lies IN the stroke, no longer on a quad facing the camera: its long axis the tip's travel at
        // the crossing, its width the stroke's own across there (the blade's line, turned to the camera by grip.face
        // exactly as GripDraw turns the ribbon: an edge-on cut's mark is no sliver either).
        var along = travel.LengthSquared() > 1e-6f ? travel.Normalized() : cam != null ? cam.GlobalBasis.X : Vector3.Right;
        var side = back.Cross(along);
        float blen = Mathf.Max(blade.Length(), 1e-4f);
        var across = blade / blen;
        if (side.LengthSquared() > 1e-6f)
        {
            side = side.Normalized();
            float shown = across.Dot(side);
            float way = Mathf.Abs(shown) > 0.15f ? Mathf.Sign(shown) : side.Dot(PlayerPos + Vector3.Up * 1.1f - at) < 0 ? -1 : 1;
            var face = P7D.All("grip.face");
            if (face[1] > 0) across = across.Lerp(side * way, 1 - Mathf.SmoothStep(face[0], face[1], shown * way));
        }
        across -= along * across.Dot(along);
        if (across.LengthSquared() < 1e-4f) across = side.LengthSquared() > 1e-6f ? side : cam != null ? cam.GlobalBasis.Y : Vector3.Up;
        across = across.Normalized();
        // (take 6) the mark's length = a share of the stroke's head (its width), by `size`; a blunt slab, not a line
        var mk = P7D.All("grip.contact.mark");
        float len = mk[0] * GripLookOf(oath).Head * blen * size, wid = mk[1] * len;
        var half = new Vector2(0.5f * len + 0.6f * wid, 0.6f * wid + 0.03f);
        var m = new ShaderMaterial { Shader = GD.Load<Shader>(GripShader) };
        FxCel.Apply(m, School.Physical, FxAfter.On);
        m.SetShaderParameter("grip_mode", 1);
        m.SetShaderParameter("grip_size", half);
        m.SetShaderParameter("grip_px", P7Px(at));
        m.SetShaderParameter("grip_seed", R() * 97f);
        m.SetShaderParameter("grip_core", oath ? 0.6f : 1f);
        var st = P7D.All("grip.contact.steps");
        float whole = P7D["grip.contact.full_frames"];
        m.SetShaderParameter("grip_kite", new Vector4(len, wid, mk[2], mk[3]));
        m.SetShaderParameter("grip_steps", new Vector4(whole, st[0], st[1], 0));
        p7Quad ??= new QuadMesh { Size = new Vector2(2, 2) };
        var q = new MeshInstance3D { Mesh = p7Quad, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(q);
        // (toward the camera: over the blade and the struck body, never inside them)
        q.GlobalTransform = new Transform3D(new Godot.Basis(along * half.X, across * half.Y, along.Cross(across)), at + back * P7D["grip.contact.lift"] * Mathf.Min(1f, size * 4));
        if (FxAfter.On) FxAfter.Adopt(q);
        var s = new P7Shape
        {
                N = q, M = m, Life = (whole + 2) / 60f - 0.002f,
            Step = x =>
            {
                x.M.SetShaderParameter("grip_thin", Mathf.Floor(x.Age * 60 + 0.05f));
                x.M.SetShaderParameter("grip_age", x.Age);
            },
        };
        p7Shapes.Add(s);
        s.Step(s);
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
