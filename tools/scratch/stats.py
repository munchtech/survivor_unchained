import json, statistics as st, collections, sys, os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot\balance\out')
def load(f): return [json.loads(l) for l in open(f)]
def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else float('nan')
def won(v): return sum(r['WonAt'] is not None for r in v) / len(v)
def fell_before(v): return sum(1 for r in v if r['Died'] and r['WonAt'] is None and r['BossLeft'] < 0) / len(v)

T = load(sys.argv[1] if len(sys.argv) > 1 else 'final_tiers.jsonl')
print('== by tier x policy')
g = collections.defaultdict(list)
for r in T: g[(r['Spec']['Tier'], r['Spec']['Policy'])].append(r)
for k in sorted(g):
    v = g[k]
    print(k, len(v), 'won %.0f%% fell<30 %.0f%% boss %.0f lowHp %.2f complete %.1f first-evo %.1f evos %.1f' % (
        100*won(v), 100*fell_before(v), med([r['BossTtk'] for r in v]), med([r['LowHp'] for r in v]),
        med([r['CompleteAt'] for r in v]), med([min([e['Item2'] for e in r['Evolved']] or [None]) if r['Evolved'] else None for r in v]),
        st.mean(len(r['Evolved']) for r in v)))
print('== by tier')
gt = collections.defaultdict(list)
for r in T: gt[r['Spec']['Tier']].append(r)
for t in sorted(gt):
    v = gt[t]
    def mm(m, key): return med([r['ByMinute'][m-1][key] for r in v if len(r['ByMinute']) >= m])
    print('tier', t, len(v), 'won %.0f%% fell<30 %.0f%% boss %.0f herald %.0f' % (100*won(v), 100*fell_before(v), med([r['BossTtk'] for r in v]), med([x for r in v for x in r['HeraldTtk']])),
          'fodderTTK 5/15/25 %.2f/%.2f/%.2f' % (mm(5,'TtkFodder'), mm(15,'TtkFodder'), mm(25,'TtkFodder')),
          'eliteTTK15 %.1f' % mm(15,'TtkElite'), 'lowHp 10/20/29 %.2f/%.2f/%.2f' % (mm(10,'LowHp'), mm(20,'LowHp'), mm(29,'LowHp')))
t1 = gt[1]
print('== pace tier 1 (ember at end of minute)')
print([round(med([r['ByMinute'][m]['Ember'] for r in t1 if len(r['ByMinute']) > m])) for m in range(30)])
print('drafts/min', [med([r['ByMinute'][m]['Drafts'] for r in t1 if len(r['ByMinute']) > m]) for m in range(10)])
print('cards/min overall %.2f' % med([r['Cards']/max(1,r['Minutes']) for r in T]))
# greats
print('== greats (first choice) win')
gg = collections.defaultdict(list)
for r in T:
    if r['Greats']: gg[r['Greats'][0]].append(r)
for k, v in sorted(gg.items(), key=lambda kv: -won(kv[1])): print(f'{k:20} {len(v):3} won {100*won(v):.0f}%')
if len(sys.argv) > 2:
    P = load(sys.argv[2])
    print('== paths')
    gp = collections.defaultdict(list)
    for r in P: gp[r['Spec']['Policy']].append(r)
    for k in sorted(gp):
        v = gp[k]
        print(f'{k:12} won {100*won(v):.0f}% fell {100*sum(r["Died"] for r in v)/len(v):.0f}% boss {med([r["BossTtk"] for r in v]):.0f} lowHp {med([r["LowHp"] for r in v]):.2f} firstEvo {med([min(e["Item2"] for e in r["Evolved"]) if r["Evolved"] else None for r in v]):.1f}')
