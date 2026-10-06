import json
import sys

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_shapes as fs

json.dump(getattr(fs, sys.argv[2]), open(sys.argv[1], "w"), indent=0)
print(len(getattr(fs, sys.argv[2])))
