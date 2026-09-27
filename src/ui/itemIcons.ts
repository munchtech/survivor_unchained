import * as THREE from 'three';
import { Assets, type PropPack, type CharacterModel } from '@/render/assets';

/* Item icons are photographs of the item.
 *
 * At load, each item's model is lit like a museum piece - warm key from the
 * upper left, cool rim from behind, soft fill - turned to a three-quarter
 * view, and rendered to a small transparent image. So the sword in your
 * pack looks like the sword in your hand, and gear reads as objects, not as
 * pictograms. Where no model exists the item is built from primitives (a
 * ring, a vial, a pelt); where even that would be silly, a glyph is used. */

type Source =
  | { prop: [PropPack, string]; rot?: [number, number, number]; scale?: number }
  | { part: [CharacterModel, string]; rot?: [number, number, number]; scale?: number }
  | { make: () => THREE.Object3D; rot?: [number, number, number]; scale?: number };

const gold = () => new THREE.MeshStandardMaterial({ color: '#e8c070', metalness: 0.9, roughness: 0.28 });
const silver = () => new THREE.MeshStandardMaterial({ color: '#d8dce4', metalness: 0.9, roughness: 0.25 });
const gem = (c: string) => new THREE.MeshStandardMaterial({ color: c, emissive: new THREE.Color(c).multiplyScalar(0.6), roughness: 0.1, metalness: 0.1 });
const cloth = (c: string) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.9 });

function ring(metal: THREE.Material, stone: string) {
  const g = new THREE.Group();
  const band = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.11, 10, 28), metal);
  const s = new THREE.Mesh(new THREE.OctahedronGeometry(0.2, 0), gem(stone));
  s.position.y = 0.58;
  g.add(band, s);
  return g;
}
function amulet(stone: string, pendant: 'gem' | 'fang' | 'bone' = 'gem') {
  const g = new THREE.Group();
  const chain = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.028, 6, 40), gold());
  chain.scale.set(1, 1.15, 1);
  chain.position.y = 0.28;
  g.add(chain);
  // Links: small beads so it reads as a chain, not a wire.
  for (let i = 0; i < 18; i++) {
    const a = (i / 18) * Math.PI * 2;
    const bead = new THREE.Mesh(new THREE.TorusGeometry(0.045, 0.014, 4, 8), gold());
    bead.position.set(Math.cos(a) * 0.55, 0.28 + Math.sin(a) * 0.63, 0);
    bead.rotation.set(0, i % 2 ? Math.PI / 2 : 0, a);
    g.add(bead);
  }
  const bail = new THREE.Mesh(new THREE.TorusGeometry(0.07, 0.022, 6, 12), gold());
  bail.position.y = -0.39;
  g.add(bail);
  let p: THREE.Mesh;
  if (pendant === 'fang') {
    p = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.62, 7), new THREE.MeshStandardMaterial({ color: '#f2ead4', roughness: 0.45 }));
    p.rotation.z = Math.PI;
    p.position.y = -0.74;
    p.geometry.translate(0.03, 0, 0);
  } else if (pendant === 'bone') {
    p = new THREE.Mesh(new THREE.CapsuleGeometry(0.09, 0.3, 4, 8), new THREE.MeshStandardMaterial({ color: '#e8dcc0', roughness: 0.7 }));
    p.position.y = -0.66;
    for (const y of [-0.52, -0.8]) {
      const k = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 6), new THREE.MeshStandardMaterial({ color: '#e8dcc0', roughness: 0.7 }));
      k.position.set(0.05, y, 0);
      g.add(k);
    }
  } else {
    p = new THREE.Mesh(new THREE.OctahedronGeometry(0.2, 0), gem(stone));
    p.scale.set(0.8, 1.2, 0.5);
    p.position.y = -0.66;
    const setting = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.03, 6, 16), silver());
    setting.position.y = -0.66;
    setting.scale.set(0.85, 1.25, 1);
    g.add(setting);
  }
  g.add(p);
  return g;
}
function vial(liquid: string) {
  const g = new THREE.Group();
  const glass = new THREE.Mesh(new THREE.SphereGeometry(0.42, 16, 12), new THREE.MeshStandardMaterial({ color: liquid, emissive: new THREE.Color(liquid).multiplyScalar(0.35), roughness: 0.08, transparent: true, opacity: 0.88 }));
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.16, 0.35, 12), new THREE.MeshStandardMaterial({ color: '#cfe0e8', roughness: 0.1, transparent: true, opacity: 0.6 }));
  neck.position.y = 0.52;
  const cork = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.1, 0.14, 10), new THREE.MeshStandardMaterial({ color: '#8a5a32', roughness: 0.8 }));
  cork.position.y = 0.74;
  g.add(glass, neck, cork);
  return g;
}
function pelt(c: string) {
  const geo = new THREE.PlaneGeometry(1.4, 1, 8, 6);
  const pos = geo.getAttribute('position');
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i);
    pos.setZ(i, Math.sin(x * 3) * 0.06 + Math.cos(y * 4) * 0.05);
    if (Math.abs(x) > 0.55 && Math.abs(y) > 0.35) pos.setXY(i, x * 0.8, y * 0.8);
  }
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: c, roughness: 1, side: THREE.DoubleSide, flatShading: true }));
  m.rotation.x = -0.9;
  return m;
}
function circlet() {
  const g = new THREE.Group();
  const band = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.05, 8, 40), silver());
  band.rotation.x = Math.PI / 2;
  g.add(band);
  // A crescent brow-piece and a pale stone.
  const moon = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.045, 8, 20, Math.PI * 1.1), silver());
  moon.position.set(0, 0.15, 0.62);
  moon.rotation.z = -0.1;
  const stone = new THREE.Mesh(new THREE.SphereGeometry(0.1, 12, 10), gem('#cfe8ff'));
  stone.position.set(0, 0.05, 0.66);
  g.add(moon, stone);
  for (const sx of [-1, 1]) {
    const leaf = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.22, 5), silver());
    leaf.position.set(sx * 0.3, 0.06, 0.56);
    leaf.rotation.z = sx * 0.9;
    g.add(leaf);
  }
  return g;
}
function mask() {
  const g = new THREE.Group();
  const leather = new THREE.MeshStandardMaterial({ color: '#5a4430', roughness: 0.75 });
  const face = new THREE.Mesh(new THREE.SphereGeometry(0.5, 16, 12, 0, Math.PI), leather);
  face.scale.set(1, 1.1, 0.7);
  const beak = new THREE.Mesh(new THREE.ConeGeometry(0.2, 1.0, 10), leather);
  beak.rotation.x = Math.PI / 2 + 0.35;
  beak.position.set(0, -0.2, 0.62);
  g.add(face, beak);
  for (const x of [-0.19, 0.19]) {
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.11, 0.028, 6, 16), gold());
    rim.position.set(x, 0.12, 0.36);
    const glass = new THREE.Mesh(new THREE.CircleGeometry(0.1, 16), new THREE.MeshStandardMaterial({ color: '#9ad8a0', emissive: '#2a6a3a', roughness: 0.05 }));
    glass.position.set(x, 0.12, 0.365);
    g.add(rim, glass);
  }
  const strap = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.03, 6, 20, Math.PI), new THREE.MeshStandardMaterial({ color: '#2a2018', roughness: 0.9 }));
  strap.rotation.y = Math.PI / 2;
  g.add(strap);
  return g;
}
function kerchief() {
  // A red cloth folded into a triangle, knotted at the corners.
  const geo = new THREE.BufferGeometry();
  const shape = new THREE.Shape();
  shape.moveTo(-0.8, 0.4); shape.lineTo(0.8, 0.4); shape.lineTo(0, -0.7); shape.closePath();
  const g2 = new THREE.ExtrudeGeometry(shape, { depth: 0.04, bevelEnabled: true, bevelSize: 0.02, bevelThickness: 0.02, bevelSegments: 1, curveSegments: 1 });
  const pos = g2.getAttribute('position');
  for (let i = 0; i < pos.count; i++) pos.setZ(i, pos.getZ(i) + Math.sin(pos.getX(i) * 3) * 0.06 + pos.getY(i) * pos.getY(i) * 0.15);
  g2.computeVertexNormals();
  void geo;
  const g = new THREE.Group();
  const red = cloth('#b8201e');
  g.add(new THREE.Mesh(g2, red));
  for (const x of [-0.82, 0.82]) {
    const knot = new THREE.Mesh(new THREE.SphereGeometry(0.09, 8, 6), red);
    knot.position.set(x, 0.42, 0.03);
    const tail = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.3, 5), red);
    tail.position.set(x * 1.08, 0.26, 0.03);
    tail.rotation.z = x > 0 ? 0.5 : -0.5;
    g.add(knot, tail);
  }
  return g;
}
function lens() {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.TorusGeometry(0.45, 0.07, 8, 28), gold()));
  const glass = new THREE.Mesh(new THREE.CircleGeometry(0.42, 28), new THREE.MeshStandardMaterial({ color: '#c8e8ff', roughness: 0.05, transparent: true, opacity: 0.5, emissive: '#2a4a6a' }));
  g.add(glass);
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, 0.6, 8), new THREE.MeshStandardMaterial({ color: '#5a3a22', roughness: 0.7 }));
  handle.position.set(0.45, -0.55, 0);
  handle.rotation.z = 0.7;
  g.add(handle);
  return g;
}
function totem() {
  const g = new THREE.Group();
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.22, 1.4, 6), new THREE.MeshStandardMaterial({ color: '#6a4a2c', roughness: 0.9, flatShading: true }));
  g.add(post);
  for (const y of [0.25, -0.2]) {
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.21, 0.04, 6, 12), new THREE.MeshStandardMaterial({ color: '#7ab8ff', emissive: '#3a6aaa', roughness: 0.3 }));
    band.rotation.x = Math.PI / 2;
    band.position.y = y;
    g.add(band);
  }
  const top = new THREE.Mesh(new THREE.OctahedronGeometry(0.2, 0), gem('#9ac8ff'));
  top.position.y = 0.85;
  g.add(top);
  return g;
}
function seedPouch() {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.SphereGeometry(0.45, 10, 8), cloth('#6a5238')));
  const tie = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.04, 6, 12), cloth('#3a2a18'));
  tie.position.y = 0.42; tie.rotation.x = Math.PI / 2;
  g.add(tie);
  for (let i = 0; i < 3; i++) {
    const thorn = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.25, 4), cloth('#5a8a3a'));
    thorn.position.set(-0.1 + i * 0.1, 0.62, 0);
    g.add(thorn);
  }
  return g;
}
function crystal(c: string) { return new THREE.Mesh(new THREE.OctahedronGeometry(0.5, 0).scale(0.7, 1.2, 0.7), gem(c)); }
function sigil() {
  const m = new THREE.Mesh(new THREE.OctahedronGeometry(0.6, 0).scale(1, 1.2, 0.35), new THREE.MeshStandardMaterial({ color: '#1a1820', emissive: '#4a2a8a', roughness: 0.3, metalness: 0.4, flatShading: true }));
  return m;
}
function book(c: string) {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.2, 0.25), cloth(c)));
  const pages = new THREE.Mesh(new THREE.BoxGeometry(0.82, 1.12, 0.2), cloth('#e8dcc0'));
  pages.position.x = 0.05;
  g.add(pages);
  return g;
}
function root() {
  const g = new THREE.Group();
  const bark = cloth('#8a6a44');
  const main = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.16, 1.3, 7, 4), bark);
  const pos = main.geometry.getAttribute('position');
  for (let i = 0; i < pos.count; i++) pos.setX(i, pos.getX(i) + Math.sin(pos.getY(i) * 4) * 0.08);
  main.geometry.computeVertexNormals();
  g.add(main);
  for (const [y, a] of [[-0.2, 0.9], [0.1, -0.8], [-0.4, -1.1]] as const) {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.06, 0.5, 5), bark);
    b.position.set(Math.sin(a) * 0.15, y, 0);
    b.rotation.z = a;
    g.add(b);
  }
  const leaves = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.4, 5), cloth('#5a8a3a'));
  leaves.position.y = 0.8;
  g.add(leaves);
  return g;
}
function flower() {
  const g = new THREE.Group();
  const petal = new THREE.MeshStandardMaterial({ color: '#d8e8ff', emissive: '#6a8ac8', emissiveIntensity: 0.6, roughness: 0.4, side: THREE.DoubleSide });
  for (let i = 0; i < 6; i++) {
    const p = new THREE.Mesh(new THREE.SphereGeometry(0.3, 10, 6).scale(0.45, 0.08, 1), petal);
    const a = (i / 6) * Math.PI * 2;
    p.position.set(Math.sin(a) * 0.28, 0, Math.cos(a) * 0.28);
    p.rotation.y = a;
    p.rotation.x = -0.35;
    g.add(p);
  }
  const heart = new THREE.Mesh(new THREE.SphereGeometry(0.12, 10, 8), gem('#fff2b0'));
  heart.position.y = 0.04;
  g.add(heart);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.8, 5), cloth('#4a7a3a'));
  stem.position.y = -0.42;
  g.add(stem);
  return g;
}
function dust() {
  const g = new THREE.Group();
  const bag = new THREE.Mesh(new THREE.SphereGeometry(0.45, 12, 10).scale(1, 0.8, 1), cloth('#5a4a3a'));
  g.add(bag);
  const heap = new THREE.Mesh(new THREE.ConeGeometry(0.4, 0.3, 12), new THREE.MeshStandardMaterial({ color: '#d8d0c0', roughness: 1 }));
  heap.position.y = 0.42;
  g.add(heap);
  const tie = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.04, 6, 14), cloth('#2a2018'));
  tie.position.y = 0.3; tie.rotation.x = Math.PI / 2;
  g.add(tie);
  return g;
}
function scroll() {
  const g = new THREE.Group();
  const paper = cloth('#e2d2aa');
  const roll = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 1.1, 16), paper);
  g.add(roll);
  const wood = new THREE.MeshStandardMaterial({ color: '#4a2e1a', roughness: 0.6 });
  for (const y of [-0.62, 0.62]) {
    const knob = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.16, 10), wood);
    knob.position.y = y;
    const cap = new THREE.Mesh(new THREE.SphereGeometry(0.08, 10, 8), wood);
    cap.position.y = y * 1.13;
    g.add(knob, cap);
  }
  const ribbon = new THREE.Mesh(new THREE.TorusGeometry(0.175, 0.025, 6, 20), cloth('#8a1a1a'));
  ribbon.rotation.x = Math.PI / 2;
  g.add(ribbon);
  const seal = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.03, 12), new THREE.MeshStandardMaterial({ color: '#a01818', roughness: 0.4 }));
  seal.rotation.x = Math.PI / 2;
  seal.position.set(0, 0, 0.19);
  g.add(seal);
  g.rotation.z = 0.9;
  return g;
}
function mapSheet() {
  const g = new THREE.Group();
  const geo = new THREE.PlaneGeometry(1.3, 0.95, 12, 8);
  const pos = geo.getAttribute('position');
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    // One end still curls where it was rolled.
    if (x > 0.35) { const a = (x - 0.35) * 3.2; pos.setX(i, 0.35 + Math.sin(a) * 0.3); pos.setZ(i, (1 - Math.cos(a)) * 0.3); }
    else pos.setZ(i, Math.sin(pos.getY(i) * 4) * 0.02);
  }
  geo.computeVertexNormals();
  const canvas = document.createElement('canvas');
  canvas.width = 128; canvas.height = 96;
  const c = canvas.getContext('2d')!;
  c.fillStyle = '#dccaa0'; c.fillRect(0, 0, 128, 96);
  c.strokeStyle = '#5a3a20'; c.lineWidth = 2;
  c.beginPath(); c.moveTo(10, 70); c.bezierCurveTo(40, 40, 60, 80, 90, 30); c.stroke();
  c.setLineDash([4, 4]); c.beginPath(); c.moveTo(20, 20); c.lineTo(60, 50); c.lineTo(80, 88); c.stroke();
  c.fillStyle = '#8a1a1a'; c.beginPath(); c.arc(90, 30, 5, 0, 7); c.fill();
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  g.add(new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.9, side: THREE.DoubleSide })));
  g.rotation.x = -0.9;
  return g;
}
function bandage() {
  const g = new THREE.Group();
  const linen = cloth('#ece2cc');
  g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.5, 20), linen));
  for (let i = 0; i < 4; i++) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.42 - i * 0.07, 0.008, 4, 24), cloth('#c8bca4'));
    ring.rotation.x = Math.PI / 2;
    ring.position.y = 0.251;
    g.add(ring);
  }
  const tail = new THREE.Mesh(new THREE.PlaneGeometry(0.46, 0.7), new THREE.MeshStandardMaterial({ color: '#ece2cc', roughness: 1, side: THREE.DoubleSide }));
  tail.position.set(0.3, -0.35, 0.3);
  tail.rotation.set(-0.5, 0.6, 0.2);
  g.add(tail);
  return g;
}

const SOURCES: Record<string, Source> = {
  sword: { prop: ['adventure_items', 'sword_1handed'], rot: [0, 0, -0.75] },
  cleaver: { prop: ['adventure_items', 'axe_2handed'], rot: [0, 0, -0.75] },
  axe: { prop: ['adventure_items', 'axe_1handed'], rot: [0, 0, -0.75] },
  dagger: { prop: ['adventure_items', 'dagger'], rot: [0, 0, -0.75] },
  bow: { prop: ['adventure_items', 'crossbow_1handed'], rot: [0.4, 0.8, -0.3] },
  staff: { prop: ['adventure_items', 'staff'], rot: [0, 0, -0.7] },
  wand: { prop: ['adventure_items', 'wand'], rot: [0, 0, -0.7], scale: 0.9 },
  wand_dark: { prop: ['adventure_items', 'Skeleton_Staff'], rot: [0, 0, -0.7], scale: 0.9 },
  shield: { prop: ['adventure_items', 'shield_round_color'], rot: [0, 0.5, 0] },
  censer: { prop: ['halloween', 'lantern_hanging'], rot: [0, 0.4, 0] },
  lantern: { prop: ['halloween', 'lantern_standing'], rot: [0, 0.4, 0] },
  lamp: { prop: ['dungeon', 'torch_lit'], rot: [0, 0.4, 0] },
  chest: { prop: ['dungeon', 'trunk_small_A'], rot: [0.3, 0.6, 0] },
  coin: { prop: ['dungeon', 'coin_stack_small'], rot: [0.4, 0.5, 0] },
  key: { prop: ['dungeon', 'key'], rot: [0.6, 0.4, 0.4] },
  potion: { make: () => vial('#e8323a') },
  antidote: { make: () => vial('#6ad84a') },
  vial: { make: () => vial('#7ad86a') },
  vial_orange: { make: () => vial('#ff8a2a') },
  bandage: { make: bandage, rot: [0.5, 0.3, 0.2] },
  helm: { part: ['knight', 'Knight_Helmet'], rot: [0.2, 0.6, 0] },
  helm_light: { part: ['barbarian', 'Barbarian_Hat'], rot: [0.2, 0.6, 0] },
  cloak: { part: ['knight', 'Knight_Cape'], rot: [0.2, 2.6, 0] },
  armor: { part: ['knight', 'Knight_Body'], rot: [0.1, 0.5, 0] },
  mask: { make: mask, rot: [0.15, 0.7, 0] },
  kerchief: { make: kerchief, rot: [-0.3, 0.3, 0.1] },
  circlet: { make: circlet, rot: [0.55, 0.35, 0] },
  ring: { make: () => ring(gold(), '#c8323a'), rot: [0.4, 0.5, 0] },
  fang: { make: () => amulet('#fff', 'fang'), rot: [0, 0.3, 0] },
  bone: { make: () => amulet('#fff', 'bone'), rot: [0, 0.3, 0] },
  lens: { make: lens, rot: [0.2, 0.5, 0] },
  totem: { make: totem, rot: [0.2, 0.4, 0.4] },
  seed: { make: seedPouch, rot: [0.2, 0.4, 0] },
  pelt: { make: () => pelt('#8a8a90'), rot: [0, 0.3, 0] },
  hide: { make: () => pelt('#7a5a3a'), rot: [0, 0.3, 0] },
  ember: { make: () => crystal('#ffa04a'), rot: [0.2, 0.5, 0] },
  sigil: { make: sigil, rot: [0.3, 0.6, 0] },
  book: { prop: ['adventure_items', 'spellbook_closed'], rot: [0.3, 0.6, 0] },
  root: { make: root, rot: [0.2, 0.4, 0.3] },
  journal: { make: () => book('#5a2a2a'), rot: [0.3, -0.5, 0] },
  flower: { make: flower, rot: [0.5, 0.3, 0] },
  dust: { make: dust, rot: [0.5, 0.3, 0] },
  scroll: { make: scroll, rot: [0.3, 0.4, 0] },
  map: { make: mapSheet, rot: [0.2, 0.3, 0] },
  moon: { make: () => amulet('#bfe0ff'), rot: [0, 0.3, 0] },
  bomb: { prop: ['dungeon', 'keg'], rot: [0.3, 0.5, 0], scale: 0.9 },
  picks: { prop: ['dungeon', 'keyring'], rot: [0.5, 0.4, 0] },
  armor_heavy: { part: ['knight', 'Knight_Body'], rot: [0.1, 0.5, 0] },
  armor_light: { part: ['barbarian', 'Barbarian_Body'], rot: [0.1, 0.5, 0] },
};

const cache = new Map<string, string>();

/** Render every icon source once. Call after assets load. */
export function renderItemIcons(size = 128) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  let gl: THREE.WebGLRenderer;
  try {
    gl = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true });
  } catch {
    return;
  }
  gl.setClearColor(0x000000, 0);
  gl.outputColorSpace = THREE.SRGBColorSpace;
  gl.toneMapping = THREE.ACESFilmicToneMapping;
  gl.toneMappingExposure = 1.15;
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(26, 1, 0.1, 100);
  cam.position.set(0, 0.4, 5);
  cam.lookAt(0, 0, 0);
  const key = new THREE.DirectionalLight(0xffe2b8, 3.2);
  key.position.set(-3, 4, 4);
  const rim = new THREE.DirectionalLight(0x8ab0ff, 2.4);
  rim.position.set(3, 2, -4);
  const fill = new THREE.HemisphereLight(0xb8c8ff, 0x3a2a1a, 0.9);
  scene.add(key, rim, fill);
  const holder = new THREE.Group();
  scene.add(holder);
  for (const [name, src] of Object.entries(SOURCES)) {
    let obj: THREE.Object3D | null = null;
    try {
      if ('prop' in src) obj = Assets.prop(src.prop[0], src.prop[1]);
      else if ('part' in src) {
        const tmpl = Assets.characterTemplate(src.part[0]);
        let found: THREE.Object3D | null = null;
        tmpl.traverse((o) => { if (!found && o.name === src.part[1] && (o as THREE.Mesh).isMesh) found = o; });
        if (found) {
          const m = found as THREE.Mesh;
          obj = new THREE.Mesh(m.geometry, m.material);
        }
      } else obj = src.make();
    } catch {
      obj = null;
    }
    if (!obj) continue;
    holder.clear();
    holder.position.set(0, 0, 0);
    holder.scale.setScalar(1);
    const pivot = new THREE.Group();
    pivot.add(obj);
    if (src.rot) pivot.rotation.set(...src.rot);
    // Frame it: measure the object on its own (no parent), then centre and
    // fit it in the holder.
    pivot.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(pivot, true);
    const c = box.getCenter(new THREE.Vector3());
    const s = box.getSize(new THREE.Vector3());
    const k = (2.1 / Math.max(s.x, s.y, s.z * 0.8, 1e-3)) * (src.scale ?? 1);
    holder.add(pivot);
    holder.scale.setScalar(k);
    holder.position.set(-c.x * k, -c.y * k, -c.z * k);
    holder.updateMatrixWorld(true);
    gl.render(scene, cam);
    cache.set(name, canvas.toDataURL('image/png'));
    holder.position.set(0, 0, 0);
    holder.scale.setScalar(1);
  }
  gl.dispose();
  gl.forceContextLoss();
}

export function itemIcon(key: string): string | null {
  return cache.get(key) ?? null;
}

/** Every icon key with a photograph, for the gallery. */
export function iconKeys(): string[] { return [...cache.keys()]; }
