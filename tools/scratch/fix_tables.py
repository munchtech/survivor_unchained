SCR = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad'
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\emblems.py'
old = open(SCR + r'\emblems_head_commit.py', encoding='utf-8').read()
cur = open(p, encoding='utf-8').read()
block = old[old.index('DESIGNS = {k[2:]'):old.index('def make_guide(key):')]


def rep(a, b):
    global block
    assert block.count(a) == 1, a[:70]
    block = block.replace(a, b)


rep('''    "smoke": "a cracked round clay pot burst open at the top, thick billowing grey-violet smoke boiling up out of it",''',
    '''    "smoke": "a cracked round clay pot burst open at the top, thick billowing pale grey smoke boiling up out of it, "
             "violet light glowing from inside the pot",''')
rep('''    "static": "a twisted iron rod with a gold ball at its tip, blue-white lightning crawling up round it and leaping "''',
    '''    "boot": "a worn leather road boot with an iron-shod sole and a buckled strap, driving forward, dust kicked up behind "
            "it, streaks of wind streaming back",
    "horns": "a forged black iron bull helm seen from the front with great curved bone horns lowered and a gold ring "
             "through its nose, streaks of rushing air round it",
    "chain": "an iron chain flung out in a curve, its end a three-hooked iron grappling hook about to bite",
    "shield": "a round wooden shield with an iron rim, rivets and a steel boss, driven forward, a blast of force going "
              "out from its face",
    "mark": "a hunter's mark daubed in glowing red paint on dark hide, a ringed cross, red drips, a fletched arrow "
            "driven into its centre",
    "wing": "a single raised grey heron's wing, long flight feathers spread, three iron caltrops lying on the ground "
            "below it",
    "static": "a twisted iron rod with a gold ball at its tip, blue-white lightning crawling up round it and leaping "''')
i = cur.index('def make_guide(key):')
cur = cur[:i] + block + cur[i:]
open(p, 'w', encoding='utf-8').write(cur)
print('ok')
