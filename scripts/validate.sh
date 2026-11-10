#!/usr/bin/env bash
# validate.sh — structural checks for the forge marketplace.
#
#   scripts/validate.sh            structure, frontmatter, references, hygiene, syntax
#   scripts/validate.sh --smoke    the above + run `--help` on every Python CLI
#   scripts/validate.sh --help
#
# Checks:
#   1. .claude-plugin/marketplace.json parses; each plugin entry has name + source,
#      the source dir has .claude-plugin/plugin.json, and the names agree.
#   2. Every plugin.json parses, has a kebab-case name and (if present) a semver version.
#   3. Every skills/*/SKILL.md has frontmatter with name == directory name
#      (lowercase, hyphens, <= 64 chars) and a description of 1..1024 chars.
#      Every commands/*.md has a description.
#   4. Every ${CLAUDE_PLUGIN_ROOT}/path in a tracked text file resolves inside its plugin.
#   5. No hard-coded user paths (/Users/<name>, /home/<name>, C:\Users) and no
#      obvious secrets (API key / token / private key patterns) in tracked files.
#   6. Every JSON file parses; every .py compiles; every .sh passes `bash -n`
#      (or `zsh -n` for #!/bin/zsh scripts when zsh is installed); every .js passes
#      `node --check` when node is installed.
#
# Needs python3 (stdlib only; uses PyYAML for frontmatter when available).
# Exit status: 0 when every check passes, 1 otherwise. Warnings do not fail.
set -uo pipefail

SMOKE=0
case "${1:-}" in
  "") ;;
  --smoke) SMOKE=1 ;;
  -h|--help) sed -n '2,21p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "unknown option: $1 (use --smoke or --help)" >&2; exit 2 ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

SMOKE="$SMOKE" python3 -I - <<'PY'
import glob, json, os, py_compile, re, shutil, subprocess, sys, tempfile

fails, warns = [], []
def fail(msg): fails.append(msg)
def warn(msg): warns.append(msg)

def tracked():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
        return [p for p in out.decode().split("\0") if p and os.path.isfile(p)]
    except Exception:
        return [os.path.relpath(os.path.join(d, f)) for d, _, fs in os.walk(".")
                if "/.git" not in d and "node_modules" not in d for f in fs]
FILES = tracked()
TEXT_EXT = (".md", ".json", ".py", ".sh", ".js", ".txt", ".toml", ".yml", ".yaml")
TEXT = [f for f in FILES if f.endswith(TEXT_EXT) and "package-lock.json" not in f]

def load_json(path):
    try:
        with open(path) as fh: return json.load(fh)
    except Exception as e:
        fail(f"{path}: invalid JSON ({e})"); return None

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

# ── 1. marketplace ────────────────────────────────────────────────────────
mp_path = ".claude-plugin/marketplace.json"
plugins = {}
mp = load_json(mp_path) if os.path.exists(mp_path) else fail(f"{mp_path}: missing")
if mp:
    for key in ("name", "owner", "plugins"):
        if key not in mp: fail(f"{mp_path}: missing '{key}'")
    seen = set()
    for i, e in enumerate(mp.get("plugins", [])):
        name, src = e.get("name"), e.get("source")
        if not name or not src:
            fail(f"{mp_path}: plugins[{i}] needs name and source"); continue
        if name in seen: fail(f"{mp_path}: duplicate plugin '{name}'")
        seen.add(name)
        if not isinstance(src, str):
            warn(f"{mp_path}: {name}: non-path source not checked"); continue
        d = os.path.normpath(src)
        if not os.path.isfile(os.path.join(d, ".claude-plugin/plugin.json")):
            fail(f"{mp_path}: {name}: {src} has no .claude-plugin/plugin.json"); continue
        plugins[d] = name
    for pj in glob.glob("*/.claude-plugin/plugin.json"):
        d = pj.split("/")[0]
        if d not in plugins: warn(f"{pj}: plugin not listed in marketplace.json")

# ── 2. plugin.json ────────────────────────────────────────────────────────
for d, mname in plugins.items():
    pj = os.path.join(d, ".claude-plugin/plugin.json")
    data = load_json(pj)
    if not data: continue
    n = data.get("name")
    if not n or not KEBAB.match(n): fail(f"{pj}: name '{n}' is not kebab-case")
    elif n != mname: fail(f"{pj}: name '{n}' != marketplace name '{mname}'")
    v = data.get("version")
    if v is not None and not SEMVER.match(str(v)): fail(f"{pj}: version '{v}' is not semver")
    if not data.get("description"): warn(f"{pj}: no description")

# ── 3. frontmatter ────────────────────────────────────────────────────────
try:
    import yaml
    def parse_fm(text): return yaml.safe_load(text)
except ImportError:
    def parse_fm(text):  # minimal: key: value, quoted scalars, >/|/>- blocks
        out, key, block = {}, None, None
        for line in text.splitlines():
            if block is not None and (line.startswith((" ", "\t")) or not line.strip()):
                block.append(line.strip()); out[key] = " ".join(x for x in block if x); continue
            block = None
            m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if not m: continue
            key, val = m.groups()
            if val in (">", ">-", "|", "|-", ">+", "|+"): block = []; out[key] = ""; continue
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1].replace('\\"', '"')
            out[key] = val
        return out

def frontmatter(path):
    with open(path, encoding="utf-8") as fh: s = fh.read()
    if not s.startswith("---\n"): return None, "no frontmatter"
    end = s.find("\n---", 4)
    if end < 0: return None, "unterminated frontmatter"
    try:
        d = parse_fm(s[4:end])
    except Exception as e:
        return None, f"frontmatter does not parse ({e})"
    return (d if isinstance(d, dict) else None), "frontmatter is not a mapping"

for d in plugins:
    skill_files = sorted(glob.glob(f"{d}/skills/*/SKILL.md"))
    for sd in sorted(glob.glob(f"{d}/skills/*/")):
        if not os.path.isfile(os.path.join(sd, "SKILL.md")): fail(f"{sd}: no SKILL.md")
    for f in skill_files:
        fm, err = frontmatter(f)
        if fm is None: fail(f"{f}: {err}"); continue
        dirname = os.path.basename(os.path.dirname(f))
        name, desc = fm.get("name"), fm.get("description")
        if name != dirname: fail(f"{f}: name '{name}' != directory '{dirname}'")
        if not name or not KEBAB.match(str(name)) or len(str(name)) > 64:
            fail(f"{f}: name must be lowercase-hyphenated, <= 64 chars")
        if not desc or not str(desc).strip(): fail(f"{f}: missing description")
        elif len(str(desc)) > 1024: fail(f"{f}: description is {len(str(desc))} chars (max 1024)")
        elif len(str(desc)) < 40: warn(f"{f}: description is very short ({len(str(desc))} chars)")
    for f in sorted(glob.glob(f"{d}/commands/*.md")):
        fm, err = frontmatter(f)
        if fm is None: fail(f"{f}: {err}"); continue
        if not fm.get("description"): fail(f"{f}: missing description")

# ── 4. ${CLAUDE_PLUGIN_ROOT} references ──────────────────────────────────
REF = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?/([A-Za-z0-9_./-]+)")
for f in TEXT:
    d = f.split("/")[0]
    if d not in plugins: continue
    with open(f, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            for m in REF.finditer(line):
                r = m.group(1).rstrip(".,;:)`'\"")
                if not r or "*" in r: continue
                if not os.path.exists(os.path.join(d, r)):
                    fail(f"{f}:{i}: ${{CLAUDE_PLUGIN_ROOT}}/{r} does not exist")

# ── 5. hygiene ────────────────────────────────────────────────────────────
USERPATH = re.compile(r"(/Users/[A-Za-z][\w.-]+|/home/[a-z][\w.-]+/|C:\\\\?Users\\\\?[A-Za-z])")
SECRET = re.compile(
    r"(sk-ant-[A-Za-z0-9_-]{20,}|sk-or-v1-[0-9a-f]{20,}|sk-[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}"
    r"|gh[pousr]_[A-Za-z0-9]{30,}|xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?:api[_-]?key|secret|token|password)\s*[=:]\s*['\"][A-Za-z0-9_\-]{20,}['\"])", re.I)
ALLOW_USERPATH = ("/Users/you", "/Users/<", "/Users/me/", "/home/you", "/home/<")
for f in TEXT:
    if f.startswith("scripts/validate.sh"): continue
    with open(f, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            m = USERPATH.search(line)
            if m and not any(a in line for a in ALLOW_USERPATH):
                fail(f"{f}:{i}: hard-coded user path {m.group(0)!r}")
            if SECRET.search(line):
                fail(f"{f}:{i}: looks like a secret")

# ── 6. syntax ─────────────────────────────────────────────────────────────
for f in FILES:
    if f.endswith(".json") and f not in (mp_path,) and not f.endswith("plugin.json"):
        load_json(f)
tmp = tempfile.mkdtemp()
for f in (f for f in FILES if f.endswith(".py")):
    try: py_compile.compile(f, cfile=os.path.join(tmp, "x.pyc"), doraise=True)
    except py_compile.PyCompileError as e: fail(f"{f}: does not compile: {e.msg.strip().splitlines()[-1]}")
shutil.rmtree(tmp, ignore_errors=True)

have_zsh, have_node = shutil.which("zsh"), shutil.which("node")
for f in (f for f in FILES if f.endswith(".sh")):
    with open(f) as fh: first = fh.readline()
    shell = "zsh" if "zsh" in first else "bash"
    if shell == "zsh" and not have_zsh:
        warn(f"{f}: zsh script, zsh not installed, syntax not checked"); continue
    r = subprocess.run([shell, "-n", f], capture_output=True, text=True)
    if r.returncode: fail(f"{f}: {shell} -n: {r.stderr.strip().splitlines()[0] if r.stderr else 'error'}")
for f in (f for f in FILES if f.endswith(".js")):
    if not have_node: warn("node not installed, .js syntax not checked"); break
    r = subprocess.run(["node", "--check", f], capture_output=True, text=True)
    if r.returncode: fail(f"{f}: node --check failed")

# ── smoke: --help on every Python CLI ─────────────────────────────────────
if os.environ.get("SMOKE") == "1":
    for f in (f for f in FILES if f.endswith(".py") and "/test_" not in f
              and not os.path.basename(f).startswith("test_")):
        with open(f, encoding="utf-8") as fh: src = fh.read()
        if "__main__" not in src: continue
        try:
            r = subprocess.run([sys.executable, f, "--help"], capture_output=True, text=True,
                               timeout=30, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            fail(f"{f}: --help timed out"); continue
        out = (r.stdout + r.stderr)
        if r.returncode == 0: continue
        if re.search(r"No module named|needs (the )?`?[\w-]+`? package|needs [\w-]+\.|pip3? install|uv run --with", out):
            warn(f"{f}: --help needs an optional dependency ({out.strip().splitlines()[-1][:80]})")
        elif "Traceback" in out:
            fail(f"{f}: --help crashed: {out.strip().splitlines()[-1][:120]}")
        else:
            warn(f"{f}: --help exited {r.returncode}: {out.strip().splitlines()[0][:80] if out.strip() else ''}")

for w in warns: print(f"  warn  {w}")
for e in fails: print(f"  FAIL  {e}")
print(f"\n{len(plugins)} plugins, "
      f"{sum(len(glob.glob(f'{d}/skills/*/SKILL.md')) for d in plugins)} skills, "
      f"{sum(len(glob.glob(f'{d}/commands/*.md')) for d in plugins)} commands: "
      f"{len(fails)} failure(s), {len(warns)} warning(s)")
sys.exit(1 if fails else 0)
PY
