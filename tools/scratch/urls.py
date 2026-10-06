"""Count URLs on asset hosts across transcripts, to find where downloaded assets came from."""
import re, sys, glob, collections
root = sys.argv[1]
hosts = sys.argv[2] if len(sys.argv) > 2 else r'itch\.io|freesound|opengameart|sonniss|pixabay|zapsplat|mixkit|kenney|fab\.com|cgtrader|turbosquid|civitai|huggingface\.co|sketchfab\.com/3d-models|polyhaven\.com/a|ambientcg|quaternius|mixamo|github\.com|zenodo|pexels|unsplash|makehumancommunity|google\.com/specimen|fonts\.google'
pat = re.compile(r'https?://[A-Za-z0-9.-]*(?:' + hosts + r')[A-Za-z0-9./_%?=&#~+-]*', re.I)
c = collections.Counter()
for p in glob.glob(root + '/**/*.jsonl', recursive=True):
    with open(p, encoding='utf-8', errors='replace') as f:
        for line in f:
            for m in pat.findall(line):
                c[m.rstrip('.\\),')] += 1
for u, n in sorted(c.items()):
    print(n, u)
