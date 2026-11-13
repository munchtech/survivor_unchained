using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>bd-ui W3: her auto skills as small square tiles over the bar's top line, left of the coin (the rule: round for
/// what she acts by, square for what fires by itself). Her three auto slots grow leftward from the coin; the great
/// uniques' item autos continue after them (a bezel in the item's rarity color), the 5th place "+N" when more than two.
/// Each tile carries the skill's glyph and its own timer (the not-yet-ready share darkened, clockwise from 12, and a
/// 0.25 s brightening when it fires). Places and the sweep's math: AutoRowModel. A child of Instrument, in its space.</summary>
public partial class AutoRow : Control
{
    static readonly Color Glass = new(0.03f, 0.06f, 0.065f), Bronze = new("#d3a464"), Veil = new(0.02f, 0.015f, 0.01f, 0.62f);
    const float GlyphPx = 22;

    sealed class Tile
    {
        public AutoRowModel.Place At;
        public string Id = "";
        public int Slot = -1, Rarity = -1;
        public bool Locked;
        public double Ready = 1, Last = 1, Fired = -1;
        public Texture2D? Glyph;
        public Color School = Colors.White;
    }

    readonly List<Tile> tiles = new();
    double now;
    bool dirty = true;
    string lastShape = "";
    /// <summary>The hidden item autos' names ("+N" hover).</summary>
    public IReadOnlyList<string> HiddenNames => hidden;
    List<string> hidden = new();

    public AutoRow()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Linear;
        Position = new Vector2(AutoRowModel.Floor, DgPanel.TopY + 1 - AutoRowModel.Tile);
        Size = new Vector2(AutoRowModel.HerRight - AutoRowModel.Floor, AutoRowModel.Tile);
        ZIndex = 2;
    }

    /// <summary>What the bar holds now, each frame (values only; it redraws on change). itemRarity: the skills her gear
    /// grants as autos, by the granting piece's rarity.</summary>
    public void Feed(Battle b, int level, IReadOnlyDictionary<string, int> itemRarity)
    {
        int open = SurvivorUnchained.Rpg.SkillBook.AutosAt(Math.Max(1, level));
        var hers = new List<WeaponInst>();
        var items = new List<WeaponInst>();
        foreach (var w in b.Weapons.OrderBy(w => w.Slot))
        {
            if (w.Slot < Weapons.MaxKeys) continue;
            // (an item auto: a skill her gear grants, or anything past her three slots; her own take the first three places)
            if (itemRarity.ContainsKey(w.Id) || w.Slot >= Weapons.MaxKeys + AutoRowModel.HerSlots) items.Add(w);
            else if (hers.Count < AutoRowModel.HerSlots) hers.Add(w);
            else items.Add(w);
        }
        var places = AutoRowModel.Places(items.Count);
        // (rebuilt only when the places or what is in them changed; the timers below are values)
        string shape = string.Join(",", places.Select(p => $"{p.Kind}{p.Index}")) + "|" + string.Join(",", hers.Concat(items).Select(w => w.Id)) + "|" + open;
        if (shape != lastShape)
        {
            lastShape = shape;
            var old = tiles.Where(t => t.Id != "").GroupBy(t => t.Id).ToDictionary(g => g.Key, g => g.First(), StringComparer.Ordinal);
            tiles.Clear();
            hidden = items.Count > AutoRowModel.ItemX.Length ? items.Skip(1).Select(w => w.Def.Name).ToList() : new();
            foreach (var p in places)
            {
                var t = new Tile { At = p };
                WeaponInst? w = p.Kind switch { AutoRowModel.Kind.Her => p.Index < hers.Count ? hers[p.Index] : null, AutoRowModel.Kind.Item => items[p.Index], _ => null };
                if (p.Kind == AutoRowModel.Kind.Her) t.Locked = w == null && p.Index >= open;
                if (w != null)
                {
                    t.Id = w.Id; t.Slot = w.Slot;
                    t.School = ItemViews.SchoolColors[w.School];
                    t.Glyph = Glyphs.Texture(Glyphs.ForSkill(w.Id, w.Art), (int)GlyphPx, t.School);
                    t.Rarity = p.Kind == AutoRowModel.Kind.Item ? itemRarity.GetValueOrDefault(w.Id, 4) : -1;
                    if (old.TryGetValue(w.Id, out var o)) { t.Ready = o.Ready; t.Last = o.Last; t.Fired = o.Fired; }
                }
                tiles.Add(t);
            }
            dirty = true;
        }
        var all = hers.Concat(items).ToDictionary(w => w.Id, w => w, StringComparer.Ordinal);
        foreach (var t in tiles)
        {
            if (t.Id == "" || !all.TryGetValue(t.Id, out var w)) continue;
            double r = b.WeaponReady(w);
            if (AutoRowModel.Fired(t.Last, r)) t.Fired = now;
            if (Math.Abs(r - t.Ready) > 0.004) dirty = true;
            t.Ready = r; t.Last = r;
        }
    }

    public override void _Process(double delta)
    {
        now += delta;
        bool flashing = false;
        foreach (var t in tiles) if (t.Fired >= 0 && AutoRowModel.Flash(now - t.Fired) > 0) flashing = true;
        if (flashing || dirty) { dirty = false; QueueRedraw(); }
    }

    Rect2 Local(Tile t) => new(t.At.X - Position.X, 0, AutoRowModel.Tile, AutoRowModel.Tile);

    /// <summary>The tile under a global point: its skill id (empty for an empty place), its slot, whether it is "+N", and
    /// its global rect; null when none.</summary>
    public (string Id, int Slot, bool More, Rect2 Rect)? TileAt(Vector2 global)
    {
        var xf = GetGlobalTransform();
        var local = xf.AffineInverse() * global;
        foreach (var t in tiles)
            if (Local(t).HasPoint(local)) return (t.Id, t.Slot, t.At.Kind == AutoRowModel.Kind.More, xf * Local(t));
        return null;
    }

    /// <summary>Tile k's (in the places' order) the same, for the pins.</summary>
    public (string Id, int Slot, bool More, Rect2 Rect)? TileNo(int k)
    {
        if (k < 0 || k >= tiles.Count) return null;
        var t = tiles[k];
        return (t.Id, t.Slot, t.At.Kind == AutoRowModel.Kind.More, GetGlobalTransform() * Local(t));
    }

    public override void _Draw()
    {
        foreach (var t in tiles)
        {
            var r = Local(t);
            bool more = t.At.Kind == AutoRowModel.Kind.More, filled = t.Id != "" || more;
            // (a locked place: the empty square at 35%; an open one with nothing in it: the bezel only, faint)
            float fillA = filled ? 1 : t.Locked ? 0.35f : 0;
            if (fillA > 0) DrawRect(r, Glass with { A = fillA }, true);
            if (t.Id != "")
            {
                float fl = AutoRowModel.Flash(now - t.Fired);
                DrawRect(r.Grow(-1), t.School with { A = 0.16f + 0.5f * fl }, true);
                if (t.Glyph != null)
                {
                    var g = new Rect2(r.GetCenter() - Vector2.One * GlyphPx / 2, Vector2.One * GlyphPx);
                    DrawTextureRect(t.Glyph, g, false, new Color(1 + 0.6f * fl, 1 + 0.6f * fl, 1 + 0.6f * fl));
                }
                float share = AutoRowModel.NotReady(t.Ready);
                if (share > 0.004f) DrawColoredPolygon(Pie(r.Grow(-1), share), Veil);
            }
            else if (more)
                DrawString(Style.UiBold, new Vector2(r.Position.X, r.Position.Y + 21), $"+{t.At.Index}", HorizontalAlignment.Center, r.Size.X, 15, Style.RarityOf(4));
            Color bez = t.Rarity >= 0 ? Style.RarityOf(t.Rarity) : more ? Style.RarityOf(4) : Bronze;
            float bezA = filled ? 1 : t.Locked ? 0.35f : 0.4f;
            DrawRect(r, bez with { A = bezA }, false, 1);
        }
    }

    /// <summary>The wedge of a square from 12 o'clock clockwise, share (0..1) of the turn.</summary>
    static Vector2[] Pie(Rect2 r, float share)
    {
        var c = r.GetCenter();
        var pts = new List<Vector2> { c };
        float h = r.Size.X / 2;
        int n = Math.Max(2, (int)Math.Ceiling(share * 90));
        for (int i = 0; i <= n; i++)
        {
            float ang = share * Mathf.Tau * i / n;                 // clockwise from 12
            var d = new Vector2(Mathf.Sin(ang), -Mathf.Cos(ang));
            float k = h / Math.Max(Math.Abs(d.X), Math.Abs(d.Y));  // the ray to the square's edge
            pts.Add(c + d * k);
        }
        return pts.ToArray();
    }
}
