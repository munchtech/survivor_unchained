_sk0 = _strike_keys
def _strike_keys():
    ks = _sk0()
    out = []
    for t, p, e in ks:
        if t == 9:
            p = dict(p); p['hand_l'] = {**p['hand_l'], 'arc': arc_of(K9_L)}
        out.append((t, p, e))
    return out
