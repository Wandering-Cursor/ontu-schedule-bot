"""Module of a day class (Day - a set of pairs for a day of a week)"""

from collections import OrderedDict
from operator import attrgetter

from classes.base import BaseClass
from classes.pair import Pair

SUMMARY = "{day} - {pairs} пари ({first} - {last})"

PAIR_SUMMARY = "{no}. {short_name} - {teacher}"


class Day(BaseClass):
    """Day is an abstraction for a weekday with a set of pairs"""

    name: str
    pairs: list[Pair]

    def __init__(self, day_name: str, pairs: list[Pair]):
        super().__init__()
        self.name = day_name
        self.pairs = pairs

    @classmethod
    def from_json(cls, json_dict: dict):
        raise ValueError("This object should not be coming from json")

    def _active_pairs(self) -> list[Pair]:
        active_pairs: list[Pair] = []

        for pair in self.pairs:
            if pair.has_lessons:
                active_pairs.append(pair)
        return active_pairs

    def get_brief(self) -> str:
        """Returns a brief summary of the day"""
        active_pairs = self._active_pairs()

        if not active_pairs:
            return f"{self.name} - немає пар"

        first: Pair = min(active_pairs, key=attrgetter('pair_no'))
        last: Pair = max(active_pairs, key=attrgetter('pair_no'))

        return SUMMARY.format(
            day=self.name,
            pairs=len(active_pairs),
            first=first.pair_no,
            last=last.pair_no
        )

    def get_details(self) -> OrderedDict[Pair, str]:
        """Returns an OrderedDictionary of pairs with representation"""
        pairs = OrderedDict()

        active_pairs = self._active_pairs()
        for pair in active_pairs:
            # Hmmm, I guess that's fine?
            lesson = pair.lessons[0]
            pairs[pair] = PAIR_SUMMARY.format(
                no=pair.pair_no,
                short_name=lesson.short_name,
                teacher=lesson.teacher.short_name
            )

        return pairs
