"""Fetch a page and save its readable text, for citing primary sources.
Usage: python fetch.py <out-name> <url> [<out-name> <url> ...]"""
import html
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'


def text_of(s):
    m = re.search(r'<div class="documentation_bbcode">(.*)', s, re.S)
    t = m.group(1) if m else s
    t = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', t, flags=re.S | re.I)
    t = re.sub(r'<(br|/p|/div|/li|/tr|/td|/th)[^>]*>', '\n', t, flags=re.I)
    t = re.sub(r'</h\d>', '\n', t, flags=re.I)
    t = re.sub(r'<li[^>]*>', '\n- ', t, flags=re.I)
    t = re.sub(r'<h(\d)[^>]*>', lambda m: '\n' + '#' * int(m.group(1)) + ' ', t, flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = re.sub(r'[ \t\r]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n\n', t)
    return t


args = sys.argv[1:]
for name, url in zip(args[0::2], args[1::2]):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-GB,en;q=0.9'})
        raw = urllib.request.urlopen(req, timeout=60).read()
        s = raw.decode('utf-8', 'ignore')
        with open(os.path.join(HERE, name + '.html'), 'w', encoding='utf-8') as f:
            f.write(s)
        t = text_of(s)
        with open(os.path.join(HERE, name + '.txt'), 'w', encoding='utf-8') as f:
            f.write(url + '\n\n' + t)
        print(name, len(s), len(t))
    except Exception as e:  # report and carry on with the rest
        print(name, 'FAILED', e)
