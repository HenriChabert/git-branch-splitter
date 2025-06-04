import typer
from git_branch_splitter.utils import load_specs
from git_branch_splitter.main import run
import json
from git_branch_splitter.github_client import GitHubClient
import os
import subprocess
import re

app = typer.Typer()


def get_token(provided_token: str | None = None) -> str:
    if provided_token:
        return provided_token

    if token := os.getenv("GH_TOKEN"):
        return token

    try:
        return subprocess.check_output(["gh", "auth", "token"]).decode().strip()
    except Exception:
        raise RuntimeError(
            "❌ No GitHub token provided and failed to load from `gh auth token`. "
            "Please provide --token or set GH_TOKEN env var."
        )


def get_repo(provided_repo: str | None = None) -> str:
    if provided_repo:
        return provided_repo

    try:
        subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "❌ Not inside a Git repository. Use --repo to specify manually."
        )

    try:
        remote_url = (
            subprocess.check_output(
                ["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "❌ Could not determine remote origin. Use --repo to specify manually."
        )

    # Parse GitHub repo from SSH or HTTPS format
    match = re.match(
        r"(git@github\.com:|https://github\.com/)([^/]+/[^/.]+)", remote_url
    )
    if match:
        return match.group(2)
    else:
        raise RuntimeError(f"❌ Unrecognized GitHub remote URL format: {remote_url}")


def get_current_branch() -> str:
    try:
        branch = (
            subprocess.check_output(
                ["git", "symbolic-ref", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        return branch
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "❌ Could not determine current branch. Are you in a detached HEAD?"
        )


@app.command()
def split(
    specs: str = typer.Option(..., help="Path to JSON spec file."),
    base_branch: str | None = typer.Option(
        None,
        help="Name of the base branch. If not provided, will use the current branch.",
    ),
    repo: str | None = typer.Option(None, help="GitHub repo, e.g., user/repo"),
    token: str | None = typer.Option(
        None, help="GitHub token (can use GH_TOKEN env var)."
    ),
):
    branch_specs = load_specs(specs)

    token = get_token(token)
    repo = get_repo(repo)
    base_branch = base_branch or get_current_branch()

    run(branch_specs, repo, token, base_branch)


@app.command()
def list_files(
    branch: str | None = typer.Option(
        None,
        help="The branch to inspect. If not provided, will use the current branch.",
    ),
    base: str = typer.Option(..., help="The base branch to compare against."),
    repo: str | None = typer.Option(None, help="GitHub repo, e.g., user/repo"),
    token: str | None = typer.Option(
        None, help="GitHub token (can use GH_TOKEN env var)."
    ),
):
    token = get_token(token)
    repo = get_repo(repo)
    branch = branch or get_current_branch()

    client = GitHubClient(token, repo)
    files = client.get_changed_files(base, branch)

    result = {"branch_name": branch, "files": files}

    print(json.dumps(result, indent=2))


@app.command(name="get-repo")
def get_repo_cmd():
    """
    Get the current GitHub repo slug (e.g. user/repo) from the local Git context.
    """
    repo = get_repo()
    print(repo)


if __name__ == "__main__":
    app()
