/* Example scenes for templates/stage.html. Every time comes from the narration (T, E, W), never a typed number of
   seconds, so a re-voiced line moves its animation with it. Every footage coordinate is in the clip's own 1920x1080
   pixels, MEASURED on the actual frame (open the frame, read the box), never estimated. */
(() => {
  const ids = CUES.lines.map(l => l.id);
  const first = ids[0], second = ids[1] || ids[0];
  scene('s1', 0, T(second) - 0.6);
  tl.set('#h1', { y: 30 }, 0);
  show('#h1', T(first) + 0.2);
})();
(() => {
  const a = T(CUES.lines[1] ? CUES.lines[1].id : CUES.lines[0].id) - 0.4;
  scene('s2', a, null);
  footage(a, CUES.total);
  // V('#fs2 video', a, 0, 12);                 // clip seconds 0-12 play from timeline time a
  // sped(a + 4, a + 7);                         // a time-lapsed wait inside that span
  ring('#r2a', 900, 420, 320, 90, a + 1.0, a + 3.0);   // replace with a measured box and spoken-word times
})();
