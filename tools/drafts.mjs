/* Level up a survivor again and again in the Verge and photograph each
 * draft, taking the first skill each time, so the run of choices a player
 * sees over a night can be read at a glance.
 *
 *   node tools/drafts.mjs [calling] [levels]
 *
 * Saves .shots/drafts_<calling>.png. Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';
import { execSync } from 'node:child_process';

const [calling = 'warden', levels = '8'] = process.argv.slice(2);
fs.mkdirSync('.shots/drafts', { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 1280, height: 720 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
await pg.goto(`http://localhost:5173/?quick=${calling}&bg=hunter&zone=verge&at=-60,8&manual&quality=low`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
await pg.evaluate(() => window.__advance(1));
const files = [];
for (let i = 0; i < Number(levels); i++) {
  await pg.evaluate(() => { const b = window.__game.game.scene.battle; b.player.hp = b.maxHp; b.gainEmber(b.ember.next - b.ember.xp + 0.1); window.__advance(0.8); });
  await pg.waitForFunction(() => document.querySelectorAll('.card').length > 0, null, { timeout: 5000 }).catch(() => console.log('  no draft'));
  // Cards are armed a moment after they appear.
  await pg.waitForTimeout(700);
  await pg.evaluate(() => window.__advance(0.4));
  const f = `.shots/drafts/${calling}_${i}.png`;
  await pg.screenshot({ path: f, clip: { x: 300, y: 90, width: 680, height: 530 }, timeout: 180000 });
  files.push(f);
  const picked = await pg.evaluate(() => {
    const cards = [...document.querySelectorAll('.card')];
    const skill = cards.findIndex((c) => /k-(weapon|rank|evolve)/.test(c.className));
    const k = skill >= 0 ? skill : 0;
    const t = cards[k]?.querySelector('.card-title')?.textContent;
    cards[k]?.click();
    return t;
  });
  // The pick lands 300 ms (real time) after the click, once the card has flown.
  await pg.waitForTimeout(500);
  await pg.evaluate(() => window.__advance(1.2));
  await pg.waitForFunction(() => !document.querySelector('.levelup'), null, { timeout: 5000 }).catch(() => console.log('  draft still open'));
  console.log(`level ${i + 2}: took ${picked}`);
}
fs.writeFileSync('.shots/drafts/list.txt', files.join('\n'));
execSync(`python3 -c "
from PIL import Image
fs=open('.shots/drafts/list.txt').read().split()
W,H=340,265
cols=4
rows=(len(fs)+cols-1)//cols
g=Image.new('RGB',(W*cols,H*rows))
for k,f in enumerate(fs):
    im=Image.open(f).resize((W,H)); g.paste(im,((k%cols)*W,(k//cols)*H))
g.save('.shots/drafts_${calling}.png')"`);
await browser.close();
