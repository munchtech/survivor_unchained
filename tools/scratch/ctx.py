"""Print text around each match of a pattern in big files (e.g. transcripts), N chars either side."""
import re, sys
pat = re.compile(sys.argv[1], re.I)
n = int(sys.argv[2])
maxhits = int(sys.argv[3])
for p in sys.argv[4:]:
    hits = 0
    with open(p, encoding='utf-8', errors='replace') as f:
        for ln, line in enumerate(f, 1):
            for m in pat.finditer(line):
                s = line[max(0, m.start() - n): m.end() + n].replace('\\n', '\n')
                print(f'--- {p.split(chr(92))[-1]}:{ln}')
                print(s)
                hits += 1
                if hits >= maxhits: break
            if hits >= maxhits: break
