"""BVH motion capture, read into global joint rotations and positions.

A BVH's rest is every channel at zero: each joint's frame is the world's,
and its offset from its parent is given. The globals come back in the
file's own units and axes; tools/anim/retarget.py turns them into hers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rig import qaxis, qmul, qrot


@dataclass
class Bvh:
    names: list
    parent: list
    offset: np.ndarray       # [J, 3] from the parent, at rest
    channels: list           # per joint: list of channel names
    frame_time: float
    data: np.ndarray         # [T, C]
    end_sites: dict          # joint index -> offset of its end site

    @property
    def fps(self):
        return 1.0 / self.frame_time

    @property
    def frames(self):
        return self.data.shape[0]

    def index(self, name):
        return self.names.index(name)

    def globals(self, start=0, stop=None):
        """(grot [T, J, 4], gpos [T, J, 3]) for frames start..stop."""
        d = self.data[start:stop]
        T = d.shape[0]
        J = len(self.names)
        lrot = np.tile(np.array([0, 0, 0, 1.0]), (T, J, 1))
        lpos = np.tile(self.offset, (T, 1, 1)).astype(float)
        col = 0
        for j, chans in enumerate(self.channels):
            r = np.tile(np.array([0, 0, 0, 1.0]), (T, 1))
            for c in chans:
                v = d[:, col]
                col += 1
                if c.endswith("position"):
                    lpos[:, j, "XYZ".index(c[0])] = v
                else:
                    axis = {"X": [1, 0, 0], "Y": [0, 1, 0], "Z": [0, 0, 1]}[c[0]]
                    # Channels compose in the order written, each about the
                    # frame turned by those before it.
                    h = np.radians(v) / 2
                    qa = np.zeros((T, 4))
                    qa[:, :3] = np.outer(np.sin(h), axis)
                    qa[:, 3] = np.cos(h)
                    r = qmul(r, qa)
            lrot[:, j] = r
        grot = np.empty_like(lrot)
        gpos = np.empty_like(lpos)
        for j, p in enumerate(self.parent):
            if p < 0:
                grot[:, j] = lrot[:, j]
                gpos[:, j] = lpos[:, j]
            else:
                grot[:, j] = qmul(grot[:, p], lrot[:, j])
                gpos[:, j] = gpos[:, p] + qrot(grot[:, p], lpos[:, j])
        return grot, gpos

    def rest_positions(self):
        pos = np.zeros((len(self.names), 3))
        for j, p in enumerate(self.parent):
            pos[j] = self.offset[j] + (pos[p] if p >= 0 else 0)
        return pos


def load(path) -> Bvh:
    text = Path(path).read_text(errors="replace")
    head, _, motion = text.partition("MOTION")
    tokens = re.findall(r"[^\s{}]+|[{}]", head)
    names, parent, offset, channels, end_sites = [], [], [], [], {}
    stack = []
    i = 0
    pending = None
    while i < len(tokens):
        t = tokens[i]
        if t in ("ROOT", "JOINT"):
            names.append(tokens[i + 1])
            parent.append(stack[-1] if stack else -1)
            offset.append([0, 0, 0])
            channels.append([])
            pending = len(names) - 1
            i += 2
        elif t == "End":
            pending = ("end", stack[-1])
            i += 2
        elif t == "{":
            stack.append(pending)
            i += 1
        elif t == "}":
            stack.pop()
            i += 1
        elif t == "OFFSET":
            v = [float(x) for x in tokens[i + 1:i + 4]]
            top = stack[-1]
            if isinstance(top, tuple):
                end_sites[top[1]] = np.array(v)
            else:
                offset[top] = v
            i += 4
        elif t == "CHANNELS":
            n = int(tokens[i + 1])
            channels[stack[-1]] = tokens[i + 2:i + 2 + n]
            i += 2 + n
        else:
            i += 1
    lines = [l for l in motion.strip().splitlines() if l.strip()]
    frame_time = float(lines[1].split(":")[1])
    data = np.array([[float(x) for x in l.split()] for l in lines[2:]])
    return Bvh(names, parent, np.array(offset, float), channels, frame_time, data, end_sites)
