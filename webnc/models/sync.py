from pydantic import BaseModel


class SyncRequest(BaseModel):
    left: str
    right: str
    subdirs: bool = True
    by_content: bool = False
    ignore_date: bool = False
    asymmetric: bool = False
    filter: str = "*"


class SyncAction(BaseModel):
    name: str
    action: str


class SyncExecuteRequest(BaseModel):
    left: str
    right: str
    actions: list[SyncAction]
