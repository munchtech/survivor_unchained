p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\tools\anim\clips\rook.py"
s = open(p, encoding="utf-8").read()
old = '''    rest_l, rest_r = np.array([0.045, 1.04, 0.20]), np.array([-0.04, 1.03, 0.195])'''
new = '''    # (From each shoulder, so they sit at her waist however low the stance.)
    rest_l, rest_r = np.array([-0.11, -0.39, 0.25]), np.array([0.105, -0.40, 0.245])'''
assert old in s
s = s.replace(old, new)
old2 = '''                pos = at * (1 - w) + rest * w + arc'''
new2 = '''                pos = at * (1 - w) + (p[fr, I[f"upperarm_{s}"]] + rest) * w + arc'''
assert old2 in s
s = s.replace(old2, new2)
open(p, "w", encoding="utf-8").write(s)
print("ok")
