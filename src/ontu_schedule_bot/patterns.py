"""Defines patterns for callbacks"""


def set_group_pattern(callback_data):
    """Pattern for set_group"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "set_group":
            return True
    return False


def pick_faculty_pattern(callback_data):
    """Pattern for pick_faculty"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "pick_faculty" and callback_data[1]:
            return True
    return False


def pick_group_pattern(callback_data):
    """Pattern for pick_group"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "pick_group" and callback_data[1]:
            return True
    return False


def start_pattern(callback_data):
    """Pattern for start"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "start":
            return True
    return False


def get_schedule(callback_data):
    """Pattern for get_schedule"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "get_schedule":
            return True
    return False


def day_details_pattern(callback_data):
    """Pattern to get details of a day"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "day_details":
            return True
    return False


def pair_details_pattern(callback_data):
    """Pattern for pair_details"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "pair_details":
            return True
    return False


def toggle_subscription_pattern(callback_data):
    """Pattern for toggle_subscription"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "toggle_subscription":
            return True
    return False


def update_cache_pattern(callback_data):
    """Pattern for update_cache"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "update_cache":
            return True
    return False


def start_for_teachers_pattern(callback_data):
    """Pattern for start_for_teachers"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "start_for_teachers":
            return True
    return False


def set_teacher(callback_data):
    """Pattern for set_teacher"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "set_teacher":
            return True
    return False


def pick_department(callback_data):
    """Pattern for pick_department"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "pick_department" and callback_data[1]:
            return True
    return False


def pick_teacher(callback_data):
    """Pattern for pick_teacher"""
    if isinstance(callback_data, tuple):
        if callback_data[0] == "pick_teacher" and callback_data[1]:
            return True
    return False
