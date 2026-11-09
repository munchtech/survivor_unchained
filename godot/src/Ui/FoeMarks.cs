using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Foe health (H1 combat teeth, item 2) and the priority mark (item 4), drawn in one batch for every foe:
/// a thin bar just under a crowd foe's feet (once below 70%, or the priority target's), a champion's bar over its head always (N19),
/// and an ellipse ring at the feet of the priority foe. No nodes per foe, nothing allocated per frame.
/// </summary>
public partial class FoeMarks : Control
{
    struct Bar { public Vector2 At; public float K; public bool Elite, Full; public Named? N; public string? Cap; }
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
    static readonly Color Ink = new(0.043f, 0.035f, 0.024f, 0.78f), Danger = new("#b8302f"), Bronze = new("#8a6a3a"), BronzeHi = new("#c9a35c"), Bone = new("#e6dcc8");

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
            if (!e.Alive || e.State == EnemyState.Dying || e.State == EnemyState.Burrowed) continue;
            // (M5 r2: Faction.Dead is the risen's side, not a corpse: it hid every undead foe's bar, ring and plate, the
            // Barrow Knight's and the Grave-Caller's among them. The dying and the fallen are out above.)
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
            // Over its head (a champion's bar, and the snuffer's diamond above that bar when it has one).
            var overHead = p + Vector3.Up * (float)Math.Max(Math.Max(1.6, e.Radius * 3.2 + 0.8), (e.Def.Scale ?? 1) * e.RankScale * 1.85 + 0.35);
            bool eliteBar = wantBar && e.Elite;
            // (M5 r2: a plate only while its owner is on screen; one at the edge was cut by it)
            if (eliteBar && (sp.X < 0 || sp.Y < 0 || sp.X > vp.Size.X || sp.Y > vp.Size.Y)) { eliteBar = false; wantBar = isPri; }
            if (snuff)
            {
                if (snuffCount == snuffs.Length) Array.Resize(ref snuffs, snuffCount * 2);
                snuffs[snuffCount++] = cam.UnprojectPosition(overHead) - new Vector2(0, eliteBar ? (e.Named != null ? 48 : 30) * s : 0);
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
            // N19 (H6): a champion's bar is over its head at full strength from its first moment, as an ARPG's elite
            // bar is; at its feet at 45% it was lost on the night ground and read as no bar at all. The crowd's small
            // bar stays at the feet (once below 70%, or the priority target's).
            bars[count++] = new Bar { At = eliteBar ? cam.UnprojectPosition(overHead) : sp, K = (float)Math.Clamp(e.Hp / e.MaxHp, 0, 1), Elite = e.Elite, Full = !low && !isPri && !e.Elite, N = eliteBar ? e.Named : null, Cap = eliteBar && e.Named == null && e.Rank == 1 ? e.Def.Name : null };
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

    /// <summary>A champion's bar over its head: the lamp bar's bronze-framed ink well at a champion's size, its life
    /// in danger red lit along the top, quarter notches, a dark shadow so it holds on any ground or crowd.</summary>
    void EliteBar(in Bar b, float s)
    {
        float w = (b.N != null ? 92 : 64) * s, h = (b.N != null ? 9 : 7) * s;
        // (M5 r2: held inside the safe area, 5% in from each side and a title's height under the top)
        var vp = GetViewportRect().Size;
        float mx = vp.X * 0.05f + 60 * s, top = vp.Y * 0.05f + 30 * s;
        float cx = Math.Clamp(b.At.X, mx, Math.Max(mx, vp.X - mx)), cy = Math.Clamp(b.At.Y, top + h, Math.Max(top + h, vp.Y * 0.95f));
        var r = new Rect2(Mathf.Round(cx - w / 2), Mathf.Round(cy - h - 6 * s), w, h);
        DrawRect(r.Grow(2 * s), new Color(0, 0, 0, 0.45f));
        DrawRect(r, Ink with { A = 0.92f });
        var inner = r.Grow(-1.5f * s);
        if (b.K > 0)
        {
            var fill = new Rect2(inner.Position, new Vector2(inner.Size.X * b.K, inner.Size.Y));
            DrawRect(fill, Danger);
            DrawRect(new Rect2(fill.Position, new Vector2(fill.Size.X, Math.Max(1, inner.Size.Y * 0.35f))), Danger.Lightened(0.28f));
        }
        for (int q = 1; q < 4; q++)
        {
            float qx = Mathf.Round(inner.Position.X + inner.Size.X * q / 4f);
            DrawRect(new Rect2(qx, inner.Position.Y, Math.Max(1, s), inner.Size.Y), new Color(Ink, 0.55f));
        }
        DrawRect(r, Bronze, false, Math.Max(1.5f, 1.5f * s));
        DrawRect(new Rect2(r.Position.X + s, r.Position.Y, r.Size.X - 2 * s, Math.Max(1, s)), BronzeHi);
        if (b.N is { } n) Champion(n, r, s);
        else if (b.Cap is { } c) Captain(c, r, s);
    }

    /// <summary>(M5 r2, functional; the look is the UI lead's) A captain's short plate: its kind and its rank, a step
    /// below a champion's title (smaller, the bronze dimmer) over its smaller bar.</summary>
    void Captain(string name, Rect2 r, float s)
    {
        var font = ThemeDB.FallbackFont;
        int fs = (int)(14 * s);
        string t = name + "  • captain";
        var sz = font.GetStringSize(t, HorizontalAlignment.Left, -1, fs);
        var at = new Vector2(Mathf.Round(r.Position.X + r.Size.X / 2 - sz.X / 2), Mathf.Round(r.Position.Y - 4 * s));
        DrawStringOutline(font, at, t, HorizontalAlignment.Left, -1, fs, Math.Max(2, (int)(3 * s)), Ink with { A = 0.9f });
        DrawString(font, at, t, HorizontalAlignment.Left, -1, fs, Bronze.Lightened(0.35f));
    }

    /// <summary>(M5-B, functional; the look is the UI lead's) A champion's title over its bar in bronze, and its affixes
    /// under it in a light parchment with an ink outline (M5 r2: red on the red bar did not read).</summary>
    void Champion(Named n, Rect2 r, float s)
    {
        var font = ThemeDB.FallbackFont;
        float cx = r.Position.X + r.Size.X / 2;
        if (n.Title.Length > 0)
        {
            int fs = (int)(16 * s);
            var sz = font.GetStringSize(n.Title, HorizontalAlignment.Left, -1, fs);
            var at = new Vector2(Mathf.Round(cx - sz.X / 2), Mathf.Round(r.Position.Y - 4 * s));
            DrawStringOutline(font, at, n.Title, HorizontalAlignment.Left, -1, fs, Math.Max(2, (int)(4 * s)), Ink with { A = 0.95f });
            DrawString(font, at, n.Title, HorizontalAlignment.Left, -1, fs, BronzeHi);
        }
        if (n.Affixes.Count == 0) return;
        int afs = (int)(17 * s);
        float gap = 9 * s, w = -gap;
        foreach (var a in n.Affixes) w += font.GetStringSize(a, HorizontalAlignment.Left, -1, afs).X + gap;
        float x = Mathf.Round(cx - w / 2), y = Mathf.Round(r.End.Y + 3 * s + font.GetAscent(afs));
        var light = new Color("#f3e7cf");
        int ow = Math.Max(2, (int)(4 * s));
        foreach (var a in n.Affixes)
        {
            DrawStringOutline(font, new Vector2(x, y), a, HorizontalAlignment.Left, -1, afs, ow, Ink with { A = 0.95f });
            DrawString(font, new Vector2(x, y), a, HorizontalAlignment.Left, -1, afs, light);
            x += font.GetStringSize(a, HorizontalAlignment.Left, -1, afs).X + gap;
        }
    }

    public override void _Draw()
    {
        float s = GetViewportRect().Size.Y / 1080f;
        for (int i = 0; i < count; i++)
        {
            ref var b = ref bars[i];
            if (b.Elite) { EliteBar(b, s); continue; }
            float w = 34 * s, h = 4 * s;
            float a = b.Full ? 0.45f : 1f;
            var r = new Rect2(b.At.X - w / 2, b.At.Y + 3 * s, w, h);
            DrawRect(r, new Color(Ink, Ink.A * a));
            var inner = r.Grow(-1 * s);
            DrawRect(new Rect2(inner.Position, new Vector2(inner.Size.X * b.K, inner.Size.Y)), new Color(Danger, a));
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
            DrawRect(r, new Color(Bone, a), false, Math.Max(1, s));
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
            DrawPolyline(ringPts, new Color(Ink, 0.85f), 4.5f * s, true);
            DrawPolyline(ringPts, new Color(Bone, 0.65f + 0.3f * pulse), 2.5f * s, true);
        }
    }
}
