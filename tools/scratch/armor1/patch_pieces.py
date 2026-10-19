import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
def sub(a, b):
    global s
    a, b = a.replace("\n", "\r\n"), b.replace("\n", "\r\n")
    assert s.count(a) == 1, a
    s = s.replace(a, b)
sub('''        for rank, (slot, sobjs) in enumerate(by_slot.items()):
            bpy.ops.object.select_all(action="DESELECT")''', '''        for rank, (slot, sobjs) in enumerate(by_slot.items()):
            # (each piece's place in the material's one join and its triangles, in this mesh's order)
            pieces_ = [[order.index(o), sum(len(f_.vertices) - 2 for f_ in o.data.polygons)] for o in sobjs]
            bpy.ops.object.select_all(action="DESELECT")''')
sub('''            ranks[sobjs[0].name] = {"outfit": name, "slot": slot, "material": key, "rank": rank}''',
    '''            ranks[sobjs[0].name] = {"outfit": name, "slot": slot, "material": key, "rank": rank, "pieces": pieces_}''')
sub('''            print("SLOT ORDER %s.%s: its slots interleave in the join (%d runs of %d slots): the LOD's join differs" % (name, key, runs, len(by_slot)))''',
    '''            print("SLOT ORDER %s.%s: its slots interleave in the join (%d runs of %d slots): heroine_lod.py lays its pieces back in order" % (name, key, runs, len(by_slot)))''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
