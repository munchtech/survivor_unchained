/* Load the game at a query and print what an expression evaluates to there.
 *
 *   node tools/probe.mjs "quick=warden&zone=verge" "window.__game.game.scene.zone.root.children.length"
 *
 * For questions a screenshot cannot answer: what is solid near a point, how
 * many copies of a tree a zone holds, what a frame costs. Runs at low
 * quality, stepping frames by hand. Expects the dev server on :5173. */
import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-webgl'] });
const pg = await browser.newPage({ viewport: { width: 320, height: 180 } });
pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
await pg.goto(`http://localhost:5173/?${process.argv[2]}&manual&quality=low`, { waitUntil: 'load' });
await pg.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 180000 });
console.log(await pg.evaluate(process.argv[3]));
await browser.close();
