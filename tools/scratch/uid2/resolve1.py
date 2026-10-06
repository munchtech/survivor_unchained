import re
p = 'godot/src/Actors/People.cs'
s = open(p, encoding='utf-8', newline='').read()
s2 = re.sub(r'<<<<<<< HEAD\r?\n(.*?)=======\r?\n(.*?)>>>>>>> [^\r\n]*\r?\n', lambda m: m.group(1) + m.group(2), s, flags=re.S)
assert '<<<<<<<' not in s2 and s2 != s
open(p, 'w', encoding='utf-8', newline='').write(s2)
print('resolved')
