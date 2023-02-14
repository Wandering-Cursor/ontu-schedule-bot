"""Describes Lesson"""
from classes.base import BaseClass

from classes.teacher import Teacher

import datetime

class Lesson(BaseClass):
    date: datetime.date
    teacher: Teacher
    full_name: str
    short_name: str
    lesson_info: str

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ['date', 'teacher', 'lesson_name', 'lesson_info']

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        teacher_params = parsed_params.pop(
            'teacher'
        )
        teacher = Teacher.from_json(teacher_params)

        lesson_name: dict[str, str] = parsed_params.pop(
            'lesson_name'
        )

        obj = cls.make_object(parsed_params)
        obj.teacher = teacher
        obj.full_name = lesson_name.get('full_name', '')
        obj.short_name = lesson_name.get('short_name', '')
        return obj
