"""Round-two revisions to pass_cinematics.py."""
import os
p = os.path.join(os.path.dirname(__file__), 'pass_cinematics.py')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)


rep("""    L('answer', 'narrator', [
        V("You know the answer. They taught it you at seven, with the lamps: morning comes.", {"bg": "devout"}),
        V(""),
    ]),
""", "")
rep("# A variant with no text is no line: only a devout survivor hears the answer.\n", "")
rep("""    L('verse1', 'chid', "(sung) Go down, go down, the morning's under, / down where the lamps are kept; / and when the day has done its turning, / it will wake you where you slept."),
    L('verse2', 'chid', "(sung) Go down, go down, and do not wonder, / down where the light is kept; / the dark is only day not happened, / and it will wake you where you slept."),""",
    """    L('verse1', 'chid', "(sung) Lie down, lie down, the lamps are tended, / and all the dark is kept; / the morning lies a little under, / and it will wake you where you slept."),
    L('verse2', 'chid', "(sung) Lie down, lie down, the road is ended, / your toll is paid and kept; / the dark is but the day not risen, / and it will wake you where you slept."),""")
rep('V("...Ashford.", F(\'redcowl.ashford_said\', eq=True)),',
    'V("...Ashford. (a laugh) There. Now we\'ve both said it.", F(\'redcowl.ashford_said\', eq=True)),')
rep('"Surface-meat! You broke my PUMP. ...Doesn\'t matter. The heart doesn\'t mind. The heart is PATIENT."',
    '"Surface-meat! You broke my PUMP. ...Doesn\'t matter. Downstairs doesn\'t mind. Downstairs is PATIENT."')
rep('"Surface-meat! Killing my lads, are we? ...Doesn\'t matter. The heart doesn\'t mind. The heart is PATIENT."',
    '"Surface-meat! Killing my lads, are we? ...Doesn\'t matter. Downstairs doesn\'t mind. Downstairs is PATIENT."')
rep("""    L('knows', 'grimtunnel', "It knows you! Downstairs! It KNOWS you!"),""",
    """    L('quiet', 'grimtunnel', "I told it about you! It went ever so QUIET!"),""")
marker = [l for l in s.splitlines() if 'Rav hears the leg held (C11)' in l][0]
rep(marker, """# ------------------------------------------- Redcowl's camp as C06 shows it
rc_first = T.node('redcowl', 'first')
rc_first['text'] = [v for v in rc_first['text'] if not (isinstance(v.get('when'), dict) and v['when'].get('sex') == 'female')]
CAGES = ("Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. "
         "I've buried enough worth-nothings for one life, {}. ...Ask them if they're hungry.")
T.text('redcowl', 'cages', [V(CAGES.format('lass'), {"sex": "female"}), V(CAGES.format('lad'))])

""" + marker)
rep("print('cinematics ok')", """it = load('items.json')
it['items']['wardens_lampiron']['lore'] = ("The iron cage of the lamp the Ford-Warden carried. Under the socket, cut clean and new, a smith's mark: "
                                           "a ring with a hammer across it. Whatever burned in it went down a hole in Grimtunnel's arms. The cage still remembers the light.")
save('items.json', it)
print('cinematics ok')""")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
