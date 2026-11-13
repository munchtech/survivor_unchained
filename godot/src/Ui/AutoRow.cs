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
    const float GlyphPx = 28;

    sealed class Tile
    {
        public AutoRowModel.Place At;
        public string Id = "";
        public int Slot = -1, Rarity = -1;
        public bool Locked;
        public double Ready = 1, Last = 1, Fired = -1, Opened = -1;
        public Texture2D? Glyph;
        public Color School = Colors.White;
    }

    /// <summary>bd-ui W4: the row's top, its bottom 3 px above the key caps' top edge (the tallest chip, the mouse's).</summary>
    public static float RowTop => AutoRowModel.RowTop(DgPanel.TopY, DgPanel.Seat(0).Y, DgPanel.SeatR, KeyTag.MouseChip);

    /// <summary>bd-ui W5: the stance block's Swap chip's right edge when the block is shown (else null): the item tiles start 10 px after.</summary>
    public float? StanceRight;
    float ItemStart => AutoRowModel.ItemStart(StanceRight != null, StanceRight ?? 0);

    readonly List<Tile> tiles = new();
    string lastLog = "";
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
        Position = new Vector2(AutoRowModel.Floor, RowTop);
        Size = new Vector2(AutoRowModel.RightEdge - AutoRowModel.Floor, AutoRowModel.Tile);
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
        int cap = AutoRowModel.ItemCapacity(ItemStart);
        var places = AutoRowModel.Places(items.Count, ItemStart);
        if (Position.Y != RowTop) Position = new Vector2(Position.X, RowTop);
        if (Args.Has("dev-log") || Args.Has("hud-pin") || Args.Has("equip") || Args.Has("hud-scale"))
        {
            string log = $"autorow: her {hers.Count} items {items.Count} ({string.Join(",", items.Select(w => w.Id))}) rarities {itemRarity.Count} bar {string.Join(",", b.Weapons.Where(w => w.Slot >= Weapons.MaxKeys).Select(w => w.Id + "@" + w.Slot))}";
            if (log != lastLog) { lastLog = log; GD.Print(log); }
        }
        // (rebuilt only when the places or what is in them changed; the timers below are values)
        string shape = string.Join(",", places.Select(p => $"{p.Kind}{p.Index}@{p.X}")) + "|" + string.Join(",", hers.Concat(items).Select(w => w.Id)) + "|" + open;
        if (shape != lastShape)
        {
            lastShape = shape;
            var old = tiles.Where(t => t.Id != "").GroupBy(t => t.Id).ToDictionary(g => g.Key, g => g.First(), StringComparer.Ordinal);
            tiles.Clear();
            hidden = items.Count > cap ? items.Skip(Math.Max(0, cap - 1)).Select(w => w.Def.Name).ToList() : new();
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
        foreach (var t in tiles) if ((t.Fired >= 0 && AutoRowModel.Flash(now - t.Fired) > 0) || (t.Opened >= 0 && now - t.Opened < 0.6)) flashing = true;
        if (flashing || dirty) { dirty = false; QueueRedraw(); }
    }

    /// <summary>Tile k's (the places' order) global rect; null when there is none.</summary>
    public Rect2? TileRect(int k) => TileNo(k)?.Rect;

    /// <summary>The place holding the skill on this slot (the card that opened it folds there); -1 none.</summary>
    public int TileOfSlot(int slot)
    {
        for (int i = 0; i < tiles.Count; i++) if (tiles[i].Id != "" && tiles[i].Slot == slot) return i;
        return -1;
    }

    /// <summary>The level card folded into tile k: a brief light (0.6 s).</summary>
    public void Opened(int k) { if (k >= 0 && k < tiles.Count) { tiles[k].Opened = now; dirty = true; } }

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
            Color bez = t.Rarity >= 0 ? Style.RarityOf(t.Rarity) : more ? Style.RarityOf(4) : Bronze;
            if (t.Id != "")
            {
                // (always live: the icon at full brightness; the timer is the 2 px bar; a fire brightens the whole tile 1.35 -> 1.0)
                float lit = 1 + 0.35f * AutoRowModel.Flash(now - t.Fired);
                DrawRect(r.Grow(-1), (t.School with { A = 0.16f }) * new Color(lit, lit, lit, 1), true);
                if (t.Glyph != null)
                {
                    var g = new Rect2(r.GetCenter() - Vector2.One * GlyphPx / 2, Vector2.One * GlyphPx);
                    DrawTextureRect(t.Glyph, g, false, new Color(lit, lit, lit));
                }
                float ready = 1 - AutoRowModel.NotReady(t.Ready);
                if (ready > 0.004f) DrawRect(new Rect2(r.Position.X + 3, r.End.Y - 4, (r.Size.X - 6) * ready, 2), bez with { A = 0.85f }, true);
            }
            else if (more)
                DrawString(Style.UiBold, new Vector2(r.Position.X, r.Position.Y + 21), $"+{t.At.Index}", HorizontalAlignment.Center, r.Size.X, 15, Style.RarityOf(4));
            if (t.Opened >= 0 && now - t.Opened < 0.6)
                DrawRect(r.Grow(-1), new Color(1f, 0.80f, 0.45f, 0.55f * (float)(1 - (now - t.Opened) / 0.6)), true);
            // (the bezel as the seats': a 1 px dark outer line, a 1.5 px bronze / rarity inner line)
            float bezA = filled ? 1 : t.Locked ? 0.35f : 0.4f;
            DrawRect(r.Grow(-0.5f), new Color("#1a120a") with { A = 0.8f * bezA }, false, 1);
            DrawRect(r.Grow(-1.75f), bez with { A = bezA }, false, 1.5f);
        }
    }
}

/// <summary>bd-ui W4: a texture clipped to a circle, drawn as a textured polygon (no shader): the item icons in the weapon-set
/// discs and the stance card's ring.</summary>
public static class DiscIcon
{
    public static void Draw(CanvasItem ci, Vector2 c, float r, Texture2D tex, Color mod, float inset = 0)
    {
        const int N = 40;
        var pts = new Vector2[N];
        var uv = new Vector2[N];
        var cols = new Color[N];
        float k = 1 - inset;
        for (int i = 0; i < N; i++)
        {
            var d = new Vector2(Mathf.Cos(Mathf.Tau * i / N), Mathf.Sin(Mathf.Tau * i / N));
            pts[i] = c + d * r;
            uv[i] = new Vector2(0.5f, 0.5f) + d * 0.5f * k;
            cols[i] = mod;
        }
        ci.DrawPolygon(pts, cols, uv, tex);
    }

    /// <summary>What she wears in a slot as a drawable: its icon key (null: nothing worn) and its real texture if there is one.</summary>
    public static (string? Key, Texture2D? Tex) Of(SurvivorUnchained.Rpg.CharacterData? ch, SurvivorUnchained.Rpg.EquipSlot slot)
    {
        if (ch?.Equipment[slot] is not { } it || SurvivorUnchained.Rpg.Items.Get(it.Def) is not { } def || def.Icon == "") return (null, null);
        return (def.Icon, ItemPhotos.Real(def.Icon));
    }
}
