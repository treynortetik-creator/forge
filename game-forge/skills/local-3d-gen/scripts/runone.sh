#!/bin/bash
# runone.sh <tag> <cmd...>
# Run one heavy job and record wall time + peak RAM, so every run has a receipt.
#   mkdir -p runs && ./runone.sh px-urn python pixal3d_generate.py in.png runs/px-urn.glb --res 1024
# Writes runs/<tag>.{mem0,log,time}. `<tag>.time` holds /usr/bin/time -l output (real seconds,
# "maximum resident set size" in bytes on macOS) plus a final `exit=<code>` line.
tag=$1; shift
mkdir -p runs
memory_pressure | tail -1 > "runs/$tag.mem0"
/usr/bin/time -l -o "runs/$tag.time" "$@" > "runs/$tag.log" 2>&1
echo "exit=$?" >> "runs/$tag.time"
