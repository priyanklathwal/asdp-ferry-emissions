#!/usr/bin/env bash
# Push this repository to a NEW PRIVATE repo under github.com/priyanklathwal
#
# Option A, with the GitHub CLI (creates the repo and pushes in one step):
#   gh auth login
#   gh repo create priyanklathwal/asdp-ferry-emissions --private --source=. --remote=origin --push
#
# Option B, without gh: create an empty private repo named asdp-ferry-emissions
# at https://github.com/new (no README, no .gitignore, no licence), then run:
#   ./push_to_github.sh
set -e
REPO="${1:-https://github.com/priyanklathwal/asdp-ferry-emissions.git}"
git remote add origin "$REPO" 2>/dev/null || git remote set-url origin "$REPO"
git branch -M main
git push -u origin main
cat <<'MSG'

Pushed.

The dashboard is at docs/index.html. To serve it:
  Settings > Pages > Source: Deploy from a branch > Branch: main, folder: /docs

Note that GitHub Pages on a PRIVATE repo requires a Team or Enterprise plan. On a
personal free account, Pages only serves public repos. If the repo must stay private,
docs/index.html is fully self-contained (data inlined, no CDN calls) and can be opened
from disk, emailed, or dropped in SharePoint as a single file.

The input workbook is NOT committed (see .gitignore). Anyone cloning this will need
Cordula's xlsx in the working directory to reproduce the numbers.
MSG
