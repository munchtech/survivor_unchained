import './ui/fonts';
import './ui/base.css';
import { Renderer } from '@/render/renderer';
import { Assets } from '@/render/assets';
import { gallery } from '@/modes/dev/gallery';
import { sandbox } from '@/modes/dev/sandbox';
import { combatDev } from '@/modes/dev/combat';
import { zoneDev } from '@/modes/dev/zone';
import { Input } from '@/core/input';
import { desktop, wantsFullscreen } from '@/core/desktop';
import { mountUi } from '@/ui/App';
import { renderItemIcons } from '@/ui/itemIcons';
import { Game } from '@/game/game';
import { screen, fade, overlay, toast } from '@/ui/store';
import { actions } from '@/game/actions';
import * as uiStore from '@/ui/store';

/* Boot. The renderer and assets come up first; then the game shell takes
 * over. `?dev=` routes to development views used by the screenshot tools. */

async function boot() {
  const params = new URLSearchParams(location.search);
  const stage = document.getElementById('stage')!;
  const saved = (() => { try { return localStorage.getItem('survivor-unchained.quality'); } catch { return null; } })();
  const wantQ = params.get('quality') ?? saved;
  // The desktop build opens fullscreen unless the player chose a window.
  if (desktop && !params.has('manual')) void desktop.fullscreen(wantsFullscreen());
  const renderer = new Renderer(stage, wantQ === 'low' || wantQ === 'medium' || wantQ === 'high' ? wantQ : 'high');
  (window as unknown as { __game: unknown }).__game = { renderer };
  // Compressed textures: what this GPU takes (render/gltfShared.ts).
  (await import('@/render/gltfShared')).initTextures(renderer.gl);
  // The KayKit set, the people (bodies, outfits, hair, the animation
  // libraries) and the weapons, together.
  const [{ preloadPeople }, { preloadArms }, { bakeReady }, { preloadEnv }, { envUsed }] = await Promise.all([
    import('@/render/people'), import('@/render/arms'), import('@/render/bakePerson'), import('@/render/env'), import('@/world/zones/envUse'),
  ]);
  // ...and the world's kits: what the zones build with (render/env.ts).
  await Promise.all([Assets.loadAll(), preloadPeople(), preloadArms(), bakeReady(), preloadEnv(envUsed())]);
  renderItemIcons();
  mountUi(document.getElementById('ui')!);

  let tick: (dt: number, t: number) => void = () => {};
  const dev = params.get('dev');
  Input.loadBindings();
  Input.attach();
  if (dev === 'gallery') tick = gallery(renderer, params);
  else if (dev === 'sandbox') tick = sandbox(renderer, params);
  else if (dev === 'combat') tick = combatDev(renderer, params);
  else if (dev === 'zone') tick = zoneDev(renderer, params);
  else if (dev === 'house') tick = await (await import('@/modes/dev/env')).houseDev(renderer, params);
  else if (dev === 'env') tick = await (await import('@/modes/dev/env')).envDev(renderer, params);
  else if (dev === 'armory') tick = await (await import('@/modes/dev/armory')).armoryDev(renderer, params);
  else if (dev === 'people') tick = await (await import('@/modes/dev/people')).peopleDev(renderer, params);
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
    game.pauseWhenAway = !params.has('manual');
    (window as unknown as { __game: unknown }).__game = { renderer, game };
    // For tools: the interface's state (which overlay is open, the draft...).
    (window as unknown as { __ui: unknown }).__ui = uiStore;
    fade.value = { to: 1, seconds: 0 };
    const quick = params.get('quick');
    if (quick) {
      // Straight into the prologue with a stock survivor (tools and tests).
      game.showTitle();
      const arch = (quick in { warden: 1, reaver: 1, arcanist: 1, stalker: 1 } ? quick : 'warden') as 'warden';
      const A = (await import('@/content/archetypes')).ARCHETYPES[arch];
      game.beginJourney({ name: params.get('name') || 'Ashe', archetype: arch, background: (params.get('bg') as 'hunter') || 'hunter', palette: A.palettes[0].id, weaponItem: params.get('weapon') || A.weapons[0], ability: A.abilities[0], startBoon: params.get('blessing') || 'hunters_mark' });
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
      ap.idle = params.get('auto') === 'idle';
      game.autopilot = ap;
      (window as unknown as { __auto: unknown }).__auto = ap;
    }
    tick = (dt) => game.update(dt);
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
  // First run on this machine (no picture setting chosen yet): if play
  // cannot keep up, step down a level rather than stutter, and say so. The
  // step is saved, and Settings can undo it.
  let autoQuality = !manual && !params.get('quality') && !saved && !params.get('dev');
  // Measured in real time (a frame's dt is clamped, and a slow machine is
  // exactly the one whose frames are long).
  let since = 0, frames = 0, slowFrames = 0;
  const watchSpeed = (now: number, raw: number) => {
    if (!autoQuality) return;
    if (screen.value !== 'play' || overlay.value || document.hidden) { since = 0; frames = 0; slowFrames = 0; return; }
    if (!since) since = now;
    const age = (now - since) / 1000;
    if (age < 5) return; // shaders compiling, the zone settling
    frames++;
    if (raw > 1 / 42) slowFrames++;
    if (age < 11 || frames < 12) return;
    const q = renderer.quality;
    if (slowFrames / frames > 0.5 && q !== 'low') {
      const next = q === 'high' ? 'medium' : 'low';
      actions.setQuality(next);
      toast('world', `Graphics set to ${next[0].toUpperCase()}${next.slice(1)} for smoother play`, { sub: 'Change it any time in the pause menu' });
      since = 0; frames = 0; slowFrames = 0;
      if (next === 'low') autoQuality = false;
    } else autoQuality = false;
  };
  const frame = (now: number) => {
    const raw = (now - last) / 1000;
    const dt = Math.min(0.1, raw);
    last = now;
    t += dt;
    tick(dt, t);
    renderer.render(dt);
    watchSpeed(now, raw);
    requestAnimationFrame(frame);
  };
  if (!manual) requestAnimationFrame(frame);
  document.body.dataset.ready = '1';
}

boot().catch((e) => {
  console.error(e);
  document.body.dataset.error = String(e?.stack || e);
});
