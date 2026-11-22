#!/usr/bin/env bash
# Fetch DevBench at the exact commit used for every result in this repo.
set -euo pipefail
COMMIT=bb593c1f9c535ff0dde0c9f4807d58c9566c3a6c
if [ ! -d DevBench/.git ]; then
  git clone https://github.com/open-compass/DevBench.git DevBench
fi
git -C DevBench fetch --depth 1 origin "$COMMIT" 2>/dev/null || true
git -C DevBench checkout -q "$COMMIT"
echo "DevBench at $(git -C DevBench rev-parse HEAD)"
