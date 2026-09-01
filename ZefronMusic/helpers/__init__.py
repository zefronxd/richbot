# ==============================================================================
# ZefronMusic.helpers
# ==============================================================================
# Exports all the helper singletons (buttons, thumb, utils, etc) so plugins
# can grab them easily.
# ==============================================================================

from ZefronMusic import config

from ._admins import admin_check, can_manage_vc, is_admin, reload_admins
from ._bot_api import BotApi10
from ._dataclass import Media, Track
from ._inline import Inline
from ._queue import Queue
from ._rich import Rich
from ._rich_layouts import (
    help_rich_message,
    playback_rich_message,
    queued_playback_rich_message,
    start_rich_message,
)
from ._thumbnails import Thumbnail
from ._utilities import Utilities

buttons = Inline()
bot_api = BotApi10(config.BOT_TOKEN)
rich = Rich()
thumb = Thumbnail()
utils = Utilities()
