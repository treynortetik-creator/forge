// Contact sheet of PNG frames on a flat background (review aid).  node sheet.mjs <out.png> <bg> <cell> <perRow> <frames...>   (needs `npm i sharp`; bg is a CSS colour such as '#cdbfa4')
import sharp from 'sharp';
const [out, bg, cellS, perS, ...files] = process.argv.slice(2);
const cell = +cellS, per = Math.min(+perS, files.length);
const tiles = await Promise.all(files.map((f) => sharp(f).flatten({ background: bg }).resize(cell, cell, { fit: 'contain', background: bg }).png().toBuffer()));
const rows = Math.ceil(tiles.length / per);
await sharp({ create: { width: per * cell, height: rows * cell, channels: 3, background: bg } })
  .composite(tiles.map((input, i) => ({ input, left: (i % per) * cell, top: Math.floor(i / per) * cell }))).png().toFile(out);
console.log('wrote', out);
