import os
from ed import ROOT, sub
p = os.path.join(ROOT, "src", "Ui", "Forge.cs")
s = open(p, encoding="utf-8", newline="").read()
cut = s.index("/// <summary>\r\n/// A seam's mark at the head of its row")
head = open(os.path.join(os.path.dirname(__file__), "forge_head.cs"), encoding="utf-8").read().replace("\r\n", "\n").replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(head + s[cut:])
print("forge rebuilt")

sub('src/Ui/Forge.cs', [
("""    /// <summary>Show what a craft may cost (lo to hi), or add (negative); a remake grows the
    /// piece's full heat as well, a rekindle only refills it.</summary>""",
"""    /// <summary>The heat a craft just took, burning out of the cells it had (from the heat before
    /// to now), or what it gave glowing in: the gauge's half of the hammer's moment.</summary>
    public void Burn(int before)
    {
        if (before == heat) return;
        burnFrom = before;
        burnT = 0;
        cells.QueueRedraw();
    }

    int burnFrom = -1;
    double burnT;

    /// <summary>Show what a craft may cost (lo to hi), or add (negative); a remake grows the
    /// piece's full heat as well, a rekindle only refills it.</summary>"""),
("""    public override void _Process(double delta)
    {
        if (preview && (lo < 0 || hi > lo)) cells.QueueRedraw();
    }""",
"""    public override void _Process(double delta)
    {
        if (burnFrom >= 0)
        {
            burnT += delta;
            if (burnT > 1.1) burnFrom = -1;
            cells.QueueRedraw();
        }
        if (preview && (lo < 0 || hi > lo)) cells.QueueRedraw();
    }"""),
("""                if (!has) { DrawRect(r, dark); DrawRect(r, Style.Line with { A = 0.25f }, false, 1); continue; }""",
"""                // Just spent: the cell flares white-hot and dies to dark over a second, the last first.
                if (!has && g.burnFrom > i)
                {
                    float t = Mathf.Clamp((float)(g.burnT - (g.burnFrom - 1 - i) * 0.07) / 0.8f, 0, 1);
                    DrawRect(r, dark);
                    DrawRect(r, new Color("#fff4d0").Lerp(Style.Ember, Mathf.Min(1, t * 2)) with { A = 1 - t });
                    DrawRect(r, Style.Line with { A = 0.25f * t }, false, 1);
                    continue;
                }
                if (!has) { DrawRect(r, dark); DrawRect(r, Style.Line with { A = 0.25f }, false, 1); continue; }
                // Just given (a rekindle, a remake): the new cells glow in from gold.
                if (g.burnFrom >= 0 && g.burnFrom <= i)
                {
                    float t = Mathf.Clamp((float)(g.burnT - (i - g.burnFrom) * 0.06) / 0.7f, 0, 1);
                    DrawRect(r, Style.Gold.Lerp(lit, t) with { A = 0.35f + 0.65f * t });
                    DrawRect(r, Colors.White with { A = 0.8f * (1 - t) }, false, 1.5f);
                    continue;
                }"""),
])
sub('logic/Rpg/Crafting.cs', [
("""    /// <summary>Their respect rises with work brought, a little a craft, to a limit.</summary>
    public int RespectPerCraft, RespectFromCraft;""",
"""    /// <summary>Their regard rises with work brought, a little a craft, to a limit (the smith's
    /// respect; the herbalist's affection).</summary>
    public int RespectPerCraft, RespectFromCraft;
    public Axis Grows = Axis.Respect;"""),
("""        if (done * d.RespectPerCraft < d.RespectFromCraft) n.Respect = Math.Min(100, n.Respect + d.RespectPerCraft);""",
"""        if (done * d.RespectPerCraft < d.RespectFromCraft) n[d.Grows] = Math.Min(100, n[d.Grows] + d.RespectPerCraft);"""),
])
