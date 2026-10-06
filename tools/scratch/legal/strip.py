"""Strip saved HTML pages to readable text. Usage: python strip.py name [name ...]"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def text_of(s):
    t = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', s, flags=re.S | re.I)
    t = re.sub(r'<(br|/p|/div|/li|/tr|/td|/th)[^>]*>', '\n', t, flags=re.I)
    t = re.sub(r'</h\d>', '\n', t, flags=re.I)
    t = re.sub(r'<li[^>]*>', '\n- ', t, flags=re.I)
    t = re.sub(r'<h(\d)[^>]*>', lambda m: '\n' + '#' * int(m.group(1)) + ' ', t, flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = re.sub(r'[ \t\r]+', ' ', t)
    return re.sub(r'\n\s*\n+', '\n\n', t)


for name in sys.argv[1:]:
    s = open(os.path.join(HERE, name + '.html'), encoding='utf-8', errors='ignore').read()
    t = text_of(s)
    open(os.path.join(HERE, name + '.txt'), 'w', encoding='utf-8').write(t)
    print(name, len(t))
