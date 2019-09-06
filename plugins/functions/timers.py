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
from copy import deepcopy
from time import sleep

from pyrogram import Client

from .. import glovar
from .channel import get_debug_text, share_data, share_regex_count
from .etc import code, general_link, get_now, thread
from .file import save
from .filters import is_in_config
from .group import leave_group
from .telegram import delete_messages, get_admins, get_group_info, get_members, send_message
from .user import kick_user, unban_user

# Enable logging
logger = logging.getLogger(__name__)


def backup_files(client: Client) -> bool:
    # Backup data files to BACKUP
    try:
        for file in glovar.file_list:
            try:
                share_data(
                    client=client,
                    receivers=["BACKUP"],
                    action="backup",
                    action_type="pickle",
                    data=file,
                    file=f"data/{file}"
                )
                sleep(5)
            except Exception as e:
                logger.warning(f"Send backup file {file} error: {e}", exc_info=True)

        return True
    except Exception as e:
        logger.warning(f"Backup error: {e}", exc_info=True)

    return False


def clean_banned(client: Client) -> bool:
    # Clean deleted accounts in groups
    try:
        for gid in list(glovar.configs):
            if is_in_config(gid, "tcl"):
                members = get_members(client, gid, "kicked")
                if members:
                    deleted_members = filter(lambda m: m.user.is_deleted, members)
                    count = 0
                    for member in deleted_members:
                        uid = member.user.id
                        thread(unban_user, (client, gid, uid))
                        count += 1

                    if count:
                        text = get_debug_text(client, gid)
                        text += (f"执行操作：{code('清理黑名单')}\n"
                                 f"规则：{code('群组自定义')}\n"
                                 f"失效用户：{code(f'{count} 名')}\n")
                        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Clean banned error: {e}", exc_info=True)

    return False


def clean_members(client: Client) -> bool:
    # Clean deleted accounts in groups
    try:
        for gid in list(glovar.configs):
            if is_in_config(gid, "tcl"):
                members = get_members(client, gid, "all")
                if members:
                    deleted_members = filter(lambda m: m.user.is_deleted, members)
                    count = 0
                    for member in deleted_members:
                        uid = member.user.id
                        if member.status not in {"creator", "administrator"}:
                            thread(kick_user, (client, gid, uid))
                            count += 1

                    if count:
                        text = get_debug_text(client, gid)
                        text += (f"执行操作：{code('清理用户')}\n"
                                 f"规则：{code('群组自定义')}\n"
                                 f"失效用户：{code(f'{count} 名')}\n")
                        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Clean members error: {e}", exc_info=True)

    return False


def interval_hour_01(client: Client) -> bool:
    # Execute every hour
    try:
        # Delete stickers and animations in groups
        for gid in list(glovar.message_ids):
            if is_in_config(gid, "ttd"):
                mid_dict = deepcopy(glovar.message_ids[gid]["stickers"])
                mid_list = list(filter(lambda m: get_now() - mid_dict[m] >= glovar.time_sticker, mid_dict))
                if mid_list:
                    thread(delete_messages, (client, gid, mid_list))
                    for mid in mid_list:
                        glovar.message_ids[gid]["stickers"].pop(mid, 0)

                    text = get_debug_text(client, gid)
                    text += (f"执行操作：{code('定时删除')}\n"
                             f"规则：{code('群组自定义')}\n"
                             f"匹配消息：{code(f'{len(mid_list)} 条')}\n")
                    thread(send_message, (client, glovar.debug_channel_id, text))

        save("message_ids")
    except Exception as e:
        logger.warning(f"Interval hour 01 error: {e}", exc_info=True)

    return False


def interval_min_10() -> bool:
    # Execute every 10 minutes
    try:
        # Clear used /dafm user lists
        for gid in list(glovar.deleted_ids):
            glovar.deleted_ids[gid] = set()

        # Clear used /purge group lists
        glovar.purged_ids = set()

        # Clear recorded users
        for gid in list(glovar.recorded_ids):
            glovar.recorded_ids[gid] = set()

        return True
    except Exception as e:
        logger.warning(f"Interval min 10 error: {e}", exc_info=True)

    return False


def reset_data() -> bool:
    # Reset user data every month
    try:
        glovar.bad_ids = {
            "channels": set(),
            "users": set()
        }
        save("bad_ids")

        glovar.except_ids = {
            "temp": set()
        }
        save("except_ids")

        glovar.user_ids = {}
        save("user_ids")

        glovar.watch_ids = {
            "ban": {},
            "delete": {}
        }
        save("watch_ids")

        return True
    except Exception as e:
        logger.warning(f"Reset data error: {e}", exc_info=True)

    return False


def send_count(client: Client) -> bool:
    # Send regex count to REGEX
    if glovar.locks["regex"].acquire():
        try:
            for word_type in glovar.regex:
                share_regex_count(client, word_type)
                word_list = list(eval(f"glovar.{word_type}_words"))
                for word in word_list:
                    eval(f"glovar.{word_type}_words")[word] = 0

                save(f"{word_type}_words")

            return True
        except Exception as e:
            logger.warning(f"Send count error: {e}", exc_info=True)
        finally:
            glovar.locks["regex"].release()

    return False


def update_admins(client: Client) -> bool:
    # Update admin list every day
    group_list = list(glovar.admin_ids)
    for gid in group_list:
        try:
            should_leave = True
            reason = "permissions"
            admin_members = get_admins(client, gid)
            if admin_members and any([admin.user.is_self for admin in admin_members]):
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                         if not admin.user.is_bot or admin.user.id in glovar.bot_ids}
                if glovar.user_id not in glovar.admin_ids[gid]:
                    reason = "user"
                else:
                    for admin in admin_members:
                        if admin.user.is_self:
                            if admin.can_delete_messages and admin.can_restrict_members:
                                should_leave = False

                if should_leave:
                    group_name, group_link = get_group_info(client, gid)
                    share_data(
                        client=client,
                        receivers=["MANAGE"],
                        action="leave",
                        action_type="request",
                        data={
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "reason": reason
                        }
                    )
                    if reason == "permissions":
                        reason = "权限缺失"
                    elif reason == "user":
                        reason = "缺失 USER"

                    debug_text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                                  f"群组名称：{general_link(group_name, group_link)}\n"
                                  f"群组 ID：{code(gid)}\n"
                                  f"状态：{code(reason)}\n")
                    thread(send_message, (client, glovar.debug_channel_id, debug_text))
            elif admin_members is False or any([admin.user.is_self for admin in admin_members]) is False:
                # Bot is not in the chat, leave automatically without approve
                group_name, group_link = get_group_info(client, gid)
                leave_group(client, gid)
                share_data(
                    client=client,
                    receivers=["MANAGE"],
                    action="leave",
                    action_type="info",
                    data=gid
                )
                debug_text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                              f"群组名称：{general_link(group_name, group_link)}\n"
                              f"群组 ID：{code(gid)}\n"
                              f"状态：{code('自动退出并清空数据')}\n"
                              f"原因：{code('非管理员或已不在群组中')}\n")
                thread(send_message, (client, glovar.debug_channel_id, debug_text))
        except Exception as e:
            logger.warning(f"Update admin in {gid} error: {e}", exc_info=True)

    return True


def update_status(client: Client) -> bool:
    # Update running status to BACKUP
    try:
        share_data(
            client=client,
            receivers=["BACKUP"],
            action="backup",
            action_type="status",
            data="awake"
        )

        return True
    except Exception as e:
        logger.warning(f"Update status error: {e}", exc_info=True)

    return False
