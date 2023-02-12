"""Describes schedule"""

from classes.base import BaseClass, pair_times

from classes.pair import Pair

import datetime

day_names = {
    0: "Понеділок",
    1: "Вівторок",
    2: "Середа",
    3: "Четверг",
    4: "П'ятниця",
    5: "Субота",
    6: "Неділя",
}


def next_pair_no_from_time(hour_minute_tuple: tuple[int, int]):
    i = 0
    hour = hour_minute_tuple[0]
    minute = hour_minute_tuple[1]
    for time_dict in pair_times:
        i += 1
        if time_dict["hour"] < hour:
            break
        if time_dict["hour"] == hour and time_dict["minute"] < minute:
            break
    else:
        i = -1
    return i

class Schedule(BaseClass):
    days: dict[str, list[Pair]]


    @classmethod
    def from_json(cls, json_dict: dict):
        required_params = ['days']

        parsed_params = BaseClass._get_parameters(
            json_dict=json_dict,
            required_params=required_params
        )

        days: dict[str, list[Pair]] = {}
        json_days: dict[str, list[dict]] = parsed_params.pop('days')
        for day_name, pairs in json_days.items():
            days[day_name] = [
                Pair.from_json(pair) for pair in pairs
            ]

        obj = cls.make_object(parsed_params)
        obj.days = days
        return obj

    def get_next_pair(self):
        now = datetime.datetime.now()
        hour_minute_tuple = (now.hour, now.minute)

        pair_no = next_pair_no_from_time(hour_minute_tuple=hour_minute_tuple)

        if pair_no < 0:
            now += datetime.timedelta(days=1)
            pair_no = 1

        day_name = day_names.get(now.weekday())

        if not day_name:
            raise ValueError(f"Impossible day no: {now.weekday()}|Days: {day_names}")

        pairs_of_day = self.days.get(day_name, [])
        next_pair = None

        for pair in pairs_of_day:
            if pair.pair_no == pair_no:
                next_pair = pair
                break

        if not next_pair:
            raise ValueError(
                "Could not get next pair",
                pairs_of_day,
                pair_no
            )

        return next_pair
