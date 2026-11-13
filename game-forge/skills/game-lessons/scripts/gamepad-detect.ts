/**
 * gamepad-detect.ts - pure gamepad helpers (no DOM). Copied and trimmed from the roguelite's
 * src/input/gamepad.ts, then given its own usage notes. Drop it into src/input/ and unit-test it with
 * stub pads; the browser layer passes navigator.getGamepads() entries in.
 *
 * What it solves:
 *   1. Which button glyphs to show (PlayStation shapes vs Xbox letters vs Deck). Sony pads report
 *      USB vendor 054c, Microsoft 045e, Nintendo 057e, Valve 28de. Chrome puts them in pad.id as
 *      "Vendor: 054c Product: 0ce6", Firefox as "054c-0ce6-...". macOS Chrome/Safari ids can carry no
 *      vendor hex at all, so fall back to names. Order of the name tests matters: a regex that matched
 *      "wireless controller" before "xbox" once gave Xbox pads PlayStation glyphs.
 *   2. Steam Input hands a game a virtual Xbox pad, so on a Steam Deck the pad id cannot tell you
 *      it is a Deck. Use deckHint() (an env flag from your desktop shell, ?deck=1, or the user agent).
 *   3. A radial dead zone with rescale (the square per-axis kind makes diagonals feel bad).
 *
 * Standard-mapping button indices (W3C): 0 Cross/A, 1 Circle/B, 2 Square/X, 3 Triangle/Y, 4 L1, 5 R1,
 * 6 L2, 7 R2, 8 Create/Back, 9 Options/Start, 10 L3, 11 R3, 12-15 d-pad, 16 PS/Home, 17 Touchpad.
 * Safari has no touchpad button, so bind your map/menu action to Touchpad (17) AND Create (8).
 *
 * Settings override: always offer "Button prompts: Auto / PlayStation / Xbox / Keyboard". Steam Input
 * can disguise a DualSense, and auto-detect will be wrong for somebody.
 */

export type PadFamily = 'ps' | 'xbox' | 'deck' | 'nintendo' | 'generic';
const SONY = 0x054c, MSFT = 0x045e, NINTENDO = 0x057e, VALVE = 0x28de;

/** Vendor/product from Chrome ("Vendor: 054c Product: 0ce6") or Firefox ("054c-0ce6-" / "54c-ce6-"). */
export function parsePadIds(id: string): { v: number; p: number } | null {
  const m = /Vendor:\s*([0-9a-f]{1,4})\s+Product:\s*([0-9a-f]{1,4})/i.exec(id) ?? /^([0-9a-f]{1,4})-([0-9a-f]{1,4})-/i.exec(id);
  return m ? { v: parseInt(m[1], 16), p: parseInt(m[2], 16) } : null;
}

/** Vendor id first, then names. */
export function detectPadFamily(id: string): PadFamily {
  const ids = parsePadIds(id);
  if (ids?.v === SONY) return 'ps';
  if (ids?.v === MSFT) return 'xbox';
  if (ids?.v === NINTENDO) return 'nintendo';
  if (ids?.v === VALVE) return 'deck'; // Deck controller, Steam Controller, Steam Virtual Gamepad
  if (/steam deck|steamdeck|steam virtual|valve|neptune/i.test(id)) return 'deck';
  if (/xbox|xinput/i.test(id)) return 'xbox'; // must come BEFORE the bare "wireless controller" test
  if (/dualsense|dualshock|playstation|\bps[345]\b/i.test(id)) return 'ps';
  if (/^\s*wireless controller\b/i.test(id)) return 'ps'; // a DualShock 4 reports a bare "Wireless Controller"
  if (/pro controller|joy-?con|nintendo/i.test(id)) return 'nintendo';
  return 'generic';
}

/** Is this machine a Steam Deck? Pass whatever hints your shell can supply. */
export function deckHint(h: { desktopDeck?: boolean; search?: string; ua?: string } = {}): boolean {
  return !!h.desktopDeck || /[?&]deck=1\b/.test(h.search ?? '') || /steam ?deck/i.test(h.ua ?? '');
}

/** Glyph family to draw: PS for Sony pads (even plugged into a Deck), Deck glyphs on a Deck, Xbox for the rest. */
export function detectFamily(id: string, onDeck = false): 'ps' | 'xbox' | 'deck' {
  const f = detectPadFamily(id);
  if (f === 'ps') return 'ps';
  if (f === 'deck') return 'deck';
  return onDeck ? 'deck' : 'xbox'; // XInput layout is what nearly every unknown pad copies
}

/** Defaults we shipped: left stick inner 0.15 / outer 0.95; right stick inner 0.25 / outer 0.95. */
export const STICK_DEADZONE = 0.15;
export const AIM_DEADZONE = 0.25;
export const STICK_OUTER = 0.95;
export const TRIGGER_THRESHOLD = 0.35; // analog triggers report .value, not always .pressed

/** Radial dead zone with rescale: no drift inside dz, full range outside, length clamped to 1. */
export function radialDeadzone(x: number, y: number, dz = STICK_DEADZONE, outer = STICK_OUTER): [number, number] {
  const l = Math.hypot(x, y);
  if (l < dz) return [0, 0];
  const s = Math.min(1, (l - dz) / (outer - dz)) / l;
  return [x * s, y * s];
}
