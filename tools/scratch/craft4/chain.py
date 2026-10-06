"""The seam's mark as a ledger numeral, and the heat as a chain of UI art's links."""
import os
from ed import ROOT
P = os.path.join(ROOT, "src/Ui/Forge.cs")
s = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")
s = s.replace("Style.Font(b, Style.TextBold, 20, q.Ok ? ink : Kit.Faint, false);", "Style.Font(b, Style.DisplayLight, 19, q.Ok ? ink : Kit.Faint, false);")

a = s.index("/// <summary>\n/// A seam's mark at the head of its row")
s = s[:a] + '''/// <summary>
/// A seam's mark at the head of its ledger row: a grade as its numeral in Cinzel, coloured as the
/// rarity of the same rank (grade IV reads as epic), no box round it; the bright grade with a little
/// light of its own; a caged coal as a flame, a worn skill as a book, the slurry's as a drop; an open
/// seam as a "+" cut into the page.
/// </summary>
public partial class GradeBadge : Control
{
    public enum Mark { Grade, Coal, Skill, Open, Slurry, Inscribed }
    readonly Mark mark;
    readonly int tier, cap;

    public GradeBadge(Mark mark, int tier, int cap)
    {
        this.mark = mark;
        this.tier = tier;
        this.cap = cap;
        CustomMinimumSize = new Vector2(44, 36);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Draw()
    {
        var c = Size / 2;
        bool bright = mark == Mark.Grade && tier >= Crafting.Bright;
        var col = mark switch { Mark.Coal => Style.Ember, Mark.Skill => Style.Day, Mark.Slurry => ItemViews.SlurryGreen, Mark.Inscribed => ItemViews.MarkInk, _ => bright ? ItemViews.BrightGrade : Style.RarityOf(tier) };
        if (mark == Mark.Open)
        {
            // Cut into the page: a dark stroke with the light catching its lower edge.
            foreach (var (off, ink) in new[] { (new Vector2(0, 1), new Color(1, 1, 1, 0.12f)), (Vector2.Zero, new Color(0, 0, 0, 0.75f)) })
            {
                DrawLine(c + off + new Vector2(-9, 0), c + off + new Vector2(9, 0), ink, 2.2f, true);
                DrawLine(c + off + new Vector2(0, -9), c + off + new Vector2(0, 9), ink, 2.2f, true);
            }
            return;
        }
        if (mark is Mark.Coal or Mark.Skill or Mark.Slurry)
        {
            var tex = Glyphs.Texture(mark switch { Mark.Coal => "flame", Mark.Slurry => "drop", _ => "book" }, 28, col);
            DrawTextureRect(tex, new Rect2(c - new Vector2(14, 14), new Vector2(28, 28)), false);
            return;
        }
        // The bright grade gives off a little light of its own.
        if (bright) for (int i = 3; i >= 1; i--) DrawCircle(c, 9 + i * 5, ItemViews.SlurryGreen with { A = 0.05f * (4 - i) });
        string numeral = Crafting.Grade(tier);
        var font = Style.Display;
        var size = font.GetStringSize(numeral, HorizontalAlignment.Left, -1, 26);
        var at = new Vector2(c.X - size.X / 2, c.Y + 9);
        DrawString(font, at + new Vector2(0, 1), numeral, HorizontalAlignment.Left, -1, 26, new Color(0, 0, 0, 0.7f));
        DrawString(font, at, numeral, HorizontalAlignment.Left, -1, 26, col.Lightened(0.15f));
    }
}

/// <summary>
/// A piece's heat as a chain of iron links (UI art's chain/: face and edge in turn, cold, warm and
/// hot): a link for every point of heat it can take, hot for what is left, cold iron for what is
/// spent, its count as type beside it. While a craft is under the pointer or the focus, the links it
/// will surely take go warm and the ones it might take pulse; a craft that adds heat lights new
/// links. Struck, the spent links cool from hot through warm to cold, the last first. The budget is
/// shown before it is spent (C3, C4), and the chain is the motif doing a job: its working life is
/// literally its hot links.
/// </summary>
public partial class HeatGauge : HBoxContainer
{
    readonly int heat, full;
    int lo, hi;
    bool preview, grows;
    readonly Links links;
    readonly Label words;

    public HeatGauge(ItemInstance it, float width = 430)
    {
        heat = it.Heat ?? 0;
        full = Math.Max(1, it.HeatFull ?? heat);
        AddThemeConstantOverride("separation", Style.Gap3);
        MouseFilter = MouseFilterEnum.Ignore;
        links = new Links(this) { CustomMinimumSize = new Vector2(width, 28) };
        links.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        AddChild(links);
        words = Style.Label("", Style.UiBold, 16, Style.EmberHi);
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        AddChild(words);
        Say();
    }

    /// <summary>The heat a craft just took, cooling out of the links it had (from the heat before to
    /// now), or what it gave heating in: the gauge's half of the hammer's moment.</summary>
    public void Burn(int before)
    {
        if (before == heat) return;
        // A preview already up (the focus stayed on the press) waits its turn.
        if (preview) { pending = (lo, hi, grows); preview = false; }
        burnFrom = before;
        burnT = 0;
        Say();
        links.QueueRedraw();
    }

    int burnFrom = -1;
    double burnT;
    (int Lo, int Hi, bool Grows)? pending;

    /// <summary>Show what a craft may cost (lo to hi), or add (negative); a remake grows the
    /// piece's full heat as well, a rekindle only refills it.</summary>
    public void Preview(int lo, int hi, bool grows = false)
    {
        if (lo == 0 && hi == 0) { Clear(); return; }
        // The heat a craft just took is seen go first; what the next would take, after.
        if (burnFrom >= 0) { pending = (lo, hi, grows); return; }
        this.lo = lo;
        this.hi = hi;
        this.grows = grows;
        preview = true;
        Say();
        links.QueueRedraw();
    }

    public void Clear()
    {
        pending = null;
        if (!preview) return;
        preview = false;
        Say();
        links.QueueRedraw();
    }

    void Say()
    {
        if (heat <= 0 && !(preview && lo < 0)) { words.Text = "Set: nothing more can be worked into it"; words.AddThemeColorOverride("font_color", Kit.Dim); return; }
        words.AddThemeColorOverride("font_color", Style.EmberHi);
        // Just worked: what it took, said while the links cool.
        if (burnFrom >= 0 && !preview)
        {
            words.Text = burnFrom > heat ? $"{burnFrom - heat} heat spent: {heat} of {full}" : $"+{heat - burnFrom} heat: {heat} of {full}";
            if (heat == 0) words.Text = "Set: the last of its heat spent";
            return;
        }
        if (!preview) { words.Text = $"Heat {heat} of {full}"; return; }
        if (lo < 0) { words.Text = $"+{NewHeat - heat} heat: {NewHeat} of {Grown}"; return; }
        int left = Math.Max(0, heat - hi), most = Math.Max(0, heat - lo);
        words.Text = left == most ? $"Heat {heat} to {left}" : $"Heat {heat} to {left}–{most}";
        if (left == 0) words.AddThemeColorOverride("font_color", Style.Bad);
    }

    /// <summary>The full heat after a craft that adds it: a remake grows the piece's full heat,
    /// a rekindle only refills it.</summary>
    int Grown => preview && lo < 0 && grows ? full - lo : full;
    int NewHeat => preview && lo < 0 ? Math.Min(Grown, heat - lo) : heat;

    public override void _Process(double delta)
    {
        if (burnFrom >= 0)
        {
            burnT += delta;
            if (burnT > 1.6)
            {
                burnFrom = -1;
                Say();
                if (pending is { } p) { pending = null; Preview(p.Lo, p.Hi, p.Grows); }
            }
            links.QueueRedraw();
        }
        if (preview && (lo < 0 || hi > lo)) links.QueueRedraw();
    }

    sealed partial class Links : Control
    {
        readonly HeatGauge g;
        public Links(HeatGauge g) { this.g = g; MouseFilter = MouseFilterEnum.Ignore; }

        /// <summary>UI art's link, by its heat (0 cold, 1 warm, 2 hot) and its turn in the chain (face or
        /// edge, and one of its six castings, so no two neighbours are the same iron).</summary>
        static Texture2D? Link(int heat, int i) =>
            UiArt.Art($"chain/{(heat switch { 2 => "hot_", 1 => "warm_", _ => "" })}{(i % 2 == 0 ? "face" : "edge")}_{i % 6}.png");

        public override void _Draw()
        {
            int n = g.Grown;
            float pulse = 0.5f + 0.5f * Mathf.Sin((float)Time.GetTicksMsec() / 180f);
            // The link's own size at the drawn scale, and the pitch the chain needs to fit its width.
            float s = Size.Y / 44f, cw = 52 * s, ch = 44 * s;
            float pitch = Mathf.Min(17.2f * s * 1.25f, n > 1 ? (Size.X - cw) / (n - 1) : 0);
            if (Link(2, 0) == null) { Cells(n, pulse); return; }
            for (int i = 0; i < n; i++)
            {
                var r = new Rect2(i * pitch, 0, cw, ch);
                bool has = i < g.heat;
                // A craft that adds heat: new links lit, breathing.
                if (g.preview && g.lo < 0 && i >= g.heat && i < g.NewHeat) { Draw(2, i, r, 0.45f + 0.4f * pulse); continue; }
                // Just spent: hot to warm to cold over a second, the last first.
                if (!has && g.burnFrom > i)
                {
                    float t = Mathf.Clamp((float)(g.burnT - (g.burnFrom - 1 - i) * 0.07) / 0.8f, 0, 1);
                    Draw(0, i, r, 1);
                    Draw(1, i, r, 1 - Mathf.Clamp((t - 0.5f) * 2, 0, 1));
                    Draw(2, i, r, 1 - Mathf.Clamp(t * 2, 0, 1));
                    continue;
                }
                if (!has) { Draw(0, i, r, 0.75f); continue; }
                // Just given (a rekindle, a remake): the new links heat in from cold.
                if (g.burnFrom >= 0 && g.burnFrom <= i)
                {
                    float t = Mathf.Clamp((float)(g.burnT - (i - g.burnFrom) * 0.06) / 0.7f, 0, 1);
                    Draw(0, i, r, 1);
                    Draw(2, i, r, t);
                    continue;
                }
                if (g.preview && g.lo >= 0)
                {
                    bool sure = i >= g.heat - g.lo, maybe = !sure && i >= g.heat - g.hi;
                    if (sure) { Draw(1, i, r, 1); continue; }
                    if (maybe) { Draw(1, i, r, 1); Draw(2, i, r, pulse); continue; }
                }
                Draw(2, i, r, 1);
            }
        }

        void Draw(int heat, int i, Rect2 r, float a)
        {
            if (a <= 0.01f || Link(heat, i) is not { } t) return;
            DrawTextureRect(t, r, false, Colors.White with { A = a });
        }

        /// <summary>Until UI art's links are in the build: the heat as plain cells.</summary>
        void Cells(int n, float pulse)
        {
            float gap = 2, w = (Size.X - gap * (n - 1)) / n, hgt = Size.Y * 0.6f, y = Size.Y * 0.2f;
            for (int i = 0; i < n; i++)
            {
                var r = new Rect2(i * (w + gap), y, w, hgt);
                bool spent = i >= g.heat || g.preview && g.lo >= 0 && i >= g.heat - g.hi;
                DrawRect(r, spent ? new Color("#1a1210") : Style.Ember with { A = spent ? 1 : 0.6f + 0.4f * pulse });
            }
        }
    }
}
'''
open(P, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print("ok")
