import sys, json, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
sys.argv=['x','none']
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'isl.py')).read().split("want=sys.argv[1]")[0])
from gl import comps
def islands(name):
    out=[]
    for i,n in enumerate(nodes):
        if n.get('name')!=name: continue
        sk=d['skins'][n['skin']]; ibm=acc(sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
        jw=np.array([world(j) for j in sk['joints']])
        for pr in d['meshes'][n['mesh']]['primitives']:
            pos=acc(pr['attributes']['POSITION']).astype(np.float64); idx=acc(pr['indices']).astype(np.int64)
            J=acc(pr['attributes']['JOINTS_0']); W=acc(pr['attributes']['WEIGHTS_0'])
            dom=J[np.arange(len(J)),W.argmax(1)]; M=jw[dom]@ibm[dom]
            wp=np.einsum('nij,nj->ni',M,np.c_[pos,np.ones(len(pos))])[:,:3]
            isl=comps(pos,idx)
            for k in np.unique(isl): out.append(wp[isl==k])
    return out
R=lambda v:[round(float(x),4) for x in v]
lap=[P for P in islands('warden.skirt.steel')+islands('warden.skirt.darksteel') if len(P)>1000]
lap.sort(key=lambda P:np.arctan2(P[:,0].mean(),P[:,2].mean()))
springs=[]
for i,P in enumerate(lap):
    top=P[P[:,1]>P[:,1].max()-0.01].mean(0); bot=P[P[:,1]<P[:,1].min()+0.01].mean(0)
    # (reach: what holds the whole plate off its chord, a centimetre over)
    a,b=top,bot; ab=b-a; t=np.clip((P-a)@ab/(ab@ab),0,1); dd=np.linalg.norm(P-(a+t[:,None]*ab),axis=1)
    springs.append({"bone":f"spring_skirt_{i:02d}","parent":"pelvis","head":R(top),"tail":R(bot),"radius":0.025,"stiffness":10,"reach":round(float(dd.max())+0.01,3)})
    print(i, R(top), R(bot), 'reach', round(float(dd.max()),3), len(P))
pa=[]
for P in islands('warden.pauldrons.steel'):
    s='l' if P[:,0].mean()>0 else 'r'
    top=P[P[:,1]>P[:,1].max()-0.01].mean(0); ax=np.abs(P[:,0]); out=P[ax>ax.max()-0.015].mean(0)
    a,b=top,out; ab=b-a; t=np.clip((P-a)@ab/(ab@ab),0,1); dd=np.linalg.norm(P-(a+t[:,None]*ab),axis=1)
    pa.append({"bone":f"spring_pauldron_{s}","parent":f"trap_{s}","head":R(top),"tail":R(out),"radius":0.025,"stiffness":14,"reach":round(float(dd.max())+0.01,3)})
    print(s, R(top), R(out), 'reach', round(float(dd.max()),3))
pa.sort(key=lambda x:x['bone'])
src="ours (her-springs lead, 13 Nov): stand-ins for body A's warden set, one link a plate from its top's middle to its hem's (pauldrons: to its outer edge), authored from heroine_outfit_warden.gltf's islands (tools/scratch/her_springs/author_springs.py); R&D's rows for B's gear replace these where they land"
out=[{"id":"warden.skirt","source":src,"springs":springs,"carry":{"rule":"island","reach":0.07,"share":0.6,"follow":True}},
     {"id":"warden.pauldrons","source":src,"springs":pa,"carry":{"rule":"island","reach":0.11,"share":0.6,"follow":True}}]
json.dump(out,open(r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f/godot/art/people/springs.json','w',encoding='utf-8'),indent=2)

# plate_pauldrons_warden (the warden look's pauldrons, armor/: three lames a side, a cap over two shingles): one chain a
# side from the cap's inner edge out over each lame to the last's outer hem, its root on the cap's own bone
f2 = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f/godot/art/armor/plate_pauldrons_warden.gltf'
d, acc = load(f2)
nodes = d['nodes']; par = {}
for i_, n_ in enumerate(nodes):
    for c_ in n_.get('children', []): par[c_] = i_
from collections import Counter
chains = []
for s in ('l', 'r'):
    big = []
    for i_, n_ in enumerate(nodes):
        if n_.get('name') != 'plate_pauldrons_warden.pauldrons.steel': continue
        sk_ = d['skins'][n_['skin']]; ibm_ = acc(sk_['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        jw_ = np.array([world(j_) for j_ in sk_['joints']]); jn_ = [nodes[j_]['name'] for j_ in sk_['joints']]
        for pr in d['meshes'][n_['mesh']]['primitives']:
            pos = acc(pr['attributes']['POSITION']).astype(np.float64); idx = acc(pr['indices']).astype(np.int64)
            J = acc(pr['attributes']['JOINTS_0']); W = acc(pr['attributes']['WEIGHTS_0'])
            dom = J[np.arange(len(J)), W.argmax(1)]; M = jw_[dom] @ ibm_[dom]
            wp = np.einsum('nij,nj->ni', M, np.c_[pos, np.ones(len(pos))])[:, :3]
            isl = comps(pos, idx)
            for k_ in np.unique(isl):
                P = wp[isl == k_]
                if len(P) > 1500 and (P[:, 0].mean() > 0) == (s == 'l'):
                    big.append((P, Counter(jn_[x] for x in dom[isl == k_]).most_common(1)[0][0]))
    # (the cap and its two lames: the largest at each height, highest first; a cap's liner shares its place)
    big.sort(key=lambda t: -t[0][:, 1].max())
    lames = []
    for P, b in big:
        if all(abs(P[:, 1].max() - Q[:, 1].max()) > 0.01 for Q, _ in lames): lames.append((P, b))
    lames = lames[:3]
    # (each point on the plates' middle band front to back: the hinge line runs through it)
    zc = np.mean([P[:, 2].mean() for P, _ in lames])
    lames = [(P[np.abs(P[:, 2] - zc) < 0.015], b, P) for P, b in lames]
    ax = lambda P: np.abs(P[:, 0])
    cap = lames[0][0]
    pts = [cap[ax(cap) < ax(cap).min() + 0.01].mean(0)]
    for (P, _, _), (Q, _, _) in zip(lames, lames[1:]):
        pts.append((P[ax(P) > ax(P).max() - 0.01].mean(0) + Q[Q[:, 1] > Q[:, 1].max() - 0.008].mean(0)) / 2)
    last = lames[-1][0]
    pts.append(last[ax(last) > ax(last).max() - 0.008].mean(0))
    for i_ in range(len(lames)):
        P = lames[i_][2]; a, b = pts[i_], pts[i_ + 1]; ab = b - a
        t = np.clip((P - a) @ ab / (ab @ ab), 0, 1); dd = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        chains.append({"bone": f"spring_pauldron_{s}{i_}", "parent": lames[0][1] if i_ == 0 else f"spring_pauldron_{s}{i_ - 1}",
                       "head": R(a), "tail": R(b), "radius": 0.02, "stiffness": 14, "reach": round(float(dd.max()) + 0.01, 3)})
        print(s, i_, lames[i_][1], R(a), R(b), 'reach', round(float(dd.max()), 3), len(P))
out.append({"id": "plate_pauldrons_warden", "source": src, "springs": chains, "carry": {"rule": "island", "reach": 0.08, "share": 0.6, "follow": True}})
json.dump(out, open(r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f/godot/art/people/springs.json', 'w', encoding='utf-8'), indent=2)
