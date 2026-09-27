import './ui/fonts';
import './ui/base.css';
import { Renderer, type Quality } from '@/render/renderer';
import { Assets } from '@/render/assets';
import { gallery } from '@/modes/dev/gallery';
import { sandbox } from '@/modes/dev/sandbox';
import { combatDev } from '@/modes/dev/combat';
import { Input } from '@/core/input';

/* Boot. The renderer and assets come up first; then the game shell takes
 * over. `?dev=` routes to development views used by the screenshot tools. */

async function boot() {
  const params = new URLSearchParams(location.search);
  const stage = document.getElementById('stage')!;
  const renderer = new Renderer(stage, (params.get('quality') as Quality) || 'high');
  (window as unknown as { __game: unknown }).__game = { renderer };
  await Assets.loadAll();

  let tick: (dt: number, t: number) => void = () => {};
  const dev = params.get('dev');
  Input.attach();
  if (dev === 'gallery') tick = gallery(renderer, params);
  else if (dev === 'sandbox') tick = sandbox(renderer, params);
  else if (dev === 'combat') tick = combatDev(renderer, params);

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
