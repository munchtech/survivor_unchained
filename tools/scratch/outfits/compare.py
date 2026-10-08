"""The motion check's numbers, before and after, per outfit: frames showing the strip or an
areola (any pixel, and 6 or more), the worst frame of each, and frames where tucked skin is seen.
Each folder holds <outfit>/counts.csv (run_outfit.sh writes them). A baseline counted before
count.py's lone-tip filter is re-read for its areola frames, so both sides count alike.
    python compare.py <base folder> <new folder> [outfit ...]"""
import csv
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
COUNT = os.path.join(HERE, '..', '..', 'legal', 'motioncheck', 'count.py')
src = open(COUNT).read().split("os.makedirs(os.path.join(folder, 'crops')")[0]
src = src.replace("folder = sys.argv[1]", "folder = None").replace(
    "least = int(sys.argv[2]) if len(sys.argv) > 2 else 6", "least = 6")
mod = {}
exec(compile(src, COUNT, 'exec'), mod)


def read(folder, outfit, refilter):
    path = os.path.join(folder, outfit, 'counts.csv')
    if not os.path.exists(path):
        return None
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        r['areola_px'] = int(r['areola_px'])
        r['genital_px'] = int(r['genital_px'])
        r['tucked_seen_px'] = int(r['tucked_seen_px'])
        if refilter and r['areola_px']:
            im = Image.open(os.path.join(folder, outfit, r['frame'])).convert('RGB')
            dist = mod['codes'](im)[0]
            r['areola_px'] = int((dist < mod['AREOLA']).sum())
    return rows


def line(rows):
    if rows is None:
        return 'no run'
    s1 = [r for r in rows if r['genital_px'] > 0]
    s6 = [r for r in rows if r['genital_px'] >= 6]
    a1 = [r for r in rows if r['areola_px'] > 0]
    t6 = [r for r in rows if r['tucked_seen_px'] >= 6]
    ws = max(rows, key=lambda r: r['genital_px'])
    wa = max(rows, key=lambda r: r['areola_px'])
    wt = max(rows, key=lambda r: r['tucked_seen_px'])
    return ('%d frames | strip: %d frames (%d of 6+ px), worst %d px %s | areola: %d frames, worst %d px %s | '
            'tucked seen 6+ px: %d frames, worst %d px %s'
            % (len(rows), len(s1), len(s6), ws['genital_px'], ws['frame'] if ws['genital_px'] else '',
               len(a1), wa['areola_px'], wa['frame'] if wa['areola_px'] else '',
               len(t6), wt['tucked_seen_px'], wt['frame'] if wt['tucked_seen_px'] else ''))


base, new = sys.argv[1], sys.argv[2]
for o in sys.argv[3:] or ['warden', 'arcanist', 'ranger', 'reaver']:
    print(o)
    print('  before:', line(read(base, o, True)))
    print('  after: ', line(read(new, o, False)))
