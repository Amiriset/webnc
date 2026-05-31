from dataclasses import dataclass


@dataclass
class UserInfo:
    username: str
    roles: list
