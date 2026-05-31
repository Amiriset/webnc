from enum import Enum


class ServerState(str, Enum):
    STARTING = "starting"
    GENERATING_CERT = "generating_cert"
    RUNNING = "running"
    ERROR = "error"
