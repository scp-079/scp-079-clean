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

from PIL import Image, ImageEnhance
from pyrogram import Client, Message
from pyzbar.pyzbar import decode

from .. import glovar
from .etc import get_md5sum, t2s
from .file import delete_file, get_downloaded_path

# Enable logging
logger = logging.getLogger(__name__)


def get_image_hash(client: Client, message: Message) -> str:
    # Get the image's hash
    result = ""
    try:
        file_id, file_ref, big = get_file_id(message)
        if not file_id:
            return ""

        image_path = get_downloaded_path(client, file_id, file_ref)
        if not image_path:
            return ""

        result = get_md5sum("file", image_path)
        delete_file(image_path)
    except Exception as e:
        logger.warning(f"Get image hash error: {e}", exc_info=True)

    return result


def get_file_id(message: Message) -> (str, str, bool):
    # Get media message's image file id
    file_id = ""
    file_ref = ""
    big = False
    try:
        if (message.photo
                or (message.sticker and not message.sticker.is_animated)
                or message.document
                or message.game):
            if message.photo:
                file_id = message.photo.file_id
                file_ref = message.photo.file_ref
            elif message.sticker:
                file_id = message.sticker.file_id
                file_ref = message.sticker.file_ref
            elif message.document:
                if (message.document.mime_type
                        and "image" in message.document.mime_type
                        and "gif" not in message.document.mime_type
                        and message.document.file_size
                        and message.document.file_size < glovar.image_size):
                    file_id = message.document.file_id
                    file_ref = message.document.file_ref
            elif message.game:
                file_id = message.game.photo.file_id
                file_ref = message.game.photo.file_ref

        if file_id:
            big = True
        elif ((message.animation and message.animation.thumbs)
              or (message.audio and message.audio.thumbs)
              or (message.video and message.video.thumbs)
              or (message.video_note and message.video_note.thumbs)
              or (message.document and message.document.thumbs)):
            if message.animation:
                file_id = message.animation.thumbs[-1].file_id
                file_ref = message.animation.file_ref
            elif message.audio:
                file_id = message.audio.thumbs[-1].file_id
                file_ref = message.audio.file_ref
            elif message.video:
                file_id = message.video.thumbs[-1].file_id
                file_ref = message.video.file_ref
            elif message.video_note:
                file_id = message.video_note.thumbs[-1].file_id
                file_ref = message.video_note.file_ref
            elif message.document:
                file_id = message.document.thumbs[-1].file_id
                file_ref = message.document.file_ref
    except Exception as e:
        logger.warning(f"Get image status error: {e}", exc_info=True)

    return file_id, file_ref, big


def get_qrcode(path: str) -> str:
    # Get QR code
    result = ""
    try:
        # Open
        image = Image.open(path)

        # Gray
        image = image.convert("L")

        # Contrast
        image = ImageEnhance.Contrast(image).enhance(4.0)

        # Thresholding
        image = image.point(lambda x: 0 if x < 150 else 255)

        # Decode
        decoded_list = decode(image)
        if decoded_list:
            for decoded in decoded_list:
                if decoded.type == "QRCODE":
                    result += f"{decoded.data}\n"

            if result:
                result = result[:-1]
                result = t2s(result)
    except Exception as e:
        logger.warning(f"Get qrcode error: {e}", exc_info=True)

    return result
