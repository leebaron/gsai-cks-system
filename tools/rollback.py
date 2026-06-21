#!/usr/bin/env python3
"""
rollback.py — Auto rollback for self-healing CI.

Triggers:
  - git revert <bad_commit>
  - Record in rollback ledger

Usage:
    python3 tools/rollback.py [--commit <sha>] [--dry-run]
    
Safety:
  --dry-run  print what would happen, do nothing destructive
  Requires full git history in repo root.
"""
import sys, json, subprocess, time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def git_log(n: int = 5) -> list:
    """Get recent commit history."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={n}", "--oneline"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        return [l.strip() for l in result.stdout.strip().split("\n") if l]
    except:
        return []


def git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=5,
        ).stdout.strip()
    except:
        return "unknown"


def rollback(commit_sha: str = None, dry_run: bool = True) -> dict:
    if not commit_sha:
        # Rollback one commit from HEAD
        current = git_head()
        commit_sha = current

    action = {
        "action": "revert",
        "commit": commit_sha,
        "dry_run": dry_run,
        "git_log": git_log(5),
    }

    if dry_run:
        action["status"] = "DRY_RUN"
        action["detail"] = f"would revert {commit_sha[:12]}"
        return action

    # Actual revert
    try:
        result = subprocess.run(
            ["git", "revert", "--no-edit", commit_sha, "-m", "Self-healing CI: auto rollback"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
        )
        action["exit_code"] = result.returncode
        action["stdout"] = result.stdout.strip() or ""
        action["stderr"] = result.stderr.strip() or ""
        action["status"] = "REVERTED" if result.returncode == 0 else "REVERT_FAILED"
        action["detail"] = f"revert {'successful' if result.returncode == 0 else 'failed'}"
    except subprocess.TimeoutExpired:
        action["status"] = "TIMEOUT"
        action["detail"] = "git revert timed out after 30s"
    except FileNotFoundError:
        action["status"] = "NO_GIT"
        action["detail"] = "git not found in PATH"

    return action


def main():
    args = sys.argv[1:]
    dry_run = False
    commit_sha = None

    for i, arg in enumerate(args):
        if arg == "--dry-run":
            dry_run = True
        elif arg == "--commit" and i + 1 < len(args):
            commit_sha = args[i + 1]
        elif arg == "--apply":
            dry_run = False

    result = rollback(commit_sha, dry_run)
    print(json.dumps(result, indent=2))

    # Record in rollback ledger
    ledger_dir = REPO_ROOT / "CKS_RUN_OUTPUT" / "rollback_ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_dir / f"rollback_{int(time.time())}.json"
    ledger_path.write_text(json.dumps(result, indent=2))

    # Exit code reflects safety only (dry-run is ok, real revert fail is bad)
    if result.get("status") == "REVERT_FAILED":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
