import os
p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'c06_forty_one_mouths.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


rep("""  (`redcowl.who`); the cages fed first (`redcowl.cages`: "I feed them before I
  feed my own"); the children (Act 2: what Redcowl is fighting for when he
  fights the Dig).""",
    """  (`redcowl.who`); the cages fed first, shown here, so that his own account of
  the cages can end on "...Ask them if they're hungry." (`redcowl.cages`) instead of
  telling what the scene has shown; the children (Act 2: what Redcowl is fighting
  for when he fights the Dig).""")
rep("""Then Redcowl's first line, by variant (`redcowl.first` #0 to #5, existing):
the crossbows (level 8 or more, or 12 Kerchiefs killed); her colours; the
arcanist; the reaver; a woman; anyone else.""",
    """Then Redcowl's first line, by variant (`redcowl.first` #0 to #4, existing):
the crossbows (level 8 or more, or 12 Kerchiefs killed); her colours; the
arcanist; the reaver; anyone else. (The variant for a woman, about his lads not
having seen one in a month, is cut: this camp is full of women and children, and
the scene exists to overturn exactly that menace.)""")
rep("""- **A woman** (#4): in shot 2 two of the men by the fires stand up; the woman
  hanging washing says something to them we do not hear, and they sit down again.
""", "")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
