import base64
import inspect
import pickle

import pydantic
from redis.asyncio import Redis
from telegram.ext import BasePersistence, PersistenceInput
from telegram.ext._utils.types import BD, CD, UD, CDCData, ConversationDict, ConversationKey


class RedisPersistence(BasePersistence[UD, CD, BD]):
    def __init__(
        self,
        redis_client: Redis,
        store_data: PersistenceInput | None = None,
        update_interval: float = 60,
    ) -> None:
        super().__init__(store_data=store_data, update_interval=update_interval)
        self.redis_client = redis_client

    @classmethod
    def create_redis_client(cls, url: pydantic.RedisDsn) -> Redis:
        return Redis.from_url(url=str(url))

    @property
    def user_data_key(self) -> str:
        return "user_data_"

    @property
    def chat_data_key(self) -> str:
        return "chat_data_"

    @property
    def bot_data_key(self) -> str:
        return "bot_data"

    @property
    def conversations_key(self) -> str:
        return "conversations_"

    @property
    def callback_data_key(self) -> str:
        return "callback_data"

    @staticmethod
    def dump_data(data: object) -> bytes:
        return pickle.dumps(data)

    @staticmethod
    def load_data(data: bytes) -> object:
        return pickle.loads(data)

    async def get_user_data(self) -> dict[int, UD]:
        users: dict[int, UD] = {}

        async for key in self.redis_client.scan_iter(match=f"{self.user_data_key}*"):
            value = await self.redis_client.get(key)
            if not value:
                continue

            # Key format: user_data_{user_id}
            if isinstance(key, bytes):
                key = key.decode("utf-8")

            try:
                user_id_str = str(key).removeprefix(self.user_data_key)
                user_id = int(user_id_str)
            except Exception:
                # Skip malformed keys
                continue

            users[user_id] = self.load_data(value)

        return users

    async def get_chat_data(self) -> dict[int, CD]:
        chats: dict[int, CD] = {}

        async for key in self.redis_client.scan_iter(match=f"{self.chat_data_key}*"):
            value = await self.redis_client.get(key)
            if not value:
                continue

            # Key format: chat_data_{chat_id}
            if isinstance(key, bytes):
                key = key.decode("utf-8")

            try:
                chat_id_str = str(key).removeprefix(self.chat_data_key)
                chat_id = int(chat_id_str)
            except Exception:
                # Skip malformed keys
                continue

            chats[chat_id] = self.load_data(value)

        return chats

    async def get_bot_data(self) -> BD:
        data_bytes = await self.redis_client.get(self.bot_data_key)

        if not data_bytes:
            return {}

        return self.load_data(data_bytes)

    async def get_conversations(self, name: str) -> ConversationDict:
        raw_conversations = self.redis_client.hgetall(f"{self.conversations_key}{name}")

        if inspect.isawaitable(raw_conversations):
            raw_conversations = await raw_conversations

        conversations: ConversationDict = {}
        for key_bytes, data_b64 in raw_conversations.items():
            key = key_bytes

            if isinstance(key_bytes, bytes):
                key = key_bytes.decode("utf-8")

            key = ConversationKey(key)
            data_bytes = base64.b64decode(data_b64)
            data = self.load_data(data_bytes)

            conversations[key] = data

        return conversations

    async def update_conversation(
        self,
        name: str,
        key: ConversationKey,
        new_state: object | None,
    ) -> None:
        data_bytes = self.dump_data(new_state)

        await self.redis_client.hset(
            name=f"{self.conversations_key}{name}",
            key=str(key),
            value=base64.b64encode(data_bytes).decode("utf-8"),
        )

    async def update_user_data(self, user_id: int, data: UD) -> None:
        data_bytes = self.dump_data(data)

        await self.redis_client.set(f"{self.user_data_key}{user_id}", data_bytes)

    async def update_chat_data(self, chat_id: int, data: CD) -> None:
        data_bytes = self.dump_data(data)

        await self.redis_client.set(f"{self.chat_data_key}{chat_id}", data_bytes)

    async def update_bot_data(self, data: BD) -> None:
        data_bytes = self.dump_data(data)

        await self.redis_client.set(self.bot_data_key, data_bytes)

    async def update_callback_data(self, data: CDCData) -> None:
        data_bytes = self.dump_data(data)

        await self.redis_client.set(self.callback_data_key, data_bytes)

    async def get_callback_data(self) -> CDCData | None:
        data_bytes = await self.redis_client.get(self.callback_data_key)
        if not data_bytes:
            return None
        return self.load_data(data_bytes)

    async def drop_chat_data(self, chat_id: int) -> None:
        await self.redis_client.delete(f"{self.chat_data_key}{chat_id}")

    async def drop_user_data(self, user_id: int) -> None:
        await self.redis_client.delete(f"{self.user_data_key}{user_id}")

    async def refresh_user_data(self, user_id: int, user_data: UD) -> None:
        key = f"{self.user_data_key}{user_id}"
        data_bytes = await self.redis_client.get(key)
        if not data_bytes:
            # Nothing in redis, clear local view
            try:
                user_data.clear()  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                # If not dict-like, just return
                return
            return

        latest: UD = self.load_data(data_bytes)  # type: ignore[assignment]
        # Update in-place for the provided dict-like object
        try:
            user_data.clear()  # type: ignore[attr-defined]
            user_data.update(latest)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            # Fallback: replace reference where possible
            # If object isn't dict-like, do nothing
            return

    async def refresh_chat_data(self, chat_id: int, chat_data: CD) -> None:
        key = f"{self.chat_data_key}{chat_id}"
        data_bytes = await self.redis_client.get(key)
        if not data_bytes:
            try:
                chat_data.clear()  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                return
            return

        latest: CD = self.load_data(data_bytes)  # type: ignore[assignment]
        try:
            chat_data.clear()  # type: ignore[attr-defined]
            chat_data.update(latest)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return

    async def refresh_bot_data(self, bot_data: BD) -> None:
        data_bytes = await self.redis_client.get(self.bot_data_key)
        if not data_bytes:
            try:
                bot_data.clear()  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                return
            return

        latest: BD = self.load_data(data_bytes)  # type: ignore[assignment]
        try:
            bot_data.clear()  # type: ignore[attr-defined]
            bot_data.update(latest)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return

    async def flush(self) -> None:
        await self.redis_client.close()
