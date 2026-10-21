import sys, numpy as np
sys.argv=[sys.argv[0],'old']
exec(open('staffcheck.py').read().split('print(f"row')[0])
clip=b.clip('idle_arcanist_town'); G=b.frames(clip)[0]; P=b.pose(G)
Mb=G[I['spine_03']]; Q=pts@Mb[:3,:3].T+Mb[:3,3]
def bb(m,l): print(l, np.round(P[m].min(0),3), np.round(P[m].max(0),3))
bb(HAT,'hat'); bb(HEADSK,'headneck'); bb(HA,'braid'); bb(SK,'skin')
print('staff head', np.round(Q[head].min(0),3), np.round(Q[head].max(0),3)); print('staff foot', np.round(Q[foot].min(0),3), np.round(Q[foot].max(0),3))
# hat brim profile by height
for y in np.arange(1.45,1.95,0.05):
  m=HAT&(P[:,1]>=y)&(P[:,1]<y+0.05)
  if m.sum(): print('hat y',round(y,2), np.round(P[m][:,0].min(),3),np.round(P[m][:,0].max(),3),np.round(P[m][:,2].min(),3),np.round(P[m][:,2].max(),3))
for y in np.arange(0.9,1.75,0.1):
  m=HA&(P[:,1]>=y)&(P[:,1]<y+0.1)
  if m.sum(): print('braid y',round(y,2), np.round(P[m][:,0].min(),3),np.round(P[m][:,0].max(),3),np.round(P[m][:,2].min(),3),np.round(P[m][:,2].max(),3))
for y in np.arange(0.3,1.6,0.1):
  m=SK&(P[:,1]>=y)&(P[:,1]<y+0.1)
  print('skin y',round(y,2), 'zmin',np.round(P[m][:,2].min(),3), 'x',np.round(P[m][:,0].min(),3),np.round(P[m][:,0].max(),3))
