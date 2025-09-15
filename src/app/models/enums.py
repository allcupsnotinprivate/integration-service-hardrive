from enum import Enum


class UserRole(str, Enum):
    SYSTEM = "SYSTEM"
    OPERATOR = "OPERATOR"
