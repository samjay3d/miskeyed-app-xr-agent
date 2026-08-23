#!/usr/bin/env bash
set -euo pipefail

source_checkout="${1:-../miskeyed-xr-agent}"
if [[ ! -d "$source_checkout/.git" ]]; then
  echo "not a miskeyed-xr-agent source checkout: $source_checkout" >&2
  exit 2
fi

branch="$(git -C "$source_checkout" branch --show-current)"
if [[ "$branch" != "codex/create-new-repository-miskeyed-xr-agent" ]]; then
  echo "expected integration branch, found: $branch" >&2
  exit 2
fi

python -m pip install --editable "$source_checkout"

