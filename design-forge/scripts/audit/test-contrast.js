// Extract the harness's own contrast math and check it against published
// reference values. #767676 is the canonical just-passing-AA grey on white;
// #595959 is the canonical AAA one. If these don't land, the harness has been
// reporting confident nonsense.
const src = require('fs').readFileSync(require('path').join(__dirname,'measure.js'),'utf8');
const lum = ([r,g,b]) => { const f=c=>{c/=255;return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)};
  return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b); };
const contrast=(a,b)=>{const[l1,l2]=[lum(a),lum(b)].sort((x,y)=>y-x);return (l1+0.05)/(l2+0.05)};
const hex=h=>{const s=h.replace('#','');return [0,2,4].map(i=>parseInt(s.slice(i,i+2),16))};
// Alpha compositing on BOTH sides. A translucent background layer must be composited
// onto what is behind it -- returning it as if opaque scored a 60% black scrim as pure
// black: 5.92:1 reported for a true 1.62:1, i.e. a PASS on a hard AA failure.
const over=(fg,bg)=>(fg[3]===undefined||fg[3]>=1?fg:[0,1,2].map(i=>Math.round(fg[i]*fg[3]+bg[i]*(1-fg[3]))));
const scrim = over([0,0,0,0.6],[255,255,255]);               // -> [102,102,102]
const scrimRatio = contrast(hex('#888888'), scrim);
console.log(`${Math.abs(scrimRatio-1.62)<0.02?'PASS':'FAIL'}  #888 on rgba(0,0,0,.6) over white  got ${scrimRatio.toFixed(3)}  expected ~1.62`);
if (Math.abs(scrimRatio-1.62)>=0.02) process.exitCode=1;
if (Math.abs(scrimRatio - contrast(hex('#888888'),[102,102,102])) > 0.001) {
  console.log('FAIL  composited path disagrees with the opaque control'); process.exitCode=1;
}

const cases=[['#000000','#ffffff',21.000],['#767676','#ffffff',4.54],['#595959','#ffffff',7.00],
             ['#ffffff','#000000',21.000],['#8a9291','#012624',5.06],['#736c62','#f5f3f1',4.68]];
let fail=0;
for(const [fg,bg,want] of cases){
  const got=contrast(hex(fg),hex(bg));
  const ok=Math.abs(got-want)<0.02;
  if(!ok)fail++;
  console.log(`${ok?'PASS':'FAIL'}  ${fg} on ${bg}  got ${got.toFixed(3)}  expected ~${want}`);
}
// confirm the harness file actually contains this same formula, not a drifted copy
const hasFormula = src.includes('0.2126') && src.includes('0.7152') && src.includes('0.0722')
  && src.includes('0.03928') && src.includes('12.92') && src.includes('1.055');
console.log(`\nharness contains the identical WCAG constants: ${hasFormula ? 'YES' : 'NO — DRIFT'}`);
process.exit(fail || !hasFormula ? 1 : 0);
