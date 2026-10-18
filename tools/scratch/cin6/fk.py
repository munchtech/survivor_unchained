import json,struct,sys,numpy as np
p,anim=sys.argv[1],sys.argv[2]
f=open(p,'rb').read()
l=struct.unpack('<I',f[12:16])[0]; j=json.loads(f[20:20+l]); off=20+l; bl=struct.unpack('<I',f[off:off+4])[0]; B=f[off+8:off+8+bl]
def acc(i):
  a=j['accessors'][i]; v=j['bufferViews'][a['bufferView']]; n={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
  o=v.get('byteOffset',0)+a.get('byteOffset',0)
  return np.frombuffer(B[o:o+a['count']*n*4],dtype='<f4').reshape(a['count'],n)
nodes=j['nodes']; par={}
for i,n in enumerate(nodes):
  for c in n.get('children',[]): par[c]=i
def q2m(q):
  x,y,z,w=q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
A=[a for a in j['animations'] if a['name']==anim][0]
ch={}
for c in A['channels']:
  s=A['samplers'][c['sampler']]; ch[(c['target']['node'],c['target']['path'])]=(acc(s['input'])[:,0],acc(s['output']))
def samp(k,t,default):
  if k not in ch: return default
  T,V=ch[k]; i=np.searchsorted(T,t); i=min(max(i,1),len(T)-1); a=(t-T[i-1])/max(T[i]-T[i-1],1e-9); a=min(max(a,0),1)
  v=V[i-1]*(1-a)+V[i]*a
  if v.shape[0]==4: v=v/np.linalg.norm(v)
  return v
def world(i,t):
  n=nodes[i]
  if 'matrix' in n:
    M=np.array(n['matrix']).reshape(4,4).T
    return world(par[i],t)@M if i in par else M
  tr=samp((i,'translation'),t,np.array(n.get('translation',[0,0,0]))); r=samp((i,'rotation'),t,np.array(n.get('rotation',[0,0,0,1]))); s=samp((i,'scale'),t,np.array(n.get('scale',[1,1,1])))
  M=np.eye(4); M[:3,:3]=q2m(r)*s; M[:3,3]=tr
  return world(par[i],t)@M if i in par else M
names={n.get('name'):i for i,n in enumerate(nodes)}
want=sys.argv[3].split(',')
for t in np.arange(0,float(sys.argv[4])+1e-6,0.05):
  print(f"{t:.2f} "+" ".join(f"{w}=({','.join(f'{x:.2f}' for x in world(names[w],t)[:3,3])})" for w in want))
