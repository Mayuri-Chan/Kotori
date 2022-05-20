import base64
import telegram
import time

from gd import BOT_TOKEN, OWNER, app_url, chat_url, def_chat_id, owner_alias, user_db as db
from telegram import ParseMode
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

bot = telegram.Bot(token=BOT_TOKEN)

owner_status = db.check_user(OWNER)
if not owner_status:
	s = "{} {} {}".format(OWNER,owner_alias,time.time())
	owner_secret = base64.b64encode(s.encode('utf-8')).decode('utf-8')
	db.add_to_users(OWNER, owner_secret, owner_alias, 1)

def b64_encode(text):
	return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def send_text(chat_id, text, btn, pin):
	m = bot.send_message(text=text, chat_id=chat_id, reply_markup=btn, parse_mode=ParseMode.MARKDOWN)
	if pin:
		m.pin()

def create_secret(update, context):
	user_id = update.effective_user.id
	user_name = update.effective_user.username
	message = update.effective_message
	if str(user_id) == str(OWNER):
		user_name = owner_alias
	user_status = db.check_user(user_id)
	if user_status:
		if user_status.status == 0:
			return message.reply_text("Sorry you are banned from this bot.")
	now = int(time.time())
	cred = "{} {} {}".format(user_id,user_name,now)
	secret = b64_encode(cred)
	db.add_to_users(user_id,secret,user_name,1)
	text = '''Your secret key:
	`{}`

	For uploading file run command below:
	`curl -X "POST" -F secret="{}" -F document=@/path/to/file {}/gd`

	Optional Argument:
	 - `-F chat_id=<chat id>` : send notification to given chat id instead of default chat.
	'''.format(secret,secret,app_url)
	bot.send_message(text=text, chat_id=user_id, parse_mode=ParseMode.MARKDOWN)
	message.reply_text("Your secret key has been generated and sended to private message.")

def get_secret(update, context):
	chat_id = update.effective_chat.id
	user_id = update.effective_user.id
	message = update.effective_message
	user_status = db.check_user(user_id)
	if user_status:
		if user_status.status == 0:
			return message.reply_text("Sorry you are banned from this bot.")
		secret = user_status.secret
		text = '''Your secret key:
		`{}`

		For uploading file run command below:
		`curl -X "POST" -F secret="{}" -F document=@/path/to/file {}/gd`

		Optional Argument:
		 - `-F chat_id=<chat id>` : send notification to given chat id instead of default chat.
		'''.format(secret,secret,app_url)
		if str(chat_id) != str(user_id):
			message.reply_text("Your secret key has been sended to private message.")
			return client.send_message(text=text, chat_id=user_id, parse_mode=ParseMode.MARKDOWN)
		return message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
	message.reply_text("Generate secret key first!")

def ban(update, context):
	message = update.effective_message
	args = context.args
	if message.reply_to_message:
		user_id = message.reply_to_message.from_user.user_id
	else:
		if len(args) > 0:
			user_id = args[0]
		else:
			return
	user_data = db.check_user(user_id)
	if str(user_id) == str(OWNER):
		return message.reply_text("Failed: Cannot ban Owner.")
	if user_data:
		db.add_to_users(user_id,user_data.secret,user_data.user_name,0)
		return message.reply_text("User {} has been banned and cannot uploading file.".format(user_id))
	return message.reply_text("Failed: User not found.")

def unban(client,message):
	message = update.effective_message
	args = context.args
	if message.reply_to_message:
		user_id = message.reply_to_message.from_user.user_id
	else:
		if len(args) > 0:
			user_id = args[0]
		else:
			return
	user_data = db.check_user(user_id)
	if str(user_id) == str(OWNER):
		return
	if user_data:
		db.add_to_users(user_id,user_data.secret,user_data.user_name,1)
		return message.reply_text("User {} has been unbanned and can upload file again.".format(user_id))
	message.reply_text("Failed: User not found.")

def bot_start(update, context):
	text = '''Bot for uploading file to Google Drive with curl by [wulan17](https://t.me/wulan17).
	send /help to view all commands.'''
	update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def bot_help(update, context):
	text = '''
	All commands:
	- /ck
	(re)generate secret key (you can only run this command in [this group]({})).

	- /gk
	Show your secret key.

	Owner only commands:

	- /bangd <user id (Optional)>
	ban a user from using your bot (reply to user message or pass their user id)

	- /bangd <user id (Optional)>
	unban a user from using your bot (reply to user message or pass their user id)
	'''.format(chat_url)
	update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

start_handler = CommandHandler('start', bot_start)
help_handler = CommandHandler('help', bot_help)
ck_handle = CommandHandler('ck', create_secret, filters=Filters.chat(def_chat_id))
gk_handle = CommandHandler('gk', get_secret)
ban_handler = CommandHandler('bangd', ban, filters=Filters.user(OWNER))
unban_handler = CommandHandler('unbangd', unban, filters=Filters.user(OWNER))
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(ck_handle)
dispatcher.add_handler(gk_handle)
dispatcher.add_handler(ban_handler)
dispatcher.add_handler(unban_handler)
updater.start_polling()
