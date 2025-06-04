from typing import List
from pydantic import BaseModel


class BranchSpec(BaseModel):
    files: List[str]
    branch_name: str
