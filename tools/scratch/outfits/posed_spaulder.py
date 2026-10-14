# posed_spaulder.py <dump dir> <prefix> ...: band 1 against the cap (edges crossing it, nearest gap) and the neck end binding lift, per Godot posed frame (dump_posed.sh writes the frames). Idle prefix first: it picks the parts.
# mdump.py <dir> <prefix-glob>: per posed frame of the ranger: band 1 vs cap (inside count, min clearance where under it),
# and the spaulder binding's lift off her skin at its neck end (max over cells of the cell's min lift)
import sys, glob, os, json, numpy as np
sys.path.insert(0, r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a5ca10091b08dc429/tools/legal/motioncheck')
from posed import load
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import trimesh
D=sys.argv[1]; pats=sys.argv[2:]
files=[f[:-5] for p in pats for f in sorted(glob.glob(os.path.join(D,p+'*_posed.json')))]
def comps(pos,tris):
    key=np.round(pos/2e-5).astype(np.int64); _,inv=np.unique(key,axis=0,return_inverse=True); inv=inv.ravel()
    T2=inv[tris]; n=inv.max()+1; e=np.vstack([T2[:,[0,1]],T2[:,[1,2]]])
    nc,lab=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n)))
    return lab[inv]
REG={}
for f in files:
    head,ms=load(f)
    byn={}
    for m in ms: byn.setdefault(m['name'],[]).append(m)
    body=[m for m in ms if m['name'] in ('Heroine','HeroineHead')]
    if not REG:
        print('meshes',sorted(set(m['name'] for m in ms)))
    BV=np.vstack([m['pos'] for m in body]); BN=np.vstack([m['nrm'] for m in body]); kb=cKDTree(BV)
    br=[m for m in ms if m['name'].endswith('bronze')][0]; dl=[m for m in ms if m['name'].endswith('darkleather')][0]
    if not REG:
        lab=comps(br['pos'],br['tris']); cs=[]
        for c in np.unique(lab):
            idx=np.where(lab==c)[0]; p=br['pos'][idx]
            if len(idx)>200 and p[:,0].min()>0.08 and p[:,1].max()>1.3: cs.append((p[:,1].mean(),idx))
        cs.sort(key=lambda t:-t[0]); grp=[[cs[0]]]
        for t in cs[1:]:
            (grp[-1].append(t) if grp[-1][-1][0]-t[0]<0.015 else grp.append([t]))
        G=[np.concatenate([t[1] for t in g]) for g in grp]; print('bronze groups',[len(g) for g in G])
        REG['cap']=G[0]; REG['b1']=G[1]; REG['b2']=G[2]
        lab=comps(dl['pos'],dl['tris']); best=None
        for c in np.unique(lab):
            idx=np.where(lab==c)[0]; p=dl['pos'][idx]
            if len(idx)>1000 and p[:,0].min()>0.09 and p[:,1].max()>1.35 and (best is None or len(idx)>len(best)): best=idx
        p=dl['pos'][best]; REG['neck']=best[p[:,0]<p[:,0].min()+0.02]
        print('cap %d b1 %d b2 %d bind %d neck %d (from %s)'%(len(REG['cap']),len(REG['b1']),len(REG['b2']),len(best),len(REG['neck']),os.path.basename(f)))
    def sub(m,idx):
        s=set(idx.tolist()); keep=np.array([all(v in s for v in t) for t in m['tris']])
        mp=-np.ones(len(m['pos']),int); mp[idx]=np.arange(len(idx))
        return trimesh.Trimesh(m['pos'][idx], mp[m['tris'][keep]], process=False)
    cap=sub(br,REG['cap'])
    if 'wt' not in REG: REG['wt']=1; print('cap watertight',cap.is_watertight)
    b1=br['pos'][REG['b1']]; n1=br['nrm'][REG['b1']]
    _,jb=kb.query(b1); outer=((b1-BV[jb])*n1).sum(1)>0
    o=b1[outer]+n1[outer]*1e-5; dirs=n1[outer]
    ri=trimesh.ray.ray_pyembree.RayMeshIntersector(cap)
    loc,ir,it=ri.intersects_location(o,dirs,multiple_hits=False)
    hd=np.linalg.norm(loc-o[ir],axis=1); near=hd<0.015
    fac=(cap.face_normals[it]*dirs[ir]).sum(1)
    pen=(near&(fac>0)).sum(); clr=hd[near&(fac<0)]
    bm=sub(br,REG['b1']); E=bm.edges_unique; e0=bm.vertices[E[:,0]]; ev=bm.vertices[E[:,1]]-e0; el=np.linalg.norm(ev,axis=1)
    lo2,ir2,_=ri.intersects_location(e0,ev/el[:,None],multiple_hits=False)
    cross=(np.linalg.norm(lo2-e0[ir2],axis=1)<el[ir2]).sum()
    ins=np.array([cross])
    if 'sh' not in REG:
        REG['sh']=1; sl=[m for m in ms if m['name'].endswith('forestleather')][0]; REG['sheetn']=None
    smp,_=trimesh.sample.sample_surface(cap,80000); dmin,_=cKDTree(smp).query(b1); clr=dmin.min()*1000
    nk=dl['pos'][REG['neck']]; db,jb=kb.query(nk); lift=((nk-BV[jb])*BN[jb]).sum(1)
    cell=np.round(nk/0.008).astype(int); cells={}
    for c_,l_ in zip(map(tuple,cell),lift): cells[c_]=min(cells.get(c_,9),l_)
    top=sorted(cells.items(),key=lambda kv:-kv[1])[:5]
    print('  worst neck cells (x,y,z mm, lift mm):',[(tuple(int(v*8) for v in k),round(l*1000,1)) for k,l in top])
    print('%-40s band1 edges crossing the cap %4d  band1-to-cap min gap %5.2f mm | neck binding lift: max cell-min %4.1f mm, median %4.1f'%(
        os.path.basename(f), ins.sum(), clr, max(cells.values())*1000, np.median(list(cells.values()))*1000))
