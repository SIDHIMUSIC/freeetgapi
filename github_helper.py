import subprocess
from pathlib import Path

REPO_DIR = Path(".")


def get_git_diff():
    try:
        diff = subprocess.check_output(
            ["git", "diff"],
            cwd=REPO_DIR
        ).decode()

        if not diff.strip():
            return None

        return diff

    except Exception as e:
        return f"ERROR: {e}"


def suggest_changes():
    diff = get_git_diff()

    if not diff:
        return "✅ Abhi koi code change detect nahi hua."

    return (
        "🧠 *Code changes detected*\n\n"
        "```diff\n"
        f"{diff[:3500]}\n"
        "```\n\n"
        "👉 `/commit yes` = GitHub commit\n"
        "👉 `/commit no` = Cancel"
    )


def commit_changes():
    try:
        subprocess.check_call(["git", "add", "."])
        subprocess.check_call(
            ["git", "commit", "-m", "Auto commit by Telegram Bot 🤖"]
        )
        subprocess.check_call(["git", "push"])
        return "✅ GitHub par successfully commit & push ho gaya 🚀"

    except Exception as e:
        return f"❌ Commit failed:\n{e}"

def rollback_last_commit(repo):
    repo.git.reset('--hard', 'HEAD~1')
    origin = repo.remote(name='origin')
    origin.push(force=True)
