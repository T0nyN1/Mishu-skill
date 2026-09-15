#!/usr/bin/env bash
# Install the Mishu skill by linking skill/mishu into ~/.claude/skills/mishu.
# Your data vault is NOT created here — on first use, /mishu creates an empty one (default ~/MishuVault)
# and helps you add your first goals.
set -euo pipefail
command -v python3 >/dev/null || { echo "✗ Python 3.9+ is required"; exit 1; }
python3 -c "import sys; sys.exit(sys.version_info < (3, 9))" || { echo "✗ Python 3.9+ is required"; exit 1; }
SRC="$(cd "$(dirname "$0")" && pwd)/skill/mishu"
DEST="$HOME/.claude/skills/mishu"
mkdir -p "$HOME/.claude/skills"
if [ -e "$DEST" ] && [ ! -L "$DEST" ]; then
  echo "✗ $DEST exists and is not a symlink; move it away first"; exit 1
fi
ln -sfn "$SRC" "$DEST"
chmod +x "$SRC/scripts/mishu.py" "$SRC/scripts/guard.py"
echo "✅ Installed: $DEST -> $SRC"
echo "   Open Claude Code and type /mishu to get started (your vault starts empty)."
echo "   已安装。在 Claude Code 中输入 /mishu 开始使用（首次使用为空库，会引导你录入第一批目标）。"
