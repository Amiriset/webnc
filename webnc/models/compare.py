from pydantic import BaseModel


class CompareRequest(BaseModel):
    left: str
    right: str
