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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import get_content, get_debug_text
from ..functions.etc import code, get_text, thread, user_mention
from ..functions.file import save
from ..functions.filters import class_d, declared_message, exchange_channel, from_user, hide_channel
from ..functions.filters import is_ban_text, is_declared_message, is_detected_url, is_high_score_user, is_in_config
from ..functions.filters import is_not_allowed, is_watch_user, new_group, test_group
from ..functions.group import delete_message, leave_group
from ..functions.ids import init_group_id
from ..functions.receive import receive_add_bad, receive_add_except, receive_config_commit, receive_config_reply
from ..functions.receive import receive_declared_message, receive_preview, receive_leave_approve
from ..functions.receive import receive_regex, receive_refresh, receive_remove_bad, receive_remove_except
from ..functions.receive import receive_remove_watch, receive_text_data, receive_user_score, receive_watch_user
from ..functions.telegram import get_admins, send_message
from ..functions.tests import clean_test
from ..functions.timers import send_count
from ..functions.user import terminate_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user & ~Filters.new_chat_members
                   & ~class_d & ~declared_message)
def check(client: Client, message: Message) -> bool:
    # Check the messages sent from groups
    if glovar.locks["message"].acquire():
        try:
            # Check declare status
            if is_declared_message(None, message):
                return True

            # Work with NOSPAM
            gid = message.chat.id
            if glovar.nospam_id in glovar.admin_ids[gid]:
                if is_ban_text(get_text(message)):
                    return False

                if is_watch_user(message, "ban"):
                    return False

                if is_high_score_user(message):
                    return False

            # Detected url
            detection = is_detected_url(message)
            if detection:
                return terminate_user(client, message, detection)

            # Not allowed message
            detection = is_not_allowed(client, message)
            if detection:
                if detection in glovar.types["spam"]:
                    content = get_content(message)
                    glovar.contents[content] = detection

                return terminate_user(client, message, detection)

            return True
        except Exception as e:
            logger.warning(f"Check error: {e}", exc_info=True)
        finally:
            glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user & Filters.new_chat_members & ~new_group
                   & ~class_d & ~declared_message)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    if glovar.locks["message"].acquire():
        try:
            gid = message.chat.id
            mid = message.message_id
            if is_in_config(gid, "ser"):
                if glovar.message_ids[gid]["service"]:
                    thread(delete_message, (client, gid, glovar.message_ids[gid]["service"]))

                glovar.message_ids[gid]["service"] = mid
                save("message_ids")

            return True
        except Exception as e:
            logger.warning(f"Check join error: {e}", exc_info=True)
        finally:
            glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix), group=-1)
def exchange_emergency(_: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)
        if data:
            sender = data["from"]
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            if "EMERGENCY" in receivers:
                if action == "backup":
                    if action_type == "hide":
                        if data is True:
                            glovar.should_hide = data
                        elif data is False and sender == "MANAGE":
                            glovar.should_hide = data

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user
                   & (Filters.new_chat_members | Filters.group_chat_created | Filters.supergroup_chat_created)
                   & new_group)
def init_group(client: Client, message: Message) -> bool:
    # Initiate new groups
    try:
        gid = message.chat.id
        text = get_debug_text(client, message.chat)
        invited_by = message.from_user.id
        # Check permission
        if invited_by == glovar.user_id:
            # Remove the left status
            if gid in glovar.left_group_ids:
                glovar.left_group_ids.discard(gid)

            # Update group's admin list
            if init_group_id(gid):
                admin_members = get_admins(client, gid)
                if admin_members:
                    glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                             if not admin.user.is_bot and not admin.user.is_deleted}
                    save("admin_ids")
                    text += f"状态：{code('已加入群组')}\n"
                else:
                    thread(leave_group, (client, gid))
                    text += (f"状态：{code('已退出群组')}\n"
                             f"原因：{code('获取管理员列表失败')}\n")
        else:
            if gid in glovar.left_group_ids:
                return leave_group(client, gid)

            leave_group(client, gid)
            text += (f"状态：{code('已退出群组')}\n"
                     f"原因：{code('未授权使用')}\n")
            if message.from_user.username:
                text += f"邀请人：{user_mention(invited_by)}\n"
            else:
                text += f"邀请人：{code(invited_by)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    try:
        data = receive_text_data(message)
        if data:
            sender = data["from"]
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            # This will look awkward,
            # seems like it can be simplified,
            # but this is to ensure that the permissions are clear,
            # so it is intentionally written like this
            if glovar.sender in receivers:

                if sender == "CAPTCHA":

                    if action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "CONFIG":

                    if action == "config":
                        if action_type == "commit":
                            receive_config_commit(data)
                        elif action_type == "reply":
                            receive_config_reply(client, data)

                elif sender == "LANG":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)
                        elif action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "LONG":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)
                        elif action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "MANAGE":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "except":
                            receive_add_except(client, data)

                    elif action == "leave":
                        if action_type == "approve":
                            receive_leave_approve(client, data)

                    elif action == "remove":
                        if action_type == "bad":
                            receive_remove_bad(sender, data)
                        elif action_type == "except":
                            receive_remove_except(client, data)
                        elif action_type == "watch":
                            receive_remove_watch(data)

                    elif action_type == "update":
                        if action_type == "refresh":
                            receive_refresh(client, data)

                elif sender == "NOFLOOD":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)
                        elif action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "NOPORN":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)
                        elif action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "NOSPAM":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)
                        elif action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "RECHECK":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)
                        elif action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "REGEX":

                    if action == "update":
                        if action_type == "download":
                            receive_regex(client, message, data)
                        elif action_type == "count":
                            if data == "ask":
                                send_count(client)

                elif sender == "USER":

                    if action == "remove":
                        if action_type == "bad":
                            receive_remove_bad(sender, data)

                    elif action == "update":
                        if action_type == "preview":
                            receive_preview(client, message, data)

                elif sender == "WARN":

                    if action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "WATCH":

                    if action == "add":
                        if action_type == "watch":
                            receive_watch_user(data)

        return True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & test_group & from_user & ~Filters.service
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def test(client: Client, message: Message) -> bool:
    # Show test results in TEST group
    if glovar.locks["test"].acquire():
        try:
            clean_test(client, message)

            return True
        except Exception as e:
            logger.warning(f"Test error: {e}", exc_info=True)
        finally:
            glovar.locks["test"].release()

    return False
