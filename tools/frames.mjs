/* A run of frames, for judging motion a still cannot show.
 *
 *   node tools/frames.mjs "<query>" <name> [frames] [fps] [setup-expression]
 *
 * Loads the game at a query (manual time), evaluates the optional setup
 * expression once, then steps time 1/fps at a time and grabs a frame after
 * each step. Before each grab, window.__frame() is called if the setup
 * defined it (to aim the camera, say). Saves .shots/<name>_NN.png and a
 * contact sheet .shots/<name>.png. Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [query = 'quick=warden', name = 'frames', count = '12', fps = '15', setup = ''] = process.argv.slice(2);
const W = 640, H = 400;
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: W, height: H } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
await pg.goto(`http://localhost:5173/?${query}&manual&quality=low`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });
if (setup) console.log('setup:', await pg.evaluate(setup));
const shots = [];
for (let i = 0; i < Number(count); i++) {
  const info = await pg.evaluate((f) => { window.__advance(1 / f, f); return window.__frame ? window.__frame() : ''; }, Number(fps));
  const file = `.shots/${name}_${String(i).padStart(2, '0')}.png`;
  await pg.screenshot({ path: file });
  shots.push(file);
  if (info) console.log(i, info);
}
// Contact sheet, in the page (it has a canvas).
const cols = 4, rows = Math.ceil(shots.length / cols);
const sheet = await pg.evaluate(async ({ imgs, cols, rows, W, H }) => {
  const c = document.createElement('canvas');
  c.width = cols * W / 2; c.height = rows * H / 2;
  const g = c.getContext('2d');
  for (let i = 0; i < imgs.length; i++) {
    const im = new Image();
    im.src = imgs[i];
    await im.decode();
    g.drawImage(im, (i % cols) * W / 2, Math.floor(i / cols) * H / 2, W / 2, H / 2);
    g.fillStyle = '#fff'; g.font = '14px sans-serif'; g.fillText(String(i), (i % cols) * W / 2 + 6, Math.floor(i / cols) * H / 2 + 18);
  }
  return c.toDataURL('image/png');
}, { imgs: shots.map((f) => `data:image/png;base64,${fs.readFileSync(f).toString('base64')}`), cols, rows, W, H });
fs.writeFileSync(`.shots/${name}.png`, Buffer.from(sheet.split(',')[1], 'base64'));
console.log(`saved .shots/${name}.png`);
await browser.close();
