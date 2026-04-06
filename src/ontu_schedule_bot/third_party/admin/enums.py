from enum import StrEnum


class Platform(StrEnum):
    TELEGRAM = "TELEGRAM"


class ScheduleEntityType(StrEnum):
    GROUP = "group"
    TEACHER = "teacher"
