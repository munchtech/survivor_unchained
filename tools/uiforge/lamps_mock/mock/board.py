"""The board: board_v2.json + lamps.json texts; adjacency, gates, cheapest paths."""
import os, json, heapq
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(HERE)
WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\ui-25'
CONTENT = os.path.join(WT, 'godot', 'data', 'content')


def _jsonc(p):
    with open(p, encoding='utf8') as f:
        return json.loads('\n'.join(l for l in f if not l.lstrip().startswith('//')))


class Board:
    def __init__(self):
        b = json.load(open(os.path.join(SCR, 'board_v2.json'), encoding='utf8'))
        self.groups = {g['id']: g for g in b['groups']}
        self.lamps = {l['id']: dict(l) for l in b['lamps']}
        for l in self.lamps.values():
            if l['kind'] == 'link' and l['region'] == 'road':   # known data bug: road links are gate 8, name "8"
                l['gate'], l['name'] = 8, ''
        self.adj = defaultdict(set)
        self.edges = []
        for l in self.lamps.values():
            for o in l['at']:
                if o in self.lamps:
                    self.adj[l['id']].add(o); self.adj[o].add(l['id'])
                    self.edges.append((o, l['id']))
        lj = _jsonc(os.path.join(CONTENT, 'lamps.json'))
        self.texts = {t['id']: t for t in lj['lamps']}
        self.roads = {r['id']: r for r in lj['roads']}
        self.wicks = _jsonc(os.path.join(CONTENT, 'wicks.json'))

    def name(self, i):
        l = self.lamps[i]
        return l['name'] if l.get('v1') else ''

    def text(self, i):
        t = self.texts.get(i)
        return t['text'] if (t and self.lamps[i].get('v1')) else ''

    def line_and_price(self, i):
        """a blue lamp's price is its text's last sentence"""
        t = self.text(i)
        if self.lamps[i]['kind'] != 'blue' or not t:
            return t, ''
        parts = [p.strip() for p in t.replace('. ', '.\n').split('\n') if p.strip()]
        return ' '.join(parts[:-1]), parts[-1]

    def group_name(self, g):
        gr = self.groups[g]
        if gr['kind'] == 'hearth':
            return 'THE %s\'S HEARTH' % gr['callings'][0].upper()
        if gr['kind'] == 'ford':
            return 'THE FORD'
        return gr['name'].upper()

    def connected(self, lit, root):
        seen, st = {root}, [root]
        while st:
            a = st.pop()
            for b in self.adj[a]:
                if b in lit and b not in seen:
                    seen.add(b); st.append(b)
        return seen

    def path_to(self, lit, gate_ok, target):
        """cheapest unlit lamps to light to reach target (Dijkstra, 1 a lamp, gates honored as of now)"""
        dist, prev, pq = {}, {}, []
        for a in lit:
            for b in self.adj[a]:
                if b not in lit and gate_ok(b):
                    if dist.get(b, 1e9) > 1:
                        dist[b] = 1; prev[b] = a; heapq.heappush(pq, (1, b))
        while pq:
            d, a = heapq.heappop(pq)
            if a == target:
                break
            if d > dist[a]:
                continue
            for b in self.adj[a]:
                if b in lit or not gate_ok(b):
                    continue
                if dist.get(b, 1e9) > d + 1:
                    dist[b] = d + 1; prev[b] = a; heapq.heappush(pq, (d + 1, b))
        if target not in dist:
            return None
        p, a = [], target
        while a not in lit:
            p.append(a); a = prev[a]
        return p[::-1], a          # lamps in order, and the lit lamp it leaves from
