"""Imports for classes"""
from .base import BaseClass
from .chat import Chat
from .day import Day
from .department import Department
from .faculty import Faculty
from .group import Group
from .lesson import Lesson
from .message_campaign import MessageCampaign
from .pair import Pair
from .schedule import Schedule
from .subscription import Subscription
from .teacher import Teacher, TeacherForSchedule

__all__ = [
    "BaseClass",
    "Chat",
    "Faculty",
    "Group",
    "Lesson",
    "Pair",
    "Schedule",
    "Subscription",
    "Teacher",
    "Day",
    "TeacherForSchedule",
    "Department",
]
