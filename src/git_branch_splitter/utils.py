import json
from typing import List
from git_branch_splitter.models import BranchSpec


def load_specs(spec_file_path: str) -> List[BranchSpec]:
    with open(spec_file_path) as f:
        data = json.load(f)
    return [BranchSpec(**spec) for spec in data]
