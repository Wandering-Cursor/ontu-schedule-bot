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
pair_times = [
    {"hour": 8, "minute": 0},
    {"hour": 9, "minute": 30},
    {"hour": 11, "minute": 30},
    {"hour": 13, "minute": 0},
    {"hour": 14, "minute": 30},
    {"hour": 16, "minute": 0},
    {"hour": 17, "minute": 30},
    {"hour": 19, "minute": 10},
]
pair_end_times = [
    {"hour": 9, "minute": 20},
    {"hour": 10, "minute": 50},
    {"hour": 12, "minute": 50},
    {"hour": 14, "minute": 20},
    {"hour": 15, "minute": 50},
    {"hour": 17, "minute": 20},
    {"hour": 18, "minute": 50},
    {"hour": 20, "minute": 30},
]
notification_times = [
    {"hour": 7, "minute": 50},
    {"hour": 9, "minute": 20},
    {"hour": 11, "minute": 20},
    {"hour": 12, "minute": 50},
    {"hour": 14, "minute": 20},
    {"hour": 15, "minute": 50},
    {"hour": 17, "minute": 20},
    {"hour": 19, "minute": 0},
]
