"""Describes Lesson"""

import datetime
import re

from .base import BaseClass
from .teacher import Teacher


class Lesson(BaseClass):
    """
    A lesson dataclass
    Use formatted_lesson_info or strip lesson_info
    """

    date: datetime.date
    teacher: Teacher
    full_name: str
    short_name: str
    lesson_info: str
    auditorium: str | None = None

    @property
    def formatted_lesson_info(self) -> str:
        """Returns a nice looking lesson info"""
        lesson_info = self.lesson_info.strip()
        all_links: set[str] = set(re.findall(r"(https?://[^\s]+)", lesson_info))
        i = 1
        for link in all_links:
            lesson_info = lesson_info.replace(
                link,
                f"<a href='{link}'>Посилання №{i}</a>",
            )
        return lesson_info

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = [
            "date",
            "teacher",
            "lesson_name",
            "lesson_info",
        ]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        teacher_params = parsed_params.pop("teacher")
        teacher = Teacher.from_json(teacher_params)

        lesson_name: dict[str, str] = parsed_params.pop("lesson_name")

        obj = cls.make_object(parsed_params)
        obj.teacher = teacher
        obj.full_name = lesson_name.get("full_name", "").strip()
        obj.short_name = lesson_name.get("short_name", "").strip()
        obj.auditorium = json_dict.get("auditorium", None)
        return obj


class TeachersLesson(BaseClass):
    """
    Teachers Lesson dataclass
    """

    name: str
    groups: list[str]

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = [
            "name",
            "groups",
        ]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        obj = cls.make_object(parsed_params)
        return obj
