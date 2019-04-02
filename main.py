from re import compile as re_compile
from redis import Redis
from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup
from logging import getLogger, Formatter, INFO, FileHandler, StreamHandler

from json import loads, dumps
from emoji import emojize
from pyrogram.api.functions.messages import SetTyping
from pyrogram.api.types import InputPeerUser, SendMessageTypingAction, SendMessageCancelAction

logger = getLogger()
logger.setLevel(level=INFO)
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s")
FileHandler = FileHandler("log")
FileHandler.setFormatter(formatter)
logger.addHandler(FileHandler)
StreamHandler = StreamHandler()
StreamHandler.setFormatter(formatter)
logger.addHandler(StreamHandler)

app = Client('[DATA EXPUNGED]', api_id=[DATA EXPUNGED], api_hash='[DATA EXPUNGED]')
db = Redis(host='127.0.0.1', port=6379, decode_responses=True)
halal = re_compile(r'[ء-ي]')             #阿拉伯语
japanese = re_compile(r'/xAC00-/xD7A3')  #日语
H = re_compile(r'/x3130-/x318F')         #韩语

def addChatBanned(chat_id, name):
    db.set('chat_%s_banned_%s' % (str(chat_id), name), '1')

def removeChatBanned(chat_id, name):
    db.delete('chat_%s_banned_%s' % (str(chat_id), name))

def isBanned(chat_id, name):
    return True if db.get('chat_%s_banned_%s' % (str(chat_id), name)) else False

def getUserStatus(chat_id, user_id):
    if db.get('cache_%s_%s_status' % (str(chat_id), str(user_id))):
        return db.get('cache_%s_%s_status' % (str(chat_id), str(user_id)))
    db.set('cache_%s_%s_status' % (str(chat_id), str(user_id)), app.get_chat_member(chat_id=chat_id, user_id=user_id).status, 3600*24*7)
    return db.get('cache_%s_%s_status' % (str(chat_id), str(user_id)))

def isUserAdmin(chat_id, user_id):
    return True if (getUserStatus(chat_id, user_id) == 'administrator') or (getUserStatus(chat_id, user_id) == 'creator') else False

def build_menu(buttons, n_cols=2, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

first_list = ['halal', 'service', 'video', 'sticker', 'document']
def buildKeyboard_first_page(chat_id):
    menu = list()
    menu.append(InlineKeyboardButton('过滤阿拉伯语', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'halal'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_halal'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_halal'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤服务信息', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'service'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_service'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_service'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤视频', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'video'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_video'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_video'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤贴纸', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'sticker'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_sticker'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_sticker'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤文件', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'document'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_document'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_document'.encode() % chat_id))

    next_page = [InlineKeyboardButton('第一页', callback_data='do_nothing'.encode()), InlineKeyboardButton('下一页 >>', callback_data='page_2'.encode())]
    X = build_menu(menu, footer_buttons=[InlineKeyboardButton('清除成员状态缓存', callback_data='clean_cache_%d'.encode() % chat_id)])
    X.append(next_page)
    return InlineKeyboardMarkup(X)

x2th_list = ['japanese', 'H', 'forward', 'photo', 'game']
def buildKeyboard_2st_page(chat_id):
    menu = list()
    menu.append(InlineKeyboardButton('过滤日语', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'japanese'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_japanese'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_japanese'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤韩语', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'H'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_H'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_H'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤转发的消息', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'forward'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_forward'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_forward'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤图片', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'photo'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_photo'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_photo'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤游戏', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'game'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_game'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_game'.encode() % chat_id))

    next_page = [InlineKeyboardButton('<< 前一页', callback_data='page_1'.encode()), InlineKeyboardButton('第二页', callback_data='do_nothing'.encode()), InlineKeyboardButton('下一页 >>', callback_data='page_3'.encode())]
    X = build_menu(menu, footer_buttons=[InlineKeyboardButton('清除成员状态缓存', callback_data='clean_cache_%d'.encode() % chat_id)])
    X.append(next_page)
    return InlineKeyboardMarkup(X)

def buildKeyboard_3th_page(chat_id):
    menu = list()
    menu.append(InlineKeyboardButton('过滤语音消息', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'voice'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_voice'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_voice'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤联系人名片', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'contact'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_contact'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_contact'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤位置信息', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'location'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_location'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_location'.encode() % chat_id))

    menu.append(InlineKeyboardButton('过滤通过机器人发送的消息', callback_data='do_nothing'.encode()))
    if isBanned(chat_id, 'viabot'):
        menu.append(InlineKeyboardButton('✅', callback_data='turnoff_%d_viabot'.encode() % chat_id))
    else:
        menu.append(InlineKeyboardButton('☑️', callback_data='turnon_%d_viabot'.encode() % chat_id))

    next_page = [InlineKeyboardButton('<< 前一页', callback_data='page_2'.encode()), InlineKeyboardButton('第三页', callback_data='do_nothing'.encode())]
    X = build_menu(menu, footer_buttons=[InlineKeyboardButton('清除成员状态缓存', callback_data='clean_cache_%d'.encode() % chat_id)])
    X.append(next_page)
    return InlineKeyboardMarkup(X)

def delete_message(chat_id, message_id):
    try:
        return app.delete_messages(chat_id, message_id)
    except:
        return

def turn_to_page(client, callback_query):
    data = callback_query.data.decode()
    chat_id = int(float(data.split('_')[1]))
    if data == 'page_1':
        return app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=buildKeyboard_first_page(chat_id))
    if data == 'page_2':
        return app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=buildKeyboard_2st_page(chat_id))
    if data == 'page_3':
        return app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=buildKeyboard_3th_page(chat_id))

@app.on_callback_query()
def query_handler(client, callback_query):
    message = callback_query.message
    data = callback_query.data.decode()
    if data == 'do_nothing':
        return callback_query.answer()
    if data.startswith('page_'):
        return turn_to_page(client, callback_query)
    if data.startswith('clean_cache'):
        for key in db.keys('cache_%s_*' % data.split('_')[2]):
            db.delete(key)
        return callback_query.answer(text='缓存已清除', show_alert=True)
    chat_id = int(float(data.split('_')[1]))
    name = data.split('_')[2]
    if data.startswith('turnon'):
        addChatBanned(chat_id, name)
    if data.startswith('turnoff'):
        removeChatBanned(chat_id, name)
    if name in first_list:
        return app.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id, reply_markup=buildKeyboard_first_page(chat_id))
    if name in x2th_list:
        return app.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id, reply_markup=buildKeyboard_2st_page(chat_id))
    app.edit_message_reply_markup(chat_id=message.chat.id, message_id=message.message_id, reply_markup=buildKeyboard_3th_page(chat_id))

@app.on_message()
def message_handler(client, message):
    text = message.text if message.text else message.caption
    user_id = message.from_user.id
    chat_id = message.chat.id
    if message.chat.type == 'private':
        return
    if text == '/config':
        if isUserAdmin(chat_id, user_id):
            try:
                app.send_message(user_id, text='群组 %d 的消息过滤类型控制台' % chat_id, reply_markup=buildKeyboard_first_page(chat_id))
                return delete_message(chat_id, message.message_id)
            except:
                return app.send_message(chat_id, text='要继续，您需先 [start](https://t.me/SCP_079_CLEAN_BOT) 我', parse_mode='MARKDOWN')
    if isUserAdmin(chat_id, user_id):
        return
    if message.service and isBanned(chat_id, 'service'):
        return delete_message(chat_id, message.message_id)
    if isBanned(chat_id, 'halal') and halal.search(message.text):
        return delete_message(chat_id, message.message_id)
    if isBanned(chat_id, 'japanese') and japanese.search(message.text):
        return delete_message(chat_id, message.message_id)
    if isBanned(chat_id, 'H') and H.search(message.text):
        return delete_message(chat_id, message.message_id)
    if message.video and isBanned(chat_id, 'video'):
        return delete_message(chat_id, message.message_id)
    if message.sticker and isBanned(chat_id, 'sticker'):
        return delete_message(chat_id, message.message_id)
    if message.document and isBanned(chat_id, 'document'):
        return delete_message(chat_id, message.message_id)
    if message.photo and isBanned(chat_id, 'photo'):
        return delete_message(chat_id, message.message_id)
    if message.game and isBanned(chat_id, 'game'):
        return delete_message(chat_id, message.message_id)
    if message.voice and isBanned(chat_id, 'voice'):
        return delete_message(chat_id, message.message_id)
    if message.contact and isBanned(chat_id, 'contact'):
        return delete_message(chat_id, message.message_id)
    if message.via_bot and isBanned(chat_id, 'viabot'):
        return delete_message(chat_id, message.message_id)
    if (message.location or message.venue) and isBanned(chat_id, 'location'):
        return delete_message(chat_id, message.message_id)
    if (message.forward_from or message.forward_from_chat) and isBanned(chat_id, 'forward'):
        return delete_message(chat_id, message.message_id)

app.run()
