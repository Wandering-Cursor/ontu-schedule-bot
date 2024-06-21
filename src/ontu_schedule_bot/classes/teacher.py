"""Describes teacher"""

from ontu_schedule_bot.classes.base import BaseClass
from ontu_schedule_bot.classes.department import Department


class Teacher(BaseClass):
    """A teacher is just a container for two names"""

    full_name: str
    short_name: str

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ["full_name", "short_name"]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        return cls.make_object(parsed_params)


class TeacherForSchedule(BaseClass):
    """Teacher class that is used to fetch schedule"""

    external_id: int
    full_name: str
    short_name: str
    department: Department | None = None

    @classmethod
    def from_json(cls, json_dict: dict, fetch_department: bool = True):
        required_params = ["external_id", "full_name", "short_name"]
        if fetch_department:
            required_params.append("department")

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        obj = cls.make_object(parsed_params)

        if fetch_department:
            department = Department.from_json(parsed_params.pop("department", {}))
            obj.department = department

        return obj
