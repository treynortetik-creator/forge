#!/usr/bin/env bash
# design-forge installer.
#
# Installs the plugin, then optionally the toolchain the heavier skills want.
# Nothing here is silent: every install is announced, and the optional group is
# opt-in because it pulls ~1GB of Homebrew formulae you may not need.
#
#   ./scripts/install.sh              plugin only  (works on python3 + a browser)
#   ./scripts/install.sh --tools      plugin + visual toolchain via Homebrew
#   ./scripts/install.sh --all        the above + generation CLIs
#   ./scripts/install.sh --check      change nothing, just report

set -uo pipefail
# NOTE: deliberately NOT `set -e` (we want to report every check), so every install
# step below must test its own exit status. It previously did not, and sailed past two
# hard failures to print "Done."
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOLD=$'\033[1m'; DIM=$'\033[2m'; GRN=$'\033[32m'; YLW=$'\033[33m'; RST=$'\033[0m'
MODE="${1:---plugin}"
have() { command -v "$1" >/dev/null 2>&1; }
say()  { printf "${BOLD}%s${RST}\n" "$*"; }
note() { printf "${DIM}  %s${RST}\n" "$*"; }

if [ "$MODE" = "--check" ]; then exec bash "$ROOT/scripts/doctor.sh"; fi

say "design-forge installer"
note "plugin root: $ROOT"
echo

# ── 1. Hard requirements ────────────────────────────────────────────────
say "1. Checking requirements"
if ! have python3; then
  echo "  python3 is required and missing. Install it, then re-run." >&2; exit 1
fi
note "python3 $(python3 -V 2>&1 | cut -d' ' -f2)"
have claude || { echo "  'claude' CLI not on PATH. Install Claude Code first." >&2; exit 1; }
note "claude CLI present"

# ── 2. Make the bundled scripts executable ──────────────────────────────
say "2. Marking scripts executable"
find "$ROOT" -name "*.sh" -exec chmod +x {} \; 2>/dev/null
find "$ROOT" \( -name "*.py" -o -name "*.js" \) -exec chmod +x {} \; 2>/dev/null
note "done  (a missing executable bit is the classic silent plugin failure)"

# ── 3. Validate before installing ───────────────────────────────────────
say "3. Validating the manifest"
if claude plugin validate "$ROOT" 2>&1 | tee /tmp/df-validate.log | grep -qi "passed"; then
  note "validation passed"
else
  echo "  Validation FAILED:"; sed 's/^/    /' /tmp/df-validate.log; exit 1
fi

# ── 4. Register + install ───────────────────────────────────────────────
say "4. Installing the plugin"

# The marketplace manifest lives in the REPO ROOT, not in the plugin dir — this
# plugin is one of several the marketplace hosts. Pointing `marketplace add` at the
# plugin dir fails with "Marketplace file not found", and the marketplace is named
# after the repo, not the plugin.
MARKET_DIR="$ROOT"
[ -f "$ROOT/../.claude-plugin/marketplace.json" ] && MARKET_DIR="$(cd "$ROOT/.." && pwd)"
MARKET_NAME=$(python3 -c "import json,sys;print(json.load(open('$MARKET_DIR/.claude-plugin/marketplace.json'))['name'])" 2>/dev/null)
PLUGIN_NAME=$(python3 -c "import json;print(json.load(open('$ROOT/.claude-plugin/plugin.json'))['name'])" 2>/dev/null)

if [ -z "$MARKET_NAME" ] || [ -z "$PLUGIN_NAME" ]; then
  echo "  Could not read the manifests. Expected:" >&2
  echo "    $MARKET_DIR/.claude-plugin/marketplace.json" >&2
  echo "    $ROOT/.claude-plugin/plugin.json" >&2
  exit 1
fi
note "marketplace '$MARKET_NAME' at $MARKET_DIR · plugin '$PLUGIN_NAME'"

if claude plugin marketplace list 2>/dev/null | grep -q "$MARKET_NAME"; then
  note "marketplace already registered, updating"
  claude plugin marketplace update "$MARKET_NAME" >/dev/null 2>&1 || true
else
  if claude plugin marketplace add "$MARKET_DIR"; then note "marketplace added"
  else echo "  FAILED to add the marketplace. Nothing installed." >&2; exit 1; fi
fi

if claude plugin list 2>/dev/null | grep -q "$PLUGIN_NAME"; then
  note "already installed — 'claude plugin update $PLUGIN_NAME@$MARKET_NAME' to refresh"
else
  if claude plugin install "$PLUGIN_NAME@$MARKET_NAME"; then note "installed"
  else echo "  FAILED to install $PLUGIN_NAME@$MARKET_NAME." >&2; exit 1; fi
fi
note "restart the session (or /clear) for the skills to load"

# ── 5. Optional toolchain ───────────────────────────────────────────────
if [ "$MODE" = "--tools" ] || [ "$MODE" = "--all" ]; then
  say "5. Visual toolchain"
  if ! have brew; then
    note "Homebrew not found — skipping. https://brew.sh"
  else
    for f in imagemagick inkscape graphviz ffmpeg duckdb; do
      if brew list "$f" >/dev/null 2>&1; then note "$f already installed"
      else printf "  installing %s...\n" "$f"; brew install "$f" >/dev/null 2>&1 \
           && note "$f ok" || note "${YLW}$f failed — install manually${RST}"; fi
    done
    note "ImageMagick 7 has no bare 'convert'. The command is 'magick'."
  fi
else
  say "5. Visual toolchain ${DIM}(skipped — pass --tools)${RST}"
  note "art-department degrades gracefully without these, it just cannot"
  note "render vectors, diagrams or video."
fi

# ── 6. Generation CLIs ──────────────────────────────────────────────────
if [ "$MODE" = "--all" ]; then
  say "6. Generation CLIs (optional media generation)"
  if have higgsfield; then note "Higgsfield CLI present"
  else
    printf "  installing Higgsfield CLI...\n"
    curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh \
      && note "installed — run 'higgsfield auth login' yourself (interactive)" \
      || note "${YLW}failed — install manually${RST}"
  fi
  have codex && note "Codex CLI present" || note "Codex CLI absent — 'npm i -g @openai/codex', then 'codex login'"
  [ -n "${OPENROUTER_API_KEY:-}" ] && note "OPENROUTER_API_KEY set" \
    || note "OPENROUTER_API_KEY unset — add it to your project .env for image/video"
else
  say "6. Generation CLIs ${DIM}(skipped — pass --all)${RST}"
fi

echo
say "Done."
note "Verify with:  ./scripts/doctor.sh"
note "Then try:     /design-audit   or   /design-loop"
echo
printf "${GRN}Skills installed:${RST} "
ls "$ROOT/skills" | tr '\n' ' '; echo; echo
