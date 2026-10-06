"""Copy voice packets from a ref into the scratch folder. Usage: python fetch_packets_s2.py <ref> name [name...]"""
import subprocess, sys, os
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a035208561a66c171"
OUT = os.path.dirname(os.path.abspath(__file__))
ref = sys.argv[1]
for n in sys.argv[2:]:
    data = subprocess.run(["git", "show", f"{ref}:docs/voice/elevenlabs/{n}.md"], cwd=WT, capture_output=True).stdout
    open(os.path.join(OUT, f"{n}.md"), "wb").write(data)
    print(n, len(data))
