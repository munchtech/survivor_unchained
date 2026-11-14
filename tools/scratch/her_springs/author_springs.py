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
out=[{"id":"warden.skirt","source":src,"springs":springs,"carry":{"rule":"island","reach":0.07,"share":0.6}},
     {"id":"warden.pauldrons","source":src,"springs":pa,"carry":{"rule":"island","reach":0.11,"share":0.6}}]
json.dump(out,open(r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f/godot/art/people/springs.json','w',encoding='utf-8'),indent=2)
