p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\blender_links.py'
s = open(p, encoding='utf-8').read()
a = s.index('def heated_material(')
b = s.index('def main():')
new = '''def heated_material(name, cold_rim, hot_core, strength):
    """Iron with heat in it, still iron: its shape and its sheen keep, and a glow comes up
    through it, hottest along the bar's crown (where it faces the eye) and darker round its
    sides, mottled where scale has crusted on it; from `cold_rim` to `hot_core`."""
    m = C.iron_chain_material()
    m.name = name
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    inv = n.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    k.new(lw.outputs["Facing"], inv.inputs[1])
    pw = n.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 1.6
    k.new(inv.outputs[0], pw.inputs[0])
    tco = n.new("ShaderNodeTexCoord")
    scale = n.new("ShaderNodeTexNoise")
    scale.inputs["Scale"].default_value = 14.0
    scale.inputs["Detail"].default_value = 4.0
    k.new(tco.outputs["Object"], scale.inputs["Vector"])
    crust = n.new("ShaderNodeMapRange")
    k.new(scale.outputs["Fac"], crust.inputs["Value"])
    crust.inputs["From Min"].default_value = 0.35
    crust.inputs["From Max"].default_value = 0.65
    crust.inputs["To Min"].default_value = 0.55
    crust.inputs["To Max"].default_value = 1.0
    heat = n.new("ShaderNodeMath")
    heat.operation = "MULTIPLY"
    k.new(pw.outputs[0], heat.inputs[0])
    k.new(crust.outputs[0], heat.inputs[1])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = B.hexc(cold_rim)
    ramp.color_ramp.elements[1].color = B.hexc(hot_core)
    k.new(heat.outputs[0], ramp.inputs["Fac"])
    k.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    st = n.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = strength
    k.new(heat.outputs[0], st.inputs[0])
    k.new(st.outputs[0], bsdf.inputs["Emission Strength"])
    return m


'''
s = s[:a] + new + s[b:]
s = s.replace('''        "warm_": heated_material("chain_warm", "#1a0401", "#a8200a", 1.1),
        "hot_": heated_material("chain_hot", "#4a0c03", "#ffa040", 2.2),''', '''        "warm_": heated_material("chain_warm", "#100200", "#7a1404", 0.75),
        "hot_": heated_material("chain_hot", "#2a0602", "#ff7a28", 1.5),''')
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''def deepen_shadow(img, k=1.7):
    """The shadow the shadow catcher gave, darker (a heavier link sits harder on the band)."""
    rgb, a = img[..., :3], img[..., 3]
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    shade = (lum < 0.03) & (a < 0.98)
    out = img.copy()
    out[..., 3] = np.where(shade, np.clip(a * k, 0, 0.92), a)
    return out''', '''def deepen_shadow(img, k=1.35, edge=8):
    """The shadow the shadow catcher gave, a little darker (a heavier link sits harder on the
    band), and faded out before the cell's sides so no edge of it shows."""
    rgb, a = img[..., :3], img[..., 3]
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    shade = (lum < 0.03) & (a < 0.98)
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    fade = np.clip(d / edge, 0, 1) ** 1.5
    out = img.copy()
    out[..., 3] = np.where(shade, np.clip(a * k, 0, 0.8) * fade, a)
    return out''')
s = s.replace('''def links(variants=6, samples=64, link=(30, 19, 3.2), cell=(44, 34), ss=3):''',
              '''def links(variants=6, samples=64, link=(30, 19, 3.2), cell=(52, 44), ss=3):''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
