# Which names assigned in the tuck loop (lines A..B) are read elsewhere as globals (functions' free names, or module code after B).
import ast, sys
p, A, B = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
src = open(p, encoding="utf-8").read()
tree = ast.parse(src)
assigned = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and A <= n.lineno <= B:
        assigned.add(n.id)
print("assigned in loop:", sorted(assigned))
uses = {}
def visit_func(f):
    local = set()
    for n in ast.walk(f):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            local.add(n.id)
        if isinstance(n, ast.arg):
            local.add(n.arg)
    for n in ast.walk(f):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in assigned and n.id not in local:
            uses.setdefault(n.id, []).append(("func " + f.name, n.lineno))
for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.Lambda)) and not isinstance(n, ast.Lambda):
        visit_func(n)
# module-level loads after B (outside functions)
funcs = [(f.lineno, f.end_lineno) for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.Lambda, ast.ListComp, ast.GeneratorExp, ast.DictComp, ast.SetComp))]
for n in ast.walk(tree):
    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in assigned and n.lineno > B:
        if not any(a <= n.lineno <= b for a, b in funcs if b - a > 0 and a > B - 100000 and False):
            uses.setdefault(n.id, []).append(("module", n.lineno))
for k, v in sorted(uses.items()):
    print(k, v[:8])
