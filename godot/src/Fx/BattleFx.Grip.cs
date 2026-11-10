using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Her held grip's cut (M3 MR 2, item 9, take 2; the most-seen effect in the game): the TRAIL HER BLADE LEAVES, built
/// from the blade itself. Her held blade's hilt and tip are sampled in world space on every skeleton update (the frame's
/// final pose, after the attachments: no frame of lag), and the trail is the ribbon between the hilt's path and the
/// tip's path over the cut's last frames: its head IS the blade on the contact frame, its tail lies where the blade came
/// from. Painted in the steel family's three bands after the grade (shaders/fx_grip_stroke.gdshader): a white-gold
/// stroke hugging the tip's path (the outer edge clean and hard), gold trailing inside it, amber only in the dry tail,
/// and a thin flat smear of dry-brush streaks in toward the hilt. It shows two frames before the contact (from the
/// sim's AttackAnim and the clip's contact, data/anim/her_events.json), is whole on the contact, follows the blade
/// through, and steps out from the tail (0.05 s a step) to nothing 0.15 s after the contact. Where the cut meets a
/// body: a short white cut-through along the blade's travel with a small kernel and a few tears thrown along it.
/// Sunder's is the wider and whiter; the Oathblade's is thinner and more gold, and keeps its gold pool on the ground.
/// Called from Swing() for a held cut; at --cel off or --p7fx-off (or --grip-old) Swing() draws the old crescents.
/// No blade found (never in the campaign): nothing is drawn but the contact.
/// </summary>
public partial class BattleFx
{
    static readonly bool GripStrokeOn = FxCel.On && !P7Off && !Args.Has("grip-old");
    static readonly bool GripSay = Args.Has("clip") || Args.Has("grip-say");
    const string GripShader = "res://shaders/fx_grip_stroke.gdshader";

    /// <summary>The look by weapon: the stroke's width at its head (m, in from the tip's path), the white's share of it,
    /// the longest the trail is drawn (m of the tip's path), the smear's coverage, the contact's size.</summary>
    readonly record struct GripLook(float Width, float Core, float MaxLen, float Smear, float Flash);
    static readonly GripLook GripSunder = new(0.28f, 0.5f, 2.7f, 0.34f, 1f), GripOath = new(0.22f, 0.34f, 2.5f, 0.28f, 0.8f);
    /// <summary>Seen before the contact, a step of the way out, the tail's cut and thinning at each step, how slow a blade
    /// leaves no trail (m/s at the tip), and the margin drawn past the tip (a share of the blade: the glow, the edge's
    /// antialiasing).</summary>
    const double GripLead = 2 / 60.0, GripStepS = 0.05;
    static readonly float[] GripCutAt = { 0f, 0.45f, 0.72f };
    const float GripSlow = 4f, GripOver = 0.12f;

    readonly record struct GripAt(Vector3 Hilt, Vector3 Tip, double At);
    readonly List<GripAt> gripRing = new(40);
    Node3D? gripBlade;
    Skeleton3D? gripSkel;
    double gripClock, gripAnimT = -1, gripDue = -1, gripPressAt;
    bool gripDueOath;
    ulong gripDrawn;

    sealed class GripTrail
    {
        public bool Oath;
        /// <summary>In the watch's clock: the oldest sample drawn, the contact (-1: not yet), and when a trail still
        /// waiting for its cut gives up.</summary>
        public double Tail, Contact = -1, Until;
        /// <summary>The contact's flash, owed until the contact frame's own sample is in.</summary>
        public bool FlashOwed;
        public int Struck, Killed;
        public Vector3 Body;
        public int Said;
    }
    GripTrail? gripLive;
    MeshInstance3D? gripNode;
    ImmediateMesh? gripMesh;
    ShaderMaterial? gripMat;
    int gripWarm;
    readonly List<(Vector3 H, Vector3 T)> gripPts = new(160);
    readonly List<float> gripCum = new(160);

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

    /// <summary>Each frame, before anything moves: the watch's clock (real frames: a hitstop does not hold the trail on
    /// screen), the hook on her skeleton kept on the blade she holds now, and a trail whose skeleton stood still.</summary>
    void GripWatch()
    {
        gripClock += GetProcessDeltaTime();
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
        if (gripLive != null && gripDrawn + 1 < Engine.GetProcessFrames()) GripDraw();
    }

    /// <summary>The blade's point `k` of the way from the guard (0) to the tip (1), in world space.</summary>
    (Vector3 Hilt, Vector3 Tip)? GripBladeNow()
    {
        if (gripBlade is not { } bl || !IsInstanceValid(bl) || !bl.IsInsideTree()) return null;
        float tip = bl.HasMeta("tip") ? (float)bl.GetMeta("tip") : 1.4f;
        var xf = bl.GlobalTransform;
        return (xf * new Vector3(0, tip * 0.14f, 0), xf * new Vector3(0, tip, 0));
    }

    /// <summary>Her skeleton has its frame's pose (and the attachments theirs): the blade's sample, a held cut's trail
    /// armed from the sim's swing, and the trail drawn from the samples.</summary>
    void GripSample()
    {
        if (GripBladeNow() is not { } now) return;
        if (gripRing.Count > 0 && gripRing[^1].At >= gripClock - 1e-6) gripRing[^1] = new GripAt(now.Hilt, now.Tip, gripClock);
        else gripRing.Add(new GripAt(now.Hilt, now.Tip, gripClock));
        if (gripRing.Count > 36) gripRing.RemoveRange(0, gripRing.Count - 36);
        if (gripWarm > 0) GripWarm();
        // A held cut's swing has begun (the sim's AttackAnim: its clip and rate): the trail is owed two frames before
        // the clip's contact comes round.
        if (b0 is { } b && b.Player.AttackAnim is { Clip: { } clip } aa && aa.T != gripAnimT)
        {
            gripAnimT = aa.T; gripDue = -1; gripPressAt = gripClock;
            if (!Flare.HushesSwings && HerEvents.Contact(clip) is double ct && GripHeld(b, aa.Weapon, out gripDueOath))
                gripDue = aa.T + ct / Math.Max(0.1, aa.Rate);
        }
        if (gripDue >= 0 && time >= gripDue - GripLead - 0.004)
        {
            if (time < gripDue + 0.05) gripLive = new GripTrail { Oath = gripDueOath, Tail = gripPressAt, Until = gripClock + GripLead + 2.5 / 60 };
            gripDue = -1;
        }
        if (gripLive != null) GripDraw();
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

    /// <summary>Swing()'s held cut: the contact. The trail (already two frames old, or born here from the samples) is
    /// whole on this frame; the flash waits for the frame's own blade.</summary>
    void GripCut(Ev.Slash e, Vector3 at, float reach, float g, bool oath)
    {
        if (oath && AaFxOff) return;
        var tr = gripLive is { Contact: < 0 } armed ? armed : new GripTrail { Tail = gripClock - 5 / 60.0 };
        tr.Oath = oath; tr.Contact = gripClock;
        gripLive = tr;
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
            // The heavy blade's grit where it passes nearest the ground.
            Dust(tx, tz, 3, 1.6f * g);
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
        gripMesh = new ImmediateMesh();
        gripMat = new ShaderMaterial { Shader = GD.Load<Shader>(GripShader) };
        FxCel.Apply(gripMat, School.Physical, FxAfter.On);
        gripNode = new MeshInstance3D { Mesh = gripMesh, MaterialOverride = gripMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false, Name = "GripTrail" };
        AddChild(gripNode);
        gripNode.GlobalTransform = Transform3D.Identity;
        if (FxAfter.On) FxAfter.Adopt(gripNode);
        gripWarm = 3;
    }

    /// <summary>The first use's compiles paid when she takes the blade, not on her first cut: the trail and the contact
    /// drawn for three frames, a few centimetres across, under her feet.</summary>
    void GripWarm()
    {
        if (gripLive != null || gripMesh == null || gripNode == null || gripMat == null) { gripWarm = 0; return; }
        gripWarm--;
        var o = PlayerPos + Vector3.Down * 0.3f;
        gripMesh.ClearSurfaces();
        if (gripWarm <= 0) { gripNode.Visible = false; return; }
        gripMesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = 0; i < 2; i++)
        {
            gripMesh.SurfaceSetUV(new Vector2(i * 0.02f, 0)); gripMesh.SurfaceAddVertex(o + new Vector3(i * 0.02f, 0, 0));
            gripMesh.SurfaceSetUV(new Vector2(i * 0.02f, 1)); gripMesh.SurfaceAddVertex(o + new Vector3(i * 0.02f, 0, 0.02f));
        }
        gripMesh.SurfaceEnd();
        GripSet(GripSunder, 0.02f, 0.02f, 0, o);
        gripNode.Visible = true;
        if (gripWarm == 2) GripFlash(o, Vector3.Right, 0.02f, 1, false);
    }

    void GripEnd()
    {
        gripLive = null;
        if (gripNode != null && IsInstanceValid(gripNode)) gripNode.Visible = false;
    }

    void GripSet(GripLook look, float total, float blade, int step, Vector3 her)
    {
        var m = gripMat!;
        m.SetShaderParameter("grip_total", total);
        m.SetShaderParameter("grip_blade", blade);
        m.SetShaderParameter("grip_w", look.Width);
        m.SetShaderParameter("grip_core", look.Core);
        m.SetShaderParameter("grip_smear", look.Smear);
        m.SetShaderParameter("grip_cut", GripCutAt[Math.Clamp(step, 0, 2)]);
        m.SetShaderParameter("grip_thin", (float)step);
        m.SetShaderParameter("grip_px", P7Px(her));
        gripNode!.CustomAabb = new Aabb(her - new Vector3(5, 3, 5), new Vector3(10, 7, 10));
    }

    /// <summary>The trail from the samples: the blade's path splined between frames (the hilt's place and the blade's
    /// direction, so the blade keeps its length through a fast turn), the tail trimmed of the wind-up's drift and capped
    /// at the look's length, the head on the newest sample.</summary>
    void GripDraw()
    {
        if (gripLive is not { } tr || gripMesh == null || gripNode == null || !IsInstanceValid(gripNode)) return;
        gripDrawn = Engine.GetProcessFrames();
        double age = tr.Contact < 0 ? -1 : gripClock - tr.Contact;
        if (tr.Contact < 0 && gripClock > tr.Until) { GripEnd(); return; }
        int step = age < 0 ? 0 : (int)((age + 0.004) / GripStepS);
        if (step >= 3) { GripEnd(); return; }
        var look = tr.Oath ? GripOath : GripSunder;
        int n = gripRing.Count, i0 = 0;
        while (i0 < n - 1 && gripRing[i0].At < tr.Tail - 1e-6) i0++;
        // the wind-up's drift leaves no trail: the tail starts where the blade is first fast
        while (i0 < n - 2 && gripRing[i0].Tip.DistanceTo(gripRing[i0 + 1].Tip) < GripSlow * Math.Max(1e-3, gripRing[i0 + 1].At - gripRing[i0].At)) i0++;
        if (tr.FlashOwed && age >= -1e-6)
        {
            tr.FlashOwed = false;
            GripContact(tr, look);
        }
        if (GripSay && tr.Said < 12 && n >= 2)
        {
            tr.Said++;
            var s1 = gripRing[^1]; var s0 = gripRing[^2];
            var d = s1.Tip - PlayerPos;
            GD.Print($"grip frame {Engine.GetFramesDrawn()} age {age * 60:0.0}f step {step} samples {n - i0} tip az {Mathf.RadToDeg(Mathf.Atan2(d.Z, d.X)):0} r {new Vector2(d.X, d.Z).Length():0.00} y {d.Y:0.00} speed {s1.Tip.DistanceTo(s0.Tip) / Math.Max(1e-3, s1.At - s0.At):0.0} m/s blade {s1.Tip.DistanceTo(s1.Hilt):0.00} oath {tr.Oath}");
        }
        gripPts.Clear(); gripCum.Clear();
        if (n - i0 < 2) { gripNode.Visible = false; return; }
        for (int k = i0; k < n - 1; k++)
        {
            var a = gripRing[k]; var b = gripRing[k + 1];
            var pa = gripRing[Math.Max(k - 1, 0)]; var pb = gripRing[Math.Min(k + 2, n - 1)];
            Vector3 da = a.Tip - a.Hilt, db = b.Tip - b.Hilt, dpa = pa.Tip - pa.Hilt, dpb = pb.Tip - pb.Hilt;
            float la = da.Length(), lb = db.Length();
            da /= la; db /= lb; dpa = dpa.Normalized(); dpb = dpb.Normalized();
            int sub = Mathf.Clamp(Mathf.CeilToInt(Mathf.RadToDeg(da.AngleTo(db)) / 4f), 1, 20);
            for (int j = 0; j < sub; j++)
            {
                float t = j / (float)sub;
                var h = a.Hilt.CubicInterpolate(b.Hilt, pa.Hilt, pb.Hilt, t);
                var dir = da.CubicInterpolate(db, dpa, dpb, t).Normalized();
                gripPts.Add((h, h + dir * Mathf.Lerp(la, lb, t)));
            }
        }
        var last = gripRing[n - 1];
        gripPts.Add((last.Hilt, last.Tip));
        float cum = 0;
        gripCum.Add(0);
        for (int i = 1; i < gripPts.Count; i++) { cum += gripPts[i].T.DistanceTo(gripPts[i - 1].T); gripCum.Add(cum); }
        int s = 0;
        while (s < gripPts.Count - 2 && cum - gripCum[s] > look.MaxLen) s++;
        float total = cum - gripCum[s];
        if (total < 0.05f) { gripNode.Visible = false; return; }
        gripMesh.ClearSurfaces();
        gripMesh.SurfaceBegin(Mesh.PrimitiveType.TriangleStrip);
        for (int i = s; i < gripPts.Count; i++)
        {
            var (h, t) = gripPts[i];
            float u = gripCum[i] - gripCum[s];
            gripMesh.SurfaceSetUV(new Vector2(u, 0)); gripMesh.SurfaceAddVertex(h);
            gripMesh.SurfaceSetUV(new Vector2(u, 1 + GripOver)); gripMesh.SurfaceAddVertex(t + (t - h) * GripOver);
        }
        // a few centimetres past the head, for the head's own edge
        {
            var (h1, t1) = gripPts[^1]; var (h0, t0) = gripPts[^2];
            float f = 0.05f / Mathf.Max(0.005f, t1.DistanceTo(t0));
            Vector3 h = h1 + (h1 - h0) * f, t = t1 + (t1 - t0) * f;
            gripMesh.SurfaceSetUV(new Vector2(total + 0.05f, 0)); gripMesh.SurfaceAddVertex(h);
            gripMesh.SurfaceSetUV(new Vector2(total + 0.05f, 1 + GripOver)); gripMesh.SurfaceAddVertex(t + (t - h) * GripOver);
        }
        gripMesh.SurfaceEnd();
        GripSet(look, total, last.Tip.DistanceTo(last.Hilt), step, PlayerPos);
        gripNode.Visible = true;
    }

    /// <summary>The contact, on the contact frame's blade: where the blade's line crosses the struck body (a step toward
    /// her and toward the camera), a cut-through laid along the tip's travel, larger for a kill or a crowd.</summary>
    void GripContact(GripTrail tr, GripLook look)
    {
        int n = gripRing.Count;
        if (n < 2) return;
        var s1 = gripRing[^1]; var s0 = gripRing[^2];
        var travel = s1.Tip - s0.Tip;
        if (travel.LengthSquared() < 1e-4f) return;
        var body = tr.Body;
        var her = new Vector3(PlayerPos.X, 0, PlayerPos.Z);
        float dBody = new Vector2(body.X - her.X, body.Z - her.Z).Length(), dHilt = new Vector2(s1.Hilt.X - her.X, s1.Hilt.Z - her.Z).Length(), dTip = new Vector2(s1.Tip.X - her.X, s1.Tip.Z - her.Z).Length();
        float k = Mathf.Clamp((dBody - 0.3f - dHilt) / Mathf.Max(0.1f, dTip - dHilt), 0.35f, 1f);
        var to = new Vector3(her.X - body.X, 0, her.Z - body.Z);
        var at = new Vector3(body.X, Mathf.Lerp(s1.Hilt.Y, s1.Tip.Y, k), body.Z);
        if (to.LengthSquared() > 0.01f) at += to.Normalized() * 0.3f;
        float size = look.Flash * (tr.Killed > 0 ? 1.3f : tr.Struck >= 3 ? 1.12f : 1f);
        int sparks = Math.Min(6, 3 + tr.Struck / 2 + (tr.Killed > 0 ? 1 : 0));
        if (GripSay) GD.Print($"grip contact frame {Engine.GetFramesDrawn()} struck {tr.Struck} killed {tr.Killed} oath {tr.Oath} size {size:0.00} at {at}");
        GripFlash(at, travel.Normalized(), size, sparks, tr.Oath);
    }

    /// <summary>The contact's picture: a quad facing the camera, its long axis the blade's travel as the camera sees it,
    /// drawn in the trail's shader (its second mode): the cut-through and its kernel for three frames (two whole, one
    /// thin), the tears flying on for a few more.</summary>
    void GripFlash(Vector3 at, Vector3 travel, float size, int sparks, bool oath)
    {
        var cam = GetViewport()?.GetCamera3D();
        var back = cam != null ? cam.GlobalBasis.Z.Normalized() : Vector3.Up;
        var along = travel - back * travel.Dot(back);
        if (along.LengthSquared() < 1e-4f) along = cam != null ? cam.GlobalBasis.X : Vector3.Right;
        along = along.Normalized();
        var across = back.Cross(along).Normalized();
        var half = new Vector2(1.5f, 0.5f) * size;
        var m = new ShaderMaterial { Shader = GD.Load<Shader>(GripShader) };
        FxCel.Apply(m, School.Physical, FxAfter.On);
        m.SetShaderParameter("grip_mode", 1);
        m.SetShaderParameter("grip_size", half);
        m.SetShaderParameter("grip_px", P7Px(at));
        m.SetShaderParameter("grip_seed", R() * 97f);
        m.SetShaderParameter("grip_sparks", (float)sparks);
        m.SetShaderParameter("grip_core", oath ? 0.6f : 1f);
        p7Quad ??= new QuadMesh { Size = new Vector2(2, 2) };
        var q = new MeshInstance3D { Mesh = p7Quad, MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        AddChild(q);
        // (toward the camera: the struck body stands in the blade's line, never over its own flash)
        q.GlobalTransform = new Transform3D(new Godot.Basis(along * half.X, across * half.Y, back), at + back * 0.6f * Mathf.Min(1f, size * 4));
        if (FxAfter.On) FxAfter.Adopt(q);
        var s = new P7Shape
        {
            N = q, M = m, Life = 8 / 60f - 0.002f,
            Step = x =>
            {
                x.M.SetShaderParameter("grip_thin", Mathf.Floor(x.Age * 60 + 0.05f));
                x.M.SetShaderParameter("grip_age", x.Age);
            },
        };
        p7Shapes.Add(s);
        s.Step(s);
    }
}
