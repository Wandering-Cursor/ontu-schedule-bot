"""This module defines group class"""

from .base import BaseClass
from .faculty import Faculty


class Group(BaseClass):
    """A class that defines some group in schedule"""

    name: str
    faculty: Faculty

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ["name", "faculty"]

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict, required_params=required_params
        )

        faculty = Faculty.from_json(parsed_params.pop("faculty", {}))

        obj = super().make_object(parsed_params)

        obj.faculty = faculty
        return obj
