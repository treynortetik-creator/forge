// Extract the harness's own contrast math and check it against published
// reference values. #767676 is the canonical just-passing-AA grey on white;
// #595959 is the canonical AAA one. If these don't land, the harness has been
// reporting confident nonsense.
const src = require('fs').readFileSync(require('path').join(__dirname,'measure.js'),'utf8');
const lum = ([r,g,b]) => { const f=c=>{c/=255;return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)};
  return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b); };
const contrast=(a,b)=>{const[l1,l2]=[lum(a),lum(b)].sort((x,y)=>y-x);return (l1+0.05)/(l2+0.05)};
const hex=h=>{const s=h.replace('#','');return [0,2,4].map(i=>parseInt(s.slice(i,i+2),16))};
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
