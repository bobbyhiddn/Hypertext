#!/usr/bin/env bash
# Fetch the cold evidence archives from the GitHub Release and unpack them
# into the repository root. Needed for full provenance verification
# (templates/archive/**) and for regenerating from historical assets.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
TAG="${1:-evidence-2026-08}"
for asset in hypertext-evidence-archive-2026-08.tar.gz \
             hypertext-tts-exports-2026-Q1-dev.tar.gz; do
  echo "fetching $asset from release $TAG ..."
  gh release download "$TAG" --pattern "$asset" --output "/tmp/$asset" --clobber
  tar -xzf "/tmp/$asset"
  rm "/tmp/$asset"
done
echo "evidence unpacked; provenance tests will no longer skip."
