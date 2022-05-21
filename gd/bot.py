import asyncio
import base64
import io
import math
import telegram
import time

from gd import BOT_TOKEN, OWNER, app_url, chat_url, def_chat_id, gd_service, owner_alias, user_db as db, data_db
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
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
	m = bot.send_message(text=text, chat_id=chat_id, reply_markup=btn, parse_mode=ParseMode.HTML)
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
			bot.send_message(text=text, chat_id=user_id, parse_mode=ParseMode.MARKDOWN)
		return message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
	message.reply_text("Generate secret key first!")

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
		db.add_to_users(user_id,user_data.secret,user_data.user_name,0)
		return message.reply_text("User {} has been banned and cannot uploading file.".format(user_id))
	return message.reply_text("Failed: User not found.")

def unban(client,message):
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
		return
	if user_data:
		db.add_to_users(user_id,user_data.secret,user_data.user_name,1)
		return message.reply_text("User {} has been unbanned and can upload file again.".format(user_id))
	message.reply_text("Failed: User not found.")

def bot_start(update, context):
	args = context.args
	if len(args) >= 1:
		if args[0].lower().startswith("gen_"):
			return asyncio.run(gen_file(update,context))
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

def time_formatter(seconds: int) -> str:
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	days, hours = divmod(hours, 24)
	tmp = (
		((str(days) + " day(s), ") if days else "")
		+ ((str(hours) + " hour(s), ") if hours else "")
		+ ((str(minutes) + " minute(s), ") if minutes else "")
		+ ((str(seconds) + " second(s), ") if seconds else "")
	)
	return tmp[:-2]

def humanbytes(size: int) -> str:
	if size is None or isinstance(size, str):
		return ""

	power = 2**10
	raised_to_pow = 0
	dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
	while size > power:
		size /= power
		raised_to_pow += 1
	return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"

async def get_information(service, Id):
	r = (
		service.files()
		.get(
			fileId=Id,
			fields="name, id, size, mimeType, "
			"webViewLink, webContentLink,"
			"description",
			supportsAllDrives=True,
		)
		.execute()
	)
	return r

async def gen_file(update, context):
	user_id = update.effective_user.id
	user_name = update.effective_user.username
	message = update.effective_message
	args = context.args
	if args[0].startswith("gen_"):
		file_id = args[0].replace("gen_", "")
	else:
		file_id = args[0]
	file_data = data_db.get_file(file_id)
	file = await get_information(gd_service, file_id)
	if not file_data:
		if not db.check_user(user_id):
			return message.reply_text("Generate secret key first!")
		file_name = file.get("name")
		addtodata = True
	else:
		file_name = file_data[0].file_name
		addtodata = False
	request = gd_service.files().get_media(fileId=file_id, supportsAllDrives=True)
	file_path = "files/{}".format(file_name)
	msg = message.reply_text("Downloading...")
	with io.FileIO(file_path, "wb") as df:
		downloader = MediaIoBaseDownload(df, request)
		complete = False
		current_time = time.time()
		display_message = None
		while complete is False:
			status, complete = downloader.next_chunk()
			if status:
				file_size = status.total_size
				diff = time.time() - current_time
				downloaded = status.resumable_progress
				percentage = downloaded / file_size * 100
				speed = round(downloaded / diff, 2)
				eta = round((file_size - downloaded) / speed)
				prog_str = "`Downloading` | [{}{}] `{}%`".format(
					"".join(["●" for i in range(math.floor(percentage / 10))]),
					"".join(["○" for i in range(10 - math.floor(percentage / 10))]),
					round(percentage, 2),
				)
				current_message = (
					"`[FILE - DOWNLOAD]`\n\n"
					f"`{file_name}`\n"
					f"`Status`\n{prog_str}\n"
					f"`{humanbytes(downloaded)} of {humanbytes(file_size)}"
					f" @ {humanbytes(speed)}`\n"
					f"`ETA` -> {time_formatter(eta)}"
				)
				if (
					round(diff % 15.00) == 0
					and (display_message != current_message)
					or (downloaded == file_size)
				):
					msg.edit_text(current_message, parse_mode=ParseMode.MARKDOWN)
					display_message = current_message
	if addtodata:
		msg.edit_text("Uploading...")
		media_body = MediaFileUpload(
			file_path,
			resumable=True
		)

		body = {
			"name": file_name,
		}

		file = gd_service.files().create(body=body, media_body=media_body,
									  fields="id").execute()

		file_id = file.get("id")
		permission = {
			"role": "reader",
			"type": "anyone"
		}

		gd_service.permissions().create(fileId=file_id, body=permission).execute()
		data_db.add_to_gddata(user_id,file_id,file_name,time.time())
	file_link = "https://drive.google.com/file/d/{}/view".format(file_id)
	index_link = "{}/files?user_id={}".format(app_url,user_id)
	direct_link = "{}/download?id={}".format(app_url,file_id)
	btn = InlineKeyboardMarkup([
		[InlineKeyboardButton(text="⬇️Download", url=file_link), InlineKeyboardButton(text="⬇️Direct", url=direct_link)],
		[InlineKeyboardButton(text="☁️Index", url=index_link)]
		])
	text = "File Name: {}\nSize: {}".format(file_name,humanbytes(file_size))
	msg.edit_text(text, reply_markup=btn, parse_mode=ParseMode.HTML)

def mirrorgd(update, context):
	message = update.effective_message
	if len(context.args) == 0:
		return message.reply_text("File id required!")
	asyncio.run(gen_file(update,context))

start_handler = CommandHandler('start', bot_start, pass_args=True)
help_handler = CommandHandler('help', bot_help)
ck_handle = CommandHandler('ck', create_secret, filters=Filters.chat(def_chat_id))
gk_handle = CommandHandler('gk', get_secret)
ban_handler = CommandHandler('bangd', ban, filters=Filters.user(OWNER))
unban_handler = CommandHandler('unbangd', unban, filters=Filters.user(OWNER))
mirror_handler = CommandHandler('mirrorgd', mirrorgd, pass_args=True)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(ck_handle)
dispatcher.add_handler(gk_handle)
dispatcher.add_handler(ban_handler)
dispatcher.add_handler(unban_handler)
dispatcher.add_handler(mirror_handler)
updater.start_polling()
