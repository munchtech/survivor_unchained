"""A reader for Godot 4's binary resources (.res, RSRC), enough to fingerprint each clip of an
AnimationLibrary (godot/art/anim/heroine.res) on its own, for tools/legal/gate.py.

    python tools/legal/godot_res.py godot/art/anim/heroine.res     clip names and their hashes

clips(path) -> {name: sha1 of the clip's decoded properties}. The hash is of the values (strings
resolved, not the file's string-table indices), so repacking the library with another clip
added or changed leaves an untouched clip's hash as it was. Raises ValueError on anything it
can't read (an unknown variant type): the gate then treats every clip as changed.
Follows core/io/resource_format_binary.cpp (Godot 4.5)."""
import hashlib
import struct
import sys

# Variant tags in the binary format (resource_format_binary.cpp)
NIL, BOOL, INT, FLOAT, STRING = 1, 2, 3, 4, 5
VECTOR2, RECT2, VECTOR3, PLANE, QUATERNION, AABB, BASIS, TRANSFORM3D, TRANSFORM2D = 10, 11, 12, 13, 14, 15, 16, 17, 18
COLOR, NODE_PATH, RID, OBJECT, INPUT_EVENT, DICTIONARY, ARRAY = 20, 22, 23, 24, 25, 26, 30
P_BYTE, P_INT32, P_FLOAT32, P_STRING, P_VECTOR3, P_COLOR, P_VECTOR2 = 31, 32, 33, 34, 35, 36, 37
INT64, DOUBLE, CALLABLE, SIGNAL, STRING_NAME = 40, 41, 42, 43, 44
VECTOR2I, RECT2I, VECTOR3I, P_INT64, P_FLOAT64, VECTOR4, VECTOR4I, PROJECTION, P_VECTOR4 = 45, 46, 47, 48, 49, 50, 51, 52, 53
# real_t counts per fixed-size math type
REALS = {VECTOR2: 2, RECT2: 4, VECTOR3: 3, PLANE: 4, QUATERNION: 4, AABB: 6, BASIS: 9, TRANSFORM3D: 12,
         TRANSFORM2D: 6, VECTOR4: 4, PROJECTION: 16}
INTS = {VECTOR2I: 2, RECT2I: 4, VECTOR3I: 3, VECTOR4I: 4}
PACKED = {P_INT32: ('i', 4), P_FLOAT32: ('f', 4), P_INT64: ('q', 8), P_FLOAT64: ('d', 8)}
PACKED_REAL = {P_VECTOR3: 3, P_VECTOR2: 2, P_VECTOR4: 4}


class Reader:
    def __init__(self, data):
        self.d = data
        self.p = 0
        self.real = 'f'
        self.strings = []

    def u32(self):
        v = struct.unpack_from('<I', self.d, self.p)[0]
        self.p += 4
        return v

    def u64(self):
        v = struct.unpack_from('<Q', self.d, self.p)[0]
        self.p += 8
        return v

    def take(self, n):
        b = self.d[self.p:self.p + n]
        if len(b) != n:
            raise ValueError('truncated')
        self.p += n
        return b

    def ustr(self):
        n = self.u32()
        return self.take(n).rstrip(b'\0').decode('utf-8', 'replace')

    def sstr(self):  # _get_string: an index into the string table, or inline when the top bit is set
        i = self.u32()
        if i & 0x80000000:
            return self.take(i & 0x7FFFFFFF).rstrip(b'\0').decode('utf-8', 'replace')
        return self.strings[i]

    def reals(self, n):
        sz = 8 if self.real == 'd' else 4
        return list(struct.unpack('<%d%s' % (n, self.real), self.take(n * sz)))

    def variant(self):
        t = self.u32()
        if t == NIL:
            return None
        if t == BOOL:
            return bool(self.u32())
        if t == INT:
            return struct.unpack('<i', self.take(4))[0]
        if t == INT64:
            return struct.unpack('<q', self.take(8))[0]
        if t == FLOAT:
            return struct.unpack('<f', self.take(4))[0]
        if t == DOUBLE:
            return struct.unpack('<d', self.take(8))[0]
        if t in (STRING, STRING_NAME):
            return ('s', self.ustr())
        if t in REALS:
            return ('r%d' % t, self.reals(REALS[t]))
        if t in INTS:
            return ('i%d' % t, list(struct.unpack('<%di' % INTS[t], self.take(4 * INTS[t]))))
        if t == COLOR:
            return ('c', list(struct.unpack('<4f', self.take(16))))
        if t == NODE_PATH:
            names = struct.unpack('<H', self.take(2))[0]
            subs = struct.unpack('<H', self.take(2))[0]
            absolute = bool(subs & 0x8000)
            subs &= 0x7FFF
            return ('np', absolute, [self.sstr() for _ in range(names)], [self.sstr() for _ in range(subs)])
        if t == RID:
            return ('rid', self.u32())
        if t == OBJECT:
            k = self.u32()
            if k == 0:
                return ('obj', None)
            if k == 1:
                return ('ext', self.ustr(), self.ustr())
            if k == 2:
                return ('int', self.u32())
            if k == 3:
                return ('exti', self.u32())
            raise ValueError('object kind %d' % k)
        if t == DICTIONARY:
            n = self.u32() & 0x7FFFFFFF
            return ('dict', [(self.variant(), self.variant()) for _ in range(n)])
        if t == ARRAY:
            n = self.u32() & 0x7FFFFFFF
            return ('arr', [self.variant() for _ in range(n)])
        if t == P_BYTE:
            n = self.u32()
            b = self.take(n)
            self.take((4 - n % 4) % 4)
            return ('pb', hashlib.sha1(b).hexdigest())
        if t in PACKED:
            c, sz = PACKED[t]
            n = self.u32()
            return ('p%d' % t, hashlib.sha1(self.take(n * sz)).hexdigest())
        if t in PACKED_REAL:
            n = self.u32()
            sz = 8 if self.real == 'd' else 4
            return ('p%d' % t, hashlib.sha1(self.take(n * PACKED_REAL[t] * sz)).hexdigest())
        if t == P_COLOR:
            n = self.u32()
            return ('pc', hashlib.sha1(self.take(n * 16)).hexdigest())
        if t == P_STRING:
            n = self.u32()
            return ('ps', [self.ustr() for _ in range(n)])
        raise ValueError('variant type %d at %d' % (t, self.p - 4))


def read(path):
    """-> (main type, [(type, path, {prop: value})] internal resources in file order)."""
    r = Reader(open(path, 'rb').read())
    if r.take(4) != b'RSRC':
        raise ValueError('not a binary resource')
    if r.u32():
        raise ValueError('big-endian resource')
    use_real64 = r.u32()
    r.u32(), r.u32()
    fmt = r.u32()
    if fmt > 6:
        raise ValueError('format %d' % fmt)
    rtype = r.ustr()
    r.u64()  # import metadata offset
    flags = r.u32()
    uids = bool(flags & 2)
    r.u64()  # uid (or unused)
    if flags & 4 or use_real64:
        r.real = 'd'
    if flags & 8:
        r.ustr()  # script class
    for _ in range(11):  # reserved fields
        r.u32()
    r.strings = [r.ustr() for _ in range(r.u32())]
    for _ in range(r.u32()):  # external resources
        r.ustr(), r.ustr()
        if uids:
            r.u64()
    heads = [(r.ustr(), r.u64()) for _ in range(r.u32())]
    out = []
    for rpath, off in heads:
        r.p = off
        typ = r.ustr()
        props = {}
        for _ in range(r.u32()):
            name = r.sstr()
            props[name] = r.variant()
        out.append((typ, rpath, props))
    return rtype, out


def digest(v):
    return hashlib.sha1(repr(v).encode()).hexdigest()


def clips(path):
    rtype, res = read(path)
    if rtype != 'AnimationLibrary':
        raise ValueError('not an AnimationLibrary: %s' % rtype)
    by_path = {p: props for _, p, props in res}
    by_index = [props for _, _, props in res]
    lib = res[-1][2]
    data = lib.get('_data')
    if not data or data[0] != 'dict':
        raise ValueError('no _data in the library')
    out = {}
    for k, v in data[1]:
        if not (isinstance(k, tuple) and k[0] == 's') or not (isinstance(v, tuple) and v[0] == 'int'):
            raise ValueError('unexpected library entry %r' % (k,))
        # An internal reference is the subresource's index in the file (local://<id> paths are
        # looked up by their order); fall back on the path if the index is out of range.
        props = by_index[v[1]] if v[1] < len(by_index) else by_path.get('local://%d' % v[1])
        if props is None:
            raise ValueError('clip %s: subresource %d not found' % (k[1], v[1]))
        out[k[1]] = digest(sorted(props.items()))
    return out


if __name__ == '__main__':
    for n, h in sorted(clips(sys.argv[1]).items()):
        print(h[:12], n)
