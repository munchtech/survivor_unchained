p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\godot\src\Audio\Sfx.cs'
s = open(p, encoding='utf-8').read()
a = s.index('    /// <summary>The tab chain sliding to another tab')
b = s.index('    public static void Pick()')
new = '''    /// <summary>The tab chain dragged to another tab (tools/uiforge/chainanim.py; heavy forged
    /// chain, the owner: "a little wimpy"). Each link that runs by knocks low iron with a thud of
    /// body under it, timed as the chain moves on its spring (a slow start, quickest early, then
    /// easing). Under them the drag, a grinding rumble. Then a solid clunk as it stops, a chink
    /// as it settles, a softer one as it swings back, and the hiss of the new links taking the
    /// heat. `links` is how many links pass; `secs` stretches the timing (0.32: the game's slide).</summary>
    public static void ChainSlide(int links = 6, double secs = 0.32)
    {
        if (A is not { } a || !a.Gate("chain", 1, 120)) return;
        int n = Math.Clamp(links, 2, 14);
        double t0 = Now, k = secs / 0.32;
        for (int i = 0; i < n; i++)
        {
            double u = (i + 0.5) / n;
            double t = t0 + k * (0.025 + 0.2 * u + 0.04 * u * u) + R(-0.004, 0.004);
            double g = (1.0 - 0.4 * u) * R(0.8, 1.15);
            a.Play(new Fm { T = t, F = R(700, 1300), Ratio = R(1.4, 2.6), Index = R(3, 5), D = R(0.07, 0.13), G = 0.035 * g, Pan = R(-0.15, 0.15), Verb = 0.15, Bus = Bus.Ui });
            double f = R(150, 230);
            a.Play(new Tone { T = t, F = f, F2 = f * 0.8, D = 0.05, G = 0.025 * g, Lp = 500, Bus = Bus.Ui });
        }
        a.Play(new Hiss { T = t0 + 0.02 * k, A = 0.05, D = 0.26 * k, G = 0.035, Lp = 900, Brown = true, Bus = Bus.Ui });
        double stop = t0 + 0.29 * k;
        a.Play(new Tone { T = stop, F = 92, F2 = 68, D = 0.25, G = 0.09, Lp = 380, Bus = Bus.Ui });
        a.Play(new Fm { T = stop, F = R(380, 440), Ratio = 1.41, Index = 4, D = 0.32, G = 0.05, Verb = 0.3, Bus = Bus.Ui });
        a.Play(new Hiss { T = stop, D = 0.07, G = 0.04, Bp = 700, Q = 1, Bus = Bus.Ui });
        a.Play(new Fm { T = stop + 0.17, F = R(1300, 1600), Ratio = 2.76, Index = 2.8, D = 0.14, G = 0.022, Verb = 0.25, Bus = Bus.Ui });
        a.Play(new Fm { T = stop + 0.42, F = R(1500, 1800), Ratio = 3.1, Index = 2.2, D = 0.1, G = 0.01, Verb = 0.25, Bus = Bus.Ui });
        a.Play(new Hiss { T = stop - 0.05, A = 0.18, D = 0.7, G = 0.014, Hp = 4500, Bus = Bus.Ui });
    }

'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\sfxpreview.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''def hiss(D, G, A=0.003, Bp=None, Q=1.0, rng=None):
    from scipy.signal import lfilter
    e = env(int(A * RATE), int(D * RATE), G)
    x = (rng or np.random.default_rng(0)).standard_normal(len(e)) * 0.35
    if Bp:
        w0 = 2 * math.pi * Bp / RATE
        al = math.sin(w0) / (2 * Q)
        b = [al, 0, -al]
        a = [1 + al, -2 * math.cos(w0), 1 - al]
        x = lfilter(b, a, x)
    return x * e''', '''def biquad(x, kind, f, Q=0.707):
    """The RBJ cookbook biquads Synth.cs uses (band, low, high)."""
    from scipy.signal import lfilter
    w0 = 2 * math.pi * f / RATE
    al = math.sin(w0) / (2 * Q)
    cw = math.cos(w0)
    if kind == "band":
        b, a = [al, 0, -al], [1 + al, -2 * cw, 1 - al]
    elif kind == "low":
        b, a = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2], [1 + al, -2 * cw, 1 - al]
    else:
        b, a = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2], [1 + al, -2 * cw, 1 - al]
    return lfilter(b, a, x)


def hiss(D, G, A=0.003, Bp=None, Q=1.0, Lp=None, Hp=None, brown=False, rng=None):
    e = env(int(A * RATE), int(D * RATE), G)
    x = (rng or np.random.default_rng(0)).standard_normal(len(e)) * 0.35
    if brown:
        x = np.cumsum(x) * 0.02
        x = x - np.convolve(x, np.ones(512) / 512, mode="same")
    if Bp:
        x = biquad(x, "band", Bp, Q)
    if Lp:
        x = biquad(x, "low", Lp)
    if Hp:
        x = biquad(x, "high", Hp)
    return x * e


def tone(F, D, G, F2=None, A=0.002, Lp=None):
    """A sine through an envelope, gliding from F to F2, low-passed if asked."""
    e = env(int(A * RATE), int(D * RATE), G)
    n = len(e)
    f = np.full(n, F) if F2 is None else F * (F2 / F) ** (np.arange(n) / n)
    x = np.sin(np.cumsum(f / RATE) * 2 * math.pi)
    if Lp:
        x = biquad(x, "low", Lp)
    return x * e''')
a = s.index('def chain(')
b = s.index('def save(')
s = s[:a] + '''def chain(links=6, secs=0.32, seed=3):
    """Sfx.ChainSlide, as Sfx.cs plays it."""
    rng = np.random.default_rng(seed)

    def R(a, b):
        return rng.uniform(a, b)
    k = secs / 0.32
    out = np.zeros(int((secs + 1.4) * RATE))

    def put(t, s):
        i = int(max(0, t) * RATE)
        j = min(len(out), i + len(s))
        out[i:j] += s[:j - i]
    n = max(2, min(14, links))
    for i in range(n):
        u = (i + 0.5) / n
        t = k * (0.025 + 0.2 * u + 0.04 * u * u) + R(-0.004, 0.004)
        g = (1.0 - 0.4 * u) * R(0.8, 1.15)
        put(t, fm(R(700, 1300), R(1.4, 2.6), R(3, 5), R(0.07, 0.13), 0.035 * g))
        f = R(150, 230)
        put(t, tone(f, 0.05, 0.025 * g, F2=f * 0.8, Lp=500))
    put(0.02 * k, hiss(0.26 * k, 0.035, A=0.05, Lp=900, brown=True, rng=rng))
    stop = 0.29 * k
    put(stop, tone(92, 0.25, 0.09, F2=68, Lp=380))
    put(stop, fm(R(380, 440), 1.41, 4, 0.32, 0.05))
    put(stop, hiss(0.07, 0.04, Bp=700, Q=1, rng=rng))
    put(stop + 0.17, fm(R(1300, 1600), 2.76, 2.8, 0.14, 0.022))
    put(stop + 0.42, fm(R(1500, 1800), 3.1, 2.2, 0.1, 0.01))
    put(stop - 0.05, hiss(0.7, 0.014, A=0.18, Hp=4500, rng=rng))
    return out


''' + s[b:]
open(p, 'w', encoding='utf-8').write(s)
print('ok')
