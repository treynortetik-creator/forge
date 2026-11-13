/**
 * Split a big speaker's voice pack into ~40 s chunks (48 s for speakers listed in NPC_SPEAKERS), grouped by trigger so one scene (a hub conversation, a boss
 * intro) loads one small chunk instead of a whole 5-minute speaker sprite. Pure; pack-voice.ts calls it.
 */
export const CHUNK_OVER_MS = 60_000;
export const CHUNK_TARGET_MS = 40_000;
/** speakers who talk one scene at a time (hub NPCs), so their chunks run longer (fewer files: some web hosts cap a build's file count and each pack is 2 files) */
export const NPC_CHUNK_TARGET_MS = 48_000;
export const NPC_SPEAKERS: string[] = []; // put your one-scene-at-a-time NPC speaker ids here
export const chunkTargetFor = (speaker: string): number => (NPC_SPEAKERS.includes(speaker) ? NPC_CHUNK_TARGET_MS : CHUNK_TARGET_MS);

/** two-speaker lines arrive as <id>_a / <id>_b; the bank knows the plain id */
export const baseId = (id: string): string => id.replace(/_[abc]$/, '');

/**
 * ids -> chunks of consecutive trigger groups. A trigger group is never split across chunks; a chunk closes once it holds
 * >= targetMs. Speakers under `overMs` total stay one pack (returns a single chunk). Deterministic: sorted by trigger, then id.
 */
export function chunkSpeaker(ids: string[], durOf: (id: string) => number, triggerOf: (id: string) => string, overMs = CHUNK_OVER_MS, targetMs = CHUNK_TARGET_MS): string[][] {
  const total = ids.reduce((t, i) => t + durOf(i), 0);
  if (total <= overMs) return [[...ids].sort()];
  const groups = new Map<string, string[]>();
  for (const id of [...ids].sort()) {
    const t = triggerOf(id) || '~misc';
    if (!groups.has(t)) groups.set(t, []);
    groups.get(t)!.push(id);
  }
  const out: string[][] = [];
  let cur: string[] = [], curMs = 0;
  const flush = () => { if (cur.length) out.push(cur); cur = []; curMs = 0; };
  for (const t of [...groups.keys()].sort()) {
    const g = groups.get(t)!;
    const gMs = g.reduce((s, i) => s + durOf(i), 0);
    if (gMs < targetMs) { // a small group stays whole: flush first when it would overshoot the chunk by half a target
      if (curMs > 0 && curMs + gMs > targetMs * 1.5) flush();
      cur.push(...g); curMs += gMs;
      if (curMs >= targetMs) flush();
    } else { // a big group is cut into target-sized runs
      for (const id of g) { cur.push(id); curMs += durOf(id); if (curMs >= targetMs) flush(); }
    }
  }
  if (cur.length) { if (out.length && curMs < targetMs / 3) out[out.length - 1].push(...cur); else out.push(cur); }
  return out;
}
