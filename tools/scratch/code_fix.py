"""The cinematics' lines that can live now as plain captions and triggers, and
the arena outcomes they carry. Run from the worktree root."""
import os

Z = os.path.join('godot', 'logic', 'Play', 'Zones')


def edit(name, pairs):
    p = os.path.join(Z, name)
    b = open(p, 'rb').read()
    crlf = b.count(b'\r\n') > (b.count(b'\n') - b.count(b'\r\n'))
    s = b.decode('utf-8').replace('\r\n', '\n')
    for a, r in pairs:
        assert s.count(a) == 1, (name, a[:90], s.count(a))
        s = s.replace(a, r)
    if crlf:
        s = s.replace('\n', '\r\n')
    open(p, 'wb').write(s.encode('utf-8'))


# ---------------------------------------------------------------- Prologue
edit('Prologue.cs', [
    # C01: the opening's three lines, until the cinematic plays them.
    ('        G.Say("The fire has burned low. Out in the dark, the ground is moving.", null, 4.5);\n',
     '        // C01\'s lines (docs/cinematics/c01_drowned_fire.md, cin_drowned_fire) as\n'
     '        // captions until the cinematic plays them.\n'
     '        G.Say("Your bedroll has not been slept in.", null, 3);\n'
     '        G.After(3.2, () => G.Say("Prints in the frost, your own. They come up from the river. None go down to it.", null, 5));\n'
     '        G.After(8.4, () => G.Say("Past the firelight, the frost is breaking.", null, 3.5));\n'),
    # C02: the Order's evening call under the water, and his word for the dead.
    ('        if (cutT > 0.8 && shown.Add("intro1")) G.Say("Something lies in the ford, larger than any man, with a lamp in its fist.", null, 3.6);\n',
     '        if (cutT > 0.8 && shown.Add("intro1")) G.Say("Something lies in the ford, larger than any man, with a lamp in its fist.", null, 3.6);\n'
     '        if (cutT > 1.4 && shown.Add("intro1b")) B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "Lamps are lit... stay where they reach...", Speaker = "The Ford-Warden" });\n'
     '        if (cutT > 3.4 && shown.Add("intro2b")) B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "Lie down.", Speaker = "The Ford-Warden" });\n'),
    # C03: the dying Warden's question, and Grimtunnel's faith.
    ('        cutT += dt;\n        double cx = wardenPos.X, cz = wardenPos.Z;\n',
     '        cutT += dt;\n        double cx = wardenPos.X, cz = wardenPos.Z;\n'
     '        // C03 (cin_heart_goes_down): a tired man\'s voice, the Order\'s question at the end of a watch.\n'
     '        if (cutT > 0.3 && shown.Add("morning")) B.Events.Emit(new Ev.Bark { X = cx, Z = cz, Text = "Is it morning?", Speaker = "The Ford-Warden" });\n'),
    ('Text = "Oho! A Warden\'s heart, still warm! Nobody\'s, is it? Nobody\'s!", Speaker = "Grimtunnel" });\n',
     'Text = "Ooh, still lit! Nobody\'s, is it? Nobody\'s!", Speaker = "Grimtunnel" });\n'
     '        if (cutT > 6.9 && shown.Add("grim1b")) B.Events.Emit(new Ev.Bark { X = cx + 2.2, Z = cz + 1.2, Text = "...You smell like downstairs.", Speaker = "Grimtunnel" });\n'),
    ('Text = "Finders keepers, surface-meat. The Deep Dig thanks you!", Speaker = "Grimtunnel" });',
     'Text = "Finders keepers, surface-m— (a sniff) ...Downstairs\'ll be ever so grateful.", Speaker = "Grimtunnel" });'),
    # C04: where the ember goes.
    ('"As the sun clears the trees, the ember in you gutters and goes out, and everything it gave you goes with it.',
     '"As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it.'),
])

# ---------------------------------------------------------------- Verge
edit('Verge.cs', [
    ('"Greymuzzle", "The Old Alpha",', '"Greymuzzle", "Who Kept the Cold Off",'),
    ('"Grimtunnel", "Come Up Out of the Dark",', '"Grimtunnel", "Finders Keepers",'),
    # C11: Redcowl's last words are the arena's outcome, cinematic or no (Rav reads them).
    ('[{ "set": { "redcowl": "dead", "roost.cleared": true, "roost.hostile": true } }, { "quest": { "id": "caravan", "entry": "roost_raided" } },',
     '[{ "set": { "redcowl": "dead", "roost.cleared": true, "roost.hostile": true } }, { "quest": { "id": "caravan", "entry": "roost_raided" } },\n'
     '                  { "if": { "fact": "redcowl.ashford_said", "eq": true }, "then": [{ "set": { "redcowl.last_words": "ashford" } }], "else": [{ "set": { "redcowl.last_words": "leg" } }] },'),
    # C06: the Roost is a village that has lost its village. "Them first.", once.
    ('            if (KerchiefsFriendly()) G.Say("Red cloth at every tent. They see your colours and go back to their dice.", null, 4);\n',
     '            if (KerchiefsFriendly())\n'
     '            {\n'
     '                G.Say("Red cloth at every tent, washing on a line, children with a wooden sword. They see your colours and go back to what they were doing.", null, 4.5);\n'
     '                // C06 (cin_forty_one_mouths), the once it matters, until the cinematic plays it.\n'
     '                if (!W.Zone("verge").TryGetValue("roost_kitchen", out var k) || !k.Truthy)\n'
     '                {\n'
     '                    W.Zone("verge")["roost_kitchen"] = true;\n'
     '                    G.After(4.8, () => G.Say("By the cages a woman is passing stew in through the bars. Her own child holds up a bowl beside her.", null, 4.5));\n'
     '                    G.After(9.5, () => G.Say("Them first.", "A Kerchief woman", 3));\n'
     '                }\n'
     '            }\n'),
])

# ---------------------------------------------------------------- Waystation
edit('Waystation.cs', [
    ('        I.Add(new()\n        {\n            Id = "garden", X = garden.X + 2.5, Z = garden.Z + 4.5, R = 2.2, Verb = "Open", Name = "An old trunk",',
     '        // C08 (cin_iron_marker): the morning they bury Nell, the town is in the Quiet\n'
     '        // Garden, and the hymn plays as a conversation until the cinematic does.\n'
     '        I.Add(new()\n'
     '        {\n'
     '            Id = "burial", X = garden.X, Z = garden.Z, R = 5, Verb = "Stand with them", Name = "The Quiet Garden",\n'
     '            When = () => F("nell.burying").Truthy && W.Time != TimeOfDay.Night\n'
     '                && !(W.Zones.TryGetValue("waystation", out var zs) && zs.TryGetValue("burial", out var g) && g.Truthy),\n'
     '            Act = () =>\n'
     '            {\n'
     '                G.Apply("""[{ "zone": { "id": "waystation", "key": "burial", "value": true } }]""");\n'
     '                G.Talk("cin_iron_marker");\n'
     '            },\n'
     '        });\n'
     '        I.Add(new()\n        {\n            Id = "garden", X = garden.X + 2.5, Z = garden.Z + 4.5, R = 2.2, Verb = "Open", Name = "An old trunk",'),
])
print('ok')
