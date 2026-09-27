import * as THREE from 'three';

/* Words in the world: "Interrupted!" over a caster, a wolf-mother's growl,
 * a bandit shouting for help. They are pinned to a point on the ground and
 * follow it, rise a little and fade. DOM, not sprites, so they are crisp
 * and use the game's typefaces; positioned imperatively every frame because
 * a signal per frame per label would be waste. */

interface Bark { el: HTMLDivElement; x: number; y: number; z: number; born: number; life: number; rise: number; follow?: () => { x: number; y: number; z: number } | null }

const v = new THREE.Vector3();

export class BarkLayer {
  readonly root: HTMLDivElement;
  private list: Bark[] = [];
  private time = 0;

  constructor(parent: HTMLElement) {
    this.root = document.createElement('div');
    this.root.className = 'barks';
    parent.appendChild(this.root);
  }

  /** A short shout at a point. */
  alert(text: string, x: number, y: number, z: number, cls = 'alert') {
    this.add(text, x, y, z, cls, 1.3, 1.2);
  }

  /** A line spoken by someone standing there, in a speech bubble. */
  speech(text: string, speaker: string | undefined, x: number, y: number, z: number, follow?: Bark['follow']) {
    // One bubble per speaker: a new line replaces the old.
    const life = Math.max(2.4, text.length * 0.065);
    const el = this.add('', x, y, z, 'speech', life, 0.25, follow);
    if (speaker) {
      const b = document.createElement('b');
      b.textContent = speaker;
      el.appendChild(b);
    }
    el.appendChild(document.createTextNode(text));
  }

  private add(text: string, x: number, y: number, z: number, cls: string, life: number, rise: number, follow?: Bark['follow']) {
    const el = document.createElement('div');
    el.className = `bark ${cls}`;
    el.textContent = text;
    this.root.appendChild(el);
    this.list.push({ el, x, y, z, born: this.time, life, rise, follow });
    if (this.list.length > 24) this.remove(0);
    return el;
  }

  private remove(i: number) {
    this.list[i].el.remove();
    this.list.splice(i, 1);
  }

  update(dt: number, camera: THREE.Camera, w: number, h: number, zoom = 1) {
    this.time += dt;
    for (let i = this.list.length - 1; i >= 0; i--) {
      const b = this.list[i];
      const age = this.time - b.born;
      if (age > b.life) { this.remove(i); continue; }
      if (b.follow) {
        const p = b.follow();
        if (p) { b.x = p.x; b.y = p.y; b.z = p.z; }
      }
      const k = age / b.life;
      v.set(b.x, b.y + 1.9 + b.rise * Math.min(1, age * 2.2), b.z).project(camera);
      if (v.z > 1) { b.el.style.opacity = '0'; continue; }
      const sx = (v.x * 0.5 + 0.5) * w / zoom, sy = (-v.y * 0.5 + 0.5) * h / zoom;
      const pop = age < 0.12 ? 0.7 + (age / 0.12) * 0.4 : age < 0.22 ? 1.1 - ((age - 0.12) / 0.1) * 0.1 : 1;
      const alpha = k > 0.8 ? 1 - (k - 0.8) / 0.2 : 1;
      b.el.style.transform = `translate(${sx}px, ${sy}px) translate(-50%, -100%) scale(${pop})`;
      b.el.style.opacity = String(alpha);
    }
  }

  clear() {
    while (this.list.length) this.remove(0);
  }
}
