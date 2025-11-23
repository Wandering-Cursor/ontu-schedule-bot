"""This is a utils module, it contains Requests and pagination for bot"""

import datetime

import pytz

import re


def current_time_in_kiev() -> datetime.datetime:
    """Returns current time in Kiev timezone"""
    kiev_tz = pytz.timezone("Europe/Kyiv")
    return datetime.datetime.now(tz=kiev_tz)


PAIR_START_TIME = {
    1: datetime.time(hour=8, minute=0),
    2: datetime.time(hour=9, minute=30),
    3: datetime.time(hour=11, minute=30),
    4: datetime.time(hour=13, minute=0),
    5: datetime.time(hour=14, minute=30),
    6: datetime.time(hour=16, minute=0),
    7: datetime.time(hour=17, minute=30),
    8: datetime.time(hour=19, minute=10),
}
PAIR_END_TIME = {
    1: datetime.time(hour=9, minute=20),
    2: datetime.time(hour=10, minute=50),
    3: datetime.time(hour=12, minute=50),
    4: datetime.time(hour=14, minute=20),
    5: datetime.time(hour=15, minute=50),
    6: datetime.time(hour=17, minute=20),
    7: datetime.time(hour=18, minute=50),
    8: datetime.time(hour=20, minute=30),
}


def get_pair_time_bounds(pair_number: int) -> tuple[datetime.time, datetime.time]:
    """Returns start and end time of some pair by its number"""
    start_time = PAIR_START_TIME.get(pair_number)
    end_time = PAIR_END_TIME.get(pair_number)

    if not start_time or not end_time:
        raise ValueError("Pair number must be between 1 and 8")

    return start_time, end_time


def get_weekday_name(date: datetime.date) -> str:
    """Returns weekday name for some date"""
    weekdays = {
        0: "Понеділок",
        1: "Вівторок",
        2: "Середа",
        3: "Четвер",
        4: "П'ятниця",
        5: "Субота",
        6: "Неділя",
    }

    return weekdays.get(date.weekday(), "Невідомий день")


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """
    Split a message into chunks no longer than max_length characters.
    Tries to split on sentence boundaries, line breaks, or word boundaries when possible.
    Preserves HTML tags when splitting by closing broken tags and reopening them in the next chunk.

    Args:
        text (str): The text to split
        max_length (int): Maximum length of each chunk (default: 4096)

    Returns:
        list[str]: List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    def find_open_tags(text_chunk: str) -> list[str]:
        """Find unclosed HTML tags in the text chunk"""
        # Find all opening tags
        opening_tags = re.findall(r"<([^/\s>]+)[^>]*>", text_chunk)
        # Find all closing tags
        closing_tags = re.findall(r"</([^>\s]+)>", text_chunk)

        # Count occurrences of each tag type
        tag_counts = {}
        for tag in opening_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        for tag in closing_tags:
            if tag in tag_counts:
                tag_counts[tag] -= 1
                if tag_counts[tag] == 0:
                    del tag_counts[tag]

        # Return tags that still have open occurrences
        open_tags = []
        for tag, count in tag_counts.items():
            open_tags.extend([tag] * count)

        return open_tags

    while len(remaining) > max_length:
        # Find the best split point within max_length
        split_point = max_length

        # Look for sentence endings (. ! ?) followed by space or newline
        for i in range(max_length - 1, max_length // 2, -1):
            if (
                remaining[i] in ".!?"
                and i + 1 < len(remaining)
                and remaining[i + 1] in " \n"
            ):
                split_point = i + 1
                break

        # If no sentence boundary found, look for line breaks
        if split_point == max_length:
            for i in range(max_length - 1, max_length // 2, -1):
                if remaining[i] == "\n":
                    split_point = i + 1
                    break

        # If no line break found, look for word boundaries
        if split_point == max_length:
            for i in range(max_length - 1, max_length // 2, -1):
                if remaining[i] == " ":
                    split_point = i + 1
                    break

        # If no good split point found, check for HTML tag boundaries
        if split_point == max_length:
            for i in range(max_length - 1, max_length // 2, -1):
                if remaining[i] == ">":
                    split_point = i + 1
                    break

        # Extract the chunk
        chunk = remaining[:split_point].rstrip()

        # Find open tags that need to be closed
        open_tags = find_open_tags(chunk)

        # Close any open tags at the end of this chunk
        if open_tags:
            for tag in reversed(open_tags):
                chunk += f"</{tag}>"

        chunks.append(chunk)

        # Prepare the next chunk by reopening the tags
        next_chunk_start = ""
        if open_tags:
            for tag in open_tags:
                next_chunk_start += f"<{tag}>"

        remaining = next_chunk_start + remaining[split_point:].lstrip()

    # Add the last chunk if there's remaining text
    if remaining:
        chunks.append(remaining)

    return chunks
