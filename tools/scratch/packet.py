"""Compact view of an ElevenLabs packet: packet.py <voice> [--full] [from] [to]
Prints: n | file | paste text (and Played/Note with --full). Flags paste != subtitle (minus tags)."""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
P = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\vo"
voice = sys.argv[1]
full = "--full" in sys.argv
nums = [int(a) for a in sys.argv[2:] if a.isdigit()]
lo, hi = (nums + [1, 10**6])[:2] if nums else (1, 10**6)
text = open(f"{P}\\{voice}.md", encoding="utf-8-sig").read()
blocks = re.split(r"\n### ", text)
section = ""
for b in blocks[1:]:
    head = b.split("\n", 1)[0]
    m = re.match(r"(\d+)\. `([^`]+)`(.*)", head)
    if not m:
        continue
    n = int(m.group(1))
    # section headings inside the previous block
    if not (lo <= n <= hi):
        continue
    played = re.search(r"\*Played:\* (.*)", b)
    note = re.search(r"\*Note:\* (.*)", b)
    where = re.search(r"\*Where:\* (.*)", b)
    paste = re.search(r"```\n(.*?)\n```", b, re.S)
    sub = re.search(r"Subtitle: (.*)", b)
    p = paste.group(1).strip() if paste else ""
    s = sub.group(1).strip() if sub else ""
    flag = ""
    plain = re.sub(r"\[[^\]]*\]\s*", "", p).replace("â€¦", "").replace("...", "")
    if re.sub(r"\W", "", plain.lower()) != re.sub(r"\W", "", s.replace("...", "").lower()):
        flag = "  <<SUB DIFFERS: " + s
    print(f"{n}. {m.group(2)}{m.group(3)}")
    if full:
        if where: print("   where:", where.group(1))
        if played: print("   played:", played.group(1))
        if note: print("   note:", note.group(1))
    print("   >", p.replace("\n", " / ") + flag)
    nxt = re.search(r"\n## (.*)", b)
    if nxt:
        print(f"\n## {nxt.group(1)}")

