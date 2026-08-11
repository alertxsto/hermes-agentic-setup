#!/usr/bin/env bash
# ~/.hermes/scripts/work_prep_collector.sh
# Gathers hard ground-truth telemetry across all user repos and services in < 1 second.

set -euo pipefail

ACTIVE_REPOS=("skill-arena" "warung-app" "notes-vault")

echo "=== DAILY WORK PREP TELEMETRY ==="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo ""

echo "--- 1. MULTI-REPO GIT GROUND TRUTH ---"
for repo in "${ACTIVE_REPOS[@]}"; do
  repo_dir="$HOME/$repo"
  if [ -d "$repo_dir/.git" ]; then
    echo ">> REPO: $repo ($repo_dir)"
    cd "$repo_dir"

    echo "[Commits in Last 24 Hours]"
    recent_commits=$(git log --since="24 hours ago" --oneline -5 || true)
    if [ -n "$recent_commits" ]; then
      echo "$recent_commits"
    else
      echo "(No commits in last 24h)"
    fi

    echo "[Uncommitted WIP / Dirty Files]"
    status=$(git status --short || true)
    if [ -n "$status" ]; then
      echo "$status" | head -n 10
      count=$(echo "$status" | wc -l)
      if [ "$count" -gt 10 ]; then
        echo "... and $((count - 10)) more dirty files (Total: $count)"
      else
        echo "Total dirty files: $count"
      fi
    else
      echo "Clean working directory"
    fi
    echo ""
  fi
done

echo "--- 2. DEV SERVICES & PORTS STATUS ---"
check_port() {
  name=$1
  url=$2
  code=$(curl -s -m 2 -o /dev/null -w "%{http_code}" "$url" || echo "DOWN")
  echo "• $name ($url): HTTP $code"
}
# --- Dev services. Mark `# dev-only` for services that are NOT expected to run
#     24/7 (e.g. Expo dev server) so the auto-verify hook skips them when down.
check_port "skill-arena" "http://localhost:3100/"
check_port "warung-app (Expo)" "http://localhost:8081/"  # dev-only

echo ""
echo "--- 3. CLOUDFLARED TUNNELS STATUS ---"
cf_procs=$(ps aux | grep cloudflared | grep -v grep || true)
if [ -n "$cf_procs" ]; then
  echo "Running Tunnels:"
  echo "$cf_procs" | awk '{print "  PID "$2": "$11, $12, $13, $14, $15}'
  if echo "$cf_procs" | grep -q "trycloudflare"; then
    echo "⚠️ ALERT: Running temporary trycloudflare tunnel (random URL on restart!)"
  fi
else
  echo "• No cloudflared tunnel running"
fi

echo ""
echo "--- 4. SYSTEM & HOUSEKEEPING HEALTH ---"
inv_mtime=$(stat -c %y "$HOME/.hermes/INVENTORY.md" 2>/dev/null || echo "Missing")
echo "• INVENTORY.md last modified: $inv_mtime"
