p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\MapScreen.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

# The ground's paint read smoothly: the splat is coarser than the drawing, and read nearest it showed as squares.
rep("""        int sr = z.Splat.GetWidth();
        for (int j = 0; j < G; j++)""", """        int sr = z.Splat.GetWidth();
        Color Splat(float u, float v)
        {
            float x = Math.Clamp(u * sr - 0.5f, 0, sr - 1.001f), y = Math.Clamp(v * sr - 0.5f, 0, sr - 1.001f);
            int x0 = (int)x, y0 = (int)y;
            float tx = x - x0, ty = y - y0;
            return z.Splat.GetPixel(x0, y0).Lerp(z.Splat.GetPixel(x0 + 1, y0), tx).Lerp(z.Splat.GetPixel(x0, y0 + 1).Lerp(z.Splat.GetPixel(x0 + 1, y0 + 1), tx), ty);
        }
        for (int j = 0; j < G; j++)""")
rep("""                int px = Math.Clamp((int)((x / z.Size + 0.5f) * sr), 0, sr - 1), py = Math.Clamp((int)((zz / z.Size + 0.5f) * sr), 0, sr - 1);
                var p = z.Splat.GetPixel(px, py);""", """                var p = Splat(x / z.Size + 0.5f, zz / z.Size + 0.5f);""")

# The fog's edge softened: the walked cells are squares, the land is not.
rep("""        for (int y = 0; y < F; y++)
            for (int x = 0; x < F; x++)
            {
                float g = (float)(Hash(x, y) * 0.025);""", """        for (int pass = 0; pass < 3; pass++) alpha = Blur(alpha, F, 3);
        for (int y = 0; y < F; y++)
            for (int x = 0; x < F; x++)
            {
                float g = (float)(Hash(x, y) * 0.025);""")
rep("""    /* --------------------------------------------------------- the atlas -- */""", """    /// <summary>A box blur of a square field, across then down.</summary>
    static float[] Blur(float[] a, int n, int r)
    {
        var b = new float[a.Length];
        var c = new float[a.Length];
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float sum = 0; int k = 0;
                for (int d = -r; d <= r; d++) { int xx = x + d; if (xx < 0 || xx >= n) continue; sum += a[y * n + xx]; k++; }
                b[y * n + x] = sum / k;
            }
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float sum = 0; int k = 0;
                for (int d = -r; d <= r; d++) { int yy = y + d; if (yy < 0 || yy >= n) continue; sum += b[yy * n + x]; k++; }
                c[y * n + x] = sum / k;
            }
        return c;
    }

    /* --------------------------------------------------------- the atlas -- */""")
rep("""        legend.AddChild(Style.H(6, Minimap.Mark(kind, 18), Style.Label(text, Style.Ui, Style.Caption, Style.Ink)));
        col.AddChild(legend);
""", """        legend.AddChild(Style.H(6, Minimap.Mark(kind, 18), Style.Label(text, Style.Ui, Style.Caption, Style.Ink)));
        col.AddChild(legend);
        // The prompts in the list's foot: under the map they would sit on the drawing.
        col.AddChild(Controls.Instance.UsingPad
            ? Style.Hints((Act.Up, "Choose"), (Act.Alt2, "Find me"), (Act.Cancel, "Close"))
            : Style.Label("Wheel to zoom · drag to move · a line to find it", Style.TextItalic, Style.Caption, Style.InkDim, true));
""")
rep("""        PageFooter(Controls.Instance.UsingPad
            ? Footer((Act.Up, "Choose a place"), (Act.SubNext, "Closer"), (Act.SubPrev, "Further"), (Act.Alt2, "Find me"), (Act.TabPrev, "Journal"), (Act.Cancel, "Close"))
            : MouseFooter("Wheel to zoom", "drag to move", "a line to find it"));
""", "")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
