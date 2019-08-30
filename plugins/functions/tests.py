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
from .etc import code, get_channel_link, get_entity_text, get_links, get_stripped_link, get_text, thread, user_mention
from .file import delete_file, get_downloaded_path
from .filters import is_detected_url, is_regex_text
from .image import get_file_id, get_qrcode
from .telegram import resolve_username, send_message

# Enable logging
logger = logging.getLogger(__name__)


def clean_test(client: Client, message: Message) -> bool:
    # Test image porn score in the test group
    if glovar.locks["message"].acquire():
        try:
            message_text = get_text(message)
            if re.search("^管理员：[0-9]", message_text):
                return True
            else:
                aid = message.from_user.id

            text = ""

            # Detected record
            content = get_content(client, message)
            detection = glovar.contents.get(content, "")
            if detection:
                text += f"过滤记录：{code(glovar.names[detection])}\n"

            # Detected url
            detection = is_detected_url(message)
            if detection:
                text += f"过滤链接：{code(glovar.names[detection])}\n"

            # AFF link
            if is_regex_text("aff", message_text):
                text += f"AFF 链接：{code('True')}\n"

            # Executive file

            if message.document:
                if message.document.file_name:
                    file_name = message.document.file_name
                    for file_type in ["apk", "bat", "cmd", "com", "exe", "vbs"]:
                        if re.search(f"{file_type}$", file_name, re.I):
                            text += f"可执行文件：{code('True')}\n"
                            break

                if "可执行文件" not in text and message.document.mime_type:
                    mime_type = message.document.mime_type
                    if "executable" in mime_type:
                        text += f"可执行文件：{code('True')}\n"

            # Instant messenger link
            if is_regex_text("iml", message_text):
                text += f"IM 链接：{code('True')}\n"

            # Short link
            if is_regex_text("sho", message_text):
                text += f"短链接：{code('True')}\n"

            # Telegram link
            bypass = get_stripped_link(get_channel_link(message))
            links = get_links(message)
            tg_links = filter(lambda l: is_regex_text("tgl", l), links)
            if not all([bypass in link for link in tg_links]):
                text += f"TG 链接：{code('True')}\n"
            elif message.entities:
                for en in message.entities:
                    if en.type == "mention":
                        username = get_entity_text(message, en)[1:]
                        peer_type, _ = resolve_username(client, username)
                        if peer_type == "channel":
                            text += f"TG 链接：{code('True')}\n"
                            break

            # Telegram proxy
            if is_regex_text("tgp", message_text):
                text += f"TG 代理：{code('True')}\n"

            # QR code
            file_id = get_file_id(message)
            image_path = get_downloaded_path(client, file_id)
            if image_path:
                qrcode = get_qrcode(image_path)
                if qrcode:
                    text += f"二维码：{code('True')}\n"

                delete_file(image_path)

            if text:
                text = f"管理员：{user_mention(aid)}\n\n" + text
                thread(send_message, (client, glovar.test_group_id, text, message.message_id))

            return True
        except Exception as e:
            logger.warning(f"Clean test error: {e}", exc_info=True)
        finally:
            glovar.locks["message"].release()

    return False
