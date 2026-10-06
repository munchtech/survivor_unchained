import re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from sub import sub, ROOT

# Normalise the earlier edit's line endings.
p = ROOT + 'logic/Play/Zones/Verge.cs'
s = open(p, encoding='utf8', newline='').read()
s = re.sub(r'(?<!\r)\n', '\r\n', s)
open(p, 'w', encoding='utf8', newline='').write(s)

V = 'logic/Play/Zones/Verge.cs'
# The Hollow's climax gives the fang the bounty asks for.
sub(V, '''{ "quest": { "id": "beasts", "entry": "alpha_dead" } }, {{Hist("killed_greymuzzle", "killed Greymuzzle, the old alpha of the Pack, in his own Hollow by night"''',
    '''{ "quest": { "id": "beasts", "entry": "alpha_dead" } }, { "give": "greymuzzle_fang" }, {{Hist("killed_greymuzzle", "killed Greymuzzle, the old alpha of the Pack, in his own Hollow by night"''')
# With the Pack running beside you, the Roost's fall is theirs too.
sub(V, '''{ "quest": { "id": "caravan", "entry": "roost_raided" } }, {{Hist(''',
    '''{ "quest": { "id": "caravan", "entry": "roost_raided" } }, {{PackLed}}, {{Hist(''')
sub(V, '''G.Apply($$"""[{ "set": { "redcowl": "dead" } }, {{Hist("killed_redcowl", "killed Redcowl in his own camp"''',
    '''G.Apply($$"""[{ "set": { "redcowl": "dead" } }, {{PackLed}}, {{Hist("killed_redcowl", "killed Redcowl in his own camp"''')
sub(V, '''    /// <summary>The caravan quest settles once both halves of it have.</summary>''',
    '''    /// <summary>Redcowl falls with the Pack running beside you: the ally route's payoff in the journal.</summary>
    const string PackLed = """{ "if": { "fact": "pack.allied", "eq": true }, "then": [{ "quest": { "id": "beasts", "entry": "pack_led" } }] }""";

    /// <summary>The caravan quest settles once both halves of it have.</summary>''')

P = 'logic/Play/Zones/Prologue.cs'
sub(P, '''                  { "history": { "id": "core_stolen", "text": "let a lampling steal the Warden's heart", "tags": ["lampling"], "spread": 1 } }
                ]
                """);''', '''                  { "history": { "id": "core_stolen", "text": "let a lampling steal the Warden's heart", "tags": ["lampling"], "spread": 1 } },
                  { "give": "grimtunnels_lamp" }
                ]
                """);
            // He went down in a hurry: Snib will know whose this is.
            G.After(2, () => G.Say("Where he went down, something glows in the churned mud: a lamp on a snapped strap, still warm. His.", null, 5));''')
print("ok")
