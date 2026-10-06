"""Print a WAV's RIFF chunks and any text metadata (INFO, bext, iXML) - often the library's name."""
import struct, sys, os, re
for p in sys.argv[1:]:
    try:
        b = open(p, 'rb').read()
    except Exception as e:
        print(p, e); continue
    if b[:4] != b'RIFF':
        print(os.path.basename(p), 'not RIFF', b[:4]); continue
    i = 12; chunks = []; text = []
    while i + 8 <= len(b):
        cid = b[i:i + 4]; n = struct.unpack('<I', b[i + 4:i + 8])[0]
        chunks.append(cid.decode('latin1'))
        if cid in (b'LIST', b'bext', b'iXML', b'_PMX', b'ID3 ', b'id3 ', b'cue ', b'smpl', b'umid'):
            body = b[i + 8:i + 8 + min(n, 4000)]
            t = re.sub(rb'[^\x20-\x7e]+', b' ', body).decode('latin1').strip()
            text.append(f'{cid.decode("latin1")}: {t[:500]}')
        i += 8 + n + (n & 1)
    print('=====', os.path.basename(p), chunks)
    for t in text: print('   ', t)
