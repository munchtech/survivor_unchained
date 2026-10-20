import sys, json, os
A=r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\anim'; sys.path.insert(0,A); os.chdir(A)
import clips.actions as M
M.FLK.update({k: tuple(v) for k, v in json.loads(sys.argv[1] if len(sys.argv)>1 else '{}').items()})
import build; build.main(['--no-pack','cast_flick'])
