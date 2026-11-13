/**
 * Pack the voice lines into one audio sprite per speaker (file-count budget: 505 lines x 2 formats were 1,011 files,
 * over a 1,000-file web-host cap).
 *
 *   npx tsx pack-voice.ts [--src audio-src/voice] [--out public/assets/audio/voice] [--bank design/lines.json]
 *   (run from the project root; needs ffmpeg with libopus + aac; voiceChunks.ts must sit beside this file)
 * --bank is optional: a JSON array of { id, trigger } used only to group a big speaker's chunks by scene.
 *
 * Reads <src>/manifest.json (id -> {ogg, m4a, durationMs, speaker}), decodes every line to mono
 * 48 kHz PCM with ffmpeg, joins each speaker's lines with 250 ms of silence, and writes
 * <out>/<speaker>.ogg (Opus 40 kbps) + <out>/<speaker>.m4a (AAC 56 kbps) and <out>/pack.json:
 *   { version: 1, packs: { speaker: { ogg, m4a, ms } }, lines: { id: { speaker, start, dur } } }   (ms)
 * A speaker over 60 s is split into ~40 s chunks (48 s for speakers in NPC_SPEAKERS, see voiceChunks.ts) grouped by trigger (<speaker>-1, <speaker>-2, ...; lines[id].speaker is the pack id).
 *   --encode a,b   only (re)write the audio of these speakers (ffmpeg re-encodes to different bytes; pack.json is always rebuilt)
 * Your runtime plays a line as a marker (start, dur) inside its speaker's pack (lazy: one pack per speaker).
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { baseId, chunkSpeaker, chunkTargetFor, CHUNK_OVER_MS } from './voiceChunks';

const a = process.argv.slice(2);
const arg = (k: string, d: string) => { const i = a.indexOf(`--${k}`); return i >= 0 ? a[i + 1] : d; };
const ROOT = process.cwd();
const SRC = resolve(ROOT, arg('src', 'audio-src/voice'));
const OUT = resolve(ROOT, arg('out', 'public/assets/audio/voice'));
const RATE = 48000, GAP_MS = 250;
const ONLY = arg('encode', '') ? new Set(arg('encode', '').split(',')) : null;
const bankPath = arg('bank', '');
const bank = (bankPath ? JSON.parse(readFileSync(resolve(ROOT, bankPath), 'utf8')) : []) as Array<{ id: string; trigger: string | string[] }>;
const triggerOfBase = new Map(bank.map((l) => [l.id, Array.isArray(l.trigger) ? l.trigger[0] : l.trigger]));

interface Entry { ogg?: string; m4a?: string; durationMs?: number; speaker?: string }
const manifest = JSON.parse(readFileSync(join(SRC, 'manifest.json'), 'utf8')) as Record<string, Entry>;
const bySpeaker = new Map<string, string[]>();
for (const [id, e] of Object.entries(manifest)) {
  if (!e || typeof e !== 'object' || !(e.ogg || e.m4a)) continue;
  const sp = e.speaker ?? 'misc';
  if (!bySpeaker.has(sp)) bySpeaker.set(sp, []);
  bySpeaker.get(sp)!.push(id);
}

const tmp = join(tmpdir(), `cb-voice-${process.pid}`);
mkdirSync(tmp, { recursive: true });
mkdirSync(OUT, { recursive: true });
const pack = { version: 1, packs: {} as Record<string, { ogg: string; m4a: string; ms: number }>, lines: {} as Record<string, { speaker: string; start: number; dur: number }> };
const gap = Buffer.alloc(Math.round((RATE * GAP_MS) / 1000) * 2);

// the PCM of every line is decoded once (durations feed the chunker); encoding happens per pack
const pcmOf = new Map<string, Buffer>();
const pcm = (id: string): Buffer => {
  let b = pcmOf.get(id);
  if (!b) { const e = manifest[id]; b = execFileSync('ffmpeg', ['-v', 'error', '-i', join(SRC, (e.ogg ?? e.m4a)!), '-f', 's16le', '-ac', '1', '-ar', String(RATE), '-'], { maxBuffer: 1 << 28 }); pcmOf.set(id, b); }
  return b;
};
const durOf = (id: string) => Math.round((pcm(id).length / 2 / RATE) * 1000) + GAP_MS;

for (const [sp, ids] of [...bySpeaker.entries()].sort()) {
  const chunks = chunkSpeaker(ids, durOf, (id) => triggerOfBase.get(baseId(id)) ?? '', CHUNK_OVER_MS, chunkTargetFor(sp));
  for (let ci = 0; ci < chunks.length; ci++) {
    const name = chunks.length === 1 ? sp : `${sp}-${ci + 1}`;
    const bufs: Buffer[] = [];
    let samples = 0;
    for (const id of chunks[ci]) {
      const p = pcm(id);
      const n = p.length / 2;
      pack.lines[id] = { speaker: name, start: Math.round((samples * 1000) / RATE), dur: Math.round((n * 1000) / RATE) };
      bufs.push(p, gap);
      samples += n + gap.length / 2;
    }
    if (!ONLY || ONLY.has(sp)) {
      const raw = join(tmp, `${name}.raw`);
      writeFileSync(raw, Buffer.concat(bufs));
      const inArgs = ['-v', 'error', '-y', '-f', 's16le', '-ar', String(RATE), '-ac', '1', '-i', raw];
      execFileSync('ffmpeg', [...inArgs, '-c:a', 'libopus', '-b:a', '40k', join(OUT, `${name}.ogg`)]);
      execFileSync('ffmpeg', [...inArgs, '-c:a', 'aac', '-b:a', '56k', '-movflags', '+faststart', join(OUT, `${name}.m4a`)]);
    }
    pack.packs[name] = { ogg: `${name}.ogg`, m4a: `${name}.m4a`, ms: Math.round((samples * 1000) / RATE) };
    console.log(`${name}: ${chunks[ci].length} lines, ${(pack.packs[name].ms / 1000).toFixed(0)} s`);
  }
  if (chunks.length > 1) for (const ext of ['ogg', 'm4a']) if (existsSync(join(OUT, `${sp}.${ext}`)) && (!ONLY || ONLY.has(sp))) rmSync(join(OUT, `${sp}.${ext}`)); // the old whole-speaker sprite
  pcmOf.clear();
}
writeFileSync(join(OUT, 'pack.json'), JSON.stringify(pack));
// stale chunk files from an earlier split (steward-9 when the speaker now has 7) would ship for nothing and count against the file budget
const keep = new Set(Object.values(pack.packs).flatMap((p) => [p.ogg, p.m4a]));
for (const f of readdirSync(OUT)) if (/\.(ogg|m4a)$/.test(f) && !keep.has(f)) { rmSync(join(OUT, f)); console.log(`removed stale ${f}`); }
rmSync(tmp, { recursive: true, force: true });
console.log(`wrote ${Object.keys(pack.packs).length} packs (${Object.keys(pack.packs).length * 2} audio files) + pack.json for ${Object.keys(pack.lines).length} lines -> ${OUT}`);
