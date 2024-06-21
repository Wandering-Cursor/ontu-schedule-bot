"""Describes department"""

from ontu_schedule_bot.classes.base import BaseClass


class Department(BaseClass):
    """Describes a department"""

    external_id: int
    name: str
    full_name: str

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ["external_id", "name", "full_name"]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        return cls.make_object(parsed_params)
