import './ui/fonts';
import './ui/base.css';
import { Renderer, type Quality } from '@/render/renderer';
import { Assets } from '@/render/assets';
import { gallery } from '@/modes/dev/gallery';
import { sandbox } from '@/modes/dev/sandbox';
import { combatDev } from '@/modes/dev/combat';
import { zoneDev } from '@/modes/dev/zone';
import { Input } from '@/core/input';
import { mountUi } from '@/ui/App';
import { renderItemIcons } from '@/ui/itemIcons';
import { Game } from '@/game/game';
import { screen, fade } from '@/ui/store';

/* Boot. The renderer and assets come up first; then the game shell takes
 * over. `?dev=` routes to development views used by the screenshot tools. */

async function boot() {
  const params = new URLSearchParams(location.search);
  const stage = document.getElementById('stage')!;
  const saved = (() => { try { return localStorage.getItem('survivor-unchained.quality'); } catch { return null; } })();
  const renderer = new Renderer(stage, ((params.get('quality') ?? saved) as Quality) || 'high');
  (window as unknown as { __game: unknown }).__game = { renderer };
  await Assets.loadAll();
  renderItemIcons();
  mountUi(document.getElementById('ui')!);

  let tick: (dt: number, t: number) => void = () => {};
  const dev = params.get('dev');
  Input.attach();
  if (dev === 'gallery') tick = gallery(renderer, params);
  else if (dev === 'sandbox') tick = sandbox(renderer, params);
  else if (dev === 'combat') tick = combatDev(renderer, params);
  else if (dev === 'zone') tick = zoneDev(renderer, params);
  else if (dev === 'icons') {
    const { iconKeys, itemIcon } = await import('@/ui/itemIcons');
    const el = document.createElement('div');
    el.style.cssText = 'position:fixed;inset:0;display:flex;flex-wrap:wrap;gap:8px;padding:16px;background:#15131a;overflow:auto;z-index:9;align-content:flex-start';
    for (const k of iconKeys()) {
      const c = document.createElement('div');
      c.style.cssText = 'width:128px;text-align:center;font:12px sans-serif;color:#ccc;background:radial-gradient(circle,#2a2530,#15131a);border:1px solid #333';
      c.innerHTML = `<img src="${itemIcon(k)}" width="128" height="128"><div>${k}</div>`;
      el.appendChild(c);
    }
    document.body.appendChild(el);
  }
  else {
    const game = new Game(renderer);
    (window as unknown as { __game: unknown }).__game = { renderer, game };
    fade.value = { to: 1, seconds: 0 };
    const quick = params.get('quick');
    if (quick) {
      // Straight into the prologue with a stock survivor (tools and tests).
      game.showTitle();
      const arch = (quick in { warden: 1, reaver: 1, arcanist: 1, stalker: 1 } ? quick : 'warden') as 'warden';
      const A = (await import('@/content/archetypes')).ARCHETYPES[arch];
      game.beginJourney({ name: params.get('name') || 'Ashe', archetype: arch, background: (params.get('bg') as 'hunter') || 'hunter', palette: A.palettes[0].id, weaponItem: params.get('weapon') || A.weapons[0], ability: A.abilities[0], startBoon: 'might' });
      // ?zone=waystation: skip ahead (the prologue counts as done).
      const z = params.get('zone');
      if (z && z !== 'lowford') {
        game.world!.facts['prologue.done'] = true;
        game.world!.time = (params.get('time') as 'day') || 'day';
        // ?at=x,z: arrive somewhere other than the zone's entrance.
        const at = params.get('at')?.split(',').map(Number);
        game.enterZone(z, 'lowford', at ? { x: at[0], z: at[1] } : undefined);
      }
      fade.value = { to: 0, seconds: 0.5 };
    } else {
      game.showTitle();
      if (params.get('screen') === 'create') game.newJourney();
    }
    if (params.has('auto')) {
      const { Autopilot } = await import('@/game/autopilot');
      const ap = new Autopilot(game);
      game.autopilot = ap;
      (window as unknown as { __auto: unknown }).__auto = ap;
    }
    tick = (dt) => game.update(dt);
    void screen;
  }

  let last = performance.now();
  let t = 0;
  // ?manual: no animation loop. Tools step time and render single frames,
  // which is how screenshots are taken on machines without a GPU.
  const manual = params.has('manual');
  (window as unknown as { __advance: (sec: number, fps?: number) => number }).__advance = (sec: number, fps = 30) => {
    const steps = Math.max(1, Math.round(sec * fps));
    for (let i = 0; i < steps; i++) { t += 1 / fps; tick(1 / fps, t); }
    const t0 = performance.now();
    renderer.render(1 / fps);
    return performance.now() - t0;
  };
  const frame = (now: number) => {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    t += dt;
    tick(dt, t);
    renderer.render(dt);
    requestAnimationFrame(frame);
  };
  if (!manual) requestAnimationFrame(frame);
  document.body.dataset.ready = '1';
}

boot().catch((e) => {
  console.error(e);
  document.body.dataset.error = String(e?.stack || e);
});
