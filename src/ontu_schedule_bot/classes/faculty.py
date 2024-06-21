"""This module defines faculty class"""

from ontu_schedule_bot.classes.base import BaseClass


class Faculty(BaseClass):
    """Faculty - An object on rozklad.ontu.edu.ua site with a name, has some groups"""

    name: str

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ["name"]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict, required_params=required_params
        )

        return super().make_object(parsed_params)
