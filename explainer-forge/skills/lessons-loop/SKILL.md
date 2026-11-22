---
name: lessons-loop
description: >
  After an explainer video ships (or is killed), turn what happened into rules the next video starts with: collect
  owner notes, reviewer findings and surprises into one retro file, sort each into keep / rule / number / trap, check it
  against the existing rules, and put it in the right place (public plugin, private overlay, or project only). Use when
  a cut is approved, when the owner gives a batch of notes, at the end of any video project, or when someone says
  "retro", "lessons", "what did we learn", "add that to the rules", "don't make that mistake again".
---

# Lessons loop

Each video should start where the last one ended. A retro takes about 15 minutes and is part of the job, not an extra.

## 1. Collect (while it is fresh)

Fill `retro.md` in the project folder (from `${CLAUDE_PLUGIN_ROOT}/skills/lessons-loop/retro-template.md`;
`new_project.py` puts a copy there at the start, so add lines as they happen). Sources: `owner-notes.md`, reviewer
findings, the run log, and the diff between cuts. Measured numbers beat adjectives.

## 2. Sort each line

| It is | Put it in |
|---|---|
| an owner note that applies to every video | a rule in `skills/house-style/rules.md` (paraphrase, one-line why) |
| an owner note about this video only | stays in the project's `retro.md` |
| a number we measured (pace, size, time, cost) | the profile or the method file that uses it, with the run it came from |
| a trap that could catch anyone | `references/lessons.md`, next free number |
| a change to how a script works | an issue or a change to the script, with a test |
| brand, people, customer, employer, ticket, price, account | the private overlay's `lessons.md`, never the plugin |

Public rules are paraphrased. No quoted messages, no names, no employer, no customer, no ticket, no path.

## 3. Check for a conflict first

Search `rules.md` for the topic. If the new note disagrees with a rule:

1. The newest note on an approved cut wins.
2. Move the old rule to **Superseded** in the same edit, with what replaced it.
3. If the new note was about one video, say so and mark it *(generalised)* or leave it in the retro.
4. Never keep both. If you can't tell which wins, ask the owner one question.

Rules we invented (not owner notes) are the first to go when an owner note disagrees.

## 4. Prove it landed

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/new_project.py --check-rules
grep -rniE -f <overlay>/public-terms.txt ${CLAUDE_PLUGIN_ROOT}   # no hits before a public push
```

`--check-rules` fails on a rule with no reason, a duplicate number, or a number in the Superseded list that is missing.
Then run `claude plugin validate` on the plugin, commit, and say which rules changed. Edit the plugin's source repo, not
the installed copy: an update overwrites that.

## 5. Say what changed

One message to the owner: rules added, rules retired, numbers updated, what stayed project-only. No essay.
