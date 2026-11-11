#!/usr/bin/env bash
# 一键：重建站点 → 推 main（笔记）→ 分批推 gh-pages（站点）
#   bash tools/publish.sh
set -uo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OWNER=2486809961-alt; NAME=arc-welding-power
cd "$REPO_DIR" || exit 1
TOK="${GH_TOKEN:-$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | awk -F= '/^password=/{print substr($0,10)}')}"
[ -z "$TOK" ] && { echo "✗ 缺少 GitHub token（export GH_TOKEN=...）"; exit 1; }
AUTH="https://x-access-token:${TOK}@github.com/${OWNER}/${NAME}.git"

echo "▶ 1/3 重建静态站点"
python3 tools/build_site.py | tail -2

echo "▶ 2/3 推送 main（Obsidian 库）"
git remote set-url origin "$AUTH"; git add -A
git diff --cached --quiet || { git commit -q -m "sync: $(date '+%Y-%m-%d %H:%M')"; }
for i in 1 2 3 4 5; do git push -q origin main && break; echo "  retry $i"; sleep 3; done
git remote set-url origin "https://github.com/${OWNER}/${NAME}.git"

echo "▶ 3/3 分批推送 gh-pages（站点）"
cd public || exit 1
rm -rf .git; git init -q -b gh-pages
git config user.name KIM; git config user.email "271341795+${OWNER}@users.noreply.github.com"
git config core.quotepath false; git config http.version HTTP/1.1; git config http.postBuffer 157286400
git remote add origin "$AUTH"
git add index.html .nojekyll assets/style.css assets/app.js assets/sidebar.html assets/search.json assets/katex assets/mermaid.min.js notes
git commit -q -m "site: 骨架 + 笔记页 $(date '+%Y-%m-%d %H:%M')"
for i in 1 2 3 4 5; do git push -q -f origin gh-pages && break; echo "  retry $i"; sleep 3; done
n=0
while :; do
  files=$(git ls-files --others --exclude-standard 'assets/img/*.jpg' | head -40)
  [ -z "$files" ] && break
  n=$((n+1))
  printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 git add --
  git commit -q -m "site: img batch $n"
  for i in 1 2 3 4 5; do git push -q origin gh-pages && break; echo "  retry $i"; sleep 3; done
  echo "  batch $n ✓"
done
git remote set-url origin "https://github.com/${OWNER}/${NAME}.git"
echo "✓ 完成 → https://${OWNER}.github.io/${NAME}/"
