# ==============================================================================
# _bot_api.py - Focused Bot API 10.3 HTTP Client
# ==============================================================================
# The music bot uses Kurigram/MTProto for updates and voice-chat operations.
# Rich Message buttons are a Bot API surface, so this small client is kept
# alongside it instead of replacing the existing Telegram framework.
# ==============================================================================

from typing import Any, Dict

import aiohttp


class BotApiError(RuntimeError):
    """Raised when Telegram rejects a Bot API request."""


class BotApi10:
    def __init__(self, token: str):
        self._url = f"https://api.telegram.org/bot{token}"

    async def _request(self, method: str, payload: Dict[str, Any]) -> Any:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self._url}/{method}",
                json=payload,
            ) as response:
                data = await response.json(content_type=None)

        if response.status >= 400 or not data.get("ok"):
            description = data.get("description", "Telegram rejected the request")
            raise BotApiError(f"{method}: {description}")

        return data.get("result")

    async def send_rich_message(
        self,
        chat_id: int,
        rich_message: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await self._request(
            "sendRichMessage",
            {
                "chat_id": chat_id,
                "rich_message": rich_message,
            },
        )

    async def edit_rich_message(
        self,
        chat_id: int,
        message_id: int,
        rich_message: Dict[str, Any],
    ) -> Any:
        return await self._request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "rich_message": rich_message,
            },
        )