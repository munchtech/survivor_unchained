"""Print each Python file's module docstring (or its first lines), trimmed."""
import ast, sys, os

limit = int(os.environ.get('LIMIT', '2000'))
for path in sys.argv[1:]:
    try:
        src = open(path, encoding='utf-8', errors='replace').read()
    except Exception as e:
        print('=====', path, 'READ FAIL', e); continue
    d = None
    if path.endswith('.py'):
        try:
            d = ast.get_docstring(ast.parse(src))
        except Exception:
            d = None
    if not d:
        d = src[:limit]
    print('=====', path)
    print(d[:limit])
