import json, numpy as np, sys, os
def load(f):
    d=json.load(open(f)); base=os.path.dirname(f)
    bufs=[open(os.path.join(base,b['uri']),'rb').read() for b in d['buffers']]
    def acc(i):
        a=d['accessors'][i]; bv=d['bufferViews'][a['bufferView']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        dt={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}[a['componentType']]
        off=bv.get('byteOffset',0)+a.get('byteOffset',0)
        stride=bv.get('byteStride',0); isz=np.dtype(dt).itemsize*n
        raw=bufs[bv['buffer']]
        if stride and stride!=isz:
            arr=np.frombuffer(raw,dtype=np.uint8,count=stride*a['count'],offset=off).reshape(a['count'],stride)[:,:isz].copy().view(dt)
        else: arr=np.frombuffer(raw,dtype=dt,count=a['count']*n,offset=off)
        return arr.reshape(a['count'],n) if n>1 else arr
    return d,acc
def comps(pos,idx,q=1e-4):
    key=np.round(pos/q).astype(np.int64); _,inv=np.unique(key,axis=0,return_inverse=True); inv=inv.ravel()
    n=inv.max()+1; par=np.arange(n)
    def f(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    t=inv[idx.reshape(-1,3)]
    for a,b,c in t:
        ra,rb,rc=f(a),f(b),f(c)
        par[rb]=ra; par[f(rc)]=ra
    root=np.array([f(i) for i in range(n)])
    return root[inv]
