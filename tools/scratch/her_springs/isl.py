import sys, numpy as np, json
sys.path.insert(0,'.')
from gl import load, comps
f=r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f/godot/art/people/heroine_outfit_warden.gltf'
d,acc=load(f)
nodes=d['nodes']
def local(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4,4).T
    T=np.eye(4); 
    t=n.get('translation',[0,0,0]); r=n.get('rotation',[0,0,0,1]); s=n.get('scale',[1,1,1])
    x,y,z,w=r
    R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    T[:3,:3]=R*np.array(s); T[:3,3]=t; return T
par={}
for i,n in enumerate(nodes):
    for c in n.get('children',[]): par[c]=i
def world(i):
    M=local(nodes[i])
    while i in par: i=par[i]; M=local(nodes[i])@M
    return M
want=sys.argv[1]
for i,n in enumerate(nodes):
    if 'mesh' not in n or not n.get('name','').startswith(want): continue
    sk=d['skins'][n['skin']]; ibm=acc(sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    jw=np.array([world(j) for j in sk['joints']]); jn=[nodes[j]['name'] for j in sk['joints']]
    for pr in d['meshes'][n['mesh']]['primitives']:
        pos=acc(pr['attributes']['POSITION']).astype(np.float64); idx=acc(pr['indices']).astype(np.int64)
        J=acc(pr['attributes']['JOINTS_0']); W=acc(pr['attributes']['WEIGHTS_0'])
        dom=J[np.arange(len(J)),W.argmax(1)]
        M=jw[dom]@ibm[dom]
        wp=np.einsum('nij,nj->ni',M,np.c_[pos,np.ones(len(pos))])[:,:3]
        isl=comps(pos,idx)
        ids,cnt=np.unique(isl,return_counts=True)
        print(n['name'],'mat',pr.get('material'),'verts',len(pos),'islands',len(ids))
        for k,c in sorted(zip(ids,cnt),key=lambda t:-t[1])[:16 if len(sys.argv)<3 else int(sys.argv[2])]:
            P=wp[isl==k]; top=P[P[:,1]>P[:,1].max()-0.01].mean(0); bot=P[P[:,1]<P[:,1].min()+0.01].mean(0)
            dn=[jn[x] for x in dom[isl==k]]; from collections import Counter
            print(f'  n{c:6d} top {np.round(top,3)} bot {np.round(bot,3)} ymin {P[:,1].min():.3f} ymax {P[:,1].max():.3f} xr {P[:,0].min():.3f}..{P[:,0].max():.3f} zr {P[:,2].min():.3f}..{P[:,2].max():.3f} dom {Counter(dn).most_common(2)}')
