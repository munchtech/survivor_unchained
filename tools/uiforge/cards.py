"""The draft's cards (frames/card_*.png): painted over guides.card_guide on the
local Krea, then fitted here. The card hangs from two lamp-iron brackets at
its top, the broken chain riding over its top edge (clear of the ribbon the
code writes there), and is nailed at its foot by two coins at the very
corners (clear of the rarity word and the key). The file is the card plus
its overhang (UiArt Out = 24): 736 by 1000, drawn one to one.
"""
from __future__ import annotations

import numpy as np

import cut as C
import forge as F
import painted as P

OUT = 24            # shown px the frame may reach past the card
W, H = 736, 1000    # file
BODY = (48, 48, 688, 952)  # the card itself, in file px

# Where the base painting's pieces lie (card_v3_401_3), in file px.
BASE = dict(
    interior=(86, 96, 650, 918),
    keep_top=150,                     # the brackets and the crest's light live above this
    crest=(250, 0, 490, 170),         # the broken link and the light it throws on the card
    holes=[(34, 24, 106, 96), (630, 24, 702, 96), (38, 886, 112, 962), (622, 886, 698, 962)],
)


# The light in the coins' holes, by what the card is (deep, hot).
HOLE = {
    "common": ("#4a1a0a", "#ff8a3a"), "uncommon": ("#123a10", "#8ae05a"), "rare": ("#0e2a4a", "#8fd0ff"),
    "epic": ("#2a0e4a", "#c070ff"), "legendary": ("#4a2a0a", "#ffd07a"), "evolution": ("#5a1a06", "#ffb050"),
}


def move_coins(rgb, mask, coins, strap=46, shift=240, heal_prompt=None, tag="card"):
    """Coins the painting set inside the card's foot (where the code writes the rarity and
    the key) moved out to the very corners: each lifted out whole, the strap behind it made
    good from the strap further along, then laid at its corner."""
    h, w = mask.shape
    pieces = []
    for (x0, y0, x1, y1), (cx, cy) in coins:
        pc = P.piece(rgb, mask, (x0, y0, x1, y1)).copy()
        # Only the coin: a square window inside its box (the box also holds strap).
        ph, pw = pc.shape[:2]
        yy, xx = np.mgrid[0:ph, 0:pw]
        edge = np.minimum(np.minimum(xx, pw - 1 - xx), np.minimum(yy, ph - 1 - yy)).astype(np.float32)
        pc[..., 3] = np.clip((edge - 2) / 2.5, 0, 1)
        pieces.append((pc, (cx, cy), max(x1 - x0, y1 - y0)))
    # Where they were, the strap and the middle grown back in (inpainted from round about).
    hole = np.zeros((h, w), np.uint8)
    for (x0, y0, x1, y1), _ in coins:
        hole[max(0, y0 - 3):y1 + 3, max(0, x0 - 3):x1 + 3] = 255
    import cv2
    u8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    rgb = cv2.inpaint(u8, hole, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
    # Then the painting's own hand over the inpainted blur.
    if heal_prompt:
        for i, ((x0, y0, x1, y1), _) in enumerate(coins):
            reg = np.zeros((h, w), np.float32)
            reg[max(0, y0 - 3):y1 + 3, max(0, x0 - 3):x1 + 3] = 1
            rgb = P.heal(rgb, reg, heal_prompt, denoise=0.55, seed=90 + i, tag=f"{tag}{i}")
    return rgb, mask, pieces


def fit(src, dst, tone="#141117", grade=True, hole_light=0.55, geo=BASE, keep=0.5, mask=None, kind="common", coins=(), heal_prompt=None):
    rgb = P.load(src)
    mask = (C.birefnet_mask(src) if mask is None else mask).copy()
    pieces = []
    if coins:
        rgb, mask, pieces = move_coins(rgb, mask, coins, heal_prompt=heal_prompt, tag=kind)
    a = P.silhouette(mask)
    h, w = a.shape
    # The card itself is solid whatever the mask made of its dark middle.
    body = np.zeros((h, w), np.float32)
    body[BODY[1] + 10:BODY[3] - 10, BODY[0] + 10:BODY[2] - 10] = 1
    a = np.maximum(a, body)
    # The middle, calm: everything inside the strap, except the brackets' ornament
    # and the light the broken link throws down onto the card.
    x0, y0, x1, y1 = geo["interior"]
    region = np.zeros((h, w), np.float32)
    region[y0:y1, x0:x1] = 1
    yy = np.arange(h)[:, None]
    region = np.where((mask > 0.5) & (yy < geo["keep_top"] + 100), 0, region)
    cx0, cy0, cx1, cy1 = geo["crest"]
    region[cy0:cy1, cx0:cx1] = np.minimum(region[cy0:cy1, cx0:cx1], np.linspace(0, 1, cy1 - cy0)[:, None] ** 2)
    rgb = P.calm(rgb, region, tone, keep=keep, low=0.05, sigma=9, feather=3)
    # The coins' quatrefoil holes, lit from beneath (the sleeping ember).
    holes = np.zeros((h, w), np.float32)
    for (bx0, by0, bx1, by1) in geo["holes"]:
        sub = mask[by0:by1, bx0:bx1]
        lum = rgb[by0:by1, bx0:bx1].mean(axis=2)
        coin = sub > 0.5
        ys, xs = np.nonzero(coin)
        if len(xs):
            cy, cx = ys.mean(), xs.mean()
            yy2, xx2 = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
            r = np.hypot(yy2 - cy, xx2 - cx)
            # The hole: the dark middle of the coin.
            inner = (r < min(sub.shape) * 0.28) & (lum < 0.12)
            holes[by0:by1, bx0:bx1] = np.maximum(holes[by0:by1, bx0:bx1], inner.astype(np.float32))
    rgb = P.ember_holes(rgb, holes, hole_light, *HOLE[kind])
    for pc, (cx, cy), size in pieces:
        rgb, a = P.paste(rgb, a, pc, cx, cy, size, shadow=5)
    out = np.dstack([rgb, a])
    if grade:
        out = C.grade(out)
    P.save_rgba(out[..., :3], out[..., 3], dst)
    return out
