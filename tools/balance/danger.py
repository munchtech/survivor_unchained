"""Danger at a glance (H1 combat teeth): an arena run's .jsonl from the balance harness
(`arena --bot plain,deft,human,careless ...`), one row per bot x calling x tier:
nights, won %, fell %, her lowest life (median, and the share of nights that dipped
under half), her life at the end, the hits a fodder and a champion took to fall
(medians over ember 0-10: H1's targets 2-4 and 8-12 at tier 1), the boss's seconds,
and the late hands' threats read.

    python tools/balance/danger.py out.jsonl [--by calling|tier|none] [--falls]

H1's tier-1 targets: the late human ends at 30-60% life and falls ~1 night in 4
careless; the deft bot still wins ~90%."""
import json, sys, statistics as st
from collections import defaultdict

def med(xs):
    xs = [x for x in xs if isinstance(x, (int, float)) and x == x]
    return st.median(xs) if xs else float('nan')

def main():
    path = sys.argv[1]
    by = sys.argv[sys.argv.index('--by') + 1] if '--by' in sys.argv else 'calling'
    rows = defaultdict(list)
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        sp = r['Spec']
        bot = sp.get('Bot') or ('deft' if sp.get('Deft') else 'plain')
        k = (bot, sp['Calling'] if by == 'calling' else '', sp['Tier'] if by in ('calling', 'tier') else '')
        rows[k].append(r)
    print(f"{'bot':9} {'calling':9} {'t':>2} {'n':>4} {'won%':>5} {'fell%':>5} {'low':>5} {'<50%':>5} {'end':>5} {'hitsF':>5} {'hitsE':>5} {'boss s':>6} {'read':>5} {'min':>5}")
    for k in sorted(rows, key=lambda k: (str(k[1]), str(k[2]), k[0])):
        rs = rows[k]
        n = len(rs)
        won = 100 * sum(1 for r in rs if r.get('WonAt') is not None) / n
        fell = 100 * sum(1 for r in rs if r.get('Died')) / n
        low = med([r.get('LowHp', 1) for r in rs])
        under = 100 * sum(1 for r in rs if r.get('LowHp', 1) < 0.5) / n
        end = med([r.get('HpEnd', float('nan')) for r in rs if not r.get('Died')])
        hf = med([r.get('HitsFodder') for r in rs]); he = med([r.get('HitsElite') for r in rs])
        boss = med([r.get('BossTtk') for r in rs if r.get('BossTtk') is not None])
        met = sum(r.get('ThreatsMet', 0) for r in rs); rd = sum(r.get('ThreatsRead', 0) for r in rs)
        read = f"{100 * rd / met:.0f}%" if met else '-'
        mins = med([r.get('Minutes') for r in rs])
        print(f"{k[0]:9} {str(k[1]):9} {str(k[2]):>2} {n:4} {won:5.0f} {fell:5.0f} {low:5.2f} {under:5.0f} {end:5.2f} {hf:5.1f} {he:5.1f} {boss:6.0f} {read:>5} {mins:5.1f}")

def falls(path):
    """What felled her, by bot: the killer, and whether on the way (before the boss) or at the boss; the kit's
    tells that caught her of those marked, and draughts drunk."""
    c = defaultdict(lambda: defaultdict(int)); kit = defaultdict(lambda: [0, 0, 0, 0])
    for line in open(path, encoding='utf-8'):
        if not line.strip(): continue
        r = json.loads(line); sp = r['Spec']
        bot = sp.get('Bot') or ('deft' if sp.get('Deft') else 'plain')
        if r.get('Died'): c[bot][(r.get('KilledBy', '?'), 'boss' if r.get('BossLeft', -1) >= 0 or r['Minutes'] >= sp.get('Minutes', 30) else 'way')] += 1
        k = kit[bot]; k[0] += r.get('KitCaught', 0); k[1] += r.get('KitMarked', 0); k[2] += r.get('Quaffs', 0); k[3] += 1
    for bot in sorted(kit):
        k = kit[bot]
        print(f"{bot:9} kit caught {k[0]}/{k[1]} ({100 * k[0] / max(1, k[1]):.0f}%)  draughts/night {k[2] / k[3]:.1f}  falls: " +
              ', '.join(f"{n} {w} {m}" for (n, w), m in sorted(c[bot].items(), key=lambda x: -x[1])[:6]))

if __name__ == '__main__':
    if '--falls' in sys.argv: falls(sys.argv[1]); sys.exit()
    main()
