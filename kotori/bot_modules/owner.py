from kotori import OWNER
from kotori.bot import dispatcher
from kotori.db import user as db
from telegram.ext import CommandHandler, Filters

def ban(update, context):
	message = update.effective_message
	args = context.args
	if message.reply_to_message:
		user_id = message.reply_to_message.from_user.id
	else:
		if len(args) > 0:
			user_id = args[0]
		else:
			return
	user_data = db.check_user(user_id)
	if str(user_id) == str(OWNER):
		return message.reply_text("Failed: Cannot ban Owner.")
	if user_data:
		db.add_to_users(user_id,user_data.secret,user_data.user_name,0,user_data.photo)
		return message.reply_text("User {} has been banned and cannot uploading file.".format(user_id))
	return message.reply_text("Failed: User not found.")

def unban(update, context):
	message = update.effective_message
	args = context.args
	if message.reply_to_message:
		user_id = message.reply_to_message.from_user.id
	else:
		if len(args) > 0:
			user_id = args[0]
		else:
			return
	user_data = db.check_user(user_id)
	if user_data:
		db.add_to_users(user_id,user_data.secret,user_data.user_name,1,user_data.photo)
		return message.reply_text("User {} has been unbanned and can upload file again.".format(user_id))
	message.reply_text("Failed: User not found.")

__mod_name__ = "Owner tools"
__help__ = """
[Owner tools]
> `/bangd`
ban a user from using your bot (reply to user message or pass their user id)

> `/unbangd`
unban a user from using your bot (reply to user message or pass their user id)
"""

ban_handler = CommandHandler('bangd', ban, filters=Filters.user(OWNER))
unban_handler = CommandHandler('unbangd', unban, filters=Filters.user(OWNER))
dispatcher.add_handler(ban_handler)
dispatcher.add_handler(unban_handler)
