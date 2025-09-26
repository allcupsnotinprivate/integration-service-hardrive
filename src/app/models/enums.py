from enum import Enum


class UserRole(str, Enum):
    SYSTEM = "SYSTEM"
    OPERATOR = "OPERATOR"


class RecipientModule(str, Enum):
    USERS = "Users"
    CONTACTS = "Contacts"
    ACCOUNTS = "Accounts"
    SYSTEMS = "Systems"


class DeliveryEventStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
