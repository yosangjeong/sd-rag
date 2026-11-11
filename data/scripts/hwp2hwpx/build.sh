#!/bin/bash
# Build the HWP -> HWPX converter used by data/scripts/build_kr.py.
#
# Sources: github.com/neolord0/{hwplib,hwpxlib,hwp2hwpx} (Apache-2.0), pinned
# to the commits below. None of them has runtime dependencies, so plain javac
# is enough (no Maven, no network access besides git).
#
# Output: data/scripts/hwp2hwpx/build/classes  (gitignored)
# Needs:  JDK 11+  (brew install openjdk@21)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BUILD="$HERE/build"
JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@21}"
export PATH="$JAVA_HOME/bin:$PATH"

REPOS=(
  "hwplib   6746c27f17ebf5277493206284aa32044a1839c4"  # 2026-09-11
  "hwpxlib  f9fd2255ac0fc57414e0b657d115e7de51d31c65"  # 2026-08-31
  "hwp2hwpx 62d95b980a4e3a6766877dd3fb6f7f45f4afcf3d"  # 2026-10-26
)

mkdir -p "$BUILD/src"
for entry in "${REPOS[@]}"; do
  read -r name sha <<< "$entry"
  dir="$BUILD/src/$name"
  if [ ! -d "$dir/.git" ]; then
    git init -q "$dir"
    git -C "$dir" remote add origin "https://github.com/neolord0/$name.git"
  fi
  if [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null || true)" != "$sha" ]; then
    git -C "$dir" fetch -q --depth 1 origin "$sha"
    git -C "$dir" checkout -q FETCH_HEAD
  fi
  echo "$name @ ${sha:0:7}"
done

rm -rf "$BUILD/classes" && mkdir -p "$BUILD/classes"
find "$BUILD/src"/*/src/main/java "$HERE/shim" -name '*.java' > "$BUILD/sources.txt"
echo "$HERE/Convert.java" >> "$BUILD/sources.txt"
javac -nowarn -encoding UTF-8 -d "$BUILD/classes" @"$BUILD/sources.txt" 2>&1 | grep -v '^Note:' || true
test -f "$BUILD/classes/Convert.class"
echo "built $BUILD/classes"
