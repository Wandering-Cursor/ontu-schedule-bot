from enum import Enum

class Statuses(Enum):
    """Conains all statuses that backend may give"""
    OK = "ok"

class Endpoints(Enum):
    """Contains all used endpoints"""
    CHAT_INFO = "/chat_info"
    CHAT_CREATE = "/chat_create"
    CHAT_UPDATE = "/chat_update"

    CHATS_ALL = "/chats_all"

    FACULTIES_GET = "/faculties_get"

    GROUPS_GET = "/groups_get"

    SCHEDULE_GET = "/schedule_get"
