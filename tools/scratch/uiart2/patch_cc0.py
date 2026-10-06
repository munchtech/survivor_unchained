p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chainsfx.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "takes"
    if what == "takes":
        build()
    elif what == "ledger":
        print("\\n".join(ledger_lines()))''', '''def apply():
    """The takes into godot/art/sound/ (with their .import files), counted in sounds.json."""
    import shutil
    import imports
    snd = os.path.join(ROOT, "godot", "art", "sound")
    counts = json.load(open(os.path.join(snd, "sounds.json"), encoding="utf-8"))
    fams = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".wav"):
            fam, i = f[:-4].rsplit("_", 1)
            fams[fam] = max(fams.get(fam, 0), int(i) + 1)
            shutil.copyfile(os.path.join(OUT, f), os.path.join(snd, f))
    counts.update(fams)
    json.dump(dict(sorted(counts.items())), open(os.path.join(snd, "sounds.json"), "w", encoding="utf-8", newline="\\n"), indent=1)
    made = imports.write([os.path.join(snd, f"{fam}_{i}.wav") for fam, n in fams.items() for i in range(n)])
    print("applied", fams, len(made), "imports")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "takes"
    if what == "takes":
        build()
    elif what == "apply":
        apply()
    elif what == "ledger":
        print("\\n".join(ledger_lines()))''')
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\godot\src\Audio\Sfx.cs'
s = open(p, encoding='utf-8').read()
old = '''    public static void ChainSlide(int links = 6, double secs = 0.32)
    {
        if (A is not { } a || !a.Gate("chain", 1, 120)) return;
        int n = Math.Clamp(links, 2, 14);
        double t0 = Now, k = secs / 0.32;'''
new = '''    public static void ChainSlide(int links = 6, double secs = 0.32)
    {
        if (A is not { } a || !a.Gate("chain", 1, 120)) return;
        int n = Math.Clamp(links, 2, 14);
        double t0 = Now, k = secs / 0.32;
        // Real chain where we have it (art/sound/chainLink_*, chainDrag_*, chainSettle_*: CC0
        // recordings cut, pitched down and given body by tools/uiforge/chainsfx.py), one clink
        // per link at the same spring-timed crossings; the modal iron below stands in without it.
        if (Recordings.Has("chainLink"))
        {
            for (int i = 0; i < n; i++)
            {
                double u = (i + 0.5) / n;
                double t = t0 + k * (0.025 + 0.2 * u + 0.04 * u * u) + R(-0.004, 0.004);
                a.Play(new Clip { T = t, Of = "chainLink", G = 0.32 * (1 - 0.35 * u) * R(0.8, 1.1), Pitch = R(0.94, 1.06), Verb = 0.12, Bus = Bus.Ui });
            }
            if (Recordings.Has("chainDrag")) a.Play(new Clip { T = t0 + 0.02 * k, Of = "chainDrag", G = 0.16, Bus = Bus.Ui });
            if (Recordings.Has("chainSettle")) a.Play(new Clip { T = t0 + 0.29 * k, Of = "chainSettle", G = 0.42, Verb = 0.25, Bus = Bus.Ui });
            return;
        }'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
