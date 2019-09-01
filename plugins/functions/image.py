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

from PIL import Image
from pyrogram import Message
from pyzbar.pyzbar import decode

from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)


def get_file_id(message: Message) -> str:
    # Get media message's file id
    file_id = ""
    try:
        if (message.photo
                or (message.sticker and not message.sticker.is_animated)
                or message.document
                or message.game):
            if message.photo:
                file_id = message.photo.file_id
            elif message.sticker:
                file_id = message.sticker.file_id
            elif message.document:
                if (message.document.mime_type
                        and "image" in message.document.mime_type
                        and "gif" not in message.document.mime_type
                        and message.document.file_size
                        and message.document.file_size < glovar.image_size):
                    file_id = message.document.file_id
            elif message.game:
                file_id = message.game.photo
    except Exception as e:
        logger.warning(f"Get file id error: {e}", exc_info=True)

    return file_id


def get_qrcode(path: str) -> str:
    # Get QR code
    result = ""
    try:
        image = Image.open(path)
        image = image.convert("L")
        image = image.point(lambda x: 0 if x < 150 else 255)
        decoded_list = decode(image)
        if decoded_list:
            for decoded in decoded_list:
                if decoded.type == "QRCODE":
                    result += f"{decoded.data}\n"

            if result:
                result = result[:-1]
    except Exception as e:
        logger.warning(f"Get qrcode error: {e}", exc_info=True)

    return result
