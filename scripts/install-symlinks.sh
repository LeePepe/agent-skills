#!/usr/bin/env bash
# 把 skills/<category>/<name>/ 全部软链到 ~/.claude/skills/<name>,幂等。
# 用于本地开发本仓库(改一处处处生效);正式分发走 plugin marketplace(见 README)。
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$DEST"

n=0
for sk in "$REPO"/skills/*/*/; do
  [ -f "$sk/SKILL.md" ] || continue
  name="$(basename "$sk")"
  ln -sfn "${sk%/}" "$DEST/$name"
  echo "  linked $name -> ${sk#"$REPO"/}"
  n=$((n+1))
done
echo "✅ $n 个 skill 已软链到 $DEST"
