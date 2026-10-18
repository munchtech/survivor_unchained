"""The legal gate: the Steam coverage check (tools/legal/motioncheck/) run only on what changed.
The owner, 17 October: "having to legal check everytime we change an outfit or animation is going
to be an issue. how can we ensure that it can be done now and be taken care of not draining
everytime we do ANYTHING". So: one command, once per merge request, as a background Bash job;
it prints ONE line, and the details go to files.

    python tools/legal/gate.py            fingerprint, compare, run what changed, one line back
    python tools/legal/gate.py --dry      the scope only (seconds, no Godot)
    python tools/legal/gate.py --full     every outfit, every clip
    python tools/legal/gate.py --restamp  re-stamp the record's fingerprints after a change of scheme (no Godot; only if nothing
                                          changed since the passes under the old scheme, else refuses and lists)
    --root <checkout>   the checkout to fingerprint and shoot (default: this file's). A worktree
                        is imported first (inside the turn); the main checkout is not, unless --import.
    --import            import the project first (inside the godot turn)
    --passed <file>     the record (default <root>/docs/legal/passed.json)
    --only <o,..>       limit to these outfits (still scoped by what changed)
    --clips <a,..>      limit to these clips (still scoped by what changed)

What coverage depends on (fingerprint(); if in doubt a thing is in):
- GLOBAL (a change runs all four outfits, every clip): her body (heroine.glb: positions, normals
  (the tuck pushes skin in along them), UVs (the areola is read from her paint by UV), skin
  weights, blend shapes, the skeleton and its rest pose, materials' settings); her paint's
  pixels over her breasts only (marks_section.py finds each areola from the paint); her head
  parts as occluders (positions and weights, not their blend shapes, UVs or paint); the ponytail
  the check wears (geometry, weights and its cards' alpha: hair can hide or bare a breast); the
  shaders that tuck, hide, discard or move a vertex (heroine_skin, heroine_outfit, fur_shell,
  sheer, heroine_hair and their includes; comments ignored; fragment() and light() reduced to what
  writes ALPHA*, DEPTH or discards and what those read, so colour and light edits don't count, and
  uniforms nothing kept reads are dropped; a file that doesn't parse counts whole); her runtime motion code (HerJiggle,
  HerPose, HerJoints, HairSway, HerFaceLife; rig_helpers.json); lookdev.gd (the check is built
  from it), the import script and the models' import settings; project.godot's rendering,
  shader_globals and importer_defaults; the motion check's own files; the Godot binary.
- PER OUTFIT (that outfit, every clip): its gltf (every mesh attribute, weights, skin, nodes,
  materials), outfit_materials.json's rows for its materials (kind, pull: view_pull moves
  vertices), the alpha channel of any texture on a material with alpha, and its tuck: its own
  channel of her vertex colours (warden R, arcanist G, reaver B, ranger A: lookdev.gd reads
  only that one for that outfit).
- PER CLIP (that clip on all four): the clip's decoded keys in godot/art/anim/heroine.res
  (godot_res.py), so repacking the library leaves untouched clips as they were.
NOT in it: her body's and head's paint off the breasts, outfit and hair colour, other hair
styles, the face's blend shapes, heroine_clips.json, the game's own People.cs (the check
emulates People in lookdev.gd: if the game diverges from lookdev, the check can't see it).

docs/legal/passed.json keeps, per outfit, the fingerprints of its last PASS and per clip the
clip's fingerprint when that clip last passed on it, with commit, date and counts. The pass bar
is count.py's, unchanged: areola and genital strip in 0 frames at 6 px (docs/team/legal.md),
FLAT asserting 0, and every clip shot. Pictures go under <root>/.legal/ (git-ignored: test
tints, and they can show her bare). Heavy runs take a godot turn per outfit and give it back.
Exit: 0 pass or skip, 1 fail, 2 blocked (stale checkout, busy too long, error)."""
import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import re
import signal
import struct
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import godot_res  # noqa: E402

OUTFITS = ['warden', 'arcanist', 'ranger', 'reaver']
CHANNEL = {'warden': 0, 'arcanist': 1, 'reaver': 2, 'ranger': 3}  # lookdev.gd's hide_skin order
MAIN = os.path.normpath(os.path.join(HERE, '..', '..'))
GODOT = os.environ.get('GODOT', r'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe')
BASH = r'C:\Program Files\Git\bin\bash.exe' if os.path.exists(r'C:\Program Files\Git\bin\bash.exe') else 'bash'
MIN_PX = 6  # count.py's pass bar as docs/team/legal.md gives it (frames with 6 px or more)
SHADERS = ['heroine_skin', 'heroine_outfit', 'fur_shell', 'sheer', 'heroine_hair']
CODE = ['HerJiggle', 'HerPose', 'HerJoints', 'HairSway', 'HerFaceLife']
HAIR = 'ponytail'  # run.sh's HAIR=
TURN = 'legal gate'


def h(*parts):
    s = hashlib.sha1()
    for p in parts:
        s.update(p if isinstance(p, bytes) else json.dumps(p, sort_keys=True, default=str).encode())
        s.update(b'\0')
    return s.hexdigest()[:16]


# ---- glTF ----------------------------------------------------------------------------------
COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}


class Gltf:
    def __init__(self, path):
        self.path = path
        d = open(path, 'rb').read()
        if d[:4] == b'glTF':
            n = struct.unpack_from('<I', d, 12)[0]
            self.j = json.loads(d[20:20 + n])
            m = struct.unpack_from('<I', d, 20 + n)[0]
            self.bufs = [d[28 + n:28 + n + m]]
        else:
            self.j = json.loads(d)
            self.bufs = [open(os.path.join(os.path.dirname(path), b['uri']), 'rb').read() for b in self.j.get('buffers', [])]

    def view(self, i):
        v = self.j['bufferViews'][i]
        o = v.get('byteOffset', 0)
        return self.bufs[v['buffer']][o:o + v['byteLength']], v.get('byteStride')

    def acc(self, i):
        """The accessor's values as a (count, n) array (sparse accessors folded in)."""
        a = self.j['accessors'][i]
        dt = np.dtype(COMP[a['componentType']])
        n = NCOMP[a['type']]
        cnt = a['count']
        if 'bufferView' in a:
            b, stride = self.view(a['bufferView'])
            o = a.get('byteOffset', 0)
            row = n * dt.itemsize
            if stride and stride != row:
                out = np.stack([np.frombuffer(b, dt, n, o + k * stride) for k in range(cnt)])
            else:
                out = np.frombuffer(b, dt, cnt * n, o).reshape(cnt, n).copy()
        else:
            out = np.zeros((cnt, n), dt)
        if 'sparse' in a:
            sp = a['sparse']
            ib, _ = self.view(sp['indices']['bufferView'])
            idx = np.frombuffer(ib, COMP[sp['indices']['componentType']], sp['count'], sp['indices'].get('byteOffset', 0))
            vb, _ = self.view(sp['values']['bufferView'])
            out[idx] = np.frombuffer(vb, dt, sp['count'] * n, sp['values'].get('byteOffset', 0)).reshape(-1, n)
        return out

    def accd(self, i):
        a = self.j['accessors'][i]
        return h({k: a.get(k) for k in ('componentType', 'type', 'count', 'normalized')}, self.acc(i).tobytes())

    def image(self, i):
        im = self.j['images'][i]
        if 'bufferView' in im:
            return self.view(im['bufferView'])[0]
        f = os.path.join(os.path.dirname(self.path), im['uri'])
        return open(f, 'rb').read() if os.path.exists(f) else None

    def skeleton(self):
        nodes = [{k: n.get(k) for k in ('name', 'children', 'translation', 'rotation', 'scale', 'matrix', 'mesh', 'skin')} for n in self.j['nodes']]
        skins = [dict(s, ibm=self.accd(s['inverseBindMatrices']) if 'inverseBindMatrices' in s else None) for s in self.j.get('skins', [])]
        return h(nodes, skins, self.j.get('scenes'), self.j.get('scene'))

    def materials(self):
        return h(self.j.get('materials'), self.j.get('textures'), self.j.get('samplers'))

    def prim(self, p, attrs=None, targets=True):
        a = {k: self.accd(v) for k, v in sorted(p['attributes'].items()) if attrs is None or attrs(k)}
        t = [{k: self.accd(v) for k, v in sorted(tg.items())} for tg in p.get('targets', [])] if targets else None
        return h(a, self.accd(p['indices']) if 'indices' in p else None, p.get('mode'), p.get('material'), t)


def alpha_of(png):
    from PIL import Image
    if png is None:
        return 'missing'
    im = Image.open(io.BytesIO(png))
    if 'A' not in im.getbands():
        return 'opaque'
    return h(np.asarray(im.getchannel('A')).tobytes())


# ---- what coverage depends on ---------------------------------------------------------------
def src_text(path, kind):
    """A source file with its comments dropped where that's safe (a comment edit is not a change)."""
    if not os.path.exists(path):
        return 'missing'
    s = open(path, encoding='utf-8-sig', errors='replace').read()
    if kind == 'shader':
        s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
        s = '\n'.join(l if l.lstrip().startswith('#include') else l.split('//')[0] for l in s.splitlines())
    elif kind == 'cs':
        s = '\n'.join(l for l in s.splitlines() if not l.lstrip().startswith('//'))
    elif kind == 'gd':
        s = '\n'.join(l for l in s.splitlines() if not l.lstrip().startswith('#'))
    return '\n'.join(l.rstrip() for l in s.splitlines() if l.strip())


STOP = set("""void bool int uint float double vec2 vec3 vec4 ivec2 ivec3 ivec4 uvec2 uvec3 uvec4 bvec2 bvec3 bvec4
mat2 mat3 mat4 sampler2D sampler3D samplerCube sampler2DArray isampler2D usampler2D const in out inout uniform varying flat
smooth highp mediump lowp if else for while do switch case default true false""".split())
ALWAYS_UNIFORM = ('alpha', 'discard', 'hide', 'tuck', 'cut', 'clip', 'mask', 'test_', 'legal')
SEED = re.compile(r'\b(?:ALPHA\w*|DEPTH|discard|return)\b')
ASSIGN = re.compile(r'(\w+)\s*(?:\[[^\]]*\])?\s*(?:\.\w+\s*(?:\[[^\]]*\])?\s*)*(?:[-+*/%&|^]|<<|>>)?=(?!=)')
IDENT = re.compile(r'[A-Za-z_]\w*')


def _items(t):
    """Top-level items of a (comment-free) shader: each ends at ';' or at the closing brace of a function."""
    out, buf, br, pa = [], '', 0, 0
    for line in t.split('\n'):
        if line.lstrip().startswith('#'):
            if buf.strip() or br or pa:
                raise ValueError('directive inside an item')
            out.append(line.strip())
            continue
        for ch in line + ' ':
            buf += ch
            if ch == '{':
                br += 1
            elif ch == '}':
                br -= 1
                if br < 0:
                    raise ValueError('brace')
                if br == 0 and pa == 0 and not buf.lstrip().startswith('struct'):
                    out.append(buf.strip())
                    buf = ''
            elif ch == '(':
                pa += 1
            elif ch == ')':
                pa -= 1
            elif ch == ';' and br == 0 and pa == 0:
                out.append(buf.strip())
                buf = ''
    if buf.strip() or br or pa:
        raise ValueError('unterminated')
    return [re.sub(r'\s+', ' ', i) for i in out if i.strip(' ;')]


def _body_nodes(body):
    """A function body as a tree of {'k': stmt|block, 'text', 'kids', 'chain'} (chain: an else, or the while of a do,
    joins the node before it)."""
    root = {'kids': []}
    stack = [root]
    buf, pa = '', 0

    def add(node, text):
        kids = stack[-1]['kids']
        node['chain'] = bool(kids) and (text.startswith('else') or (text.startswith('while') and kids[-1].get('text') == 'do'))
        kids.append(node)

    for ch in body:
        if ch == '(':
            pa += 1
        elif ch == ')':
            pa -= 1
        if pa == 0 and ch == '{':
            t = re.sub(r'\s+', ' ', buf).strip()
            n = {'k': 'block', 'text': t, 'kids': [], 'keep': False}
            add(n, t)
            stack.append(n)
            buf = ''
        elif pa == 0 and ch == '}':
            t = re.sub(r'\s+', ' ', buf).strip()
            if t:
                add({'k': 'stmt', 'text': t, 'kids': [], 'keep': False}, t)
            buf = ''
            if len(stack) < 2:
                raise ValueError('brace')
            stack.pop()
        elif pa == 0 and ch == ';':
            t = re.sub(r'\s+', ' ', buf).strip()
            if t:
                add({'k': 'stmt', 'text': t, 'kids': [], 'keep': False}, t)
            buf = ''
        else:
            buf += ch
    if len(stack) != 1 or pa != 0 or buf.strip():
        raise ValueError('unbalanced')
    return root


def _reduce_body(body):
    """The statements of fragment()/light() that can change coverage (see the docstring), as text."""
    root = _body_nodes(body)
    flat = []

    def walk(n, anc):
        for k in n['kids']:
            k['anc'] = anc
            flat.append(k)
            walk(k, anc + [k])
    walk(root, [])
    for n in flat:
        txt = n['text']
        n['ids'] = {i for i in IDENT.findall(txt) if i not in STOP}
        if n['k'] == 'stmt':
            d = {m.group(1) for m in ASSIGN.finditer(txt)} if '=' in txt else set()
            n['defs'] = (d or n['ids']) - STOP
            n['seed'] = bool(SEED.search(txt))
            n['loopctl'] = bool(re.search(r'\b(?:break|continue)\b', txt))
    chains = []

    def groups(n):
        cur = None
        for k in n['kids']:
            if k['chain'] and cur is not None:
                cur.append(k)
            else:
                cur = [k]
                chains.append(cur)
            groups(k)
    groups(root)
    needed = set()

    def keep(n):
        if not n['keep']:
            n['keep'] = True
            needed.update(n['ids'])
            return True
        return False
    changed = True
    while changed:
        changed = False
        for n in flat:
            if n['k'] == 'stmt' and not n['keep']:
                if n['loopctl']:
                    if any(a['keep'] and re.match(r'(for|while|do|switch)\b', a['text']) for a in n['anc']):
                        changed |= keep(n)
                elif n['seed'] or (n['defs'] & needed):
                    changed |= keep(n)
        for n in reversed(flat):
            if n['k'] == 'block' and not n['keep'] and any(k['keep'] for k in n['kids']):
                changed |= keep(n)
        for c in chains:
            if any(n['keep'] for n in c):
                for n in c:
                    changed |= keep(n)

    def emit(n):
        out = []
        for k in n['kids']:
            if k['keep']:
                out.append(k['text'] + (' {' + ' '.join(emit(k)) + '}' if k['k'] == 'block' else ';'))
        return out
    return ' '.join(emit(root))


def reduce_shader(t):
    """-> ([non-uniform kept strings], [(uniform name, its declaration)]); raises on anything it can't parse."""
    plain, unis = [], []
    for it in _items(t):
        if re.match(r'(?:(?:global|instance)\s+)?uniform\b', it):
            head = re.split(r'[:=]', it, maxsplit=1)[0]
            head = re.sub(r'\[[^\]]*\]', '', head).split()
            unis.append((head[-1], it))
            continue
        m = re.match(r'(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*\{', it)
        if m and m.group(1) in ('fragment', 'light'):
            body = it[it.index('{') + 1:it.rindex('}')]
            plain.append(it[:it.index('{')] + '{' + _reduce_body(body) + '}')
        else:
            plain.append(it)
    return plain, unis


def motion_uniforms(root):
    """Uniform names the motion check sets or injects (tools/legal/motioncheck/), plus the ones it is known to."""
    names = {'test_flat', 'tuck_channel'}
    mc = os.path.join(root, 'tools', 'legal', 'motioncheck')
    if os.path.isdir(mc):
        for f in os.listdir(mc):
            fp_ = os.path.join(mc, f)
            if os.path.isfile(fp_) and not f.endswith('.pyc'):
                x = open(fp_, encoding='utf-8', errors='replace').read()
                names.update(re.findall(r'set_shader_parameter\(\\?"(\w+)', x))
                names.update(re.findall(r'uniform\s+\w+\s+(\w+)', x))
    return names


def shader_fp_old(root, name, seen):
    """The whole text of the shader minus comments (the scheme before the coverage-only one; --restamp uses it)."""
    p = os.path.join(root, 'godot', 'shaders', name)
    if p in seen:
        return {}
    seen.add(p)
    t = src_text(p, 'shader')
    out = {name: h(t)}
    for inc in re.findall(r'#include\s+"res://([^"]+)"', t):
        out.update(shader_fp_old(root, os.path.relpath(os.path.join(root, 'godot', inc), os.path.join(root, 'godot', 'shaders')), seen))
    return out


def _includes(root, t):
    return [os.path.relpath(os.path.join(root, 'godot', inc), os.path.join(root, 'godot', 'shaders'))
            for inc in re.findall(r'#include\s+"res://([^"]+)"', t)]


def _corpus(root, name, seen, parts):
    """All the text coverage could be read from, over a shader and its includes (reduced where that parses)."""
    p = os.path.join(root, 'godot', 'shaders', name)
    if p in seen:
        return
    seen.add(p)
    t = src_text(p, 'shader')
    try:
        parts.extend(reduce_shader(t)[0])
    except Exception:
        parts.append(t)
    for inc in _includes(root, t):
        _corpus(root, inc, seen, parts)


def shader_fp(root, name, seen):
    """Per shader file, a fingerprint of what can change coverage: everything but what feeds only colour and light
    (fragment()/light() reduced to alpha, depth, discard and what they read; uniforms nothing kept reads are dropped).
    If the file doesn't parse, its whole text, as before."""
    p = os.path.join(root, 'godot', 'shaders', name)
    if p in seen:
        return {}
    seen.add(p)
    t = src_text(p, 'shader')
    try:
        plain, unis = reduce_shader(t)
        parts = []
        _corpus(root, name, set(), parts)
        corpus = '\n'.join(parts)
        mot = motion_uniforms(root)
        keepu = [d for n, d in unis if n in mot or any(w in n.lower() for w in ALWAYS_UNIFORM) or re.search(r'\b%s\b' % re.escape(n), corpus)]
        out = {name: h(plain, keepu)}
    except Exception:
        out = {name: h(t)}
    for inc in _includes(root, t):
        out.update(shader_fp(root, inc, seen))
    return out


def import_params(path):
    if not os.path.exists(path):
        return 'missing'
    s = open(path, encoding='utf-8', errors='replace').read()
    return h(s.split('[params]', 1)[1] if '[params]' in s else s)


def project_sections(root):
    s = open(os.path.join(root, 'godot', 'project.godot'), encoding='utf-8', errors='replace').read()
    secs = re.split(r'^\[(\w+)\]\s*$', s, flags=re.M)
    keep = {secs[i]: secs[i + 1].strip() for i in range(1, len(secs) - 1, 2) if secs[i] in ('rendering', 'shader_globals', 'importer_defaults')}
    return h(keep)


def fingerprint(root, old_shaders=False):
    """-> {'global': {part: h}, 'outfit': {o: h}, 'tuck': {o: h}, 'clips': {clip: h}}"""
    G = {}
    people = os.path.join(root, 'godot', 'art', 'people')
    body = Gltf(os.path.join(people, 'heroine.glb'))
    G['body skeleton'] = body.skeleton()
    G['body materials'] = body.materials()
    colour = {o: [] for o in OUTFITS}
    skin, occl, paint = [], [], []
    joint_names = [body.j['nodes'][n].get('name', '') for n in body.j['skins'][0]['joints']] if body.j.get('skins') else []
    breast = [i for i, n in enumerate(joint_names) if 'breast' in n.lower()]
    for m in body.j['meshes']:
        has_colour = any('COLOR_0' in p['attributes'] for p in m['primitives'])
        for p in m['primitives']:
            if has_colour:  # her skin meshes: everything but tangents and the colour (split below)
                skin.append((m.get('name'), m.get('weights'), m.get('extras'),
                             body.prim(p, lambda k: k != 'TANGENT' and not k.startswith('COLOR'))))
                if 'COLOR_0' in p['attributes']:
                    c = body.acc(p['attributes']['COLOR_0'])
                    for o in OUTFITS:
                        k = CHANNEL[o]
                        colour[o].append(h(c[:, k].tobytes()) if c.shape[1] > k else 'none')
                # her paint over her breasts: the UV box of every vertex any breast bone moves
                mat = body.j['materials'][p['material']] if 'material' in p else {}
                tex = mat.get('pbrMetallicRoughness', {}).get('baseColorTexture')
                if tex is not None and breast and 'TEXCOORD_0' in p['attributes']:
                    js = body.acc(p['attributes']['JOINTS_0'])
                    ws = body.acc(p['attributes']['WEIGHTS_0']).astype(np.float64)
                    sel = (np.isin(js, breast) & (ws > 0)).any(axis=1)
                    if sel.any():
                        from PIL import Image
                        uv = body.acc(p['attributes']['TEXCOORD_0'])[sel]
                        im = Image.open(io.BytesIO(body.image(body.j['textures'][tex['index']]['source']))).convert('RGB')
                        W, H = im.size
                        box = (max(int(uv[:, 0].min() * W) - 2, 0), max(int(uv[:, 1].min() * H) - 2, 0),
                               min(int(uv[:, 0].max() * W) + 3, W), min(int(uv[:, 1].max() * H) + 3, H))
                        paint.append((box, h(np.asarray(im.crop(box)).tobytes())))
            else:  # her head's parts: occluders only
                occl.append((m.get('name'), body.prim(p, lambda k: k in ('POSITION',) or k.startswith(('JOINTS', 'WEIGHTS')), targets=False)))
    G['body skin meshes'] = h(skin)
    G['body breast paint'] = h(paint)
    G['head parts (occluders)'] = h(occl)
    G['body import'] = import_params(os.path.join(people, 'heroine.glb.import'))
    hp = os.path.join(people, 'heroine_hair_%s.gltf' % HAIR)
    if os.path.exists(hp):
        hair = Gltf(hp)
        alphas = [alpha_of(hair.image(i)) for i in range(len(hair.j.get('images', [])))]
        G['hair ' + HAIR] = h(hair.skeleton(), hair.materials(), alphas,
                              [hair.prim(p, lambda k: k != 'TANGENT' and not k.startswith('COLOR')) for m in hair.j['meshes'] for p in m['primitives']],
                              import_params(hp + '.import'),
                              h(open(os.path.join(people, 'heroine_hair_%s.chain.json' % HAIR), 'rb').read()) if os.path.exists(os.path.join(people, 'heroine_hair_%s.chain.json' % HAIR)) else None)
    else:
        G['hair ' + HAIR] = 'missing'
    seen = set()
    for s in SHADERS:
        for k, v in (shader_fp_old if old_shaders else shader_fp)(root, s + '.gdshader', seen).items():
            G['shader ' + k] = v
    for c in CODE:
        G['code %s.cs' % c] = h(src_text(os.path.join(root, 'godot', 'src', 'Actors', c + '.cs'), 'cs'))
    rh = os.path.join(people, 'rig_helpers.json')
    G['rig_helpers.json'] = h(open(rh, 'rb').read()) if os.path.exists(rh) else 'missing'
    G['lookdev.gd'] = h(src_text(os.path.join(root, 'godot', 'tools_scenes', 'lookdev.gd'), 'gd'))
    G['import_mipmaps.gd'] = h(src_text(os.path.join(root, 'godot', 'tools_scenes', 'import_mipmaps.gd'), 'gd'))
    G['project.godot rendering'] = project_sections(root)
    mc = os.path.join(root, 'tools', 'legal', 'motioncheck')
    for f in sorted(os.listdir(mc)):
        if os.path.isfile(os.path.join(mc, f)) and not f.endswith('.pyc'):
            G['tool ' + f] = h(open(os.path.join(mc, f), 'rb').read().replace(b'\r\n', b'\n'))
    G['godot binary'] = h(os.path.basename(GODOT), os.path.getsize(GODOT) if os.path.exists(GODOT) else None)

    table = json.load(open(os.path.join(people, 'outfit_materials.json'), encoding='utf-8'))
    O, T = {}, {}
    for o in OUTFITS:
        p = os.path.join(people, 'heroine_outfit_%s.gltf' % o)
        if not os.path.exists(p):
            O[o] = 'missing'
        else:
            g = Gltf(p)
            mats = g.j.get('materials', [])
            alphas = {}
            for m in mats:
                if m.get('alphaMode', 'OPAQUE') != 'OPAQUE':
                    t = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
                    if t is not None:
                        alphas[m['name']] = alpha_of(g.image(g.j['textures'][t['index']]['source']))
            O[o] = h(g.skeleton(), g.materials(), alphas,
                     [(m.get('name'), m.get('weights'), [g.prim(pr) for pr in m['primitives']]) for m in g.j['meshes']],
                     {m.get('name'): table.get(m.get('name')) for m in mats}, import_params(p + '.import'))
        T[o] = h(colour[o])
    try:
        C = godot_res.clips(os.path.join(root, 'godot', 'art', 'anim', 'heroine.res'))
    except Exception as e:  # unreadable: every clip changed
        G['clip library unreadable'] = h(str(e), time.time())
        C = {}
    return {'global': G, 'outfit': O, 'tuck': T, 'clips': C}


def clip_lists(root, scratch):
    """run.sh's own clips per outfit (LIST=1: it prints them and runs nothing)."""
    os.makedirs(scratch, exist_ok=True)
    env = dict(os.environ, LIST='1', OUT=scratch.replace('\\', '/'), ONLY=' '.join(OUTFITS))
    env.pop('CLIPS', None)
    r = subprocess.run([BASH, os.path.join(root, 'tools', 'legal', 'motioncheck', 'run.sh').replace('\\', '/'), 'all'],
                       env=env, capture_output=True, text=True, timeout=60)
    out = {o: [] for o in OUTFITS}
    for line in r.stdout.splitlines():
        p = line.split()
        if len(p) == 3 and p[0] == 'LIST' and p[1] in out:
            out[p[1]].append(p[2])
    if not all(out.values()):
        raise SystemExit('LEGAL BLOCKED: run.sh LIST=1 gave no clips (%s)' % (r.stderr.strip()[-200:] or 'no output'))
    return out


# ---- scope ----------------------------------------------------------------------------------
def scope(fp, passed, lists, full=False, only=None, clips=None):
    """-> ({outfit: [clips]}, {outfit: reason}, [clips run.sh lists but the library lacks])"""
    lacking = sorted({c for o in lists for c in lists[o] if c not in fp['clips']})
    run, why = {}, {}
    for o in OUTFITS:
        if only and o not in only:
            continue
        mine = [c for c in lists[o] if c in fp['clips'] and (not clips or c in clips)]
        rec = passed.get('outfits', {}).get(o)
        if full:
            r = 'forced (--full)'
        elif not rec:
            r = 'no pass on record'
        else:
            g = [k for k in sorted(set(fp['global']) | set(rec.get('global', {}))) if fp['global'].get(k) != rec.get('global', {}).get(k)]
            r = ('changed: ' + ', '.join(g)) if g else ''
            if not r and fp['outfit'][o] != rec.get('outfit'):
                r = 'its pieces changed'
            if not r and fp['tuck'][o] != rec.get('tuck'):
                r = 'its tuck channel changed'
        if r:
            run[o], why[o] = mine, r
            continue
        cs = [c for c in mine if rec.get('clips', {}).get(c, {}).get('fp') != fp['clips'][c]]
        if cs:
            run[o], why[o] = cs, 'clips changed'
    return run, why, lacking


def scope_line(run, why, lists, passed):
    if not run:
        commits = sorted(((r.get('date', ''), r.get('commit', '?')) for r in passed.get('outfits', {}).values()), reverse=True)
        return 'LEGAL SKIP (unchanged since %s)' % (commits[0][1] if commits else '?')
    globals_ = {why[o] for o in run if why[o].startswith(('changed:', 'no pass', 'forced'))}
    if len(run) == 4 and all(len(run[o]) == len(lists[o]) for o in run) and len(globals_) == 1:
        return 'LEGAL SCOPE all 4 outfits x all clips (%d clip runs): %s' % (sum(len(v) for v in run.values()), globals_.pop())
    parts = []
    for o in OUTFITS:
        if o in run:
            n = len(run[o])
            what = 'all %d clips' % n if n == len(lists[o]) else ('%d clips: %s' % (n, ' '.join(run[o])) if n <= 6 else '%d clips' % n)
            parts.append('%s (%s; %s)' % (o, what, why[o]))
    return 'LEGAL SCOPE ' + '; '.join(parts)


# ---- run ------------------------------------------------------------------------------------
def git(root, *a):
    return subprocess.run(['git', *a], cwd=root, capture_output=True, text=True).stdout.strip()


def turn(root, verb, who, wait_min=600):
    t = [sys.executable, os.path.join(MAIN, 'tools', 'turn.py')]
    if verb == 'give':
        subprocess.run(t + ['give', 'godot', who], capture_output=True, text=True)
        return 0, ''
    end = time.time() + wait_min * 60
    while True:
        r = subprocess.run(t + ['take', 'godot', who, '--wait', '20', '--root', root], capture_output=True, text=True, cwd=root)
        if r.returncode != 1 or time.time() > end:
            return r.returncode, (r.stdout + r.stderr).strip()


def summary_of(folder):
    s = open(os.path.join(folder, 'summary.txt'), encoding='utf-8', errors='replace').read()
    res = {'flat': None, 'areola': None, 'strip': None, 'frames': 0, 'closest': {}, 'flagged': []}
    m = re.search(r'FLAT: stray (\d+) px, binding (\d+) px, lone (\d+) px', s)
    if m:
        res['flat'] = sum(int(x) for x in m.groups())
    m = re.search(r'^\w+: (\d+) frames; areola shows in (\d+); genital strip shows in (\d+)', s, re.M)
    if m:
        res['frames'], res['areola'], res['strip'] = (int(x) for x in m.groups())
    for side, v in re.findall(r'^\s+(.+?): closest ([+-]\d+\.\d+) cm', s, re.M):
        res['closest']['L' if 'left' in side.lower() or side.lower().endswith('l') else 'R'] = float(v)
    for nm, kind, px in re.findall(r'flagged: (\S+), (areola|genital strip), (\d+) px', s):
        res['flagged'].append((int(px), kind, nm))
    res['flagged'].sort(reverse=True)
    return res


def run_outfit(root, project, out, o, clips, all_clips, do_import, log):
    os.makedirs(out, exist_ok=True)
    # The label is unique to this process, so giving it back frees exactly what this run took and never another's.
    who = '%s: %s (%d clips, pid %d)' % (TURN, o, len(clips), os.getpid())
    rc = None  # None: the take didn't return (an exception or an interrupt may have landed after it was made)
    try:
        rc, msg = turn(root, 'take', who)
        if rc != 0:
            return {'blocked': msg.splitlines()[-1] if msg else 'turn refused'}
        if do_import:
            with open(os.path.join(out, 'import.log'), 'w') as f:
                subprocess.run([GODOT, '--headless', '--path', project, '--import'], stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT, timeout=3600)
        env = dict(os.environ, OUT=out.replace('\\', '/'), PROJECT=project.replace('\\', '/'), ONLY=o)
        env.pop('LIST', None)
        if len(clips) < len(all_clips):
            env['CLIPS'] = ' '.join(clips)
        else:
            env.pop('CLIPS', None)
        with open(os.path.join(out, 'run.log'), 'w') as f:
            subprocess.run([BASH, os.path.join(root, 'tools', 'legal', 'motioncheck', 'run.sh').replace('\\', '/'), 'all'],
                           env=env, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT)
    finally:
        if rc is None or rc == 0:  # taken, or maybe taken: give back (harmless if it wasn't)
            turn(root, 'give', who)
    with open(os.path.join(out, 'count.txt'), 'w') as f:
        cr = subprocess.run([sys.executable, os.path.join(root, 'tools', 'legal', 'motioncheck', 'count.py'), out, str(MIN_PX)],
                            stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT)
    pngs = os.listdir(out)
    empty = [c for c in clips if not any(n.startswith('%s_%s_' % (o, c)) and n.endswith('.png') and re.match(r'.*_\d\d\.png$', n) for n in pngs)]
    if not os.path.exists(os.path.join(out, 'summary.txt')):
        return {'error': 'count.py wrote no summary (exit %d, see count.txt)' % cr.returncode, 'empty': empty}
    r = summary_of(out)
    r['empty'] = empty
    r['count_exit'] = cr.returncode
    r['pass'] = (r['areola'] == 0 and r['strip'] == 0 and r['flat'] == 0 and not empty and cr.returncode == 0)
    return r


def describe(o, n, r):
    if 'blocked' in r:
        return '%s: blocked (%s)' % (o, r['blocked'])
    if 'error' in r:
        return '%s: %s' % (o, r['error'])
    cl = ' '.join('%s %+.2f' % (k, r['closest'][k]) for k in ('L', 'R') if k in r['closest'])
    s = '%s(%d clips) areola %s strip %s FLAT %s%s' % (o, n, r['areola'], r['strip'], r['flat'] if r['flat'] is not None else 'off',
                                                     (' closest %s cm' % cl) if cl else '')
    if r['empty']:
        s += ' NO FRAMES: ' + ' '.join(r['empty'][:6]) + (' ...' if len(r['empty']) > 6 else '')
    if r['flagged']:
        px, kind, nm = r['flagged'][0]
        m = re.match(r'%s_(.+)_(\w+)_(\d\d)\.png$' % o, nm)
        s += ' (worst: %s %s %s, %s %d px)' % (m.group(1), m.group(2), m.group(3), kind, px) if m else ' (worst: %s %s %d px)' % (nm, kind, px)
    return s


def restamp(root, passed, passed_path):
    """Rewrite the record's fingerprints to the current scheme, without running Godot. Only if the current tree, under
    the OLD (whole-shader) scheme, equals every recorded fingerprint: nothing changed since the passes."""
    rec = passed.get('outfits', {})
    if not rec:
        print('LEGAL RESTAMP: nothing recorded in %s' % passed_path)
        return 0
    old, new = fingerprint(root, True), fingerprint(root)
    diff = []
    for o, e in sorted(rec.items()):
        g = [k for k in sorted(set(old['global']) | set(e.get('global', {}))) if old['global'].get(k) != e.get('global', {}).get(k)]
        if g:
            diff.append('%s global: %s' % (o, ', '.join(g)))
        if old['outfit'].get(o) != e.get('outfit'):
            diff.append('%s: its pieces' % o)
        if old['tuck'].get(o) != e.get('tuck'):
            diff.append('%s: its tuck channel' % o)
        for c, v in sorted(e.get('clips', {}).items()):
            if old['clips'].get(c) != v.get('fp'):
                diff.append('%s clip %s' % (o, c))
    if diff:
        print('LEGAL RESTAMP REFUSED (the tree differs from the recorded passes): ' + '; '.join(diff))
        return 2
    for o, e in rec.items():
        e['global'], e['outfit'], e['tuck'] = new['global'], new['outfit'][o], new['tuck'][o]
    passed['note'] = 'Written by tools/legal/gate.py: the last PASS per outfit and per clip (fingerprints, commit, counts).'
    json.dump(passed, open(passed_path, 'w', encoding='utf-8'), indent=1, sort_keys=True)
    print('LEGAL RESTAMP ok: %d outfits re-stamped to the coverage-only shader scheme, pass status kept' % len(rec))
    return 0


def _term(signum, frame):
    raise SystemExit(3)  # unwinds through run_outfit's finally, which gives the godot turn back


def main():
    for name in ('SIGTERM', 'SIGBREAK'):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), _term)
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--restamp', action='store_true')
    ap.add_argument('--root', default=MAIN)
    ap.add_argument('--import', dest='do_import', action='store_true')
    ap.add_argument('--passed')
    ap.add_argument('--only')
    ap.add_argument('--clips')
    a = ap.parse_args()
    root = os.path.normpath(os.path.abspath(a.root))
    passed_path = a.passed or os.path.join(root, 'docs', 'legal', 'passed.json')
    passed = json.load(open(passed_path, encoding='utf-8')) if os.path.exists(passed_path) and os.path.getsize(passed_path) > 2 else {}
    if a.restamp:
        return restamp(root, passed, passed_path)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    legal = os.path.join(root, '.legal')
    fp = fingerprint(root)
    lists = clip_lists(root, os.path.join(legal, 'list'))
    only = set(a.only.split(',')) if a.only else None
    clips = set(a.clips.split(',')) if a.clips else None
    run, why, lacking = scope(fp, passed, lists, a.full, only, clips)
    line = scope_line(run, why, lists, passed)
    if lacking:
        line += ' [not in the clip library, not shot: %s]' % ' '.join(lacking)
    if a.dry or not run:
        print(line)
        return 0
    base = os.path.join(legal, stamp)
    os.makedirs(base, exist_ok=True)
    project = os.path.join(root, 'godot')
    do_import = a.do_import or os.path.normcase(root) != os.path.normcase(MAIN)
    results = {}
    for o in OUTFITS:
        if o in run and run[o]:
            results[o] = run_outfit(root, project, os.path.join(base, o), o, run[o], [c for c in lists[o] if c in fp['clips']], do_import, None)
            if 'blocked' in results[o]:
                break
    after = fingerprint(root)
    changed = after != fp
    commit = git(root, 'rev-parse', '--short', 'HEAD')
    dirty = bool(git(root, 'status', '--porcelain', '--', 'godot/art/people', 'godot/art/anim', 'godot/shaders', 'godot/src/Actors', 'godot/tools_scenes', 'tools/legal'))
    today = datetime.date.today().isoformat()
    rec = passed.setdefault('outfits', {})
    for o, r in results.items():
        if r.get('pass') and not changed:
            e = rec.setdefault(o, {})
            whole = set(run[o]) >= {c for c in lists[o] if c in fp['clips']}
            if why[o] != 'clips changed' and whole:  # the whole outfit ran: its fingerprints are now these
                e['global'], e['outfit'], e['tuck'] = fp['global'], fp['outfit'][o], fp['tuck'][o]
                e['commit'], e['date'], e['dirty'] = commit, today, dirty
                e['counts'] = {k: r[k] for k in ('frames', 'areola', 'strip', 'flat', 'closest')}
            cs = e.setdefault('clips', {})
            for c in run[o]:
                cs[c] = {'fp': fp['clips'][c], 'commit': commit, 'date': today}
    if any(r.get('pass') for r in results.values()) and not changed:
        passed['note'] = 'Written by tools/legal/gate.py: the last PASS per outfit and per clip (fingerprints, commit, counts).'
        os.makedirs(os.path.dirname(passed_path), exist_ok=True)
        json.dump(passed, open(passed_path, 'w', encoding='utf-8'), indent=1, sort_keys=True)
    parts = [describe(o, len(run[o]), r) for o, r in results.items()]
    ok = all(r.get('pass') for r in results.values()) and len(results) == len([o for o in run if run[o]])
    blocked = any('blocked' in r or 'error' in r for r in results.values())
    head = 'LEGAL PASS' if ok else ('LEGAL BLOCKED' if blocked else 'LEGAL FAIL')
    msg = '%s %s -> %s' % (head, '; '.join(parts), base)
    if changed:
        msg += ' (inputs changed during the run: not recorded, run again)'
    open(os.path.join(base, 'gate.txt'), 'w', encoding='utf-8').write(line + '\n' + msg + '\n' + json.dumps(results, indent=1, default=str) + '\n')
    print(msg)
    return 0 if ok else (2 if blocked else 1)


if __name__ == '__main__':
    sys.exit(main())
