p = 'tools/assets/heroine_paint.py'
s = open(p, encoding='utf-8').read()
i = s.index("if __name__ == '__main__':")
s = s[:i] + '''def preview(ref, L):
    """A design over her face on the sheet (to look at)."""
    a = L[..., 3:4]
    return np.clip(ref * (1 - a) + L[..., :3] * a, 0, 1)


if __name__ == '__main__':
    ref, back, valid, eyes = maps()
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--sheet' in sys.argv:
        img = (np.clip(ref, 0, 1) * 255).astype(np.uint8)
        for e in eyes:
            cv2.circle(img, tuple(int(v) for v in e), 6, (0, 255, 0), 2)
        out = args[0] if args else 'sheet.png'
        Image.fromarray(img).save(out)
        print('sheet', img.shape, 'eyes', [e.round(1).tolist() for e in eyes])
        sys.exit()
    shape = ref.shape[:2]
    f = features(ref, eyes)
    look = os.environ.get('PAINT_PREVIEW')          # a folder: each design over her face, on the sheet
    names = args or list(DESIGNS) + ['brows']
    for name in names:
        L = brows_layer(shape, f) if name == 'brows' else DESIGNS[name](shape, f)
        if look:
            os.makedirs(look, exist_ok=True)
            Image.fromarray((preview(ref, L) * 255).astype(np.uint8)).save(os.path.join(look, name + '.jpg'), quality=90)
        save(to_uv(L, back, valid), name)
        print('painted', name)
'''
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
