# SCP-079-CLEAN - Filter specific types of messages
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-CLEAN.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re

from pyrogram import Client, Message

from .. import glovar
from .channel import get_content
from .etc import code, get_text, thread, user_mention
from .file import delete_file, get_downloaded_path
from .filters import is_bmd, is_class_e, is_detected_url, is_exe, is_regex_text, is_tgl
from .image import get_file_id, get_qrcode
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def clean_test(client: Client, message: Message) -> bool:
    # Test image porn score in the test group
    try:
        message_text = get_text(message)
        if re.search(f"^{glovar.lang['admin']}{glovar.lang['colon']}[0-9]", message_text):
            return True
        else:
            aid = message.from_user.id

        text = ""

        # Detected record
        content = get_content(message)
        detection = glovar.contents.get(content, "")
        if detection:
            text += f"{glovar.lang['record_content']}{glovar.lang['colon']}{code(glovar.names[detection])}\n"

        # Detected url
        detection = is_detected_url(message)
        if detection:
            text += f"{glovar.lang['record_link']}{glovar.lang['colon']}{code(glovar.names[detection])}\n"

        # Bot command
        if is_bmd(message):
            text += f"{glovar.lang['bmd']}{glovar.lang['colon']}{code('True')}\n"

        # AFF link
        if is_regex_text("aff", message_text):
            text += f"{glovar.lang['aff']}{glovar.lang['colon']}{code('True')}\n"

        # Executive file
        if is_exe(message):
            text += f"{glovar.lang['exe']}{glovar.lang['colon']}{code('True')}\n"

        # Instant messenger link
        if is_regex_text("iml", message_text):
            text += f"{glovar.lang['iml']}{glovar.lang['colon']}{code('True')}\n"

        # Short link
        if is_regex_text("sho", message_text):
            text += f"{glovar.lang['sho']}{glovar.lang['colon']}{code('True')}\n"

        # Telegram link
        if is_tgl(client, message):
            text += f"{glovar.lang['tgl']}{glovar.lang['colon']}{code('True')}\n"

        # Telegram proxy
        if is_regex_text("tgp", message_text):
            text += f"{glovar.lang['tgp']}{glovar.lang['colon']}{code('True')}\n"

        # QR code
        file_id, big = get_file_id(message)
        if big:
            image_path = get_downloaded_path(client, file_id)
            if image_path:
                qrcode = get_qrcode(image_path)
                if qrcode:
                    text += f"{glovar.lang['qrc']}{glovar.lang['colon']}{code('True')}\n"

                delete_file(image_path)

        if text:
            text += f"{glovar.lang['white_listed']}{glovar.lang['colon']}{code(is_class_e(None, message))}\n"
            text = f"{glovar.lang['admin']}{glovar.lang['colon']}{user_mention(aid)}\n\n" + text
            thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        return True
    except Exception as e:
        logger.warning(f"Clean test error: {e}", exc_info=True)

    return False
