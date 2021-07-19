# SCP-079-CLEAN - Filter specific types of messages
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
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
from subprocess import run, PIPE

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import ask_for_help, forward_evidence, get_debug_text, send_debug, share_data
from ..functions.etc import code, delay, general_link, get_command_context, get_command_type, get_int, get_now
from ..functions.etc import get_readable_time, lang, mention_id, message_link, thread
from ..functions.file import save
from ..functions.filters import authorized_group, from_user, is_class_c, test_group
from ..functions.group import delete_message, get_config_text
from ..functions.telegram import delete_messages, get_group_info, send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["clean"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def clean(client: Client, message: Message) -> bool:
    # Clean messages

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check record
        if gid in glovar.cleaned_ids:
            return True

        # Check permission
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id

        # Forward the request command message as evidence
        result = forward_evidence(
            client=client,
            message=message,
            level=lang("auto_delete"),
            rule=lang("rule_custom"),
            the_type="cln",
            general=False
        )

        if not result:
            return True

        # Clean
        glovar.cleaned_ids.add(gid)

        with glovar.locks["message"]:
            mids = deepcopy(glovar.message_ids[gid]["stickers"])

        thread(delete_messages, (client, gid, mids))

        for sticker_mid in mids:
            glovar.message_ids[gid]["stickers"].pop(sticker_mid, 0)

        save("message_ids")

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('clean_action'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        reason = get_command_type(message)

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("clean_debug"),
            uid=aid,
            mid=mid,
            em=result
        )

        return True
    except Exception as e:
        logger.warning(f"Clean error: {e}", exc_info=True)
    finally:
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["config"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def config(client: Client, message: Message) -> bool:
    # Request CONFIG session

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        # Check command format
        command_type = get_command_type(message)

        if not command_type or not re.search(f"^{glovar.sender}$", command_type, re.I):
            return True

        now = get_now()

        # Check the config lock
        if now - glovar.configs[gid]["lock"] < 310:
            return True

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

        # Send debug message
        text = get_debug_text(client, message.chat)
        text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                 f"{lang('action')}{lang('colon')}{code(lang('config_create'))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)
    finally:
        if is_class_c(None, message):
            delay(3, delete_message, [client, gid, mid])
        else:
            delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command([f"config_{glovar.sender.lower()}"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def config_directly(client: Client, message: Message) -> bool:
    # Config the bot directly

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        success = True
        reason = lang("config_updated")
        new_config = deepcopy(glovar.configs[gid])
        text = f"{lang('admin_group')}{lang('colon')}{code(aid)}\n"

        # Check command format
        command_type, command_context = get_command_context(message)

        if command_type:
            if command_type == "show":
                text += f"{lang('action')}{lang('colon')}{code(lang('config_show'))}\n"
                text += get_config_text(new_config)
                thread(send_report_message, (30, client, gid, text))
                return True

            now = get_now()

            # Check the config lock
            if now - new_config["lock"] > 310:
                if command_type == "default":
                    new_config = deepcopy(glovar.default_config)
                else:
                    if command_context:
                        direct_list = ["delete", "restrict", "friend", "clean"]

                        if command_type in direct_list + glovar.types["all"] + glovar.types["function"]:
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
            # Save new config
            glovar.configs[gid] = new_config
            save("configs")

            # Send debug message
            debug_text = get_debug_text(client, message.chat)
            debug_text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                           f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                           f"{lang('more')}{lang('colon')}{code(f'{command_type} {command_context}')}\n")
            thread(send_message, (client, glovar.debug_channel_id, debug_text))

        text += (f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                 f"{lang('status')}{lang('colon')}{code(reason)}\n")
        thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Config directly error: {e}", exc_info=True)
    finally:
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["dafm"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def dafm(client: Client, message: Message) -> bool:
    # Delete all from me
    result = False

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()

    try:
        # Check permission
        if not glovar.configs[gid].get("sde", False) and not is_class_c(None, message):
            return True

        # Check record
        uid = message.from_user.id

        if uid in glovar.deleted_ids[gid]:
            return True

        return thread(send_report_message, (10, client, gid, f"{mention_id(uid)} 抱歉，本实例下此功能已停用"))

        # Check confirmation
        confirm_text = get_command_type(message)

        if not confirm_text or not re.search("^yes$|^y$", confirm_text, re.I):
            return True

        # Forward the request command message as evidence
        result = forward_evidence(
            client=client,
            message=message,
            level=lang("auto_delete"),
            rule=lang("rule_custom"),
            the_type="sde",
            general=False
        )

        if not result:
            return True

        # Delete
        glovar.deleted_ids[gid].add(uid)
        ask_for_help(client, "delete", gid, uid)

        # Generate the report message's text
        text = (f"{lang('user')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('sde_action'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")

        # Send the report message
        thread(send_report_message, (15, client, gid, text))

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("sde_debug"),
            uid=uid,
            mid=mid,
            em=result
        )

        result = True
    except Exception as e:
        logger.warning(f"DAFM error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return result


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["purge"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def purge(client: Client, message: Message) -> bool:
    # Purge messages

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check record
        if gid in glovar.purged_ids:
            return True

        # Check permission
        if not is_class_c(None, message):
            return True

        # Validation
        r_message = message.reply_to_message

        if not r_message:
            return True

        # Check total count
        r_mid = r_message.message_id

        if mid - r_mid > 1000:
            return True

        # Forward the request command message as evidence
        result = forward_evidence(
            client=client,
            message=message,
            level=lang("auto_delete"),
            rule=lang("rule_custom"),
            the_type="pur",
            general=False
        )

        if not result:
            return True

        # Purge
        glovar.purged_ids.add(gid)
        thread(delete_messages, (client, gid, range(r_mid, mid)))

        # Generate the report message's text
        aid = message.from_user.id
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('pur_action'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        reason = get_command_type(message)

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("pur_debug"),
            uid=aid,
            mid=mid,
            em=result
        )

        return True
    except Exception as e:
        logger.warning(f"Purge error: {e}", exc_info=True)
    finally:
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["purge_begin", "pb"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def purge_begin(client: Client, message: Message) -> bool:
    # Purge begin

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check record
        if gid in glovar.purged_ids:
            return True

        # Check permission
        if not is_class_c(None, message):
            return True

        # Validation
        r_message = message.reply_to_message

        if not r_message:
            return True

        # Save the message id
        r_mid = r_message.message_id
        now = message.date or get_now()
        glovar.message_ids[gid]["purge"] = (r_mid, now)
        save("message_ids")

        # Generate the report message's text
        aid = message.from_user.id
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('pur_begin'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                f"{lang('triggered_by')}{lang('colon')}{general_link(r_mid, message_link(r_message))}\n")
        reason = get_command_type(message)

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Purge begin error: {e}", exc_info=True)
    finally:
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["purge_end", "pe"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def purge_end(client: Client, message: Message) -> bool:
    # Purge end

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check record
        if gid in glovar.purged_ids:
            return True

        # Check permission
        if not is_class_c(None, message):
            return True

        # Validation
        r_message = message.reply_to_message

        if not r_message:
            return True

        # Check usage
        bid, _ = glovar.message_ids[gid]["purge"]
        eid = r_message.message_id

        if not bid or bid > eid:
            return True

        # Check total count
        if bid - eid > 1000:
            return True

        # Forward the request command message as evidence
        result = forward_evidence(
            client=client,
            message=message,
            level=lang("auto_delete"),
            rule=lang("rule_custom"),
            the_type="pur",
            general=False
        )

        if not result:
            return True

        # Purge
        glovar.purged_ids.add(gid)
        thread(delete_messages, (client, gid, range(bid, eid + 1)))
        glovar.message_ids[gid]["purge"] = (0, 0)
        save("message_ids")

        # Generate the report message's text
        aid = message.from_user.id
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('pur_action'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        reason = get_command_type(message)

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("pur_debug"),
            uid=aid,
            mid=mid,
            em=result
        )

        return True
    except Exception as e:
        logger.warning(f"Purge end error: {e}", exc_info=True)
    finally:
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["version"], glovar.prefix)
                   & test_group
                   & from_user)
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Get command type
        command_type = get_command_type(message)

        # Check the command type
        if command_type and command_type.upper() != glovar.sender:
            return False

        # Version info
        git_change = bool(run("git diff-index HEAD --", stdout=PIPE, shell=True).stdout.decode().strip())
        git_date = run("git log -1 --format='%at'", stdout=PIPE, shell=True).stdout.decode()
        git_date = get_readable_time(get_int(git_date), "%Y/%m/%d %H:%M:%S")
        git_hash = run("git rev-parse --short HEAD", stdout=PIPE, shell=True).stdout.decode()
        get_hash_link = f"https://github.com/scp-079/scp-079-{glovar.sender.lower()}/commit/{git_hash}"
        command_date = get_readable_time(message.date, "%Y/%m/%d %H:%M:%S")

        # Generate the text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('version')}{lang('colon')}{code(glovar.version)}\n"
                f"{lang('本地修改')}{lang('colon')}{code(git_change)}\n"
                f"{lang('哈希值')}{lang('colon')}{general_link(git_hash, get_hash_link)}\n"
                f"{lang('提交时间')}{lang('colon')}{code(git_date)}\n"
                f"{lang('命令发送时间')}{lang('colon')}{code(command_date)}\n")

        # Send the report message
        result = send_message(client, cid, text, mid)
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return result
