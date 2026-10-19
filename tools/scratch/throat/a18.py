from exp import *
G_,P,inv,U0,T,H=load(sys.argv[1]); Wx=dense(G_,inv)
names=[G_.g["nodes"][j]["name"] for j in G_.g["skins"][0]["joints"]]
th,r=cyl(U0); idx=np.nonzero((U0[:,1]>1.45)&(U0[:,1]<1.70)&(np.abs(th)<140)&(r<0.17))[0]
for nm,op in (("rest",[]),("c01--",[("neck_01",1,-6),("neck_01",2,16),("Head",1,-8),("Head",2,14)])):
    Jm=skin_custom(G_,op,None); U=apply(Jm,U0,Wx); S,res=mls(U,vn(U,T),idx,0.05,0.02)
    o=np.argsort(-res)[:12]
    print(nm)
    for k in o:
        i=idx[k]; d={names[j]:w for j,w in enumerate(Wx[i]) if w>0.03}
        print("  res %.1f th %.0f y %.3f r %.3f"%(res[k]*1e3,th[i],U0[i,1],r[i]), " ".join("%s:%.2f"%(a,b) for a,b in sorted(d.items(),key=lambda x:-x[1])))
