#!/usr/bin/env bash
# Fetch pages with curl (Windows' own certificate store), then strip them to text
# with fetch.py's text_of. Usage: curlfetch.sh name url [name url ...]
cd "$(dirname "$0")"
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'
while [ $# -ge 2 ]; do
  n="$1"; u="$2"; shift 2
  curl -sL -A "$UA" -H 'Accept-Language: en-US,en;q=0.9' "$u" -o "$n.html" -w "$n %{http_code} %{size_download}\n"
  python -c "
import sys,importlib.util
spec=importlib.util.spec_from_file_location('f','fetch.py')
src=open('fetch.py',encoding='utf-8').read().split('args = sys.argv')[0]
ns={}; exec(src,ns)
s=open('$n.html',encoding='utf-8',errors='ignore').read()
open('$n.txt','w',encoding='utf-8').write('$u\n\n'+ns['text_of'](s))
"
done
