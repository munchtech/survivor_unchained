"""The mock state, identical for every direction."""
from board import Board

CALLING, TYPE, LEVEL = 'warden', 'The Sunderer', 14
ROOT = 'warden.the_wardens_oath'
LIT = ['warden.the_wardens_oath', 'warden.hearth.p2', 'sunderer.two_hands', 'sunderer.s1', 'sunderer.s2', 'sunderer.s3',
       'sunderer.s4', 'sunderer.the_long_cut', 'sunderer.the_long_cut.second_cut', 'sunderer.rite1',
       'sunderer.breaking_point', 'warden.iron_hide', 'warden.shield_bash', 'warden.concussion', 'warden.hand1']
FREE = ['warden.the_wardens_oath', 'sunderer.two_hands', 'sunderer.the_long_cut']
SPARE = 3
FROM_LEVELS, FROM_STORY = 13, 2
# rites' mock tags: (tag, fed)
RITE_TAGS = {
    'sunderer.rite1': ('heavy blows', True), 'sunderer.rite2': ('slams', True),
    'sunderer.rite3': ('fire', False), 'sunderer.rite4': ('projectiles', False),
    'bulwark.rite1': ('blocks', True), 'bulwark.rite2': ('shield hits', True),
    'bulwark.rite3': ('frost', False), 'bulwark.rite4': ('summons', False),
}
DIM_REASON = {'fire': 'Sleeps: carry a fire skill to wake it', 'projectiles': 'Sleeps: carry a projectile skill to wake it',
              'frost': 'Sleeps: carry a frost skill to wake it', 'summons': 'Sleeps: carry a summon to wake it'}
# the six seats, left to right, as the foot shows them (read from u25_town_day_foot.png); None = empty
SEATS = ['sunder', 'oathblade', 'rebuke', 'groundbreaker', 'watch_bell', None]
WICK_SEAT = 0            # the seat the wick panel opens on (Sunder)
FEEDS_TEXT = 'Feeds Sunder, Oathblade'
FEEDS_GLYPHS = ['glyph_color/slash_heavy', 'glyph_color/slash_steel']


class State:
    def __init__(self, board=None):
        self.b = b = board or Board()
        self.lit = set(LIT)
        reach = b.connected(self.lit, ROOT)
        self.disconnected = sorted(self.lit - reach)
        self.count = {}
        for i in self.lit:
            g = b.lamps[i]['group']; self.count[g] = self.count.get(g, 0) + 1
        self.dim = {i for i, (t, fed) in RITE_TAGS.items() if not fed}
        self.spare = SPARE
        # her light reaches so far (brief §5): road steps from the lit set
        self.steps = {i: 0 for i in self.lit}
        q = list(self.lit)
        while q:
            nq = []
            for a in q:
                for n in b.adj[a]:
                    if n not in self.steps:
                        self.steps[n] = self.steps[a] + 1; nq.append(n)
            q = nq

    def fade(self, i):
        """unlit lamps fade with road steps from her lit lamps: <=3 100%, 4-8 65%, past 8 40%"""
        s = self.steps.get(i, 99)
        return 1.0 if s <= 3 else 0.65 if s <= 8 else 0.40

    def near(self, i):
        """within 3 steps: blue lamps keep their cobalt glow, gate notches show"""
        return self.steps.get(i, 99) <= 3

    def lit_on(self, g):
        return self.count.get(g, 0)

    def gate_ok(self, i):
        l = self.b.lamps[i]
        return l['gate'] <= self.lit_on(l['group'])

    def state(self, i):
        """lit | available | blocked | unlit (dim is a separate flag)"""
        if i in self.lit:
            return 'lit'
        if not self.gate_ok(i):
            return 'blocked'
        if any(n in self.lit for n in self.b.adj[i]):
            return 'available'
        return 'unlit'

    def path(self, target):
        return self.b.path_to(self.lit, self.gate_ok, target)
