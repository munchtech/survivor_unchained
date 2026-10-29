# The Turn measure's reading (turn_measure.sh; Balance arena --pair turn:ID). Per pair: the skill's damage with its
# Turn and without, on the same build. S = sum on / sum off (pooled, ratio of sums), split into the crowd (not
# champions) and champions; P = all her damage dealt (on/off) x taken (off/on), as the Hand measure reads it.
# sigma: delta method on log S over pairs. A/B: two disjoint halves of the seeds (the lower and the upper half; not odd
# and even, which splits the starting weapon), which should agree.
import json,sys,math,collections
def load(fs):
    L=[]
    for f in fs:
        for l in open(f): L.append(json.loads(l))
    return L
def ratio(L,f):
    a=sum(f(x['On']) for x in L); b=sum(f(x['Off']) for x in L); return a/b if b else float('nan')
def sig(L,f):
    a=sum(f(x['On']) for x in L); b=sum(f(x['Off']) for x in L); n=len(L)
    z=[f(x['On'])/a-f(x['Off'])/b for x in L]; m=sum(z)/n
    return math.sqrt(sum((v-m)**2 for v in z)*n/max(1,n-1))
sk=lambda s:s['Skill']; el=lambda s:s['Elite']; cr=lambda s:s['Skill']-s['Elite']
def row(name,L):
    S=ratio(L,sk); s=sig(L,sk)*S
    ss=sorted({x['Seed'] for x in L}); mid=ss[len(ss)//2]
    A=[x for x in L if x['Seed']<mid]; B=[x for x in L if x['Seed']>=mid]
    d=ratio(L,lambda s:s['Dmg']); t=sum(x['Off']['DamageTaken'] for x in L)/max(1e-9,sum(x['On']['DamageTaken'] for x in L))
    share=sum(x['Off']['Skill'] for x in L)/sum(x['Off']['Dmg'] for x in L)
    champ=sum(x['Off']['Elite'] for x in L)/sum(x['Off']['Skill'] for x in L)
    lit=sum(1 for x in L if x['Turn'] in x['On']['TurnsOn'])/len(L)
    print(f"{name:22} {len(L):4}  S {S:.3f} ±{s:.3f}  A {ratio(A,sk):.3f} B {ratio(B,sk):.3f}  crowd {ratio(L,cr):.3f} champ {ratio(L,el):.3f}"
          f"  | P {d*t:.3f} (dealt {d:.3f} taken {t:.3f})  share {share:.2f} champ-part {champ:.2f} lit {lit:.2f}")
L=load(sys.argv[1:])
G=collections.defaultdict(list)
for x in L:
    b='deft' if x['Deft'] else 'plain'
    G[(x['Turn'],b,'all')].append(x); G[(x['Turn'],b,x['Calling'])].append(x); G[(x['Turn'],b,f"t{x['Tier']}")].append(x)
for k in sorted(G, key=lambda k:(k[0],k[1],k[2]!='all',k[2])): row(' '.join(k),G[k])
