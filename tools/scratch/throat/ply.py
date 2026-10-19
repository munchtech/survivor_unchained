"""python ply.py <glb> <out.ply> <weights.npy|-> <pose: back,turn,tilt | c01 | c01m> [mark threshold mm]"""
from exp import *
G_,P,inv,U0,T,H=load(sys.argv[1]); out=sys.argv[2]
Wx=dense(G_,inv) if sys.argv[3]=="-" else np.load(sys.argv[3])
if sys.argv[4]=="c01": op=[("neck_01",1,6),("neck_01",2,16),("Head",1,8),("Head",2,14)]
elif sys.argv[4]=="c01m": op=[("neck_01",1,-6),("neck_01",2,16),("Head",1,-8),("Head",2,14)]
else: op=pose_ops(*[float(v) for v in sys.argv[4].split(",")])
Jm=skin_custom(G_,op,None); U=apply(Jm,U0,Wx)
g=G_.g; hp=g["meshes"][g["nodes"][86]["mesh"]]["primitives"][0]
nj=len(g["skins"][0]["joints"]); Jh=G_.acc(hp["attributes"]["JOINTS_0"]).astype(int); Whh=G_.acc(hp["attributes"]["WEIGHTS_0"]).astype(float)
Dh=np.zeros((len(Jh),nj))
for k in range(4): np.add.at(Dh,(np.arange(len(Jh)),Jh[:,k]),Whh[:,k])
Hp=apply(Jm,H,Dh); Th=G_.acc(hp["indices"]).reshape(-1,3).astype(int)
col=np.full((len(U),3),200)
if len(sys.argv)>5:
    th,r=cyl(U0); idx=np.nonzero((U0[:,1]>1.45)&(U0[:,1]<1.70)&(np.abs(th)<140)&(r<0.17))[0]
    S,res=mls(U,vn(U,T),idx,0.05,0.02); hot=idx[res>float(sys.argv[5])*1e-3]; col[hot]=[230,40,40]
V=np.r_[U,Hp]; F=np.r_[T,Th+len(U)]; C=np.r_[col,np.full((len(Hp),3),200)]
with open(out,"w") as f:
    f.write("ply\nformat ascii 1.0\nelement vertex %d\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nelement face %d\nproperty list uchar int vertex_indices\nend_header\n"%(len(V),len(F)))
    for v,c in zip(V,C): f.write("%.5f %.5f %.5f %d %d %d\n"%(v[0],-v[2],v[1],c[0],c[1],c[2]))
    for t in F: f.write("3 %d %d %d\n"%tuple(t))
