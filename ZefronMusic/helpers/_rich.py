# ==============================================================================
# _rich.py - Bot API 10.3 Rich Message Helpers
# ==============================================================================
# Uses Kurigram's Bot API 10.3-compatible rich-message methods while keeping a
# normal-message fallback for older Telegram clients or transient API failures.
# ==============================================================================

from typing import Optional

from pyrogram import errors, types

from ZefronMusic import app, logger


class Rich:
    async def send(
        self,
        chat_id: int,
        html: str,
        reply_markup=None,
    ) -> Optional[types.Message]:
        """Send a rich message, falling back to the regular message API."""
        try:
            return await app.send_rich_message(
                chat_id=chat_id,
                rich_message=types.InputRichMessage(html=html),
                reply_markup=reply_markup,
            )
        except Exception as exc:
            logger.debug("Rich message unavailable, using regular message: %s", exc)
            return await app.send_message(
                chat_id=chat_id,
                text=html,
                reply_markup=reply_markup,
            )

    async def ephemeral(
        self,
        query: types.CallbackQuery,
        html: str,
    ) -> bool:
        """Show a callback response only to its requesting user."""
        if not query.message or not query.from_user:
            return False

        try:
            await app.send_rich_message(
                chat_id=query.message.chat.id,
                rich_message=types.InputRichMessage(html=html),
                receiver_user_id=query.from_user.id,
                callback_query_id=query.id,
            )
            return True
        except (errors.QueryIdInvalid, errors.RPCError):
            return False
        except Exception as exc:
            logger.debug("Ephemeral message unavailable: %s", exc)
            return False


rich = Rich()