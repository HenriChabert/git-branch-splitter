from github import Github
from github.Repository import Repository
from github.InputGitTreeElement import InputGitTreeElement
from typing import List


class GitHubClient:
    def __init__(self, token: str, repo_name: str):
        self.gh = Github(token)
        self.repo: Repository = self.gh.get_repo(repo_name)

    def get_branch_sha(self, branch_name: str) -> str:
        return self.repo.get_branch(branch_name).commit.sha

    def create_branch(self, new_branch: str, from_sha: str):
        self.repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=from_sha)

    def create_commit_with_files(
        self, base_sha: str, files: List[str], branch_name: str, message: str
    ) -> str:
        base_commit = self.repo.get_commit(sha=base_sha)
        base_tree = base_commit.commit.tree

        elements: List[InputGitTreeElement] = []
        for file_path in files:
            try:
                contents = self.repo.get_contents(file_path, ref=branch_name)
                elements.append(
                    InputGitTreeElement(
                        path=file_path, mode="100644", type="blob", sha=contents.sha
                    )
                )
            except Exception as e:
                print(f"⚠️ Skipping missing file: {file_path} ({e})")

        new_tree = self.repo.create_git_tree(elements, base_tree)
        new_commit = self.repo.create_git_commit(
            message, new_tree, [base_commit.commit]
        )
        return new_commit.sha

    def update_branch(self, branch_name: str, new_sha: str):
        ref = self.repo.get_git_ref(f"heads/{branch_name}")
        ref.edit(sha=new_sha, force=True)

    def generate_pr_url(self, head: str, base: str) -> str:
        return (
            f"https://github.com/{self.repo.full_name}/compare/{base}...{head}?expand=1"
        )

    def get_changed_files(self, base: str, head: str) -> List[str]:
        comparison = self.repo.compare(base, head)
        return [
            f.filename
            for f in comparison.files
            if f.status in {"added", "modified", "renamed"}
        ]
