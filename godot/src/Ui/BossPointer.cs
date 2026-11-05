using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A live boss off screen (H1 round 2B; round 1's judge: "the boss is often off screen at his own signature"): a small
/// triangle on the screen's edge toward him, in the light he carries, pulsing while his signature move is on
/// (Enemy.SignatureUntil). Hidden while he is on screen. Nothing allocated per frame.
/// </summary>
public partial class BossPointer : Control
{
    const int Max = 4;
    readonly Vector2[] at = new Vector2[Max], dir = new Vector2[Max];
    readonly Color[] col = new Color[Max];
    readonly bool[] sig = new bool[Max], gap = new bool[Max];
    int count;
    float time;
    readonly Vector2[] tri = new Vector2[3];
    string? lastHex;
    Color lastCol = new("#b0222a");

    public BossPointer() { MouseFilter = MouseFilterEnum.Ignore; }

    public void Hide0() { if (count == 0) return; count = 0; QueueRedraw(); }

    public void Show(Battle b, Camera3D cam, Func<Enemy, (double X, double Z)> at_)
    {
        var vp = GetViewportRect();
        float s = vp.Size.Y / 1080f;
        time += (float)GetProcessDeltaTime();
        count = 0;
        var items = b.Enemies.Items;
        var c0 = vp.Size / 2;
        float m = 34 * s;
        for (int i = 0; i < items.Length && count < Max; i++)
        {
            var e = items[i];
            if (!e.Boss || !e.Alive || e.State == EnemyState.Dying || e.State == EnemyState.Burrowed) continue;
            var (x, z) = at_(e);
            var p = new Vector3((float)x, (float)b.HeightAt(x, z) + 1.5f, (float)z);
            bool behind = cam.IsPositionBehind(p);
            var sp = cam.UnprojectPosition(p);
            if (!behind && sp.X > 0 && sp.Y > 0 && sp.X < vp.Size.X && sp.Y < vp.Size.Y) continue;
            // (behind the camera the projection flips: point away from it)
            var d = sp - c0;
            if (behind) d = -d;
            if (d.LengthSquared() < 1) d = Vector2.Up;
            d = d.Normalized();
            // the edge point along d from the middle, inset by m
            float hx = vp.Size.X / 2 - m, hy = vp.Size.Y / 2 - m;
            float t = Math.Min(Math.Abs(d.X) < 1e-4f ? float.MaxValue : hx / Math.Abs(d.X), Math.Abs(d.Y) < 1e-4f ? float.MaxValue : hy / Math.Abs(d.Y));
            at[count] = c0 + d * t;
            dir[count] = d;
            if (e.Def.CarriedLight is { } cl)
            {
                if (!ReferenceEquals(cl.Color, lastHex)) { lastHex = cl.Color; lastCol = new Color(cl.Color); }
                col[count] = lastCol;
            }
            else col[count] = lastCol;
            sig[count] = e.SignatureUntil > b.Time;
            gap[count] = false;
            count++;
        }
        // A closing's way out off the screen (H6 r1 fix 1): a chevron in its own cyan on the edge toward it, for its windup
        // and while its wall stands (inset clear of the HUD's statues along the bottom).
        var tells = b.ActiveTells;
        for (int i = 0; i < tells.Count && count < Max; i++)
        {
            var t = tells[i];
            var k = t.Blow;
            if (t.Kind != "closing" || k.GapWidth <= 0 || !(k.T > 0 || (t.Landed && t.Walled))) continue;
            double r = (k.Inner + k.Radius) / 2, x = k.X + Math.Cos(k.GapAngle) * r, z = k.Z + Math.Sin(k.GapAngle) * r;
            var p = new Vector3((float)x, (float)b.HeightAt(x, z), (float)z);
            bool behind = cam.IsPositionBehind(p);
            var sp = cam.UnprojectPosition(p);
            float bottom = 200 * s;
            if (!behind && sp.X > m && sp.Y > m && sp.X < vp.Size.X - m && sp.Y < vp.Size.Y - bottom) continue;
            var d = sp - c0;
            if (behind) d = -d;
            if (d.LengthSquared() < 1) d = Vector2.Up;
            d = d.Normalized();
            float hx = vp.Size.X / 2 - m, hu = vp.Size.Y / 2 - m, hd = vp.Size.Y / 2 - bottom;
            float hy = d.Y > 0 ? hd : hu;
            float tt = Math.Min(Math.Abs(d.X) < 1e-4f ? float.MaxValue : hx / Math.Abs(d.X), Math.Abs(d.Y) < 1e-4f ? float.MaxValue : hy / Math.Abs(d.Y));
            at[count] = c0 + d * tt;
            dir[count] = d;
            col[count] = GapCyan;
            sig[count] = false;
            gap[count] = true;
            count++;
        }
        QueueRedraw();
    }

    public override void _Draw()
    {
        float s = GetViewportRect().Size.Y / 1080f;
        for (int i = 0; i < count; i++)
        {
            if (gap[i]) { Chevron(i, s); continue; }
            float pulse = sig[i] ? 0.55f + 0.45f * (0.5f + 0.5f * Mathf.Sin(time * 9f)) : 0.65f;
            float size = (sig[i] ? 17 + 4 * pulse : 15) * s;
            var d = dir[i];
            var n = new Vector2(-d.Y, d.X);
            tri[0] = at[i] + d * size;
            tri[1] = at[i] - d * size * 0.5f + n * size * 0.7f;
            tri[2] = at[i] - d * size * 0.5f - n * size * 0.7f;
            DrawColoredPolygon(tri, new Color(0.043f, 0.035f, 0.024f, 0.7f));
            var c = col[i] with { A = pulse };
            tri[0] = at[i] + d * size * 0.8f;
            tri[1] = at[i] - d * size * 0.4f + n * size * 0.5f;
            tri[2] = at[i] - d * size * 0.4f - n * size * 0.5f;
            DrawColoredPolygon(tri, c);
        }
    }

    readonly Vector2[] chev = new Vector2[6];
    /// <summary>The way out's own cyan (Palette.TeleSafe's hue at display strength).</summary>
    static readonly Color GapCyan = new("#8ad0ff");

    /// <summary>The way out's chevron: ~28 px, a dark keyline under the safe cyan, breathing.</summary>
    void Chevron(int i, float s)
    {
        var d = dir[i];
        var n = new Vector2(-d.Y, d.X);
        float size = 14 * s, th = 6 * s, pulse = 0.75f + 0.25f * (0.5f + 0.5f * Mathf.Sin(time * 6f));
        for (int pass = 0; pass < 2; pass++)
        {
            float g = pass == 0 ? 2.5f * s : 0;
            var tip = at[i] + d * (size + g);
            var back = at[i] - d * (size * 0.6f);
            chev[0] = tip;
            chev[1] = back + n * (size + g);
            chev[2] = back + n * (size + g) - d * th;
            chev[3] = tip - d * (th * 1.6f + g * 0.5f);
            chev[4] = back - n * (size + g) - d * th;
            chev[5] = back - n * (size + g);
            var c = pass == 0 ? new Color(0.02f, 0.04f, 0.06f, 0.75f) : new Color(Mathf.Min(1, col[i].R), Mathf.Min(1, col[i].G), Mathf.Min(1, col[i].B), pulse);
            DrawColoredPolygon(chev, c);
        }
    }
}
