import datetime
import json
import logging
from collections.abc import AsyncGenerator, Generator

import httpx
import pydantic

from ontu_schedule_bot.errors import SubscriptionNotFoundError
from ontu_schedule_bot.settings import settings
from ontu_schedule_bot.third_party.admin.schemas import (
    Chat,
    CreateChatRequest,
    DaySchedule,
    Department,
    DepartmentPaginatedRequest,
    DepartmentPaginatedResponse,
    Faculty,
    FacultyPaginatedRequest,
    FacultyPaginatedResponse,
    GroupPaginatedRequest,
    GroupPaginatedResponse,
    MessageCampaign,
    Subscription,
    TeacherPaginatedRequest,
    TeacherPaginatedResponse,
    WeekSchedule,
)

logger = logging.getLogger(__name__)


def reraise_for_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error occurred: %s; response text:\n%s",
            e,
            response.text,
        )

        raise httpx.HTTPStatusError(
            message=e.args[0] + f"; response text:\n{response.text[:128]}",
            request=e.request,
            response=e.response,
        ) from e


def _parse_bulk_schedule_record(
    data: dict[str, list[dict | None]],
) -> dict[str, list[DaySchedule | None]]:
    return {
        key: [DaySchedule.model_validate(item) if item is not None else None for item in value]
        for key, value in data.items()
    }


def _prepare_bulk_buffer(
    buffer: str,
    chunk: str,
    *,
    array_started: bool,
) -> tuple[str, bool]:
    if not chunk:
        return buffer, array_started

    buffer += chunk

    if array_started:
        return buffer, True

    buffer = buffer.lstrip()
    if not buffer:
        return buffer, False

    if buffer[0] != "[":
        raise ValueError("bulk_schedule response must be a JSON array")

    return buffer[1:], True


def _consume_array_separators(buffer: str) -> str:
    buffer = buffer.lstrip()

    while buffer.startswith(","):
        buffer = buffer[1:].lstrip()

    return buffer


def _decode_next_bulk_payload(
    decoder: json.JSONDecoder,
    buffer: str,
) -> tuple[object | None, str, bool]:
    buffer = _consume_array_separators(buffer)

    if not buffer:
        return None, buffer, False

    if buffer[0] == "]":
        return None, buffer[1:], True

    try:
        payload, consumed = decoder.raw_decode(buffer)
    except json.JSONDecodeError:
        # Need more bytes for a complete JSON value.
        return None, buffer, False

    return payload, buffer[consumed:], False


def _iter_bulk_payload_records(
    payload: object,
) -> Generator[dict[str, list[DaySchedule | None]], None, None]:
    if isinstance(payload, dict):
        yield _parse_bulk_schedule_record(payload)
        return

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                logger.warning(
                    "Unexpected bulk item type in array payload: %s",
                    type(item),
                )
                continue
            yield _parse_bulk_schedule_record(item)
        return

    logger.warning("Unexpected bulk payload type: %s", type(payload))


class AdminClient:
    def __init__(self) -> None:
        self.api_url = settings.API_URL

        self.api_auth = httpx.BasicAuth(
            username=settings.API_USERNAME,
            password=settings.API_PASSWORD.get_secret_value(),
        )

        self.client = httpx.Client(
            auth=self.api_auth,
            base_url=str(self.api_url),
            timeout=httpx.Timeout(
                30.0,
            ),
            headers={
                "Content-Type": "application/json",
            },
        )

        self.async_client = httpx.AsyncClient(
            auth=self.api_auth,
            base_url=str(self.api_url),
            timeout=httpx.Timeout(
                30.0,
            ),
            headers={
                "Content-Type": "application/json",
            },
        )

    def get_chat(self, chat_id: str) -> Chat:
        response = self.client.get(url=f"/chat/{chat_id}")

        if response.status_code != httpx.codes.OK:
            reraise_for_status(response)

        return Chat.model_validate(response.json())

    def create_chat(self, chat_info: CreateChatRequest) -> Chat:
        response = self.client.post(
            url="/chat/",
            json=chat_info.model_dump(),
        )

        if response.status_code not in [httpx.codes.OK, httpx.codes.CREATED]:
            reraise_for_status(response)

        return Chat.model_validate(response.json())

    def get_or_create_chat(self, chat_info: CreateChatRequest) -> Chat:
        try:
            chat = self.get_chat(chat_info.platform_chat_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == httpx.codes.NOT_FOUND:
                chat = self.create_chat(chat_info)
            else:
                raise

        return chat

    def create_subscription(self, chat_id: str) -> Subscription:
        response = self.client.post(
            "/chat/subscription/",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return Subscription.model_validate(response.json())

    def get_subscription(self, chat_id: str) -> Subscription:
        response = self.client.get(
            "/chat/subscription/info",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        if response.status_code == httpx.codes.NOT_FOUND:
            raise SubscriptionNotFoundError(
                response=response,
                chat_id=chat_id,
            )

        reraise_for_status(response)

        return Subscription.model_validate(response.json())

    def add_group(self, chat_id: str, group_id: pydantic.UUID4) -> Subscription:
        response = self.client.post(
            f"/chat/subscription/info/group/{group_id}",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return Subscription.model_validate(response.json())

    def remove_group(self, chat_id: str, group_id: pydantic.UUID4) -> Subscription:
        response = self.client.delete(
            f"/chat/subscription/info/group/{group_id}",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return Subscription.model_validate(response.json())

    def add_teacher(self, chat_id: str, teacher_id: pydantic.UUID4) -> Subscription:
        response = self.client.post(
            f"/chat/subscription/info/teacher/{teacher_id}",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return Subscription.model_validate(response.json())

    def remove_teacher(self, chat_id: str, teacher_id: pydantic.UUID4) -> Subscription:
        response = self.client.delete(
            f"/chat/subscription/info/teacher/{teacher_id}",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return Subscription.model_validate(response.json())

    def toggle_subscription(self, chat_id: str) -> Subscription:
        response = self.client.patch(
            "/chat/subscription/status",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return Subscription.model_validate(response.json())

    async def bulk_schedule(  # noqa: C901
        self,
    ) -> AsyncGenerator[dict[str, list[DaySchedule | None]], None]:
        async with self.async_client.stream(
            method="GET",
            url="/chat/bulk/schedule",
            timeout=httpx.Timeout(600.0),
        ) as response:
            decoder = json.JSONDecoder()
            buffer = ""
            array_started = False
            array_finished = False

            async for chunk in response.aiter_text():
                buffer, array_started = _prepare_bulk_buffer(
                    buffer,
                    chunk,
                    array_started=array_started,
                )

                if not array_started:
                    continue

                while True:
                    payload, buffer, reached_array_end = _decode_next_bulk_payload(
                        decoder,
                        buffer,
                    )

                    if reached_array_end:
                        array_finished = True
                        break

                    if payload is None:
                        break

                    for record in _iter_bulk_payload_records(payload):
                        yield record

                if array_finished:
                    break

            if not array_started:
                logger.warning("bulk_schedule_async response was empty")
            elif not array_finished:
                logger.warning("bulk_schedule_async response ended before JSON array was closed")

            if array_finished and buffer.strip():
                logger.warning(
                    f"bulk_schedule_async response contained trailing data: {buffer[:256]!r}"
                )

    def schedule_tomorrow(self, chat_id: str) -> list[DaySchedule | None]:
        response = self.client.get(
            "/chat/schedule/tomorrow",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return [
            DaySchedule.model_validate(item) if item is not None else None
            for item in response.json()
        ]

    def schedule_today(self, chat_id: str) -> list[DaySchedule | None]:
        response = self.client.get(
            "/chat/schedule/today",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return [
            DaySchedule.model_validate(item) if item is not None else None
            for item in response.json()
        ]

    def schedule_day(self, chat_id: str, date: datetime.date) -> list[DaySchedule | None]:
        response = self.client.get(
            f"/chat/schedule/day/{date.isoformat()}",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return [
            DaySchedule.model_validate(item) if item is not None else None
            for item in response.json()
        ]

    def schedule_week(self, chat_id: str) -> list[WeekSchedule]:
        response = self.client.get(
            "/chat/schedule/week",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        reraise_for_status(response)

        return [WeekSchedule.model_validate(item) for item in response.json()]

    def read_faculties(self) -> FacultyPaginatedResponse:
        response = self.client.get(
            "/public/faculty/",
            # Too lazy to implement pagination for faculties
            params=FacultyPaginatedRequest(
                page=1,
                page_size=100,
            ).model_dump(),
        )

        reraise_for_status(response)

        data = FacultyPaginatedResponse.model_validate(response.json())

        if data.meta.has_next:
            raise ValueError("Too many faculties to read in one request")

        return data

    def read_faculty(self, faculty_id: pydantic.UUID4) -> Faculty | None:
        response = self.client.get(f"/public/faculty/{faculty_id}")

        if response.status_code == httpx.codes.NOT_FOUND:
            return None

        reraise_for_status(response)

        return Faculty.model_validate(response.json())

    def read_groups(
        self,
        page: int = 1,
        page_size: int = 10,
        faculty_id: pydantic.UUID4 | None = None,
    ) -> GroupPaginatedResponse:
        response = self.client.get(
            "/public/group/",
            params=GroupPaginatedRequest(
                page=page,
                page_size=page_size,
                faculty_id=faculty_id,
            ).model_dump(),
        )

        reraise_for_status(response)

        return GroupPaginatedResponse.model_validate(response.json())

    def read_departments(self) -> DepartmentPaginatedResponse:
        response = self.client.get(
            "/public/department/",
            # Too lazy to implement pagination for departments
            params=DepartmentPaginatedRequest(
                page=1,
                page_size=100,
            ).model_dump(),
        )

        reraise_for_status(response)

        data = DepartmentPaginatedResponse.model_validate(response.json())

        if data.meta.has_next:
            raise ValueError("Too many departments to read in one request")

        return data

    def read_department(self, department_id: pydantic.UUID4) -> Department | None:
        response = self.client.get(f"/public/department/{department_id}")

        if response.status_code == httpx.codes.NOT_FOUND:
            return None

        reraise_for_status(response)

        return Department.model_validate(response.json())

    def read_teachers(
        self,
        page: int = 1,
        page_size: int = 10,
        department_id: pydantic.UUID4 | None = None,
    ) -> TeacherPaginatedResponse:
        response = self.client.get(
            "/public/teacher/",
            params=TeacherPaginatedRequest(
                page=page,
                page_size=page_size,
                department_id=department_id,
            ).model_dump(),
        )

        reraise_for_status(response)

        return TeacherPaginatedResponse.model_validate(response.json())

    def read_message_campaign(
        self,
        message_campaign_id: pydantic.UUID4,
    ) -> MessageCampaign:
        response = self.client.get(f"/chat/message_campaign/{message_campaign_id}")

        reraise_for_status(response)

        return MessageCampaign.model_validate(response.json())
