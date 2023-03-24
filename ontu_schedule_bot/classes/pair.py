"""Describes pair"""
from classes.base import BaseClass, pair_times, pair_end_times

from classes.lesson import Lesson

MESSAGE_FORMAT = """
Пара №{pair_no}, пара триває з {hour_0}:{minute_0} по {hour_1}:{minute_1} - {day_name}

{lessons}
"""

LESSON_FORMAT = """
{short_name} | {full_name} {lesson_date}
{teacher_name}

Картка:
{lesson_info}
"""


class Pair(BaseClass):
    """Pair class that keeps a list of lessons (because schedule is weird)"""
    lessons: list[Lesson]
    pair_no: int

    _pair_shift = -1

    @property
    def pair_index(self):
        """Returns pair_index (because pair_no starts from 1)"""
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

    @property
    def has_lessons(self):
        """Determines wether or not we should show this pair as active"""
        return bool(self.lessons)

    def as_text(self, day_name: str | None = None):
        """Returns pair's representation to show in bot (may be HTML)"""
        time_start = pair_times[self.pair_index]
        time_end = pair_end_times[self.pair_index]

        lessons_string = ""

        for lesson in self.lessons:
            lessons_string += LESSON_FORMAT.format(
                short_name=lesson.short_name,
                full_name=lesson.full_name,
                lesson_date=f"({lesson.date})" if lesson.date else "",
                teacher_name=lesson.teacher.full_name,
                lesson_info=lesson.formatted_lesson_info
            )
            lessons_string += "\n"

        message = MESSAGE_FORMAT.format(
            pair_no=self.pair_no,
            hour_0=str(time_start['hour']).zfill(2),
            minute_0=str(time_start['minute']).zfill(2),
            hour_1=str(time_end['hour']).zfill(2),
            minute_1=str(time_end['minute']).zfill(2),
            day_name=day_name or "",
            lessons=lessons_string
        )
        return message
