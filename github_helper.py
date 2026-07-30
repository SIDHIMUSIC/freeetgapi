from github import Github
import os
import subprocess
from pathlib import Path

REPO_DIR = Path(".")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "SIDHIMUSIC/freeetgapi"   # Ya os.getenv("GITHUB_REPO")

if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is missing!")

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)


def get_git_diff():
    try:
        diff = subprocess.check_output(
            ["git", "diff"],
            cwd=REPO_DIR
        ).decode()

        return diff if diff.strip() else None

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
        "👉 /commit yes = GitHub commit\n"
        "👉 /commit no = Cancel"
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


def rollback_last_commit():
    try:
        subprocess.check_call(["git", "reset", "--hard", "HEAD~1"])
        subprocess.check_call(["git", "push", "--force"])

        return "🔁 Last commit rollback successful."

    except Exception as e:
        return f"❌ Rollback failed:\n{e}"


def trigger_rollback():
    try:
        workflow = repo.get_workflow("deploy.yml")

        workflow.create_dispatch(
            ref="main",
            inputs={
                "rollback": "true"
            }
        )

        return "🔁 Rollback workflow triggered."

    except Exception as e:
        return f"❌ Workflow trigger failed:\n{e}"
