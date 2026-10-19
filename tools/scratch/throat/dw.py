from exp import *
G_,P,inv,U0,T,H=load(sys.argv[1]); np.save(sys.argv[2],dense(G_,inv))
names=[G_.g["nodes"][j]["name"] for j in G_.g["skins"][0]["joints"]]; X=dense(G_,inv); th,r=cyl(U0)
hj,nj,sj=names.index("Head"),names.index("neck_01"),names.index("spine_03")
s=np.nonzero((np.abs(th)<3)&(U0[:,1]>1.50)&(U0[:,1]<1.66)&(r<0.18))[0]; s=s[np.argsort(U0[s,1])]
print(" ".join("%.3f:%.2f/%.2f/%.2f"%(U0[i,1],X[i,hj],X[i,nj],X[i,sj]) for i in s[::2]))
