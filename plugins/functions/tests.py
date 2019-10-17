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
from copy import deepcopy

from pyrogram import Client, Message

from .. import glovar
from .channel import get_content
from .etc import code, get_md5sum, get_text, lang, thread, user_mention
from .file import delete_file, get_downloaded_path
from .filters import is_bmd, is_class_e, is_detected_url, is_emoji, is_exe, is_regex_text, is_tgl
from .image import get_file_id, get_qrcode
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def clean_test(client: Client, message: Message) -> bool:
    # Test image porn score in the test group
    try:
        message_text = get_text(message, True)
        if re.search(f"^{lang('admin')}{lang('colon')}[0-9]", message_text):
            return True
        else:
            aid = message.from_user.id

        text = ""

        # Detected record
        content = get_content(message)
        detection = glovar.contents.get(content, "")
        if detection:
            text += f"{lang('record_content')}{lang('colon')}{code(lang(detection))}\n"

        # Detected url
        detection = is_detected_url(message)
        if detection:
            text += f"{lang('record_link')}{lang('colon')}{code(lang(detection))}\n"

        # Bot command
        if is_bmd(message):
            text += f"{lang('bmd')}{lang('colon')}{code('True')}\n"

        # AFF link
        if is_regex_text("aff", message_text):
            text += f"{lang('aff')}{lang('colon')}{code('True')}\n"

        # Emoji
        if is_emoji("many", message_text):
            text += f"{lang('emo')}{lang('colon')}{code('True')}\n"

        # Executive file
        if is_exe(message):
            text += f"{lang('exe')}{lang('colon')}{code('True')}\n"

        # Instant messenger link
        if is_regex_text("iml", message_text):
            text += f"{lang('iml')}{lang('colon')}{code('True')}\n"

        # Phone number
        if is_regex_text("pho", message_text):
            text += f"{lang('pho')}{lang('colon')}{code('True')}\n"

        # Short link
        if is_regex_text("sho", message_text):
            text += f"{lang('sho')}{lang('colon')}{code('True')}\n"

        # Telegram link
        if is_tgl(client, message):
            text += f"{lang('tgl')}{lang('colon')}{code('True')}\n"
            text += f"{lang('friend')}{lang('colon')}{code(not is_tgl(client, message, True))}\n"

        # Telegram proxy
        if is_regex_text("tgp", message_text):
            text += f"{lang('tgp')}{lang('colon')}{code('True')}\n"

        # QR code
        file_id, file_ref, big = get_file_id(message)
        image_path = big and get_downloaded_path(client, file_id, file_ref)
        image_hash = image_path and get_md5sum("file", image_path)
        qrcode = image_path and get_qrcode(image_path)
        image_path and delete_file(image_path)

        if qrcode:
            text += f"{lang('qrc')}{lang('colon')}{code('True')}\n"

        # Send the result
        if text:
            whitelisted = is_class_e(None, message) or image_hash in glovar.except_ids["temp"]
            text += f"{lang('white_listed')}{lang('colon')}{code(whitelisted)}\n"
            text = f"{lang('admin')}{lang('colon')}{user_mention(aid)}\n\n" + text

            # Show emoji
            emoji_dict = {}
            emoji_set = {emoji for emoji in glovar.emoji_set
                         if emoji in message_text and emoji not in glovar.emoji_protect}
            emoji_old_set = deepcopy(emoji_set)

            for emoji in emoji_old_set:
                if any(emoji in emoji_old and emoji != emoji_old for emoji_old in emoji_old_set):
                    emoji_set.discard(emoji)

            for emoji in emoji_set:
                emoji_dict[emoji] = message_text.count(emoji)

            if emoji_dict:
                text += f"{lang('emoji_total')}{lang('colon')}{code(sum(emoji_dict.values()))}\n\n"
                for emoji in emoji_dict:
                    text += "\t" * 4 + f"{emoji}    {code(emoji_dict[emoji])}\n"

            thread(send_message, (client, glovar.test_group_id, text, message.message_id))

        return True
    except Exception as e:
        logger.warning(f"Clean test error: {e}", exc_info=True)

    return False
