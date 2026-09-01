# ==============================================================================
# radio.py - Live Radio
# ==============================================================================
# Opens a paginated station picker and streams the selected station directly in
# the current voice chat.  Radio is intentionally available to every member;
# only playback controls remain admin/authorized-user restricted.
# ==============================================================================

from pyrogram import enums, errors, filters, types
from html import unescape
import re

from ZefronMusic import app, config, db, lang, logger, queue, tune
from ZefronMusic.helpers import Track, bot_api, buttons, rich


# Public streams.  Keep the callback key short; the full URL never goes into
# Telegram callback data.
RADIO_STATIONS = {
    # Short aliases requested for the public radio picker.
    "bollywood": {
        "label": "Bolly",
        "url": "https://drive.uber.radio/uber/bollywoodnow/icecast.audio",
    },
    # Page 1: Bollywood, ordered from new to old.
    "bollywood_new": {
        "label": "Bolly New",
        "url": "https://drive.uber.radio/uber/bollywoodnow/icecast.audio",
    },
    "new": {
        "label": "New",
        "url": "https://drive.uber.radio/uber/bollywoodnow/icecast.audio",
    },
    "hindi": {
        "label": "Hindi",
        "url": "https://azuracast.vibesounds.in:8010/radio.mp3",
    },
    "mirchi": {"label": "Mirchi", "url": "http://162.244.80.118:9460/stream.mp3"},
    "love": {
        "label": "Love",
        "url": "https://nl4.mystreaming.net/uber/bollywoodlove/icecast.audio",
    },
    "90s": {
        "label": "90s",
        "url": "https://2.mystreaming.net/uber/bollywood2000s/icecast.audio",
    },
    "2000s": {
        "label": "00s",
        "url": "https://2.mystreaming.net/uber/bollywood2000s/icecast.audio",
    },
    "old": {
        "label": "Old",
        "url": "https://2.mystreaming.net/uber/bollywood2000s/icecast.audio",
    },
    "bollywood_old": {
        "label": "Bolly Old",
        "url": "https://2.mystreaming.net/uber/bollywood2000s/icecast.audio",
    },
    "2010s": {
        "label": "10s",
        "url": "https://drive.uber.radio/uber/bollywood2010s/icecast.audio",
    },
    "desi": {"label": "Desi", "url": "https://streamer.radio.co/se30891e37/listen"},
    "air": {
        "label": "AIR",
        "url": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio001/chunklist.m3u8",
    },
    "punjabi": {"label": "Punjabi", "url": "https://stream.zeno.fm/1mwx0wv629duv"},
    "haryanvi": {"label": "Haryanvi", "url": "https://stream.zeno.fm/ryektectsf9uv"},
    "english": {
        "label": "English",
        "url": "https://media-ssl.musicradio.com/CapitalUK",
    },
    "rajasthani": {
        "label": "Rajasthani",
        "url": "https://streamasiacdn.atc-labs.com/jaipurradio.aac",
    },
    "bollywood_2010s": {
        "label": "10s Bolly",
        "url": "https://drive.uber.radio/uber/bollywood2010s/icecast.audio",
    },
    "hindi_2000s": {
        "label": "00s Bolly",
        "url": "https://drive.uber.radio/uber/bollywood2000s/icecast.audio",
    },
    "radio_bollywood_hits": {
        "label": "Hits Bolly",
        "url": "https://stream.zeno.fm/143d7gty24zuv",
    },
    "hindi_90s": {"label": "90s Bolly", "url": "https://stream.zeno.fm/rm4i9pdex3cuv"},
    "bollywood_classics": {
        "label": "Retro Bolly",
        "url": "https://stream.zeno.fm/6n6ewddtad0uv",
    },
    # Page 2: new Haryanvi first, then two old Haryanvi choices.
    "haryanvi_kasoot": {
        "label": "New Haryanvi",
        "url": "https://azuracast.radiokasoot.com/radio/8000/listen",
    },
    "haryanvi_khas": {
        "label": "Hary Hits",
        "url": "https://puma.streemlion.com:4130/stream",
    },
    "haryanvi_maharani": {
        "label": "Hary Mix",
        "url": "https://streamasiacdn.atc-labs.com/radiomaharani.aac",
    },
    "haryanvi_desi": {
        "label": "Hary Fresh",
        "url": "https://stream.zeno.fm/0r0xa792kwzuv",
    },
    "haryanvi_old": {
        "label": "Old Hary",
        "url": "https://stream.zeno.fm/7yhq985hnxhvv",
    },
    "haryanvi_gold": {
        "label": "Hary Gold",
        "url": "https://stream.zeno.fm/yz0ncx9gha0uv",
    },
    # Page 3: new Punjabi first, then two old Punjabi choices.
    "punjabi_bol": {
        "label": "New Punjabi",
        "url": "https://bolpunjabi-ekamsoftware.radioca.st/stream",
    },
    "punjabi_britasia": {
        "label": "Punj Hits",
        "url": "https://s4.radio.co/sfefce156f/listen",
    },
    "punjabi_risham": {
        "label": "Punj Mix",
        "url": "https://stream.zeno.fm/4pd041xv1a0uv",
    },
    "punjabi_desi": {
        "label": "Punj Fresh",
        "url": "https://stream.zenolive.com/4mbfcn4mf24tv",
    },
    "punjabi_old": {
        "label": "Old Punj",
        "url": "https://gurbanikirtan.radioca.st/start.mp3",
    },
    "punjabi_gold": {
        "label": "Punj Gold",
        "url": "https://live.sgpc.net:8443/;stream.mp3",
    },
    # Remaining nonstop Indian regional streams.
    "bengali": {
        "label": "Bengali",
        "url": "https://audio.streamcast.xyz/listen/radiogoongoon/radio.mp3",
    },
    "tamil": {
        "label": "Tamil",
        "url": "https://psrlive2.listenon.in/80?station=tamil80shitsradio",
    },
    "telugu": {
        "label": "Telugu",
        "url": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio032/playlist.m3u8",
    },
    "marathi": {
        "label": "Marathi",
        "url": "https://airhlspush.pc.cdn.bitgravity.com/httppush/hlspbaudio008/hlspbaudio008_Auto.m3u8",
    },
    "bhojpuri": {"label": "Bhojpuri", "url": "https://stream.zeno.fm/yz0ncx9gha0uv"},
    "kannada": {"label": "Kannada", "url": "https://stream.zeno.fm/68snnbug8rhvv"},
    "hindi_gold": {
        "label": "Hindi Gold",
        "url": "https://azuracast.vibesounds.in:8010/radio.mp3",
    },
    "vividh_bharati": {
        "label": "Vividh",
        "url": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio001/playlist.m3u8",
    },
    "malayalam": {"label": "Malayalam", "url": "https://stream.zeno.fm/9x1sw687nf9uv"},
    "odia": {"label": "Odia", "url": "https://stream.zeno.fm/x1q3r3qdxy8uv"},
    "assamese": {
        "label": "Assamese",
        "url": "https://internetradio.gupshupradio.com:8080/?type=mp3",
    },
    "nepali": {
        "label": "Nepali",
        "url": "https://radio-broadcast.ekantipur.com/stream",
    },
    "urdu": {
        "label": "Urdu",
        "url": "https://samaakhi107-itelservices.radioca.st/stream",
    },
    "tamil_panpalai": {
        "label": "Panpalai",
        "url": "https://tamilpanpalai.radioca.st/ind",
    },
    "tamil_90s": {
        "label": "Tamil90s",
        "url": "https://stream.zeno.fm/tqnws2eafwzuv.aac",
    },
    "kannada_amr": {"label": "AMR", "url": "https://stream.zenolive.com/7g8axtgtsg0uv"},
    "radio_city_kannada": {
        "label": "CityKannada",
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/RADIO_SUNO_MELODY_S06.mp3",
    },
    "bhojpuri_kesari": {
        "label": "Kesari",
        "url": "https://stream.zeno.fm/7yhq985hnxhvv",
    },
    "bhojpuri_sneh": {"label": "Sneh", "url": "https://stream.zeno.fm/zqyhigwwo5mvv"},
    "bengali_a2z": {
        "label": "A2Z",
        "url": "https://listen.radioking.com/radio/1743/stream/125",
    },
    "bengali_mellow": {
        "label": "Mellow",
        "url": "https://radio.mellowbangla.com/stream",
    },
    "raagam": {
        "label": "Raagam",
        "url": "https://airhlspush.pc.cdn.bitgravity.com/httppush/hlspbaudioragam/hlspbaudioragam_Auto.m3u8",
    },
}


def _radio_text(lang_dict) -> str:
    return lang_dict["radio_menu"]


def _plain_rich_text(value: str) -> str:
    """Convert the existing localized HTML copy into a plain rich paragraph."""
    return unescape(re.sub(r"<[^>]+>", "", value)).strip()


def _radio_rich_message(lang_dict, page: int = 0) -> dict:
    """Build a Bot API 10.3 rich message with buttons inside its content."""
    station_items = list(RADIO_STATIONS.items())
    page_size = 6
    page_count = max(1, (len(station_items) + page_size - 1) // page_size)
    page = max(0, min(page, page_count - 1))
    page_items = station_items[page * page_size : (page + 1) * page_size]

    blocks = [
        {
            "type": "blockquote",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": _plain_rich_text(_radio_text(lang_dict)),
                }
            ],
        }
    ]
    blocks.insert(
        0,
        {
            "type": "photo",
            "photo": {
                "type": "photo",
                "media": config.RADIO_IMG,
            },
        },
    )

    for index in range(0, len(page_items), 2):
        row = []
        for key, station in page_items[index : index + 2]:
            button = {
                "text": station["label"],
                "callback_data": f"radio:{key}",
                "style": "primary",
            }
            row.append(button)
        blocks.append(
            {
                "type": "buttons",
                "buttons": row,
                "align": "center",
            }
        )

    navigation = []
    if page > 0:
        navigation.append(
            {
                "text": "Back",
                "callback_data": f"radio:page:{page - 1}",
                "style": "primary",
            }
        )
    if page < page_count - 1:
        navigation.append(
            {
                "text": "Next",
                "callback_data": f"radio:page:{page + 1}",
                "style": "primary",
            }
        )
    if navigation:
        blocks.append(
            {
                "type": "buttons",
                "buttons": navigation,
                "align": "center",
            }
        )

    blocks.append(
        {
            "type": "buttons",
            "buttons": [
                {
                    "text": "Close",
                    "callback_data": "radio:close",
                    "style": "danger",
                }
            ],
            "align": "center",
        }
    )
    return {"blocks": blocks}


async def _answer_callback(
    query: types.CallbackQuery, text: str = None, show_alert: bool = False
) -> None:
    """Answer a callback without failing when Telegram has expired its query ID."""
    try:
        if text:
            await query.answer(text, show_alert=show_alert)
        else:
            await query.answer()
    except errors.QueryIdInvalid:
        logger.debug("Ignoring expired radio callback query.")


async def _ensure_assistant(chat_id: int) -> bool:
    """Make sure the selected assistant can resolve and join this group."""
    client = await db.get_client(chat_id)
    if not client:
        return False

    try:
        member = await app.get_chat_member(chat_id, client.id)
        if member.status in (
            enums.ChatMemberStatus.BANNED,
            enums.ChatMemberStatus.RESTRICTED,
        ):
            await app.unban_chat_member(chat_id, client.id)
    except errors.UserNotParticipant:
        try:
            chat = await app.get_chat(chat_id)
            invite_link = (
                f"https://t.me/{chat.username}" if chat.username else chat.invite_link
            )
            if not invite_link:
                invite_link = await app.export_chat_invite_link(chat_id)
            try:
                await client.join_chat(invite_link)
            except errors.InviteRequestSent:
                await app.approve_chat_join_request(chat_id, client.id)
        except errors.UserAlreadyParticipant:
            pass
        except Exception as exc:
            logger.warning(
                "Could not join assistant to radio chat %s: %s", chat_id, exc
            )
            return False
    except Exception as exc:
        logger.warning("Could not verify assistant in radio chat %s: %s", chat_id, exc)
        return False

    try:
        await client.resolve_peer(chat_id)
        return True
    except Exception as exc:
        logger.warning("Could not resolve radio chat %s: %s", chat_id, exc)
        return False


async def _show_radio_menu(query: types.CallbackQuery, page: int) -> None:
    markup = buttons.radio_markup(RADIO_STATIONS, page)
    try:
        await bot_api.edit_rich_message(
            chat_id=query.message.chat.id,
            message_id=query.message.id,
            rich_message=_radio_rich_message(query.lang, page),
        )
        return
    except Exception as exc:
        logger.debug("Embedded radio menu edit unavailable: %s", exc)
    try:
        await query.edit_message_caption(
            caption=_radio_text(query.lang),
            reply_markup=markup,
        )
    except Exception:
        await query.edit_message_text(
            text=_radio_text(query.lang),
            reply_markup=markup,
        )


@app.on_message(filters.command("radio") & filters.group & ~app.bl_users)
@lang.language()
async def radio_command(_, message: types.Message):
    if not message.from_user:
        return

    try:
        await message.delete()
    except Exception:
        pass

    try:
        # This is the real Bot API 10.3 path: button rows are blocks inside the
        # rich message, not a reply_markup keyboard below the message.
        await bot_api.send_rich_message(
            chat_id=message.chat.id,
            rich_message=_radio_rich_message(message.lang),
        )
    except Exception:
        try:
            markup = buttons.radio_markup(RADIO_STATIONS)
            await message.reply_photo(
                photo=config.RADIO_IMG,
                caption=_radio_text(message.lang),
                reply_markup=markup,
                quote=False,
            )
        except Exception:
            # Keep /radio usable when Telegram cannot fetch the configured image.
            await message.reply_text(
                text=_radio_text(message.lang),
                reply_markup=markup,
                quote=False,
            )


@app.on_callback_query(filters.regex(r"^radio(?::|$)") & ~app.bl_users)
@lang.language()
async def radio_callback(_, query: types.CallbackQuery):
    if not query.from_user or not query.message:
        return

    data = query.data.split(":")
    action = data[1] if len(data) > 1 else ""

    if action == "close":
        await _answer_callback(query)
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    if action == "page":
        await _answer_callback(query)
        try:
            page = int(data[2])
        except (IndexError, ValueError):
            page = 0
        return await _show_radio_menu(query, page)

    station = RADIO_STATIONS.get(action)
    if not station:
        await _answer_callback(
            query, "❌ This station is no longer available.", show_alert=True
        )
        return

    chat_id = query.message.chat.id
    if query.message.chat.type != enums.ChatType.SUPERGROUP:
        await _answer_callback(
            query,
            query.lang["play_chat_invalid"].replace("ᴛʜɪꜱ ʙᴏᴛ", "ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ"),
            show_alert=True,
        )
        return

    if len(queue.get_queue(chat_id)) >= config.QUEUE_LIMIT:
        await _answer_callback(
            query,
            query.lang["play_queue_full"].format(config.QUEUE_LIMIT),
            show_alert=True,
        )
        return

    if not await rich.ephemeral(
        query, "<blockquote>📻 Connecting to the radio station...</blockquote>"
    ):
        await _answer_callback(query, "📻 Connecting to the radio station...")

    if not await db.get_call(chat_id) and not await _ensure_assistant(chat_id):
        return await query.message.reply_text(query.lang["radio_assistant_error"])

    track = Track(
        id=action,
        channel_name="Live Radio",
        duration="LIVE",
        duration_sec=0,
        title=station["label"],
        url=station["url"],
        file_path=station["url"],
        thumbnail=config.RADIO_IMG,
        user=query.from_user.mention,
        is_live=True,
    )

    position = queue.add(chat_id, track)
    try:
        await query.message.delete()
    except Exception:
        pass

    if await db.get_call(chat_id) or position > 0:
        await rich.send(
            chat_id=chat_id,
            html=query.lang["radio_queued"].format(station["label"], position),
            reply_markup=buttons.radio_copy_markup(station["url"]),
        )
        return

    status = await rich.send(
        chat_id=chat_id,
        html=query.lang["radio_connecting"].format(station["label"]),
        reply_markup=buttons.radio_copy_markup(station["url"]),
    )
    try:
        await tune.play_media(chat_id=chat_id, message=status, media=track)
    except Exception as exc:
        logger.error("Radio playback failed in %s: %s", chat_id, exc, exc_info=True)
        queue.clear(chat_id)
        try:
            await status.edit_text(query.lang["radio_error"])
        except Exception:
            pass
