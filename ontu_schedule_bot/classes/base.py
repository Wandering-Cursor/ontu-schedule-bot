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
