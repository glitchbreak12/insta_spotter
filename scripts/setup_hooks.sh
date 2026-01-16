#!/usr/bin/env bash
# Setup a post-commit hook that automatically pushes to origin/main after each commit.
HOOK_DIR=".git/hooks"
HOOK_FILE="$HOOK_DIR/post-commit"

mkdir -p "$HOOK_DIR"
cat > "$HOOK_FILE" <<'HOOK'
#!/usr/bin/env bash
# Automatically push after commit
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "main" ]; then
  echo "Auto-pushing to origin/main..."
  git push origin main
fi
HOOK

chmod +x "$HOOK_FILE"
echo "Post-commit hook installed (pushes main after each commit)."