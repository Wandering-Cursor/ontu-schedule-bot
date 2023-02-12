"""This module describes subscription class"""

from classes.base import BaseClass

from classes.group import Group

class Subscription(BaseClass):
    """Class for subscription to some group's schedule"""
    group: Group

    is_active: bool

    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ['group', 'is_active']

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params
        )

        group = Group.from_json(
            parsed_params.pop('group', {})
        )

        obj = cls.make_object(parsed_params)
        obj.group = group
        return obj
