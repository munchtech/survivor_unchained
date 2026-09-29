/* Search and fetch Sketchfab models (CC-BY and CC0 only, so they can ship
 * with credit).
 *
 *   SKETCHFAB_TOKEN=... node tools/assets/sketchfab.mjs search "<query>" [maxFaces] [--sheet name] [--animated]
 *   SKETCHFAB_TOKEN=... node tools/assets/sketchfab.mjs get <uid> <out.glb>
 *
 * search prints uid, name, licence, faces, likes and author, and with
 * --sheet saves a contact sheet of thumbnails (.shots/sf_<name>.png) to
 * choose from by eye. get downloads the model as .glb and appends its
 * credit line to public/assets/CREDITS.md. The token is never written to
 * the repository. */
import fs from 'node:fs';

const token = process.env.SKETCHFAB_TOKEN;
if (!token) { console.log('set SKETCHFAB_TOKEN'); process.exit(1); }
const H = { Authorization: `Token ${token}` };
const [cmd, a, b, ...rest] = process.argv.slice(2);

async function api(path) {
  const r = await fetch(`https://api.sketchfab.com/v3${path}`, { headers: H });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

if (cmd === 'search') {
  const max = Number(b) || 40000;
  const out = [];
  for (const lic of ['cc0', 'by']) {
    const animated = process.argv.includes('--animated') ? '&animated=true' : '';
    const d = await api(`/search?type=models&q=${encodeURIComponent(a)}&downloadable=true&license=${lic}&max_face_count=${max}&sort_by=-likeCount&count=24${animated}`);
    for (const m of d.results) out.push(m);
  }
  out.sort((x, y) => y.likeCount - x.likeCount);
  const top = out.slice(0, 24);
  top.forEach((m, i) => console.log(`${String(i).padStart(2)} ${m.uid} | ${m.name.slice(0, 44)} | ${m.license?.label ?? m.license} | ${m.faceCount} faces | ${m.animationCount ?? 0} anims | ${m.likeCount} likes | ${m.user.username}`));
  const si = rest.indexOf('--sheet');
  const sheet = process.argv.includes('--sheet') ? process.argv[process.argv.indexOf('--sheet') + 1] : null;
  if (sheet) {
    // Thumbnails into one HTML page, photographed by the page itself.
    // Fetched here (the headless browser has no route out) and inlined.
    const imgs = (await Promise.all(top.map(async (m, i) => {
      const t = [...(m.thumbnails?.images ?? [])].sort((p, q) => Math.abs(p.width - 256) - Math.abs(q.width - 256))[0];
      let src = '';
      try { const r = await fetch(t.url); src = `data:image/jpeg;base64,${Buffer.from(await r.arrayBuffer()).toString('base64')}`; } catch { /* no picture */ }
      return `<div style="position:relative;display:inline-block;width:256px;height:180px;background:#222"><img src="${src}" style="width:256px;height:180px;object-fit:cover"><span style="position:absolute;left:4px;top:2px;color:#fff;font:bold 18px sans-serif;text-shadow:0 0 3px #000">${i}</span></div>`;
    }))).join('');
    fs.mkdirSync('.shots', { recursive: true });
    fs.writeFileSync(`.shots/sf_${sheet}.html`, `<body style="margin:0;background:#111;width:1536px">${imgs}</body>`);
    const { chromium } = await import('playwright');
    const br = await chromium.launch();
    const pg = await br.newPage({ viewport: { width: 1536, height: 720 } });
    await pg.goto(`file://${process.cwd()}/.shots/sf_${sheet}.html`);
    await pg.waitForTimeout(3000);
    await pg.screenshot({ path: `.shots/sf_${sheet}.png`, fullPage: true });
    await br.close();
    console.log(`sheet .shots/sf_${sheet}.png`);
  }
  void si;
} else if (cmd === 'get') {
  const m = await api(`/models/${a}`);
  const lic = m.license?.label ?? m.license?.slug ?? '';
  if (!/CC0|Attribution(?!-N)/.test(lic) || /NonCommercial|NoDerivs/.test(lic)) throw new Error(`licence not allowed: ${lic}`);
  const d = await api(`/models/${a}/download`);
  const src = d.glb?.url ?? d.gltf?.url;
  if (!src) throw new Error('no download');
  const r = await fetch(src);
  const buf = Buffer.from(await r.arrayBuffer());
  fs.writeFileSync(b, buf);
  console.log(`saved ${b} (${(buf.length / 1e6).toFixed(1)} MB, ${d.glb ? 'glb' : 'gltf zip'})`);
  const credit = `- "${m.name}" by ${m.user.displayName ?? m.user.username} (${m.user.profileUrl ?? `https://sketchfab.com/${m.user.username}`}), ${lic}: ${m.viewerUrl ?? `https://sketchfab.com/3d-models/${a}`} -> ${b}\n`;
  fs.appendFileSync('public/assets/CREDITS.md', credit);
}
