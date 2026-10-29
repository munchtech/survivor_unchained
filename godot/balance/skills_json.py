"""The tuning scripts' hands on data/content/skills.json. They change damage
numbers in the text itself, so the file keeps its layout (SkillsJson.Write's)
and the diff shows only the numbers that moved."""
import json, os, re

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'content', 'skills.json')

def read():
    return open(PATH, encoding='utf-8').read()

def write(text):
    open(PATH, 'w', encoding='utf-8', newline='\n').write(text)

def unions():
    return json.loads(read())['unions']

def _span(text, id_):
    """From a skill's or evolution's "id" to the next "id" (its own fields)."""
    m = re.search(r'"id": "%s",' % re.escape(id_), text)
    if not m:
        return None
    n = re.search(r'"id": "', text[m.end():])
    return m.start(), (m.end() + n.start()) if n else len(text)

def scale_base(text, skill, f, digits=2):
    """The skill's base damage times f; the text unchanged if it has none."""
    return _scale(text, skill, r'("base": \{\s*(?:"cooldown": [\d.]+,\s*)?"damage": )([\d.]+)', f, digits)

def scale_mods(text, evo, f, digits=2):
    """An evolution's damage multiplier times f; the text unchanged if it has none."""
    return _scale(text, evo, r'("mods": \{\s*"damage": )([\d.]+)', f, digits)

def _scale(text, id_, pat, f, digits):
    s = _span(text, id_)
    if not s:
        return text
    a, b = s
    block = re.sub(pat, lambda m: m.group(1) + fmt(float(m.group(2)) * f, digits), text[a:b], count=1)
    return text[:a] + block + text[b:]

def fmt(v, digits=2):
    return ('%.*f' % (digits, v)).rstrip('0').rstrip('.')
