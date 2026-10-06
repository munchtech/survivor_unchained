PAIRS = [
("""        public bool Eyelet;""", """        /// <summary>Fixed at both ends through an iron eye, with a tab beyond it (the owner: it should
        /// truly go through), rather than fading out.</summary>
        public bool Eye;
        public float Tail = 18;"""),
("""                f.Eyelet = r.TryGetProperty("eyelet", out var ey) && ey.ValueKind == System.Text.Json.JsonValueKind.True;""",
"""                f.Eye = r.TryGetProperty("eye", out var ey) && ey.ValueKind == System.Text.Json.JsonValueKind.True;
                f.Tail = N("tail", f.Tail);"""),
("""        float inset = F.Eyelet ? Math.Max(0, Run + 28 - first) : 0;""",
"""        float inset = F.Eye ? Math.Max(0, Run + F.Tail + 26 - first) : 0;"""),
("""        float x0 = Centre(0) - Run, x1 = Centre(n - 1) + Run, mid = (x0 + x1) / 2, half = (x1 - x0) / 2;
        float Y(float at) { float t = (at - mid) / half; return chainY + sag * (1 - t * t); }
        int k0 = (int)Math.Floor((x0 - x) / Pitch) - 1, k1 = (int)Math.Ceiling((x1 - x) / Pitch) + 1;
        heated.Clear();""",
"""        float x0 = Centre(0) - Run, x1 = Centre(n - 1) + Run, mid = (x0 + x1) / 2, half = (x1 - x0) / 2;
        // Through the eyes, the chain runs on to a tab each side; it hangs only between the eyes.
        float t0 = F.Eye ? x0 - F.Tail : x0, t1 = F.Eye ? x1 + F.Tail : x1;
        float Y(float at) { float t = (at - mid) / half; return Math.Abs(t) >= 1 ? chainY : chainY + sag * (1 - t * t); }
        int k0 = (int)Math.Floor((t0 - x) / Pitch) - 1, k1 = (int)Math.Ceiling((t1 - x) / Pitch) + 1;
        heated.Clear();
        eyes = F.Eye ? (new Vector2(x0, chainY), new Vector2(x1, chainY), new Vector2(t0, chainY), new Vector2(t1, chainY)) : null;
        if (eyes != null && Sprite("eye_back") is { } back)
        {
            DrawTexture(back, eyes.Value.L - back.GetSize() / 2);
            DrawSetTransform(eyes.Value.R, 0, new Vector2(-1, 1));
            DrawTexture(back, -back.GetSize() / 2);
            DrawSetTransform(Vector2.Zero);
        }"""),
("""                float a = Fade <= 0 ? (lx >= x0 && lx <= x1 ? 1 : 0) : Mathf.Pow(Mathf.Clamp(Math.Min(lx - x0, x1 - lx) / Fade, 0, 1), 1.3f);""",
"""                float a = Fade <= 0 ? (lx >= t0 && lx <= t1 ? 1 : 0) : Mathf.Pow(Mathf.Clamp(Math.Min(lx - x0, x1 - lx) / Fade, 0, 1), 1.3f);"""),
("""        // The forged eyelets the chain is fixed in, over the links' ends (the owner disliked it fading).
        if (F.Eyelet && Sprite("eyelet") is { } eye)
        {
            DrawSetTransform(new Vector2(x0, Y(x0)));
            DrawTexture(eye, -eye.GetSize() / 2);
            DrawSetTransform(new Vector2(x1, Y(x1)), 0, new Vector2(-1, 1));
            DrawTexture(eye, -eye.GetSize() / 2);
        }
        DrawSetTransform(Vector2.Zero);
        glow.QueueRedraw();""",
"""        DrawSetTransform(Vector2.Zero);
        glow.QueueRedraw();
        front.QueueRedraw();"""),
("""        glow = new HeatGlow(this);
        AddChild(glow);""",
"""        glow = new HeatGlow(this);
        AddChild(glow);
        // (the eyes' near sides and the tabs, over the links and their glow)
        front = new Front(this);
        AddChild(front);"""),
("""    readonly HeatGlow glow;""",
"""    readonly HeatGlow glow;
    readonly Front front;
    /// <summary>Where the eyes (L, R) and the tabs beyond them (TL, TR) are this frame.</summary>
    (Vector2 L, Vector2 R, Vector2 TL, Vector2 TR)? eyes;

    /// <summary>The near side of each eye, the chain passing behind it, and the tab that holds its end.</summary>
    partial class Front : Control
    {
        readonly ChainTabs chain;
        public Front(ChainTabs chain) { this.chain = chain; MouseFilter = MouseFilterEnum.Ignore; TextureFilter = TextureFilterEnum.LinearWithMipmaps; }

        public override void _Draw()
        {
            if (chain.eyes is not { } e) return;
            foreach (var (name, l, r) in new[] { ("eye_front", e.L, e.R), ("tab", e.TL, e.TR) })
            {
                if (Sprite(name) is not { } t) continue;
                DrawTexture(t, l - t.GetSize() / 2);
                DrawSetTransform(r, 0, new Vector2(-1, 1));
                DrawTexture(t, -t.GetSize() / 2);
                DrawSetTransform(Vector2.Zero);
            }
        }
    }"""),
]
