"""Small geometry for staging: headings, her-space offsets, Godot YXZ Euler angles."""
import math


def fwd(h):
    """The way a heading faces (0 south +z, pi/2 east)."""
    return (math.sin(h), math.cos(h))


def left(h):
    return fwd(h + math.pi / 2)


def her(at, h, x, z):
    """A point x to her left and z ahead of `at` (x, z) facing h."""
    f, l = fwd(h), left(h)
    return (at[0] + l[0] * x + f[0] * z, at[1] + l[1] * x + f[1] * z)


def heading(a, b):
    return math.atan2(b[0] - a[0], b[1] - a[1])


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def euler_yxz(X, Y, Z):
    """Godot's RotationDegrees (YXZ order) for a basis with these columns."""
    R = [[X[0], Y[0], Z[0]], [X[1], Y[1], Z[1]], [X[2], Y[2], Z[2]]]
    b = math.asin(max(-1, min(1, -R[1][2])))
    a = math.atan2(R[0][2], R[2][2])
    c = math.atan2(R[1][0], R[1][1])
    return [round(math.degrees(b), 1), round(math.degrees(a), 1), round(math.degrees(c), 1)]


def basis_for(y_axis, x_hint):
    Y = norm(y_axis)
    X = norm(tuple(x - Y[i] * dot(x_hint, Y) for i, x in enumerate(x_hint)))
    Z = cross(X, Y)
    return X, Y, Z
