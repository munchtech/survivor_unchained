"""The Act 1 audit's fixes to the content (docs/WRITING_PASS.md section 15)."""
import sys, os, copy
sys.path.insert(0, os.path.dirname(__file__))
from cj import *

d = load('dialogue.json')

STREAM_CTX = {"any": [{"knows": "clue.green_stream"}, {"knows": "clue.sick_wolf"}, {"knows": "clue.analysis"}, {"knows": "root_cause"}, {"knows": "hint.stream"}]}
PUMPING = {"any": [{"not": {"fact": "dig.pump", "exists": True}}, {"fact": "dig.pump", "eq": "running"}]}
CTX_KERCHIEF = {"any": [{"quest": {"id": "caravan", "entry": e}} for e in ["wreck", "ruts", "roost_found", "redcowl_met", "redcowl_wagons", "roost_raided"]] + [{"knows": "hint.roost"}]}
CTX_COYLE = {"any": [{"quest": {"id": "caravan", "entry": e}} for e in ["harlan_plea", "guard_says", "clerk_turned", "wreck", "redcowl_wagons", "ledger_read"]]}
LEDGER_CTX = {"all": [CTX_KERCHIEF, CTX_COYLE]}
NO_BEASTS = {"not": {"fact": "beasts.outcome", "exists": True}}
NO_SURVIVORS = {"not": {"fact": "caravan.survivors", "exists": True}}

def both(*conds):
    conds = [c for c in conds if c]
    return conds[0] if len(conds) == 1 else {"all": list(conds)}

def gate_show(c, cond):
    c['show'] = both(c.get('show'), cond)

def gate_when(c, cond):
    c['when'] = both(c.get('when'), cond)

def only_if(cond, effects):
    """Wrap a list of effects so they happen only while cond holds."""
    return {"if": cond, "then": effects}

# A. Redcowl keeps Pell's book once he has read it ("Give me that."), so it
# cannot be shown to him twice (flipping where Pell sleeps) nor shown to
# Holloway to put a man in irons who has already gone.
fx = node(d, 'redcowl', 'pell')['effects']
if not any(e.get('take') == 'pell_ledger' for e in fx):
    fx.insert(0, {"take": "pell_ledger"})

# B. Snib: nobody is asked to move, shut off or be bribed over a pump that is
# no longer pumping into the stream; and he says so.
for nid in ('first', 'hub'):
    for frag in ("Your pump's poisoning the stream", "Pump it into", "Grimtunnel sent me", "How much to shut it off", "Then I'll shut it off myself"):
        for c in [c for c in node(d, 'snib', nid).get('choices') or [] if frag in (c['text'] if isinstance(c['text'], str) else c['text'][0]['text'])]:
            if PUMPING not in (c.get('show', {}).get('all') or []) and c.get('show') != PUMPING:
                gate_show(c, PUMPING)
hub = node(d, 'snib', 'hub')
if isinstance(hub['text'], str):
    hub['text'] = [
        {"when": {"fact": "dig.pump", "eq": "broken"}, "text": "You again. Pump is BROKEN. Somebody broke it. Snib does not know who. Snib knows exactly who. Foreman is still foreman."},
        {"when": {"fact": "dig.pump", "eq": "moved"}, "text": "You again. Pump is pumping in the sinkhole now. Deeper. Boss likes deeper. Boss has not said he likes it. Foreman is still foreman."},
        {"text": hub['text']},
    ]

# C. Vonnra hears the accusation once; read again, the fortune does not ask for it twice.
c = choice(d, 'vonnra', 'f_below', 'You lit the lamps')
c['once'] = 'accuse'

# D. Her mark asks for you only until the chapter is closed.
for m in d['vonnra']['marker']:
    if m.get('mark') == '?':
        m['when'] = {"all": [{"fact": "chapter.ready", "eq": True}, {"not": {"fact": "chapter.done", "eq": True}}]}

# E. The toll ledger is paid for once: read, the question goes.
for nid, c in choices(d, 'vonnra', "Did Coyle's caravan pay your toll"):
    gate_show(c, {"not": {"quest": {"id": "caravan", "entry": "toll_ledger"}}})

# F. Greymuzzle, met before the survivor knew of the Roost, can still be asked to run.
again = node(d, 'greymuzzle', 'again')
if not any('Run with me' in (x['text'] if isinstance(x['text'], str) else x['text'][0]['text']) for x in again['choices']):
    ally = copy.deepcopy(choice(d, 'greymuzzle', 'show', 'Run with me'))
    ally['show'] = {"all": [{"fact": "greymuzzle", "eq": "met"}, {"not": {"fact": "promise.broken", "eq": True}}, {"not": {"fact": "pack.allied", "eq": True}},
                            {"any": [NO_BEASTS, {"fact": "beasts.outcome", "eq": "cured"}]}]}
    again['choices'].insert(0, ally)

# H. The arrest's way out is the ledger, and only for someone who knows what it proves.
gate_when(choice(d, 'holloway', 'arrest', 'who paid the Kerchiefs'), LEDGER_CTX)

# K. Harlan's mark: a box to give back while it is still his to want, Jory's
# news until he has heard it, the Roost until he knows where his wagons are.
for m in d['harlan']['marker']:
    if m.get('mark') == '?':
        m['when'] = {"any": [
            {"all": [{"hasItem": "coyle_strongbox"}, {"not": {"fact": "caravan.cargo", "exists": True}}]},
            {"all": [{"fact": "caravan.survivors", "eq": "rescued"}, {"not": {"npcFlag": {"npc": "harlan", "key": "once:jory", "eq": True}}}]},
            {"all": [{"quest": {"id": "caravan", "entry": "roost_found"}}, NO_SURVIVORS, {"not": {"npcFlag": {"npc": "harlan", "key": "once:roost", "eq": True}}}]},
        ]}

# L. Holloway's mark for the ledger: only while he would take it or read it.
for m in d['holloway']['marker']:
    if m.get('mark') == '?' and m.get('when') == {"hasItem": "pell_ledger"}:
        m['when'] = {"all": [{"hasItem": "pell_ledger"}, {"any": [LEDGER_CTX, {"not": {"quest": {"id": "caravan", "entry": "ledger_read"}}}]}]}

# N. The teamsters' keep is paid once, and the hundred buys them too, as Redcowl says.
for nid, c in choices(d, 'redcowl', 'Let the teamsters go'):
    gate_when(c, {"not": {"fact": "redcowl.releases", "eq": True}})
deal = node(d, 'redcowl', 'deal')
for e in deal['effects']:
    if 'set' in e and e['set'].get('redcowl') == 'bargained':
        e['set']['redcowl.releases'] = True
# He has nothing left to sell you once the box is yours.
for nid, c in choices(d, 'redcowl', 'Coyle wagons'):
    if c.get('goto') == 'goods':
        gate_when(c, {"all": [{"not": {"fact": "caravan.box_taken", "eq": True}}, {"not": {"fact": "caravan.cargo", "exists": True}}]})
for nid, c in choices(d, 'redcowl', 'come for them'):
    gate_when(c, {"all": [{"not": {"fact": "caravan.box_taken", "eq": True}}, {"not": {"fact": "caravan.cargo", "exists": True}}]})

# O. Rav slides Jessop's key across the table once.
for e in node(d, 'rav', 'clerk')['effects']:
    if 'if' in e and e['if'] == {"knows": "underworld"}:
        e['if'] = {"all": [{"knows": "underworld"}, {"not": {"quest": {"id": "caravan", "entry": "clerks_key"}}}]}

# P. Maeca thanks whoever cleared the water, met or not, before she starts on the bounty.
entries = d['maeca']['entry']
thanks = next(e for e in entries if e['node'] == 'thanks')
first = next(e for e in entries if e['node'] == 'first')
if entries.index(thanks) > entries.index(first):
    entries.remove(thanks)
    entries.insert(entries.index(first), thanks)

# R. Leads are not written into a story that is already over (the journal
# would gain "Harlan blames the wolves" after Jory was home).
def wrap_entry_effects(effects, entry_ids, cond):
    out = []
    for e in effects:
        q = e.get('quest')
        if q and q.get('entry') in entry_ids:
            out.append(only_if(cond, [e]))
        else:
            out.append(e)
    return out

def gate_entries(convo, nid, entry_ids, cond, where='node'):
    n = node(d, convo, nid)
    n['effects'] = wrap_entry_effects(n.get('effects') or [], entry_ids, cond)

# Rook's talk: the wolves while they are a rumour, Harlan's plea while Jory is missing.
gate_entries('rook', 'rumours', {'rumour'}, NO_BEASTS)
gate_entries('rook', 'rumours', {'harlan_plea'}, NO_SURVIVORS)
# Holloway's bounty, Maeca's theory, Tam's plea: while the wolves are unsettled.
gate_entries('holloway', 'first', {'holloway_bounty'}, NO_BEASTS)
gate_entries('holloway', 'wolves', {'holloway_bounty'}, NO_BEASTS)
gate_entries('maeca', 'first', {'maeca_theory'}, NO_BEASTS)
gate_entries('maeca', 'driving', {'maeca_theory'}, NO_BEASTS)
gate_entries('tam', 'story', {'tam_plea'}, NO_BEASTS)
# Wenna asks for water only until she has tested some.
gate_entries('wenna', 'animals', {'wenna_request'}, {"all": [NO_BEASTS, {"not": {"knows": "clue.analysis"}}]})
gate_entries('wenna', 'tamsays', {'wenna_request'}, NO_BEASTS)
# Harlan blames the wolves only while they are still out there.
first_fx = node(d, 'harlan', 'first')['effects']
for e in first_fx:
    if 'if' in e and e['if'] == NO_SURVIVORS:
        then = e['then'] if isinstance(e['then'], list) else [e['then']]
        e['then'] = [x if x.get('quest', {}).get('entry') != 'harlan_view' else only_if(NO_BEASTS, [x]) for x in then]

# V. Harlan does not ask a reward for Jory, nor count the days, once Jory's fate is known.
for frag in ("What happened to the caravan", "Which road were they on"):
    for nid, c in choices(d, 'harlan', frag):
        gate_show(c, NO_SURVIVORS)

save('dialogue.json', d)

# M. Things the town says happened, said only once they have.
r = load('rules.json')
corran = next(x for x in r['rules'] if x['id'] == 'holloway.corran')
eff = corran['effect'] if isinstance(corran['effect'], list) else [corran['effect']]
if not any('set' in e and 'corran.home' in e['set'] for e in eff):
    eff.append({"set": {"corran.home": True}})
corran['effect'] = eff
save('rules.json', r)

c = load('concerns.json')
for x in c['holloway']:
    if x.get('when') == {"fact": "holloway.post_told", "eq": True}:
        x['when'] = {"fact": "corran.home", "eq": True}
save('concerns.json', c)

f = load('folk.json')
for x in f['lines']:
    if x.get('when') == {"fact": "holloway.post_told", "eq": True}:
        x['when'] = {"fact": "corran.home", "eq": True}
    if x.get('when') == {"fact": "wolves.at_gate", "eq": True} and 'buried Aldo' in x['text']:
        x['when'] = {"fact": "aldo.buried", "eq": True}
save('folk.json', f)
print('ok')
