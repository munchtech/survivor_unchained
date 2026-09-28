/* A monkey at the keyboard: random keys and clicks, looking for stuck states.
 *
 *   node tools/monkey.mjs [zone] [steps] [seed]
 *
 * Quick-starts in a zone (waystation by default) and does random things a
 * player might: menu keys, movement, dashing, talking, clicking whatever
 * button is on screen (never quit or delete), levelling up now and then.
 * After every step it checks what must always hold:
 *   - no page error or console error;
 *   - with no overlay open and nothing fading, the game is running (not
 *     paused, input not captured) and nothing invisible covers the screen;
 *   - an open overlay has something on screen to show for it.
 * Prints each broken rule with the steps that led to it. Expects the dev
 * server on :5173. */
import { chromium } from 'playwright';

const [zone = 'waystation', steps = '300', seed0 = '7'] = process.argv.slice(2);
let seed = Number(seed0);
const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
const pick = (a) => a[Math.floor(rnd() * a.length)];
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 960, height: 540 } });
const problems = [];
const log = [];
pg.on('pageerror', (e) => problems.push(`pageerror: ${e.message} after ${log.slice(-6).join(' > ')}`));
pg.on('console', (m) => { if (m.type() === 'error') problems.push(`console: ${m.text().slice(0, 200)} after ${log.slice(-6).join(' > ')}`); });
await pg.goto(`http://localhost:5173/?quick=stalker&bg=outcast&zone=${zone}&manual&quality=low`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
await pg.evaluate(() => { const g = window.__game.game; g.ch.gold = 400; g.ch.points = 6; g.ch.traitPicks = 2; window.__advance(1); });

const KEYS = ['KeyI', 'KeyC', 'KeyJ', 'KeyM', 'Escape', 'KeyP', 'KeyE', 'Tab', 'Digit1', 'Digit2', 'Digit3', 'KeyX', 'KeyB', 'Enter', 'Space', 'KeyR', 'KeyQ', 'Backspace', 'BracketRight'];
const BAD = /quit|title|delete|abandon|new journey|leave the journey|export|import/i;
for (let i = 0; i < Number(steps); i++) {
  const r = rnd();
  let what;
  if (r < 0.42) {
    const k = pick(KEYS);
    await pg.keyboard.press(k);
    what = k;
  } else if (r < 0.72) {
    // Click something clickable that is on screen.
    what = await pg.evaluate(([bad, roll]) => {
      const els = [...document.querySelectorAll('button, .choice, .card, .pslot.filled, .trait.offer, .dlg-choice, .slot')]
        .filter((e) => { const b = e.getBoundingClientRect(); return b.width > 0 && b.height > 0 && !bad.test(e.textContent ?? '') && getComputedStyle(e).visibility !== 'hidden'; });
      if (!els.length) return 'no buttons';
      const el = els[Math.floor(roll * els.length)];
      el.click();
      return `click "${(el.textContent ?? '').trim().slice(0, 24)}"`;
    }, [BAD, rnd()]);
  } else if (r < 0.87) {
    // Walk somewhere for a moment.
    const k = pick(['KeyW', 'KeyA', 'KeyS', 'KeyD']);
    await pg.keyboard.down(k);
    await pg.evaluate(() => window.__advance(0.6, 30));
    await pg.keyboard.up(k);
    what = `walk ${k}`;
  } else if (r < 0.93) {
    await pg.evaluate(() => { const b = window.__game.game.scene.battle; if (b) b.gainEmber(b.ember.next - b.ember.xp + 0.1); });
    what = 'level up';
  } else {
    // Stand next to someone and press E.
    what = await pg.evaluate(() => {
      const g = window.__game.game, z = g.zone, b = g.scene.battle;
      const list = z?.interactables?.filter((it) => !it.when || it.when()) ?? [];
      if (!list.length || !b) return 'nobody near';
      const it = list[Math.floor(Math.random() * list.length)];
      if (/gate|travel/i.test(it.id + it.verb)) return 'skip travel';
      b.player.x = it.x + 0.8; b.player.z = it.z + 0.8;
      return `go to ${it.id}`;
    });
    await pg.evaluate(() => window.__advance(0.3, 30));
    await pg.keyboard.press('KeyE');
  }
  await pg.waitForTimeout(80);
  await pg.evaluate(() => window.__advance(0.25, 30));
  await pg.waitForTimeout(40);
  log.push(what);
  const bad = await pg.evaluate(() => {
    const g = window.__game.game, ui = window.__ui;
    const ov = ui.overlay.value, lv = ui.levelUp.value, f = ui.fade.value.to;
    const out = [];
    if (!ov && !lv && f < 0.01 && g.mode === 'play') {
      if (g.scene.simPaused) out.push('no overlay, but the game is paused');
      const w = innerWidth, h = innerHeight;
      for (const [x, y] of [[w / 2, h / 2], [w * 0.3, h * 0.4], [w * 0.7, h * 0.6]]) {
        const el = document.elementFromPoint(x, y);
        if (el && el.tagName !== 'CANVAS' && !el.closest('.bark, .plate, .hud-tip, .toast, .speech')) {
          const cs = getComputedStyle(el);
          out.push(`something covers the screen at ${Math.round(x)},${Math.round(y)}: <${el.tagName.toLowerCase()} class="${el.className}"> (pointer-events ${cs.pointerEvents}, position ${cs.position})`);
          break;
        }
      }
    }
    if (ov && !document.querySelector('.inv-overlay, .menu-overlay, .map-overlay, .dialogue, .chapter-overlay, .death, .rest, .levelup, .journal, .ch-wrap, .dlg')) out.push(`overlay "${ov}" is open but nothing shows`);
    return out;
  });
  for (const b of bad) problems.push(`${b} after ${log.slice(-6).join(' > ')}`);
  if (bad.length) {
    // Recover so one stuck state does not hide the next.
    await pg.evaluate(() => { const g = window.__game.game; try { if (g.dialogue) g.endDialogue(); } catch {} g.closeOverlay(); window.__advance(0.3); });
  }
}
const uniq = [...new Set(problems.map((p) => p.replace(/ after .*/, '')))];
console.log(`${zone}: ${steps} steps, ${problems.length} problems, ${uniq.length} kinds`);
for (const u of uniq) console.log(' -', problems.find((p) => p.startsWith(u)));
await browser.close();
