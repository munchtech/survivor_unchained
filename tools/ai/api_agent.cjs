// One short helper (a judge, mostly) run headless on the API credits instead of the
// subscription. The owner, 16 October: "if you can offload any of this to the api
// credits feel free". Same model, same effort; only the bill differs.
//   node tools/ai/api_agent.cjs <brief.md> --out <verdict.md> [--cwd <worktree>]
//        [--effort xhigh] [--usd 6] [--model claude-opus-5-5] [--readonly]
//   node tools/ai/api_agent.cjs status        (what's left of the month's cap)
// The key, the monthly cap and the ledger are Marionette's (one pool of credits):
// C:\Users\munch\Desktop\Marionette\.env.ai, generated/ai/ledger.jsonl. The key goes
// into the child's environment only, under the name bare mode reads, and is never
// printed. Exit code 3 = no room on the cap: spawn the judge as a subagent instead.
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const MAR = 'C:/Users/munch/Desktop/Marionette';
const AI = require(path.join(MAR, 'tools/ai/client.cjs'));
// Dollars left for Marionette's own app calls; none in October 2026 (the owner, 16 October).
const KEEP = new Date().toISOString().startsWith('2026-10') ? 0 : 5;

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i > 0 ? process.argv[i + 1] : dflt;
}
function left() { return AI.CAP - AI.spentThisMonth() - KEEP; }
function key() {
  const t = fs.readFileSync(path.join(MAR, '.env.ai'), 'utf8').match(/^\s*MARIONETTE_API_KEY\s*=\s*["']?([^"'\s]+)/m);
  if (!t) throw new Error('No MARIONETTE_API_KEY in .env.ai.');
  return t[1];
}

async function main() {
  if (process.argv[2] === 'status') {
    console.log(JSON.stringify({ cap: AI.CAP, spent: +AI.spentThisMonth().toFixed(2), usable: +left().toFixed(2) }));
    return 0;
  }
  const briefFile = process.argv[2], out = arg('out');
  if (!briefFile || !out) { console.error('usage: api_agent.cjs <brief.md> --out <file> [--cwd DIR] [--effort xhigh] [--usd 6] [--readonly]'); return 2; }
  if (!AI.available()) { console.error(AI.PAUSED ? 'API credits are paused (Marionette/AI_PAUSED): use a subagent.' : 'No API key in .env.ai.'); return 3; }
  const usd = +arg('usd', 6), model = arg('model', 'claude-opus-5-5'), effort = arg('effort', 'xhigh');
  if (usd > left()) { console.error(`$${usd} asked, $${left().toFixed(2)} usable on the month's cap: use a subagent.`); return 3; }
  const cwd = path.resolve(arg('cwd', process.cwd()));
  const brief = fs.readFileSync(path.resolve(briefFile), 'utf8') +
    `\n\nYou run headless on the API credits with a $${usd} cap: stay lean and end with your full written result as your final message (it is saved to a file for the lead).`;

  // Strip the parent session's variables (its proxy would bill the subscription or fail).
  const env = Object.fromEntries(Object.entries(process.env).filter(([k]) => !/^(ANTHROPIC_|CLAUDE)/i.test(k)));
  env.ANTHROPIC_API_KEY = key();
  const args = ['-p', '--bare', '--model', model, '--effort', effort,
    '--permission-mode', 'bypassPermissions', '--max-budget-usd', String(usd),
    '--output-format', 'stream-json', '--verbose',
    '--append-system-prompt', 'You are a short-lived helper on Survivor Unchained. Do only the job in the brief. Read only what it names. Never print secrets.',
    '--add-dir', cwd];
  if (process.argv.includes('--readonly')) args.push('--disallowedTools', 'Edit,Write,NotebookEdit');
  const exe = path.join(process.env.USERPROFILE || '', '.local', 'bin', 'claude.exe');
  const logFile = out.replace(/\.[^.\\/]+$/, '') + '.api.jsonl';
  const log = fs.createWriteStream(logFile);
  const child = spawn(fs.existsSync(exe) ? exe : 'claude', args, { cwd, env, stdio: ['pipe', 'pipe', 'pipe'] });
  child.stdin.end(brief);
  let result = null, source = null, buf = '';
  child.stdout.on('data', (d) => {
    log.write(d);
    buf += d;
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, i); buf = buf.slice(i + 1);
      try {
        const m = JSON.parse(line);
        if (m.type === 'system' && m.subtype === 'init') {
          source = m.apiKeySource;
          if (source !== 'ANTHROPIC_API_KEY') { console.error('Auth is not the API key (' + source + '): stopping.'); child.kill(); }
        }
        if (m.type === 'result') result = m;
      } catch {}
    }
  });
  child.stderr.on('data', (d) => log.write(d));
  const code = await new Promise((r) => child.on('close', r));
  log.end();
  const cost = result?.total_cost_usd ?? 0;
  fs.appendFileSync(path.join(AI.OUT, 'ledger.jsonl'), JSON.stringify({ at: new Date().toISOString(), label: `survivorsunchained ${path.basename(briefFile)}`, model, batch: false, usage: result?.usage || {}, usd: +cost.toFixed(4) }) + '\n');
  if (result?.result) fs.writeFileSync(out, result.result);
  console.log(JSON.stringify({ out: result?.result ? out : null, log: logFile, code, auth: source, usd: +cost.toFixed(2), turns: result?.num_turns, stop: result?.subtype }));
  return result?.result ? 0 : 1;
}
main().then((c) => process.exit(c), (e) => { console.error(e.message); process.exit(1); });
