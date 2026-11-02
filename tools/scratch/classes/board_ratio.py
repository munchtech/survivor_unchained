# The board measure's reading (Balance arena --pair board): each arena with an empty board and no wicks (off), then
# with the full board (lamps: full) and the wicks Light my way lights (on), replaying the off run's cards, no falls,
# 30 minutes. P = all her damage dealt (on/off) x taken (off/on), as the Hand measure reads it; target <= x1.25.
# sigma: delta method on log dealt over pairs. A/B: two disjoint halves of the seeds. "top": the sources whose damage
# grew most, as a share of the off run's whole damage (OnBy - OffBy over Off's total).
# board_ratio.py OUT.jsonl [more.jsonl ...]
import json,sys,math,collections
L=[json.loads(l) for f in sys.argv[1:] for l in open(f)]
def ratio(L,f):
    a=sum(f(x['On']) for x in L); b=sum(f(x['Off']) for x in L); return a/b if b else float('nan')
def P(L):
    d=ratio(L,lambda s:s['Dmg']); t=sum(x['Off']['DamageTaken'] for x in L)/max(1e-9,sum(x['On']['DamageTaken'] for x in L))
    return d*t,d,t
def sig(L):
    a=sum(x['On']['Dmg'] for x in L); b=sum(x['Off']['Dmg'] for x in L); n=len(L)
    z=[x['On']['Dmg']/a-x['Off']['Dmg']/b for x in L]; m=sum(z)/n
    return math.sqrt(sum((v-m)**2 for v in z)*n/max(1,n-1))
def top(L,k=4):
    tot=sum(x['Off']['Dmg'] for x in L); g=collections.Counter()
    for x in L:
        for s,v in (x.get('OnBy') or {}).items(): g[s]+=v
        for s,v in (x.get('OffBy') or {}).items(): g[s]-=v
    return ' '.join(f"{s}{v/tot:+.2f}" for s,v in g.most_common(k))
def row(name,L):
    p,d,t=P(L); ss=sorted({x['Seed'] for x in L}); mid=ss[len(ss)//2]
    A=[x for x in L if x['Seed']<mid]; B=[x for x in L if x['Seed']>=mid]
    print(f"{name:20} {len(L):4}  P {p:.3f} (dealt {d:.3f} ±{sig(L)*d:.3f} taken {t:.3f})  A {P(A)[0]:.3f} B {P(B)[0]:.3f}  top {top(L)}")
G=collections.defaultdict(list)
for x in L:
    b='deft' if x['Deft'] else 'plain'
    G[(b,'all','')].append(x); G[(b,x['Calling'],'')].append(x); G[(b,x['Calling'],f"t{x['Tier']}")].append(x)
for k in sorted(G, key=lambda k:(k[0],k[1]!='all',k[1],k[2])): row(' '.join(k).strip(),G[k])
