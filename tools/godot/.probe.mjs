import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 640, height: 400 } });
await pg.goto(`http://localhost:5173/?quick=warden&zone=waystation&time=day&manual&quality=low`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });
const r = await pg.evaluate(() => {
  const root = window.__game.game.scene.zone.root;
  const tex = new Map(), srcs = new Map();
  root.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of [o.material].flat()) for (const k of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap']) {
      const t = m?.[k]; if (!t) continue;
      tex.set(t, 1);
      const s = t.source; const key = s.uuid;
      if (!srcs.has(key)) srcs.set(key, { n: 0, name: t.name, w: s.data?.width, h: s.data?.height, compressed: !!t.isCompressedTexture, mime: t.userData?.mimeType, url: s.data?.src?.slice?.(-60), k, mat: m.name });
      srcs.get(key).n++;
    }
  });
  return { textures: tex.size, sources: srcs.size, list: [...srcs.values()].slice(0, 60) };
});
console.log(JSON.stringify(r, null, 0).replace(/\},\{/g, '},\n{'));
await browser.close();
