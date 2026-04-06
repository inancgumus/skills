#!/usr/bin/env bash
# Symlink skills from this repo into ~/.agents/skills/
# Idempotent — safe to run repeatedly, on new machines, or after adding new skills.
#
# Usage:
#   ./install.sh          # symlink all skills
#   ./install.sh slack    # symlink only "slack"

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${HOME}/.agents/skills"

mkdir -p "$TARGET_DIR"

# Collect skill directories (any dir containing SKILL.md)
skills=()
if [[ $# -gt 0 ]]; then
  skills=("$@")
else
  for dir in "$REPO_DIR"/*/; do
    [[ -f "$dir/SKILL.md" ]] && skills+=("$(basename "$dir")")
  done
fi

if [[ ${#skills[@]} -eq 0 ]]; then
  echo "No skills found in $REPO_DIR"
  exit 1
fi

for skill in "${skills[@]}"; do
  src="$REPO_DIR/$skill"
  dest="$TARGET_DIR/$skill"

  if [[ ! -d "$src" ]] || [[ ! -f "$src/SKILL.md" ]]; then
    echo "skip: $skill (no SKILL.md found in $src)"
    continue
  fi

  # Already a correct symlink — nothing to do
  if [[ -L "$dest" ]] && [[ "$(readlink "$dest")" == "$src" ]]; then
    echo "  ok: $skill"
    continue
  fi

  # Remove existing (old symlink, or plain directory from npx install)
  if [[ -L "$dest" ]] || [[ -d "$dest" ]]; then
    rm -rf "$dest"
    echo "link: $skill (replaced existing)"
  else
    echo "link: $skill"
  fi

  ln -s "$src" "$dest"
done
