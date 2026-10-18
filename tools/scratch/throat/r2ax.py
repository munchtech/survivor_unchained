from exp import *
G_,P,inv,U0,T,H=load(sys.argv[1]); g=G_.g
hp=g["meshes"][g["nodes"][86]["mesh"]]["primitives"][0]
nj=len(g["skins"][0]["joints"]); Jh=G_.acc(hp["attributes"]["JOINTS_0"]).astype(int); Wh=G_.acc(hp["attributes"]["WEIGHTS_0"]).astype(float)
Dh=np.zeros((len(Jh),nj))
for k in range(4): np.add.at(Dh,(np.arange(len(Jh)),Jh[:,k]),Wh[:,k])
chin=np.argmax(H[:,2]-3*np.abs(H[:,1]-1.62)); nose=np.argmax(H[:,2])
print("chin",H[chin],"nose",H[nose], "nU",len(U0))
for ax in range(3):
  for dg in (20,):
    Jm=skin_custom(G_,[("neck_01",ax,dg),("Head",ax,dg)],None,0); Q=apply(Jm,H[[chin,nose]],Dh[[chin,nose]])
    print("axis",ax,"+%d"%dg,"chin d",np.round((Q[0]-H[chin])*100,1),"nose d",np.round((Q[1]-H[nose])*100,1))
for b in ("clavicle_l","upperarm_l"):
  i=[k for k,n in enumerate(g["nodes"]) if n.get("name")==b][0]
  print(b, g["nodes"][i].get("rotation"))
