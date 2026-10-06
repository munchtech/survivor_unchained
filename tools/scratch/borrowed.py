"""Scan the game's shipped text for borrowed names (The Ember Watch's Warcraft list, plus other
well-known franchises' and D&D's product identity), whole words, case-insensitive."""
import re, sys, os, collections
WOW = ['warcraft', 'wowsurvivors', 'world of warcraft', 'azeroth', 'blizzard', 'elwynn', 'westfall', 'duskwood',
       'icecrown', 'stormwind', 'goldshire', 'northshire', 'westbrook', 'raven hill', 'twilight grove', 'frozen throne',
       'silver hand', 'the barrens', 'murloc', 'worgen', 'quilboar', 'kobold', 'gnoll', 'defias', 'riverpaw', 'kolkar',
       'razormane', 'witchwing', 'scourge', 'illidari', 'elune', 'sunscale', 'stonetusk', 'plainstrider',
       'bronze dragonflight', 'death knight', 'demon hunter', "kel'thuzad", 'sylvanas', 'illidan', 'arcane missile',
       'arcane barrage', 'fireball', 'pyroblast', 'frostbolt', 'chain lightning', 'holy nova', 'death coil',
       'death and decay', 'death strike', 'consecration', 'shadow bolt', 'chaos bolt', 'fan of knives', 'blade flurry',
       'whirlwind', 'bladestorm', 'multi-shot', 'moonfire', 'starfall', "avenger's shield", 'metamorphosis',
       'reincarnation', 'desecration', 'soul rending', 'retribution aura', 'divine bulwark', 'divine storm',
       'seal of command', 'raise dead', 'unholy command', 'icebound fury', 'stormcaller', 'windseeker', 'windrunner',
       'marrowrend', 'eye beam', 'defile', 'limit break', 'blessing of kings', 'blessing of wisdom', 'mark of the wild',
       'grace of elune', 'wrath of air', 'ancestral guidance', 'thunderfury', 'warglaive', 'runeblade',
       'ankh of reincarnation', 'you no take candle', 'mrglglgl', 'you are prepared', 'hogger', 'van cleef', 'arthas',
       'thrall', 'jaina', 'lich king', 'ragnaros', 'onyxia', 'naxxramas', 'molten core', 'deadmines', 'ner\'zhul']
OTHER = ['diablo', 'path of exile', 'vampire survivors', 'beholder', 'mind flayer', 'illithid', 'displacer beast',
         'forgotten realms', 'baldur', 'dungeons & dragons', 'dungeons and dragons', 'nazgul', 'nazgûl', 'mordor',
         'hobbit', 'white walker', 'westeros', 'witcher', 'warhammer', 'skaven', 'elden ring', 'dark souls', 'estus',
         'pokemon', 'pokémon', 'zelda', 'hyrule', 'final fantasy', 'chocobo', 'moogle', 'skyrim', 'tamriel', 'dovahkiin',
         'hades', 'tarnished', 'lovecraft', 'cthulhu', 'necronomicon', 'sauron', 'gandalf', 'mithril', 'balrog',
         'ent ', 'hollow knight', 'bloodborne', 'kratos', 'conan', 'drizzt', 'tiamat', 'vecna', 'bigby', 'mordenkainen',
         'melf', 'tasha', 'owlbear', 'umber hulk', 'carrion crawler', 'githyanki', 'slaad', 'yuan-ti']
terms = [(t, 'WoW') for t in WOW] + [(t.strip(), 'other') for t in OTHER]
pats = [(t, k, re.compile(r'(?<![A-Za-z])' + re.escape(t) + r'(?![A-Za-z])', re.I)) for t, k in terms]
hits = collections.defaultdict(list)
for root in sys.argv[1:]:
    for dp, dn, fn in os.walk(root):
        if any(x in dp for x in ('node_modules', '.godot', os.sep + 'bin', os.sep + 'obj')):
            continue
        for f in fn:
            if not f.endswith(('.json', '.cs', '.ts', '.tsx', '.gdshader', '.tscn', '.txt', '.md')):
                continue
            p = os.path.join(dp, f)
            try:
                s = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            for t, k, pat in pats:
                for m in pat.finditer(s):
                    ctx = s[max(0, m.start() - 60): m.end() + 60].replace('\n', ' ')
                    hits[(k, t)].append(f'{p}: ...{ctx}...')
for (k, t), lst in sorted(hits.items()):
    print(f'== [{k}] {t}: {len(lst)}')
    for x in lst[:4]:
        print('    ', x[:260])
