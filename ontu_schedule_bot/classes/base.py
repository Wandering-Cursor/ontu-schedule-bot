"""Defines a base class for all the dataclasses"""

class BaseClass:
    """A base class for all dataclasses"""

    @staticmethod
    def _get_parameters(json_dict: dict, required_params: list, optional_params: list|None=None):
        """A method to get parameters from JSON response"""
        actual_params = {}

        if not optional_params:
            optional_params = []

        for param_name in required_params:
            parameter = json_dict.get(param_name, None)
            if parameter is None:
                raise ValueError(
                    f"parameter {param_name} is not found and is required"
                )
            actual_params[param_name] = parameter

        for param_name in optional_params:
            parameter = json_dict.get(param_name, None)
            if parameter:
                actual_params[param_name] = parameter

        return actual_params

    @classmethod
    def make_object(cls, parameters: dict):
        """Method to create object from parsed parameters"""
        obj = cls()
        for parameter, value in parameters.items():
            setattr(obj, parameter, value)
        return obj

    @classmethod
    def from_json(cls, json_dict: dict):
        """Method to turn JSON response to an object"""
        raise NotImplementedError(
            "`from_json` method must be implemented"
        )


pair_times = [
    {"hour": 8, "minute": 0},
    {"hour": 9, "minute": 30},
    {"hour": 11, "minute": 30},
    {"hour": 13, "minute": 0},
    {"hour": 14, "minute": 30},
    {"hour": 16, "minute": 0},
]

pair_end_times = [
    {"hour": 9, "minute": 20},
    {"hour": 10, "minute": 50},
    {"hour": 12, "minute": 50},
    {"hour": 14, "minute": 20},
    {"hour": 15, "minute": 50},
    {"hour": 17, "minute": 20},
]

notification_times = [
    {"hour": 7, "minute": 50},
    {"hour": 9, "minute": 20},
    {"hour": 11, "minute": 20},
    {"hour": 12, "minute": 50},
    {"hour": 14, "minute": 20},
    {"hour": 15, "minute": 50},
]
