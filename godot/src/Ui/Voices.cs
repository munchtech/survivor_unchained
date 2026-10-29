using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using Style = SurvivorUnchained.Ui.Style;

namespace SurvivorUnchained.View;

/// <summary>
/// Words over heads (the web game's hud/barks): names over the people who
/// live here, with a mark when someone has something for you, drawn in the
/// world at a fixed size on screen; and things said to the air, over the
/// speaker's head, that rise a little and fade. Those are drawn on the screen
/// (under the HUD) so that they never cross: one speaker says one line at a
/// time, the next waiting its turn; lines from different speakers stack, the
/// newer moved up clear of the older.
/// </summary>
public partial class Voices : Node3D
{
    static Font? display, ui;
    readonly Dictionary<string, (Label3D Name, Label3D Mark)> plates = new();

    /// <summary>A line on screen: who says it (its queue), where in the world, how long it lives.</summary>
    sealed class Said
    {
        public required Control Box;
        public required string Key;
        public required Vector3 At;
        public required string Text;
        public double T, Life;
        /// <summary>0..1: whether its speaker's head is on the screen (eased over 0.25 s); the anchor it follows (smoothed).</summary>
        public float Vis;
        public Vector2? Anchor;
        /// <summary>How far it is moved up to stand clear of the lines before it (eased).</summary>
        public float Lift;
        public float? Pick;
        /// <summary>Its shot under a live tip was asked for (--shot only).</summary>
        public bool Shot;
        public bool HudLogged;
    }
    static int barkTipShots;

    /// <summary>A line waiting for its speaker's last to finish.</summary>
    sealed record Waiting(string Text, Vector3 At, string? Speaker, bool Alert, string? Voice, Func<double>? Shown);

    readonly List<Said> barks = new();
    /// <summary>Combat's floaters standing now (a "blocked"), where they stand on the screen and until when:
    /// a line shown while one stands is lifted clear of it, as of an older line.</summary>
    readonly List<(Rect2 R, double Until)> floaters = new();
    double now;
    readonly Dictionary<string, Queue<Waiting>> waiting = new();
    CanvasLayer? layer;
    /// <summary>A conversation is on: the names and words step back.</summary>
    public bool Quiet;
    /// <summary>The close view of her is in (GameCloseUp): the names step away (eased out, back at once), so
    /// none floats beside her head.</summary>
    public bool Away;
    /// <summary>No name plates or quest marks at all (set by shots that must keep the frame clear; Away and Quiet are driven by the game).</summary>
    public bool Bare;
    float plateK = 1;
    /// <summary>Per plate: how far it has stepped aside (0 standing, 1 gone) for its own speaker's bark. The
    /// bark names the speaker already, and the plate's letters showed through the words (UI 16 MR2).</summary>
    readonly Dictionary<string, float> aside = new();
    static readonly bool platesOld = OS.GetCmdlineUserArgs().Contains("--plates-old");

    public Voices() { Name = "Voices"; }

    static Label3D Label(Font font, int size, Color color)
    {
        var l = new Label3D
        {
            Font = font, FontSize = size, Modulate = color, OutlineSize = 8, OutlineModulate = new Color(0.02f, 0.015f, 0.01f, 0.9f),
            Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true, FixedSize = true, PixelSize = 0.0007f,
            Shaded = false, RenderPriority = 20, OutlineRenderPriority = 19, DoubleSided = true,
        };
        return l;
    }

    public override void _Ready()
    {
        display ??= GD.Load<Font>("res://art/fonts/cinzel-600.woff2");
        ui ??= GD.Load<Font>("res://art/fonts/alegreya-sans-500.woff2");
    }

    /// <summary>The names to show now (near the survivor): the rest go.</summary>
    // What each plate says now, so its words are made and set only when they
    // change (every frame for everyone was a frame's worth of garbage), and
    // the sets kept from frame to frame.
    readonly Dictionary<string, (string Name, string? Role, char? Marker)> said = new();
    readonly HashSet<string> keep = new();
    readonly List<string> gone = new();

    public void Plates(List<Plate> list)
    {
        keep.Clear();
        foreach (var p in list)
        {
            keep.Add(p.Id);
            if (!plates.TryGetValue(p.Id, out var pl))
            {
                pl = (Label(display!, 22, new Color("#e8dcc4")), Label(display!, 34, new Color("#f3d9a0")));
                AddChild(pl.Name);
                AddChild(pl.Mark);
                plates[p.Id] = pl;
                said.Remove(p.Id);
            }
            if (!said.TryGetValue(p.Id, out var was) || was.Name != p.Name || was.Role != p.Role || was.Marker != p.Marker)
            {
                said[p.Id] = (p.Name, p.Role, p.Marker);
                pl.Name.Text = p.Role != null ? $"{p.Name}\n{p.Role}" : p.Name;
                pl.Mark.Text = p.Marker?.ToString() ?? "";
                pl.Mark.Visible = p.Marker != null;
                // The mark stands clear above the name, however many lines the name has: a fixed-size
                // plate is measured on the screen, so the gap is in its pixels, not the world's (a
                // world-space lift let the "!" fall into a two-line name and read as one of its letters).
                pl.Mark.Offset = new Vector2(0, (p.Role != null ? 2 : 1) * 15 + 26);
            }
            var at = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            if (pl.Name.Position != at)
            {
                pl.Name.Position = at;
                pl.Mark.Position = at;
            }
        }
        gone.Clear();
        foreach (var id in plates.Keys) if (!keep.Contains(id)) gone.Add(id);
        foreach (var id in gone) { plates[id].Name.QueueFree(); plates[id].Mark.QueueFree(); plates.Remove(id); said.Remove(id); aside.Remove(id); }
    }

    /// <summary>Something said to the air, over someone's head. Their line before
    /// still showing, it waits its turn (the same words again only keep that
    /// one up longer); `shown` runs when it shows (a named voice heard then,
    /// returning how long it speaks).</summary>
    public void Bark(string text, Vector3 at, string? speaker = null, bool alert = false, string? voice = null, Func<double>? shown = null)
    {
        // Whose turn it is: a named speaker's own; else whatever stands there.
        string key = speaker ?? $"@{Mathf.RoundToInt(at.X / 3)},{Mathf.RoundToInt(at.Z / 3)}";
        if (barks.FirstOrDefault(b => b.Key == key) is { } now)
        {
            if (now.Text == text) { now.Life = Math.Max(now.Life, now.T + 1.6); return; }
            // The line showing stays only until it has been read (a scene's lines keep near their beats);
            // an alert is only ever about now, so the newer takes its place at once.
            now.Life = Math.Max(now.T + 0.25, Math.Min(now.Life, alert ? 0 : 1.0 + now.Text.Length * 0.045));
            if (!waiting.TryGetValue(key, out var q)) waiting[key] = q = new();
            if (q.Any(w => w.Text == text)) return;
            q.Enqueue(new Waiting(text, at, speaker, alert, voice, shown));
            // (a speaker who says too much drops what is oldest unsaid, not what is newest)
            while (q.Count > 3) q.Dequeue();
            return;
        }
        Show(key, new Waiting(text, at, speaker, alert, voice, shown));
    }

    /// <summary>A bark's width: one line if it fits 460 px; else the narrowest width giving the same number of
    /// lines with the last no shorter than a third of the first (no lone word on a line of its own).</summary>
    static float BarkWidth(string text, int size)
    {
        float One(string t) => Style.Ui.GetStringSize(t, HorizontalAlignment.Left, -1, size).X;
        float tw = One(text);
        if (tw + 8 <= 460) return tw + 8;
        var words = text.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        int n = (int)Math.Ceiling((tw + 8) / 460);
        for (float width = tw / n + 8; width <= 460; width += 6)
        {
            var lines = new List<string>(); string cur = "";
            foreach (var wd in words)
            {
                string t = cur == "" ? wd : cur + " " + wd;
                if (cur != "" && One(t) > width - 8) { lines.Add(cur); cur = wd; } else cur = t;
            }
            lines.Add(cur);
            bool dangling = lines.Take(lines.Count - 1).Any(l => { var e = l.Split(' ')[^1].ToLowerInvariant(); return e is "a" or "an" or "the"; });
            if (!dangling && lines.Count <= n && (lines.Count == 1 || One(lines[^1]) >= One(lines[0]) * 0.33f && lines[^1].Contains(' '))) return width;
        }
        return 460;
    }

    void Show(string key, Waiting w)
    {
        if (layer == null) { layer = new CanvasLayer { Layer = 5 }; AddChild(layer); }
        var box = Style.V(0);
        box.MouseFilter = Control.MouseFilterEnum.Ignore;
        // A named speaker's name over their words, small and gold; the words in the hand.
        if (w.Speaker != null)
            box.AddChild(Style.Label(w.Speaker.ToUpperInvariant(), Style.UiHeavy, 15, new Color("#e0b868"), false, HorizontalAlignment.Center));
        var words = Style.Label(w.Text, Style.Ui, w.Alert ? 26 : 23, w.Alert ? new Color("#ffd07a") : new Color("#f0e6d2"), true, HorizontalAlignment.Center);
        words.AddThemeConstantOverride("outline_size", 7);
        words.AddThemeColorOverride("font_outline_color", new Color(0.02f, 0.015f, 0.01f, 0.92f));
        words.CustomMinimumSize = new Vector2(BarkWidth(w.Text, w.Alert ? 26 : 23), 0);
        box.AddChild(words);
        box.Modulate = new Color(1, 1, 1, 0);
        layer.AddChild(box);
        double life = Mathf.Clamp(2.2 + w.Text.Length * 0.05, 2.5, 6);
        // Heard, too, from where they stand (a named voice in a fight is the
        // game's to play, over everything; a caption is never spoken).
        if (!w.Alert && w.Speaker == null && Sound.VoiceOver.Instance?.Bark(w.Text, this, w.At, w.Voice) is double said and > 0)
            life = Mathf.Max(life, said + 0.8);
        if (w.Shown?.Invoke() is double spoken and > 0) life = Mathf.Max(life, spoken + 0.6);
        barks.Add(new Said { Box = box, Key = key, At = w.At, Text = w.Text, Life = life });
        // Not too many at once: the oldest go first.
        while (barks.Count > 6) { barks[0].Box.QueueFree(); barks.RemoveAt(0); }
    }

    public void Clear()
    {
        foreach (var b in barks) b.Box.QueueFree();
        barks.Clear();
        waiting.Clear();
        Plates(new());
    }

    /// <summary>A combat floater (a "blocked": damage numbers' family, short-lived, at the hit) kept off every
    /// line being said (UI note 1, 26 Oct: it printed into the Warden's bark): moved down under a box its
    /// footprint (worldW by worldH metres, rising `rise` over `life` seconds) would cross; false when there
    /// is no room under it on the screen, and it is better not shown.</summary>
    public bool ClearOfLines(ref Vector3 at, float worldW, float worldH, float rise, double life)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null || cam.IsPositionBehind(at)) return true;
        var p = cam.UnprojectPosition(at);
        var up = cam.UnprojectPosition(at + Vector3.Up * (worldH / 2 + rise));
        var down = cam.UnprojectPosition(at - Vector3.Up * worldH / 2);
        float half = (cam.UnprojectPosition(at + cam.GlobalBasis.X * worldW / 2) - p).Length();
        float above = p.Y - up.Y, below = down.Y - p.Y;
        Rect2 Foot(Vector2 c) => new(c.X - half, c.Y - above, half * 2, above + below);
        var boxes = barks.Where(b => b.Box.Visible && b.T > 0).Select(b => new Rect2(b.Box.Position, b.Box.Size).Grow(6)).ToList();
        bool moved = false;
        for (int pass = 0; pass < 4; pass++)
        {
            var f = Foot(p);
            var hit = boxes.FirstOrDefault(r => r.Intersects(f));
            if (hit.Size == Vector2.Zero) break;
            p.Y = hit.End.Y + above;
            moved = true;
        }
        if (Foot(p).End.Y > GetViewport().GetVisibleRect().Size.Y - 8 || boxes.Any(r => r.Intersects(Foot(p)))) return false;
        if (moved)
        {
            float depth = (at - cam.GlobalPosition).Dot(-cam.GlobalBasis.Z);
            at = cam.ProjectPosition(p, depth);
        }
        floaters.Add((Foot(p), now + life));
        return true;
    }

    public override void _Process(double delta)
    {
        now += delta;
        floaters.RemoveAll(f => f.Until <= now);
        float quiet = Quiet ? 0 : 1;
        plateK = Away ? Mathf.Max(0, plateK - (float)delta / 0.4f) : 1;
        float pk = Bare ? 0 : quiet * plateK;
        // A boss's own plate stands down while its bar is up: the bar already names it, and over the fight the
        // plate fell onto the instrument (UI notes r3 judge, 27 Oct).
        foreach (var (id, (n, m)) in plates)
        {
            float k2 = Ui.GameHud.BossName is { } bn && said.TryGetValue(id, out var sw) && string.Equals(sw.Name, bn, StringComparison.OrdinalIgnoreCase) ? 0 : pk;
            // (its own speaker's bark is up: the plate and its quest mark fade out over 0.2 s, back after)
            bool talking = barks.Any(b => b.T < b.Life && new Vector2(b.At.X - n.Position.X, b.At.Z - n.Position.Z).LengthSquared() < 1.2f * 1.2f);
            float ow = aside.GetValueOrDefault(id);
            aside[id] = ow = Mathf.Clamp(ow + (talking ? 1 : -1) * (float)delta / 0.2f, 0, 1);
            k2 *= 1 - ow;
            n.Transparency = 1 - k2; m.Transparency = 1 - k2; n.Visible = k2 > 0;
        }
        for (int i = barks.Count - 1; i >= 0; i--)
        {
            var b = barks[i];
            b.T += delta;
            if (b.T < b.Life) continue;
            b.Box.QueueFree();
            barks.RemoveAt(i);
            // That speaker's next line, now theirs is done.
            if (waiting.TryGetValue(b.Key, out var q) && q.Count > 0) Show(b.Key, q.Dequeue());
        }
        Place(delta, quiet);
    }

    /// <summary>Each line over its speaker's head, as the camera sees them now, the
    /// older first; a newer one that would cross an older is lifted clear of it.</summary>
    float barkMinGap = float.MaxValue;
    void Place(double delta, float quiet)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null) return;
        var placed = new List<Rect2>();
        // The name plates first, as they stand on the screen: a line never prints over someone's name
        // (crafting's finding at the forge); it is lifted clear of it as of an older line.
        if (display != null && plates.Count > 0)
        {
            float vpH = GetViewport().GetVisibleRect().Size.Y;
            // (a fixed-size Label3D's font pixel on the screen)
            float k = 0.0007f / (2 * Mathf.Tan(Mathf.DegToRad(cam.Fov) / 2)) * vpH;
            foreach (var (pid, (n, m)) in plates)
            {
                // (a plate stepping aside for its own speaker's bark is no obstacle to it)
                if (aside.GetValueOrDefault(pid) > 0) continue;
                if (!n.Visible || n.Text == "" || cam.IsPositionBehind(n.Position)) continue;
                var c = cam.UnprojectPosition(n.Position);
                var lines = n.Text.Split('\n');
                float w = lines.Max(l => display.GetStringSize(l, HorizontalAlignment.Left, -1, n.FontSize).X) * k, h = lines.Length * n.FontSize * 1.3f * k;
                // A name never runs off the screen: moved in (label pixels) to stand at least 24 px inside the viewport.
                float vpW = GetViewport().GetVisibleRect().Size.X, dx = 0;
                if (c.X - w / 2 < 24) dx = 24 - (c.X - w / 2);
                else if (c.X + w / 2 > vpW - 24) dx = vpW - 24 - (c.X + w / 2);
                n.Offset = n.Offset with { X = dx / k };
                m.Offset = m.Offset with { X = dx / k };
                c.X += dx;
                // Nor half off the top or the foot of the screen, nor under the top-right block (the minimap, the
                // place, the objectives): it fades out over the last 40 px before it would be cut or covered.
                var box = new Rect2(c - new Vector2(w / 2, h / 2), new Vector2(w, h));
                // (--plates-old: as before UI 16, for before/after pictures)
                if (platesOld) { placed.Add(box.Grow(4)); continue; }
                if (m.Visible && m.Text != "") box = box.Expand(c - new Vector2(0, m.Offset.Y * k + m.FontSize * k / 2));
                float edge = Mathf.Clamp(Mathf.Min(box.Position.Y - 4, vpH - 4 - box.End.Y) / 40f, 0, 1);
                if (Ui.GameHud.Header is Rect2 hd)
                {
                    float sx = vpW / 1920f;
                    var hr = new Rect2(hd.Position * sx, hd.Size * sx).Grow(6);
                    // (how far clear of the block: the larger of the gaps across and down; 0 inside it)
                    float gap = Mathf.Max(Mathf.Max(hr.Position.X - box.End.X, box.Position.X - hr.End.X), Mathf.Max(hr.Position.Y - box.End.Y, box.Position.Y - hr.End.Y));
                    edge = Mathf.Min(edge, Mathf.Clamp(gap / 40f, 0, 1));
                }
                if (edge < 1)
                {
                    n.Transparency = 1 - (1 - n.Transparency) * edge; m.Transparency = 1 - (1 - m.Transparency) * edge;
                    if (edge <= 0) { n.Visible = false; continue; }
                }
                placed.Add(new Rect2(c - new Vector2(w / 2, h / 2), new Vector2(w, h)).Grow(4));
                if (m.Visible) placed.Add(new Rect2(c - new Vector2(m.FontSize * k / 2, m.Offset.Y * k + m.FontSize * k / 2), new Vector2(m.FontSize * k, m.FontSize * k)));
            }
        }
        // (and combat's floaters: a line said while a "blocked" stands is lifted clear of it)
        foreach (var f in floaters) placed.Add(f.R);
        // (and the top-right block, the minimap over the place and the objectives: a bark never stands in it)
        if (Ui.GameHud.Header is Rect2 hdr) { float sx = GetViewport().GetVisibleRect().Size.X / 1920f; placed.Add(new Rect2(hdr.Position * sx, hdr.Size * sx).Grow(6)); }
        float ease = 1 - Mathf.Exp(-10f * (float)delta);
        var barkRects = new List<Rect2>();
        foreach (var b in barks)
        {
            var head = b.At + Vector3.Up * 2.1f;
            if (cam.IsPositionBehind(head)) { b.Vis = 0; b.Box.Visible = false; b.Anchor = null; continue; }
            var size = b.Box.GetCombinedMinimumSize();
            var vp = GetViewport().GetVisibleRect().Size;
            var hp = cam.UnprojectPosition(head);
            // (only while his head is on the screen is the bark shifted in to fit; once it leaves, the bark fades out over 0.25 s)
            bool onScreen = hp.X >= 16 && hp.X <= vp.X - 16 && hp.Y >= 0 && hp.Y <= vp.Y;
            b.Vis = Mathf.Clamp(b.Vis + (onScreen ? 1 : -1) * (float)delta / 0.25f, 0, 1);
            if (b.Vis <= 0) { b.Box.Visible = false; b.Anchor = null; continue; }
            b.Box.Visible = true;
            // (following the head, smoothed: no jitter)
            b.Anchor = b.Anchor is Vector2 prev ? prev.Lerp(hp, ease) : hp;
            // (rising a little as it is said)
            var at = b.Anchor.Value - new Vector2(size.X / 2, size.Y + (float)Math.Min(b.T, 3) * 6);
            // A speaker at the top of the screen says it under their feet, not under the HUD's bars
            // nor over the name of the move they make (held just under the bars: Hits.UnderTheBars).
            float top = Ui.GameHud.TopClear + 66;
            if (at.Y < top) at.Y = Math.Max(top, hp.Y + 14);
            at.X = Mathf.Clamp(at.X, 16, GetViewport().GetVisibleRect().Size.X - 16 - size.X);
            // Never inside the banner's words, nor beside them on their line (read across, a howl's
            // caption and the banner's title made one sentence): under them (over them is the boss's bar).
            if (Ui.GameHud.Banner is Rect2 band && band.GrowIndividual(140, 6, 140, 6).Intersects(new Rect2(at, size))) at.Y = band.End.Y + 10;
            // Under a live tip by 24 px at the least (never over its words).
            float floor = Ui.GameHud.TipBottom > 0 ? Ui.GameHud.TipBottom + 24 : 0;
            if (at.Y < floor) at.Y = floor;
            // (--shot: a bark placed under a live tip, a frame of it a moment on, up to three)
            if (floor > 0 && !b.Shot && barkTipShots < 3 && Args.Has("shot")) { b.Shot = true; Shots.Want($"barktip_{++barkTipShots}", 0.2); }
            // Clear of every other line, plate and floater by 12 px at the least: the natural spot if it is
            // clear, else (the one it took last time if still clear, so it never flips) the nearest spot just
            // above or below something in the way.
            float vpH2 = GetViewport().GetVisibleRect().Size.Y, lo = Math.Max(8, floor);
            // Never over the Drowned Girl: the box's bottom 8 px above the HUD's highest top across its whole width
            // (UI 20: a boss behind the HUD's foot barked onto the hair's river). This wins over the natural spot
            // and over the tip's floor; the clear-of-others pass below keeps to it too.
            float hk = vpH2 / 1080f, low = vpH2 - 8;
            if (Hits.HudTopOver(at.X / hk, (at.X + size.X) / hk) is float hudTop)
            {
                low = Math.Min(low, hudTop * hk - 8);
                if (at.Y + size.Y > low)
                {
                    if (!b.HudLogged) { b.HudLogged = true; GD.Print($"bark: '{b.Text}' x {at.X:0}-{at.X + size.X:0} lifted from y {at.Y:0} (bottom {at.Y + size.Y:0}) to {low - size.Y:0} (bottom {low:0}), HUD top {hudTop * hk:0}"); }
                    at.Y = low - size.Y;
                    lo = Math.Min(lo, at.Y);
                }
            }
            bool Clear(float y) { var r = new Rect2(at.X, y, size.X, size.Y).Grow(6); return y >= lo - 0.5f && y + size.Y <= low + 0.5f && !placed.Any(p => p.Intersects(r)); }
            float pick = at.Y;
            if (!Clear(pick))
            {
                if (b.Pick is float pv && Clear(pv)) pick = pv;
                else
                {
                    float best = float.MaxValue, bestY = at.Y;
                    foreach (var p in placed)
                        foreach (var y in new[] { p.Position.Y - 12 - size.Y, p.End.Y + 12 })
                            if (Clear(y) && Math.Abs(y - at.Y) < best) { best = Math.Abs(y - at.Y); bestY = y; }
                    pick = bestY;
                }
            }
            b.Pick = pick == at.Y ? null : pick;
            float want = at.Y - pick;
            b.Lift = b.T < 0.05 ? want : Mathf.Lerp(b.Lift, want, ease);
            b.Box.Position = at - new Vector2(0, b.Lift);
            b.Box.Size = size;
            placed.Add(new Rect2(at - new Vector2(0, want), size).Grow(6));
            if (Args.Has("shot")) { var me = new Rect2(at - new Vector2(0, want), size); foreach (var o in barkRects) { float gx = Math.Max(o.Position.X - me.End.X, me.Position.X - o.End.X), gy = Math.Max(o.Position.Y - me.End.Y, me.Position.Y - o.End.Y); float g = Math.Max(gx, gy); if (g < barkMinGap) { barkMinGap = g; GD.Print($"[bark-gap] min {g:0.0} px me {me} other {o} lift {b.Lift:0.0} want {want:0.0} T {b.T:0.00} ({b.Text.Length} chars, {b.Box.GetCombinedMinimumSize().Y:0} px tall)"); } } barkRects.Add(me); }
            float a = (float)Mathf.Min(1, Mathf.Min(b.T / 0.2, (b.Life - b.T) / 0.6)) * quiet * b.Vis;
            b.Box.Modulate = new Color(1, 1, 1, a);
        }
    }
}
