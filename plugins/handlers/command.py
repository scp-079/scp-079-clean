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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import ask_for_help, forward_evidence, get_debug_text, send_debug, share_data
from ..functions.etc import bold, code, delay, get_command_context, get_command_type, get_now, lang
from ..functions.etc import thread, user_mention
from ..functions.file import save
from ..functions.filters import from_user, is_class_c, test_group
from ..functions.group import delete_message
from ..functions.ids import init_group_id
from ..functions.telegram import delete_messages, get_group_info, send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user
                   & Filters.command(["config"], glovar.prefix))
def config(client: Client, message: Message) -> bool:
    # Request CONFIG session
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            # Check command format
            command_type = get_command_type(message)
            if command_type and re.search(f"^{glovar.sender}$", command_type, re.I):
                now = get_now()
                # Check the config lock
                if now - glovar.configs[gid]["lock"] > 310:
                    # Set lock
                    glovar.configs[gid]["lock"] = now
                    save("configs")
                    # Ask CONFIG generate a config session
                    group_name, group_link = get_group_info(client, message.chat)
                    share_data(
                        client=client,
                        receivers=["CONFIG"],
                        action="config",
                        action_type="ask",
                        data={
                            "project_name": glovar.project_name,
                            "project_link": glovar.project_link,
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "user_id": message.from_user.id,
                            "config": glovar.configs[gid],
                            "default": glovar.default_config
                        }
                    )
                    # Send a report message to debug channel
                    text = get_debug_text(client, message.chat)
                    text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                             f"{lang('action')}{lang('colon')}{code(lang('config_create'))}\n")
                    thread(send_message, (client, glovar.debug_channel_id, text))

            delay(3, delete_message, [client, gid, mid])
        else:
            thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user
                   & Filters.command(["config_clean"], glovar.prefix))
def config_directly(client: Client, message: Message) -> bool:
    # Config the bot directly
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            aid = message.from_user.id
            success = True
            reason = lang("config_updated")
            new_config = deepcopy(glovar.configs[gid])
            text = f"{lang('admin_group')}{lang('colon')}{code(aid)}\n"
            # Check command format
            command_type, command_context = get_command_context(message)
            if command_type:
                if command_type == "show":
                    default_text = (lambda x: lang('default') if x else lang('custom'))(new_config.get('default'))
                    text += (f"{lang('action')}{lang('colon')}{code(lang('config_show'))}\n"
                             f"{lang('config')}{lang('colon')}{code(default_text)}\n")
                    for name in glovar.types["all"]:
                        name_text = (lambda x: lang('filter') if x else lang('ignore'))(new_config.get(name))
                        text += f"{glovar.names[name]}{lang('colon')}{code(name_text)}\n"

                    for name in glovar.types["function"]:
                        name_text = (lambda x: lang('enabled') if x else lang('disabled'))(new_config.get(name))
                        text += f"{glovar.names[name]}{lang('colon')}{code(name_text)}\n"

                    thread(send_report_message, (30, client, gid, text))
                    thread(delete_message, (client, gid, mid))
                    return True

                now = get_now()
                # Check the config lock
                if now - new_config["lock"] > 310:
                    if command_type == "default":
                        if not new_config.get("default"):
                            new_config = deepcopy(glovar.default_config)
                    else:
                        if command_context:
                            if command_type in glovar.types["all"] + glovar.types["function"]:
                                if command_context == "off":
                                    new_config[command_type] = False
                                elif command_context == "on":
                                    new_config[command_type] = True
                                else:
                                    success = False
                                    reason = lang("command_para")
                            else:
                                success = False
                                reason = lang("command_type")
                        else:
                            success = False
                            reason = lang("command_lack")

                        if success:
                            new_config["default"] = False
                else:
                    success = False
                    reason = lang("config_locked")
            else:
                success = False
                reason = lang("command_usage")

            if success and new_config != glovar.configs[gid]:
                glovar.configs[gid] = new_config
                save("configs")
                debug_text = get_debug_text(client, message.chat)
                debug_text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                               f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                               f"{lang('more')}{lang('colon')}{code(f'{command_type} {command_context}')}\n")
                thread(send_message, (client, glovar.debug_channel_id, text))

            text += (f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                     f"{lang('status')}{lang('colon')}{code(reason)}\n")
            thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Config directly error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user
                   & Filters.command(["dafm"], glovar.prefix))
def dafm(client: Client, message: Message) -> bool:
    # Delete all from me
    try:
        gid = message.chat.id
        mid = message.message_id
        if init_group_id(gid):
            if glovar.configs[gid]["sde"] or is_class_c(None, message):
                uid = message.from_user.id
                confirm_text = get_command_type(message)
                if confirm_text and re.search("^yes$|^y$", confirm_text, re.I):
                    if uid not in glovar.deleted_ids[gid]:
                        # Forward the request command message as evidence
                        result = forward_evidence(client, message, lang('auto_delete'), lang('custom_group'), "sde")
                        if result:
                            glovar.deleted_ids[gid].add(uid)
                            ask_for_help(client, "delete", gid, uid)
                            send_debug(client, message.chat, lang('sde_action'), uid, mid, result)
                            text = (f"{lang('user')}{lang('colon')}{user_mention(uid)}\n"
                                    f"{lang('action')}{lang('colon')}{code(lang('sde_action'))}\n"
                                    f"{lang('status')}{lang('colon')}{code(lang('status_succeed'))}\n")
                            thread(send_report_message, (15, client, gid, text))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"DAFM error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user
                   & Filters.command(["purge"], glovar.prefix))
def purge(client: Client, message: Message) -> bool:
    # Purge messages
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            # Check validation
            r_message = message.reply_to_message
            if r_message and gid not in glovar.purged_ids:
                aid = message.from_user.id
                r_mid = r_message.message_id
                if mid - r_mid <= 1000:
                    result = forward_evidence(client, message, lang('auto_delete'), lang('custom_group'), "pur")
                    if result:
                        glovar.purged_ids.add(gid)
                        thread(delete_messages, (client, gid, range(r_mid, mid)))
                        send_debug(client, message.chat, lang('pur_debug'), aid, mid, result)
                        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                                f"{lang('action')}{lang('colon')}{code(lang('pur_action'))}\n"
                                f"{lang('status')}{lang('colon')}{code(lang('status_succeed'))}\n")
                        reason = get_command_type(message)
                        if reason:
                            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

                        thread(send_report_message, (30, client, gid, text))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Purge error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & test_group & from_user
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"{lang('admin')}{lang('colon')}{user_mention(aid)}\n\n"
                f"{lang('version')}{lang('colon')}{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return False
