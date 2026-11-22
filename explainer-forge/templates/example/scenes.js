/* Example scenes for the explainer engine. Every time comes from the narration (S, E, SC, SE), never a typed number of
   seconds, so re-voicing a line moves its animation with it. Positions are px on the 1920x1080 stage. */
(() => {
  /* scene 1: title, the parcel pops in, a tag says what is wrong */
  const p1 = sprite($('#p1'), 'parcel', 960, 820, 380, { id: 'bigParcel' });
  popIn(p1, S('s1a') + .2);
  fade('#t1', S('s1a'));
  const lost = tagAt($('#p1'), 'bad', 'No lane yet', 960, 400);
  tagPop(lost, S('s1b') + .1, SC(2) - .2);
})();

(() => {
  /* scenes 2 and 3 share a persistent world: belt, scanner, two crates, one token that rides and hops */
  const W = $('#wprops');
  const BY = 760;
  const MAIN = track(`M -60 ${BY} L 1300 ${BY}`);
  const adv = belt(W, [MAIN], { w: 70, rail: '#8E8A86', bed: '#B9B2AB', side: '#6F6B67', img: 'slat', th: 10, sp: 44, speed: 60 });
  UPD.push(adv);
  const scanner = sprite(W, 'scanner', 760, BY - 30, 340, { id: 'scanner' });
  const binA = sprite(W, 'bin-a', 1450, BY + 20, 200, { id: 'binA' });
  const binB = sprite(W, 'bin-b', 1700, BY - 70, 150, { id: 'binB' });
  const T = Tok(W, 'parcel', 1);
  T.ride(MAIN, 0, 640, S('s2a') - .2, E('s2a') - S('s2a') - 1.2);                 // rides to the scanner while the line is read
  T.go(E('s2a') - .5, .9, u => MAIN.at(640 + 90 * u));                              // a short creep past it
  const read = S('s2a') + 2.2;
  tl.to('#scanner', { scaleY: .94, scaleX: 1.04, duration: .1 }, read).to('#scanner', { scaleY: 1, scaleX: 1, duration: .5, ease: 'elastic.out(1,.45)' }, read + .1);
  const lane = tagAt(W, 'info', 'Lane: green', 760, BY - 420);
  tagPop(lane, read + .3, SC(3) - .1);
  worldOn(SC(2), DUR + 1);
  fade('#t2', SC(2) + .1); fade('#t3', SC(3) + .1);
  cam(0, 1, 1.0, 960, 540);
  cam(S('s2a'), 1.2, 1.3, 700, BY - 140);
  cam(S('s3a') - .2, 1.2, 1.2, 1300, BY - 160);
  T.hop([730, BY], [1450, BY - 100], S('s3a') + .3, 1.1, 190);                      // the hop into the crate
  T.key(S('s3a') + 1.4, { s: .0 });                                                  // it settles inside, hidden
  squash(binA, S('s3a') + 1.4);
  const done = tagAt(W, 'ok', 'Sorted', 1450, BY - 290);
  tagPop(done, S('s3a') + 1.5);
  const ok = mark(W, 'ok', 1450, BY - 390, 120);
  popIn(ok, S('s3a') + 1.6, 20);
  capHigh(SC(2), DUR);                                                               // captions clear of the low art
})();
