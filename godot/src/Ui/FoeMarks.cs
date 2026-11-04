using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Foe health (H1 combat teeth, item 2) and the priority mark (item 4), drawn in one batch for every foe:
/// a thin bar just under a foe's feet (crowd foes only once below 70%, champions always, fainter while full),
/// and an ellipse ring at the feet of the priority foe. No nodes per foe, nothing allocated per frame.
/// </summary>
public partial class FoeMarks : Control
{
    struct Bar { public Vector2 At; public float K; public bool Elite, Full; }
    Bar[] bars = new Bar[256];
    int count;
    bool ring;
    Vector2 ringAt;
    float ringR;
    float time;
    readonly Vector2[] ringPts = new Vector2[33];
    // A board's lamp (H1 item 6B, Battle.HeldLamp): its life bar over it when below full, and its pool's edge on the
    // ground while she stands outside it. Functional; its look is H2's.
    bool lampBar, lampRing, lampOut;
    Vector2 lampAt;
    // The lamp's snuffers (Enemy.Goal): a small cold-blue diamond over each, the foes to turn on to save it.
    Vector2[] snuffs = new Vector2[32];
    int snuffCount;
    readonly Vector2[] dia = new Vector2[4], diaEdge = new Vector2[5];
    static readonly Color Snuff = new("#8fd0ff");
    float lampK;
    readonly Vector2[] poolPts = new Vector2[49];
    static readonly Color LampFill = new("#ffd07a");
    static readonly Color Ink = new(0.043f, 0.035f, 0.024f, 0.78f), Danger = new("#b8302f"), Bronze = new("#8a6a3a"), BronzeHi = new("#c9a35c");

    public FoeMarks() { MouseFilter = MouseFilterEnum.Ignore; }

    /// <summary>This frame's marks from the battle. at: where a foe is drawn (sim X, Z).</summary>
    public void Show(Battle b, Camera3D cam, Func<Enemy, (double X, double Z)> at, bool bars_)
    {
        count = 0;
        snuffCount = 0;
        ring = false;
        var vp = GetViewportRect();
        float s = vp.Size.Y / 1080f;
        time += (float)GetProcessDeltaTime();
        var items = b.Enemies.Items;
        int pri = b.Priority;
        if (pri >= 0 && (pri >= items.Length || !b.Targetable(items[pri]))) pri = -1;
        for (int i = 0; i < items.Length; i++)
        {
            var e = items[i];
            if (!e.Alive || e.State == EnemyState.Dying || e.State == EnemyState.Burrowed || e.Faction == Faction.Dead) continue;
            if (e.Disposition == Disposition.Ally) continue;
            bool isPri = i == pri;
            if (e.Boss && !isPri) continue;
            if (!isPri && !b.Targetable(e)) continue;
            bool low = e.Hp / Math.Max(1e-6, e.MaxHp) < 0.7;
            bool wantBar = bars_ && !e.Boss && (low || e.Elite || isPri);
            bool snuff = e.Goal && b.HeldLamp is { Lit: true };
            if (!wantBar && !isPri && !snuff) continue;
            var (x, z) = at(e);
            var p = new Vector3((float)x, (float)b.HeightAt(x, z), (float)z);
            if (cam.IsPositionBehind(p)) continue;
            var sp = cam.UnprojectPosition(p);
            if (sp.X < -80 || sp.Y < -40 || sp.X > vp.Size.X + 80 || sp.Y > vp.Size.Y + 80) continue;
            if (snuff)
            {
                if (snuffCount == snuffs.Length) Array.Resize(ref snuffs, snuffCount * 2);
                snuffs[snuffCount++] = cam.UnprojectPosition(p + Vector3.Up * (float)Math.Max(1.6, e.Radius * 3.2 + 0.8));
            }
            if (!wantBar && !isPri) continue;
            if (isPri)
            {
                ring = true;
                ringAt = sp;
                // Radius on screen: the foe's radius at its ground point, to the side of the camera.
                var side = cam.UnprojectPosition(p + cam.GlobalTransform.Basis.X * (float)Math.Max(0.4, e.Radius));
                ringR = Math.Max(10 * s, Math.Abs(side.X - sp.X) * 1.15f);
            }
            if (!wantBar || e.Boss) continue;
            if (count == bars.Length) Array.Resize(ref bars, count * 2);
            bool full = !low;
            bars[count++] = new Bar { At = sp, K = (float)Math.Clamp(e.Hp / e.MaxHp, 0, 1), Elite = e.Elite, Full = full && !isPri };
        }
        Lamp(b, cam, vp);
        QueueRedraw();
    }

    void Lamp(Battle b, Camera3D cam, Rect2 vp)
    {
        lampBar = lampRing = lampOut = false;
        if (b.HeldLamp is not { Caught: true } l) return;
        float y = (float)b.HeightAt(l.X, l.Z);
        var top = new Vector3((float)l.X, y + (float)l.Top + 0.4f, (float)l.Z);
        // Doused, its life over it; out, an empty bar and the hint to light it again.
        if ((l.Life < 0.999 || !l.Lit) && !cam.IsPositionBehind(top))
        {
            lampBar = true; lampOut = !l.Lit;
            lampAt = cam.UnprojectPosition(top);
            lampAt.Y = Math.Max(lampAt.Y, 60 * vp.Size.Y / 1080f);
            lampK = l.Lit ? (float)Math.Clamp(l.Life, 0, 1) : 0;
        }
        var p = b.Player;
        if (!l.Lit || (p.X - l.X) * (p.X - l.X) + (p.Z - l.Z) * (p.Z - l.Z) < l.Pool * l.Pool) return;
        for (int i = 0; i < poolPts.Length; i++)
        {
            double t = i / (double)(poolPts.Length - 1) * Math.Tau;
            double x = l.X + Math.Cos(t) * l.Pool, z = l.Z + Math.Sin(t) * l.Pool;
            var w = new Vector3((float)x, (float)b.HeightAt(x, z) + 0.05f, (float)z);
            if (cam.IsPositionBehind(w)) return;
            poolPts[i] = cam.UnprojectPosition(w);
        }
        lampRing = true;
    }

    /// <summary>Nothing this frame.</summary>
    public void Show0() { if (count == 0 && snuffCount == 0 && !ring && !lampBar && !lampRing) return; count = snuffCount = 0; ring = lampBar = lampRing = false; QueueRedraw(); }

    public override void _Draw()
    {
        float s = GetViewportRect().Size.Y / 1080f;
        for (int i = 0; i < count; i++)
        {
            ref var b = ref bars[i];
            float w = (b.Elite ? 64 : 34) * s, h = (b.Elite ? 6 : 4) * s;
            float a = b.Full ? 0.45f : 1f;
            var r = new Rect2(b.At.X - w / 2, b.At.Y + 3 * s, w, h);
            DrawRect(r, new Color(Ink, Ink.A * a));
            var inner = r.Grow(-1 * s);
            DrawRect(new Rect2(inner.Position, new Vector2(inner.Size.X * b.K, inner.Size.Y)), new Color(Danger, a));
            if (b.Elite) DrawRect(r, new Color(Bronze, a), false, Math.Max(1, s));
        }
        if (lampRing)
        {
            // A dashed warm-white line (the place to hold), never the unbroken amber ring of a blow to leave.
            var warm = new Color("#fff1d6");
            for (int i = 0; i + 1 < poolPts.Length; i += 2)
            {
                DrawLine(poolPts[i], poolPts[i + 1], new Color(Ink, 0.4f), 4.5f * s);
                DrawLine(poolPts[i], poolPts[i + 1], new Color(warm, 0.75f), 2.2f * s);
            }
        }
        if (lampBar)
        {
            // As a champion's bar, in the lamp's own light.
            float w = 128 * s, h = 12 * s;
            var r = new Rect2(lampAt.X - w / 2, lampAt.Y - h - 4 * s, w, h);
            float a = lampOut ? 0.55f : 1f;
            DrawRect(r, new Color(Ink, Ink.A * a));
            var inner = r.Grow(-1 * s);
            DrawRect(new Rect2(inner.Position, new Vector2(inner.Size.X * lampK, inner.Size.Y)), LampFill);
            DrawRect(r, new Color(Bronze, a), false, Math.Max(1, s));
            if (lampOut)
            {
                var font = ThemeDB.FallbackFont;
                int fs = (int)(22 * s);
                const string hint = "Out: stand at the lamp to relight";
                var sz = font.GetStringSize(hint, HorizontalAlignment.Left, -1, fs);
                var at = new Vector2(lampAt.X - sz.X / 2, lampAt.Y - 5 * s);
                DrawString(font, at + new Vector2(1, 1) * s, hint, HorizontalAlignment.Left, -1, fs, Ink);
                DrawString(font, at, hint, HorizontalAlignment.Left, -1, fs, new Color(LampFill, 0.85f));
            }
        }
        for (int i = 0; i < snuffCount; i++)
        {
            // A small diamond, ink-edged, the cold of what puts the light out.
            var c = snuffs[i];
            float rx = 12 * s, ry = 16 * s;
            dia[0] = diaEdge[0] = diaEdge[4] = c + new Vector2(0, -ry);
            dia[1] = diaEdge[1] = c + new Vector2(rx, 0);
            dia[2] = diaEdge[2] = c + new Vector2(0, ry);
            dia[3] = diaEdge[3] = c + new Vector2(-rx, 0);
            DrawColoredPolygon(dia, new Color(Snuff, 0.9f));
            DrawPolyline(diaEdge, Ink, 3f * s, true);
        }
        if (ring)
        {
            float pulse = 0.5f + 0.5f * Mathf.Sin(time * 2.6f);
            float rx = ringR * (1 + 0.05f * pulse), ry = rx * 0.5f;
            for (int i = 0; i < ringPts.Length; i++)
            {
                float t = i / (float)(ringPts.Length - 1) * Mathf.Tau;
                ringPts[i] = ringAt + new Vector2(Mathf.Cos(t) * rx, Mathf.Sin(t) * ry);
            }
            DrawPolyline(ringPts, new Color(Ink, 0.6f), 4.5f * s, true);
            DrawPolyline(ringPts, new Color(BronzeHi, 0.65f + 0.3f * pulse), 2.5f * s, true);
        }
    }
}
