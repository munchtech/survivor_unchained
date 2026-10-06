p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\godot\src\Audio\Sfx.cs'
s = open(p, encoding='utf-8').read()
a = s.index('    /// <summary>The tab chain dragged to another tab')
b = s.index('    public static void Pick()')
new = '''    /// <summary>An iron ring's bending modes, n(n^2-1)/sqrt(n^2+1) for n = 2..5, relative to the
    /// first: a chain link is a stretched ring, so each is struck as two close partials.</summary>
    static readonly double[] Ring = { 1.0, 2.83, 5.42, 8.77 };

    /// <summary>One link of iron struck (modal): its ring's partials, each split, detuned and
    /// decaying on its own and the higher ones faster, so no two links ring alike; a tick of
    /// contact; a little low body under it.</summary>
    static void Strike(Synth a, double t, double f0, double g, double decay = 0.13, double verb = 0.12, bool body = true)
    {
        for (int j = 0; j < Ring.Length; j++)
            for (int split = -1; split <= 1; split += 2)
            {
                double f = f0 * Ring[j] * (1 + split * R(0.003, 0.009)) * (1 + R(-0.01, 0.01));
                if (f > 15000) continue;
                double amp = g * Math.Pow(0.9, j) * (j == 0 ? 1.15 : 1.0) * R(0.7, 1.1) * 0.5;
                a.Play(new Tone { T = t, F = f, D = decay / (1 + 1.2 * j) * R(0.75, 1.25), G = amp, A = 0.0006, Verb = verb, Bus = Bus.Ui });
            }
        a.Play(new Hiss { T = t, A = 0.0004, D = R(0.004, 0.008), G = g * 1.3, Bp = f0 * R(4, 7), Q = 0.9, Bus = Bus.Ui });
        if (body)
        {
            double fb = R(120, 165);
            a.Play(new Tone { T = t, F = fb, F2 = fb * 0.85, D = R(0.07, 0.1), G = g * 0.55, Lp = 400, Bus = Bus.Ui });
        }
    }

    /// <summary>The tab chain dragged to another tab (tools/uiforge/chainanim.py; heard first with
    /// tools/uiforge/sfxpreview.py). Modal, not FM (the owner: "the sound still kinda sucks"): each
    /// link that runs through the eyelet is a struck iron ring, timed as the chain moves on its
    /// slide spring (slow off the mark, quickest early, easing), its neighbour knocking a beat
    /// after; under them a bed of scrape grains, densest where it runs fastest. Then a sub-thump
    /// through the band as it stops with the whole chain ringing low, a chink as it settles and a
    /// softer one as it swings back, and a sizzle of tiny pops as the new links take the heat.
    /// `links` is how many links pass; `secs` stretches the timing (0.32: the game's slide).</summary>
    public static void ChainSlide(int links = 6, double secs = 0.32)
    {
        if (A is not { } a || !a.Gate("chain", 1, 120)) return;
        int n = Math.Clamp(links, 2, 14);
        double t0 = Now, k = secs / 0.32;
        for (int i = 0; i < n; i++)
        {
            double u = (i + 0.5) / n;
            double t = t0 + k * (0.025 + 0.2 * u + 0.04 * u * u);
            Strike(a, t + R(-0.004, 0.004), R(420, 640), 0.03 * (1.0 - 0.35 * u) * R(0.8, 1.15));
            if (R(0, 1) < 0.5) Strike(a, t + R(0.012, 0.03), R(600, 900), 0.012 * R(0.7, 1.1), 0.08, 0.12, false);
        }
        double stop = t0 + 0.29 * k;
        for (double t = t0 + 0.02 * k; t < stop;)
        {
            double speed = Math.Max(0.15, Math.Pow(Math.Sin(Math.Min(1, (t - t0) / (stop - t0)) * Math.PI), 0.7));
            a.Play(new Hiss { T = t, A = 0.001, D = R(0.006, 0.018), G = 0.022 * speed * R(0.5, 1.1), Bp = R(1200, 3600), Q = R(2, 5), Bus = Bus.Ui });
            t += R(0.008, 0.02) / speed;
        }
        a.Play(new Tone { T = stop, F = 62, F2 = 44, A = 0.003, D = 0.22, G = 0.12, Lp = 160, Bus = Bus.Ui });
        a.Play(new Hiss { T = stop, A = 0.002, D = 0.06, G = 0.05, Lp = 300, Brown = true, Bus = Bus.Ui });
        Strike(a, stop, R(300, 360), 0.05, 0.45, 0.28);
        Strike(a, stop + 0.006, R(430, 520), 0.03, 0.3, 0.28, false);
        Strike(a, stop + 0.17, R(640, 760), 0.02, 0.25, 0.25, false);
        Strike(a, stop + 0.42, R(700, 860), 0.01, 0.2, 0.25, false);
        for (double t = stop - 0.05; t < stop + 0.65; t += R(0.01, 0.045))
        {
            double f = 1 - (t - stop + 0.05) / 0.7;
            a.Play(new Hiss { T = t, A = 0.0003, D = R(0.002, 0.005), G = 0.012 * f * R(0.4, 1.0), Hp = R(4500, 7000), Bus = Bus.Ui });
        }
    }

'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8').write(s)
print('ok')
