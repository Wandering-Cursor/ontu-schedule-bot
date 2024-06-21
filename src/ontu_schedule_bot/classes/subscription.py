"""This module describes subscription class"""

from ontu_schedule_bot.classes.base import BaseClass
from ontu_schedule_bot.classes.group import Group
from ontu_schedule_bot.classes.teacher import TeacherForSchedule


class Subscription(BaseClass):
    """Class for subscription to some group's schedule"""

    group: Group | None = None
    teacher: TeacherForSchedule | None = None

    is_active: bool

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ["is_active"]
        optional_params = ["group", "teacher"]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
            optional_params=optional_params,
        )

        group_json = parsed_params.pop("group", None)
        teacher_json = parsed_params.pop("teacher", None)

        if not group_json and not teacher_json:
            raise ValueError("group or teacher must be specified")

        obj = cls.make_object(parsed_params)

        if group_json:
            obj.group = Group.from_json(group_json)
        if teacher_json:
            obj.teacher = TeacherForSchedule.from_json(teacher_json)

        return obj
