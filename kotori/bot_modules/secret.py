import base64
import time

from kotori import OWNER, app_url, chat_url, def_chat_id, owner_alias
from kotori.bot import bot, dispatcher
from kotori.db import user as db
from telegram import ParseMode
from telegram.ext import CommandHandler, Filters

def b64_encode(text):
	return base64.b64encode(text.encode('utf-8')).decode('utf-8')

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
	user_data = db.check_user(user_id)
	if user_data:
		db.add_to_users(user_id,secret,user_name,1,user_data.photo)
	else:
		db.add_to_users(user_id,secret,user_name,1,'')
	text = 'Your secret key:\n`{}`\n\nFor uploading file run command below:\n`curl -X "POST" -F secret="{}" -F document=@/path/to/file {}/gd`'.format(secret,secret,app_url)
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
		text = 'Your secret key:\n`{}`\n\nFor uploading file run command below:\n`curl -X "POST" -F secret="{}" -F document=@/path/to/file {}/gd`'.format(secret,secret,app_url)
		if str(chat_id) != str(user_id):
			message.reply_text("Your secret key has been sended to private message.")
			return bot.send_message(text=text, chat_id=user_id, parse_mode=ParseMode.MARKDOWN)
		return message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
	message.reply_text("Generate secret key first!")

__mod_name__ = "Secret"
__help__ = """
[Secret]
> `/ck`
(re)generate secret key (you can only run this command in [this group]({})).

> `/gk`
Show your secret key.
""".format(chat_url)

ck_handler = CommandHandler('ck', create_secret, filters=Filters.chat(def_chat_id))
gk_handler = CommandHandler('gk', get_secret)
dispatcher.add_handler(ck_handler)
dispatcher.add_handler(gk_handler)
