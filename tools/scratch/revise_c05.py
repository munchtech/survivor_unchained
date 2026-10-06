import os
p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'c05_kneeling.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


rep("""  **He hides** the sick ones until he has decided about her. **He reveals**,
  only to the camera, that he can smell what she is: the first creature in the
  game who knows, and he lets her in anyway.""",
    """  **He hides** the sick ones until he has decided about her. **He reveals**,
  only to the camera, that he can smell what she is. The Warden knew it, and
  Grimtunnel; he is the first who knows and lets her in anyway.""")
rep("on the ridge 47 m south-east at (-26, -40)", "on the ridge 60 m south-east at (-26, -40)")
rep("Greymuzzle comes out of the shadow alone, slowly, and stops. Line `greymuzzle.first` begins. |",
    "Greymuzzle comes out of the shadow alone, slowly, and stops. |")
rep("wolves lying in the dirt that do not get up. The line ends. **Choice 1**",
    "wolves lying in the dirt that do not get up. **Choice 1**")
rep("she rises and follows him into the shadow. Line `greymuzzle.show` begins. |",
    "she rises and follows him into the shadow. |")
rep("then back at her, and waits. The line ends. **Choice 2**", "then back at her, and waits. **Choice 2**")
rep("watching the Hollow. When the camera finds her she turns and goes. | 3.0 |",
    "watching the Hollow. When the camera finds her she does not go: she sits down on the ridge, her crossbow across her knees, to watch the rest. | 3.5 |")
rep("(`greymuzzle.ally`, line read.)", "(`greymuzzle.ally`.)")
start = s.index("## Lines")
end = s.index("## Sound")
s = s[:start] + """## Lines

None. The cinematic is wordless: `VOICES.md` says Greymuzzle never speaks and
that everything he says is the narrator watching what he does, and in a
cinematic the camera is that narrator. The conversation's narration
(`greymuzzle.first`; `greymuzzle.show`, with its variant for Maeca's lover;
`greymuzzle.ally`) stays in the data, for the conversation as text when the
cinematic is skipped or switched off; the cinematic plays it as picture, beat for
beat. The choices come up in the lower bar, read, not voiced.

""" + s[end:]
rep("- **Subtitles.** The narrator in italics.", "- **Subtitles.** None; the choices only.")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
