#!/usr/bin/env sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command -v pnpm >/dev/null 2>&1 || {
  echo "pnpm 10 is required. Install Node.js 20+ and run: corepack enable" >&2
  exit 1
}

cd "$project_root"
pnpm install --frozen-lockfile
exec pnpm dev
