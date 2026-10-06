"""Second pass, the scripts: the prologue's dead and the costs that land in the Verge."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from sub import sub

P = "logic/Play/Zones/Prologue.cs"
sub(P, '''G.Say("A Watchman, a long time dead. In his belt-book, the last line: \\"Lamps at the Low Ford lit again, and not by us. The Warden is walking.\\"", null, 8);''',
    '''G.Say("A Watchman, a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes: \\"Lamps at the Low Ford lit again, and not by us.\\" \\"Sent Dannet for the captain. Dannet not back.\\" \\"The Warden is walking. I can hear it singing in the water.\\"", null, 10);''')
sub(P, '''G.After(8.2, () => G.Say(''', '''G.After(10.2, () => G.Say(''')
sub(P, '''G.Say("A wagon on its side, and the ditch beside it full of the drowned. They were waiting.", null, 5);''',
    '''G.Say("A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting.", null, 5);''')
sub(P, '''G.Say("The last of them falls back into the ditch and stays there.", null, 4);''',
    '''G.Say("The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most. Her boots are new.", null, 5);''')
sub(P, '''When the dark comes again, it will burn again, from nothing.", null, 10));''',
    '''When the dark comes again, it will burn again, from nothing. You try to call up your mother's face, and find it is not quite where you left it.", null, 11));''')

V = "logic/Play/Zones/Verge.cs"
sub(V, '''G.Say("The fire takes the tents, and the cages with them. There is screaming, and then there is not.", null, 6);''',
    '''G.Say("The fire takes the tents, and then the cages. There is screaming, and the smell, and hands through the bars; and then there is only the fire.", null, 7);''')
sub(V, '''"A teamster, thin and grey, stumbles out and grips your arm.",''',
    '''"A teamster, thin and grey, stumbles out and grips your arm. His nails are broken to the quick from the bars.",''')
sub(V, '''        if (!blown) G.Say("Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.", null, 4);''',
    '''        if (!blown) G.Say("Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.", null, 4);
        // The Dig's people pay for it too: blasting the hill buries the ones working inside it.
        else G.After(3, () => G.Say("When the dust comes down, the hillside is a wound. Small shapes crawl out of it with their lamps still lit. Some of them are on fire. Most of them do not crawl far.", null, 7));''')
print("ok")
