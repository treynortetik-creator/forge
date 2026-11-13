"""preview_rooms.py: contact sheet of draft rooms, one coloured square per tile, name burned above each room (labelled proofs).
Usage: python3 preview_rooms.py <dir-of-draft-txt> out.png [id ...]    (needs Pillow; header lines starting "@ " are skipped)"""
import sys, os
from PIL import Image, ImageDraw
COL = {' ': (8, 8, 14), '.': (92, 84, 74), ':': (110, 96, 78), '#': (40, 34, 52), '=': (130, 100, 60), 'P': (0, 0, 0), 'O': (150, 150, 160),
       'o': (180, 120, 70), 'L': (120, 110, 100), 'T': (200, 80, 160), 'n': (80, 200, 200), 'R': (255, 215, 0), 'w': (50, 90, 130), 'W': (20, 40, 80),
       '^': (220, 50, 50), 'v': (230, 130, 60), 'k': (230, 200, 60), 'z': (200, 200, 200), 'S': (255, 60, 60), 'U': (140, 90, 200), 'E': (60, 255, 80),
       '1': (255, 255, 255), '2': (255, 255, 255), '3': (255, 255, 255), 't': (220, 50, 50), 'b': (200, 200, 200), 's': (200, 200, 255), 'a': (100, 220, 80)}
d, out = sys.argv[1], sys.argv[2]
ids = sys.argv[3:]
files = sorted(f for f in os.listdir(d) if f.endswith('.txt') and (not ids or f[:-4] in ids))
rooms = []
for f in files:
    rows = [l.rstrip('\n') for l in open(os.path.join(d, f)) if not l.startswith('@')]
    rooms.append((f[:-4], rows))
S = 12
cols = 2
cw = max(len(r[1][0]) for r in rooms) * S + 20
ch = max(len(r[1]) for r in rooms) * S + 30
rowsn = (len(rooms) + cols - 1) // cols
im = Image.new('RGB', (cols * cw, rowsn * ch), (20, 20, 24))
dr = ImageDraw.Draw(im)
for k, (name, rows) in enumerate(rooms):
    ox, oy = (k % cols) * cw + 10, (k // cols) * ch + 22
    dr.text((ox, oy - 16), name, fill=(255, 255, 255))
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            dr.rectangle([ox + i * S, oy + j * S, ox + i * S + S - 1, oy + j * S + S - 1], fill=COL.get(c, (255, 0, 255)))
im.save(out)
print(im.size)
