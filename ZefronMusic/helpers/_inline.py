# ==============================================================================
# _inline.py - Keyboard Buttons
# ==============================================================================
# Helper methods to generate all the inline keyboards (play controls, help menus, etc).
# ==============================================================================

from pyrogram import enums, types

from ZefronMusic import app, config, lang


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = self._styled_button

    @staticmethod
    def _styled_button(*args, **kwargs):
        """Create Telegram-native 10.3 buttons with clear visual hierarchy."""
        text = str(kwargs.get("text", "")).lower()
        callback = str(kwargs.get("callback_data", "")).lower()
        danger_words = ("cancel", "close", "delete", "stop", "revert")
        primary_words = (
            "add me",
            "help",
            "open in",
            "play now",
            "resume",
            "watch",
        )

        # Bot API 10.3 treats the default style as a neutral secondary pill.
        # Older code used SUCCESS for many ordinary actions, which made every
        # keyboard look equally loud. Keep danger buttons red, promote only
        # true primary actions, and keep the rest neutral.
        if kwargs.get("style") == enums.ButtonStyle.SUCCESS:
            kwargs["style"] = (
                enums.ButtonStyle.PRIMARY
                if any(word in text or word in callback for word in primary_words)
                else enums.ButtonStyle.DEFAULT
            )
        elif "style" not in kwargs:
            if any(word in text or word in callback for word in danger_words):
                kwargs["style"] = enums.ButtonStyle.DANGER
            elif any(word in text or word in callback for word in primary_words):
                kwargs["style"] = enums.ButtonStyle.PRIMARY
            else:
                kwargs["style"] = enums.ButtonStyle.DEFAULT

        return types.InlineKeyboardButton(*args, **kwargs)

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, callback_data=f"cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(text=status, callback_data=f"controls status {chat_id}")]
            )
        elif timer:
            keyboard.append(
                [self.ikb(text=timer, callback_data=f"controls status {chat_id}")]
            )

        if not remove:
            # Seek buttons row
            keyboard.append(
                [
                    self.ikb(
                        text="« 30", callback_data=f"controls seek_back_30 {chat_id}"
                    ),
                    self.ikb(
                        text="« 10", callback_data=f"controls seek_back_10 {chat_id}"
                    ),
                    self.ikb(
                        text="10 »", callback_data=f"controls seek_forward_10 {chat_id}"
                    ),
                    self.ikb(
                        text="30 »", callback_data=f"controls seek_forward_30 {chat_id}"
                    ),
                ]
            )
            # Main control buttons row
            keyboard.append(
                [
                    self.ikb(
                        text="▷",
                        callback_data=f"controls resume {chat_id}",
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                    self.ikb(
                        text="II",
                        callback_data=f"controls pause {chat_id}",
                        style=enums.ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="↻",
                        callback_data=f"controls replay {chat_id}",
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                    self.ikb(
                        text="‣‣I",
                        callback_data=f"controls skip {chat_id}",
                        style=enums.ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="▢",
                        callback_data=f"controls stop {chat_id}",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ]
            )
            # Delete button as full-width button at bottom
            keyboard.append(
                [
                    self.ikb(
                        text="ᴅᴇʟᴇᴛᴇ",
                        callback_data=f"controls close {chat_id}",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ]
            )
        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text="ʙᴀᴄᴋ", callback_data="help_main"),
                ]
            ]
        else:
            # Help menu with categorized buttons (3 per row)
            rows = [
                [
                    self.ikb(text="ᴀᴅᴍɪɴꜱ", callback_data="help_admins"),
                    self.ikb(
                        text="ᴀᴜᴛʜ",
                        callback_data="help_auth",
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                    self.ikb(
                        text="ʙʀᴏᴀᴅᴄᴀꜱᴛ",
                        callback_data="help_broadcast",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ],
                [
                    self.ikb(text="ʟᴏᴏᴘ", callback_data="help_loop"),
                    self.ikb(
                        text="ᴘʟᴀʏ",
                        callback_data="help_play",
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                    self.ikb(text="ǫᴜᴇᴜᴇ", callback_data="help_queue"),
                ],
                [
                    self.ikb(
                        text="ʙʟ-ᴄʜᴀᴛ",
                        callback_data="help_blchat",
                        style=enums.ButtonStyle.DANGER,
                    ),
                    self.ikb(
                        text="ʙʟ-ᴜꜱᴇʀ",
                        callback_data="help_bluser",
                        style=enums.ButtonStyle.DANGER,
                    ),
                    self.ikb(text="ꜱᴇᴇᴋ", callback_data="help_seek"),
                ],
                [
                    self.ikb(
                        text="ᴘɪɴɢ",
                        callback_data="help_ping",
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                    self.ikb(text="ꜱᴛᴀᴛꜱ", callback_data="help_stats"),
                    self.ikb(
                        text="ꜱᴜᴅᴏ",
                        callback_data="help_sudo",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ],
                [
                    self.ikb(text="ʙᴀᴄᴋ", callback_data="start"),
                ],
            ]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text="📢 Channel",
                        url=config.SUPPORT_CHANNEL,
                        style=enums.ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="🆘 Support",
                        url=config.SUPPORT_CHAT,
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                ],
                [
                    self.ikb(
                        text="➕ Add Me to Your Group",
                        url=f"https://t.me/{app.username}?startgroup=true",
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                ],
            ]
        )

    def radio_markup(self, stations: dict, page: int = 0) -> types.InlineKeyboardMarkup:
        """Paginated genre picker for live radio streams."""
        station_items = list(stations.items())
        page_size = 6
        page_count = max(1, (len(station_items) + page_size - 1) // page_size)
        page = max(0, min(page, page_count - 1))
        page_items = station_items[page * page_size : (page + 1) * page_size]

        rows = []
        for index in range(0, len(page_items), 2):
            row = []
            for key, station in page_items[index : index + 2]:
                row.append(
                    self.ikb(
                        text=station["label"],
                        callback_data=f"radio:{key}",
                        style=(
                            enums.ButtonStyle.PRIMARY
                            if (page * page_size + index) % 3 != 1
                            else enums.ButtonStyle.DEFAULT
                        ),
                    )
                )
            rows.append(row)

        navigation = []
        if page > 0:
            navigation.append(
                self.ikb(
                    text="⬅️ Back",
                    callback_data=f"radio:page:{page - 1}",
                    style=enums.ButtonStyle.PRIMARY,
                )
            )
        if page < page_count - 1:
            navigation.append(
                self.ikb(
                    text="Next ➡️",
                    callback_data=f"radio:page:{page + 1}",
                    style=enums.ButtonStyle.SUCCESS,
                )
            )
        if navigation:
            rows.append(navigation)

        rows.append(
            [
                self.ikb(
                    text="❌ Close",
                    callback_data="radio:close",
                    style=enums.ButtonStyle.DANGER,
                ),
            ]
        )
        return self.ikm(rows)

    def radio_copy_markup(self, stream_url: str) -> types.InlineKeyboardMarkup:
        """Native Bot API copy-text button for a live radio URL."""
        return self.ikm(
            [
                [
                    self.ikb(
                        text="📋 Copy Stream",
                        copy_text=stream_url,
                        style=enums.ButtonStyle.SUCCESS,
                    )
                ]
            ]
        )

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text="▷",
                        callback_data=f"controls resume {chat_id}",
                        style=enums.ButtonStyle.SUCCESS,
                    ),
                    self.ikb(
                        text="∣ ∣",
                        callback_data=f"controls pause {chat_id}",
                        style=enums.ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text=" >>",
                        callback_data=f"controls skip {chat_id}",
                        style=enums.ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="▣",
                        callback_data=f"controls stop {chat_id}",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ],
                [
                    self.ikb(
                        text="ᴅᴇʟᴇᴛᴇ",
                        callback_data=f"controls close {chat_id}",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ],
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜",
                        callback_data=f"controls status {chat_id}",
                    ),
                    self.ikb(text=admin_only, callback_data="playmode"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text=lang["help"],
                    callback_data="help",
                    style=enums.ButtonStyle.PRIMARY,
                )
            ],
            [
                self.ikb(
                    text=lang["support"],
                    url=config.SUPPORT_CHAT,
                    style=enums.ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text=lang["channel"],
                    url=config.SUPPORT_CHANNEL,
                    style=enums.ButtonStyle.DEFAULT,
                ),
            ],
        ]
        if private:
            rows += [
                [
                    self.ikb(
                        text="Owner",
                        url="https://t.me/II_ALONE_III",
                        style=enums.ButtonStyle.SUCCESS,
                    )
                ]
            ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="ᴄᴏᴘʏ ʟɪɴᴋ", copy_text=link),
                    self.ikb(text="ᴏᴘᴇɴ ɪɴ ʏᴏᴜᴛᴜʙᴇ", url=link),
                ],
            ]
        )
