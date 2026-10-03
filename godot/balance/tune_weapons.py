"""Nudge each combat skill's numbers toward its target (docs/SKILLS_DESIGN.md,
"Targets"), from the harness's per-skill probe:

    dotnet bin/Release/net8.0/Balance.dll weapons --seeds 5 --json out/w.json
    python tune_weapons.py out/w.json [--apply] [--damp 0.8]

Base damage is set from ranks 4 and 8 together; each evolution's damage
multiplier from the evolved stage, after the base has moved. A skill that
fights close (it is hurt doing it) is allowed more, as the price of the
range; a skill that mends or wards or holds the crowd, less."""
import json, math, re, sys

WEAPONS = '../logic/Content/Weapons.cs'

# What each is aimed at, against the median skill at its stage (1.0).
CLOSE = 1.2
UTILITY = {
    'grave_tether': 0.85, 'gravecall': 0.9, 'reaving_arc': 1.05, 'hoarfrost': 0.9, 'thornbloom': 0.95,
    # evolutions that mend, ward or hold
    'tether_of_anguish': 0.85, 'soul_siphon': 0.85, 'rend_and_mend': 1.0, 'circle_of_dawn': 1.0, 'winter_ward': 0.85,
    'absolute_zero': 0.85, 'aegis_wheel': 0.9, 'sanctified_earth': 1.0, 'strangleroot': 0.9, 'blighted_earth': 0.95,
}

def main():
    data = json.load(open(sys.argv[1]))
    apply = '--apply' in sys.argv
    damp = float(sys.argv[sys.argv.index('--damp') + 1]) if '--damp' in sys.argv else 0.8
    idx = {(d['weapon'], d['evo'], d['stage']): d for d in data}
    src = open(WEAPONS, encoding='utf-8').read()
    out = src
    for w in sorted({d['weapon'] for d in data}):
        r1, r4, r8 = idx.get((w, None, 'r1')), idx.get((w, None, 'r4')), idx.get((w, None, 'r8'))
        if not r1 or not r4 or not r8:
            continue
        hurt = (r4['hurt'] + r8['hurt']) / 2
        target = UTILITY.get(w, CLOSE if hurt >= 4 else 1.0)
        # Ranks 4 and 8 weigh most; the first rank a little (its fights are short).
        g = math.exp(0.2 * math.log(max(0.05, r1['index'])) + 0.4 * math.log(max(0.05, r4['index'])) + 0.4 * math.log(max(0.05, r8['index'])))
        f = max(0.5, min(2.0, (target / g) ** damp))
        # The weapon's block: from its Id to the next weapon's.
        m = re.search(r'Id = "%s", Name = .*?(?=\n        new\(\)\n|\n    \}\.ToDictionary)' % w, out, re.S)
        block = m.group(0)
        nb = re.sub(r'(Base = new\(\) \{ Cooldown = [\d.]+, Damage = )([\d.]+)', lambda mm: mm.group(1) + fmt(float(mm.group(2)) * f), block, count=1)
        line = [f'{w:16} r1 {r1["index"]:.2f} r4 {r4["index"]:.2f} r8 {r8["index"]:.2f} hurt {hurt:4.1f} target {target:.2f} base x{f:.2f}']
        for evo in [d['evo'] for d in data if d['weapon'] == w and d['evo']]:
            e = idx[(w, evo, 'evo')]
            et = UTILITY.get(evo, CLOSE if e['hurt'] >= 4 else 1.0)
            moved = e['index'] * f
            ef = max(0.55, min(1.8, (et / max(0.05, moved)) ** damp))
            pat = r'(Id = "%s", Name = [^\n]*\n[^\n]*?Mods = new\(\) \{ Damage = )([\d.]+)' % evo
            nb2 = re.sub(pat, lambda mm: mm.group(1) + fmt(float(mm.group(2)) * ef), nb, count=1)
            if nb2 == nb:
                line.append(f'   {evo}: no Mods.Damage found')
            nb = nb2
            line.append(f'   {evo:18} {e["index"]:.2f} -> {moved:.2f}, target {et:.2f}, mult x{ef:.2f}')
        print('\n'.join(line))
        out = out.replace(block, nb)
    if apply:
        open(WEAPONS, 'w', encoding='utf-8').write(out)
        print('applied')

def fmt(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')

main()
