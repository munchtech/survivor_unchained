W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Bosses\ArenaBosses.cs', [
('''/// <summary>Grimtunnel, roused: the ground is the enemy. He cannot die before the
/// story's end, so the fight is won when he goes back down the hole. Frost stops
/// him under the ground.</summary>
public sealed class Grimtunnel : ArenaBoss
{
    public Grimtunnel(IBossArena a) : base(a) { }''',
'''/// <summary>Grimtunnel, roused: the ground is the enemy. He cannot die before the
/// story's end, so the fight is won when he goes back down the hole. Frost stops
/// him under the ground.
///
/// The Ganger fights the same fight: a Dig foreman, the table's Lamplings' boss,
/// since the story keeps Grimtunnel and his name for the Dig Boils Over and Act 3
/// (docs/STORY_BIBLE.md, "The nights"). It wears one lamp, not his three, that
/// flares for each of the three verbs in turn and puts them all out when it breaks;
/// and it dies like anything else.</summary>
public sealed class Grimtunnel : ArenaBoss
{
    readonly bool ganger;
    public Grimtunnel(IBossArena a, bool ganger = false) : base(a)
    {
        this.ganger = ganger;
        Lit = ganger ? [true] : [true, true, true];
        lampHp = new double[Lit.Length];
    }
    public bool Ganger => ganger;'''),
('''    public override string WeaknessText => "Frost stops him under the ground";
    protected override string HardName => "The Fall";
    protected override bool DiesAtZero => false;
    double underT = 5, lampT = 3, mothT = 12, boilT = 6, pickT = 2;
    int lampIx;
    double dazeT;
    /// <summary>His three lamps (red, blue, green): each lit, a verb; hit while it flares to break it.</summary>
    public readonly bool[] Lit = [true, true, true];
    readonly double[] lampHp = new double[3];
    int flaring = -1;''',
'''    public override string WeaknessText => ganger ? "Frost catches it under the ground" : "Frost stops him under the ground";
    protected override string HardName => "The Fall";
    protected override bool DiesAtZero => ganger;
    double underT = 5, lampT = 3, mothT = 12, boilT = 6, pickT = 2;
    int lampIx, verb;
    double dazeT;
    /// <summary>His three lamps (red, blue, green): each lit, a verb; hit while it flares to
    /// break it. The Ganger's one lamp carries all three verbs.</summary>
    public readonly bool[] Lit;
    readonly double[] lampHp;
    int flaring = -1;'''),
('''        if (phase == 0) for (int i = 0; i < 3; i++) lampHp[i] = E.MaxHp * 0.08;''',
'''        // His three lamps a twelfth of him each; the Ganger's one a sixth.
        if (phase == 0) for (int i = 0; i < Lit.Length; i++) lampHp[i] = E.MaxHp * (ganger ? 0.16 : 0.08);'''),
('''        if (e.Hp <= 1.5 && PhaseIx == Phases.Length - 1) { StartDown(e); return true; }
        if (dazeT > 0)''',
'''        if (!ganger && e.Hp <= 1.5 && PhaseIx == Phases.Length - 1) { StartDown(e); return true; }
        if (dazeT > 0)'''),
('''            lampT = 7 * Cadence;
            for (int k = 0; k < 3; k++) { lampIx = (lampIx + 1) % 3; if (Lit[lampIx]) break; }
            Lamp(lampIx);
            return true;''',
'''            lampT = 7 * Cadence;
            if (ganger) { lampIx = 0; verb = (verb + 1) % 3; }
            else { for (int k = 0; k < 3; k++) { lampIx = (lampIx + 1) % 3; if (Lit[lampIx]) break; } verb = lampIx; }
            flaring = lampIx;
            Lamp(verb);
            return true;'''),
('''    /// <summary>His lamp flares: a verb, and while it flares, hits on him break it.</summary>
    void Lamp(int i)
    {
        flaring = i;
        flareT = 2.5;''',
'''    /// <summary>His lamp flares: a verb, and while it flares, hits on him break it.</summary>
    void Lamp(int i)
    {
        flareT = 2.5;'''),
('''                B.Events.Emit(new Ev.Announce { Title = $"His {LampNames[flaring]} breaks", Tone = Tone.Boon });
                B.Events.Emit(new Ev.Explosion { X = e.X, Z = e.Z, Radius = 2.5, School = flaring == 0 ? School.Fire : flaring == 1 ? School.Frost : School.Nature, Power = 1 });''',
'''                B.Events.Emit(new Ev.Announce { Title = ganger ? "Its lamp breaks" : $"His {LampNames[flaring]} breaks", Subtitle = ganger ? "Its blasting, its diggers and its slurry are done" : null, Tone = Tone.Boon });
                B.Events.Emit(new Ev.Explosion { X = e.X, Z = e.Z, Radius = 2.5, School = verb == 0 ? School.Fire : verb == 1 ? School.Frost : School.Nature, Power = 1 });'''),
('''    public string Lamps => string.Join(" ", Lit.Select((l, i) => l ? LampNames[i].Split(' ')[0] : "-"));''',
'''    public string Lamps => ganger ? (Lit[0] ? "lit" : "out") : string.Join(" ", Lit.Select((l, i) => l ? LampNames[i].Split(' ')[0] : "-"));'''),
])

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''G.SetBoss(script != null ? script.Bar(BossName, script is Grimtunnel g ? $"{BossTitle} · lamps: {g.Lamps}" : BossTitle)''',
'''G.SetBoss(script != null ? script.Bar(BossName, script is Grimtunnel g ? $"{BossTitle} · {(g.Ganger ? "lamp" : "lamps")}: {g.Lamps}" : BossTitle)'''),
])
print("ok")
