# ==============================================================================
# start.py - Basics
# ==============================================================================
# Essential user-facing commands: /start, /help, /settings, etc.
# ==============================================================================

from pyrogram import enums, errors, filters, types

from ZefronMusic import app, config, db, lang
from ZefronMusic.helpers import (
    bot_api,
    buttons,
    help_rich_message,
    start_rich_message,
    utils,
)


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    try:
        await bot_api.send_rich_message(
            chat_id=m.chat.id,
            rich_message=help_rich_message(m.lang, image_url=config.START_IMG),
        )
    except Exception:
        try:
            await m.reply_photo(
                photo=config.START_IMG,  # Use same image as start command
                caption=m.lang["help_menu"],
                reply_markup=buttons.help_markup(m.lang),
                quote=False,
            )
        except Exception:
            # Fallback to text if photo/rich message is unavailable.
            await m.reply_text(
                text=m.lang["help_menu"],
                reply_markup=buttons.help_markup(m.lang),
                quote=True,
            )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    # Auto-delete command message in group chats
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass
    
    # Skip if message from channel or anonymous admin
    if not message.from_user:
        return

    # Check if user is blacklisted
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    # If /start help, show help menu
    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    # Determine if chat is private or group
    private = message.chat.type == enums.ChatType.PRIVATE

    # Choose appropriate welcome message
    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else message.lang["start_gp"].format(app.name)
    )

    try:
        await bot_api.send_rich_message(
            chat_id=message.chat.id,
            rich_message=start_rich_message(
                message.lang,
                app.username,
                app.name,
                message.from_user.first_name,
                private,
                config.SUPPORT_CHAT,
                config.SUPPORT_CHANNEL,
                config.START_IMG,
            ),
        )
    except Exception:
        key = buttons.start_key(message.lang, private)
        try:
            await message.reply_photo(
                photo=config.START_IMG,
                caption=_text,
                reply_markup=key,
                quote=False,
            )
        except errors.ChatSendPhotosForbidden:
            # If photos are not allowed, send text only
            await message.reply_text(
                text=_text,
                reply_markup=key,
                quote=False,
            )

    # For private chats, add user to database if new
    if private:
        if await db.is_user(message.from_user.id):
            return  # User already exists, no need to add
        # Log new user to logger group
        await utils.send_log(message)
        # Add user to database
        return await db.add_user(message.from_user.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    # Auto-delete command message
    try:
        await message.delete()
    except Exception:
        pass
    
    admin_only = await db.get_play_mode(message.chat.id)  # Get play mode setting
    _language = "en"
    await utils.safe_text(
        message,
        message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, _language, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    # Only work in supergroups (not basic groups)
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    # Check each new member
    for member in message.new_chat_members:
        if member.id == app.id:  # Bot itself was added
            if await db.is_chat(message.chat.id):
                return  # Chat already in database
            # Add chat to database (log is sent from new_chat.py with photo)
            await db.add_chat(message.chat.id)
