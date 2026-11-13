"""example_draft.py: a runnable 30 x 20 room built with roomdraft.py. Run: python3 example_draft.py [outdir]
Writes <outdir>/demo_hall.txt (default ./drafts), prints the report and the room. Then: python3 preview_rooms.py drafts sheet.png"""
import sys
from roomdraft import C, emit, entry, finish, dump

c = C(30, 18)
c.rect(1, 1, 28, 16, '.')                      # open floor
c.rect(12, 6, 6, 5, 'P')                       # a pit in the middle ...
c.rect(14, 3, 2, 2, 'T')                       # ... a landmark footprint (one big set piece) above it
c.tiles([(5, 5), (24, 5), (5, 12), (24, 12)], 'O')       # pillars as cover
c.tiles([(8, 3), (21, 3), (3, 9), (26, 9)], 'o')         # breakable cover
c.tiles([(15, 13)], 'R')                       # reward point: where the drop heads after the clear
c.wallify()                                    # void touching floor becomes wall
entry(c, 15)                                   # E on the bottom row + a 1-wide stem up
c.doors([(1, 8, 0), (2, 21, 0)])               # two doors on the top edge
c.scatter(8, 'S', zone=(3, 2, 26, 12))         # spawns: farthest-point scatter, >= 4.6 tiles from E
c.scatter(3, 'U')                              # urns: only next to something solid
c = finish(c, alcoves=(15,))                   # thicken the north wall; doors sit in 3-wide recesses
out = sys.argv[1] if len(sys.argv) > 1 else 'drafts'
emit({'id': 'demo_hall', 'name': 'Demo Hall', 'archetype': 'broken_hall', 'entry': 'S'}, c, out)
print(c.report('demo_hall'))
dump(c)
