"""Describes pair"""
from classes.base import BaseClass, pair_times

from classes.lesson import Lesson


class Pair(BaseClass):
    lessons: list[Lesson]
    pair_no: int

    _pair_shift = -1

    @property
    def pair_index(self):
        return self.pair_no + self._pair_shift

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ['lessons', 'pair_no']

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        lessons: list[Lesson] = []
        json_lessons: list[dict] = parsed_params.pop(
            'lessons'
        )
        for json_data in json_lessons:
            lessons.append(
                Lesson.from_json(
                    json_data
                )
            )

        obj = cls.make_object(parsed_params)
        obj.lessons = lessons
        return obj

    def get_text(self):
        message = f"Пара №{self.pair_no}, початок о {pair_times[self.pair_index]}\n"

        for lesson in self.lessons:
            message += f"""
                {lesson.full_name} - {lesson.date}\n
                {lesson.teacher.short_name}\n
            """
        return message
