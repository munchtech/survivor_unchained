cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
python build.py --no-pack $@ > /dev/null; python motion.py $@ --outfits 2>&1 | grep -v "body ready" | python -c "
import sys,re
for l in sys.stdin:
  p=l.split('|'); print(p[0].strip(), 'R:', ' '.join(re.findall(r'(up|br|war|rea) +(\d+)', p[1].split('r:')[1]) and [a+b for a,b in re.findall(r'(up|br|war|rea) +(\d+)', p[1].split('r:')[1])]), re.search(r'slide [^ ]+', l).group(0))"
