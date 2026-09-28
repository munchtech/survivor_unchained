import * as THREE from 'three';
import { damp, clamp } from '@/core/math';
import { shakeScale } from './motion';

/* The game camera: a steep three-quarter view that follows the survivor.
 *
 *   - it leads a little in the direction of travel, so you see more of what
 *     you are running into than what you are running from;
 *   - it eases to a new distance when the game asks (in close for a
 *     conversation: `targetDistance`);
 *   - shake uses a trauma model (shake = trauma^2) with smooth noise, so a big
 *     hit is felt and a stream of small ones is not a blur;
 *   - `focusOverride` lets a cutscene or a boss intro frame something else. */

export class FollowCamera {
  pitch = THREE.MathUtils.degToRad(56);
  yaw = 0;
  distance = 23;
  targetDistance = 23;
  lead = 2.2;
  private pos = new THREE.Vector3();
  private look = new THREE.Vector3();
  private leadX = 0;
  private leadZ = 0;
  trauma = 0;
  private shakeT = 0;
  focusOverride: THREE.Vector3 | null = null;
  overrideBlend = 0;
  private initialised = false;

  constructor(readonly camera: THREE.PerspectiveCamera) {}

  addTrauma(v: number) { this.trauma = clamp(this.trauma + v * shakeScale(), 0, 1); }

  snap(x: number, y: number, z: number) {
    this.look.set(x, y, z);
    this.distance = this.targetDistance;
    this.initialised = true;
    this.place(0);
  }

  update(dt: number, x: number, y: number, z: number, vx: number, vz: number) {
    if (!this.initialised) this.snap(x, y, z);
    this.leadX = damp(this.leadX, vx * this.lead * 0.2, 3, dt);
    this.leadZ = damp(this.leadZ, vz * this.lead * 0.2, 3, dt);
    const tx = x + this.leadX, ty = y + 0.8, tz = z + this.leadZ;
    this.overrideBlend = damp(this.overrideBlend, this.focusOverride ? 1 : 0, 2.5, dt);
    const fx = this.focusOverride ? THREE.MathUtils.lerp(tx, this.focusOverride.x, this.overrideBlend) : tx;
    const fy = this.focusOverride ? THREE.MathUtils.lerp(ty, this.focusOverride.y, this.overrideBlend) : ty;
    const fz = this.focusOverride ? THREE.MathUtils.lerp(tz, this.focusOverride.z, this.overrideBlend) : tz;
    this.look.x = damp(this.look.x, fx, 7, dt);
    this.look.y = damp(this.look.y, fy, 4, dt);
    this.look.z = damp(this.look.z, fz, 7, dt);
    this.distance = damp(this.distance, this.targetDistance, 1.6, dt);
    this.trauma = Math.max(0, this.trauma - dt * 1.4);
    this.shakeT += dt;
    this.place(dt);
  }

  private place(_dt: number) {
    const cp = Math.cos(this.pitch), sp = Math.sin(this.pitch);
    this.pos.set(
      this.look.x + Math.sin(this.yaw) * cp * this.distance,
      this.look.y + sp * this.distance,
      this.look.z + Math.cos(this.yaw) * cp * this.distance,
    );
    const s = this.trauma * this.trauma;
    const t = this.shakeT * 22;
    const n = (a: number) => Math.sin(t * 1.0 + a) * 0.5 + Math.sin(t * 2.3 + a * 1.7) * 0.3 + Math.sin(t * 4.1 + a * 3.1) * 0.2;
    this.camera.position.set(this.pos.x + n(1) * s * 0.7, this.pos.y + n(2) * s * 0.5, this.pos.z + n(3) * s * 0.7);
    this.camera.lookAt(this.look.x + n(4) * s * 0.25, this.look.y, this.look.z + n(5) * s * 0.25);
    this.camera.rotateZ(n(6) * s * 0.025);
  }

  /** Where the camera is looking (for shadows, grass and audio). */
  get focus() { return this.look; }
}
