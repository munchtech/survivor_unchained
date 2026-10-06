"""Calls that turn a string literal into a StringName or NodePath (a new
disposable each call), grouped by the method they sit in, for methods whose
names say they run every frame.
    python stringnames.py SRC_DIR"""
import os
import re
import sys

CALLS = re.compile(r'\b(SetShaderParameter|GetShaderParameter|GlobalShaderParameterSet|SetInstanceShaderParameter|Play|PlayBackwards|HasAnimation|GetAnimation|GetNode|GetNodeOrNull|HasNode|SetMeta|GetMeta|HasMeta|EmitSignal|Call|CallDeferred|Set|Get|IsActionPressed|IsActionJustPressed|GetActionStrength|FindBone|FindChild|FindBlendShapeByName|SetBlendShapeValue|GetBoneName|AddThemeColorOverride|AddThemeConstantOverride|AddThemeFontSizeOverride|AddThemeStyleboxOverride|AddThemeFontOverride|HasThemeConstant|GetThemeColor)\s*(<[^>]*>)?\(\s*(\$?"[^"]*")')
METHOD = re.compile(r'^\s*(?:public |private |protected |internal |static |override |virtual |readonly |unsafe |async |sealed |new )*[\w<>\[\],.? ]+\s+(\w+)\s*\([^;]*$')
HOT = re.compile(r'^(_Process|_PhysicsProcess|Update|Step|Tick|Frame|Draw|Follow|Animate|Advance|Each|Flow|Sway|Breathe|Track|Place|Show|_Draw)$')
root = sys.argv[1]
rows = {}
for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith(".cs"):
            continue
        path = os.path.join(dirpath, f)
        method = "?"
        for i, line in enumerate(open(path, encoding="utf-8", errors="replace")):
            m = METHOD.match(line)
            if m and not line.strip().startswith(("if", "for", "while", "return", "var ", "else", "switch", "using", "new ")):
                method = m.group(1)
            for c in CALLS.finditer(line):
                rows.setdefault((os.path.relpath(path, root), method), []).append((i + 1, c.group(1), c.group(3)))
for (path, method), calls in sorted(rows.items()):
    if HOT.match(method):
        print(f"{path} :: {method}")
        for ln, fn, arg in calls:
            print(f"    {ln}: {fn}({arg})")
