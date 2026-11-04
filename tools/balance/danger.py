"""Danger at a glance (H1 combat teeth): an arena run's .jsonl from the balance harness
(`arena --bot plain,deft,human,careless ...`), one row per bot x calling x tier:
nights, won %, fell %, her lowest life (median, and the share of nights that dipped
under half), her life at the end, the hits a fodder and a champion took to fall
(medians over ember 0-10: H1's targets 2-4 and 8-12 at tier 1), the boss's seconds,
and the late hands' threats read.

    python tools/balance/danger.py out.jsonl [--by calling|tier|none] [--falls] [--lamp]

--lamp: a board's lamp (H1 item 6B), by bot, holders against the rest: nights, won %, fell %, her lowest life and
her life at the end, seconds in the lit pool, the lamp's outs and relights, Flare casts and the Flare meter (in casts)
as the boss came, and blows landed on her a minute in the pool and out of it (after it caught).

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
    print(f"{'bot':9} {'calling':9} {'t':>2} {'n':>4} {'won%':>5} {'fell%':>5} {'low':>5} {'<50%':>5} {'end':>5} {'hitsF':>5} {'hitsE':>5} {'boss s':>6} {'read':>5} {'min':>5} {'surr':>4} {'s2+%':>4} {'mk':>4} {'gap':>4}")
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
        # H6: times surrounded a night (median; share of nights with 2+), marks laid on her before the boss, the longest gap without one (s).
        surr = med([r.get('Surrounds', 0) for r in rs]); s2 = 100 * sum(1 for r in rs if r.get('Surrounds', 0) >= 2) / n
        mk = med([r.get('MarksOnHer', 0) for r in rs]); gap = med([r.get('MarkGapMax', float('nan')) for r in rs])
        print(f"{k[0]:9} {str(k[1]):9} {str(k[2]):>2} {n:4} {won:5.0f} {fell:5.0f} {low:5.2f} {under:5.0f} {end:5.2f} {hf:5.1f} {he:5.1f} {boss:6.0f} {read:>5} {mins:5.1f} {surr:4.0f} {s2:4.0f} {mk:4.0f} {gap:4.0f}")

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

def lamp(path):
    rows = defaultdict(list)
    for line in open(path, encoding='utf-8'):
        if not line.strip(): continue
        r = json.loads(line); sp = r['Spec']
        if r.get('LampHeld') is None: continue
        bot = sp.get('Bot') or ('deft' if sp.get('Deft') else 'plain')
        rows[(bot, 'held' if r['LampHeld'] else 'not')].append(r)
    print(f"{'bot':9} {'hold':5} {'n':>4} {'won%':>5} {'fell%':>5} {'low':>5} {'end':>5} {'pool s':>6} {'outs':>5} {'relit':>5} {'flare':>5} {'@boss':>5} {'hit/m in':>8} {'out':>5}")
    for k in sorted(rows):
        rs = rows[k]; n = len(rs)
        won = 100 * sum(1 for r in rs if r.get('WonAt') is not None) / n
        fell = 100 * sum(1 for r in rs if r.get('Died')) / n
        low = med([r.get('LowHp', 1) for r in rs]); end = med([r.get('HpEnd', float('nan')) for r in rs if not r.get('Died')])
        pool = med([r.get('LampPoolSec', 0) for r in rs])
        outs = sum(r.get('LampOuts', 0) for r in rs) / n; relit = sum(r.get('LampRelights', 0) for r in rs) / n
        flare = med([r.get('FlareCasts', 0) for r in rs]); atb = med([r.get('FlareAtBoss') for r in rs])
        si = sum(r.get('LampPoolSec', 0) for r in rs); so = sum(r.get('LampOutSec', 0) for r in rs)
        hin = 60 * sum(r.get('LampHitsIn', 0) for r in rs) / si if si else float('nan')
        hout = 60 * sum(r.get('LampHitsOut', 0) for r in rs) / so if so else float('nan')
        print(f"{k[0]:9} {k[1]:5} {n:4} {won:5.0f} {fell:5.0f} {low:5.2f} {end:5.2f} {pool:6.0f} {outs:5.2f} {relit:5.2f} {flare:5.0f} {atb:5.2f} {hin:8.1f} {hout:5.1f}")

if __name__ == '__main__':
    if '--falls' in sys.argv: falls(sys.argv[1]); sys.exit()
    if '--lamp' in sys.argv: lamp(sys.argv[1]); sys.exit()
    main()
