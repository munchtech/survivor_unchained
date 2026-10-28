# The Hand measure's reading (hand_measure.sh; Balance arena --pair 1): each arena twice on the same build (the on run
# replays the off run's cards and chests), no falls, 30 minutes. The horde, not her hands, caps the damage dealt (a x1.10
# damage yardstick, --cal 1.10, reads only x1.015 there), so a Hand shows in damage dealt AND damage taken:
# P = dealt(on/off) x taken(off/on). The yardstick x1.10 reads P x1.06-1.11, so P is in about damage-multiplier units.
import json,sys,math,collections
C=collections.defaultdict(list)
for f in sys.argv[1:]:
    for l in open(f):
        r=json.loads(l); C[(r['Calling'],r['Tier'])].append(r); C[(r['Calling'],0)].append(r)
def P(L,side):
    d=sum(x[side]['Dmg'] for x in L)/sum(x['Off']['Dmg'] for x in L); t=sum(x['Off']['DamageTaken'] for x in L)/sum(x[side]['DamageTaken'] for x in L)
    return d,t,d*t
def sig(L,side):
    # delta method on log P = log sum on dmg - log sum off dmg + log sum off taken - log sum on taken
    n=len(L); a=sum(x[side]['Dmg'] for x in L); b=sum(x['Off']['Dmg'] for x in L); c=sum(x['Off']['DamageTaken'] for x in L); d=sum(x[side]['DamageTaken'] for x in L)
    z=[x[side]['Dmg']/a-x['Off']['Dmg']/b+x['Off']['DamageTaken']/c-x[side]['DamageTaken']/d for x in L]
    m=sum(z)/n; return math.sqrt(sum((v-m)**2 for v in z)*n/max(1,n-1))
print("calling  tier   n  dealt  taken    P    sigma   falls off/on  | yardstick P")
for k in sorted(C):
    L=C[k]; d,t,p=P(L,'On'); s=sig(L,'On')*p
    y=f"{P(L,'Cal')[2]:.3f}" if all(x.get('Cal') for x in L) else ''
    print(f"{k[0]:8} {k[1] or 'all':>4} {len(L):4}  {d:.3f}  {t:.3f}  {p:.3f}  {s:.3f}  {sum(x['Off']['Falls'] for x in L)/len(L):.2f}/{sum(x['On']['Falls'] for x in L)/len(L):.2f}  | {y}")
