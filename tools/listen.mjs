/* Listen to the game without ears: record the master mix for a while and
 * draw it as a waveform over a spectrogram, with loudness numbers.
 *
 *   node tools/listen.mjs "<query>" <name> [seconds] [evalAfterStart]
 *
 * Runs live (real time). Saves .shots/<name>.png and prints peak, RMS per
 * second and how much of it clipped. Expects the dev server on :5173. */
import { chromium } from 'playwright';
import fs from 'node:fs';

const [query = 'quick=warden&auto', name = 'listen', secs = '12', evalAfter = ''] = process.argv.slice(2);
fs.mkdirSync('.shots', { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--autoplay-policy=no-user-gesture-required'],
});
const page = await browser.newPage({ viewport: { width: 320, height: 180 } });
page.on('pageerror', (e) => console.log('[pageerror]', e.message));
page.on('console', (m) => { if (m.type() === 'error') console.log('[error]', m.text().slice(0, 300)); });
await page.goto(`http://localhost:5173/?${query}&quality=low`, { waitUntil: 'load' });
await page.waitForFunction(() => document.body.dataset.ready === '1' || document.body.dataset.error, null, { timeout: 120000 });
await page.mouse.click(5, 5);
await page.waitForTimeout(400);
if (evalAfter) console.log(await page.evaluate(evalAfter));
const out = await page.evaluate(async (seconds) => {
  const A = window.__audio;
  if (!A?.ctx) return { error: 'no audio context' };
  await A.ctx.resume();
  const dest = A.ctx.createMediaStreamDestination();
  A.master.connect(dest);
  const rec = new MediaRecorder(dest.stream);
  const chunks = [];
  rec.ondataavailable = (e) => chunks.push(e.data);
  rec.start();
  await new Promise((r) => setTimeout(r, seconds * 1000));
  rec.stop();
  await new Promise((r) => (rec.onstop = r));
  const buf = await new Blob(chunks).arrayBuffer();
  const dec = await new AudioContext().decodeAudioData(buf);
  const x = dec.getChannelData(0), sr = dec.sampleRate;
  let peak = 0, clip = 0;
  const rms = [];
  for (let s = 0; s < x.length; s += sr) {
    let acc = 0, n = 0;
    for (let i = s; i < Math.min(x.length, s + sr); i++) { const v = x[i]; acc += v * v; n++; const a = Math.abs(v); if (a > peak) peak = a; if (a > 0.98) clip++; }
    rms.push(Math.round(20 * Math.log10(Math.sqrt(acc / Math.max(1, n)) + 1e-9)));
  }
  // Spectrogram: 1024-point FFT, log frequency axis.
  const W = 900, H = 300, N = 1024, hop = Math.max(1, Math.floor((x.length - N) / W));
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H + 80;
  const g = cv.getContext('2d');
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H + 80);
  const re = new Float32Array(N), im = new Float32Array(N);
  const fft = () => {
    for (let i = 1, j = 0; i < N; i++) { let bit = N >> 1; for (; j & bit; bit >>= 1) j ^= bit; j ^= bit; if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
    for (let len = 2; len <= N; len <<= 1) {
      const ang = -2 * Math.PI / len;
      for (let i = 0; i < N; i += len) for (let k = 0; k < len / 2; k++) {
        const wr = Math.cos(ang * k), wi = Math.sin(ang * k);
        const ur = re[i + k], ui = im[i + k];
        const vr = re[i + k + len / 2] * wr - im[i + k + len / 2] * wi, vi = re[i + k + len / 2] * wi + im[i + k + len / 2] * wr;
        re[i + k] = ur + vr; im[i + k] = ui + vi; re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi;
      }
    }
  };
  const img = g.createImageData(W, H);
  for (let c = 0; c < W; c++) {
    const s0 = c * hop;
    for (let i = 0; i < N; i++) { re[i] = (x[s0 + i] ?? 0) * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / N)); im[i] = 0; }
    fft();
    for (let r = 0; r < H; r++) {
      const f = 30 * Math.pow(16000 / 30, 1 - r / H);
      const bin = Math.min(N / 2 - 1, Math.round(f / sr * N));
      const mag = Math.hypot(re[bin], im[bin]);
      const db = 20 * Math.log10(mag / (N / 4) + 1e-9);
      const v = Math.max(0, Math.min(1, (db + 96) / 84));
      const o = (r * W + c) * 4;
      img.data[o] = 255 * Math.min(1, v * 1.8); img.data[o + 1] = 255 * Math.max(0, v * 1.6 - 0.5); img.data[o + 2] = 255 * Math.max(0, v * 2 - 1.2) + 60 * v; img.data[o + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  g.strokeStyle = '#8cf'; g.beginPath();
  for (let c = 0; c < W; c++) {
    let m = 0; for (let i = c * hop; i < (c + 1) * hop && i < x.length; i++) m = Math.max(m, Math.abs(x[i]));
    g.moveTo(c, H + 40 - m * 38); g.lineTo(c, H + 40 + m * 38);
  }
  g.stroke();
  g.fillStyle = '#fff'; g.font = '11px monospace';
  for (const f of [100, 1000, 10000]) { const r = H * (1 - Math.log(f / 30) / Math.log(16000 / 30)); g.fillText(`${f}Hz`, 2, r); }
  return { peak: +peak.toFixed(3), clippedSamples: clip, rmsPerSecond: rms, seconds: +(x.length / sr).toFixed(1), png: cv.toDataURL('image/png') };
}, Number(secs));
if (out.png) { fs.writeFileSync(`.shots/${name}.png`, Buffer.from(out.png.split(',')[1], 'base64')); delete out.png; }
console.log(JSON.stringify(out));
await browser.close();
