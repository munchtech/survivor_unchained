/* Every look the creation screen offers, photographed.
 *
 *   node tools/looks.mjs [warden|reaver|arcanist|stalker ...]
 *
 * Opens character creation, picks each calling, and for each colour, cloak
 * dye, skin tone and hair colour clicks the chip and photographs the figure
 * by the fire. Saves a contact sheet per calling, .shots/looks_<calling>.png,
 * so a choice that changes nothing is plain to see. Expects the dev server
 * on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';
import { execSync } from 'node:child_process';

const want = process.argv.slice(2);
const CALLINGS = ['warden', 'reaver', 'arcanist', 'stalker'];
fs.mkdirSync('.shots/looks', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 1280, height: 720 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
pg.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') { const t = m.text(); if (!/toNonIndexed/.test(t)) console.log(`[${m.type()}]`, t.slice(0, 200)); } });
await pg.goto('http://localhost:5173/?screen=create&manual&quality=low', { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
const settle = async () => { await pg.waitForTimeout(60); await pg.evaluate(() => window.__advance(0.9)); };
const click = async (sel, i) => { await pg.evaluate(([s, n]) => document.querySelectorAll(s)[n]?.click(), [sel, i]); await settle(); };
// The figure stands right of centre; crop around it.
const shoot = async (file) => pg.screenshot({ path: file, clip: { x: 560, y: 110, width: 300, height: 470 }, timeout: 180000 });
for (const [ci, calling] of CALLINGS.entries()) {
  if (want.length && !want.includes(calling)) continue;
  await click('.step', 0);
  await click('.choices .choice', ci);
  await pg.evaluate(() => window.__advance(2.5)); // let the new body finish its flourish
  await click('.step', 3);
  const files = [];
  const counts = await pg.evaluate(() => ({ sw: document.querySelectorAll('.swatch').length, groups: [...document.querySelectorAll('.dyes')].map((g) => g.querySelectorAll('.dye').length) }));
  for (let i = 0; i < counts.sw; i++) { await click('.swatch', i); const f = `.shots/looks/${calling}_colour${i}.png`; await shoot(f); files.push(f); }
  await click('.swatch', 0);
  const groups = ['cloak', 'skin', 'hair'];
  for (const [gi, g] of groups.entries()) {
    for (let i = 0; i < (counts.groups[gi] ?? 0); i++) {
      await pg.evaluate(([gi2, n]) => document.querySelectorAll('.dyes')[gi2].querySelectorAll('.dye')[n].click(), [gi, i]);
      await settle();
      // Cloaks turn round to show themselves: wait for the turn.
      if (g === 'cloak') await pg.evaluate(() => window.__advance(0.6));
      const f = `.shots/looks/${calling}_${g}${i}.png`; await shoot(f); files.push(f);
    }
    await pg.evaluate((gi2) => document.querySelectorAll('.dyes')[gi2].querySelectorAll('.dye')[0].click(), gi);
    await settle();
  }
  console.log(`${calling}: ${files.length} looks`);
  fs.writeFileSync('.shots/looks/list.txt', files.join('\n'));
  execSync(`python3 -c "
import sys
from PIL import Image
fs=open('.shots/looks/list.txt').read().split()
W,H=150,235
cols=10
rows=(len(fs)+cols-1)//cols
g=Image.new('RGB',(W*cols,H*rows))
for k,f in enumerate(fs):
    im=Image.open(f).resize((W,H)); g.paste(im,((k%cols)*W,(k//cols)*H))
g.save('.shots/looks_${calling}.png')"`);
}
await browser.close();
