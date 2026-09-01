# ==============================================================================
# _rich_layouts.py - Embedded Bot API 10.3 Button Layouts
# ==============================================================================

from html import unescape
import re


def _plain(value: str) -> str:
    """Keep existing localized copy readable inside a rich paragraph block."""
    return unescape(re.sub(r"<[^>]+>", "", value)).strip()


def _button(text: str, *, callback_data: str = None, url: str = None, style: str = None) -> dict:
    button = {"text": text}
    if callback_data is not None:
        button["callback_data"] = callback_data
    if url is not None:
        button["url"] = url
    # Neutral is Telegram's default when no style is provided. Omitting it is
    # more compatible than sending a version-specific "default" style value.
    if style is not None and style != "default":
        button["style"] = style
    return button


def _button_row(*buttons: dict) -> dict:
    return {
        "type": "buttons",
        "buttons": list(buttons),
        "align": "center",
    }


def _photo_block(image_url: str) -> dict:
    return {
        "type": "photo",
        "photo": {
            "type": "photo",
            "media": image_url,
        },
    }


def _blockquote_block(value: str) -> dict:
    """Render every rich text section as a Telegram block quotation."""
    return {
        "type": "blockquote",
        "blocks": [
            {
                "type": "paragraph",
                "text": _plain(value),
            }
        ],
    }


def start_rich_message(
    lang: dict,
    app_username: str,
    app_name: str,
    user_name: str,
    private: bool,
    support_chat: str,
    support_channel: str,
    image_url: str = None,
) -> dict:
    text_key = "start_pm" if private else "start_gp"
    blocks = []
    if image_url:
        blocks.append(_photo_block(image_url))
    blocks.extend(
        [
            _blockquote_block(lang[text_key].format(user_name, app_name)),
            _button_row(
                _button(lang["help"], callback_data="help", style="primary"),
            ),
            _button_row(
                _button(lang["support"], url=support_chat, style="primary"),
                _button(lang["channel"], url=support_channel, style="primary"),
            ),
        ]
    )
    if private:
        blocks.append(
            _button_row(
                _button("Owner", url="https://t.me/II_ALONE_III", style="primary"),
            )
        )
    return {"blocks": blocks}


def help_rich_message(
    lang: dict,
    *,
    category_text: str = None,
    back: bool = False,
    image_url: str = None,
) -> dict:
    blocks = []
    if image_url:
        blocks.append(_photo_block(image_url))
    blocks.append(
        _blockquote_block(category_text or lang["help_menu"])
    )
    if back:
        blocks.append(
            _button_row(
                _button("ʙᴀᴄᴋ", callback_data="help_main", style="primary"),
            )
        )
        return {"blocks": blocks}

    rows = [
        (
            _button("ᴀᴅᴍɪɴꜱ", callback_data="help_admins", style="primary"),
            _button("ᴀᴜᴛʜ", callback_data="help_auth", style="primary"),
            _button("ʙʀᴏᴀᴅᴄᴀꜱᴛ", callback_data="help_broadcast", style="primary"),
        ),
        (
            _button("ʟᴏᴏᴘ", callback_data="help_loop", style="primary"),
            _button("ᴘʟᴀʏ", callback_data="help_play", style="primary"),
            _button("ǫᴜᴇᴜᴇ", callback_data="help_queue", style="primary"),
        ),
        (
            _button("ʙʟ-ᴄʜᴀᴛ", callback_data="help_blchat", style="primary"),
            _button("ʙʟ-ᴜꜱᴇʀ", callback_data="help_bluser", style="primary"),
            _button("ꜱᴇᴇᴋ", callback_data="help_seek", style="primary"),
        ),
        (
            _button("ᴘɪɴɢ", callback_data="help_ping", style="primary"),
            _button("ꜱᴛᴀᴛꜱ", callback_data="help_stats", style="primary"),
            _button("ꜱᴜᴅᴏ", callback_data="help_sudo", style="primary"),
        ),
    ]
    blocks.extend(_button_row(*row) for row in rows)
    blocks.append(_button_row(_button("ʙᴀᴄᴋ", callback_data="start", style="primary")))
    return {"blocks": blocks}


def _playback_control_blocks(chat_id: int, *, status: str = None, timer: str = None) -> list:
    """Return the colorful rich-message controls used by a playing track."""
    blocks = []
    label = status or timer
    if label:
        blocks.append(
            _button_row(
                _button(
                    label,
                    callback_data=f"controls status {chat_id}",
                    style="primary",
                )
            )
        )

    blocks.append(
        _button_row(
            _button("« 30", callback_data=f"controls seek_back_30 {chat_id}", style="primary"),
            _button("« 10", callback_data=f"controls seek_back_10 {chat_id}", style="primary"),
            _button("10 »", callback_data=f"controls seek_forward_10 {chat_id}", style="primary"),
            _button("30 »", callback_data=f"controls seek_forward_30 {chat_id}", style="primary"),
        )
    )
    blocks.append(
        _button_row(
            _button("▶️", callback_data=f"controls resume {chat_id}", style="primary"),
            _button("⏸️", callback_data=f"controls pause {chat_id}", style="primary"),
            _button("🔁", callback_data=f"controls replay {chat_id}", style="primary"),
            _button("⏭️", callback_data=f"controls skip {chat_id}", style="primary"),
            _button("⏹️", callback_data=f"controls stop {chat_id}", style="danger"),
        )
    )
    blocks.append(
        _button_row(
            _button(
                "🗑️ ᴅᴇʟᴇᴛᴇ",
                callback_data=f"controls close {chat_id}",
                style="danger",
            )
        )
    )
    return blocks


def playback_rich_message(
    html: str,
    chat_id: int,
    *,
    image_url: str = None,
    status: str = None,
    timer: str = None,
) -> dict:
    """Build a rich now-playing message with embedded playback controls."""
    blocks = []
    if image_url:
        blocks.append(_photo_block(image_url))
    blocks.append(_blockquote_block(html))
    blocks.extend(_playback_control_blocks(chat_id, status=status, timer=timer))
    return {"blocks": blocks}


def queued_playback_rich_message(html: str, chat_id: int) -> dict:
    """Build a rich queued-track message with embedded action controls."""
    return {
        "blocks": [
            _blockquote_block(html),
            _button_row(
                _button("▶️", callback_data=f"controls resume {chat_id}", style="primary"),
                _button("⏸️", callback_data=f"controls pause {chat_id}", style="primary"),
                _button("⏭️", callback_data=f"controls skip {chat_id}", style="primary"),
                _button("⏹️", callback_data=f"controls stop {chat_id}", style="danger"),
            ),
            _button_row(
                _button(
                    "🗑️ ᴅᴇʟᴇᴛᴇ",
                    callback_data=f"controls close {chat_id}",
                    style="danger",
                )
            ),
        ]
    }