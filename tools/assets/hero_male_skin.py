"""His body's paint made clean skin. hero_male_head.py runs it on the paint
hero_male_body.py baked from his TRELLIS sculpt.

TRELLIS painted the sculpt with light and hair in it. Its highlights became
white flecks along his collarbones and shoulders, and the long hair it gave
him left dark streaks and blotches down his neck and at the hollow of his
throat. The game lights him and gives him his own hair, so both are taken
out.

Each texel is judged against the skin around it in the body, not in the
texture: the paint's islands are cut small, and a fleck can fill one. The
skin's broad colour is gathered in centimetre cells through him, as a field
smoothed over a few cells. A texel much brighter than the field there is a
fleck. On his neck and shoulders (`dark_zone`), a texel much darker, or of
another hue, is a streak. Flecks are not counted when the field is gathered
again, so a streak does not darken its own reference. They are then eased
into the field's colour, softly by how far out they are. Everything else
keeps its own paint.
"""
import numpy as np
from scipy import ndimage

CELL = 0.01           # metres: the field's cells
LUM = np.array([0.3, 0.59, 0.11])


def clean(img, P, rows, cols, dark_zone, keep, rounds=5):
    """img (rows x cols x 4, as Blender holds it) cleaned in place over the
    texels given (their rows, columns and points P on him). keep: texels
    left as they are (nails, which are pale by right). Returns how many
    texels were eased, and by how much at most."""
    c = img[rows, cols, :3].astype(np.float64)
    lum = c @ LUM
    lo = P.min(0) - 4 * CELL
    g = np.floor((P - lo) / CELL).astype(np.int64)
    shape = tuple(g.max(0) + 5)
    lin = np.ravel_multi_index(g.T, shape)
    size = int(np.prod(shape))
    coords = ((P - lo) / CELL - 0.5).T

    def field(use, sigma):
        """The skin's colour about each texel, from the texels `use`."""
        n = ndimage.gaussian_filter(np.bincount(lin[use], minlength=size).astype(np.float32).reshape(shape), sigma)
        nn = ndimage.map_coordinates(n, coords, order=1)
        out = np.zeros_like(c)
        for k in range(3):
            s = np.bincount(lin[use], weights=c[use, k], minlength=size).astype(np.float32).reshape(shape)
            out[:, k] = ndimage.map_coordinates(ndimage.gaussian_filter(s, sigma), coords, order=1)
        return out / np.maximum(nn, 1e-6)[:, None], nn

    use = ~keep
    for r in range(rounds):
        ref, nn = field(use, 1.5)
        wide, _ = field(use, 4.0)
        # (Where too few clean texels are near, the wider field; and on his
        # neck and shoulders always: a streak a few centimetres across
        # darkens a fine field as much as itself, and hides in it.)
        thin = (nn < 0.5 * np.median(nn[use])) | dark_zone
        ref[thin] = wide[thin]
        dev = lum - ref @ LUM
        hue = np.linalg.norm((c - ref) - (dev[:, None] * np.ones(3)), axis=1)
        bright = dev > 0.05
        dark = dark_zone & ((dev < -0.05) | (hue > 0.07))
        out = (bright | dark) & ~keep
        use = ~out & ~keep
        print("  SKIN round %d: %d flecks (%d bright, %d dark or off-hue)" % (r, out.sum(), (bright & ~keep).sum(), (dark & ~keep).sum()))
    a = np.clip(np.maximum(np.where(dev > 0, (dev - 0.03) / 0.05, 0),
                           np.where(dark_zone, np.maximum((-dev - 0.03) / 0.05, (hue - 0.04) / 0.06), 0)), 0, 1)
    a = (a * a * (3 - 2 * a)) * ~keep
    new = c * (1 - a[:, None]) + ref * a[:, None]
    img[rows, cols, :3] = new
    return int((a > 0.5).sum()), float(np.abs(new - c).max())



def clean_relief(img, P, rows, cols, keep, hair=None, small=4000, sigma=8.0):
    """His relief (a tangent-space normal map, rows x cols x 4 as Blender
    holds it, 0..1) cleaned in place. Where the bake's rays missed his
    sculpt or struck the wrong part of it, it wrote slopes no skin has, some
    turned inside out, and under the game's light they showed as
    hard-edged patches, as if painted. That happened on the smallest
    islands of his unwrap (a few triangles each, along his collarbones and
    in his joints), whose bake had no room. There a slope is judged against
    the steepness of his relief about it in the body (as the paint is, in
    clean), and one much steeper is laid flat; the large islands, whose
    veins and grooves are true, keep theirs. Anywhere, a slope facing back
    into him is laid flat.

    hair (0 to 1 a texel): where the sculpt's long hair lay on him, its
    strands moulded into his neck, collarbones and shoulders. There only the
    broad relief is kept (his muscles), blurred within each island, so his
    hair's strands are gone. Returns how many texels were flattened."""
    n = img[rows, cols, :3].astype(np.float64) * 2 - 1
    tilt = np.linalg.norm(n[:, :2], axis=1)
    # His unwrap's islands, by the texels their triangles cover.
    cover = np.zeros(img.shape[:2], bool)
    cover[rows, cols] = True
    lab, k = ndimage.label(cover)
    sizes = np.bincount(lab.ravel(), minlength=k + 1)
    tiny = sizes[lab[rows, cols]] < small
    lo = P.min(0) - 4 * CELL
    g = np.floor((P - lo) / CELL).astype(np.int64)
    shape = tuple(g.max(0) + 5)
    lin = np.ravel_multi_index(g.T, shape)
    size = int(np.prod(shape))
    coords = ((P - lo) / CELL - 0.5).T
    # (the steepness about each texel, from the large islands only)
    use = ~tiny & ~keep & (n[:, 2] > 0.3)
    cnt = ndimage.gaussian_filter(np.bincount(lin[use], minlength=size).astype(np.float32).reshape(shape), 1.5)
    sm = ndimage.gaussian_filter(np.bincount(lin[use], weights=tilt[use], minlength=size).astype(np.float32).reshape(shape), 1.5)
    ref = ndimage.map_coordinates(sm, coords, order=1) / np.maximum(ndimage.map_coordinates(cnt, coords, order=1), 1e-6)
    a = np.where(tiny, np.clip((tilt - (ref * 1.5 + 0.05)) / 0.1, 0, 1), 0.0)
    a = np.maximum(a, np.clip((0.4 - n[:, 2]) / 0.2, 0, 1))
    a = a * a * (3 - 2 * a) * ~keep
    flat = np.array([0.0, 0.0, 1.0])
    m = n * (1 - a[:, None]) + flat * a[:, None]
    if hair is not None:
        # (blurred within each island: across one, the tangents' frames turn)
        full = np.zeros(img.shape[:2] + (3,), np.float32)
        full[rows, cols] = m
        blur = np.zeros_like(full)
        wanted = np.unique(lab[rows[hair > 0.01], cols[hair > 0.01]])
        objs = ndimage.find_objects(lab)
        pad_ = int(3 * sigma)
        for k_ in wanted:
            if k_ == 0:
                continue
            sl = objs[k_ - 1]
            y0, y1 = max(sl[0].start - pad_, 0), min(sl[0].stop + pad_, img.shape[0])
            x0, x1 = max(sl[1].start - pad_, 0), min(sl[1].stop + pad_, img.shape[1])
            mk = (lab[y0:y1, x0:x1] == k_).astype(np.float32)
            wsum = ndimage.gaussian_filter(mk, sigma)
            for ch in range(3):
                b = ndimage.gaussian_filter(full[y0:y1, x0:x1, ch] * mk, sigma) / np.maximum(wsum, 1e-6)
                blur[y0:y1, x0:x1, ch] = np.where(mk > 0, b, blur[y0:y1, x0:x1, ch])
        h = hair[:, None]
        m = m * (1 - h) + blur[rows, cols] * h
    m /= np.linalg.norm(m, axis=1)[:, None]
    img[rows, cols, :3] = m * 0.5 + 0.5
    print("  RELIEF: %d islands, %d of them tiny (%d%% of texels); %d texels flattened, %d of them inside out" % (
        k, (sizes[1:] < small).sum(), 100 * tiny.mean(), (a > 0.5).sum(), (n[:, 2] < 0.3).sum()))
    return int((a > 0.5).sum())


def even(img, P, rows, cols, w, grain_px=2.5, grain_max=0.025):
    """His skin where the sculpt's hair lay (w, 0 to 1 a texel) made even:
    paler and darker bands its hair left, too faint to be flecks, still
    showed as a tide-mark across his nape. There his colour is a smooth
    fit through the body (a quadratic in where he is, fitted so what
    strays from it counts for nothing), with the paint's own finest grain
    laid back over it, kept small."""
    z = w > 0.01
    c = img[rows, cols, :3].astype(np.float64)
    q = P[z]
    x, y, h = np.abs(q[:, 0]), q[:, 1], q[:, 2]
    X = np.stack([np.ones(len(q)), x, y, h, x * x, y * y, h * h, x * y, x * h, y * h], 1)
    C = c[z]
    wt = np.ones(len(q))
    for _ in range(8):
        sw = np.sqrt(wt)[:, None]
        beta = np.linalg.lstsq(X * sw, C * sw, rcond=None)[0]
        r = (C - X @ beta) @ LUM
        s = 1.4826 * np.median(np.abs(r)) + 1e-6
        u = np.clip(r / (4.685 * s), -1, 1)
        wt = (1 - u * u) ** 2
    fit = X @ beta
    # (the grain: the paint less its blur, within his unwrap's faces only)
    cover = np.zeros(img.shape[:2], np.float32)
    cover[rows, cols] = 1
    nrm = ndimage.gaussian_filter(cover, grain_px)
    grain = np.zeros((z.sum(), 3))
    for k in range(3):
        b = ndimage.gaussian_filter(img[..., k] * cover, grain_px) / np.maximum(nrm, 1e-6)
        grain[:, k] = (img[rows, cols, k] - b[rows, cols])[z]
    grain = np.clip(grain, -grain_max, grain_max)
    new = c.copy()
    ww = w[z][:, None]
    new[z] = c[z] * (1 - ww) + (fit + grain) * ww
    img[rows, cols, :3] = new
    print("  EVEN: %d texels, his skin there %s, %.3f spread left out" % (z.sum(), np.round(fit.mean(0), 3), s))


def broad(c, P, sigma, cell=0.005, w=None):
    """Colours c at points P (texels on him) blurred through the body, not
    the texture: each the mean of those about it, a Gaussian of sigma
    metres (weighted by w, when given, so one region's colour is not
    another's)."""
    w = np.ones(len(P)) if w is None else w
    lo = P.min(0) - 4 * cell
    g = np.floor((P - lo) / cell).astype(np.int64)
    shape = tuple(g.max(0) + 5)
    lin = np.ravel_multi_index(g.T, shape)
    size = int(np.prod(shape))
    coords = ((P - lo) / cell - 0.5).T
    s = sigma / cell
    n = ndimage.map_coordinates(ndimage.gaussian_filter(np.bincount(lin, weights=w, minlength=size).astype(np.float32).reshape(shape), s),
                                coords, order=1)
    out = np.zeros((len(P), c.shape[1]))
    for k in range(c.shape[1]):
        f = ndimage.gaussian_filter(np.bincount(lin, weights=c[:, k] * w, minlength=size).astype(np.float32).reshape(shape), s)
        out[:, k] = ndimage.map_coordinates(f, coords, order=1)
    return out / np.maximum(n, 1e-6)[:, None]


def one_tone(c, P, tone, face, keep=0.6):
    """A head's colours (c at points P) brought to one skin with his body's
    (tone): MakeHuman's paint, pinker than his, and his painted face, paler,
    each met his neck along a visible line. Where nothing is drawn (his
    scalp, nape and neck) the colour broader than 1.5 cm is his body's,
    only the finer grain kept; on his face and ears (face, 0 to 1) the
    colour broader than 4 cm is, keeping `keep` of its own (the warmth of
    his face) and all that is finer (lips, brows, eyes)."""
    # (each region's own: his face's colour from his face, the rest from the rest)
    b = broad(c, P, 0.015, w=1.0001 - face) * (1 - face[:, None]) + broad(c, P, 0.04, w=face + 1e-4) * face[:, None]
    k = (keep * face)[:, None]
    # (by gain, not by adding: a lip's red stays a lip's red on any skin)
    return c * (tone + k * (b - tone)) / np.maximum(b, 1e-3)
