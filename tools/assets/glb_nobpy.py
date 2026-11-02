"""warden_head's Glb reader/writer outside Blender: stubs bpy/bmesh/mathutils so plain python can import it."""
import os, sys, types
import numpy as np


def _stub():
    if "bpy" in sys.modules:
        return
    for n in ("bpy", "bmesh", "mathutils", "mathutils.bvhtree", "mathutils.kdtree"):
        sys.modules[n] = types.ModuleType(n)

    class Quaternion:
        def __init__(self, wxyz):
            self.w, self.x, self.y, self.z = wxyz

        def to_matrix(self):
            w, x, y, z = self.w, self.x, self.y, self.z
            return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                             [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                             [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    sys.modules["mathutils"].Quaternion = Quaternion
    sys.modules["mathutils"].Vector = Matrix = object
    sys.modules["mathutils"].Matrix = object
    sys.modules["mathutils.bvhtree"].BVHTree = object
    sys.modules["mathutils.kdtree"].KDTree = object


_stub()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warden_head import Glb  # noqa: E402,F401
