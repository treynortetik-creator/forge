#!/usr/bin/env bash
# design-forge doctor — what works right now, and what each gap actually costs you.
#
# Exits 0 always. This is a report, not a gate: most of design-forge runs on
# nothing but python3 and a browser, and a missing optional tool should never
# stop you from using the parts that work.
set -uo pipefail

BOLD=$'\033[1m'; DIM=$'\033[2m'; GRN=$'\033[32m'; YLW=$'\033[33m'; RED=$'\033[31m'; RST=$'\033[0m'
ok=0; warn=0; miss=0

have() { command -v "$1" >/dev/null 2>&1; }
row() { # name | status | detail
  case "$2" in
    ok)   printf "  ${GRN}✔${RST} %-22s %s\n" "$1" "${DIM}$3${RST}"; ok=$((ok+1)) ;;
    opt)  printf "  ${YLW}○${RST} %-22s %s\n" "$1" "$3"; warn=$((warn+1)) ;;
    no)   printf "  ${RED}✘${RST} %-22s %s\n" "$1" "$3"; miss=$((miss+1)) ;;
  esac
}
check() { # binary, label, required|optional, what-it-unlocks, version-cmd
  if have "$1"; then
    local v; v=$(eval "${5:-$1 --version}" 2>&1 | head -1 | cut -c1-42)
    row "$2" ok "$v"
  elif [ "$3" = "required" ]; then row "$2" no "MISSING — $4"
  else row "$2" opt "not installed — $4"; fi
}

echo
echo "${BOLD}design-forge doctor${RST}"
echo "${DIM}$(date '+%Y-%m-%d %H:%M')${RST}"
echo
echo "${BOLD}Core${RST} ${DIM}(design-loop, design-audit, de-sloppifier, clean-export, voice)${RST}"
check python3 "python3"      required "serving pages, chunking prose, clean-export"
check node    "node"         optional "syntax-checking the audit harness; scroll-film scripts"
check git     "git"          optional "versioning your design work"

echo
echo "${BOLD}Rendering${RST} ${DIM}(the craft critic goes blind without one of these)${RST}"
if [ -d "$HOME/Library/Application Support/Google/Chrome" ] || have google-chrome || have chromium; then
  row "Chrome" ok "present — pair the claude-in-chrome extension"
else
  row "Chrome" no "MISSING — no screenshots, no measurement, no craft critic"
fi
printf "  ${DIM}note: file:// is blocked for scripted eval. Serve with: python3 -m http.server 8899${RST}\n"

echo
echo "${BOLD}Visual toolchain${RST} ${DIM}(art-department)${RST}"
check magick   "ImageMagick"  optional "resize/pad/composite. ImageMagick 7 has no bare 'convert'"
check inkscape "Inkscape"     optional "real SVG work, PDF→vector, --query-all geometry"
check dot      "Graphviz"     optional "generated diagrams" "dot -V"
check ffmpeg   "ffmpeg"       optional "video assembly, filmstrips, poster frames" "ffmpeg -version"
check duckdb   "DuckDB"       optional "query CSV/XLSX/Parquet in place"
check soffice  "LibreOffice"  optional "headless document conversion" "soffice --version"
if [ -d "/Applications/Blender.app" ] || have blender; then
  row "Blender" ok "present — 3D stills/animation via MCP"
else
  row "Blender" opt "not installed — no 3D. CSS approximations instead"
fi

echo
echo "${BOLD}Generation${RST} ${DIM}(optional — every one of these costs money or an account)${RST}"
check higgsfield "Higgsfield CLI" optional "the generated-film lane in scroll-film-studio"
check codex      "Codex CLI"      optional "image generation on a ChatGPT plan"
# Keys normally live in a project .env rather than the exported environment.
for envf in "$PWD/.env" "$(dirname "${BASH_SOURCE[0]}")/../../.env"; do
  [ -f "$envf" ] && [ -z "${OPENROUTER_API_KEY:-}" ] && \
    OPENROUTER_API_KEY=$(grep -m1 '^OPENROUTER_API_KEY=' "$envf" 2>/dev/null | cut -d= -f2- | tr -d '"'"'"'" ')
done
if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  row "OPENROUTER_API_KEY" ok "found — image + video models"
else
  row "OPENROUTER_API_KEY" opt "not found in env or .env — no OpenRouter image/video"
fi
printf "  ${DIM}video lives on a SEPARATE async API: GET /api/v1/videos/models,${RST}\n"
printf "  ${DIM}not /api/v1/models. Grepping the model list 'proves' a false absence.${RST}\n"

echo
echo "${BOLD}Asset library${RST}"
LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skills/art-department/library"
if [ -f "$LIB/manifest.json" ]; then
  n=$(python3 -c "import json;print(len(json.load(open('$LIB/manifest.json'))['entries']))" 2>/dev/null || echo "?")
  row "manifest.json" ok "$n assets, every one licence-verified"
  for d in icons fonts textures ornament; do
    [ -d "$LIB/$d" ] && printf "  ${DIM}    %-10s %s${RST}\n" "$d" "$(du -sh "$LIB/$d" 2>/dev/null | cut -f1)"
  done
else
  row "asset library" no "manifest.json missing — run library/fetch.py"
fi

echo
echo "${BOLD}Summary${RST}  ${GRN}$ok ready${RST} · ${YLW}$warn optional gaps${RST} · ${RED}$miss blocking${RST}"
if [ "$miss" -eq 0 ]; then
  echo "${DIM}Everything required is present. Optional gaps only limit specific skills.${RST}"
else
  echo "${DIM}Run ./scripts/install.sh to fix what Homebrew can fix.${RST}"
fi
echo
