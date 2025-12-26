from github import Github
import os
import base64
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
from github import Github
import os
import base64

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def commit_changes():
    try:
        file_path = "bot.py"

        contents = repo.get_contents(file_path)
        new_content = contents.decoded_content.decode()

        repo.update_file(
            path=file_path,
            message="🤖 Auto commit from Telegram bot",
            content=new_content,
            sha=contents.sha
        )
        return "✅ Commit successful via GitHub API"

    except Exception as e:
        return f"❌ Commit failed:\n{e}"

from github import Github
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "SIDHIMUSIC/freeetgapi"   # change if needed

def trigger_rollback():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    workflow = repo.get_workflow("deploy.yml")

    workflow.create_dispatch(
        ref="main",
        inputs={
            "rollback": "true"
        }
    )

    return "🔁 Rollback triggered successfully"
