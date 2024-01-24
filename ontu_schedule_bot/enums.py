"""This module contains some handy enumerators for bot"""
from enum import Enum


class Statuses(Enum):
    """Contains all statuses that backend may give"""

    OK = "ok"


class Endpoints(Enum):
    """Contains all used endpoints"""

    CHAT_INFO = "/api/chat_info"
    CHAT_CREATE = "/api/chat_create"
    CHAT_UPDATE = "/api/chat_update"

    CHATS_ALL = "/api/chats_all"

    FACULTIES_GET = "/api/faculties_get"

    GROUPS_GET = "/api/groups_get"

    SCHEDULE_GET = "/api/schedule_get"
    SCHEDULE_BATCH_GET = "/api/batch_schedule"

    NOTBOT_GET = "/api/update_notbot"
    CACHE_RESET = "/api/reset_cache"
    MESSAGE_CAMPAIGN_GET = "/api/message_campaign"

    # Teachers
    DEPARTMENTS_GET = "/api/teachers/departments"
    DEPARTMENT_GET = "api/teachers/department"
    TEACHERS_SCHEDULE = "/api/teachers/schedule"


FACULTY_NAME_INDEX = 1
PAGE_INDEX = 2
