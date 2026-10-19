import sys,numpy as np
sys.argv=['x','godot/art/beasts/lampling.glb','Idle','mixamorig:Hips_56','0']
exec(open(sys.path[0]+'/fk.py').read().split('want=sys.argv')[0])
t=1.8
bones=[n.get('name') for n in nodes if n.get('name','').startswith('mixamorig:')]
P={b:world(names[b],t)[:3,3] for b in bones}
L=lambda s:P['mixamorig:'+s]
fwd=np.cross(L('LeftUpLeg_50')-L('RightUpLeg_55'),[0,1,0]); fwd[1]=0; fwd/=np.linalg.norm(fwd)
yaw=np.arctan2(fwd[0],fwd[2]); c,s=np.cos(-yaw),np.sin(-yaw)
Ry=np.array([[c,0,s],[0,1,0],[-s,0,c]])
ys=[p[1] for p in P.values()]; low,high=min(ys),max(ys); sc=0.95/(high-low)
mid=L('Hips_56')
M=lambda p: sc*(Ry@(np.array([p[0]-mid[0],p[1]-low,p[2]-mid[2]])))
for k in ['Hips_56','Spine2_43','Neck_2','Head_1','LeftShoulder_22','LeftArm_21','LeftForeArm_20','LeftHand_19','LeftHandMiddle1_14','RightArm_41','RightForeArm_40','RightHand_39','HeadTop_End_0']:
  print(k, np.round(M(L(k)),3))

def rx(a): c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rot_between(a,b):
  a=a/np.linalg.norm(a); b=b/np.linalg.norm(b); v=np.cross(a,b); cth=np.dot(a,b); s=np.linalg.norm(v)
  if s<1e-9: return np.eye(3)
  k=v/s; K=np.array([[0,-k[2],k[1]],[k[2],0,-k[0]],[-k[1],k[0],0]]); th=np.arctan2(s,cth)
  return np.eye(3)+np.sin(th)*K+(1-np.cos(th))*K@K
def euler(R):
  y=np.arcsin(np.clip(R[0,2],-1,1)); x=np.arctan2(-R[1,2],R[2,2]); z=np.arctan2(-R[0,1],R[0,0]); return x,y,z
lean=float(__import__('os').environ.get('LEAN','0.25'))
Q={k[10:]:M(v) for k,v in P.items()}
C=Q['Spine2_43']; Rl=rx(lean)
chest_kids=['Neck_2','Head_1','HeadTop_End_0','LeftShoulder_22','LeftArm_21','LeftForeArm_20','LeftHand_19','RightShoulder_42','RightArm_41','RightForeArm_40','RightHand_39']
for k in chest_kids: Q[k]=C+Rl@(Q[k]-C)
heart=np.array([0,float(__import__('os').environ.get('HY','0.585')),float(__import__('os').environ.get('HZ','0.115'))])
hw=float(__import__('os').environ.get('HW','0.045'))
print('chest',np.round(C,3),'heart(model)',heart, 'in game x1.9:',np.round(heart*1.9,3))
for side,sg,A,F,H in [('L',1,'LeftArm_21','LeftForeArm_20','LeftHand_19'),('R',-1,'RightArm_41','RightForeArm_40','RightHand_39')]:
  S=Q[A]; l1=np.linalg.norm(Q[F]-Q[A]); l2=np.linalg.norm(Q[H]-Q[F])
  T=heart+np.array([sg*hw,0,0])
  d=T-S; D=np.linalg.norm(d); u=d/D
  a=(l1*l1-l2*l2+D*D)/(2*D); h=np.sqrt(max(l1*l1-a*a,0))
  pole=np.array([sg*1.0,-0.7,-0.2]); pole=pole-np.dot(pole,u)*u; pole/=np.linalg.norm(pole)
  E=S+u*a+pole*h
  R1=rot_between(Q[F]-S,E-S)
  F1=S+R1@(Q[F]-S); H1=S+R1@(Q[H]-S)
  R2=rot_between(H1-F1,T-F1)
  H2=F1+R2@(H1-F1)
  print(side,'reach',round(D,3),'of',round(l1+l2,3),'elbow',np.round(E,3),'hand',np.round(H2,3),'arm euler',np.round(euler(R1),3),'fore euler',np.round(euler(R2),3))
