from git_branch_splitter.github_client import GitHubClient
from git_branch_splitter.models import BranchSpec
from typing import List


def run(specs: List[BranchSpec], repo: str, token: str, base_branch: str):
    client = GitHubClient(token, repo)
    current_base = base_branch
    created_branches: List[tuple[str, str, str]] = []

    for spec in specs:
        print(f"\n🔧 Creating branch: {spec.branch_name} from base: {current_base}")

        base_sha = client.get_branch_sha(current_base)
        client.create_branch(spec.branch_name, base_sha)

        new_commit_sha = client.create_commit_with_files(
            base_sha,
            spec.files,
            spec.branch_name,
            message=f"chore: isolate files for {spec.branch_name}",
        )

        client.update_branch(spec.branch_name, new_commit_sha)

        pr_url = client.generate_pr_url(spec.branch_name, current_base)
        created_branches.append((spec.branch_name, current_base, pr_url))

        current_base = spec.branch_name

    print("\n✅ Branches created and ready for PRs:\n")
    for branch, base, pr in created_branches:
        print(f"🔗 {branch} (from {base}): {pr}")
