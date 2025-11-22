import json
from typing import Generator
import httpx
import pydantic
from ontu_schedule_bot.settings import settings
from ontu_schedule_bot.third_party.admin.schemas import Chat, CreateChatRequest, DaySchedule, Subscription, WeekSchedule

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
            timeout=httpx.Timeout(30.0,)
        )
    
    def get_chat(self, chat_id: str) -> Chat:
        response = self.client.get(
            url=f"/chat/{chat_id}"
        )

        if response.status_code != 200:
            response.raise_for_status()

        return Chat.model_validate(response.json())

    def create_chat(self, chat_info: CreateChatRequest) -> Chat:
        response = self.client.post(
            url="/chat/",
            json=chat_info.model_dump(),
        )

        if response.status_code not in [200, 201]:
            response.raise_for_status()

        return Chat.model_validate(response.json())

    def get_or_create_chat(self, chat_info: CreateChatRequest) -> Chat:
        try:
            chat = self.get_chat(chat_info.platform_chat_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                chat = self.create_chat(chat_info)
            else:
                raise
        
        return chat

    def get_subscription(self, chat_id: str) -> Subscription:
        response = self.client.get(
            "/chat/subscription/info",
            headers={
                "X-Chat-ID": chat_id,
            }
        )

        response.raise_for_status()

        return Subscription.model_validate(response.json())


    def add_group(self, chat_id: str, group_id: pydantic.UUID4) -> Subscription:
        response = self.client.post(
            f"/chat/subscription/info/group/{group_id}",
            headers={
                "X-Chat-ID": chat_id,
            }
        )

        response.raise_for_status()

        return Subscription.model_validate(response.json())

    def remove_group(self, chat_id: str, group_id: pydantic.UUID4) -> Subscription:
        response = self.client.delete(
            f"/chat/subscription/info/group/{group_id}",
            headers={
                "X-Chat-ID": chat_id,
            }
        )

        response.raise_for_status()

        return Subscription.model_validate(response.json())

    def add_teacher(self, chat_id: str, teacher_id: pydantic.UUID4) -> Subscription:
        response = self.client.post(
            f"/chat/subscription/info/teacher/{teacher_id}",
            headers={
                "X-Chat-ID": chat_id,
            }
        )

        response.raise_for_status()

        return Subscription.model_validate(response.json())

    def remove_teacher(self, chat_id: str, teacher_id: pydantic.UUID4) -> Subscription:
        response = self.client.delete(
            f"/chat/subscription/info/teacher/{teacher_id}",
            headers={
                "X-Chat-ID": chat_id,
            }
        )

        response.raise_for_status()

        return Subscription.model_validate(response.json())

    def toggle_subscription(self, chat_id: str) -> Subscription:
        response = self.client.patch(
            "/chat/subscription/status",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        response.raise_for_status()

        return Subscription.model_validate(response.json())

    def bulk_schedule(self) -> Generator[dict[str, list[DaySchedule | None]], None, None]:
        with self.client.stream(
            method="GET",
            url="/chat/bulk/schedule",
        ) as response:
            for chunk in response.iter_bytes():
                try:
                    data = json.loads(chunk)
                except json.JSONDecodeError as e:
                    # TODO: Use logging
                    print(e, chunk)
                    continue

                yield {key: [DaySchedule.model_validate(item) if item is not None else None for item in value] for key, value in data.items()}

    def schedule_tomorrow(self, chat_id: str) -> list[DaySchedule | None]:
        response = self.client.get(
            "/chat/schedule/tomorrow",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        response.raise_for_status()

        return [DaySchedule.model_validate(item) if item is not None else None for item in response.json()]

    def schedule_today(self, chat_id: str) -> list[DaySchedule | None]:
        response = self.client.get(
            "/chat/schedule/today",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        response.raise_for_status()

        return [DaySchedule.model_validate(item) if item is not None else None for item in response.json()]

    def schedule_week(self, chat_id: str) -> list[WeekSchedule]:
        response = self.client.get(
            "/chat/schedule/week",
            headers={
                "X-Chat-ID": chat_id,
            },
        )

        response.raise_for_status()

        return [WeekSchedule.model_validate(item) for item in response.json()]