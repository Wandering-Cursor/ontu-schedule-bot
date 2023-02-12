"""Describes teacher"""

from classes.base import BaseClass


class Teacher(BaseClass):
    full_name: str
    short_name: str

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ['full_name', 'short_name']

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params,
        )

        return cls.make_object(parsed_params)
