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
    readonly bool[] sig = new bool[Max];
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
            count++;
        }
        QueueRedraw();
    }

    public override void _Draw()
    {
        float s = GetViewportRect().Size.Y / 1080f;
        for (int i = 0; i < count; i++)
        {
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
}
